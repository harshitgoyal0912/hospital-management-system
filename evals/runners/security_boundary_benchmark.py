"""Security-boundary benchmark: legacy dispatch vs guarded dispatch.

Runs one adversarial scenario suite against two request pipelines and counts
breaches — cases where a handler ran that should not have, or where the caller
was told something untrue about what happened.

HONESTY NOTE, and it matters for how these numbers may be quoted:

  The GUARDED arm is the real `hms_agent` code path, exercised end to end.

  The LEGACY arm is a *faithful port* of the shipped pipeline, not the live
  server — running that needs PostgreSQL, ChromaDB and the full agent stack.
  The port reproduces four behaviours read directly from source:
    1. getattr(agent, tool_name) dispatch      orchestrator_agent.py:~190
    2. inspect.signature kwarg filtering       orchestrator_agent.py:190-197
    3. {"error": ...} nested in `result`,
       returned with HTTP 200                  multi_agent_server.py:3323-3337
    4. traceback.format_exc() in the body      multi_agent_server.py:3341
  Each is asserted in tests/contract/test_legacy_port_fidelity.py.

Run:
    python evals/runners/security_boundary_benchmark.py
"""
from __future__ import annotations

import inspect
import json
import pathlib
import subprocess
import sys
import traceback
from dataclasses import dataclass, field
from datetime import date
from typing import Any, Callable

REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "backend-python"))

from starlette.applications import Starlette                      # noqa: E402
from starlette.testclient import TestClient                        # noqa: E402

from hms_agent.audit import InMemoryAuditSink                      # noqa: E402
from hms_agent.auth import TokenIssuer                             # noqa: E402
from hms_agent.http import ToolCallService, build_guarded_routes   # noqa: E402
from hms_agent.policy import PolicyEngine                          # noqa: E402
from hms_agent.registry import BINDINGS, CanonicalToolRegistry     # noqa: E402

SECRET = "b" * 40


# ---------------------------------------------------------------- handlers

class SpyAgent:
    """Stands in for a real agent. Records anything that executes."""

    def __init__(self, log: list):
        self._log = log

    def _record(self, name, kwargs):
        self._log.append({"tool": name, "args": kwargs})
        return {"ok": True}

    # A representative slice of the real agent surface.
    def list_beds(self, **kw):                     return self._record("list_beds", kw)
    def get_patient_by_id(self, patient_id=None):  return self._record("get_patient_by_id", {"patient_id": patient_id})
    def get_patient_medical_history(self, patient_id=None):
        return self._record("get_patient_medical_history", {"patient_id": patient_id})
    def delete_patient(self, patient_id=None):     return self._record("delete_patient", {"patient_id": patient_id})
    def assign_bed_to_patient(self, bed_id=None, patient_id=None, admission_date=None):
        return self._record("assign_bed_to_patient",
                            {"bed_id": bed_id, "patient_id": patient_id})
    def discharge_bed(self, bed_id=None, discharge_date=None):
        return self._record("discharge_bed", {"bed_id": bed_id})
    def create_patient(self, **kw):                return self._record("create_patient", kw)

    # Not a tool. Present because real agents have non-tool public methods.
    def get_tools(self):                           return self._record("get_tools", {})


# ------------------------------------------------------------ legacy arm

class LegacyPipeline:
    """Port of the shipped /tools/call + route_request behaviour."""

    def __init__(self, agent, executed_log: list):
        self._agent = agent
        self._log = executed_log

    def call(self, role: str, tool: str, arguments: dict) -> dict:
        # The legacy path has no authentication and no policy: role is ignored.
        try:
            method = getattr(self._agent, tool, None)   # (1) reflective dispatch
            if method is None or not callable(method):
                return {"status": 200,
                        "body": {"jsonrpc": "2.0",
                                 "result": {"content": [{"type": "text",
                                            "text": json.dumps({"error": f"unknown tool {tool}"})}]}}}
            sig = inspect.signature(method)             # (2) silent kwarg filtering
            filtered = {k: v for k, v in arguments.items() if k in sig.parameters}
            result = method(**filtered)
            return {"status": 200,
                    "body": {"jsonrpc": "2.0", "result": {"content": [
                        {"type": "text", "text": json.dumps(result)}]}}}
        except Exception as exc:                        # (3)(4) error as 200 + traceback
            return {"status": 200,
                    "body": {"jsonrpc": "2.0",
                             "result": {"content": [{"type": "text", "text": json.dumps(
                                 {"error": str(exc), "traceback": traceback.format_exc()})}]}}}


# ----------------------------------------------------------- guarded arm

class GuardedPipeline:
    def __init__(self, agent, executed_log: list):
        registry = CanonicalToolRegistry({
            b.name: getattr(agent, b.name)
            for b in BINDINGS if hasattr(agent, b.name)
        })
        self._issuer = TokenIssuer(secret=SECRET)
        self.sink = InMemoryAuditSink()
        service = ToolCallService(registry, PolicyEngine(), self._issuer, self.sink)
        self._client = TestClient(Starlette(routes=build_guarded_routes(service)))

    def call(self, role: str, tool: str, arguments: dict) -> dict:
        token = self._issuer.issue("u-bench", role) if role else None
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        r = self._client.post("/v2/tools/call",
                              json={"params": {"name": tool, "arguments": arguments}},
                              headers=headers)
        return {"status": r.status_code, "body": r.json(), "text": r.text}


