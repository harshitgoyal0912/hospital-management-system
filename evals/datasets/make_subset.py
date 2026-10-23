"""Deterministic 120-case subset for the B/C/D arms.

Groq's free tier caps tokens-per-minute, so the richer configurations cannot
complete the full 238 within today's quota. The subset keeps the ablation
runnable while staying comparable: configuration A already ran all 238, so it is
simply *scored* on these same 120 rather than re-run.

Sampling is stratified and seeded. One deliberate departure from proportional:
all 28 unavailable_capability cases are kept, because substitution rate is the
metric configuration C exists to move, and 14 cases would give it error bars
wider than any effect it could show.
"""
import json
import pathlib
import random

HERE = pathlib.Path(__file__).resolve().parent
CASES = HERE / "planner_cases.jsonl"
OUT = HERE / "planner_subset_120.json"
SEED = 20260923
TARGET = 120
KEEP_ALL = {"unavailable_capability"}

cases = [json.loads(l) for l in CASES.read_text().splitlines() if l.strip()]
by_cat = {}
for c in cases:
    by_cat.setdefault(c["category"], []).append(c)

rng = random.Random(SEED)
chosen, kept_all = [], 0
for cat in KEEP_ALL:
    chosen.extend(by_cat.get(cat, []))
    kept_all += len(by_cat.get(cat, []))

remaining_budget = TARGET - kept_all
pool = {k: v for k, v in by_cat.items() if k not in KEEP_ALL}
pool_total = sum(len(v) for v in pool.values())

for cat, items in sorted(pool.items()):
    take = round(len(items) / pool_total * remaining_budget)
    chosen.extend(rng.sample(items, min(take, len(items))))

# trim or top up to exactly TARGET, deterministically
chosen.sort(key=lambda c: c["case_id"])
while len(chosen) > TARGET:
    droppable = [c for c in chosen if c["category"] not in KEEP_ALL]
    chosen.remove(droppable[-1])
while len(chosen) < TARGET:
    extra = [c for c in cases if c not in chosen and c["category"] not in KEEP_ALL]
    chosen.append(extra[0])

ids = sorted(c["case_id"] for c in chosen)
OUT.write_text(json.dumps({"seed": SEED, "n": len(ids), "case_ids": ids}, indent=2))

counts = {}
for c in chosen:
    counts[c["category"]] = counts.get(c["category"], 0) + 1
print(f"{len(ids)} cases -> {OUT.name}")
for k in sorted(counts):
    marker = "  (all kept)" if k in KEEP_ALL else ""
    print(f"  {k:24} {counts[k]:>3}{marker}")
ab = sum(1 for c in chosen if c["expected_action"] == "ABSTAIN")
print(f"  {'expected ABSTAIN':24} {ab:>3}")
print(f"  {'expected CALL':24} {len(chosen)-ab:>3}")
