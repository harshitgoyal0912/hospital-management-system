"""Tool policy registry.

Every tool the agent may reach is declared here with a risk tier and the roles
permitted to invoke it. A tool that is not declared is denied: the engine fails
closed, so adding a tool to the codebase does not silently grant the agent a new
capability.

Roles are the values already present in ``User.role`` (database.py:92):
admin, doctor, nurse, manager, receptionist.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

from .decisions import Decision, ToolTier

ALL_ROLES = frozenset({"admin", "doctor", "nurse", "manager", "receptionist"})
CLINICAL_ROLES = frozenset({"doctor", "admin"})
WARD_ROLES = frozenset({"doctor", "nurse", "admin"})
OPS_ROLES = frozenset({"admin", "manager"})
FRONT_DESK = frozenset({"admin", "manager", "receptionist"})


@dataclass(frozen=True)
class ToolPolicy:
    """Declared policy for one tool."""

    tier: ToolTier
    allowed_roles: frozenset[str]
    #: Roles that may invoke the tool but only behind an explicit human approval.
    approval_roles: frozenset[str] = field(default_factory=frozenset)
    #: Roles that may invoke it but must confirm first (reversible but disruptive).
    confirm_roles: frozenset[str] = field(default_factory=frozenset)
    reason: str = ""


def _read(*roles: str, reason: str = "") -> ToolPolicy:
    return ToolPolicy(ToolTier.READ, frozenset(roles), reason=reason)


def _write(*roles: str, confirm: frozenset[str] = frozenset(), reason: str = "") -> ToolPolicy:
    return ToolPolicy(ToolTier.WRITE, frozenset(roles), confirm_roles=confirm, reason=reason)


def _execute(*roles: str, approval: frozenset[str] = frozenset(), confirm: frozenset[str] = frozenset(), reason: str = "") -> ToolPolicy:
    return ToolPolicy(
        ToolTier.EXECUTE, frozenset(roles), approval_roles=approval, confirm_roles=confirm, reason=reason
    )


def _clinical(*roles: str, approval: frozenset[str] = frozenset(), reason: str = "") -> ToolPolicy:
    return ToolPolicy(ToolTier.CLINICAL, frozenset(roles), approval_roles=approval, reason=reason)


TOOL_POLICIES: Mapping[str, ToolPolicy] = {
    # ---- Read-only operational lookups -------------------------------------
    "list_patients": _read(*FRONT_DESK, "doctor", "nurse"),
    "search_patients": _read(*FRONT_DESK, "doctor", "nurse"),
    "get_patient_by_id": _read(*FRONT_DESK, "doctor", "nurse"),
    "list_beds": _read(*ALL_ROLES),
    "get_bed_by_id": _read(*ALL_ROLES),
    "get_bed_by_number": _read(*ALL_ROLES),
    "check_bed_status": _read(*ALL_ROLES),
    "list_rooms": _read(*ALL_ROLES),
    "list_departments": _read(*ALL_ROLES),
    "list_staff": _read(*ALL_ROLES),
    "get_staff_by_id": _read(*ALL_ROLES),
    "list_equipment": _read(*ALL_ROLES),
    "list_supplies": _read(*ALL_ROLES),
    "get_low_stock_supplies": _read(*ALL_ROLES),
    "list_inventory_transactions": _read(*OPS_ROLES, "nurse"),
    "get_system_status": _read(*ALL_ROLES),
    "list_meetings": _read(*ALL_ROLES),

    # ---- Patient clinical record: narrower than demographics ---------------
    "get_patient_medical_history": _read(*WARD_ROLES, reason="clinical record, not front-desk data"),
    "get_patient_medical_history_summary": _read(*WARD_ROLES, reason="clinical record"),
    "get_medical_timeline": _read(*WARD_ROLES, reason="clinical record"),
    "search_medical_documents": _read(*WARD_ROLES, reason="clinical record"),
    "get_document_by_id": _read(*WARD_ROLES, reason="clinical record"),

    # ---- Ordinary writes ---------------------------------------------------
    "create_patient": _write(*FRONT_DESK, "doctor", "nurse"),
    "update_patient": _write(*FRONT_DESK, "doctor", "nurse"),
    "create_staff": _write(*OPS_ROLES),
    "update_staff": _write(*OPS_ROLES),
    "update_staff_status": _write(*OPS_ROLES, "nurse"),
    "create_department": _write(*OPS_ROLES),
    "create_room": _write(*OPS_ROLES),
    "create_bed": _write(*OPS_ROLES),
    "create_equipment": _write(*OPS_ROLES),
    "update_equipment": _write(*OPS_ROLES),
    "update_equipment_status": _write(*OPS_ROLES, "nurse"),
    "create_supply": _write(*OPS_ROLES),
    "update_supply": _write(*OPS_ROLES),
    "schedule_meeting": _write(*ALL_ROLES),
    "add_meeting_notes": _write(*ALL_ROLES),
    "add_patient_to_queue": _write(*WARD_ROLES, *FRONT_DESK),

    # ---- Resource allocation: reversible but disruptive --------------------
    "assign_bed_to_patient": _write(*WARD_ROLES, confirm=frozenset({"nurse"}),
                                    reason="ward resource allocation"),
    "assign_next_patient_to_bed": _write(*WARD_ROLES, confirm=frozenset({"nurse"})),
    "assign_staff_to_patient_simple": _write(*WARD_ROLES),
    "update_bed_status": _write(*WARD_ROLES),
    "update_supply_stock": _write(*OPS_ROLES, "nurse", confirm=frozenset({"nurse"}),
                                  reason="inventory mutation"),
    "record_patient_supply_usage": _write(*WARD_ROLES),

    # ---- Irreversible / high-impact execution ------------------------------
    "discharge_bed": _execute("doctor", "admin", confirm=frozenset({"doctor"}),
                              approval=frozenset({"nurse"}),
                              reason="frees a bed and closes an occupancy record"),
    "discharge_patient_complete": _execute("doctor", "admin", confirm=frozenset({"doctor"}),
                                           reason="closes the episode of care"),
    "generate_discharge_report": _execute("doctor", "admin", "nurse"),
    "delete_user": _execute("admin", approval=frozenset({"admin"}),
                            reason="irreversible; admin still requires human approval"),
    "delete_equipment": _execute("admin", approval=frozenset({"admin"})),
    "delete_supply": _execute("admin", approval=frozenset({"admin"})),
    "delete_patient": _execute("admin", approval=frozenset({"admin"}),
                               reason="irreversible destruction of a patient record"),
    "delete_staff": _execute("admin", approval=frozenset({"admin"})),
    "delete_room": _execute("admin", approval=frozenset({"admin"})),
    "delete_department": _execute("admin", approval=frozenset({"admin"})),

    # ---- Clinical decision support -----------------------------------------
    # Support, never authority. A nurse may request it; the output reaches the
    # record only behind a clinician's approval.
    "query_medical_knowledge": _clinical(*WARD_ROLES),
    "analyze_vital_signs": _clinical(*CLINICAL_ROLES, approval=frozenset({"nurse"})),
    "generate_differential_diagnosis": _clinical(*CLINICAL_ROLES, approval=frozenset({"nurse"})),
    "enhanced_differential_diagnosis": _clinical(*CLINICAL_ROLES, approval=frozenset({"nurse"})),
    "enhanced_treatment_recommendations": _clinical(*CLINICAL_ROLES, approval=frozenset({"nurse"})),
    "enhanced_drug_interaction_analysis": _clinical(*WARD_ROLES),
    "enhanced_clinical_risk_assessment": _clinical(*CLINICAL_ROLES, approval=frozenset({"nurse"})),
    "enhanced_symptom_analysis": _clinical(*WARD_ROLES),
    "process_clinical_notes": _clinical(*WARD_ROLES),
    "add_treatment_record_simple": _clinical(*CLINICAL_ROLES, approval=frozenset({"nurse"})),
}


def tier_of(tool: str) -> ToolTier | None:
    policy = TOOL_POLICIES.get(tool)
    return policy.tier if policy else None
