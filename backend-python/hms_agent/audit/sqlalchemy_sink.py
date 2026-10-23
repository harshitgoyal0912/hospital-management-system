"""PostgreSQL-backed audit sink.

Failure policy is explicit, because "the audit write failed" must not silently
become "the action was unlogged":

* ``strict=True`` (the default) raises :class:`AuditWriteError`. Callers that
  audit *before* executing therefore refuse to execute an unauditable action.
* ``strict=False`` degrades to the fallback sink and records the loss, for paths
  where refusing would be worse than proceeding.

Nothing here silently drops an event.
"""
from __future__ import annotations

import logging
import sys
import threading
from typing import Any

from .models import AgentAuditEvent, create_audit_tables
from .trail import AuditEvent

logger = logging.getLogger("hms_agent.audit")


class AuditWriteError(RuntimeError):
    """The audit event could not be persisted."""


class StderrAuditSink:
    """Last-resort sink. Losing an audit event entirely is worse than noise."""

    def write(self, event: AuditEvent) -> None:
        print(f"[AUDIT-FALLBACK] {event.to_dict()}", file=sys.stderr, flush=True)


class SqlAlchemyAuditSink:
    """Appends audit events to `agent_audit_events`."""

    def __init__(
        self,
        session_factory,
        *,
        strict: bool = True,
        fallback: Any | None = None,
        create_tables: bool = False,
        engine=None,
    ):
        self._session_factory = session_factory
        self._strict = strict
        self._fallback = fallback if fallback is not None else StderrAuditSink()
        self._sequence: dict[str, int] = {}
        self._lock = threading.Lock()

        if create_tables:
            if engine is None:
                raise ValueError("create_tables=True requires an engine")
            create_audit_tables(engine)

    def _next_sequence(self, run_id: str) -> int:
        with self._lock:
            nxt = self._sequence.get(run_id, 0) + 1
            self._sequence[run_id] = nxt
            return nxt

    def write(self, event: AuditEvent) -> None:
        row = AgentAuditEvent(
            run_id=event.run_id,
            sequence=self._next_sequence(event.run_id),
            stage=event.stage.value,
            tool=event.tool,
            user_id=event.user_id,
            role=event.role,
            arguments=dict(event.arguments) if event.arguments else None,
            detail=event.detail,
            latency_ms=event.latency_ms,
        )

        session = self._session_factory()
        try:
            session.add(row)
            session.commit()
        except Exception as exc:
            session.rollback()
            self._fallback.write(event)
            logger.error("audit write failed for run %s: %s", event.run_id, exc)
            if self._strict:
                raise AuditWriteError(
                    f"could not persist audit event for run {event.run_id}"
                ) from exc
        finally:
            session.close()

    # -- read side --------------------------------------------------------

    def events_for_run(self, run_id: str) -> list[AgentAuditEvent]:
        session = self._session_factory()
        try:
            return (
                session.query(AgentAuditEvent)
                .filter(AgentAuditEvent.run_id == run_id)
                .order_by(AgentAuditEvent.sequence)
                .all()
            )
        finally:
            session.close()

    def stages_for_run(self, run_id: str) -> list[str]:
        return [e.stage for e in self.events_for_run(run_id)]
