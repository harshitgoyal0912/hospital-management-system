"""Convergence of the SSE transport onto the same policy boundary as HTTP.

`mcp.sse_app()` serves the FastMCP tool registry directly, so closing the HTTP
path alone would leave a second, unguarded door onto the same agent methods.

Two pieces:

* :class:`RequireBearerAuth` — ASGI middleware that rejects unauthenticated SSE
  traffic before it reaches the MCP machinery, and publishes the verified
  Principal in a context variable.
* :func:`guard_tool_manager` — wraps ``FastMCP._tool_manager.call_tool`` so every
  SSE tool invocation passes registry membership, schema validation and policy.

**Fail-closed by design.** If no authenticated Principal is visible when a tool
is invoked — including the case where the context variable does not propagate
across the transport's task boundaries — the call is *denied*, not allowed. A
misbehaving context therefore produces visible refusals rather than a silent
bypass. The `sse_requires_principal` test pins this.
"""
from __future__ import annotations

import contextvars
from typing import Any, Awaitable, Callable, Iterable

from ..audit import AuditStage, AuditTrail
from ..auth import AuthError, TokenIssuer
from ..policy import Decision, PolicyEngine, Principal
from ..schemas import UnknownArgument, validate_arguments

#: Set by the middleware, read by the guarded tool manager.
SSE_PRINCIPAL: contextvars.ContextVar[Principal | None] = contextvars.ContextVar(
    "hms_sse_principal", default=None
)


class SseToolDenied(Exception):
    """Raised inside the MCP machinery so the client receives a tool error."""


def _unauthorized_response(status: int, code: str) -> bytes:
    import json

    return json.dumps({"success": False, "executed": False,
                       "error": {"code": code, "message": "authentication required"}}).encode()


class RequireBearerAuth:
    """ASGI middleware enforcing a bearer token on the MCP transport paths."""

    def __init__(
        self,
        app,
        issuer: TokenIssuer,
        protected_prefixes: Iterable[str] = ("/sse", "/messages"),
    ):
        self._app = app
        self._issuer = issuer
        self._prefixes = tuple(protected_prefixes)

    async def __call__(self, scope, receive, send):
        if scope.get("type") != "http":
            await self._app(scope, receive, send)
            return

        path = scope.get("path", "")
        if not path.startswith(self._prefixes):
            await self._app(scope, receive, send)
            return

        headers = {
            k.decode("latin-1").lower(): v.decode("latin-1")
            for k, v in scope.get("headers", [])
        }
        raw = headers.get("authorization", "")
        scheme, _, token = raw.partition(" ")

        if scheme.lower() != "bearer" or not token.strip():
            await self._send_error(send, 401, "MISSING_TOKEN")
            return

        try:
            principal = self._issuer.verify(token.strip())
        except AuthError as exc:
            await self._send_error(send, exc.http_status, exc.code)
            return

        reset_token = SSE_PRINCIPAL.set(principal)
        try:
            await self._app(scope, receive, send)
        finally:
            SSE_PRINCIPAL.reset(reset_token)

    @staticmethod
    async def _send_error(send, status: int, code: str) -> None:
        body = _unauthorized_response(status, code)
        await send({"type": "http.response.start", "status": status,
                    "headers": [(b"content-type", b"application/json"),
                                (b"content-length", str(len(body)).encode())]})
        await send({"type": "http.response.body", "body": body})


def guard_tool_manager(
    mcp: Any,
    engine: PolicyEngine | None = None,
    allowed_tools: Iterable[str] | None = None,
    audit_sink: Any | None = None,
) -> Callable[[], None]:
    """Wrap a FastMCP instance's tool dispatch and listing with the boundary.

    Both are wrapped, not just dispatch. Listing 129 tools while only 26 can be
    executed is a poor contract for any client, and for an LLM client it is
    actively harmful: every unusable name is a plausible thing to propose and
    then be refused. It also discloses the full internal tool surface to anyone
    who can open a session.

    Returns a callable that restores the originals, so tests can undo it.
    """
    engine = engine or PolicyEngine()
    manager = mcp._tool_manager
    original: Callable[..., Awaitable[Any]] = manager.call_tool
    original_list = manager.list_tools
    permitted = frozenset(allowed_tools) if allowed_tools is not None else None

    def guarded_list_tools(*args: Any, **kwargs: Any):
        """Advertise only what this caller could actually execute."""
        tools = original_list(*args, **kwargs)
        if permitted is None:
            return tools

        visible = permitted
        principal = SSE_PRINCIPAL.get()
        if principal is not None:
            # Narrow further to the caller's role. Absent a principal we still
            # never exceed the canonical registry.
            visible = permitted & engine.tools_for_role(principal.role)

        return [t for t in tools if getattr(t, "name", None) in visible]

    async def guarded_call_tool(name: str, arguments: dict, *args: Any, **kwargs: Any):
        trail = AuditTrail(audit_sink) if audit_sink is not None else None

        def record(stage, **fields):
            if trail is not None:
                trail.record(stage, tool=name, **fields)

        record(AuditStage.REQUESTED, arguments=arguments or {})

        principal = SSE_PRINCIPAL.get()
        if principal is None:
            # No verified identity reached this call. Refuse rather than assume.
            record(AuditStage.AUTHENTICATION_FAILED)
            record(AuditStage.NOT_EXECUTED)
            raise SseToolDenied(
                f"'{name}' refused: no authenticated principal on this connection"
            )

        if permitted is not None and name not in permitted:
            record(AuditStage.VALIDATION_FAILED, user_id=principal.user_id,
                   role=principal.role, detail="not in canonical registry")
            record(AuditStage.NOT_EXECUTED)
            raise SseToolDenied(f"'{name}' is not exposed on this transport")

        try:
            validated = validate_arguments(name, arguments or {})
        except UnknownArgument as exc:
            record(AuditStage.VALIDATION_FAILED, user_id=principal.user_id,
                   role=principal.role, detail="schema violation")
            record(AuditStage.NOT_EXECUTED)
            raise SseToolDenied(f"'{name}' rejected: {exc.errors}") from exc

        decision = engine.check(principal, name, validated)
        if decision.decision is Decision.DENY:
            record(AuditStage.POLICY_DENIED, user_id=principal.user_id,
                   role=principal.role, detail=decision.rule_id)
            record(AuditStage.NOT_EXECUTED)
            raise SseToolDenied(f"'{name}' denied: {decision.reason}")

        if decision.decision in (Decision.REQUIRE_HUMAN_APPROVAL,
                                 Decision.REQUIRE_CONFIRMATION):
            stage = (AuditStage.APPROVAL_REQUIRED
                     if decision.decision is Decision.REQUIRE_HUMAN_APPROVAL
                     else AuditStage.CONFIRMATION_REQUIRED)
            record(stage, user_id=principal.user_id, role=principal.role,
                   detail=decision.rule_id)
            record(AuditStage.NOT_EXECUTED)
            # Surfaced as an error, not a result: an agent must never read a
            # pending approval as an observation that the action happened.
            raise SseToolDenied(
                f"'{name}' requires {decision.decision.value}; not executed"
            )

        record(AuditStage.EXECUTING, user_id=principal.user_id, role=principal.role,
               arguments=validated)
        result = await original(name, validated, *args, **kwargs)
        record(AuditStage.SUCCEEDED, user_id=principal.user_id, role=principal.role)
        return result

    manager.call_tool = guarded_call_tool
    manager.list_tools = guarded_list_tools

    def restore() -> None:
        manager.call_tool = original
        manager.list_tools = original_list

    return restore
