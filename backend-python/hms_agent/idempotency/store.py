"""Idempotency store.

Turns "retry the request" into "return the original result" rather than
"perform the operation twice". A retried bed assignment must not produce two
assignments, and a resumed workflow must not re-run the step it already
completed.

The mechanism is a primary-key insert. Application code cannot check-then-act
safely under concurrency; the database can, because the second insert of the
same key fails. Everything here is built on that single guarantee.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from sqlalchemy.exc import IntegrityError

from .models import IdempotencyRecord, RecordStatus


class ArgumentMismatch(Exception):
    """The key was reused with different arguments.

    Serving the earlier result would be wrong (the caller asked for something
    else) and executing would break the guarantee the key was meant to provide.
    So neither happens.
    """

    def __init__(self, key: str, tool: str):
        self.key = key
        self.tool = tool
        super().__init__(
            f"idempotency key '{key}' was already used for '{tool}' with different arguments"
        )


@dataclass(frozen=True)
class Proceed:
    """First time this key has been seen. The caller should execute."""

    key: str


@dataclass(frozen=True)
class Replay:
    """This key already completed. Return the stored outcome; do not execute."""

    key: str
    status: str
    response: Any
    error: str | None
    run_id: str | None

    @property
    def succeeded(self) -> bool:
        return self.status == RecordStatus.SUCCEEDED


@dataclass(frozen=True)
class InFlight:
    """The same key is being processed right now by another request.

    Executing would race; returning a result would be a lie, because there is
    not one yet. The caller must surface this as "in progress", not as success.
    """

    key: str


def hash_arguments(arguments: Mapping[str, Any] | None) -> str:
    payload = json.dumps(arguments or {}, sort_keys=True, default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class IdempotencyStore:
    def __init__(self, session_factory):
        self._session_factory = session_factory

    def begin(
        self,
        key: str,
        tool: str,
        arguments: Mapping[str, Any] | None,
        user_id: str | None = None,
        run_id: str | None = None,
    ) -> Proceed | Replay | InFlight:
        """Claim this key, or report what already happened under it."""
        if not key:
            raise ValueError("idempotency key must not be empty")

        digest = hash_arguments(arguments)
        session = self._session_factory()
        try:
            record = IdempotencyRecord(
                key=key,
                tool=tool,
                user_id=user_id,
                argument_hash=digest,
                status=RecordStatus.IN_FLIGHT,
                run_id=run_id,
            )
            session.add(record)
            session.commit()
            return Proceed(key=key)
        except IntegrityError:
            # Someone else holds this key. Read what they recorded.
            session.rollback()
            existing = session.get(IdempotencyRecord, key)
            if existing is None:
                # Deleted between our insert failing and this read. Treat it as
                # in flight rather than guessing.
                return InFlight(key=key)

            if existing.argument_hash != digest:
                raise ArgumentMismatch(key, existing.tool) from None

            if existing.status == RecordStatus.IN_FLIGHT:
                return InFlight(key=key)

            return Replay(
                key=key,
                status=existing.status,
                response=existing.response,
                error=existing.error,
                run_id=existing.run_id,
            )
        finally:
            session.close()

    def complete(self, key: str, response: Any) -> None:
        self._finish(key, RecordStatus.SUCCEEDED, response=response, error=None)

    def fail(self, key: str, error: str) -> None:
        """Record a failure.

        A failed attempt stays recorded so the outcome is auditable, and a retry
        with the same key replays the failure rather than silently trying again
        under a guarantee it no longer has. A genuine retry uses a new key.
        """
        self._finish(key, RecordStatus.FAILED, response=None, error=error)

    def release(self, key: str) -> None:
        """Remove an in-flight claim, so the key can be retried.

        Only for a request that never reached execution — a policy denial, for
        instance. Never call this after a handler has run.
        """
        session = self._session_factory()
        try:
            record = session.get(IdempotencyRecord, key)
            if record is not None and record.status == RecordStatus.IN_FLIGHT:
                session.delete(record)
                session.commit()
        finally:
            session.close()

    def _finish(self, key: str, status: str, response: Any, error: str | None) -> None:
        session = self._session_factory()
        try:
            record = session.get(IdempotencyRecord, key)
            if record is None:
                return
            record.status = status
            record.response = response
            record.error = error
            record.completed_at = datetime.now(timezone.utc)
            session.commit()
        finally:
            session.close()

    def get(self, key: str) -> IdempotencyRecord | None:
        session = self._session_factory()
        try:
            return session.get(IdempotencyRecord, key)
        finally:
            session.close()
