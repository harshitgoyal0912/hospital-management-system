# Architecture Audit — Phase 1

Produced by direct inspection of the repository at commit `f048560` (branch `main`).
Every claim below cites a file and line. Claims made only by existing documentation
and **not** supported by code are listed separately in §3.

---

## 1. Current architecture summary

### 1.1 Actual runtime topology

```text
Browser (React + Vite)
  │
  │  authService.js — MOCK auth, localStorage only, no server involvement
  │  directHttpAiMcpService.js (5,285 lines) — holds ALL tool orchestration
  │  directHttpMcpClient.js — HTTP client
  │
  │  fetch POST /tools/call     <-- unauthenticated
  ▼
FastAPI app wrapped around FastMCP  (multi_agent_server.py:3492 mcp.sse_app())
  │  CORS allow_origins=["*"], allow_credentials=True   (:3517-3530)
  │  Custom routes: /tools/call, /tools/list, /health, /api/bulk-upload
  ▼
OrchestratorAgent (agents/orchestrator_agent.py)
  │  static dict: tool name -> agent  (setup_routing, :83-92)
  ▼
13 registered specialist agents
  │
  ├── SQLAlchemy Session -> PostgreSQL (33 models, database.py)
  ├── ChromaDB PersistentClient (medical_knowledge_db/)
  └── OpenAI API (gpt-4 / gpt-3.5-turbo, hardcoded)
```

**The key structural fact:** the agent loop does not run on the server. It runs in
the browser. `directHttpAiMcpService.js` decides which tools to call, then posts each
one to `/tools/call`. The server is a bare tool executor with no notion of who is
calling or why.

### 1.2 Backend inventory

| File | Lines | Role |
|---|---|---|
| `multi_agent_server.py` | 3,547 | Primary entrypoint. 129 `@mcp.tool` registrations |
| `comprehensive_server.py` | 1,283 | Alternate server. 33 `@mcp.tool` |
| `server.py` | 297 | Third server. 6 `@mcp.tool` |
| `client.py` | 2,222 | Interactive CLI client |
| `database.py` | 999 | 33 SQLAlchemy models |
| `agents/*.py` | 13,700 | 25 agent modules |

Three separate MCP server entrypoints with overlapping tool registrations.
`setup_database_broken_backup.py` (2,452 lines) is dead.

### 1.3 Database

33 models. Well-developed for inpatient operations: `Patient`, `Bed`, `Room`,
`Staff`, `Equipment`, `Supply`, `InventoryTransaction`, `DischargeReport`,
`BedTurnover`, `PatientQueue`, `TreatmentRecord`, `MedicalDocument`,
`ExtractedMedicalData`, `DocumentEmbedding`.

`User.role` exists (`database.py:92`) with values `admin, doctor, nurse, manager,
receptionist`. **This is the only existing foundation for a policy engine.**

`AgentInteraction` (`database.py:320-336`) already captures `agent_type`, `user_id`,
`query`, `response`, `action_taken`, `confidence_score`, `execution_time_ms`.
This is a partial audit-log foundation and should be extended rather than replaced.

Engine config (`database.py:22`) is `create_engine(DATABASE_URL)` with **no pool
tuning, no isolation level set, and no locking helpers anywhere in the codebase.**

---

## 2. Existing AI / LangGraph features

### 2.1 What is genuinely implemented

`agents/langraph_workflows.py` (909 lines) — real, compiled `StateGraph`s:

- **Patient admission** (`:95-129`): 8 nodes, one conditional edge on bed
  availability. Compiled at `:129`.
- **Clinical decision** (`:586-605`): 6 nodes, linear. Compiled at `:605`.
- **Document processing**: third graph in same module.

Typed state via `TypedDict`: `PatientAdmissionState`, `ClinicalDecisionState`,
`DocumentProcessingState` (`:43-67`).

### 2.2 The critical limitation

**Both live graphs compile with no checkpointer** (`:129`, `:605`).

No checkpointer means no durable state, no `interrupt_before`/`interrupt_after`,
and therefore **human-in-the-loop as specified in Phase 5 is currently impossible** —
not partially implemented, structurally unavailable.

