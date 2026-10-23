"""Server-issued identity tokens.

Replaces `authService.js`, which mints `mock_token_${id}_${Date.now()}` in the
browser and recovers the role by splitting that string. A role the client can
write is not an authorization signal, so the policy engine cannot be built on it.

Every Principal reaching the policy engine is constructed here, from claims whose
signature this server verified.
"""
from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Any, Mapping

import jwt

from ..policy.decisions import Principal
from .errors import ExpiredToken, InvalidToken, MissingToken

ALGORITHM = "HS256"
DEFAULT_TTL_MINUTES = 60
ISSUER = "hms-agent"
#: Roles the server will mint a token for. A value outside this set is a bug or
#: an attack, never a new capability.
VALID_ROLES = frozenset({"admin", "doctor", "nurse", "manager", "receptionist"})


class TokenIssuer:
    """Issues and verifies bearer tokens."""

    def __init__(self, secret: str | None = None, ttl_minutes: int = DEFAULT_TTL_MINUTES):
        secret = secret or os.getenv("HMS_JWT_SECRET")
        if not secret:
            raise RuntimeError(
                "HMS_JWT_SECRET is not set. Refusing to start with a default signing key."
            )
        if len(secret) < 32:
            raise RuntimeError("HMS_JWT_SECRET must be at least 32 characters")
        self._secret = secret
        self._ttl = timedelta(minutes=ttl_minutes)

    def issue(self, user_id: str, role: str, session_id: str | None = None) -> str:
        if role not in VALID_ROLES:
            raise ValueError(f"refusing to issue a token for unknown role '{role}'")
        now = datetime.now(timezone.utc)
        claims: dict[str, Any] = {
            "sub": str(user_id),
            "role": role,
            "iss": ISSUER,
            "iat": now,
            "exp": now + self._ttl,
        }
        if session_id:
            claims["sid"] = session_id
        return jwt.encode(claims, self._secret, algorithm=ALGORITHM)

    def verify(self, token: str) -> Principal:
        """Return a Principal, or raise. Never returns a partially trusted value."""
        if not token:
            raise MissingToken("no token supplied")
        try:
            claims = jwt.decode(
                token,
                self._secret,
                algorithms=[ALGORITHM],   # pinned: an 'alg: none' header is rejected
                issuer=ISSUER,
                options={"require": ["exp", "iat", "sub", "iss"]},
            )
        except jwt.ExpiredSignatureError as exc:
            raise ExpiredToken("token expired") from exc
        except jwt.InvalidTokenError as exc:
            raise InvalidToken("token failed verification") from exc

        role = claims.get("role")
        if role not in VALID_ROLES:
            # A signed token carrying an unknown role is still not authorization.
            raise InvalidToken("token carries an unrecognised role")

        return Principal(
            user_id=str(claims["sub"]),
            role=role,
            session_id=claims.get("sid"),
        )


def _bearer(header_value: str | None) -> str:
    if not header_value:
        raise MissingToken("Authorization header absent")
    scheme, _, token = header_value.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        raise InvalidToken("Authorization header is not a bearer token")
    return token.strip()


def principal_from_request(headers: Mapping[str, str], issuer: TokenIssuer) -> Principal:
    """Extract and verify identity from request headers.

    Header lookup is case-insensitive because Starlette and raw dicts differ.
    """
    value = None
    for key in ("authorization", "Authorization"):
        if key in headers:
            value = headers[key]
            break
    else:
        try:
            value = headers.get("authorization")  # Starlette Headers
        except AttributeError:
            value = None
    return issuer.verify(_bearer(value))
