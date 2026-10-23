"""Discharge Report Agent - manages discharge workflow and related clinical records."""
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List
from .base_agent import BaseAgent

try:
    from discharge_service import PatientDischargeReportGenerator
    from discharge_report_models import TreatmentRecord, EquipmentUsage, StaffAssignment
    from database import SessionLocal
    from sqlalchemy import and_
    DISCHARGE_DEPS = True
except ImportError:
    DISCHARGE_DEPS = False

class DischargeAgent(BaseAgent):
    def __init__(self):
        super().__init__("Discharge Report Agent", "discharge_agent")
        self.generator = PatientDischargeReportGenerator() if DISCHARGE_DEPS else None

    # Helper: robust patient lookup by name (supports "First Last" or partials)
    def _find_patient_by_name(self, db, patient_name: str):
        try:
            from database import Patient as CorePatient
        except Exception:
            return None
        if not patient_name:
            return None
        # Normalize and split tokens
        name = (patient_name or "").strip()
        tokens = [t for t in name.replace('  ', ' ').split(' ') if t]
        q = db.query(CorePatient)
        # Prefer two-token match: First Last
        if len(tokens) >= 2:
            first, last = tokens[0], tokens[1]
            # 1) First startswith + Last startswith
            p = (q.filter(CorePatient.first_name.ilike(f"{first}%"),
                          CorePatient.last_name.ilike(f"{last}%")).first())
            if p:
                return p
            # 2) Try reversed order
            p = (q.filter(CorePatient.first_name.ilike(f"{last}%"),
                          CorePatient.last_name.ilike(f"{first}%")).first())
            if p:
                return p
            # 3) Fallback: first or last contains either token
            p = (q.filter((CorePatient.first_name.ilike(f"%{first}%")) |
                          (CorePatient.last_name.ilike(f"%{last}%"))).first())
            if p:
                return p
        # Single-token fallback: match either first or last name
        token = tokens[0]
        p = (q.filter((CorePatient.first_name.ilike(f"%{token}%")) |
                      (CorePatient.last_name.ilike(f"%{token}%"))).first())
        return p

    def get_tools(self) -> List[str]:
        return [
            # Existing discharge tools
            "generate_discharge_report",
            "add_treatment_record_simple",
            "add_treatment_record_by_codes",
            "add_equipment_usage_simple",
            "assign_staff_to_patient_simple",
            "complete_equipment_usage_simple",
            "list_discharge_reports",
            
            # Comprehensive Discharge Workflow
            "discharge_patient_complete",
            "get_patient_discharge_status",
            
            # Bed Turnover Management Tools
            "start_bed_turnover_process",
            "complete_bed_cleaning",
            "get_bed_status_with_time_remaining",
            "add_patient_to_queue",
            "get_patient_queue",
            "assign_next_patient_to_bed",
            "update_turnover_progress",
            "get_bed_turnover_details",
            "mark_equipment_for_cleaning",
            "complete_equipment_cleaning",
            "get_equipment_turnover_status",
            "auto_update_expired_cleaning_beds"
        ]

    def get_capabilities(self) -> List[str]:
        return [
            "Generate comprehensive discharge reports",
            "Capture treatments / equipment usage / staff assignments",
            "Finalize equipment usage records",
            "List existing discharge reports"
        ]

    # ---- Tool Implementations ----
    def generate_discharge_report(self, bed_id: str, discharge_condition: str = "stable", discharge_destination: str = "home") -> Dict[str, Any]:
        if not DISCHARGE_DEPS or not self.generator:
            return {"success": False, "message": "Discharge dependencies not available"}
        result = self.generator.generate_discharge_report(bed_id=bed_id, discharge_condition=discharge_condition, discharge_destination=discharge_destination)
        self.log_interaction(query=f"Generate discharge report for bed {bed_id}", response=result.get("message",""), tool_used="generate_discharge_report")
        return result

    def add_treatment_record_simple(self, patient_id: str, doctor_id: str, treatment_type: str, treatment_name: str) -> Dict[str, Any]:
        if not DISCHARGE_DEPS:
            return {"success": False, "message": "Discharge dependencies not available"}
        from database import SessionLocal, TreatmentRecord as CoreTreatmentRecord  # ensure main models
        db = SessionLocal()
        try:
            tr = CoreTreatmentRecord(
                patient_id=uuid.UUID(patient_id),
                doctor_id=uuid.UUID(doctor_id),
                treatment_type=treatment_type,
                treatment_name=treatment_name,
                start_date=datetime.now()
            )
            db.add(tr)
            db.commit()
            db.refresh(tr)
            db.close()
            return {"success": True, "data": {"id": str(tr.id)}}
        except Exception as e:
            db.rollback()
            db.close()
            return {"success": False, "message": str(e)}

    def add_equipment_usage_simple(self, patient_id: str, equipment_id: str, staff_id: str, purpose: str, start_time: str = None, end_time: str = None, notes: str = None) -> Dict[str, Any]:
        if not DISCHARGE_DEPS:
            return {"success": False, "message": "Discharge dependencies not available"}
        from database import SessionLocal, EquipmentUsage as CoreEquipmentUsage
        db = SessionLocal()
        try:
            # Parse start_time and end_time if provided
            start_dt = datetime.now()
            if start_time:
                try:
                    # Handle both full datetime and date-only formats
                    if len(start_time) <= 10:  # YYYY-MM-DD format
                        start_dt = datetime.fromisoformat(start_time + " 00:00:00")
                    else:  # Full datetime format
                        start_dt = datetime.fromisoformat(start_time.replace(' ', 'T') if ' ' in start_time else start_time)
                except ValueError:
                    start_dt = datetime.now()  # Fallback to current time
            
            end_dt = None
            if end_time:
                try:
                    if len(end_time) <= 10:  # YYYY-MM-DD format
                        end_dt = datetime.fromisoformat(end_time + " 23:59:59")
                    else:  # Full datetime format
                        end_dt = datetime.fromisoformat(end_time.replace(' ', 'T') if ' ' in end_time else end_time)
                except ValueError:
                    end_dt = None  # Keep as None if parsing fails
            
            eu = CoreEquipmentUsage(
                patient_id=uuid.UUID(patient_id),
                equipment_id=uuid.UUID(equipment_id),
                staff_id=uuid.UUID(staff_id),
                purpose=purpose,
                start_time=start_dt,
                end_time=end_dt,
                notes=notes
            )
            db.add(eu)
            db.commit()
            db.refresh(eu)
            db.close()
            
            result = {
                "success": True,
                "data": {
                    "id": str(eu.id),
                    "patient_id": str(eu.patient_id),
                    "equipment_id": str(eu.equipment_id),
                    "staff_id": str(eu.staff_id),
                    "purpose": eu.purpose,
                    "start_time": eu.start_time.isoformat() if eu.start_time else None,
                    "end_time": eu.end_time.isoformat() if eu.end_time else None,
                    "notes": eu.notes
                }
            }
            return result
        except Exception as e:
            db.rollback()
            db.close()
            return {"success": False, "message": f"Failed to add equipment usage: {str(e)}"}

    def add_equipment_usage_by_codes(self, patient_number: str, equipment_id: str, employee_id: str, purpose: str, start_time: str = None, end_time: str = None, notes: str = None) -> Dict[str, Any]:
        """Add equipment usage using patient_number, equipment_id (code), and employee_id (staff code), not UUIDs."""
        if not DISCHARGE_DEPS:
            return {"success": False, "message": "Discharge dependencies not available"}
        from database import SessionLocal, Patient as CorePatient, Staff as CoreStaff, Equipment as CoreEquipment, EquipmentUsage as CoreEquipmentUsage
        db = SessionLocal()
        try:
            patient = db.query(CorePatient).filter(CorePatient.patient_number == patient_number).first()
            if not patient:
                db.close()
                return {"success": False, "message": f"Patient with number {patient_number} not found"}
            staff = db.query(CoreStaff).filter(CoreStaff.employee_id == employee_id).first()
            if not staff:
                db.close()
                return {"success": False, "message": f"Staff with employee_id {employee_id} not found"}
            equipment = db.query(CoreEquipment).filter(CoreEquipment.equipment_id == equipment_id).first()
            if not equipment:
                db.close()
                return {"success": False, "message": f"Equipment with equipment_id {equipment_id} not found"}
            eu = CoreEquipmentUsage(
                patient_id=patient.id,
                equipment_id=equipment.id,
                staff_id=staff.id,
                purpose=purpose,
                start_time=datetime.fromisoformat(start_time) if start_time else datetime.now(),
                end_time=datetime.fromisoformat(end_time) if end_time else None,
                notes=notes
            )
            db.add(eu)
            db.commit()
            db.refresh(eu)
            db.close()
            return {"success": True, "data": {"id": str(eu.id)}}
        except Exception as e:
            db.rollback()
            db.close()
            return {"success": False, "message": str(e)}

    def assign_staff_to_patient_simple(self, patient_id: str, staff_id: str, assignment_type: str = None, role: str = None) -> Dict[str, Any]:
        if not DISCHARGE_DEPS:
            return {"success": False, "message": "Discharge dependencies not available"}
        # Support both "assignment_type" (agent) and "role" (server wrapper)
        assignment_value = assignment_type or role or "assigned"
        from database import SessionLocal, StaffAssignment as CoreStaffAssignment
        db = SessionLocal()
        try:
            sa = CoreStaffAssignment(
                patient_id=uuid.UUID(patient_id),
                staff_id=uuid.UUID(staff_id),
                assignment_type=assignment_value,
                start_date=datetime.now()
            )
            db.add(sa)
            db.commit()
            db.refresh(sa)
            db.close()
            return {"success": True, "data": {"id": str(sa.id)}}
        except Exception as e:
            db.rollback()
            db.close()
            return {"success": False, "message": str(e)}

    def complete_equipment_usage_simple(self, usage_id: str) -> Dict[str, Any]:
        if not DISCHARGE_DEPS:
            return {"success": False, "message": "Discharge dependencies not available"}
        from database import SessionLocal, EquipmentUsage as CoreEquipmentUsage
        db = SessionLocal()
        try:
            usage = db.query(CoreEquipmentUsage).filter(CoreEquipmentUsage.id == uuid.UUID(usage_id)).first()
            if not usage:
                db.close()
                return {"success": False, "message": "Usage not found"}
            usage.end_time = datetime.now()
            usage.status = "completed"
            db.commit()
            db.refresh(usage)
            db.close()
            return {"success": True, "data": {"id": str(usage.id), "status": usage.status}}
        except Exception as e:
            db.rollback()
            db.close()
            return {"success": False, "message": str(e)}

    def list_discharge_reports(self, patient_id: str = None) -> Dict[str, Any]:
        if not DISCHARGE_DEPS:
            return {"success": False, "message": "Discharge dependencies not available"}
        from database import SessionLocal, DischargeReport
        db = SessionLocal()
        try:
            q = db.query(DischargeReport)
            if patient_id:
                q = q.filter(DischargeReport.patient_id == uuid.UUID(patient_id))
            reports = q.order_by(DischargeReport.created_at.desc()).limit(25).all()
            data = []
            for r in reports:
                data.append({
                    "report_id": str(r.id),
                    "report_number": r.report_number,
                    "patient_id": str(r.patient_id),
                    "discharge_date": r.discharge_date.isoformat() if r.discharge_date else None,
                    "condition": r.discharge_condition,
                    "destination": r.discharge_destination
                })
            db.close()
            return {"success": True, "reports": data, "total": len(data)}
        except Exception as e:
            db.close()
            return {"success": False, "message": str(e)}

    # ---- Bed Turnover Management Tools ----

    def start_bed_turnover_process(self, bed_id: str, previous_patient_id: str = None, turnover_type: str = "standard", priority_level: str = "normal") -> Dict[str, Any]:
        """Initiate bed turnover process after patient discharge."""
        if not DISCHARGE_DEPS:
            return {"success": False, "message": "Discharge dependencies not available"}
        
        from database import SessionLocal, BedTurnover, Bed
        db = SessionLocal()
        try:
            # Check if bed exists and get current status
            bed = db.query(Bed).filter(Bed.id == uuid.UUID(bed_id)).first()
            if not bed:
                db.close()
                return {"success": False, "message": "Bed not found"}
            
            # Create new bed turnover record; start cleaning immediately for countdown UI
            estimated_minutes = 30 if turnover_type in ("standard", None) else (60 if turnover_type == "deep_clean" else 45)
            turnover = BedTurnover(
                bed_id=uuid.UUID(bed_id),
                previous_patient_id=uuid.UUID(previous_patient_id) if previous_patient_id else None,
                status="cleaning",
                turnover_type=turnover_type,
                priority_level=priority_level,
                discharge_time=datetime.now(),
                cleaning_start_time=datetime.now(),
                estimated_cleaning_duration=estimated_minutes
            )
            
            db.add(turnover)
            
            # Update bed status to cleaning
            bed.status = "cleaning"
            bed.updated_at = datetime.now()
            
            db.commit()
            db.refresh(turnover)
            
            result = {
                "success": True,
                "turnover_id": str(turnover.id),
                "bed_id": bed_id,
                "status": turnover.status,
                "estimated_duration": turnover.estimated_cleaning_duration,
                "priority": priority_level,
                "message": f"Bed turnover process initiated for bed {bed.bed_number} and cleaning started"
            }
            
            db.close()
            return result
            
        except Exception as e:
            db.rollback()
            db.close()
            return {"success": False, "message": str(e)}

    def complete_bed_cleaning(self, turnover_id: str = None, bed_id: str = None, inspector_id: str = None, inspection_passed: bool = True, inspector_notes: str = "", cleaned_by: str = None, cleaning_notes: str = None) -> Dict[str, Any]:
        """Complete bed cleaning process and mark bed as ready.
        Supports both turnover_id (agent) and bed_id/cleaned_by (server wrapper) styles."""
        if not DISCHARGE_DEPS:
            return {"success": False, "message": "Discharge dependencies not available"}
        
        from database import SessionLocal, BedTurnover, Bed
        db = SessionLocal()
        try:
            turnover = None
            if turnover_id:
                try:
                    turnover = db.query(BedTurnover).filter(BedTurnover.id == uuid.UUID(turnover_id)).first()
                except Exception:
                    turnover = None
            elif bed_id:
                # Find active turnover for the bed
                turnover = db.query(BedTurnover).filter(
                    BedTurnover.bed_id == uuid.UUID(bed_id),
                    BedTurnover.status.in_(["initiated", "cleaning"])
                ).first()
            
            if not turnover:
                db.close()
                return {"success": False, "message": "Turnover record not found"}
            
            # Use cleaned_by as alias for inspector_id; cleaning_notes for inspector_notes
            if cleaned_by and not inspector_id:
                try:
                    inspector_id = str(uuid.UUID(cleaned_by))
                except Exception:
                    inspector_id = None
            if cleaning_notes and not inspector_notes:
                inspector_notes = cleaning_notes
            
            # Update turnover record
            turnover.cleaning_end_time = datetime.now()
            turnover.status = "cleaning_complete"
            turnover.inspection_passed = inspection_passed
            turnover.inspector_notes = inspector_notes
            
            if inspector_id:
                try:
                    turnover.assigned_inspector_id = uuid.UUID(inspector_id)
                except Exception:
                    pass
            
            if inspection_passed:
                turnover.status = "ready"
                turnover.ready_time = datetime.now()
                
                # Update bed status
                bed = db.query(Bed).filter(Bed.id == turnover.bed_id).first()
                if bed:
                    bed.status = "available"
                    bed.updated_at = datetime.now()
            
            db.commit()
            db.refresh(turnover)
            
            result = {
                "success": True,
                "turnover_id": str(turnover.id),
                "status": turnover.status,
                "inspection_passed": inspection_passed,
                "cleaning_duration": (turnover.cleaning_end_time - turnover.cleaning_start_time).seconds // 60 if getattr(turnover, 'cleaning_start_time', None) else None,
                "message": "Bed cleaning completed successfully" if inspection_passed else "Bed cleaning completed but failed inspection"
            }
            
            db.close()
            return result
            
        except Exception as e:
            db.rollback()
            db.close()
            return {"success": False, "message": str(e)}

    def get_bed_status_with_time_remaining(self, bed_id: str) -> Dict[str, Any]:
        """🛏️ Check specific bed status after discharge - shows cleaning time remaining.
        
        ⭐ PRIMARY TOOL for checking individual bed status ⭐
        
        Use this when user asks:
        - "check bed 302A status"
        - "check bed status after discharge" 
        - "how long until bed ready"
        - "is bed cleaning done"
        
        Returns detailed status with cleaning countdown timer.
        
        Args:
            bed_id: Bed number (e.g., "302A") or bed UUID
            
        Returns:
            Detailed bed status including cleaning time remaining and progress.
        """
        if not DISCHARGE_DEPS:
            return {"success": False, "message": "Discharge dependencies not available"}
        
        from database import SessionLocal, BedTurnover, Bed
        db = SessionLocal()
        try:
            # Try to find bed by UUID first, then by bed number
            bed = None
            try:
                # Try as UUID first
                bed = db.query(Bed).filter(Bed.id == uuid.UUID(bed_id)).first()
            except (ValueError, TypeError):
                # If not a valid UUID, try as bed number
                bed = db.query(Bed).filter(Bed.bed_number == bed_id).first()
            
            if not bed:
                db.close()
                return {"success": False, "message": f"Bed not found with identifier: {bed_id}"}
            
            # Use the actual bed UUID for turnover queries
            actual_bed_id = bed.id
            
            # Get active turnover process
            turnover = db.query(BedTurnover).filter(
                BedTurnover.bed_id == actual_bed_id,
                BedTurnover.status.in_(["initiated", "cleaning"])
            ).first()
            
            result = {
                "success": True,
                "bed_id": str(actual_bed_id),
                "bed_number": bed.bed_number,
                "current_status": bed.status,
                "room_number": bed.room.room_number if bed.room else "Unknown",
            }
            
            if turnover:
                now = datetime.now()
                
                if turnover.status == "cleaning" and turnover.cleaning_start_time:
                    elapsed = (now - turnover.cleaning_start_time).seconds // 60
                    remaining = max(0, turnover.estimated_cleaning_duration - elapsed)
                    
                    # AUTO-UPDATE: If cleaning time is complete, mark bed as available
                    if remaining == 0 and bed.status == "cleaning":
                        print(f"🔄 Auto-updating bed {bed.bed_number} from cleaning to available (cleaning time complete)")
                        bed.status = "available"
                        turnover.status = "completed"
                        turnover.cleaning_completion_time = now
                        db.commit()
                        
                        result.update({
                            "current_status": "available",  # Updated status
                            "process_status": "completed",
                            "time_remaining_minutes": 0,
                            "estimated_completion": (turnover.cleaning_start_time + timedelta(minutes=turnover.estimated_cleaning_duration)).isoformat(),
                            "progress_percentage": 100,
                            "auto_updated": True,
                            "message": f"Bed {bed.bed_number} automatically marked as available - cleaning complete!"
                        })
                    else:
                        result.update({
                            "process_status": "cleaning",
                            "time_remaining_minutes": remaining,
                            "estimated_completion": (turnover.cleaning_start_time + timedelta(minutes=turnover.estimated_cleaning_duration)).isoformat(),
                            "progress_percentage": min(100, (elapsed / turnover.estimated_cleaning_duration) * 100)
                        })
                else:
                    result.update({
                        "process_status": "initiated",
                        "time_remaining_minutes": turnover.estimated_cleaning_duration,
                        "progress_percentage": 0
                    })
            else:
                # Check if bed is in cleaning status but no active turnover - auto-fix
                if bed.status == "cleaning":
                    print(f"🔄 Auto-fixing bed {bed.bed_number} - no active turnover but status is cleaning")
                    bed.status = "available"
                    db.commit()
                    result.update({
                        "current_status": "available",  # Updated status
                        "process_status": "completed",
                        "time_remaining_minutes": 0,
                        "progress_percentage": 100,
                        "auto_updated": True,
                        "message": f"Bed {bed.bed_number} automatically marked as available - no active cleaning process"
                    })
                else:
                    result.update({
                        "process_status": "none",
                        "time_remaining_minutes": 0,
                        "progress_percentage": 100
                    })
            
            db.close()
            return result
            
        except Exception as e:
            db.close()
            return {"success": False, "message": str(e)}

    def add_patient_to_queue(self, patient_id: str, department_id: str, bed_type_required: str = "general", priority_level: str = "normal", medical_condition: str = "") -> Dict[str, Any]:
        """Add patient to bed assignment queue."""
        if not DISCHARGE_DEPS:
            return {"success": False, "message": "Discharge dependencies not available"}
        
        from database import SessionLocal, PatientQueue, Patient, Department
        db = SessionLocal()
        try:
            # Get next queue position
            max_position = db.query(PatientQueue).filter(
                PatientQueue.department_id == uuid.UUID(department_id)
            ).count()
            
            queue_entry = PatientQueue(
                patient_id=uuid.UUID(patient_id),
                department_id=uuid.UUID(department_id),
                queue_position=max_position + 1,
                bed_type_required=bed_type_required,
                priority_level=priority_level,
                medical_condition=medical_condition,
                status="waiting"
            )
            
            db.add(queue_entry)
            db.commit()
            db.refresh(queue_entry)
            
            # Get patient and department names for response
            patient = db.query(Patient).filter(Patient.id == uuid.UUID(patient_id)).first()
            department = db.query(Department).filter(Department.id == uuid.UUID(department_id)).first()
            
            result = {
                "success": True,
                "queue_id": str(queue_entry.id),
                "patient_name": f"{patient.first_name} {patient.last_name}" if patient else "Unknown",
                "department_name": department.name if department else "Unknown",
                "queue_position": queue_entry.queue_position,
                "priority_level": priority_level,
                "estimated_wait_time": self._calculate_estimated_wait_time(db, department_id, queue_entry.queue_position)
            }
            
            db.close()
            return result
            
        except Exception as e:
            db.rollback()
            db.close()
            return {"success": False, "message": str(e)}

    def get_patient_queue(self, department_id: str = None, status: str = "waiting") -> Dict[str, Any]:
        """Get current patient queue for bed assignments."""
        if not DISCHARGE_DEPS:
            return {"success": False, "message": "Discharge dependencies not available"}
        
        from database import SessionLocal, PatientQueue, Patient, Department
        db = SessionLocal()
        try:
            query = db.query(PatientQueue).join(Patient).join(Department)
            
            if department_id:
                query = query.filter(PatientQueue.department_id == uuid.UUID(department_id))
            
            if status:
                query = query.filter(PatientQueue.status == status)
            
            queue_entries = query.order_by(PatientQueue.priority_level.desc(), PatientQueue.queue_position).all()
            
            queue_data = []
            for entry in queue_entries:
                queue_data.append({
                    "queue_id": str(entry.id),
                    "patient_id": str(entry.patient_id),
                    "patient_name": f"{entry.patient.first_name} {entry.patient.last_name}",
                    "patient_number": entry.patient.patient_number,
                    "department_name": entry.department.name,
                    "queue_position": entry.queue_position,
                    "priority_level": entry.priority_level,
                    "bed_type_required": entry.bed_type_required,
                    "medical_condition": entry.medical_condition,
                    "wait_time_minutes": (datetime.now() - entry.queue_entry_time).seconds // 60,
                    "status": entry.status
                })
            
            result = {
                "success": True,
                "queue": queue_data,
                "total_waiting": len([e for e in queue_data if e["status"] == "waiting"]),
                "departments": list(set([e["department_name"] for e in queue_data]))
            }
            
            db.close()
            return result
            
        except Exception as e:
            db.close()
            return {"success": False, "message": str(e)}

    def assign_next_patient_to_bed(self, bed_id: str, department_id: str = None) -> Dict[str, Any]:
        """Automatically assign next patient in queue to available bed."""
        if not DISCHARGE_DEPS:
            return {"success": False, "message": "Discharge dependencies not available"}
        
        from database import SessionLocal, PatientQueue, Bed, Patient, Department
        db = SessionLocal()
        try:
            # Verify bed is available
            bed = db.query(Bed).filter(Bed.id == uuid.UUID(bed_id)).first()
            if not bed or bed.status != "available":
                db.close()
                return {"success": False, "message": "Bed is not available for assignment"}
            
            # Find next patient in queue
            query = db.query(PatientQueue).filter(PatientQueue.status == "waiting")
            
            if department_id:
                query = query.filter(PatientQueue.department_id == uuid.UUID(department_id))
            elif bed.room and bed.room.department:
                query = query.filter(PatientQueue.department_id == bed.room.department_id)
            
            next_patient = query.order_by(
                PatientQueue.priority_level.desc(), 
                PatientQueue.queue_position
            ).first()
            
            if not next_patient:
                db.close()
                return {"success": False, "message": "No patients waiting in queue"}
            
            # Assign bed to patient
            next_patient.assigned_bed_id = uuid.UUID(bed_id)
            next_patient.assignment_time = datetime.now()
            next_patient.status = "assigned"
            
            # Update bed status
            bed.status = "occupied"
            bed.current_patient_id = next_patient.patient_id
            bed.updated_at = datetime.now()
            
            # Update any active bed turnover
            from database import BedTurnover
            turnover = db.query(BedTurnover).filter(
                BedTurnover.bed_id == uuid.UUID(bed_id),
                BedTurnover.status == "ready"
            ).first()
            
            if turnover:
                turnover.next_patient_id = next_patient.patient_id
                turnover.status = "assigned"
                turnover.next_assignment_time = datetime.now()
            
            db.commit()
            
            # Get patient details for response
            patient = db.query(Patient).filter(Patient.id == next_patient.patient_id).first()
            
            result = {
                "success": True,
                "assignment": {
                    "bed_id": bed_id,
                    "bed_number": bed.bed_number,
                    "patient_id": str(next_patient.patient_id),
                    "patient_name": f"{patient.first_name} {patient.last_name}" if patient else "Unknown",
                    "patient_number": patient.patient_number if patient else "Unknown",
                    "room_number": bed.room.room_number if bed.room else "Unknown",
                    "assignment_time": next_patient.assignment_time.isoformat()
                },
                "message": f"Patient {patient.first_name} {patient.last_name} assigned to bed {bed.bed_number}"
            }
            
            db.close()
            return result
            
        except Exception as e:
            db.rollback()
            db.close()
            return {"success": False, "message": str(e)}

    def _calculate_estimated_wait_time(self, db, department_id: str, queue_position: int) -> int:
        """Calculate estimated wait time based on queue position and average turnover time."""
        # Simple estimation: assume 90 minutes average turnover time
        from database import BedTurnover
        avg_turnover_time = 90  # minutes
        
        # Get number of patients ahead in queue
        patients_ahead = queue_position - 1
        
        # Estimate based on average turnover times
        estimated_minutes = patients_ahead * avg_turnover_time
        
        return max(0, estimated_minutes)

    # Additional helper methods for equipment and staff management

    def mark_equipment_for_cleaning(self, equipment_id: str = None, bed_id: str = None, equipment_ids: List[str] = None, cleaning_type: str = "surface") -> Dict[str, Any]:
        """Mark equipment for cleaning during bed turnover."""
        if not DISCHARGE_DEPS:
            return {"success": False, "message": "Discharge dependencies not available"}
        
        from database import SessionLocal, BedTurnover, EquipmentTurnover
        db = SessionLocal()
        try:
            # Handle single equipment_id parameter (new API)
            if equipment_id and not bed_id and not equipment_ids:
                # Simple case - mark single equipment for cleaning
                from datetime import datetime
                equipment_turnover = EquipmentTurnover(
                    equipment_id=uuid.UUID(equipment_id),
                    status="cleaning",
                    start_time=datetime.now(),
                    cleaning_type=cleaning_type
                )
                db.add(equipment_turnover)
                db.commit()
                
                result = {
                    "success": True,
                    "equipment_id": equipment_id,
                    "status": "marked_for_cleaning",
                    "cleaning_type": cleaning_type,
                    "message": f"Equipment {equipment_id} marked for {cleaning_type} cleaning"
                }
                db.close()
                return result
            
            # Handle original API (bed_id + equipment_ids list)
            if not bed_id or not equipment_ids:
                db.close()
                return {"success": False, "message": "Either provide equipment_id alone, or both bed_id and equipment_ids"}
                
            # Get active turnover for this bed
            turnover = db.query(BedTurnover).filter(
                BedTurnover.bed_id == uuid.UUID(bed_id),
                BedTurnover.status.in_(["initiated", "cleaning"])
            ).first()
            
            if not turnover:
                db.close()
                return {"success": False, "message": "No active turnover found for this bed"}
            
            equipment_records = []
            for equipment_id in equipment_ids:
                equipment_turnover = EquipmentTurnover(
                    bed_turnover_id=turnover.id,
                    equipment_id=uuid.UUID(equipment_id),
                    status="needs_cleaning",
                    cleaning_required=True,
                    cleaning_type=cleaning_type,
                    release_time=datetime.now()
                )
                db.add(equipment_turnover)
                equipment_records.append(equipment_turnover)
            
            db.commit()
            
            result = {
                "success": True,
                "equipment_count": len(equipment_records),
                "cleaning_type": cleaning_type,
                "message": f"Marked {len(equipment_records)} pieces of equipment for {cleaning_type} cleaning"
            }
            
            db.close()
            return result
            
        except Exception as e:
            db.rollback()
            db.close()
            return {"success": False, "message": str(e)}

    def update_turnover_progress(self, turnover_id: str, progress_status: str) -> Dict[str, Any]:
        """Update bed turnover progress status."""
        if not DISCHARGE_DEPS:
            return {"success": False, "message": "Discharge dependencies not available"}
        
        try:
            from database import SessionLocal, BedTurnover
            db = SessionLocal()
            
            # Find the turnover record
            turnover = db.query(BedTurnover).filter(BedTurnover.turnover_id == turnover_id).first()
            
            if not turnover:
                db.close()
                return {"success": False, "message": f"Turnover {turnover_id} not found"}
            
            # Update progress status
            turnover.progress_status = progress_status
            db.commit()
            
            result = {
                "success": True,
                "message": f"Turnover progress updated to {progress_status}",
                "turnover_id": turnover_id,
                "new_status": progress_status,
                "updated_at": datetime.now().isoformat()
            }
            
            db.close()
            return result
            
        except Exception as e:
            return {"success": False, "message": f"Failed to update turnover progress: {str(e)}"}

    def get_bed_turnover_details(self, bed_id: str) -> Dict[str, Any]:
        """Get detailed information about bed turnover process."""
        if not DISCHARGE_DEPS:
            return {"success": False, "message": "Discharge dependencies not available"}
        
        try:
            from database import SessionLocal, BedTurnover, Bed
            db = SessionLocal()
            
            # Find the bed
            bed = db.query(Bed).filter(Bed.bed_id == bed_id).first()
            if not bed:
                db.close()
                return {"success": False, "message": f"Bed {bed_id} not found"}
            
            # Find active turnover
            active_turnover = db.query(BedTurnover).filter(
                BedTurnover.bed_id == bed_id,
                BedTurnover.status.in_(["in_progress", "cleaning", "inspection"])
            ).first()
            
            if not active_turnover:
                db.close()
                return {
                    "success": True,
                    "bed_id": bed_id,
                    "status": "no_active_turnover",
                    "message": "No active turnover process for this bed"
                }
            
            result = {
                "success": True,
                "bed_id": bed_id,
                "turnover_id": active_turnover.turnover_id,
                "status": active_turnover.status,
                "progress_status": getattr(active_turnover, 'progress_status', 'unknown'),
                "started_at": active_turnover.start_time.isoformat() if active_turnover.start_time else None,
                "estimated_completion": active_turnover.estimated_completion_time.isoformat() if hasattr(active_turnover, 'estimated_completion_time') and active_turnover.estimated_completion_time else None,
                "turnover_type": getattr(active_turnover, 'turnover_type', 'standard'),
                "priority": getattr(active_turnover, 'priority_level', 'normal')
            }
            
            db.close()
            return result
            
        except Exception as e:
            return {"success": False, "message": f"Failed to get turnover details: {str(e)}"}

    def complete_equipment_cleaning(self, equipment_id: str) -> Dict[str, Any]:
        """Complete equipment cleaning process."""
        if not DISCHARGE_DEPS:
            return {"success": False, "message": "Discharge dependencies not available"}
        
        try:
            from database import SessionLocal, EquipmentTurnover
            db = SessionLocal()
            
            # Find equipment turnover record
            equipment_turnover = db.query(EquipmentTurnover).filter(
                EquipmentTurnover.equipment_id == equipment_id,
                EquipmentTurnover.status == "cleaning"
            ).first()
            
            if not equipment_turnover:
                db.close()
                return {"success": False, "message": f"No active cleaning process found for equipment {equipment_id}"}
            
            # Update status to cleaned
            equipment_turnover.status = "cleaned"
            equipment_turnover.completion_time = datetime.now()
            db.commit()
            
            result = {
                "success": True,
                "message": f"Equipment {equipment_id} cleaning completed",
                "equipment_id": equipment_id,
                "completed_at": datetime.now().isoformat(),
                "status": "cleaned"
            }
            
            db.close()
            return result
            
        except Exception as e:
            return {"success": False, "message": f"Failed to complete equipment cleaning: {str(e)}"}

    def get_equipment_turnover_status(self, equipment_id: str) -> Dict[str, Any]:
        """Get equipment turnover status."""
        if not DISCHARGE_DEPS:
            return {"success": False, "message": "Discharge dependencies not available"}
        
        try:
            from database import SessionLocal, EquipmentTurnover, Equipment
            db = SessionLocal()
            
            # Find equipment
            equipment = db.query(Equipment).filter(Equipment.equipment_id == equipment_id).first()
            if not equipment:
                db.close()
                return {"success": False, "message": f"Equipment {equipment_id} not found"}
            
            # Find active turnover
            active_turnover = db.query(EquipmentTurnover).filter(
                EquipmentTurnover.equipment_id == equipment_id,
                EquipmentTurnover.status.in_(["cleaning", "maintenance", "inspection"])
            ).first()
            
            if not active_turnover:
                db.close()
                return {
                    "success": True,
                    "equipment_id": equipment_id,
                    "status": "available",
                    "message": "Equipment is available for use"
                }
            
            result = {
                "success": True,
                "equipment_id": equipment_id,
                "turnover_status": active_turnover.status,
                "started_at": active_turnover.start_time.isoformat() if active_turnover.start_time else None,
                "estimated_completion": active_turnover.estimated_completion_time.isoformat() if hasattr(active_turnover, 'estimated_completion_time') and active_turnover.estimated_completion_time else None,
                "cleaning_type": getattr(active_turnover, 'cleaning_type', 'standard')
            }
            
            db.close()
            return result
            
        except Exception as e:
            return {"success": False, "message": f"Failed to get equipment turnover status: {str(e)}"}

    # ---- Comprehensive Discharge Workflow ----

    def discharge_patient_complete(self, patient_id: str = None, bed_id: str = None, patient_name: str = None, 
                                 patient_number: str = None, discharge_condition: str = "stable", discharge_destination: str = "home") -> Dict[str, Any]:
        """Complete comprehensive patient discharge workflow including bed turnover."""
        if not DISCHARGE_DEPS:
            return {"success": False, "message": "Discharge dependencies not available"}
        
        from database import SessionLocal, Patient, Bed, DischargeReport, BedTurnover
        db = SessionLocal()
        
        try:
            # Find patient by ID, bed ID, or name
            patient = None
            bed = None
            
            if patient_id and patient_id not in [None, "", "undefined", "null"]:
                try:
                    patient = db.query(Patient).filter(Patient.id == uuid.UUID(patient_id)).first()
                except (ValueError, TypeError):
                    # If patient_id is not a valid UUID, skip this check
                    patient = None
            elif patient_number:
                # Search by patient number (e.g., P1025)
                patient = db.query(Patient).filter(Patient.patient_number == patient_number).first()
            elif bed_id:
                bed = db.query(Bed).filter(Bed.id == uuid.UUID(bed_id)).first()
                if bed and bed.patient_id:
                    patient = db.query(Patient).filter(Patient.id == bed.patient_id).first()
                else:
                    # Fallback: use most recent turnover to identify previous patient
                    recent_turnover = db.query(BedTurnover).filter(BedTurnover.bed_id == uuid.UUID(bed_id)).order_by(BedTurnover.discharge_time.desc()).first()
                    if recent_turnover and recent_turnover.previous_patient_id:
                        patient = db.query(Patient).filter(Patient.id == recent_turnover.previous_patient_id).first()
            elif patient_name:
                # Search by name (partial match)
                patient = db.query(Patient).filter(
                    Patient.first_name.ilike(f"%{patient_name}%") | 
                    Patient.last_name.ilike(f"%{patient_name}%")
                ).first()
            
            if not patient:
                db.close()
                return {"success": False, "message": "Patient not found"}

            if patient.status == "discharged":
                db.close()
                return {"success": False, "message": f"Patient {patient.first_name} {patient.last_name} is already discharged"}

            # Get bed if not already found
            if not bed:
                bed = db.query(Bed).filter(Bed.patient_id == patient.id).first()

            if not bed:
                # No bed assigned (e.g. registered but never admitted to a ward):
                # there is no bed turnover or bed-based report, so just close the record.
                patient.status = "discharged"
                patient.updated_at = datetime.now()
                db.commit()

                self.log_interaction(
                    query=f"Complete discharge for patient {patient.first_name} {patient.last_name}",
                    response="Patient had no bed assigned; status set to discharged.",
                    tool_used="discharge_patient_complete"
                )

                result = {
                    "success": True,
                    "message": f"Patient {patient.first_name} {patient.last_name} discharged successfully (no bed was assigned)",
                    "patient_id": str(patient.id),
                    "bed_id": None,
                    "report_number": None,
                    "report_download_url": None
                }
                db.close()
                return result
            
            # Generate discharge report with explicit patient_id BEFORE clearing bed assignment
            discharge_result = self.generator.generate_discharge_report(
                bed_id=str(bed.id),
                discharge_condition=discharge_condition,
                discharge_destination=discharge_destination,
                patient_id=str(patient.id)
            )
            
            if not discharge_result.get("success"):
                db.close()
                return {"success": False, "message": f"Failed to generate discharge report: {discharge_result.get('message')}"}
            
            # Extract report number and construct download URL
            report_number = None
            try:
                report_number = (
                    discharge_result.get("report_number")
                    or (discharge_result.get("data", {}) or {}).get("report_number")
                    or (discharge_result.get("report", {}) or {}).get("number")
                    or (discharge_result.get("report", {}) or {}).get("report_number")
                )
            except Exception:
                report_number = None
            download_url = f"/discharge/{report_number}.pdf" if report_number else None
            
            # Start bed turnover process (puts bed into cleaning)
            turnover_result = self.start_bed_turnover_process(
                bed_id=str(bed.id),
                previous_patient_id=str(patient.id),
                turnover_type="standard",
                priority_level="normal"
            )
            
            if not turnover_result.get("success"):
                db.close()
                return {"success": False, "message": f"Failed to start bed turnover: {turnover_result.get('message')}"}
            
            # Only now clear bed assignment and update statuses
            patient.status = "discharged"
            patient.updated_at = datetime.now()
            bed.discharge_date = datetime.now()
            bed.patient_id = None
            bed.status = "cleaning"
            
            # Commit all changes
            db.commit()
            
            # Schedule automatic bed cleaning completion (30 minutes)
            import threading
            import time
            
            def auto_complete_cleaning():
                time.sleep(30 * 60)  # 30 minutes
                try:
                    # Auto-complete the cleaning process
                    self.complete_bed_cleaning_auto(str(bed.id))
                except Exception as e:
                    print(f"Auto-complete cleaning failed: {e}")
            
            # Start the timer in a separate thread
            cleaning_timer = threading.Thread(target=auto_complete_cleaning, daemon=True)
            cleaning_timer.start()
            
            result = {
                "success": True,
                "message": f"Patient {patient.first_name} {patient.last_name} discharged successfully" + (f". Discharge report {report_number} generated and ready for download." if report_number else ""),
                "patient_id": str(patient.id),
                "bed_id": str(bed.id),
                "report_number": report_number,
                "report_download_url": download_url,
                "discharge_report": discharge_result,
                "bed_turnover": turnover_result,
                "cleaning_timer": "30 minutes",
                "next_steps": [
                    "Bed is now in cleaning process (30 minutes)",
                    "Patient status updated to 'discharged'",
                    "Discharge report generated and available for download",
                    "Bed will automatically become available after cleaning"
                ]
            }
            
            self.log_interaction(
                query=f"Complete discharge for patient {patient.first_name} {patient.last_name}",
                response=f"Discharge completed successfully. Bed {bed.bed_number} in cleaning for 30 minutes.",
                tool_used="discharge_patient_complete"
            )
            
            db.close()
            return result
            
        except Exception as e:
            db.rollback()
            db.close()
            return {"success": False, "message": f"Discharge workflow failed: {str(e)}"}

    def complete_bed_cleaning_auto(self, bed_id: str) -> Dict[str, Any]:
        """Automatically complete bed cleaning after timer expires."""
        if not DISCHARGE_DEPS:
            return {"success": False, "message": "Discharge dependencies not available"}
        
        from database import SessionLocal, Bed, BedTurnover
        db = SessionLocal()
        
        try:
            # Find the active turnover process
            turnover = db.query(BedTurnover).filter(
                BedTurnover.bed_id == uuid.UUID(bed_id),
                BedTurnover.status.in_(["initiated", "cleaning"])
            ).first()
            
            if not turnover:
                db.close()
                return {"success": False, "message": "No active turnover process found"}
            
            # Update turnover status
            turnover.status = "cleaning_complete"
            turnover.cleaning_end_time = datetime.now()
            turnover.inspection_passed = True
            turnover.status = "ready"
            turnover.ready_time = datetime.now()
            
            # Update bed status
            bed = db.query(Bed).filter(Bed.id == uuid.UUID(bed_id)).first()
            if bed:
                bed.status = "available"
                bed.updated_at = datetime.now()
            
            db.commit()
            
            result = {
                "success": True,
                "message": f"Bed {bed.bed_number if bed else 'Unknown'} cleaning completed automatically",
                "status": "ready",
                "completion_time": turnover.ready_time.isoformat()
            }
            
            db.close()
            return result
            
        except Exception as e:
            db.rollback()
            db.close()
            return {"success": False, "message": f"Auto-complete cleaning failed: {str(e)}"}

    def get_patient_discharge_status(self, patient_id: str = None, patient_name: str = None) -> Dict[str, Any]:
        """Get patient discharge status and related information."""
        if not DISCHARGE_DEPS:
            return {"success": False, "message": "Discharge dependencies not available"}
        
        from database import SessionLocal, Patient, Bed, DischargeReport
        db = SessionLocal()
        
        try:
            # Find patient
            patient = None
            if patient_id:
                patient = db.query(Patient).filter(Patient.id == uuid.UUID(patient_id)).first()
            elif patient_name:
                # Use robust name lookup
                patient = self._find_patient_by_name(db, patient_name)
            
            if not patient:
                db.close()
                return {"success": False, "message": "Patient not found"}
            
            # Get bed information
            bed = db.query(Bed).filter(Bed.patient_id == patient.id).first()
            
            # Get discharge reports
            discharge_reports = db.query(DischargeReport).filter(
                DischargeReport.patient_id == patient.id
            ).order_by(DischargeReport.created_at.desc()).all()
            
            result = {
                "success": True,
                "patient": {
                    "id": str(patient.id),
                    "name": f"{patient.first_name} {patient.last_name}",
                    "status": patient.status,
                    "patient_number": patient.patient_number
                },
                "bed_assignment": {
                    "bed_id": str(bed.id) if bed else None,
                    "bed_number": bed.bed_number if bed else None,
                    "room_number": bed.room.room_number if bed and bed.room else None,
                    "status": bed.status if bed else None
                } if bed else None,
                "discharge_reports": [
                    {
                        "report_id": str(report.id),
                        "report_number": report.report_number,
                        "discharge_date": report.discharge_date.isoformat() if report.discharge_date else None,
                        "condition": report.discharge_condition,
                        "destination": report.discharge_destination
                    } for report in discharge_reports
                ],
                "total_discharge_reports": len(discharge_reports)
            }
            
            db.close()
            return result
            
        except Exception as e:
            db.close()
            return {"success": False, "message": f"Failed to get discharge status: {str(e)}"}

    def add_treatment_record_by_codes(self,
                                      patient_id: str = None,
                                      patient_number: str = None,
                                      staff_id: str = None,
                                      employee_id: str = None,
                                      treatment_type: str = None,
                                      treatment_name: str = None,
                                      start_date: str = None) -> Dict[str, Any]:
        """Add a treatment record using patient_number and employee_id (staff code).
        Falls back to UUIDs if provided. Resolves doctor_id from staff.user_id.
        Allows optional start_date (ISO date/time or YYYY-MM-DD)."""
        if not DISCHARGE_DEPS:
            return {"success": False, "message": "Discharge dependencies not available"}
        if not treatment_type or not treatment_name:
            return {"success": False, "message": "treatment_type and treatment_name are required"}

        from database import SessionLocal, TreatmentRecord as CoreTreatmentRecord, Patient as CorePatient, Staff as CoreStaff
        db = SessionLocal()
        try:
            # Resolve patient
            patient_uuid = None
            if patient_id:
                try:
                    patient_uuid = uuid.UUID(patient_id)
                except Exception:
                    patient_uuid = None
            if not patient_uuid and patient_number:
                p = db.query(CorePatient).filter(CorePatient.patient_number == patient_number).first()
                if not p:
                    db.close()
                    return {"success": False, "message": f"Patient not found for number {patient_number}"}
                patient_uuid = p.id
            if not patient_uuid:
                db.close()
                return {"success": False, "message": "Provide patient_number or patient_id"}

            # Resolve staff to doctor user id
            staff_rec = None
            if employee_id:
                staff_rec = db.query(CoreStaff).filter(CoreStaff.employee_id == employee_id).first()
            elif staff_id:
                try:
                    staff_uuid = uuid.UUID(staff_id)
                    staff_rec = db.query(CoreStaff).filter(CoreStaff.id == staff_uuid).first()
                except Exception:
                    staff_rec = None
            if not staff_rec:
                db.close()
                return {"success": False, "message": "Staff not found for given employee_id/staff_id"}
            if not getattr(staff_rec, 'user_id', None):
                db.close()
                return {"success": False, "message": "Selected staff has no linked user_id"}

            doctor_user_id = staff_rec.user_id

            # Parse optional start_date
            start_dt = datetime.now()
            if start_date:
                try:
                    # Accept YYYY-MM-DD or full ISO
                    if len(start_date) == 10:
                        start_dt = datetime.fromisoformat(start_date)
                    else:
                        start_dt = datetime.fromisoformat(start_date)
                except Exception:
                    # keep default now
                    pass

            # Enforce DB limits and preserve full text in notes when truncated
            full_type = (treatment_type or '').strip()
            full_name = (treatment_name or '').strip()
            type_db = full_type[:50]
            name_db = full_name[:100]
            notes_extra = None
            if len(full_type) > 50 or len(full_name) > 100:
                notes_extra = f"Full treatment_type: {full_type}\nFull treatment_name: {full_name}"

            tr = CoreTreatmentRecord(
                patient_id=patient_uuid,
                doctor_id=doctor_user_id,
                treatment_type=type_db,
                treatment_name=name_db,
                start_date=start_dt,
                notes=notes_extra
            )
            db.add(tr)
            db.commit()
            db.refresh(tr)
            result = {"id": str(tr.id), "patient_id": str(patient_uuid), "doctor_user_id": str(doctor_user_id)}
            db.close()
            return {"success": True, "data": result}
        except Exception as e:
            db.rollback()
            db.close()
            return {"success": False, "message": str(e)}

    def auto_update_expired_cleaning_beds(self) -> Dict[str, Any]:
        """Automatically update beds that have completed their cleaning time to 'available' status.
        
        This method checks all beds in 'cleaning' status and updates them to 'available' 
        if their estimated cleaning duration has elapsed.
        """
        if not DISCHARGE_DEPS:
            return {"success": False, "message": "Discharge dependencies not available"}
        
        from database import SessionLocal, BedTurnover, Bed
        db = SessionLocal()
        try:
            updated_beds = []
            now = datetime.now()
            
            # Find all active cleaning processes
            active_turnovers = db.query(BedTurnover).filter(
                BedTurnover.status == "cleaning",
                BedTurnover.cleaning_start_time.isnot(None)
            ).all()
            
            for turnover in active_turnovers:
                elapsed_minutes = (now - turnover.cleaning_start_time).seconds // 60
                
                # If cleaning time has elapsed
                if elapsed_minutes >= turnover.estimated_cleaning_duration:
                    bed = db.query(Bed).filter(Bed.id == turnover.bed_id).first()
                    if bed and bed.status == "cleaning":
                        # Update bed to available
                        bed.status = "available"
                        bed.updated_at = now
                        
                        # Mark turnover as completed
                        turnover.status = "completed"
                        turnover.cleaning_completion_time = now
                        
                        updated_beds.append({
                            "bed_id": str(bed.id),
                            "bed_number": bed.bed_number,
                            "room_number": bed.room.room_number if bed.room else "Unknown",
                            "elapsed_minutes": elapsed_minutes,
                            "estimated_duration": turnover.estimated_cleaning_duration
                        })
                        
                        print(f"🔄 Auto-updated bed {bed.bed_number} from cleaning to available after {elapsed_minutes} minutes")
            
            # Also check for beds stuck in cleaning status without active turnover
            orphaned_cleaning_beds = db.query(Bed).filter(
                Bed.status == "cleaning"
            ).all()
            
            for bed in orphaned_cleaning_beds:
                # Check if there's an active turnover for this bed
                active_turnover = db.query(BedTurnover).filter(
                    BedTurnover.bed_id == bed.id,
                    BedTurnover.status.in_(["cleaning", "initiated"])
                ).first()
                
                if not active_turnover:
                    # No active turnover, but bed is in cleaning status - fix it
                    bed.status = "available"
                    bed.updated_at = now
                    
                    updated_beds.append({
                        "bed_id": str(bed.id),
                        "bed_number": bed.bed_number,
                        "room_number": bed.room.room_number if bed.room else "Unknown",
                        "reason": "orphaned_cleaning_status"
                    })
                    
                    print(f"🔧 Fixed orphaned bed {bed.bed_number} - removed cleaning status without active turnover")
            
            db.commit()
            
            result = {
                "success": True,
                "updated_count": len(updated_beds),
                "updated_beds": updated_beds,
                "timestamp": now.isoformat(),
                "message": f"Auto-updated {len(updated_beds)} beds from cleaning to available status"
            }
            
            db.close()
            return result
            
        except Exception as e:
            db.rollback()
            db.close()
            return {"success": False, "message": str(e)}
