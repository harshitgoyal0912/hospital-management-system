"""LLM-backed planner.

The model's entire job is to propose one tool and its arguments. It is handed a
menu built from the canonical registry, narrowed to what the caller's role can
actually reach, with the schemas the boundary will enforce anyway.

Two properties follow from that construction:

* **The menu is role-scoped.** A receptionist's request never shows
  `delete_patient` in the tool list. That is a context and token optimisation,
  not a security control — the policy engine still runs on whatever comes back,
  and a model that invents a tool name gets a registry miss.
* **The model cannot widen its own options.** The menu is built from declared
  bindings, so nothing it writes adds a capability.

NOT YET VERIFIED AGAINST A LIVE MODEL. The graph and policy tests run against
`ScriptedPlanner`; this class has unit coverage for menu construction and
response parsing, but no run against a real endpoint. Treat the first staging
run as the real test.
"""
from __future__ import annotations

import json
import os
from typing import Any

from ..policy import PolicyEngine
from ..schemas import TOOL_ARG_MODELS
from .planner import Plan
from .state import AgentState

#: Configurable rather than hardcoded. The existing code pins "gpt-4" in five
#: places (e.g. agents/langraph_workflows.py:32); this reads the environment so
#: a model change is a deployment decision, not an edit.
#:
#: LLM_MODEL is accepted as an alias because OpenAI-compatible providers
#: commonly document that name.
DEFAULT_MODEL = os.getenv("HMS_AGENT_MODEL") or os.getenv("LLM_MODEL") or "gpt-4o-mini"

#: Any OpenAI-compatible endpoint. Left unset, the SDK uses api.openai.com.
#: Set it to run against NVIDIA NIM, vLLM, Together, Groq, a local Ollama, or
#: anything else speaking the same protocol — the planner does not care which,
#: because the policy engine validates whatever comes back either way.
API_BASE = os.getenv("OPENAI_API_BASE") or os.getenv("OPENAI_BASE_URL")

SYSTEM_PROMPT = """You coordinate hospital operations by selecting tools.

Rules you must follow:
- Select exactly one tool per step, or finish if the request is satisfied.
- Use only the tools listed. Do not invent tool names or arguments.
- You do not decide what is permitted. A separate policy layer authorises every
  action, and some will require human approval. That is expected; do not try to
  work around a refusal or retry it with different wording.
- Clinical output is decision support for a clinician, never a diagnosis or an
  instruction to a patient.
- If the request is ambiguous or you lack an identifier you need, finish and ask
  for the missing detail rather than guessing.
"""


def build_tool_menu(engine: PolicyEngine, role: str, registry_names: set[str]) -> list[dict]:
    """Tools this role can reach, as function-calling definitions.

    Descriptions and argument schemas come from the declared models — the same
    ones the boundary validates against — so the menu cannot drift from what is
    actually accepted.
    """
    reachable = engine.tools_for_role(role) & registry_names
    menu = []
    for name in sorted(reachable):
        model = TOOL_ARG_MODELS.get(name)
        schema = model.model_json_schema() if model else {"type": "object", "properties": {}}
        schema.pop("title", None)
        menu.append(
            {
                "type": "function",
                "function": {
                    "name": name,
                    "description": (model.__doc__ or name.replace("_", " ")).strip().split("\n")[0],
                    "parameters": schema,
                },
            }
        )
    return menu


class LLMPlanner:
    def __init__(
        self,
        engine: PolicyEngine,
        registry_names: set[str],
        client: Any = None,
        model: str = DEFAULT_MODEL,
    ):
        self._engine = engine
        self._registry_names = set(registry_names)
        self._model = model
        self._client = client

    def _get_client(self):
        if self._client is None:
            from openai import OpenAI

            # Read the server-side variable. The VITE_-prefixed one is bundled
            # into browser JavaScript and must never be used here.
            kwargs = {"api_key": os.getenv("OPENAI_API_KEY")}
            if API_BASE:
                kwargs["base_url"] = API_BASE
            self._client = OpenAI(**kwargs)
        return self._client

    def _messages(self, state: AgentState) -> list[dict]:
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": state["request"]},
        ]
        for entry in state.get("messages", []):
            if entry.get("role") == "tool":
                messages.append(
                    {
                        "role": "user",
                        "content": f"Result of {entry.get('name')}: "
                        f"{json.dumps(entry.get('content'), default=str)[:2000]}",
                    }
                )
        if state.get("errors"):
            messages.append(
                {
                    "role": "user",
                    "content": "Previous steps reported: " + "; ".join(state["errors"][-3:]),
                }
            )
        return messages

    def plan(self, state: AgentState) -> Plan:
        menu = build_tool_menu(self._engine, state["role"], self._registry_names)
        if not menu:
            return Plan(tool=None, response="There are no actions available to your role.")

        response = self._get_client().chat.completions.create(
            model=self._model,
            messages=self._messages(state),
            tools=menu,
            tool_choice="auto",
            temperature=0,
        )
        return self.parse(response)

    @staticmethod
    def parse(response: Any) -> Plan:
        """Turn a completion into a Plan.

        A malformed tool call finishes the run rather than guessing: an
        unparseable proposal is not a reason to act.
        """
        try:
            message = response.choices[0].message
        except (AttributeError, IndexError, TypeError):
            return Plan(tool=None, response="I could not determine a next step.")

        calls = getattr(message, "tool_calls", None)
        if not calls:
            return Plan(tool=None, response=(getattr(message, "content", None) or "Done."))

        call = calls[0]
        try:
            arguments = json.loads(call.function.arguments or "{}")
        except (json.JSONDecodeError, AttributeError):
            return Plan(tool=None, response="I could not read the proposed arguments.")

        if not isinstance(arguments, dict):
            return Plan(tool=None, response="I could not read the proposed arguments.")

        return Plan(
            tool=call.function.name,
            arguments=arguments,
            reasoning=(getattr(message, "content", None) or "")[:500],
        )
