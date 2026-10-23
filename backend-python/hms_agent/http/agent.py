"""The agent-facing HTTP surface.

`POST /agent/run` and `POST /agent/resume` put the LangGraph agent behind the
same controls as the single-tool endpoint. The connection that matters is this
one line in `_call_tool`:

    self._tools.call_as(principal, tool, arguments, request_id)

The graph does not reach handlers itself. Every tool it selects goes through
the same registry lookup, schema validation, policy check, idempotency claim and
audit trail as a direct API call. Policy is therefore evaluated twice — once in
the graph's `check_policy` node so routing can react to it, and again at the
execution boundary. That is deliberate: the boundary must hold even if a future
edit to the graph forgets to route through the policy node.

Status codes describe what happened to the requested work:

    200  the run completed
    202  suspended awaiting human approval; nothing executed
    403  policy refused the action; nothing executed
    502  could not complete, escalated for human review

`executed` and `completed` are always present, so no client has to infer
outcome from a status code alone.
"""
from __future__ import annotations

import uuid
from typing import Any, Callable, Mapping

from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from ..auth import AuthError, TokenIssuer, principal_from_request
from ..graph import build_agent_graph, initial_state
from ..graph.planner import Planner
from ..policy import PolicyEngine, Principal
from .app import CallResponse, ToolCallService


def _interrupt_payload(result: Mapping[str, Any]) -> dict[str, Any] | None:
    """Extract the approval request from an interrupted run, across langgraph
    versions that shape `__interrupt__` slightly differently."""
    raw = result.get("__interrupt__")
    if not raw:
        return None
    first = raw[0] if isinstance(raw, (list, tuple)) and raw else raw
    value = getattr(first, "value", None)
    return value if isinstance(value, dict) else {"kind": "approval_required"}