`MemorySaver` is imported in `enhanced_orchestrator_agent.py:15` and
`master_integration_system.py:17`, but both are in-process only (lost on restart,
not shared across workers) and both modules sit on code paths that are imported but
whose graph builders are largely stubs.

### 2.3 Stub workflows

Five agents declare workflow builders where only the first is implemented and the
remainder are bare `pass`:

| Agent | Implemented | Stubbed |
|---|---|---|
| `predictive_analytics_agent.py` | `build_demand_forecasting_workflow` | 3 (`:407`, `:412`, `:417`) |
| `multilingual_support_agent.py` | `build_medical_translation_workflow` | 3 (`:455`, `:460`, `:465`) |
| `real_time_monitoring_agent.py` | `build_monitoring_workflow` | 3 (`:373`, `:378`, `:383`) |
| `master_integration_system.py` | `build_unified_request_workflow` | 3 (`:481`, `:486`, `:491`) |
| `equipment_lifecycle_agent.py` | `build_lifecycle_management_workflow` | 4 (`:490`-`:505`) |

**17 stubbed workflow builders.** Each returns `None`, so any caller that invokes
one and then calls `.invoke()` raises `AttributeError` at runtime.

### 2.4 LLM integration

- `gpt-4` hardcoded: `langraph_workflows.py:32`, `enhanced_ai_clinical.py:29`,
  `equipment_lifecycle_agent.py:150`, `master_integration_system.py:177`
- `gpt-3.5-turbo` hardcoded: `ai_clinical_assistant_agent.py:208`
- `ai_clinical_assistant_agent.py:102` reads `VITE_OPENAI_API_KEY` — a Vite-prefixed
  variable, meaning the same key is bundled into shipped browser JavaScript.

### 2.5 RAG

ChromaDB `PersistentClient` (`medical_document_agent.py:137`), collection queried at
`:513`, documents added at `:853`.

