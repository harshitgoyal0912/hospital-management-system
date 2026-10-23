# Cutover runbook — legacy to guarded execution

The guarded path is wired into `multi_agent_server.py` but **inert by default**.
`TOOL_EXECUTION_MODE` selects the pipeline:

| Mode | `/tools/call` served by | `/v2/tools/call` | `/auth/login` |
|---|---|---|---|
| `legacy` (default) | original handler, unauthenticated | not mounted | not mounted |
| `shadow` | original handler | mounted | mounted |
| `guarded` | **guarded pipeline** | mounted | mounted |

Route precedence is load-bearing: guarded routes are prepended, and Starlette
matches in declaration order, so in `guarded` mode the legacy handler is shadowed.
`tests/integration/test_cutover_routing.py` pins this — including that an
unauthenticated call to `/tools/call` returns 401 rather than executing.

## Prerequisites

1. **Rotate everything that was committed.** `backend-python/.env` and
   `hospital-key.pem` were tracked; untracking them does not remove them from
   history. Treat the EC2 key, database credentials and any API keys as
   compromised.

2. **Set a signing secret.** `TokenIssuer` refuses to start without it:

   ```bash
   export HMS_JWT_SECRET="$(python -c 'import secrets; print(secrets.token_urlsafe(48))')"
   ```

   There is no default. A server configured for `shadow` or `guarded` that cannot
   build the guarded path raises at startup rather than falling back to the open
   path.

3. **Give the seeded users real credentials.** `setup_database.py:53` writes
   literal strings like `hashed_password_101`, which are not bcrypt hashes and
   cannot authenticate anyone:

   ```bash
   python scripts/reset_dev_users.py --list     # audit
   python scripts/reset_dev_users.py --apply    # mint + print once
   ```

   The script refuses a non-local `DATABASE_URL` unless explicitly overridden.

## Sequence

### 1. Staging, shadow mode

```bash
export TOOL_EXECUTION_MODE=shadow
```

`/tools/call` behaves exactly as before. `/auth/login` and `/v2/tools/call` become
available for migration work and live comparison traffic.

### 2. Migrate the frontend — DONE (not yet verified against a live server)

Replace the `localStorage` mock in `frontend/src/services/authService.js`:

```
POST /auth/login  ->  { token }
     store the token
     send `Authorization: Bearer <token>` on every tool call
     POST /v2/tools/call
```

The response envelope changed, deliberately:

| Legacy | Guarded |
|---|---|
| always HTTP 200 | 200 / 202 / 400 / 401 / 403 / 404 / 502 |
| `result.content[0].text` (JSON string) | `result` (parsed) |
| failures nested inside `result` | `success: false`, `executed: false` |
| — | `202` = approval or confirmation required, **not executed** |

Clients must branch on `executed`, and must not read `202` as completion.

### 3. Staging, guarded mode

```bash
export TOOL_EXECUTION_MODE=guarded
```

`/tools/call` is now authenticated and policy-gated. Any client still calling it
without a token receives 401.

### 4. Live comparison

Run `evals/runners/security_boundary_benchmark.py` against the deployed staging
instance in each mode. This replaces the benchmark's ported legacy arm with the
real pipeline and is what turns the current benchmark result into a statement
about the running system.

### 5. Production, then deletion

After production traffic has moved, delete in one commit:

- `call_tool_http` and its `system_tools` branch (`multi_agent_server.py:3276`)
- the `getattr` dispatch in `route_request` (`agents/orchestrator_agent.py:~190`)
- the `"*"` entry in `allow_origins` (`multi_agent_server.py:3527`)

Then rename `/v2/tools/call` to `/tools/call`.

## SSE transport

In `guarded` mode the SSE transport is closed too, via two mechanisms in
`hms_agent/transport/`:

* `RequireBearerAuth` rejects unauthenticated traffic to `/sse` and `/messages`
  before it reaches the MCP machinery, and publishes the verified Principal in a
  context variable.
* `guard_tool_manager` wraps `FastMCP._tool_manager.call_tool` so every SSE tool
  call passes registry membership, schema validation and policy.

