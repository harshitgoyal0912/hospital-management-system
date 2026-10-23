"""
Discharge Report MCP Tools
=========================

Additional MCP tools for the comprehensive server to handle discharge reports
and related tracking functionality.
"""

from typing import Dict, Any
import uuid
from datetime import datetime
from discharge_report_service import PatientDischargeReportGenerator
from discharge_report_models import TreatmentRecord, EquipmentUsage, StaffAssignment
from database import get_db_session

# Add these tools to your comprehensive_server.py

@mcp.tool()
def generate_discharge_report(bed_id: str,
                            discharge_condition: str = "stable",
                            discharge_destination: str = "home",
                            discharge_instructions: str = "",
                            follow_up_required: str = "",
                            generated_by_user_id: str = None) -> Dict[str, Any]:
    """Generate a comprehensive discharge report for a patient being discharged from a bed."""
    if not DATABASE_AVAILABLE:
        return {"success": False, "message": "Database not available"}
    
    try:
        generator = PatientDischargeReportGenerator()
        result = generator.generate_discharge_report(
            bed_id=bed_id,
            discharge_condition=discharge_condition,
            discharge_destination=discharge_destination,
            discharge_instructions=discharge_instructions,
            follow_up_required=follow_up_required,
            generated_by_user_id=generated_by_user_id
        )
        return result
    except Exception as e:
        return {"success": False, "message": f"Failed to generate discharge report: {str(e)}"}

@mcp.tool()
def add_treatment_record(patient_id: str,
                        doctor_id: str,
                        treatment_type: str,
                        treatment_name: str,
                        description: str = "",
                        dosage: str = "",
                        frequency: str = "",
                        bed_id: str = None) -> Dict[str, Any]:
    """Add a treatment record for a patient."""
    if not DATABASE_AVAILABLE:
        return {"success": False, "message": "Database not available"}
    
    try:
        db = get_db_session()
        
        treatment = TreatmentRecord(
            patient_id=uuid.UUID(patient_id),
            doctor_id=uuid.UUID(doctor_id),
            treatment_type=treatment_type,
            treatment_name=treatment_name,
            description=description,
            dosage=dosage,
            frequency=frequency,
            start_date=datetime.now(),
            bed_id=uuid.UUID(bed_id) if bed_id else None
        )
        
        db.add(treatment)
        db.commit()
        db.refresh(treatment)
        
        result = {
            "id": str(treatment.id),
            "patient_id": patient_id,
            "doctor_id": doctor_id,
            "treatment_type": treatment_type,
            "treatment_name": treatment_name,
            "start_date": treatment.start_date.isoformat()
        }
        
        db.close()
        return {"success": True, "message": "Treatment record added successfully", "data": result}
        
    except Exception as e:
        return {"success": False, "message": f"Failed to add treatment record: {str(e)}"}

@mcp.tool()
def add_equipment_usage(patient_id: str,
                       equipment_id: str,
                       staff_id: str,
                       purpose: str,
                       duration_minutes: int = None,
                       settings: str = "",
                       readings: str = "",
                       bed_id: str = None) -> Dict[str, Any]:
    """Record equipment usage for a patient."""
    if not DATABASE_AVAILABLE:
        return {"success": False, "message": "Database not available"}
    
    try:
        db = get_db_session()
        
        equipment_usage = EquipmentUsage(
            patient_id=uuid.UUID(patient_id),
            equipment_id=uuid.UUID(equipment_id),
            staff_id=uuid.UUID(staff_id),
            purpose=purpose,
            start_time=datetime.now(),
            duration_minutes=duration_minutes,
            settings=settings,
            readings=readings,
            bed_id=uuid.UUID(bed_id) if bed_id else None
        )
        
        if duration_minutes:
            equipment_usage.end_time = datetime.now()
            equipment_usage.status = "completed"
        
        db.add(equipment_usage)
        db.commit()
        db.refresh(equipment_usage)
        
        result = {
            "id": str(equipment_usage.id),
            "patient_id": patient_id,
            "equipment_id": equipment_id,
            "staff_id": staff_id,
            "purpose": purpose,
            "start_time": equipment_usage.start_time.isoformat()
        }
        
        db.close()
        return {"success": True, "message": "Equipment usage recorded successfully", "data": result}
        
    except Exception as e:
        return {"success": False, "message": f"Failed to record equipment usage: {str(e)}"}

@mcp.tool()
def assign_staff_to_patient(patient_id: str,
                           staff_id: str,
                           assignment_type: str,
                           shift: str = "",
                           responsibilities: str = "",
                           bed_id: str = None) -> Dict[str, Any]:
    """Assign staff member to a patient."""
    if not DATABASE_AVAILABLE:
        return {"success": False, "message": "Database not available"}
    
    try:
        db = get_db_session()
        
        staff_assignment = StaffAssignment(
            patient_id=uuid.UUID(patient_id),
            staff_id=uuid.UUID(staff_id),
            assignment_type=assignment_type,
            start_date=datetime.now(),
            shift=shift,
            responsibilities=responsibilities,
            bed_id=uuid.UUID(bed_id) if bed_id else None
        )
        
        db.add(staff_assignment)
        db.commit()
        db.refresh(staff_assignment)
        
        result = {
            "id": str(staff_assignment.id),
            "patient_id": patient_id,
            "staff_id": staff_id,
            "assignment_type": assignment_type,
            "start_date": staff_assignment.start_date.isoformat()
        }
        
        db.close()
        return {"success": True, "message": "Staff assigned successfully", "data": result}
        
    except Exception as e:
        db.rollback()
        db.close()
        return {"success": False, "message": f"Failed to assign staff: {str(e)}"}

