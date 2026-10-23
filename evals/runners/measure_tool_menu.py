"""Token cost of the role-scoped tool menu vs the shipped prompt.

Deterministic, no API calls. The baseline is the prompt the frontend actually
builds today (directHttpAiMcpService.js:1377): all 98 tool NAMES comma-joined,
with no descriptions and no schemas.
"""
from __future__ import annotations

import json
import pathlib
import subprocess
import sys
from datetime import date

REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "backend-python"))

import tiktoken  # noqa: E402

from hms_agent.graph import build_tool_menu  # noqa: E402
from hms_agent.policy import PolicyEngine  # noqa: E402
from hms_agent.registry import BINDINGS  # noqa: E402

ENCODING = "o200k_base"
ROLES = ["receptionist", "nurse", "doctor", "manager", "admin"]


def tokens(text: str) -> int:
    return len(tiktoken.get_encoding(ENCODING).encode(text))


def main() -> int:
    baseline_path = REPO / "evals" / "results" / "baseline_tool_surface.json"
    if not baseline_path.exists():
        print("run measure_baseline_tools.py first", file=sys.stderr)
        return 2
    baseline = json.loads(baseline_path.read_text())["report"]
    names_only = baseline["selection_prompt_tokens_names_only"]
    with_desc = baseline["selection_prompt_tokens_with_descriptions"]

    engine = PolicyEngine()
    registry_names = {b.name for b in BINDINGS}

    rows = {}
    print(f"\nTool menu size by role (encoding: {ENCODING})")
    print(f"{'role':14} {'tools':>6} {'tokens':>8}")
    print("-" * 32)
    for role in ROLES:
        menu = build_tool_menu(engine, role, registry_names)
        t = tokens(json.dumps(menu))
        rows[role] = {"tools": len(menu), "tokens": t}
        print(f"{role:14} {len(menu):>6} {t:>8}")

    print("-" * 32)
    print(f"{'BASELINE':14} {baseline['exposed_to_frontend']:>6} {names_only:>8}"
          f"   names only, as shipped")
    print(f"{'':14} {baseline['exposed_to_frontend']:>6} {with_desc:>8}"
          f"   same tools + descriptions")

    print("\nThe baseline carries no argument schemas, so the model cannot know")
    print("what any tool accepts. The role menus do. A smaller tool count")
    print("therefore does not automatically mean fewer tokens -- the comparison")
    print("that matters is tokens against selection accuracy, which needs a")
    print("live model run and is not claimed here.")

    out = {
        "measured_on": date.today().isoformat(),
        "commit": subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=REPO,
                                 capture_output=True, text=True).stdout.strip() or "unknown",
        "encoding": ENCODING,
        "baseline_names_only_tokens": names_only,
        "baseline_with_descriptions_tokens": with_desc,
        "baseline_tool_count": baseline["exposed_to_frontend"],
        "by_role": rows,
    }
    path = REPO / "evals" / "results" / "tool_menu_tokens.json"
    path.write_text(json.dumps(out, indent=2))
    print(f"\nwrote {path.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
