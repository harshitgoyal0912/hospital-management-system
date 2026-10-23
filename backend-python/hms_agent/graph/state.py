"""Explicit agent state.

Everything the agent knows lives here, and it is serialisable — which is what
makes a run durable, inspectable and resumable. Nothing important is carried in
a closure or in the LLM's context window.

Note what the state does *not* contain: any field the model can set to grant
itself permission. `policy_decision` is written by the policy engine, read by
the router, and never produced by generation.
"""
from __future__ import annotations

from typing import Annotated, Any, Literal, TypedDict

#: Hard cap on planner iterations in one run. Exceeding it ends the run with a
#: controlled response and an escalation, never an infinite loop.
MAX_AGENT_STEPS = 6

#: How many times a transient tool failure is retried before escalating.
MAX_TOOL_RETRIES = 2

ApprovalStatus = Literal["NOT_REQUIRED", "PENDING", "APPROVED", "REJECTED"]
Disposition = Literal["CONTINUE", "COMPLETE", "ESCALATE", "DENIED", "EXHAUSTED"]


def _append(existing: list | None, new: list | None) -> list:
    """Reducer: accumulate rather than overwrite."""
    return (existing or []) + (new or [])


class AgentState(TypedDict, total=False):
    # -- identity, set once from the verified principal ---------------------
    user_id: str
    role: str
    session_id: str | None

    # -- the request --------------------------------------------------------
    request: str
    patient_id: str | None
    intent: str | None
    entities: dict[str, Any]

    # -- conversation -------------------------------------------------------
    messages: Annotated[list[dict[str, Any]], _append]

    # -- current step -------------------------------------------------------
    selected_tool: str | None
    tool_arguments: dict[str, Any]
    tool_result: Any
    request_id: str | None

    # -- policy, written only by the policy engine --------------------------
    policy_decision: str | None
    policy_reason: str | None
    approval_required: bool
    approval_status: ApprovalStatus
    #: Serialised ApprovalGrant, set once a human approves. Passed to the
    #: execution boundary so the approval it already granted is honoured.
    approval_grant: dict[str, Any] | None

    # -- control ------------------------------------------------------------
    iteration_count: int
    retry_count: int
    disposition: Disposition
    errors: Annotated[list[str], _append]
    executed_tools: Annotated[list[dict[str, Any]], _append]

    # -- output -------------------------------------------------------------
    final_response: str | None
    run_id: str | None


def initial_state(
    *,
    request: str,
    user_id: str,
    role: str,
    run_id: str | None = None,
    session_id: str | None = None,
    patient_id: str | None = None,
) -> AgentState:
    return AgentState(
        request=request,
        user_id=user_id,
        role=role,
        session_id=session_id,
        patient_id=patient_id,
        intent=None,
        entities={},
        messages=[],
        selected_tool=None,
        tool_arguments={},
        tool_result=None,
        request_id=None,
        policy_decision=None,
        policy_reason=None,
        approval_required=False,
        approval_status="NOT_REQUIRED",
        approval_grant=None,
        iteration_count=0,
        retry_count=0,
        disposition="CONTINUE",
        errors=[],
        executed_tools=[],
        final_response=None,
        run_id=run_id,
    )
