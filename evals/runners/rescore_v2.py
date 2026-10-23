"""Re-score the recorded runs against the corrected (v2) labels.

No model calls. Every row stored `proposed_tool` and `proposed_arguments`, so
classification can be recomputed offline — which means the label fix costs no
API budget and does not require re-running anything.

The original rows are left untouched. Output goes to planner_eval_v2.jsonl so
both scorings remain inspectable: v1 says what the run was scored as at the
time, v2 says what it should have been scored as.
"""
import json
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "backend-python"))
sys.path.insert(0, str(REPO / "evals" / "runners"))

from run_planner_eval import classify  # noqa: E402

RESULTS = REPO / "evals" / "results" / "planner_eval.jsonl"
OUT = REPO / "evals" / "results" / "planner_eval_v2.jsonl"
CASES_V2 = REPO / "evals" / "datasets" / "planner_cases_v2.jsonl"

cases = {c["case_id"]: c for c in
         (json.loads(l) for l in CASES_V2.read_text().splitlines() if l.strip())}
rows = [json.loads(l) for l in RESULTS.read_text().splitlines() if l.strip()]

from hms_agent.registry import BINDINGS  # noqa: E402
registry = {b.name for b in BINDINGS}

changed = 0
out = []
for r in rows:
    case = cases.get(r["case_id"])
    if case is None or r["classification"] == "CALL_FAILED":
        out.append(r)
        continue
    new = classify(case, r.get("proposed_tool"), r.get("proposed_arguments"),
                   registry, r.get("policy_decision"))
    row = dict(r)
    row["classification_v1"] = r["classification"]
    row["classification"] = new
    row["category"] = case["category"]
    row["expected_action"] = case["expected_action"]
    row["expected_tool"] = case["expected_tool"]
    row["case_set_version"] = "planner-cases-v2"
    if new != r["classification"]:
        changed += 1
    out.append(row)

OUT.write_text("\n".join(json.dumps(r) for r in out) + "\n")
print(f"re-scored {len(rows)} rows, {changed} classifications changed")
print(f"wrote {OUT.relative_to(REPO)}")

import collections
moves = collections.Counter(
    (r["classification_v1"], r["classification"])
    for r in out if r.get("classification_v1") and r["classification_v1"] != r["classification"])
print("\n  what moved:")
for (a, b), n in moves.most_common(10):
    print(f"    {a:22} -> {b:22} {n:>4}")
