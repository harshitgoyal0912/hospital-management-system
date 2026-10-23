"""Correct the identifier-coherence labels (v1 -> v2).

Phase 21 scored 24 `destructive` cases against a gold answer that was not
achievable: the label passed a human-readable identifier (`C-101-A`, `P-0001`,
`GAUZE-1`) into a schema field defined as an opaque UUID. No single tool accepts
that, so the "correct" answer the benchmark asked for did not exist.

The real workflow is two steps — resolve the human identifier, then act:

    "Discharge bed C-101-A"
      -> get_bed_by_number("C-101-A")  -> bed_id
      -> discharge_bed(bed_id)

So the gold answer becomes the *first* step, matching the convention already
used for `multi_step`.

Resolvers present in the canonical registry:

    bed number      -> get_bed_by_number(bed_number)
    patient number  -> search_patients(patient_number)
    supply code     -> NONE. Only list_supplies, which takes no arguments.

That last row is a real capability gap, not a labelling choice, and is recorded
as `identifier_resolution_gap` rather than quietly assigned a substitute.

v1 is preserved. Both sets stay in the repo so the original run remains
interpretable against the labels it was actually scored on.
"""
import json
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
SRC = HERE / "planner_cases.jsonl"
OUT = HERE / "planner_cases_v2.jsonl"

HUMAN_IDS = {"C-101-A", "C-101-B", "P-0001", "GAUZE-1"}

RESOLVER = {
    "bed_id": ("get_bed_by_number", "bed_number"),
    "patient_id": ("search_patients", "patient_number"),
    "supply_id": (None, None),          # no resolver exists
}

cases = [json.loads(l) for l in SRC.read_text().splitlines() if l.strip()]
changed = gaps = 0

for c in cases:
    args = c.get("expected_arguments") or {}
    hit = next((k for k, v in args.items()
                if k.endswith("_id") and str(v) in HUMAN_IDS), None)
    if not hit:
        continue

    human_value = args[hit]
    tool, field = RESOLVER.get(hit, (None, None))
    c["v1_expected_tool"] = c["expected_tool"]
    c["v1_expected_arguments"] = dict(args)
    c["relabelled"] = "identifier_resolution"

    if tool is None:
        # No way to turn the code into an id. The planner cannot complete this,
        # and pretending otherwise would just move the defect.
        c["category"] = "identifier_resolution_gap"
        c["expected_action"] = "ABSTAIN"
        c["expected_tool"] = None
        c["expected_arguments"] = None
        c["expected_policy"] = None
        c["expected_execution"] = False
        c["note"] = (f"'{human_value}' is a human identifier and no tool resolves "
                     f"it to {hit}; abstain rather than guess a UUID")
        gaps += 1
    else:
        c["category"] = "identifier_resolution"
        c["expected_action"] = "CALL"
        c["expected_tool"] = tool
        c["expected_arguments"] = {field: human_value}
        c["expected_policy"] = "ALLOW"
        c["expected_execution"] = True
        c["note"] = (f"two-step: resolve '{human_value}' via {tool}, then call "
                     f"{c['v1_expected_tool']} with the returned id")
    c["case_set_version"] = "planner-cases-v2"
    changed += 1

for c in cases:
    c.setdefault("case_set_version", "planner-cases-v2")

OUT.write_text("\n".join(json.dumps(c) for c in cases) + "\n")

counts = {}
for c in cases:
    counts[c["category"]] = counts.get(c["category"], 0) + 1
print(f"relabelled {changed} cases ({gaps} as an unresolvable capability gap)")
print(f"wrote {OUT.name}\n")
for k in sorted(counts):
    mark = "  <- new" if k.startswith("identifier_resolution") else ""
    print(f"  {k:28} {counts[k]:>3}{mark}")
