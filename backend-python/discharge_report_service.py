"""
Patient Discharge Report Generator
=================================

Comprehensive discharge report system that generates detailed reports
including admission details, treatments, equipment usage, staff assignments,
and discharge recommendations.
"""

import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from database import SessionLocal, Patient, Bed, User, Staff, Equipment, TreatmentRecord, EquipmentUsage, StaffAssignment, DischargeReport

class PatientDischargeReportGenerator:
    """Generate comprehensive discharge reports for patients."""
    
    def __init__(self):
        self.session = SessionLocal()
    
    def generate_discharge_report(self, 
                                bed_id: str, 
                                discharge_date: datetime = None,
                                discharge_condition: str = "stable",
                                discharge_destination: str = "home",
                                discharge_instructions: str = "",
                                follow_up_required: str = "",
                                generated_by_user_id: str = None) -> Dict[str, Any]:
        """
        Generate a comprehensive discharge report for a patient.
        
        Args:
            bed_id: UUID of the bed being discharged
            discharge_date: Date of discharge (defaults to now)
            discharge_condition: Patient's condition at discharge
            discharge_destination: Where patient is going after discharge
            discharge_instructions: Instructions for patient
            follow_up_required: Follow-up care requirements
            generated_by_user_id: User generating the report
        """
        
        try:
            # Get bed and patient information
            bed = self.session.query(Bed).filter(Bed.id == uuid.UUID(bed_id)).first()
            if not bed or not bed.patient_id:
                return {"success": False, "message": "Bed not found or no patient assigned"}
            
            patient = bed.patient
            if not patient:
                return {"success": False, "message": "Patient not found"}
            
            discharge_date = discharge_date or datetime.now()
            
            # If no admission date is set, use a reasonable default that includes historical data
            if bed.admission_date:
                admission_date = bed.admission_date
            else:
                # Default to 30 days ago to include recent supply usage and treatments
                admission_date = datetime.now() - timedelta(days=30)
                print(f"⚠️ No admission date set for bed {bed.bed_number}, using default: {admission_date}")
            
            length_of_stay = (discharge_date - admission_date).days
            
            # Generate report sections
            report_data = {
                "patient_summary": self._get_patient_summary(patient, bed, admission_date, discharge_date),
                "treatment_summary": self._get_treatment_summary(patient.id, admission_date, discharge_date),
                "equipment_summary": self._get_equipment_summary(patient.id, admission_date, discharge_date),
                "staff_summary": self._get_staff_summary(patient.id, admission_date, discharge_date),
                "medications": self._get_medications_summary(patient.id, admission_date, discharge_date),
                "supply_usage": self._get_supply_usage_summary(patient.id, admission_date, discharge_date),
                "procedures": self._get_procedures_summary(patient.id, admission_date, discharge_date),
                "appointments": self._get_appointments_summary(patient.id, admission_date, discharge_date)
            }
            
            # Create discharge report record
            report_number = f"DR-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
            
            # Use Admin User as default if no user provided
            default_user_id = "e89313e0-a3ff-4dc6-b163-983a96161e8f"  # Stephanie Smith (Admin)
            generated_by_id = uuid.UUID(generated_by_user_id) if generated_by_user_id else uuid.UUID(default_user_id)
            
            discharge_report = DischargeReport(
                patient_id=patient.id,
                bed_id=uuid.UUID(bed_id),
                generated_by=generated_by_id,
                report_number=report_number,
                admission_date=admission_date,
                discharge_date=discharge_date,
                length_of_stay_days=length_of_stay,
                patient_summary=json.dumps(report_data["patient_summary"]),
                treatment_summary=json.dumps(report_data["treatment_summary"]),
                equipment_summary=json.dumps(report_data["equipment_summary"]),
                staff_summary=json.dumps(report_data["staff_summary"]),
                medications=json.dumps(report_data["medications"]),
                supply_usage=json.dumps(report_data["supply_usage"]),
                procedures=json.dumps(report_data["procedures"]),
                discharge_instructions=discharge_instructions,
                follow_up_required=follow_up_required,
                discharge_condition=discharge_condition,
                discharge_destination=discharge_destination
            )
            
            self.session.add(discharge_report)
            self.session.commit()
            
            # Generate formatted report
            formatted_report = self._format_discharge_report(report_data, discharge_report)
            
            return {
                "success": True,
                "report_id": str(discharge_report.id),
                "report_number": report_number,
                "patient_name": f"{patient.first_name} {patient.last_name}",
                "formatted_report": formatted_report,
                "raw_data": report_data,
                "supply_usage": report_data["supply_usage"],  # Include supply usage in main response
                "equipment_usage": report_data["equipment_summary"]  # Include equipment usage in main response
            }
            
        except Exception as e:
            self.session.rollback()
            return {"success": False, "message": f"Failed to generate discharge report: {str(e)}"}
        finally:
            self.session.close()
    
    def _get_patient_summary(self, patient, bed, admission_date, discharge_date) -> Dict[str, Any]:
        """Get patient demographic and admission summary."""
        return {
            "patient_id": str(patient.id),
            "patient_number": patient.patient_number,
            "name": f"{patient.first_name} {patient.last_name}",
            "date_of_birth": patient.date_of_birth.isoformat() if patient.date_of_birth else None,
            "gender": patient.gender,
            "blood_type": patient.blood_type,
            "allergies": patient.allergies,
            "emergency_contact": {
                "name": patient.emergency_contact_name,
                "phone": patient.emergency_contact_phone
            },
            "bed_info": {
                "bed_number": bed.bed_number,
                "room": bed.room.room_number if bed.room else None,
                "bed_type": bed.bed_type,
                "department": bed.room.department.name if bed.room and bed.room.department else None
            },
            "admission_date": admission_date.isoformat(),
            "discharge_date": discharge_date.isoformat(),
            "length_of_stay_days": (discharge_date - admission_date).days
        }
    
    def _get_treatment_summary(self, patient_id, admission_date, discharge_date) -> List[Dict[str, Any]]:
        """Get all treatments during the stay."""
        treatments = self.session.query(TreatmentRecord).filter(
            TreatmentRecord.patient_id == patient_id,
            TreatmentRecord.start_date >= admission_date,
            TreatmentRecord.start_date <= discharge_date
        ).all()
        
        return [{
            "treatment_type": t.treatment_type,
            "treatment_name": t.treatment_name,
            "description": t.description,
            "doctor": f"{t.doctor.first_name} {t.doctor.last_name}" if t.doctor else "Unknown",
            "start_date": t.start_date.isoformat(),
            "end_date": t.end_date.isoformat() if t.end_date else None,
            "status": t.status,
            "effectiveness": t.effectiveness,
            "notes": t.notes
        } for t in treatments]
    
    def _get_equipment_summary(self, patient_id, admission_date, discharge_date) -> List[Dict[str, Any]]:
        """Get all equipment used during the stay."""
        equipment_usage = self.session.query(EquipmentUsage).filter(
            EquipmentUsage.patient_id == patient_id,
            EquipmentUsage.start_time >= admission_date,
            EquipmentUsage.start_time <= discharge_date
        ).all()
        
        return [{
            "equipment_name": eu.equipment.name if eu.equipment else "Unknown",
            "equipment_type": eu.equipment.category.name if eu.equipment and eu.equipment.category else "Unknown",
            "purpose": eu.purpose,
            "start_time": eu.start_time.isoformat(),
            "end_time": eu.end_time.isoformat() if eu.end_time else None,
            "duration_minutes": eu.duration_minutes,
            "operated_by": f"{eu.staff.user.first_name} {eu.staff.user.last_name}" if eu.staff and eu.staff.user else "Unknown",
            "status": eu.status,
            "readings": eu.readings,
            "notes": eu.notes
        } for eu in equipment_usage]
    
    def _get_staff_summary(self, patient_id, admission_date, discharge_date) -> List[Dict[str, Any]]:
        """Get all staff assignments during the stay."""
        staff_assignments = self.session.query(StaffAssignment).filter(
            StaffAssignment.patient_id == patient_id,
            StaffAssignment.start_date <= discharge_date,
            (StaffAssignment.end_date >= admission_date) | (StaffAssignment.end_date.is_(None))
        ).all()
        
        return [{
            "staff_name": f"{sa.staff.user.first_name} {sa.staff.user.last_name}" if sa.staff and sa.staff.user else "Unknown",
            "position": sa.staff.position if sa.staff else "Unknown",
            "department": sa.staff.department.name if sa.staff and sa.staff.department else "Unknown",
            "assignment_type": sa.assignment_type,
            "start_date": sa.start_date.isoformat(),
            "end_date": sa.end_date.isoformat() if sa.end_date else discharge_date.isoformat(),
            "shift": sa.shift,
            "responsibilities": sa.responsibilities,
            "notes": sa.notes
        } for sa in staff_assignments]
    
    def _get_medications_summary(self, patient_id, admission_date, discharge_date) -> List[Dict[str, Any]]:
        """Get medication treatments."""
        medications = self.session.query(TreatmentRecord).filter(
            TreatmentRecord.patient_id == patient_id,
            TreatmentRecord.treatment_type == "medication",
            TreatmentRecord.start_date >= admission_date,
            TreatmentRecord.start_date <= discharge_date
        ).all()
        
        return [{
            "medication_name": m.treatment_name,
            "dosage": m.dosage,
            "frequency": m.frequency,
            "duration": m.duration,
            "prescribed_by": f"{m.doctor.first_name} {m.doctor.last_name}" if m.doctor else "Unknown",
            "start_date": m.start_date.isoformat(),
            "end_date": m.end_date.isoformat() if m.end_date else None,
            "status": m.status,
            "side_effects": m.side_effects,
            "effectiveness": m.effectiveness
        } for m in medications]
    
    def _get_supply_usage_summary(self, patient_id, admission_date, discharge_date) -> Dict[str, Any]:
        """Get supply and medication usage from inventory system."""
        try:
            from database import PatientSupplyUsage
            
            # Query patient supply usage records
            usage_records = self.session.query(PatientSupplyUsage).filter(
                PatientSupplyUsage.patient_id == patient_id,
                PatientSupplyUsage.prescribed_date >= admission_date,
                PatientSupplyUsage.prescribed_date <= discharge_date
            ).all()
            
            if not usage_records:
                return {
                    "medications": [],
                    "medical_supplies": [],
                    "total_cost": 0,
                    "summary": {
                        "total_items": 0,
                        "medications_count": 0,
                        "supplies_count": 0,
                        "total_cost": 0
                    }
                }
            
            medications = []
            medical_supplies = []
            total_cost = 0
            
            for usage in usage_records:
                # Debug logging
                print(f"🔍 Processing usage record: {usage.id}")
                print(f"  Supply object: {usage.supply}")
                print(f"  Supply name: {getattr(usage.supply, 'name', 'No name attribute') if usage.supply else 'No supply object'}")
                print(f"  Supply category: {getattr(usage.supply, 'category', 'No category attribute') if usage.supply else 'No supply object'}")
                
                # Build usage data
                usage_data = {
                    "item_name": usage.supply.name if usage.supply else "Unknown",
                    "category": usage.supply.category.name if usage.supply and usage.supply.category else "Unknown",
                    "quantity_used": usage.quantity_used,
                    "unit_of_measure": usage.supply.unit_of_measure if usage.supply else "",
                    "dosage": usage.dosage,
                    "frequency": usage.frequency,
                    "administration_route": usage.administration_route,
                    "indication": usage.indication,
                    "prescribed_by": f"{usage.prescribed_by.first_name} {usage.prescribed_by.last_name}" if usage.prescribed_by else "Unknown",
                    "administered_by": f"{usage.administered_by.first_name} {usage.administered_by.last_name}" if usage.administered_by else None,
                    "prescribed_date": usage.prescribed_date.isoformat() if usage.prescribed_date else None,
                    "administration_date": usage.administration_date.isoformat() if usage.administration_date else None,
                    "start_date": usage.start_date.isoformat() if usage.start_date else None,
                    "end_date": usage.end_date.isoformat() if usage.end_date else None,
                    "status": usage.status,
                    "effectiveness": usage.effectiveness,
                    "side_effects": usage.side_effects,
                    "unit_cost": float(usage.unit_cost or 0),
                    "total_cost": float(usage.total_cost or 0),
                    "notes": usage.notes
                }
                
                # Calculate total cost
                total_cost += float(usage.total_cost or 0)
                
                # Categorize as medication or supply
                if usage.supply and usage.supply.category:
                    category_name = usage.supply.category.name.lower()
                    print(f"  Category: {category_name}")
                    
                    if any(med_keyword in category_name for med_keyword in ['medication', 'drug', 'pharmaceutical', 'medicine']):
                        print(f"  → Categorized as MEDICATION")
                        medications.append(usage_data)
                    else:
                        print(f"  → Categorized as MEDICAL SUPPLY")
                        medical_supplies.append(usage_data)
                else:
                    print(f"  → Categorized as MEDICAL SUPPLY (no category)")
                    medical_supplies.append(usage_data)
                
                print(f"  Medications count: {len(medications)}")
                print(f"  Medical supplies count: {len(medical_supplies)}")
            
            result = {
                "medications": medications,
                "medical_supplies": medical_supplies,
                "total_cost": round(total_cost, 2),
                "summary": {
                    "total_items": len(usage_records),
                    "medications_count": len(medications),
                    "supplies_count": len(medical_supplies),
                    "total_cost": round(total_cost, 2)
                }
            }
            
            print(f"🔍 Final result:")
            print(f"  Medications: {len(result['medications'])}")
            print(f"  Medical supplies: {len(result['medical_supplies'])}")
            print(f"  Total cost: ${result['total_cost']}")
            print(f"  Summary: {result['summary']}")
            
            return result
            
        except Exception as e:
            # Fallback to empty data if PatientSupplyUsage is not available
            return {
                "medications": [],
                "medical_supplies": [],
                "total_cost": 0,
                "summary": {
                    "total_items": 0,
                    "medications_count": 0,
                    "supplies_count": 0,
                    "total_cost": 0
                }
            }
    
    def _get_procedures_summary(self, patient_id, admission_date, discharge_date) -> List[Dict[str, Any]]:
        """Get procedure treatments."""
        procedures = self.session.query(TreatmentRecord).filter(
            TreatmentRecord.patient_id == patient_id,
            TreatmentRecord.treatment_type.in_(["procedure", "surgery", "therapy"]),
            TreatmentRecord.start_date >= admission_date,
            TreatmentRecord.start_date <= discharge_date
        ).all()
        
        return [{
            "procedure_name": p.treatment_name,
            "type": p.treatment_type,
            "description": p.description,
            "performed_by": f"{p.doctor.first_name} {p.doctor.last_name}" if p.doctor else "Unknown",
            "date": p.start_date.isoformat(),
            "status": p.status,
            "effectiveness": p.effectiveness,
            "notes": p.notes
        } for p in procedures]
    
    def _get_appointments_summary(self, patient_id, admission_date, discharge_date) -> List[Dict[str, Any]]:
        """Get appointments during the stay."""
        # Note: Appointment model not available, returning empty list
        return []
        
        # Commented out until Appointment model is available
        # appointments = self.session.query(Appointment).filter(
        #     Appointment.patient_id == patient_id,
        #     Appointment.appointment_date >= admission_date,
        #     Appointment.appointment_date <= discharge_date
        # ).all()
        # 
        # return [{
        #     "appointment_date": a.appointment_date.isoformat(),
        #     "doctor": f"{a.doctor.first_name} {a.doctor.last_name}" if a.doctor else "Unknown",
        #     "department": a.department.name if a.department else "Unknown",
        #     "duration_minutes": a.duration_minutes,
        #     "status": a.status,
        #     "reason": a.reason,
        #     "notes": a.notes
        # } for a in appointments]
    
    def _format_discharge_report(self, data, report_record) -> str:
        """Format the discharge report as a comprehensive document."""
        patient = data["patient_summary"]
        
        report = f"""
# PATIENT DISCHARGE REPORT
**Report Number:** {report_record.report_number}
**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

## PATIENT INFORMATION
**Name:** {patient['name']}
**Patient ID:** {patient['patient_number']}
**Date of Birth:** {patient['date_of_birth']}
**Gender:** {patient['gender']}
**Blood Type:** {patient['blood_type']}
**Allergies:** {patient['allergies'] or 'None reported'}

**Emergency Contact:**
- **Name:** {patient['emergency_contact']['name'] or 'Not provided'}
- **Phone:** {patient['emergency_contact']['phone'] or 'Not provided'}

---

## ADMISSION & DISCHARGE DETAILS
**Admission Date:** {patient['admission_date']}
**Discharge Date:** {patient['discharge_date']}
**Length of Stay:** {patient['length_of_stay_days']} days
**Discharge Condition:** {report_record.discharge_condition}
**Discharge Destination:** {report_record.discharge_destination}

**Bed Information:**
- **Bed Number:** {patient['bed_info']['bed_number']}
- **Room:** {patient['bed_info']['room']}
- **Department:** {patient['bed_info']['department']}
- **Bed Type:** {patient['bed_info']['bed_type']}

---

## TREATMENT SUMMARY
"""
        
        # Add treatments
        if data["treatment_summary"]:
            for treatment in data["treatment_summary"]:
                report += f"""
### {treatment['treatment_name']} ({treatment['treatment_type']})
- **Doctor:** {treatment['doctor']}
- **Duration:** {treatment['start_date']} to {treatment['end_date'] or 'Ongoing'}
- **Status:** {treatment['status']}
- **Effectiveness:** {treatment['effectiveness'] or 'Not assessed'}
- **Description:** {treatment['description']}
- **Notes:** {treatment['notes'] or 'None'}
"""
        else:
            report += "\nNo treatments recorded during this stay.\n"
        
        # Add medications
        report += "\n---\n\n## MEDICATIONS\n"
        if data["medications"]:
            for med in data["medications"]:
                report += f"""
### {med['medication_name']}
- **Dosage:** {med['dosage']}
- **Frequency:** {med['frequency']}
- **Duration:** {med['duration']}
- **Prescribed by:** {med['prescribed_by']}
- **Status:** {med['status']}
- **Side Effects:** {med['side_effects'] or 'None reported'}
"""
        else:
            report += "\nNo medications prescribed during this stay.\n"
        
        # Add supply usage (medications and medical supplies from inventory)
        report += "\n---\n\n## SUPPLY USAGE & INVENTORY\n"
        supply_data = data.get("supply_usage", {})
        
        if supply_data.get("medications") or supply_data.get("medical_supplies"):
            # Medications from inventory
            if supply_data.get("medications"):
                report += "\n### 💊 Medications Used\n"
                for med in supply_data["medications"]:
                    report += f"""
**{med['item_name']}** ({med['category']})
- **Quantity:** {med['quantity_used']} {med['unit_of_measure']}
- **Dosage:** {med['dosage'] or 'Not specified'}
- **Frequency:** {med['frequency'] or 'Not specified'}
- **Route:** {med['administration_route'] or 'Not specified'}
- **Indication:** {med['indication'] or 'Not specified'}
- **Prescribed by:** {med['prescribed_by']}
- **Status:** {med['status']}
- **Cost:** ${med['total_cost']:.2f}
- **Effectiveness:** {med['effectiveness'] or 'Not assessed'}
"""
            
            # Medical supplies from inventory
            if supply_data.get("medical_supplies"):
                report += "\n### 🏥 Medical Supplies Used\n"
                for supply in supply_data["medical_supplies"]:
                    report += f"""
**{supply['item_name']}** ({supply['category']})
- **Quantity:** {supply['quantity_used']} {supply['unit_of_measure']}
- **Used for:** {supply['indication'] or 'Not specified'}
- **Used by:** {supply['administered_by'] or supply['prescribed_by']}
- **Cost:** ${supply['total_cost']:.2f}
"""
            
            # Cost summary
            summary = supply_data.get("summary", {})
            if summary.get("total_cost", 0) > 0:
                report += f"""
### 💰 Supply Cost Summary
- **Total Medications:** {summary.get('medications_count', 0)} items
- **Total Supplies:** {summary.get('supplies_count', 0)} items
- **Total Cost:** ${summary.get('total_cost', 0):.2f}
"""
        else:
            report += "\nNo supply usage recorded from inventory system.\n"
        
        # Add procedures
        report += "\n---\n\n## PROCEDURES\n"
        if data["procedures"]:
            for proc in data["procedures"]:
                report += f"""
### {proc['procedure_name']} ({proc['type']})
- **Performed by:** {proc['performed_by']}
- **Date:** {proc['date']}
- **Status:** {proc['status']}
- **Effectiveness:** {proc['effectiveness'] or 'Not assessed'}
- **Description:** {proc['description']}
"""
        else:
            report += "\nNo procedures performed during this stay.\n"
        
        # Add equipment usage
        report += "\n---\n\n## EQUIPMENT USED\n"
        if data["equipment_summary"]:
            for eq in data["equipment_summary"]:
                report += f"""
### {eq['equipment_name']} ({eq['equipment_type']})
- **Purpose:** {eq['purpose']}
- **Operated by:** {eq['operated_by']}
- **Duration:** {eq['duration_minutes']} minutes
- **Period:** {eq['start_time']} to {eq['end_time'] or 'End of stay'}
- **Notes:** {eq['notes'] or 'None'}
"""
        else:
            report += "\nNo equipment usage recorded during this stay.\n"
        
        # Add staff assignments
        report += "\n---\n\n## STAFF ASSIGNMENTS\n"
        if data["staff_summary"]:
            for staff in data["staff_summary"]:
                report += f"""
### {staff['staff_name']} - {staff['position']}
- **Department:** {staff['department']}
- **Role:** {staff['assignment_type']}
- **Period:** {staff['start_date']} to {staff['end_date']}
- **Shift:** {staff['shift'] or 'All day'}
- **Responsibilities:** {staff['responsibilities'] or 'Standard care'}
"""
        else:
            report += "\nNo specific staff assignments recorded.\n"
        
        # Add discharge instructions and follow-up
        report += f"""
---

## DISCHARGE INSTRUCTIONS
{report_record.discharge_instructions or 'Standard discharge instructions apply.'}

## FOLLOW-UP CARE REQUIRED
{report_record.follow_up_required or 'No specific follow-up required.'}

---

**Report Generated By:** Hospital Management System
**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        
        return report.strip()

# Convenience function for easy import
def generate_patient_discharge_report(**kwargs):
    """Generate a discharge report."""
    generator = PatientDischargeReportGenerator()
    return generator.generate_discharge_report(**kwargs)
