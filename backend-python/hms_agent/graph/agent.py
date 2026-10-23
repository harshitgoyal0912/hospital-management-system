"""The agent graph.

    plan ──► check_policy ──┬── DENY ────────────────► respond
                            │
                            ├── approval ──► await_approval ──┬── rejected ──► respond
                            │                    (interrupt)  │
                            │                                 └── approved ──► execute
                            │
                            └── allow ──────────────────────► execute
                                                                  │
                                                     validate_result
                                                                  │
                                                               decide
                                                    ┌─────────────┴─────────────┐
                                              CONTINUE                    terminal
                                                    │                          │
                                                  plan                     respond

Three properties this structure exists to guarantee:

* **The loop is bounded.** `decide` is the only node that routes back to `plan`,
  and it refuses past MAX_AGENT_STEPS. There is one place to read to know the
  run terminates.
* **Approval is a real suspension.** `await_approval` calls LangGraph's
  `interrupt()`, so the run stops and its state is checkpointed. Nothing
  executes while it waits, and resuming needs a separate call carrying a
  decision. It is not a boolean checked inside one request.
* **Policy always precedes execution.** There is no edge from `plan` or
  `await_approval` straight to `execute`.
"""
from __future__ import annotations

from typing import Any, Callable

from langgraph.graph import END, StateGraph
from langgraph.types import interrupt

from ..idempotency.store import hash_arguments
from ..policy import ApprovalGrant, PolicyEngine
from .nodes import (
    decide_node,
    make_execute_node,
    make_plan_node,
    make_policy_node,
    respond_node,
    validate_result_node,
)
from .planner import Planner
from .state import MAX_AGENT_STEPS, AgentState

#: Graph nodes traversed per planner iteration:
#: plan -> check_policy -> execute -> validate_result -> decide
NODES_PER_ITERATION = 5

#: LangGraph counts *supersteps*, not planner iterations, and defaults to 25.
#: Left alone it fires before MAX_AGENT_STEPS does and surfaces as a
#: GraphRecursionError rather than the controlled response the bound exists to
#: produce. Deriving it here keeps MAX_AGENT_STEPS the binding limit and leaves
#: LangGraph's as a backstop.
RECURSION_LIMIT = MAX_AGENT_STEPS * NODES_PER_ITERATION + NODES_PER_ITERATION


def await_approval_node(state: AgentState) -> dict:
    """Suspend until a human decides.

    `interrupt()` raises out of the graph; LangGraph checkpoints the state and
    returns control to the caller. Execution resumes from exactly here when the
    graph is invoked again with a Command(resume=...), so no work before this
    point is repeated and nothing after it has happened.
    """
    decision = interrupt(
        {
            "kind": "approval_required",
            "tool": state.get("selected_tool"),
            "arguments": state.get("tool_arguments"),
            "reason": state.get("policy_reason"),
            "requested_by": state.get("user_id"),
            "role": state.get("role"),
        }
    )

    approved = bool(decision.get("approved")) if isinstance(decision, dict) else bool(decision)
    approver = decision.get("approver") if isinstance(decision, dict) else None

    if approved:
        # Bind the grant to this tool and these exact arguments, so it cannot be
        # replayed against a different target.
        grant = ApprovalGrant(
            tool=state.get("selected_tool") or "",
            approver_id=str(approver or "unknown"),
            approver_role=str(
                decision.get("approver_role") if isinstance(decision, dict) else "unknown"
            ),
            arguments_hash=hash_arguments(state.get("tool_arguments") or {}),
        )
        return {
            "approval_status": "APPROVED",
            "approval_grant": grant.to_dict(),
            "messages": [{"role": "approval", "content": f"approved by {approver or 'unknown'}"}],
        }

    return {
        "approval_status": "REJECTED",
        "disposition": "DENIED",
        "final_response": "The action was not approved, so nothing was carried out.",
        "messages": [{"role": "approval", "content": f"rejected by {approver or 'unknown'}"}],
    }


# -- routers ---------------------------------------------------------------

def route_after_plan(state: AgentState) -> str:
    return "respond" if state.get("selected_tool") is None else "check_policy"


def route_after_policy(state: AgentState) -> str:
    if state.get("policy_decision") == "DENY":
        return "respond"
    if state.get("approval_required"):
        return "await_approval"
    return "execute"


def route_after_approval(state: AgentState) -> str:
    return "execute" if state.get("approval_status") == "APPROVED" else "respond"


def route_after_decide(state: AgentState) -> str:
    return "plan" if state.get("disposition") == "CONTINUE" else "respond"


def build_agent_graph(
    planner: Planner,
    policy_engine: PolicyEngine,
    call_tool: Callable[..., Any],
    checkpointer: Any = None,
    audit_sink: Any = None,
):
    """Compile the agent.

    A checkpointer is required for approval to be resumable; without one,
    `interrupt()` has nowhere to store the suspended run. Callers that do not
    need approval may omit it.
    """
    graph = StateGraph(AgentState)

    graph.add_node("plan", make_plan_node(planner))
    graph.add_node("check_policy", make_policy_node(policy_engine, audit_sink))
    graph.add_node("await_approval", await_approval_node)
    graph.add_node("execute", make_execute_node(call_tool))
    graph.add_node("validate_result", validate_result_node)
    graph.add_node("decide", decide_node)
    graph.add_node("respond", respond_node)

    graph.set_entry_point("plan")

    graph.add_conditional_edges("plan", route_after_plan,
                                {"check_policy": "check_policy", "respond": "respond"})
    graph.add_conditional_edges("check_policy", route_after_policy,
                                {"execute": "execute",
                                 "await_approval": "await_approval",
                                 "respond": "respond"})
    graph.add_conditional_edges("await_approval", route_after_approval,
                                {"execute": "execute", "respond": "respond"})
    graph.add_edge("execute", "validate_result")
    graph.add_edge("validate_result", "decide")
    graph.add_conditional_edges("decide", route_after_decide,
                                {"plan": "plan", "respond": "respond"})
    graph.add_edge("respond", END)

    compiled = graph.compile(checkpointer=checkpointer)
    return compiled.with_config({"recursion_limit": RECURSION_LIMIT})