`SentenceTransformer` is **commented out** (`:18`, `:76`, `:118`) and excluded from
`pyproject.toml` ("Temporarily commented out for deployment - large model
dependencies"). The collection therefore runs on ChromaDB's default embedding
function, not the intended medical-domain embeddings.

No retrieval evaluation, no citations returned to the caller, no abstention path.

---

## 3. Documented but NOT implemented

| Claim | Source | Reality |
|---|---|---|
| "Appointment Scheduling: Book and manage patient appointments" | `README.md` | **No `Appointment` model exists.** `meeting_scheduler.py:604`: "Since appointments are removed". `discharge_report_service.py:378-392` has the Appointment query commented out. |
| "`/api/appointments/` endpoint" | `README.md` | Route does not exist |
| "Security Features: CORS protection" | `README.md` | `allow_origins` includes `"*"` (`multi_agent_server.py:3527`) |
| Advanced agents (predictive, multilingual, monitoring) | `LANGCHAIN_LANGGRAPH_FEATURES_GUIDE.md` | 17 of their workflow builders are `pass` |

---

## 4. Existing MCP / tool capabilities

- **129** `@mcp.tool` in `multi_agent_server.py`, **33** in `comprehensive_server.py`,
  **6** in `server.py`.
- **98** tools reach the frontend (`tools_list.json`).
- Transport: **SSE only** (`mcp.sse_app()`, `:3492`). No stdio transport, so standard
  MCP clients (Claude Desktop, `mcp` CLI) cannot connect. `.vscode/mcp.json` exists
  but the server does not speak the transport it would need.
- Tool selection prompt (`directHttpAiMcpService.js:1377`) passes **tool names only**,
  comma-joined — no descriptions, no argument schemas.
- A parallel hand-written keyword/regex matcher, `determineToolsNeeded()`
  (`:1431` onward), runs alongside GPT-4 function calling. Two competing selection
  paths, neither measured.

### Tool quality against the Phase 2 bar

| Requirement | Status |
|---|---|
| Strong input schema | Partial — Python type hints only, no Pydantic models |
| Strong output schema | **Missing** — tools return ad-hoc dicts |
| Input validation | **Missing** |
| Error handling | Inconsistent — mix of exceptions and `{"success": false}` |
| Authentication context | **Missing** |
| Authorization context | **Missing** |
| Structured errors | **Missing** |
| Logging | `print()` statements only |
| Tests | **None** |

---

## 5. Existing tests

**Zero.** No test, eval, or benchmark file exists anywhere in the repository.
No `pytest` dependency in `pyproject.toml`. No `conftest.py`.

`.github/workflows/deploy.yml` has a job named `test` (`:32`) and `deploy` declares
`needs: test` (`:90`) — but the job's only substantive check is that ReportLab can
generate a PDF (`:68-79`). **No application code is exercised before deploy.**

`evals/` currently contains three empty `.gitkeep` directories from a prior session.

---

## 6. Security posture (findings that gate later phases)

1. **`POST /tools/call` is unauthenticated.** Any client that can reach the host can
   invoke any of the 129 tools, including `delete_patient`, `delete_staff`,
   `discharge_bed`, `update_supply_stock`.
2. **CORS is `"*"` with `allow_credentials=True`** (`:3527-3529`).
3. **Authentication is entirely client-side fiction.** `authService.js` seeds demo
   users into `localStorage` (`:17-52`) and mints `mock_token_${id}_${Date.now()}`
   (`:111`). `getUserProfile` parses the role back out of that string (`:190-208`).
   The server never sees, issues, or validates a token.
4. **Consequence for Phase 4:** a policy engine cannot be built on a role the client
   asserts. Server-side identity is a hard prerequisite, not an optional extra.
5. Secrets committed to the public repo: `backend-python/.env`, `hospital-key.pem`.

---

## 7. Proposed implementation plan

Ordered by dependency. Each stage ends with committed tests and, where the stage
claims an improvement, a measured before/after in `RESULTS.md`.

### Stage 0 — Secret remediation and baseline harness
Rotate the committed EC2 key and `.env` credentials. Add `pytest`, `conftest.py`,
Postgres test fixtures, and a real CI test gate. **Record the baseline**: current
tool-selection behaviour, prompt token count, latency. No behaviour changes.

### Stage 1 — Typed tool layer
Introduce Pydantic input/output models and a structured error envelope. Wrap
existing agent methods rather than rewriting them. Start with the ~25 tools the
evaluation will exercise, not all 129.

### Stage 2 — Server-side identity
Real authentication issuing a signed token carrying `user_id` and `role`.
`/tools/call` requires it. This unblocks Stages 3 and 5.

### Stage 3 — Policy engine
Deterministic `policy.check(role, tool, args) -> ALLOW | DENY | REQUIRE_CONFIRMATION
| REQUIRE_HUMAN_APPROVAL`, enforced **before** handler dispatch. Tests must prove the
handler and the database are never reached on DENY.

### Stage 4 — Audit log
Extend `AgentInteraction` (or add `agent_audit_events`) with `run_id`, `tool`,
`arguments`, `policy_decision`, `approval_status`, `result`, `error`, `latency_ms`.
Redact credentials. Append-only.

### Stage 5 — Idempotency and transaction safety
`request_id` on every mutating tool, unique-constrained. Row-level locking
(`SELECT ... FOR UPDATE`) for `assign_bed` and `update_supply_stock`. Concurrency
tests that measure double-booking before and after.

### Stage 6 — Server-side LangGraph agent
Move the loop out of the browser. Explicit `AgentState`, bounded at
`MAX_AGENT_STEPS`, with a Postgres checkpointer so runs are durable and resumable.

### Stage 7 — Human-in-the-loop
`interrupt_before` the execution node when policy returns `REQUIRE_HUMAN_APPROVAL`.
Approve/reject endpoints resume the graph from the checkpoint. Resumption must
survive a process restart — that is the test.

### Stage 8 — Hierarchical tool routing
Two-stage selection (agent, then tool). Measure accuracy, prompt tokens, latency.

### Stage 9 — RAG evaluation and grounding
Restore real embeddings. Labelled query set. Dense vs BM25 vs hybrid RRF on
Recall@k / MRR / nDCG@3. Citations in tool output. Abstention on out-of-corpus.

### Stage 10 — Groundedness / claim validation
Split clinical responses into claims; verify patient-fact claims against the
database and knowledge claims against retrieved evidence. Qualify or escalate
unsupported claims. Log every verdict.

### Stage 11 — Failure injection
Fault-injection fixtures for LLM / DB / Chroma / MCP unavailability and timeouts.
Assert bounded retries, controlled failure messages, escalation, and audit events.
Assert the system never reports success for an operation that did not commit.

### Stage 12 — Evaluation harness and baseline comparison
150-300 labelled scenarios. Run the **same** benchmark against the browser-orchestrated
baseline and the guarded architecture. Report both.

### Stage 13 — Observability
OpenTelemetry spans per agent run. Metrics for runs, success, escalations, policy
blocks, latency p50/p95, tool calls, tokens, cost.

### Stage 14 — Documentation
Rewrite README around the engineering problem. Architecture diagram. Measured
results only.

**Appointments are deliberately excluded** — see §9.

---

## 8. Files affected

### Modified
```text
backend-python/database.py              + audit / idempotency / approval models
backend-python/multi_agent_server.py    auth + policy gate at dispatch; CORS fix
backend-python/agents/langraph_workflows.py   add checkpointer + interrupts
backend-python/agents/orchestrator_agent.py   two-stage routing
backend-python/agents/medical_document_agent.py  real embeddings, citations
backend-python/agents/ai_clinical_assistant_agent.py  claim verification
backend-python/pyproject.toml           pytest, otel, bm25, auth deps
.github/workflows/deploy.yml            real test gate
frontend/src/services/directHttpAiMcpService.js  thin client; loop moves server-side
frontend/src/services/authService.js    real tokens
README.md                               rewritten
```

### Created
```text
backend-python/hms_agent/
    schemas/           Pydantic tool input/output models
    tools/             typed MCP tool wrappers
    policy/            engine, rules, decisions
    auth/              token issue/verify, role resolution
    audit/             append-only audit writer
    idempotency/       request_id store
    graph/             AgentState, nodes, bounded loop, checkpointer
    rag/               retrievers, rerank, citations, abstention
    grounding/         claim extraction + verification
    observability/     otel setup, metrics
    failures/          fault injection
backend-python/tests/
    unit/ integration/ security/ failure/ contract/
evals/
    datasets/  scenarios.jsonl, rag_queries.jsonl
    redteam/   injection + unauthorized suites
    runners/   run_agent_eval.py, run_rag_eval.py, run_baseline.py
    results/   raw JSON, committed
ARCHITECTURE.md
```

### Deleted
```text
backend-python/setup_database_broken_backup.py
backend-python/agents/dashboard_agent_backup.py
frontend/src/components/*_backup.jsx, *_broken.jsx, "DirectMCPChatbot copy.jsx"
```

---

## 9. Evaluation strategy

### Scope decision: appointments
Phase 2 of the brief specifies `book_appointment`, `find_available_slots`,
`cancel_appointment`, `reschedule_appointment`. **None of this exists** — the
Appointment model was removed from the codebase. Building it would be CRUD work that
demonstrates nothing about agent safety.

The evaluation therefore targets the operations the system actually performs:
**bed assignment, discharge, staff assignment, supply/inventory, patient records,
and medical-document retrieval.** Bed assignment is the better subject anyway: it
has a real concurrency hazard, a real authorization boundary, and a real
patient-safety consequence.

### Dataset
150-300 labelled scenarios, each `{query, role, gold_tool, gold_args, expected_outcome}`:

| Category | ~n | Purpose |
|---|---|---|
| Bed / resource allocation | 45 | tool + argument accuracy |
| Patient record operations | 40 | retrieval and update correctness |
| Staff assignment | 25 | multi-step workflows |
| Supply / inventory | 25 | mutation + idempotency |
| Clinical decision support | 30 | RAG grounding, citations, abstention |
| Unauthorized / injection | 45 | policy enforcement |
| Failure injection | 35 | controlled degradation |
| Ambiguous / underspecified | 25 | clarification vs guessing |

Split by **scenario group**, not by row, to prevent template leakage between
train-time prompt tuning and evaluation.

### Metrics
Agent: tool-selection accuracy@1, argument exactness, workflow completion,
**unauthorized-execution rate** (must be 0), policy-block precision, escalation rate,
hallucinated-success rate, latency p50/p95, tool calls per run, tokens, cost/query.

RAG: Recall@k, MRR, nDCG@3, citation accuracy, groundedness, abstention accuracy at
a fixed false-abstention budget.

### Baseline comparison
Same dataset, two systems:
- **A (baseline):** current browser orchestration — names-only prompt, direct
  `/tools/call`, no policy.
- **B (guarded):** LangGraph + typed tools + policy + validation + audit.

Report both, including any metric where B is worse (latency and cost almost
certainly will be — that tradeoff is the finding, not a failure).

### Reproducibility
Pinned model version and `temperature=0`; fixed seeds; committed datasets; raw
per-run JSON in `evals/results/`; every number in `RESULTS.md` regenerable by a
named script. Three repeats per config with variance reported, because LLM
evaluation at n=1 is noise.

---

## 10. Addendum — the dispatch path (measured after §1 was written)

`POST /tools/call` (`multi_agent_server.py:3276-3345`) **does not go through the
FastMCP registry.** For any tool outside a 13-entry `system_tools` list it calls:

```python
result = orchestrator.route_request(tool_name, **arguments)
```

`route_request` (`agents/orchestrator_agent.py:180-215`) resolves the target with
`getattr(agent, tool_name)` and invokes it, filtering kwargs by
`inspect.signature`.

Four consequences, each verified in source:

1. **The `@mcp.tool` decorators are inert on the HTTP path.** Any schema handling
   FastMCP would apply is bypassed. This explains why 17 tools advertised in
   `tools_list.json` — including `delete_patient`, `delete_staff`, `delete_room`,
   `update_patient` — resolve to no `@mcp.tool` registration yet remain callable:
   they exist as agent methods (`agents/patient_agent.py:319`,
   `agents/staff_agent.py:335`, `agents/patient_agent.py:250`).
   **The reachable attack surface is the union of all agent methods, not the 129
   decorated functions.**

2. **Client JSON is splatted into a Python method** with no validation. Because
   `route_request` *filters* unknown kwargs instead of rejecting them, a caller
   supplying wrong or misspelled argument names gets the tool executed with its
   defaults rather than an error.

3. **Full tracebacks are returned to the client.** The 500 response body includes
   `traceback.format_exc()` (`:3341`).

4. **Failures are reported as successes.** When agent routing raises, the handler
   returns `{"error": ...}` nested inside a `result` envelope with HTTP 200
   (`:3323-3337`). A caller — including the LLM — sees a well-formed JSON-RPC
   result for an operation that did not happen. This is the Phase 10 hazard
   ("never hallucinate successful execution") occurring at the transport layer,
   before the model is involved.

Additionally, `route_request` writes its audit entry as
`response=f"Successfully executed {tool_name}"` (`:205`) **before inspecting the
result**, so the existing `AgentInteraction` log records success unconditionally.

### Baseline measurement (reproducible)

`python evals/runners/measure_baseline_tools.py` → `evals/results/baseline_tool_surface.json`

| Measure | Value |
|---|---|
| `@mcp.tool` registrations | 168 across 3 server files (134 unique names) |
| Tools advertised to frontend | 98 |
| ...resolving to an `@mcp.tool` registration | 81 |
| ...callable only as agent methods | 17 |
| Exposed tools whose source has a docstring | 81 / 81 (100%) |
| Selection prompt, names only (as shipped) | 460 tokens |
| Selection prompt, same tools with descriptions | 1,225 tokens |

**Correction to a prior note in this repo:** the tools are not missing
descriptions. Every one of the 81 resolvable tools has a docstring. The frontend
*discards* them when building the selection prompt. The information the model needs
to choose correctly already exists and is thrown away — a stronger and cheaper
finding than the tools being undocumented.