**Fail-closed.** If no authenticated Principal is visible when a tool runs —
including if the context variable does not propagate across the transport's task
boundaries — the call is refused. A broken context produces visible denials, not
a silent bypass. Verify this explicitly in staging: an authenticated SSE client
should be able to call `list_beds`, and if it cannot, the context propagation
needs attention rather than the guard being relaxed.

`RequireBearerAuth` is a bare ASGI callable with no `.routes` or
`.add_middleware`, so it wraps the app immediately before `uvicorn.run` — after
route assembly and CORS. Keep that ordering.

## Dependency reproducibility

Fixed as part of this stage, and unrelated to the cutover:

* `pyproject.toml` declared `mcp[cli]>=1.0.0` while the code imports the v1 API
  (`mcp.server.fastmcp`, `multi_agent_server.py:25`). mcp 2.x renamed that
  module, so the constraint had started resolving to an unimportable release.
  Now pinned `<2`.
* The Dockerfile and CI both ran `uv pip install --system -e .`, which
  re-resolves from `pyproject.toml` and **ignores `uv.lock`** — so the lock was
  copied into the image and never used. Both now install from the locked
  resolution.
* `uv.lock` was stale: `langgraph`, `langchain`, `langchain-openai` and
  `chromadb` were declared but absent from it. Regenerated.
* `fastmcp` was declared but never imported. Removed.

`tests/contract/test_dependency_contract.py` pins all of the above.

## Audit persistence

Audit events are written to `agent_audit_events` in PostgreSQL. The table is
created on startup in non-legacy modes (`create_audit_tables`), and lives on its
own declarative Base with portable column types — which is what lets the test
suite exercise the real schema on SQLite without a database server.

One run produces several rows (REQUESTED, AUTHENTICATED, POLICY_DENIED,
NOT_EXECUTED, ...), ordered by `sequence` and keyed by `run_id`, rather than the
single optimistic summary `AgentInteraction` writes.

**Failure policy.** `HMS_AUDIT_STRICT` defaults to `true`, meaning an action that
cannot be audited is not performed: `ToolCallService` writes the EXECUTING event
*before* dispatch, so a failed audit write stops the call instead of producing an
unlogged mutation. Set `HMS_AUDIT_STRICT=false` to degrade to the stderr fallback
instead — events are still emitted, never silently dropped.

Consider whether the audit database role should be INSERT-only at the grant
level. The sink exposes no update or delete path, but that is an application
convention; a grant makes it an infrastructure guarantee.

## Not yet done

- **No idempotency.** Retried mutations are not deduplicated.
- **The server has not been booted.** Both the backend wiring and the frontend
  migration are verified by tests against mocked transports, not a live start.
  Staging is the first place these meet.
- **`/tools/list` is still unauthenticated.** It is read-only, but it advertises
  the whole tool surface and should eventually be scoped per role.
- **Self-service registration is disabled, not replaced.** `signUp` previously
  let a caller choose their own role, which server-side authorization would have
  honoured. There is no `/auth/register` endpoint; accounts are created
  administratively (`scripts/reset_dev_users.py` for development).


## Frontend

`src/services/apiClient.js` is the single place the frontend holds identity and
interprets the response envelope. Everything that calls a tool goes through it.

* Token in `sessionStorage`, not `localStorage` — clinical workstations are
  shared, so a token that dies with the tab is the safer default. Neither
  survives XSS; an httpOnly SameSite cookie is the stronger option if the API
  ever moves to the same origin.
* `exp` is read client-side only to avoid sending a token already known to be
  stale. Verification remains the server's job.
* A 401 clears the session and fires `apiClient.onAuthRequired`, so the app can
  require login again.

**The rule the tests exist to protect:** execution is read from the `executed`
field, never inferred from an HTTP status. A 202 is a successful request for an
action that deliberately did not happen.

`mcpClient.callTool` therefore *throws* `ToolNotExecutedError` for any
non-executed outcome rather than returning a value. Callers already wrap tool
calls in try/catch, and an exception cannot be rendered as "done" — whereas a
returned object can be. `callToolDetailed` returns the outcome without throwing,
for UI that wants to render an "awaiting approval" state explicitly.

Run the frontend suite with `npm test` in `frontend/`.
