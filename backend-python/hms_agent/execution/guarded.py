"""Guarded tool execution.

The existing HTTP path (``multi_agent_server.py:3276``) resolves a tool name
straight onto an agent method and splats client JSON into it. This module is the
replacement boundary: policy is evaluated first, and the handler is looked up and
invoked only for an ALLOW.

It also fixes a reporting defect in the current path, which nests ``{"error":...}``
inside a ``result`` envelope and returns HTTP 200 — so a failed operation reads as
a successful one. Here, outcome is explicit and a failure can never be mistaken for
a success.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Mapping, Protocol

from ..policy import Decision, PolicyDecision, PolicyEngine, Principal


class ToolOutcome(str, Enum):
    SUCCESS = "SUCCESS"
    DENIED = "DENIED"
    AWAITING_APPROVAL = "AWAITING_APPROVAL"
    AWAITING_CONFIRMATION = "AWAITING_CONFIRMATION"
    FAILED = "FAILED"


@dataclass(frozen=True)
class ToolResult:
    outcome: ToolOutcome
    tool: str
    policy: PolicyDecision
    value: Any = None
    error: str | None = None
    latency_ms: int = 0
    metadata: Mapping[str, Any] = field(default_factory=dict)

    @property
    def executed(self) -> bool:
        """True only if the underlying handler actually ran to completion."""
        return self.outcome is ToolOutcome.SUCCESS

    def to_audit(self) -> dict[str, Any]:
        return {
            "tool": self.tool,
            "outcome": self.outcome.value,
            "error": self.error,
            "latency_ms": self.latency_ms,
            **self.policy.to_audit(),
        }


class ToolRegistry(Protocol):
    def resolve(self, tool: str) -> Callable[..., Any] | None: ...


class DictToolRegistry:
    """Simple name -> callable registry."""

    def __init__(self, handlers: Mapping[str, Callable[..., Any]] | None = None):
        self._handlers = dict(handlers or {})

    def register(self, name: str, handler: Callable[..., Any]) -> None:
        self._handlers[name] = handler

    def resolve(self, tool: str) -> Callable[..., Any] | None:
        return self._handlers.get(tool)


_DECISION_TO_OUTCOME = {
    Decision.DENY: ToolOutcome.DENIED,
    Decision.REQUIRE_HUMAN_APPROVAL: ToolOutcome.AWAITING_APPROVAL,
    Decision.REQUIRE_CONFIRMATION: ToolOutcome.AWAITING_CONFIRMATION,
}


class GuardedExecutor:
    """Policy-gated tool dispatch.

    Ordering is the contract: policy is evaluated *before* the handler is even
    resolved, so a denied call cannot reach application code through a bug in
    handler lookup.
    """

    def __init__(
        self,
        registry: ToolRegistry,
        engine: PolicyEngine | None = None,
        audit_sink: Callable[[dict[str, Any]], None] | None = None,
    ):
        self._registry = registry
        self._engine = engine or PolicyEngine()
        self._audit = audit_sink

    def call(
        self,
        principal: Principal,
        tool: str,
        arguments: Mapping[str, Any] | None = None,
    ) -> ToolResult:
        arguments = dict(arguments or {})
        decision = self._engine.check(principal, tool, arguments)

        if decision.blocked:
            result = ToolResult(
                outcome=_DECISION_TO_OUTCOME[decision.decision],
                tool=tool,
                policy=decision,
                error=decision.reason,
            )
            self._emit(result, principal)
            return result

        handler = self._registry.resolve(tool)
        if handler is None:
            result = ToolResult(
                outcome=ToolOutcome.FAILED,
                tool=tool,
                policy=decision,
                error=f"tool '{tool}' is permitted but has no registered handler",
            )
            self._emit(result, principal)
            return result

        started = time.perf_counter()
        try:
            value = handler(**arguments)
            result = ToolResult(
                outcome=ToolOutcome.SUCCESS,
                tool=tool,
                policy=decision,
                value=value,
                latency_ms=int((time.perf_counter() - started) * 1000),
            )
        except Exception as exc:
            result = ToolResult(
                outcome=ToolOutcome.FAILED,
                tool=tool,
                policy=decision,
                error=f"{type(exc).__name__}: {exc}",
                latency_ms=int((time.perf_counter() - started) * 1000),
            )

        self._emit(result, principal)
        return result

    def _emit(self, result: ToolResult, principal: Principal) -> None:
        if self._audit is None:
            return
        entry = result.to_audit()
        entry["user_id"] = principal.user_id
        entry["session_id"] = principal.session_id
        self._audit(entry)
