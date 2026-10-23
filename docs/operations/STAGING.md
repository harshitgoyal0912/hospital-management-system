# Staging validation

Four things are implemented but unverified outside the test harness. This is the
order to settle them in, and what counts as passing.

Status at time of writing: **Phase 20 implementation complete, staging
validation pending.** Not production-ready — the four gates below are exactly
why.

---

## Gate 1 — the declared environment is reproducible

The current test counts prove the code works against *locally resolved*
dependency versions. They do not prove `uv.lock` works.

```bash
cd backend-python
uv sync --extra dev --frozen
uv run pytest
```

**Passing:** the same count the working tree reports, from the locked
resolution.

**If it fails, separate the two causes before touching anything:**

| Symptom | Cause | Action |
|---|---|---|
| `Failed to download`, `operation timed out`, names a package | network | retry with `UV_HTTP_TIMEOUT=300`; do **not** edit the lock |
| `ModuleNotFoundError`, `ImportError`, a test fails | project | a real bug — fix it |

Do not loosen a pin or regenerate the lock to make this green. The lock is the
artefact under test.

Known drift as of writing: the working venv had mcp 1.30.0 and starlette 1.6.0
while the lock pins 1.12.2 and 0.47.2. Both satisfy the declared ranges, so the
suite has never run against what CI and Docker actually install.

---

## Gate 2 — PostgreSQL serialises competing requests

Nine concurrency tests currently **skip**. They must execute.

```bash
docker run --rm -d --name hms-pg \
  -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=hms_test \
  -p 5432:5432 postgres:16

export TEST_DATABASE_URL=postgresql://postgres:postgres@localhost:5432/hms_test

cd backend-python
uv run pytest tests/integration/test_transaction_locking.py -v
```

**Passing:** 9 passed, 0 skipped. Specifically:

- two requests with different `request_id`s racing for one bed produce exactly
  one assignment;
- two concurrent `-10` decrements from 100 leave **80**, not 90;
- twelve threads each taking 10 from 100 yield exactly ten successes and stock
  floors at 0.

**Do not run these on SQLite.** SQLAlchemy silently omits `SELECT ... FOR UPDATE`
there, so they would pass while testing nothing. The fixtures refuse a
non-PostgreSQL URL for that reason.

Replace "307 passed, 9 skipped" in `RESULTS.md` with the real numbers.

---

## Gate 3 — the guarded path works on a running server

```bash
export HMS_JWT_SECRET="$(python -c 'import secrets;print(secrets.token_urlsafe(48))')"
export DATABASE_URL=postgresql://postgres:postgres@localhost:5432/hms_test
export TOOL_EXECUTION_MODE=guarded

cd backend-python
uv run python scripts/reset_dev_users.py --apply    # seeded hashes are unusable
uv run python multi_agent_server.py
```

Expect on startup:

```
🔒 Guarded execution enabled (mode=guarded, N tools bound, sse=guarded)
🔒 SSE transport requires a bearer token
```

Then, in order:

1. **Unauthenticated call is refused**
   `curl -i -X POST localhost:8000/tools/call -d '{"params":{"name":"list_beds"}}'`
   → **401**, and nothing in the audit table beyond the refusal.

2. **Login works**
   `POST /auth/login` with a credential from the reset script → a token whose
   `role` matches the database row.

3. **Authorised call executes** → 200, `executed: true`, and a row sequence in
   `agent_audit_events` ending `SUCCEEDED`.

4. **Denied call is refused** — a nurse calling `delete_patient` → **403**,
   audit shows `POLICY_DENIED` then `NOT_EXECUTED`, and no `SUCCEEDED`.

5. **SSE carries identity.** This is the one with real uncertainty: the guard
   publishes the verified principal in a `contextvars.ContextVar`, and whether
   that survives the transport's task boundaries has never been observed.

   - Connect to `/sse` without a token → **401**.
   - Connect with a token and call `list_beds` → it should execute.
   - **If it is refused instead, the context variable is not propagating.** That
     is the fail-closed design working. Fix the propagation; do not relax the
     guard to make the call succeed.

6. **Approval round-trip with real persistence**
   `POST /agent/run` proposing a tool that needs approval → **202**,
   `executed: false`. Restart the server. `POST /agent/resume` with the same
   `thread_id` → the tool executes **once**. Surviving the restart is the point;
   an in-process checkpointer would pass a single-process test and fail this.

---

## Gate 4 — the planner makes a real model call

Never done. Until it has, the planner is untested against the thing it exists to
talk to.

```bash
export OPENAI_API_KEY=...
export HMS_AGENT_MODEL=gpt-4o-mini        # or whichever model you are measuring

cd backend-python
uv run python ../evals/runners/planner_probe.py --role doctor \
  --request "Which beds are free on the cardiology ward?"
```

Record, per call:

| Field | Why |
|---|---|
| model | the number means nothing without it |
| prompt tokens / tool-menu tokens | the cost side of the trade below |
| latency ms | |
| proposed tool | |
| proposed arguments | |
| schema validation result | did the boundary accept them |
| policy decision | |
| executed | |
| abstained / malformed | how often it proposes nothing usable |

**Treat the first call as an evaluation point, not a verdict.** One call tells
you the integration works, not that the planner is good.

### The open experiment

Already measured, and it went against expectation:

| prompt | tools | tokens |
|---|---|---|
| baseline, as shipped | 98 | 460 |
| receptionist menu | 14 | 1,404 |
| admin menu | 26 | 2,911 |

Fewer tools cost **more** tokens, because the menus carry descriptions and
argument schemas the baseline omits entirely.

The unanswered question is whether that context improves selection accuracy
enough to justify 3-6x the prompt cost. Answering it needs a labelled scenario
set run against both prompts on the same model. Do not assume the richer prompt
wins.

---

## After the gates

Only once all four pass:

- remove the legacy `/tools/call` handler and the `getattr` dispatch in
  `route_request`;
- drop `"*"` from `allow_origins`;
- re-run the adversarial benchmark against the real pipeline, replacing the
  ported legacy arm with measured numbers.

Still untouched and out of scope until then: RAG grounding and citations.