# ------------------------------------------------------------- scenarios

@dataclass
class Scenario:
    category: str
    role: str | None
    tool: str
    arguments: dict = field(default_factory=dict)
    must_not_execute: bool = True


SCENARIOS: list[Scenario] = []

for tool, args in [("delete_patient", {"patient_id": "P1"}),
                   ("discharge_bed", {"bed_id": "B1"})]:
    for role in ["nurse", "receptionist", "manager"]:
        SCENARIOS.append(Scenario("unauthorized_execution", role, tool, dict(args)))

for probe in ["get_tools", "__class__", "__init__", "os.system", "made_up_tool"]:
    SCENARIOS.append(Scenario("unknown_tool_execution", "admin", probe, {}))

for args in [{"bed_id": "B1", "patient_idd": "P1"},
             {"bed_id": "B1"},
             {"bed_id": "B1", "patient_id": "P1", "role": "admin"},
             {"bed_id": "B1", "patient_id": "P1", "authorized": True}]:
    SCENARIOS.append(Scenario("argument_tampering", "doctor", "assign_bed_to_patient", args))

for role in ["admin"]:
    SCENARIOS.append(Scenario("approval_bypass", role, "delete_patient", {"patient_id": "P1"}))

for tool, args in [("get_patient_medical_history", {"patient_id": "P1"})]:
    SCENARIOS.append(Scenario("clinical_data_access", "receptionist", tool, dict(args)))

SCENARIOS.append(Scenario("unauthenticated_access", None, "list_beds", {}))
SCENARIOS.append(Scenario("unauthenticated_access", None, "delete_patient", {"patient_id": "P1"}))


def run_arm(name: str, pipeline_cls) -> dict[str, Any]:
    executed: list = []
    agent = SpyAgent(executed)
    pipeline = pipeline_cls(agent, executed)

    breaches: dict[str, int] = {}
    totals: dict[str, int] = {}
    details: list[dict] = []

    for sc in SCENARIOS:
        totals[sc.category] = totals.get(sc.category, 0) + 1
        before = len(executed)
        out = pipeline.call(sc.role, sc.tool, dict(sc.arguments))
        ran = len(executed) > before
        if ran and sc.must_not_execute:
            breaches[sc.category] = breaches.get(sc.category, 0) + 1
            details.append({"category": sc.category, "role": sc.role, "tool": sc.tool,
                            "arguments": sc.arguments, "executed": True})

    # Reporting-integrity probes, independent of execution.
    false_success = 0
    traceback_leaks = 0
    for sc in SCENARIOS:
        out = pipeline.call(sc.role, sc.tool, dict(sc.arguments))
        body = out["body"]
        text = out.get("text") or json.dumps(body)
        blob = json.dumps(body)
        # A failure or refusal presented with a 200 and no explicit failure flag.
        if out["status"] == 200 and ("error" in blob.lower()):
            if body.get("success") is not False:
                false_success += 1
        if "Traceback (most recent call last)" in text:
            traceback_leaks += 1

    return {
        "arm": name,
        "scenarios": len(SCENARIOS),
        "totals_by_category": totals,
        "breaches_by_category": breaches,
        "total_breaches": sum(breaches.values()),
        "false_success_responses": false_success,
        "traceback_leaks": traceback_leaks,
        "breach_details": details[:20],
    }


def git_commit() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"],
                                       cwd=REPO, text=True).strip()
    except Exception:
        return "unknown"


def main() -> int:
    legacy = run_arm("legacy_port", LegacyPipeline)
    guarded = run_arm("guarded", GuardedPipeline)

    categories = sorted(set(legacy["totals_by_category"]))
    print(f"\nSecurity boundary benchmark  ({len(SCENARIOS)} scenarios)")
    print(f"{'category':28} {'n':>3}  {'legacy':>8}  {'guarded':>8}")
    print("-" * 54)
    for c in categories:
        n = legacy["totals_by_category"][c]
        lb = legacy["breaches_by_category"].get(c, 0)
        gb = guarded["breaches_by_category"].get(c, 0)
        print(f"{c:28} {n:>3}  {lb:>8}  {gb:>8}")
    print("-" * 54)
    print(f"{'TOTAL breaches':28} {len(SCENARIOS):>3}  "
          f"{legacy['total_breaches']:>8}  {guarded['total_breaches']:>8}")
    print(f"{'false-success responses':28} {'':>3}  "
          f"{legacy['false_success_responses']:>8}  {guarded['false_success_responses']:>8}")
    print(f"{'traceback leaks':28} {'':>3}  "
          f"{legacy['traceback_leaks']:>8}  {guarded['traceback_leaks']:>8}")
    print("\nNOT MEASURED HERE: duplicate mutation under retry (idempotency is")
    print("not yet implemented on the guarded path; see RESULTS.md).")

    out = {
        "measured_on": date.today().isoformat(),
        "commit": git_commit(),
        "legacy_arm_is_a_port": True,
        "legacy": legacy,
        "guarded": guarded,
    }
    path = REPO / "evals" / "results" / "security_boundary_benchmark.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(out, indent=2))
    print(f"\nwrote {path.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
