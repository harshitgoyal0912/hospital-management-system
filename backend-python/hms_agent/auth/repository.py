"""User lookup for authentication.

Behind a protocol so the login path is testable without PostgreSQL, and so the
SQLAlchemy session never leaks into the authentication logic.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class UserRecord:
    """The only user fields authentication is allowed to see."""

    user_id: str
    username: str
    password_hash: str
    role: str
    is_active: bool = True


class UserRepository(Protocol):
    def find_by_username(self, username: str) -> UserRecord | None: ...


class InMemoryUserRepository:
    def __init__(self, users: list[UserRecord] | None = None):
        self._by_name = {u.username.lower(): u for u in (users or [])}

    def add(self, user: UserRecord) -> None:
        self._by_name[user.username.lower()] = user

    def find_by_username(self, username: str) -> UserRecord | None:
        return self._by_name.get((username or "").lower())


class SqlAlchemyUserRepository:
    """Reads the existing `users` table (database.py:84).

    Accepts either a username or an email, because the current frontend signs in
    with whichever the demo rows happened to use.
    """

    def __init__(self, session_factory):
        self._session_factory = session_factory

    def find_by_username(self, username: str) -> UserRecord | None:
        if not username:
            return None
        from database import User  # imported lazily; keeps auth importable without the app

        session = self._session_factory()
        try:
            row: Any = (
                session.query(User)
                .filter((User.username == username) | (User.email == username))
                .first()
            )
            if row is None:
                return None
            return UserRecord(
                user_id=str(row.id),
                username=row.username,
                password_hash=row.password_hash or "",
                role=(row.role or "").strip().lower(),
                is_active=bool(getattr(row, "is_active", True)),
            )
        finally:
            session.close()
