"""Static baseline measurement of the MCP tool surface.

Measures what the repository actually exposes today, with no LLM calls, so the
numbers are deterministic and reproducible. Writes JSON to evals/results/.

Run:
    python evals/runners/measure_baseline_tools.py
"""
from __future__ import annotations

import ast
import json
import pathlib
import subprocess
import sys
from datetime import date

REPO = pathlib.Path(__file__).resolve().parents[2]
BACKEND = REPO / "backend-python"
RESULTS = REPO / "evals" / "results"

SERVER_FILES = [
    "multi_agent_server.py",
    "comprehensive_server.py",
    "server.py",
]

ENCODING = "o200k_base"


def is_mcp_tool(node: ast.FunctionDef) -> bool:
    for dec in node.decorator_list:
        target = dec.func if isinstance(dec, ast.Call) else dec
        if isinstance(target, ast.Attribute) and target.attr == "tool":
            return True
    return False


def scan_server(path: pathlib.Path) -> list[dict]:
    """Extract every @mcp.tool function with its docstring and parameters."""
    tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
    tools = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if not is_mcp_tool(node):
            continue
        doc = ast.get_docstring(node)
        params = [a.arg for a in node.args.args if a.arg != "self"]
        annotated = sum(1 for a in node.args.args if a.arg != "self" and a.annotation)
        tools.append(
            {
                "name": node.name,
                "file": path.name,
                "line": node.lineno,
                "has_description": bool(doc and doc.strip()),
                "description_chars": len(doc.strip()) if doc else 0,
                "param_count": len(params),
                "annotated_param_count": annotated,
            }
        )
    return tools


def count_tokens(text: str) -> int:
    import tiktoken

    return len(tiktoken.get_encoding(ENCODING).encode(text))


def frontend_exposed_tools() -> list[str]:
    path = REPO / "evals" / "datasets" / "tools_list.json"
    if not path.exists():
        return []
    data = json.loads(path.read_text())
    names: list[str] = []

    def walk(o):
        if isinstance(o, dict):
            if "name" in o and ("description" in o or "inputSchema" in o):
                names.append(o["name"])
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)

    walk(data)
    return names


def git_commit() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], cwd=REPO, text=True
        ).strip()
    except Exception:
        return "unknown"


def main() -> int:
    all_tools: list[dict] = []
    per_file = {}
    for name in SERVER_FILES:
        path = BACKEND / name
        if not path.exists():
            continue
        tools = scan_server(path)
        per_file[name] = len(tools)
        all_tools.extend(tools)

    exposed = frontend_exposed_tools()

    # Reconstruct the selection prompt the frontend actually builds today:
    # directHttpAiMcpService.js ~line 1377 comma-joins tool NAMES only.
    names_only_prompt = "Available tools: " + ", ".join(exposed)
    names_only_tokens = count_tokens(names_only_prompt)

    # Counterfactual: the same tool list carrying its real descriptions.
    doc_by_name = {t["name"]: t for t in all_tools}
    with_desc_lines = []
    for n in exposed:
        d = doc_by_name.get(n, {})
        desc = (d.get("description_chars") or 0) and "" or ""
        with_desc_lines.append(n)
    # Build from actual docstrings where available.
    described = []
    for n in exposed:
        t = doc_by_name.get(n)
        if t and t["has_description"]:
            src = (BACKEND / t["file"]).read_text(errors="replace")
            tree = ast.parse(src)
            doc = ""
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == n:
                    doc = (ast.get_docstring(node) or "").strip().split("\n")[0]
                    break
            described.append(f"- {n}: {doc}")
        else:
            described.append(f"- {n}: (no description)")
    with_desc_prompt = "Available tools:\n" + "\n".join(described)
    with_desc_tokens = count_tokens(with_desc_prompt)

    exposed_set = set(exposed)
    exposed_tools = [t for t in all_tools if t["name"] in exposed_set]
    # De-duplicate: a tool name may be registered in more than one server file.
    seen = {}
    for t in exposed_tools:
        seen.setdefault(t["name"], t)
    exposed_unique = list(seen.values())

    with_desc = sum(1 for t in exposed_unique if t["has_description"])
    fully_annotated = sum(
        1 for t in exposed_unique if t["param_count"] == t["annotated_param_count"]
    )

    report = {
        "measured_on": date.today().isoformat(),
        "commit": git_commit(),
        "encoding": ENCODING,
        "registrations_per_file": per_file,
        "total_registrations": len(all_tools),
        "unique_tool_names": len({t["name"] for t in all_tools}),
        "exposed_to_frontend": len(exposed),
        "exposed_resolved_in_source": len(exposed_unique),
        "exposed_with_description": with_desc,
        "exposed_with_description_pct": round(100 * with_desc / len(exposed_unique), 1)
        if exposed_unique
        else 0.0,
        "exposed_fully_type_annotated": fully_annotated,
        "selection_prompt_tokens_names_only": names_only_tokens,
        "selection_prompt_tokens_with_descriptions": with_desc_tokens,
        "tools_missing_from_source": sorted(exposed_set - {t["name"] for t in all_tools}),
    }

    RESULTS.mkdir(parents=True, exist_ok=True)
    out = RESULTS / "baseline_tool_surface.json"
    out.write_text(json.dumps({"report": report, "tools": all_tools}, indent=2))

    print(json.dumps(report, indent=2))
    print(f"\nwrote {out.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
