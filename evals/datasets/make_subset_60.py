"""60-case subset for the B and C arms.

Groq's free tier allows ~200,000 tokens per day for one model. Configuration B
costs ~1,311 tokens per case and C ~1,340, so 60 cases across both arms is
~159,000 — the largest common subset that completes within one day's budget.

All 28 unavailable_capability cases are retained. Substitution rate is the
metric configuration C exists to move, and it is the headline finding from
configuration A (0.643); measuring it on a reduced sample would widen its error
bars past the size of any effect C could show.

Configuration A already ran all 238 cases, so it is scored on these same 60
rather than re-run.
"""
import json
import pathlib
import random

HERE = pathlib.Path(__file__).resolve().parent
cases = [json.loads(l) for l in (HERE / "planner_cases.jsonl").read_text().splitlines() if l.strip()]

KEEP_ALL = "unavailable_capability"
TARGET = 60
rng = random.Random(20260923)

chosen = [c for c in cases if c["category"] == KEEP_ALL]
others = [c for c in cases if c["category"] != KEEP_ALL]

by_cat = {}
for c in others:
    by_cat.setdefault(c["category"], []).append(c)

budget = TARGET - len(chosen)
total = len(others)
for cat, items in sorted(by_cat.items()):
    take = max(1, round(len(items) / total * budget))
    chosen.extend(rng.sample(items, min(take, len(items))))

chosen.sort(key=lambda c: c["case_id"])
while len(chosen) > TARGET:
    chosen.remove([c for c in chosen if c["category"] != KEEP_ALL][-1])

ids = sorted(c["case_id"] for c in chosen)
out = HERE / "planner_subset_60.json"
out.write_text(json.dumps({"seed": 20260923, "n": len(ids), "case_ids": ids}, indent=2))

counts = {}
for c in chosen:
    counts[c["category"]] = counts.get(c["category"], 0) + 1
print(f"{len(ids)} cases -> {out.name}")
for k in sorted(counts):
    print(f"  {k:24} {counts[k]:>3}" + ("  (all kept)" if k == KEEP_ALL else ""))
ab = sum(1 for c in chosen if c["expected_action"] == "ABSTAIN")
print(f"  {'expected ABSTAIN':24} {ab:>3}")
print(f"  {'expected CALL':24} {len(chosen)-ab:>3}")
