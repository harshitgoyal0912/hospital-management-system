"""Audit trail with explicit execution lifecycle.

The existing log writes ``"Successfully executed {tool}"`` before inspecting the
result (orchestrator_agent.py:205), so a denied or failed call is recorded as a
success. A single optimistic event also cannot express the state that matters
most for an agent system: *authorized but deliberately not executed*.

This records a sequence of stages instead, so every run answers three separate
questions: what was asked, what was decided, and what actually happened.
"""
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Iterable, Mapping, Protocol

#: Argument names whose values are never written to the trail.
SENSITIVE_KEYS = frozenset({
    "password", "password_hash", "token", "authorization", "api_key",
    "secret", "ssn", "credit_card",
})

REDACTED = "[REDACTED]"


def redact(data: Mapping[str, Any] | None) -> dict[str, Any]:
    """Shallow-redact sensitive argument values, preserving shape."""
    if not data:
        return {}
    out: dict[str, Any] = {}
    for key, value in data.items():
        if key.lower() in SENSITIVE_KEYS:
            out[key] = REDACTED
        elif isinstance(value, Mapping):
            out[key] = redact(value)
        else:
            out[key] = value
    return out


class AuditStage(str, Enum):
    REQUESTED = "REQUESTED"
    AUTHENTICATED = "AUTHENTICATED"
    AUTHENTICATION_FAILED = "AUTHENTICATION_FAILED"
    VALIDATION_FAILED = "VALIDATION_FAILED"
    POLICY_ALLOWED = "POLICY_ALLOWED"
    POLICY_DENIED = "POLICY_DENIED"
    APPROVAL_REQUIRED = "APPROVAL_REQUIRED"
    APPROVAL_GRANTED = "APPROVAL_GRANTED"
    CONFIRMATION_REQUIRED = "CONFIRMATION_REQUIRED"
    EXECUTING = "EXECUTING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    NOT_EXECUTED = "NOT_EXECUTED"


#: Stages after which no handler ran. Used by tests and by the reporting layer.
NON_EXECUTING = frozenset({
    AuditStage.AUTHENTICATION_FAILED,
    AuditStage.VALIDATION_FAILED,
    AuditStage.POLICY_DENIED,
    AuditStage.APPROVAL_REQUIRED,
    AuditStage.CONFIRMATION_REQUIRED,
    AuditStage.NOT_EXECUTED,
})


@dataclass(frozen=True)
class AuditEvent:
    run_id: str
    stage: AuditStage
    tool: str | None = None
    user_id: str | None = None
    role: str | None = None
    arguments: Mapping[str, Any] = field(default_factory=dict)
    detail: str | None = None
    latency_ms: int | None = None
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "stage": self.stage.value,
            "tool": self.tool,
            "user_id": self.user_id,
            "role": self.role,
            "arguments": dict(self.arguments),
            "detail": self.detail,
            "latency_ms": self.latency_ms,
            "timestamp": self.timestamp,
        }


class AuditSink(Protocol):
    def write(self, event: AuditEvent) -> None: ...


class InMemoryAuditSink:
    """Append-only sink for tests and local runs."""

    def __init__(self) -> None:
        self._events: list[AuditEvent] = []

    def write(self, event: AuditEvent) -> None:
        self._events.append(event)

    @property
    def events(self) -> tuple[AuditEvent, ...]:
        return tuple(self._events)

    def for_run(self, run_id: str) -> tuple[AuditEvent, ...]:
        return tuple(e for e in self._events if e.run_id == run_id)

    def stages(self, run_id: str) -> list[AuditStage]:
        return [e.stage for e in self.for_run(run_id)]


class AuditTrail:
    """Records the lifecycle of one tool invocation."""

    def __init__(self, sink: AuditSink, run_id: str | None = None):
        self._sink = sink
        self.run_id = run_id or uuid.uuid4().hex

    def record(
        self,
        stage: AuditStage,
        *,
        tool: str | None = None,
        user_id: str | None = None,
        role: str | None = None,
        arguments: Mapping[str, Any] | None = None,
        detail: str | None = None,
        latency_ms: int | None = None,
    ) -> AuditEvent:
        event = AuditEvent(
            run_id=self.run_id,
            stage=stage,
            tool=tool,
            user_id=user_id,
            role=role,
            arguments=redact(arguments),
            detail=detail,
            latency_ms=latency_ms,
        )
        self._sink.write(event)
        return event
