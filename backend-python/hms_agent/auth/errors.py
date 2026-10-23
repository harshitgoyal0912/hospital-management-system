"""Authentication failures.

Separate types so the transport layer can map them to distinct status codes
without inspecting message strings.
"""


class AuthError(Exception):
    """Base class. Carries no detail that would help an attacker."""

    code = "UNAUTHENTICATED"
    http_status = 401


class MissingToken(AuthError):
    code = "MISSING_TOKEN"


class InvalidToken(AuthError):
    code = "INVALID_TOKEN"


class ExpiredToken(AuthError):
    code = "EXPIRED_TOKEN"