class AgentRunService:
    def __init__(
        self,
        planner: Planner,
        policy_engine: PolicyEngine,
        tool_service: ToolCallService,
        issuer: TokenIssuer,
        checkpointer: Any,
        metrics: Any = None,
    ):
        self._planner = planner
        self._policy = policy_engine
        self._tools = tool_service
        self._issuer = issuer
        self._checkpointer = checkpointer
        self._metrics = metrics
        self._graph = build_agent_graph(
            planner, policy_engine, self._call_tool,
            checkpointer=checkpointer,
            # Agent-level denials never reach the execution boundary, so the
            # graph needs the sink directly or they would go unaudited.
            audit_sink=getattr(tool_service, "_sink", None),
        )

    # -- the bridge -------------------------------------------------------

    def _call_tool(self, principal: Principal, tool: str, arguments: dict,
                   request_id=None, approval=None):
        """Every tool the agent selects goes through the guarded boundary."""
        response: CallResponse = self._tools.call_as(
            principal, tool, arguments, request_id=request_id, approval=approval
        )
        return response.body

    # -- authentication ---------------------------------------------------

    def _authenticate(self, headers: Mapping[str, str]) -> Principal:
        return principal_from_request(headers, self._issuer)

    # -- run --------------------------------------------------------------

    def run(self, headers: Mapping[str, str], payload: Mapping[str, Any]) -> CallResponse:
        try:
            principal = self._authenticate(headers)
        except AuthError as exc:
            return CallResponse(
                status=exc.http_status,
                body={"success": False, "executed": False, "completed": False,
                      "error": {"code": exc.code, "message": "authentication required"}},
            )

        request_text = (payload.get("request") or "").strip()
        if not request_text:
            return CallResponse(
                status=400,
                body={"success": False, "executed": False, "completed": False,
                      "error": {"code": "MISSING_REQUEST", "message": "request is required"}},
            )

        thread_id = payload.get("thread_id") or uuid.uuid4().hex
        run_id = uuid.uuid4().hex
        config = {"configurable": {"thread_id": thread_id}}

        span = None
        if self._metrics is not None:
            span = self._metrics.start_run(run_id, principal.user_id, principal.role)

        state = initial_state(
            request=request_text,
            user_id=principal.user_id,
            role=principal.role,
            run_id=run_id,
            session_id=principal.session_id,
            patient_id=payload.get("patient_id"),
        )

        try:
            result = self._graph.invoke(state, config=config)
        except Exception as exc:
            # A planner or graph failure must not look like a completed action.
            if self._metrics is not None:
                self._metrics.end_run(run_id, "FAILED")
            return CallResponse(
                status=502,
                body={"success": False, "executed": False, "completed": False,
                      "run_id": run_id, "thread_id": thread_id,
                      "error": {"code": "AGENT_RUN_FAILED",
                                "message": "the agent could not complete this request",
                                "failure_type": type(exc).__name__}},
            )

        return self._to_response(result, run_id, thread_id, span)

    # -- resume -----------------------------------------------------------

    def resume(self, headers: Mapping[str, str], payload: Mapping[str, Any]) -> CallResponse:
        from langgraph.types import Command

        try:
            approver = self._authenticate(headers)
        except AuthError as exc:
            return CallResponse(
                status=exc.http_status,
                body={"success": False, "executed": False, "completed": False,
                      "error": {"code": exc.code, "message": "authentication required"}},
            )

        thread_id = payload.get("thread_id")
        if not thread_id:
            return CallResponse(
                status=400,
                body={"success": False, "executed": False, "completed": False,
                      "error": {"code": "MISSING_THREAD_ID",
                                "message": "thread_id is required to resume a run"}},
            )

        if "approved" not in payload:
            return CallResponse(
                status=400,
                body={"success": False, "executed": False, "completed": False,
                      "error": {"code": "MISSING_DECISION",
                                "message": "approved must be true or false"}},
            )

        config = {"configurable": {"thread_id": thread_id}}
        decision = {
            "approved": bool(payload["approved"]),
            # The approver is the authenticated caller, never a body field.
            "approver": approver.user_id,
            "approver_role": approver.role,
        }

        try:
            result = self._graph.invoke(Command(resume=decision), config=config)
        except Exception as exc:
            return CallResponse(
                status=502,
                body={"success": False, "executed": False, "completed": False,
                      "thread_id": thread_id,
                      "error": {"code": "AGENT_RESUME_FAILED",
                                "message": "the run could not be resumed",
                                "failure_type": type(exc).__name__}},
            )

        return self._to_response(result, result.get("run_id"), thread_id, None)

    # -- response mapping -------------------------------------------------

    def _to_response(self, result, run_id, thread_id, span) -> CallResponse:
        executed_tools = result.get("executed_tools") or []
        executed = len(executed_tools) > 0

        base = {
            "run_id": run_id,
            "thread_id": thread_id,
            "executed": executed,
            "executed_tools": [t.get("tool") for t in executed_tools],
            "iterations": result.get("iteration_count", 0),
            "errors": result.get("errors") or [],
        }

        if span is not None:
            span.tool_calls = len(executed_tools)

        interrupt = _interrupt_payload(result)
        if interrupt is not None:
            if self._metrics is not None and run_id:
                self._metrics.end_run(run_id, "AWAITING_APPROVAL")
            return CallResponse(
                status=202,
                body={**base, "success": False, "completed": False,
                      "status": "AWAITING_APPROVAL", "approval": interrupt,
                      "message": "This action needs approval before it can be carried out."},
            )

        disposition = result.get("disposition")
        final_response = result.get("final_response")

        if self._metrics is not None and run_id:
            self._metrics.end_run(run_id, disposition or "UNKNOWN")

        if disposition == "DENIED":
            return CallResponse(
                status=403,
                body={**base, "success": False, "completed": False,
                      "disposition": "DENIED", "response": final_response,
                      "error": {"code": "POLICY_DENIED",
                                "message": result.get("policy_reason") or "not permitted"}},
            )

        if disposition in ("ESCALATE", "EXHAUSTED"):
            return CallResponse(
                status=502,
                body={**base, "success": False, "completed": False,
                      "disposition": disposition, "needs_human": True,
                      "response": final_response,
                      "error": {"code": f"AGENT_{disposition}",
                                "message": final_response or "could not complete"}},
            )

        return CallResponse(
            status=200,
            body={**base, "success": True, "completed": True,
                  "disposition": disposition or "COMPLETE", "response": final_response},
        )


def build_agent_routes(service: AgentRunService, prefix: str = "/agent") -> list[Route]:
    async def run_handler(request: Request) -> JSONResponse:
        try:
            payload = await request.json()
        except Exception:
            return JSONResponse(
                {"success": False, "executed": False,
                 "error": {"code": "MALFORMED_BODY", "message": "request body must be JSON"}},
                status_code=400,
            )
        response = service.run(request.headers, payload)
        return JSONResponse(response.body, status_code=response.status)

    async def resume_handler(request: Request) -> JSONResponse:
        try:
            payload = await request.json()
        except Exception:
            return JSONResponse(
                {"success": False, "executed": False,
                 "error": {"code": "MALFORMED_BODY", "message": "request body must be JSON"}},
                status_code=400,
            )
        response = service.resume(request.headers, payload)
        return JSONResponse(response.body, status_code=response.status)

    return [
        Route(f"{prefix}/run", run_handler, methods=["POST"]),
        Route(f"{prefix}/resume", resume_handler, methods=["POST"]),
    ]
