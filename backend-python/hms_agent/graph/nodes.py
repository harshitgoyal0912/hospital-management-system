"""Graph nodes.

Each node does one thing and writes its result into the state. The division is
the Phase 20 responsibility split made literal:

    plan            -> the LLM proposes
    check_policy    -> deterministic code decides
    execute         -> the guarded boundary acts
    validate_result -> deterministic code checks what came back
    decide          -> deterministic code routes

A node never both proposes and authorises.
"""
from __future__ import annotations

import uuid
from typing import Any, Callable

from ..audit import AuditStage, AuditTrail
from ..policy import ApprovalGrant, Decision, PolicyEngine, Principal
from .planner import Plan, Planner
from .state import MAX_AGENT_STEPS, MAX_TOOL_RETRIES, AgentState


def make_plan_node(planner: Planner) -> Callable[[AgentState], dict]:
    def plan_node(state: AgentState) -> dict:
        plan: Plan = planner.plan(state)
        update: dict[str, Any] = {
            "iteration_count": state.get("iteration_count", 0) + 1,
            "selected_tool": plan.tool,
            "tool_arguments": dict(plan.arguments or {}),
            "messages": [{"role": "planner", "content": plan.reasoning or ""}],
        }
        if plan.intent:
            update["intent"] = plan.intent
        if plan.tool is None:
            update["disposition"] = "COMPLETE"
            update["final_response"] = plan.response or "Done."
        else:
            # A fresh idempotency key per planned step, stable across retries of
            # that same step so a retry cannot double-execute.
            update["request_id"] = f"{state.get('run_id') or uuid.uuid4().hex}-{update['iteration_count']}"
        return update

    return plan_node


def make_policy_node(engine: PolicyEngine, audit_sink=None) -> Callable[[AgentState], dict]:
    def policy_node(state: AgentState) -> dict:
        tool = state.get("selected_tool")
        if not tool:
            return {"policy_decision": None}

        principal = Principal(
            user_id=state["user_id"],
            role=state["role"],
            session_id=state.get("session_id"),
        )
        decision = engine.check(principal, tool, state.get("tool_arguments") or {})

        update: dict[str, Any] = {
            "policy_decision": decision.decision.value,
            "policy_reason": decision.reason,
            "approval_required": decision.decision
            in (Decision.REQUIRE_HUMAN_APPROVAL, Decision.REQUIRE_CONFIRMATION),
        }

        if audit_sink is not None and state.get("run_id"):
            # An agent-level refusal never reaches the execution boundary, so
            # without this the denial would leave no audit record at all.
            trail = AuditTrail(audit_sink, run_id=state["run_id"])
            trail.record(
                AuditStage.REQUESTED, tool=tool, user_id=state["user_id"],
                role=state["role"], arguments=state.get("tool_arguments"),
            )
            trail.record(
                AuditStage.AUTHENTICATED, tool=tool,
                user_id=state["user_id"], role=state["role"],
            )
            if decision.decision is Decision.DENY:
                trail.record(
                    AuditStage.POLICY_DENIED, tool=tool, user_id=state["user_id"],
                    role=state["role"], detail=decision.rule_id,
                )
                trail.record(AuditStage.NOT_EXECUTED, tool=tool)

        if decision.decision is Decision.DENY:
            update["disposition"] = "DENIED"
            update["final_response"] = (
                f"That action is not permitted for your role. {decision.reason}"
            )
            update["errors"] = [f"policy denied {tool}: {decision.rule_id}"]
        elif update["approval_required"]:
            update["approval_status"] = "PENDING"
        else:
            update["approval_status"] = "NOT_REQUIRED"

        return update

    return policy_node


def make_execute_node(call_tool: Callable[..., Any]) -> Callable[[AgentState], dict]:
    """`call_tool(principal, tool, arguments, request_id) -> ToolResult-like`."""

    def execute_node(state: AgentState) -> dict:
        tool = state["selected_tool"]
        principal = Principal(
            user_id=state["user_id"],
            role=state["role"],
            session_id=state.get("session_id"),
        )
        try:
            result = call_tool(
                principal=principal,
                tool=tool,
                arguments=state.get("tool_arguments") or {},
                request_id=state.get("request_id"),
                approval=ApprovalGrant.from_dict(state.get("approval_grant")),
            )
        except Exception as exc:
            return {
                "tool_result": None,
                "errors": [f"{tool} raised {type(exc).__name__}"],
                "retry_count": state.get("retry_count", 0) + 1,
            }

        executed = getattr(result, "executed", None)
        if executed is None and isinstance(result, dict):
            executed = result.get("executed")

        if not executed:
            error = getattr(result, "error", None) or (
                result.get("error") if isinstance(result, dict) else None
            )
            return {
                "tool_result": None,
                "errors": [f"{tool} did not execute: {error}"],
                "retry_count": state.get("retry_count", 0) + 1,
            }

        value = getattr(result, "value", None)
        if value is None and isinstance(result, dict):
            value = result.get("result")

        return {
            "tool_result": value,
            "retry_count": 0,
            "executed_tools": [{"tool": tool, "arguments": state.get("tool_arguments")}],
            "messages": [{"role": "tool", "name": tool, "content": value}],
        }

    return execute_node


def validate_result_node(state: AgentState) -> dict:
    """Deterministic check on what the tool returned.

    A tool that returns nothing is not treated as a success just because it did
    not raise.
    """
    tool = state.get("selected_tool")
    if state.get("tool_result") is None and state.get("retry_count", 0) == 0:
        return {
            "errors": [f"{tool} returned no result"],
            "retry_count": state.get("retry_count", 0) + 1,
        }
    return {}


def decide_node(state: AgentState) -> dict:
    """Route: continue planning, finish, retry, or stop.

    The bound is enforced here and nowhere else, so there is one place to read
    to know the loop terminates.
    """
    if state.get("disposition") in ("DENIED", "COMPLETE"):
        return {}

    if state.get("iteration_count", 0) >= MAX_AGENT_STEPS:
        return {
            "disposition": "EXHAUSTED",
            "final_response": (
                "I could not complete this within the allowed number of steps, "
                "so I have stopped and flagged it for a person to review."
            ),
            "errors": [f"step limit {MAX_AGENT_STEPS} reached"],
        }

    if state.get("retry_count", 0) > MAX_TOOL_RETRIES:
        return {
            "disposition": "ESCALATE",
            "final_response": (
                "The action could not be completed after repeated attempts and "
                "has been escalated for human review."
            ),
        }

    return {"disposition": "CONTINUE"}


def respond_node(state: AgentState) -> dict:
    if state.get("final_response"):
        return {}
    return {"final_response": "Done."}
