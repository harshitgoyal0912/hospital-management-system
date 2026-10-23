"""Login.

Replaces the browser-side mock in `authService.js`. Two properties define this
module:

* **The role is read from the database row, never from the request.** A login
  body claiming ``{"role": "admin"}`` changes nothing.
* **The seeded placeholder hashes cannot authenticate anyone.** `setup_database.py:53`
  writes literal strings like ``hashed_password_101``; `needs_rehash` classifies
  those as unusable so they fail closed rather than matching something.
"""
from __future__ import annotations

import time
from dataclasses import dataclass

from .passwords import needs_rehash, verify_password
from .repository import UserRepository
from .tokens import VALID_ROLES, TokenIssuer

#: A dummy bcrypt hash, verified against when the user does not exist, so that a
#: missing account costs the same time as a wrong password. Without this, response
#: timing enumerates valid usernames.
_DUMMY_HASH = "$2b$12$C6UzMDM.H6dfI/f/IKcEe.3PkGqFYvJ3wQ8y5dQ0mS1rEJ9oQqZ8u"


class LoginFailed(Exception):
    """Deliberately undifferentiated: the caller is never told which check failed."""

    code = "INVALID_CREDENTIALS"
    http_status = 401


@dataclass(frozen=True)
class LoginResult:
    token: str
    user_id: str
    role: str
    expires_in_minutes: int


class LoginService:
    def __init__(
        self,
        repository: UserRepository,
        issuer: TokenIssuer,
        *,
        max_attempts: int = 10,
        window_seconds: int = 300,
    ):
        self._repo = repository
        self._issuer = issuer
        self._max_attempts = max_attempts
        self._window = window_seconds
        self._attempts: dict[str, list[float]] = {}

    def _throttled(self, key: str) -> bool:
        now = time.time()
        recent = [t for t in self._attempts.get(key, []) if now - t < self._window]
        self._attempts[key] = recent
        return len(recent) >= self._max_attempts

    def _record_attempt(self, key: str) -> None:
        self._attempts.setdefault(key, []).append(time.time())

    def authenticate(self, username: str, password: str) -> LoginResult:
        key = (username or "").lower()
        if self._throttled(key):
            raise LoginFailed("too many attempts")

        self._record_attempt(key)
        user = self._repo.find_by_username(username)

        if user is None:
            verify_password(password or "", _DUMMY_HASH)  # equalise timing
            raise LoginFailed("invalid credentials")

        if not user.is_active:
            raise LoginFailed("invalid credentials")

        # A placeholder or non-bcrypt hash is not a credential.
        if needs_rehash(user.password_hash):
            raise LoginFailed("invalid credentials")

        if not verify_password(password or "", user.password_hash):
            raise LoginFailed("invalid credentials")

        role = (user.role or "").strip().lower()
        if role not in VALID_ROLES:
            # A row carrying an unrecognised role is a data problem, not a login.
            raise LoginFailed("invalid credentials")

        token = self._issuer.issue(user_id=user.user_id, role=role)
        return LoginResult(
            token=token,
            user_id=user.user_id,
            role=role,
            expires_in_minutes=int(self._issuer._ttl.total_seconds() // 60),
        )
