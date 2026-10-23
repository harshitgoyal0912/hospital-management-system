# Phase 20 — engineering standard

Responsibility split, and where each piece lives. Every row marked DONE has
tests; the gaps are listed honestly at the bottom rather than shaded in.

## LLM

| Responsibility | Where | Status |
|---|---|---|
| Natural-language understanding, planning | `hms_agent/graph/llm_planner.py` | DONE, unverified live |
| Response generation | planner `Plan.response` | DONE |

The planner is the only place a model is consulted, and it may return exactly
one thing: a proposed tool and arguments. It cannot approve, authorise or
execute. Because it sits behind a protocol, the control-flow tests run against
a scripted planner — they measure the graph, not a model.

## Deterministic application code

| Responsibility | Where | Status |
|---|---|---|
| Authorization | `hms_agent/policy/` | DONE |
| Validation | `hms_agent/schemas/` | DONE |
| Safety gates | `hms_agent/execution/` | DONE |
| Idempotency | `hms_agent/idempotency/` | DONE |
| Transactions | `SELECT ... FOR UPDATE` in the agent methods | DONE, proof pending PostgreSQL |

Idempotency rests on a primary-key insert, not application logic: 20 threads
racing for one key yield exactly one execution, because the database arbitrates.

## MCP

| Responsibility | Where | Status |
|---|---|---|
| Controlled capability exposure | `hms_agent/registry.py` | DONE |
| Typed tool interface | `hms_agent/schemas/tools.py` | DONE |
| Execution boundary | `hms_agent/http/`, `hms_agent/transport/` | DONE |

Adding a method to an agent grants no capability: a binding must be declared,
and it must also have a policy entry and an argument schema, or the registry
refuses to start.

## LangGraph

| Responsibility | Where | Status |
|---|---|---|
| Explicit state | `hms_agent/graph/state.py` | DONE |
| Workflow orchestration | `hms_agent/graph/agent.py` | DONE |
| Conditional routing | `route_after_*` | DONE |
| Retries | `decide_node`, `MAX_TOOL_RETRIES` | DONE |
| Human interruption / resumption | `await_approval_node` | DONE |
| Bounded agent loop | `MAX_AGENT_STEPS` | DONE |

`decide` is the only node that routes back to `plan`, so there is one place to
read to know the run terminates. Approval is a genuine suspension via
`interrupt()`: the run stops, its state is checkpointed, and a test resumes it
from a *new graph instance built by a new process-scope* — proving the resume
does not depend on the original object.

One subtlety worth knowing: LangGraph counts supersteps, not planner
iterations, and its default limit of 25 fired before `MAX_AGENT_STEPS` did —
turning a controlled stop into a `GraphRecursionError`. The limit is now derived
from `MAX_AGENT_STEPS`, so the intended bound is the binding one.

## Observability

| Responsibility | Where | Status |
|---|---|---|
| Audit | `hms_agent/audit/` | DONE (PostgreSQL) |
| Tracing (run spans) | `hms_agent/observability/` | DONE |
| Metrics, latency | `MetricsRegistry.snapshot()` | DONE |
| Cost | `estimate_cost` | DONE, unconfigured |

`TOKEN_PRICES_USD_PER_MILLION` ships **empty**. An unknown model costs 0.0, so
the dashboard reads "not measured" rather than showing a plausible number
derived from an invented rate card. Fill it from the provider's published rates
at the time you measure.

OpenTelemetry is the right destination but needs a collector to be useful, and
this deployment has none. `export_otel_spans()` marks the seam: when a collector
exists, that is the only function that changes.

## HTTP integration

`POST /agent/run` and `POST /agent/resume` (`hms_agent/http/agent.py`) put the
agent behind the same controls as the single-tool endpoint. The connection is
one line in `_call_tool`, which routes every tool the agent selects through
`ToolCallService.call_as` — the same registry lookup, schema validation, policy
check, idempotency claim and audit trail as a direct API call.

Policy is therefore evaluated twice: in the graph's `check_policy` node so
routing can react to it, and again at the execution boundary. That defence in
depth initially **deadlocked approvals**: the graph approved an action, then the
boundary re-checked, did not know about the approval, and returned "approval
required" again — so an approved action could never complete.

The fix is `ApprovalGrant`, bound to the tool *and* a hash of its arguments.
Approving "delete patient P1" cannot be replayed to delete P2, a grant for one
tool does not unlock another, and no grant can turn a DENY into an ALLOW.
Tested in `tests/security/test_approval_grant.py`.

Status codes describe what happened to the requested work: 200 completed,
202 awaiting approval (nothing executed), 403 refused, 502 escalated. `executed`
and `completed` are always present, so no client infers outcome from a status.

A second gap surfaced with it: an agent-level denial never reaches the execution
boundary, so it was leaving **no audit record at all**. The policy node now
writes the trail directly.

## Concurrency

Two different races, two different mechanisms, both required:

| Race | Mechanism | Where |
|---|---|---|
| The same request arrives twice | idempotency replay | `hms_agent/idempotency/` |
| Two different requests contend for one row | `SELECT ... FOR UPDATE` | the agent methods |

Neither substitutes for the other. Idempotency cannot help when two genuinely
distinct requests each have a right to run once; locking cannot help when the
same request is retried after its result was already committed.

`assign_bed_to_patient` locks the `beds` row before re-reading `status`, so the
availability check is evaluated against state that cannot move underneath it.
`update_supply_stock` locks the `supplies` row before reading `current_stock`,
so the read-modify-write cannot lose an update.

## Known gaps

* **The row-locking proof has not been executed.** The locks are in place
  (`agents/room_bed_agent.py`, `agents/inventory_agent.py`) and guarded by static
  contract tests, but the nine concurrency tests need PostgreSQL and skip here.
  They must not be run on SQLite: SQLAlchemy silently omits FOR UPDATE there, so
  they would pass without testing anything.
* **A planner exception propagates** out of `graph.invoke`. No tool runs — the
  test proves that — but it is an exception rather than a controlled response.
  The wrapper belongs at the service layer above the graph.
* **The LLM planner has never called a live model.** Menu construction and
  response parsing have unit coverage; a real completion has not been made.
* **The venv does not match `uv.lock`.** PyPI kept timing out during
  `uv sync --extra dev --frozen` (on `hf-xet`, then `reportlab`), so the test
  counts are against locally resolved versions — mcp 1.30.0 and starlette 1.6.0
  rather than the locked 1.12.2 and 0.47.2. Re-run the sync before trusting CI.
* **RAG grounding and citations** (Phases 6-7) are untouched.
* **Nothing has been run against a live server.**