@mcp.tool()
def complete_equipment_usage(usage_id: str, readings: str = "", notes: str = "") -> Dict[str, Any]:
    """Mark equipment usage as completed and record final readings."""
    if not DATABASE_AVAILABLE:
        return {"success": False, "message": "Database not available"}
    
    try:
        db = get_db_session()
        
        usage = db.query(EquipmentUsage).filter(EquipmentUsage.id == uuid.UUID(usage_id)).first()
        if not usage:
            db.close()
            return {"success": False, "message": "Equipment usage record not found"}
        
        usage.end_time = datetime.now()
        usage.status = "completed"
        usage.duration_minutes = int((usage.end_time - usage.start_time).total_seconds() / 60)
        
        if readings:
            usage.readings = readings
        if notes:
            usage.notes = notes
        
        db.commit()
        db.refresh(usage)
        
        result = {
            "id": str(usage.id),
            "end_time": usage.end_time.isoformat(),
            "duration_minutes": usage.duration_minutes,
            "status": usage.status
        }
        
        db.close()
        return {"success": True, "message": "Equipment usage completed", "data": result}
        
    except Exception as e:
        return {"success": False, "message": f"Failed to complete equipment usage: {str(e)}"}

@mcp.tool()
def update_treatment_status(treatment_id: str, 
                           status: str, 
                           effectiveness: str = "",
                           notes: str = "",
                           side_effects: str = "") -> Dict[str, Any]:
    """Update the status and effectiveness of a treatment."""
    if not DATABASE_AVAILABLE:
        return {"success": False, "message": "Database not available"}
    
    try:
        db = get_db_session()
        
        treatment = db.query(TreatmentRecord).filter(TreatmentRecord.id == uuid.UUID(treatment_id)).first()
        if not treatment:
            db.close()
            return {"success": False, "message": "Treatment record not found"}
        
        treatment.status = status
        if effectiveness:
            treatment.effectiveness = effectiveness
        if notes:
            treatment.notes = notes
        if side_effects:
            treatment.side_effects = side_effects
        
        if status in ["completed", "discontinued"]:
            treatment.end_date = datetime.now()
        
        db.commit()
        db.refresh(treatment)
        
        result = {
            "id": str(treatment.id),
            "status": treatment.status,
            "effectiveness": treatment.effectiveness,
            "end_date": treatment.end_date.isoformat() if treatment.end_date else None
        }
        
        db.close()
        return {"success": True, "message": "Treatment status updated", "data": result}
        
    except Exception as e:
        return {"success": False, "message": f"Failed to update treatment: {str(e)}"}

@mcp.tool()
def get_patient_treatment_history(patient_id: str, 
                                 from_date: str = None, 
                                 to_date: str = None) -> Dict[str, Any]:
    """Get complete treatment history for a patient."""
    if not DATABASE_AVAILABLE:
        return {"success": False, "message": "Database not available"}
    
    try:
        db = get_db_session()
        
        query = db.query(TreatmentRecord).filter(TreatmentRecord.patient_id == uuid.UUID(patient_id))
        
        if from_date:
            query = query.filter(TreatmentRecord.start_date >= datetime.fromisoformat(from_date))
        if to_date:
            query = query.filter(TreatmentRecord.start_date <= datetime.fromisoformat(to_date))
        
        treatments = query.order_by(TreatmentRecord.start_date.desc()).all()
        
        result = [{
            "id": str(t.id),
            "treatment_type": t.treatment_type,
            "treatment_name": t.treatment_name,
            "description": t.description,
            "dosage": t.dosage,
            "frequency": t.frequency,
            "duration": t.duration,
            "start_date": t.start_date.isoformat(),
            "end_date": t.end_date.isoformat() if t.end_date else None,
            "status": t.status,
            "effectiveness": t.effectiveness,
            "doctor_name": f"{t.doctor.first_name} {t.doctor.last_name}" if t.doctor else "Unknown",
            "notes": t.notes,
            "side_effects": t.side_effects
        } for t in treatments]
        
        db.close()
        return {"success": True, "data": result, "count": len(result)}
        
    except Exception as e:
        return {"success": False, "message": f"Failed to get treatment history: {str(e)}"}

@mcp.tool()
def get_discharge_report(report_id: str) -> Dict[str, Any]:
    """Retrieve a previously generated discharge report."""
    if not DATABASE_AVAILABLE:
        return {"success": False, "message": "Database not available"}
    
    try:
        from discharge_report_models import DischargeReport
        db = get_db_session()
        
        report = db.query(DischargeReport).filter(DischargeReport.id == uuid.UUID(report_id)).first()
        if not report:
            db.close()
            return {"success": False, "message": "Discharge report not found"}
        
        result = {
            "id": str(report.id),
            "report_number": report.report_number,
            "patient_name": f"{report.patient.first_name} {report.patient.last_name}" if report.patient else "Unknown",
            "admission_date": report.admission_date.isoformat(),
            "discharge_date": report.discharge_date.isoformat(),
            "length_of_stay_days": report.length_of_stay_days,
            "discharge_condition": report.discharge_condition,
            "discharge_destination": report.discharge_destination,
            "discharge_instructions": report.discharge_instructions,
            "follow_up_required": report.follow_up_required,
            "generated_at": report.created_at.isoformat(),
            "generated_by": f"{report.generated_by_user.first_name} {report.generated_by_user.last_name}" if report.generated_by_user else "System"
        }
        
        db.close()
        return {"success": True, "data": result}
        
    except Exception as e:
        return {"success": False, "message": f"Failed to retrieve discharge report: {str(e)}"}
