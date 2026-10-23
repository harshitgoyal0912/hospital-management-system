"""One live planner call, fully instrumented.

Gate 4 of STAGING.md. Makes a real model call and records what the request cost,
what the model proposed, and what the deterministic layers then did with it.

It deliberately stops before execution: the point is to observe the planner and
the checks, not to change hospital state from a probe script.

    export OPENAI_API_KEY=...
    python evals/runners/planner_probe.py --role doctor \
        --request "Which beds are free on the cardiology ward?"

Results append to evals/results/planner_probe.jsonl, so repeated runs accumulate
into something worth summarising rather than overwriting each other.
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import sys
import time
from datetime import datetime, timezone

REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "backend-python"))

# Load backend-python/.env directly rather than relying on the shell. Values
# there are unquoted and contain spaces, so `source`-ing the file breaks.
try:
    from dotenv import load_dotenv

    load_dotenv(REPO / "backend-python" / ".env")
except ImportError:
    pass

RESULTS = REPO / "evals" / "results" / "planner_probe.jsonl"


def count_tokens(text: str, encoding: str = "o200k_base") -> int | None:
    try:
        import tiktoken

        return len(tiktoken.get_encoding(encoding).encode(text))
    except Exception:
        return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--role", required=True,
                        choices=["admin", "doctor", "nurse", "manager", "receptionist"])
    parser.add_argument("--request", required=True)
    parser.add_argument("--user-id", default="probe-user")
    parser.add_argument(
        "--model",
        default=os.getenv("HMS_AGENT_MODEL") or os.getenv("LLM_MODEL") or "gpt-4o-mini",
    )
    parser.add_argument("--repeat", type=int, default=1,
                        help="run the same request N times to observe variance")
    args = parser.parse_args()

    if not os.getenv("OPENAI_API_KEY"):
        print("OPENAI_API_KEY is not set.", file=sys.stderr)
        return 2

    from hms_agent.graph import LLMPlanner, build_tool_menu
    from hms_agent.graph.state import initial_state
    from hms_agent.policy import Decision, PolicyEngine, Principal
    from hms_agent.registry import BINDINGS
    from hms_agent.schemas import UnknownArgument, validate_arguments

    engine = PolicyEngine()
    registry_names = {b.name for b in BINDINGS}
    planner = LLMPlanner(engine, registry_names, model=args.model)

    menu = build_tool_menu(engine, args.role, registry_names)
    menu_tokens = count_tokens(json.dumps(menu))

    state = initial_state(
        request=args.request, user_id=args.user_id, role=args.role, run_id="probe"
    )

    RESULTS.parent.mkdir(parents=True, exist_ok=True)
    rows = []

    for attempt in range(args.repeat):
        record: dict = {
            "at": datetime.now(timezone.utc).isoformat(),
            "model": args.model,
            "role": args.role,
            "request": args.request,
            "attempt": attempt + 1,
            "tools_offered": len(menu),
            "tool_menu_tokens": menu_tokens,
        }

        started = time.perf_counter()
        try:
            plan = planner.plan(state)
            record["latency_ms"] = int((time.perf_counter() - started) * 1000)
        except Exception as exc:
            record.update({
                "latency_ms": int((time.perf_counter() - started) * 1000),
                "outcome": "CALL_FAILED",
                "error": f"{type(exc).__name__}: {exc}",
            })
            rows.append(record)
            continue

        record["proposed_tool"] = plan.tool
        record["proposed_arguments"] = plan.arguments

        if plan.tool is None:
            # Abstention is a legitimate outcome, not a failure. Worth counting
            # separately from a malformed proposal.
            record.update({"outcome": "ABSTAINED", "response": plan.response})
            rows.append(record)
            continue

        if plan.tool not in registry_names:
            record.update({"outcome": "HALLUCINATED_TOOL", "schema_valid": False})
            rows.append(record)
            continue

        try:
            validated = validate_arguments(plan.tool, plan.arguments)
            record["schema_valid"] = True
            record["validated_arguments"] = validated
        except UnknownArgument as exc:
            record.update({"outcome": "SCHEMA_REJECTED", "schema_valid": False,
                           "violations": exc.errors})
            rows.append(record)
            continue

        decision = engine.check(Principal(args.user_id, args.role), plan.tool, validated)
        record["policy_decision"] = decision.decision.value
        record["policy_rule"] = decision.rule_id
        # The probe never executes. It reports what would have happened.
        record["would_execute"] = decision.decision is Decision.ALLOW
        record["executed"] = False
        record["outcome"] = "PLANNED"
        rows.append(record)

    with RESULTS.open("a") as handle:
        for row in rows:
            handle.write(json.dumps(row) + "\n")

    endpoint = os.getenv("OPENAI_API_BASE") or os.getenv("OPENAI_BASE_URL") or "api.openai.com (default)"
    print(f"\nmodel: {args.model}   endpoint: {endpoint}")
    print(f"role: {args.role}   tools offered: {len(menu)} ({menu_tokens} tokens)")
    print(f"request: {args.request}\n")
    for row in rows:
        print(f"  attempt {row['attempt']}: {row.get('outcome')}"
              f"  tool={row.get('proposed_tool')}"
              f"  policy={row.get('policy_decision', '-')}"
              f"  {row.get('latency_ms')}ms")
        if row.get("violations"):
            print(f"    schema violations: {row['violations']}")
        if row.get("error"):
            print(f"    error: {row['error']}")

    outcomes = [r.get("outcome") for r in rows]
    print(f"\n{len(rows)} call(s). "
          f"planned={outcomes.count('PLANNED')} "
          f"abstained={outcomes.count('ABSTAINED')} "
          f"schema_rejected={outcomes.count('SCHEMA_REJECTED')} "
          f"hallucinated={outcomes.count('HALLUCINATED_TOOL')} "
          f"failed={outcomes.count('CALL_FAILED')}")
    print(f"appended to {RESULTS.relative_to(REPO)}")
    print("\nNothing was executed. This probe stops after the policy decision.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
