"""Idempotency record schema.

Portable column types and its own Base, for the same reason as the audit
schema: the test suite exercises the real table on SQLite while production runs
on PostgreSQL.

The uniqueness guarantee is a database constraint, not application logic. Two
concurrent requests carrying the same key cannot both insert; one loses on the
unique index, and that loss is what makes the second a replay rather than a
second execution.
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import JSON, Column, DateTime, Index, String, Text
from sqlalchemy.orm import declarative_base

IdempotencyBase = declarative_base()


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class RecordStatus:
    IN_FLIGHT = "IN_FLIGHT"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"


class IdempotencyRecord(IdempotencyBase):
    __tablename__ = "agent_idempotency"

    #: Client-supplied request id. Primary key, so the database enforces it.
    key = Column(String(128), primary_key=True)

    tool = Column(String(128), nullable=False)
    user_id = Column(String(64), nullable=True)

    #: Hash of the validated arguments. A retry that reuses a key with
    #: different arguments is a client bug and is rejected rather than served
    #: the earlier result.
    argument_hash = Column(String(64), nullable=False)

    status = Column(String(16), nullable=False, default=RecordStatus.IN_FLIGHT)
    response = Column(JSON, nullable=True)
    error = Column(Text, nullable=True)
    run_id = Column(String(32), nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_idempotency_tool_user", "tool", "user_id"),
        Index("ix_idempotency_created", "created_at"),
    )


def create_idempotency_tables(engine) -> None:
    IdempotencyBase.metadata.create_all(engine)
