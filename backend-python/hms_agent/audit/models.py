"""Persistent audit schema.

Kept on its own declarative Base rather than added to `database.py` for two
reasons: the audit store is deliberately separable from operational data, and
the column types here are portable, so the table can be created on SQLite for
tests while running on PostgreSQL in production. The 33 models in `database.py`
use the postgresql UUID dialect and cannot do that.

Append-only by construction: this module exposes no update or delete path, and
`AgentAuditEvent` carries no mutable columns.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, Column, DateTime, Index, Integer, String, Text
from sqlalchemy.orm import declarative_base

AuditBase = declarative_base()


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class AgentAuditEvent(AuditBase):
    """One stage in the lifecycle of one tool invocation.

    A single run produces several rows — REQUESTED, AUTHENTICATED, POLICY_DENIED,
    NOT_EXECUTED, and so on — rather than one optimistic summary. That is the
    point: `AgentInteraction` (database.py:320) records
    ``"Successfully executed {tool}"`` before the result is known, so a denied or
    failed call is indistinguishable from a successful one.
    """

    __tablename__ = "agent_audit_events"

    id = Column(String(32), primary_key=True, default=lambda: uuid.uuid4().hex)
    run_id = Column(String(32), nullable=False, index=True)
    sequence = Column(Integer, nullable=False)

    stage = Column(String(32), nullable=False, index=True)
    tool = Column(String(128), nullable=True, index=True)

    user_id = Column(String(64), nullable=True, index=True)
    role = Column(String(32), nullable=True)
    session_id = Column(String(64), nullable=True)

    arguments = Column(JSON, nullable=True)
    detail = Column(Text, nullable=True)
    latency_ms = Column(Integer, nullable=True)

    recorded_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, index=True)

    __table_args__ = (
        Index("ix_audit_run_sequence", "run_id", "sequence", unique=True),
        Index("ix_audit_tool_stage", "tool", "stage"),
    )

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<AgentAuditEvent {self.run_id[:8]} #{self.sequence} {self.stage} {self.tool}>"


def create_audit_tables(engine) -> None:
    """Create the audit table if it does not exist."""
    AuditBase.metadata.create_all(engine)
