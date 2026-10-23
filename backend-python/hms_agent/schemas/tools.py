"""Typed tool arguments.

The current dispatch path filters unknown kwargs by inspecting the target's
signature (orchestrator_agent.py:190-197), so a caller who misspells an argument
gets the tool executed with defaults instead of an error. For an agent that is
the worst option: a wrong argument silently becomes a different operation.

Every model here sets ``extra="forbid"``. An unrecognised argument is a hard
validation failure and the handler does not run.
"""
from __future__ import annotations

from typing import Any, Mapping, Type

from pydantic import BaseModel, ConfigDict, Field, ValidationError


class UnknownArgument(ValueError):
    """Raised when arguments do not satisfy the tool's declared schema."""

    def __init__(self, tool: str, errors: list[dict[str, Any]]):
        self.tool = tool
        self.errors = errors
        super().__init__(f"invalid arguments for '{tool}': {errors}")


class StrictArgs(BaseModel):
    """Base for every tool argument model."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


# --- read ---------------------------------------------------------------

class NoArgs(StrictArgs):
    pass


class PatientId(StrictArgs):
    patient_id: str = Field(min_length=1)


class BedId(StrictArgs):
    bed_id: str = Field(min_length=1)


class BedNumber(StrictArgs):
    bed_number: str = Field(min_length=1)


class StaffId(StrictArgs):
    staff_id: str = Field(min_length=1)


class SearchPatients(StrictArgs):
    query: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    patient_number: str | None = None
    limit: int = Field(default=25, ge=1, le=200)


# --- write --------------------------------------------------------------

class CreatePatient(StrictArgs):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    date_of_birth: str | None = None
    gender: str | None = None
    phone: str | None = None
    email: str | None = None
    address: str | None = None


class UpdatePatient(StrictArgs):
    patient_id: str = Field(min_length=1)
    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None
    email: str | None = None
    address: str | None = None


class AssignBed(StrictArgs):
    bed_id: str = Field(min_length=1)
    patient_id: str = Field(min_length=1)
    admission_date: str | None = None


class UpdateSupplyStock(StrictArgs):
    supply_id: str = Field(min_length=1)
    quantity_change: int
    transaction_type: str = Field(min_length=1)
    performed_by: str | None = None


class DischargeBed(StrictArgs):
    bed_id: str = Field(min_length=1)
    discharge_date: str | None = None


class DischargePatient(StrictArgs):
    patient_id: str = Field(min_length=1)
    discharge_condition: str = Field(default="stable", min_length=1)
    discharge_destination: str = Field(default="home", min_length=1)


class ListRooms(StrictArgs):
    department_id: str | None = None
    status: str | None = None


class CreateStaff(StrictArgs):
    # Either user_id (existing user) or first_name (create the user too)
    user_id: str | None = None
    first_name: str | None = Field(default=None, max_length=50)
    last_name: str | None = Field(default=None, max_length=50)
    email: str | None = None
    phone: str | None = None
    employee_id: str = Field(min_length=1)
    department_id: str | None = None
    position: str | None = None
    specialization: str | None = None
    shift_pattern: str | None = None


class UpdateStaffStatus(StrictArgs):
    staff_id: str = Field(min_length=1)
    status: str = Field(min_length=1)


class UpdateBedStatus(StrictArgs):
    bed_id: str = Field(min_length=1)
    status: str = Field(min_length=1)
    notes: str | None = None


class SearchMedicalDocuments(StrictArgs):
    query: str = Field(min_length=1)
    patient_id: str | None = None
    document_type: str | None = None
    limit: int = Field(default=10, ge=1, le=100)


# --- clinical -----------------------------------------------------------

class QueryMedicalKnowledge(StrictArgs):
    query: str = Field(min_length=1)
    patient_id: str | None = None
    top_k: int = Field(default=5, ge=1, le=20)


#: Declared argument schema per tool. A tool with no entry gets `StrictArgs`,
#: which forbids *all* arguments — so an undeclared tool cannot be driven with
#: arbitrary input even if it is somehow reachable.
TOOL_ARG_MODELS: Mapping[str, Type[StrictArgs]] = {
    "list_patients": NoArgs,
    "list_beds": NoArgs,
    "list_staff": NoArgs,
    "list_departments": NoArgs,
    "list_supplies": NoArgs,
    "get_low_stock_supplies": NoArgs,
    "get_system_status": NoArgs,
    "search_patients": SearchPatients,
    "get_patient_by_id": PatientId,
    "get_patient_medical_history": PatientId,
    "get_patient_medical_history_summary": PatientId,
    "get_medical_timeline": PatientId,
    "get_bed_by_id": BedId,
    "get_bed_by_number": BedNumber,
    "get_staff_by_id": StaffId,
    "create_patient": CreatePatient,
    "update_patient": UpdatePatient,
    "assign_bed_to_patient": AssignBed,
    "update_supply_stock": UpdateSupplyStock,
    "discharge_bed": DischargeBed,
    "discharge_patient_complete": DischargePatient,
    "delete_patient": PatientId,
    "query_medical_knowledge": QueryMedicalKnowledge,
    "list_rooms": ListRooms,
    "create_staff": CreateStaff,
    "update_staff_status": UpdateStaffStatus,
    "update_bed_status": UpdateBedStatus,
    "search_medical_documents": SearchMedicalDocuments,
}


def validate_arguments(tool: str, arguments: Mapping[str, Any] | None) -> dict[str, Any]:
    """Validate and normalise arguments, or raise UnknownArgument."""
    model = TOOL_ARG_MODELS.get(tool, StrictArgs)
    try:
        return model(**(arguments or {})).model_dump(exclude_none=True)
    except ValidationError as exc:
        raise UnknownArgument(tool, exc.errors(include_url=False)) from exc
