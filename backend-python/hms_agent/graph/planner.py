"""Planner protocol.

The planner is the only place the LLM is consulted, and it may return exactly
one thing: a proposed tool and arguments. It cannot approve, authorise, or
execute anything — those are separate nodes that read the policy engine.

Keeping it behind a protocol also means the graph is testable without a model,
which is what lets the control-flow tests be deterministic.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

from .state import AgentState


@dataclass(frozen=True)
class Plan:
    """A proposed next step.

    `tool=None` means the planner believes the request is satisfied; the graph
    then finishes rather than calling anything.
    """

    tool: str | None
    arguments: dict[str, Any] = field(default_factory=dict)
    intent: str | None = None
    reasoning: str = ""
    response: str | None = None


class Planner(Protocol):
    def plan(self, state: AgentState) -> Plan: ...


class ScriptedPlanner:
    """Deterministic planner for tests and for the baseline arm of evaluations."""

    def __init__(self, plans: list[Plan]):
        self._plans = list(plans)
        self.calls = 0

    def plan(self, state: AgentState) -> Plan:
        index = self.calls
        self.calls += 1
        if index < len(self._plans):
            return self._plans[index]
        return Plan(tool=None, response="Nothing further to do.")
