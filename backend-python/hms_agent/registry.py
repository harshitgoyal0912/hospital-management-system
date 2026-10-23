"""Canonical tool registry.

The single source of truth for what the agent can invoke.

The defect this replaces: `/tools/call` passes a client-supplied string to
`getattr(agent, tool_name)` (orchestrator_agent.py:~190), so the reachable
surface is *every public method on every registered agent* — which is how
`delete_patient` stays callable despite having no `@mcp.tool` registration.

Here a client string is only ever used as a **dictionary key**. It never reaches
`getattr`. Adding a method to an agent therefore grants no new capability; a
binding must be declared below, and it must also have a policy entry, or the
registry refuses to start.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping

from .policy.registry import TOOL_POLICIES
from .schemas import TOOL_ARG_MODELS


@dataclass(frozen=True)
class ToolBinding:
    """Declared binding from a tool name to one agent method."""

    name: str
    agent_key: str
    method: str


#: Every tool the guarded path exposes. Agent keys match orchestrator.agents
#: (orchestrator_agent.py:64-78).
BINDINGS: tuple[ToolBinding, ...] = (
    # patient
    ToolBinding("list_patients", "patient", "list_patients"),
    ToolBinding("search_patients", "patient", "search_patients"),
    ToolBinding("get_patient_by_id", "patient", "get_patient_by_id"),
    ToolBinding("create_patient", "patient", "create_patient"),
    ToolBinding("update_patient", "patient", "update_patient"),
    ToolBinding("delete_patient", "patient", "delete_patient"),
    ToolBinding("get_patient_medical_history_summary", "patient", "get_patient_medical_history_summary"),
    ToolBinding("discharge_patient_complete", "discharge", "discharge_patient_complete"),
    # beds and rooms
    ToolBinding("list_beds", "room_bed", "list_beds"),
    ToolBinding("get_bed_by_id", "room_bed", "get_bed_by_id"),
    ToolBinding("get_bed_by_number", "room_bed", "get_bed_by_number"),
    ToolBinding("assign_bed_to_patient", "room_bed", "assign_bed_to_patient"),
    ToolBinding("discharge_bed", "room_bed", "discharge_bed"),
    ToolBinding("update_bed_status", "room_bed", "update_bed_status"),
    ToolBinding("list_rooms", "room_bed", "list_rooms"),
    # staff and departments
    ToolBinding("list_staff", "staff", "list_staff"),
    ToolBinding("get_staff_by_id", "staff", "get_staff_by_id"),
    ToolBinding("create_staff", "staff", "create_staff"),
    ToolBinding("update_staff_status", "staff", "update_staff_status"),
    ToolBinding("list_departments", "department", "list_departments"),
    # inventory
    ToolBinding("list_supplies", "inventory", "list_supplies"),
    ToolBinding("get_low_stock_supplies", "inventory", "get_low_stock_supplies"),
    ToolBinding("update_supply_stock", "inventory", "update_supply_stock"),
    # clinical documents
    ToolBinding("get_patient_medical_history", "medical_document", "get_patient_medical_history"),
    ToolBinding("search_medical_documents", "medical_document", "search_medical_documents"),
    ToolBinding("query_medical_knowledge", "medical_document", "query_medical_knowledge"),
    ToolBinding("get_medical_timeline", "medical_document", "get_medical_timeline"),
)


class RegistryError(RuntimeError):
    """Raised at startup when the declared registry is inconsistent."""


class CanonicalToolRegistry:
    """Name -> callable, resolved once at startup and never by reflection."""

    def __init__(self, handlers: Mapping[str, Callable[..., Any]]):
        self._handlers = dict(handlers)

    @classmethod
    def from_agents(
        cls,
        agents: Mapping[str, Any],
        bindings: tuple[ToolBinding, ...] = BINDINGS,
        *,
        strict: bool = True,
    ) -> "CanonicalToolRegistry":
        """Bind declared tools to live agent methods, validating every binding.

        Resolution happens here, at startup, against a fixed table — not per
        request against a client string. A binding that does not resolve is a
        deployment error, surfaced immediately rather than at call time.
        """
        handlers: dict[str, Callable[..., Any]] = {}
        problems: list[str] = []

        for b in bindings:
            agent = agents.get(b.agent_key)
            if agent is None:
                problems.append(f"{b.name}: no agent '{b.agent_key}'")
                continue
            handler = getattr(agent, b.method, None)   # fixed literal, not client input
            if not callable(handler):
                problems.append(f"{b.name}: agent '{b.agent_key}' has no method '{b.method}'")
                continue
            if b.name not in TOOL_POLICIES:
                problems.append(f"{b.name}: bound but has no policy entry")
                continue
            if b.name not in TOOL_ARG_MODELS:
                problems.append(f"{b.name}: bound but has no argument schema")
                continue
            handlers[b.name] = handler

        if problems and strict:
            raise RegistryError("invalid tool bindings:\n  " + "\n  ".join(problems))

        return cls(handlers)

    def resolve(self, tool: str) -> Callable[..., Any] | None:
        """Dictionary lookup only. `tool` is untrusted input and is never executed."""
        return self._handlers.get(tool)

    def names(self) -> frozenset[str]:
        return frozenset(self._handlers)


def audit_registry_consistency(bindings: tuple[ToolBinding, ...] = BINDINGS) -> dict[str, list[str]]:
    """Report declarations that disagree with each other.

    Three tables must agree for a tool to be safely callable: the binding table,
    the policy registry, and the argument schemas. This surfaces drift.
    """
    declared = {b.name for b in bindings}
    return {
        "bound_without_policy": sorted(declared - set(TOOL_POLICIES)),
        "bound_without_schema": sorted(declared - set(TOOL_ARG_MODELS)),
        "policy_without_binding": sorted(set(TOOL_POLICIES) - declared),
    }
