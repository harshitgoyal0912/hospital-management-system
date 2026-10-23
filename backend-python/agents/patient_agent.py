"""Patient Management Agent - Handles all patient-related operations"""

import uuid
from datetime import datetime, date
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from .base_agent import BaseAgent

try:
    from database import Patient, SessionLocal
    DATABASE_AVAILABLE = True
except ImportError:
    DATABASE_AVAILABLE = False


class PatientAgent(BaseAgent):
    """Agent specialized in patient management operations"""
    
    def __init__(self):
        super().__init__("Patient Management Agent", "patient_agent")
    
    def get_tools(self) -> List[str]:
        """Return list of patient management tools"""
        return [
            "create_patient",
            "list_patients",
            "get_patient_by_id",
            "search_patients",
            "update_patient",
            "delete_patient",
            "get_patient_medical_history_summary"
        ]
    
    def get_capabilities(self) -> List[str]:
        """Return list of patient management capabilities"""
        return [
            "Patient registration and admission",
            "Medical records management",
            "Patient information retrieval and search",
            "Patient demographics tracking",
            "Emergency contact management",
            "Medical history and allergy tracking"
        ]
    
    def create_patient(self, first_name: str, last_name: str, date_of_birth: str,
                      gender: str = None, phone: str = None, email: str = None,
                      address: str = None, emergency_contact_name: str = None,
                      emergency_contact_phone: str = None, blood_type: str = None,
                      allergies: str = None, medical_history: str = None,
                      patient_number: str = None) -> Dict[str, Any]:
        """Create a new patient record."""
        if not DATABASE_AVAILABLE:
            return {"success": False, "message": "Database not available"}
        
        try:
            # Use provided patient number or generate a unique one
            import random
            if patient_number:
                # Check if the provided patient number already exists
                db = self.get_db_session()
                existing_patient = db.query(Patient).filter(Patient.patient_number == patient_number).first()
                if existing_patient:
                    db.close()
                    return {
                        "success": False,
                        "message": f"Patient number {patient_number} already exists. Please choose a different number."
                    }
                db.close()
            else:
                # Generate unique patient number
                patient_number = f"P{random.randint(100000, 999999)}"
                # Check for uniqueness
                db = self.get_db_session()
                while db.query(Patient).filter(Patient.patient_number == patient_number).first():
                    patient_number = f"P{random.randint(100000, 999999)}"
                db.close()
            
            # Parse date of birth
            dob = datetime.strptime(date_of_birth, "%Y-%m-%d").date()
            
            db = self.get_db_session()
            patient = Patient(
                patient_number=patient_number,
                first_name=first_name,
                last_name=last_name,
                date_of_birth=dob,
                gender=gender,
                phone=phone,
                email=email,
                address=address,
                emergency_contact_name=emergency_contact_name,
                emergency_contact_phone=emergency_contact_phone,
                blood_type=blood_type,
                allergies=allergies,
                medical_history=medical_history
            )
            db.add(patient)
            db.commit()
            db.refresh(patient)
            result = self.serialize_model(patient)
            db.close()
            
            # Ensure result is not None
            if result is None:
                result = {
                    "id": str(patient.id),
                    "patient_number": patient.patient_number,
                    "first_name": patient.first_name,
                    "last_name": patient.last_name,
                    "date_of_birth": patient.date_of_birth.isoformat() if patient.date_of_birth else None,
                    "gender": patient.gender,
                    "phone": patient.phone,
                    "email": patient.email,
                    "address": patient.address,
                    "blood_type": patient.blood_type
                }
            
            # Log the interaction
            self.log_interaction(
                query=f"Create patient: {first_name} {last_name}",
                response=f"Patient created successfully with number: {patient_number}",
                tool_used="create_patient"
            )
            
            return {"success": True, "message": "Patient created successfully", "data": result}
        except Exception as e:
            return {"success": False, "message": f"Failed to create patient: {str(e)}"}

    def list_patients(self, status: str = "active") -> Dict[str, Any]:
        """List patients with optional status filtering.
        
        Args:
            status: Filter by patient status - "active" (default), "discharged", "all"
        """
        if not DATABASE_AVAILABLE:
            return {"error": "Database not available"}
        
        try:
            db = self.get_db_session()
            query = db.query(Patient)
            
            # Apply status filter - default to active patients only
            if status and status != "all":
                query = query.filter(Patient.status == status)
            
            patients = query.order_by(Patient.created_at.desc()).all()
            
            # Return only essential information for list views
            result = []
            for patient in patients:
                brief_info = {
                    "id": str(patient.id),
                    "first_name": patient.first_name,
                    "last_name": patient.last_name,
                    "patient_number": patient.patient_number,
                    "phone": patient.phone,  # Keep for contact purposes
                    "date_of_birth": patient.date_of_birth.isoformat() if patient.date_of_birth else None,
                    "status": patient.status,
                    "last_updated": patient.updated_at.isoformat() if patient.updated_at else None
                }
                result.append(brief_info)
            
            db.close()
            
            # Log the interaction
            self.log_interaction(
                query=f"List patients with status filter: {status}",
                response=f"Found {len(result)} patients",
                tool_used="list_patients"
            )
            
            return {"data": result, "status_filter": status, "total_count": len(result)}
        except Exception as e:
            return {"error": f"Failed to list patients: {str(e)}"}

    def get_patient_by_id(self, patient_id: str) -> Dict[str, Any]:
        """Get a patient by ID."""
        if not DATABASE_AVAILABLE:
            return {"error": "Database not available"}
        
        try:
            db = self.get_db_session()
            patient = db.query(Patient).filter(Patient.id == uuid.UUID(patient_id)).first()
            result = self.serialize_model(patient) if patient else None
            db.close()
            
            if result:
                # Log the interaction
                self.log_interaction(
                    query=f"Get patient by ID: {patient_id}",
                    response=f"Patient found: {result.get('first_name', '')} {result.get('last_name', '')}",
                    tool_used="get_patient_by_id"
                )
                return {"data": result}
            else:
                return {"error": "Patient not found"}
        except Exception as e:
            return {"error": f"Failed to get patient: {str(e)}"}

    def search_patients(self, patient_number: str = None, first_name: str = None, 
                       last_name: str = None, phone: str = None, email: str = None) -> Dict[str, Any]:
        """Search for patients by various criteria."""
        if not DATABASE_AVAILABLE:
            return {"error": "Database not available"}
        
        try:
            db = self.get_db_session()
            query = db.query(Patient)
            
            # Build search filters
            filters = []
            search_criteria = []
            
            if patient_number:
                filters.append(Patient.patient_number.ilike(f"%{patient_number}%"))
                search_criteria.append(f"patient_number: {patient_number}")
            if first_name:
                filters.append(Patient.first_name.ilike(f"%{first_name}%"))
                search_criteria.append(f"first_name: {first_name}")
            if last_name:
                filters.append(Patient.last_name.ilike(f"%{last_name}%"))
                search_criteria.append(f"last_name: {last_name}")
            if phone:
                filters.append(Patient.phone.ilike(f"%{phone}%"))
                search_criteria.append(f"phone: {phone}")
            if email:
                filters.append(Patient.email.ilike(f"%{email}%"))
                search_criteria.append(f"email: {email}")
            
            # Apply filters
            if filters:
                query = query.filter(and_(*filters))
            
            patients = query.all()
            result = [self.serialize_model(patient) for patient in patients]
            db.close()
            
            # Log the interaction
            self.log_interaction(
                query=f"Search patients: {', '.join(search_criteria)}",
                response=f"Found {len(result)} matching patients",
                tool_used="search_patients"
            )
            
            return {"data": result}
        except Exception as e:
            return {"error": f"Failed to search patients: {str(e)}"}

    def update_patient(self, patient_id: str, first_name: str = None, last_name: str = None,
                      gender: str = None, phone: str = None, email: str = None,
                      address: str = None, emergency_contact_name: str = None,
                      emergency_contact_phone: str = None, blood_type: str = None,
                      allergies: str = None, medical_history: str = None) -> Dict[str, Any]:
        """Update patient information."""
        if not DATABASE_AVAILABLE:
            return {"success": False, "message": "Database not available"}
        
        try:
            db = self.get_db_session()
            patient = db.query(Patient).filter(Patient.id == uuid.UUID(patient_id)).first()
            
            if not patient:
                db.close()
                return {"success": False, "message": "Patient not found"}
            
            # Update provided fields
            update_fields = []
            if first_name is not None:
                patient.first_name = first_name
                update_fields.append("first_name")
            if last_name is not None:
                patient.last_name = last_name
                update_fields.append("last_name")
            if gender is not None:
                patient.gender = gender
                update_fields.append("gender")
            if phone is not None:
                patient.phone = phone
                update_fields.append("phone")
            if email is not None:
                patient.email = email
                update_fields.append("email")
            if address is not None:
                patient.address = address
                update_fields.append("address")
            if emergency_contact_name is not None:
                patient.emergency_contact_name = emergency_contact_name
                update_fields.append("emergency_contact_name")
            if emergency_contact_phone is not None:
                patient.emergency_contact_phone = emergency_contact_phone
                update_fields.append("emergency_contact_phone")
            if blood_type is not None:
                patient.blood_type = blood_type
                update_fields.append("blood_type")
            if allergies is not None:
                patient.allergies = allergies
                update_fields.append("allergies")
            if medical_history is not None:
                patient.medical_history = medical_history
                update_fields.append("medical_history")
            
            db.commit()
            db.refresh(patient)
            result = self.serialize_model(patient)
            db.close()
            
            # Log the interaction
            self.log_interaction(
                query=f"Update patient {patient_id}: {', '.join(update_fields)}",
                response=f"Patient updated successfully",
                tool_used="update_patient"
            )
            
            return {"success": True, "message": "Patient updated successfully", "data": result}
        except Exception as e:
            return {"success": False, "message": f"Failed to update patient: {str(e)}"}

    def delete_patient(self, patient_id: str) -> Dict[str, Any]:
        """Delete a patient record."""
        if not DATABASE_AVAILABLE:
            return {"success": False, "message": "Database not available"}
        
        try:
            db = self.get_db_session()
            patient = db.query(Patient).filter(Patient.id == uuid.UUID(patient_id)).first()
            
            if not patient:
                db.close()
                return {"success": False, "message": "Patient not found"}
            
            patient_name = f"{patient.first_name} {patient.last_name}"  # Store for logging
            db.delete(patient)
            db.commit()
            db.close()
            
            # Log the interaction
            self.log_interaction(
                query=f"Delete patient: {patient_id}",
                response=f"Patient {patient_name} deleted successfully",
                tool_used="delete_patient"
            )
            
            return {"success": True, "message": "Patient deleted successfully"}
        except Exception as e:
            return {"success": False, "message": f"Failed to delete patient: {str(e)}"}
    
    def get_patient_medical_history_summary(self, patient_id: str = None, patient_number: str = None, 
                                          patient_name: str = None) -> Dict[str, Any]:
        """Get comprehensive medical history summary for a patient from documents and basic info."""
        if not DATABASE_AVAILABLE:
            return {"success": False, "message": "Database not available"}
        
        try:
            db = self.get_db_session()
            patient = None
            
            # Find patient by different identifiers
            if patient_id:
                patient = db.query(Patient).filter(Patient.id == uuid.UUID(patient_id)).first()
            elif patient_number:
                patient = db.query(Patient).filter(Patient.patient_number == patient_number).first()
            elif patient_name:
                # Search by name (case insensitive)
                name_parts = patient_name.strip().split()
                if len(name_parts) >= 2:
                    first_name, last_name = name_parts[0], " ".join(name_parts[1:])
                    patient = db.query(Patient).filter(
                        Patient.first_name.ilike(f"%{first_name}%"),
                        Patient.last_name.ilike(f"%{last_name}%")
                    ).first()
                else:
                    # Single name search
                    patient = db.query(Patient).filter(
                        or_(
                            Patient.first_name.ilike(f"%{patient_name}%"),
                            Patient.last_name.ilike(f"%{patient_name}%")
                        )
                    ).first()
            
            if not patient:
                return {"success": False, "message": "Patient not found"}
            
            # Get basic patient info
            basic_info = {
                "patient_id": str(patient.id),
                "patient_number": patient.patient_number,
                "name": f"{patient.first_name} {patient.last_name}",
                "date_of_birth": patient.date_of_birth.isoformat() if patient.date_of_birth else None,
                "gender": patient.gender,
                "phone": patient.phone,
                "email": patient.email,
                "address": patient.address,
                "blood_type": patient.blood_type,
                "allergies": patient.allergies,
                "basic_medical_history": patient.medical_history
            }
            
            # Try to get detailed medical history from documents
            from agents.medical_document_agent import MedicalDocumentAgent
            medical_agent = MedicalDocumentAgent()
            
            try:
                detailed_history = medical_agent.get_patient_medical_history(str(patient.id))
                if detailed_history.get("success"):
                    medical_data = detailed_history.get("medical_history", {})
                    
                    # Create comprehensive summary
                    total_documents = detailed_history.get("total_documents", 0)
                    medications_count = len(medical_data.get("medications", []))
                    conditions_count = len(medical_data.get("conditions", []))
                    instructions_count = len(medical_data.get("instructions", []))
                    allergies_count = len(medical_data.get("allergies", []))
                    
                    if total_documents > 0:
                        summary = f"""
📋 **Comprehensive Medical History for {basic_info['name']} (Patient #{patient.patient_number})**

👤 **Basic Information:**
- Date of Birth: {basic_info['date_of_birth']}
- Gender: {basic_info['gender'] or 'Not specified'}
- Blood Type: {basic_info['blood_type'] or 'Not recorded'}
- Phone: {basic_info['phone'] or 'Not recorded'}
- Email: {basic_info['email'] or 'Not recorded'}

📄 **Medical Documents:** {total_documents} document(s) processed

💊 **Current Medications ({medications_count}):**"""
                        
                        for med in medical_data.get("medications", [])[:5]:  # Show up to 5
                            name = med.get('name', 'Unknown')
                            value = med.get('value', '')
                            confidence = med.get('confidence', 0)
                            summary += f"\n- {name}" + (f" ({value})" if value else "") + f" [Confidence: {confidence:.0%}]"
                        
                        summary += f"\n\n🏥 **Medical Conditions ({conditions_count}):**"
                        for condition in medical_data.get("conditions", [])[:3]:  # Show up to 3
                            name = condition.get('name', 'Unknown')
                            confidence = condition.get('confidence', 0)
                            summary += f"\n- {name} [Confidence: {confidence:.0%}]"
                        
                        if instructions_count > 0:
                            summary += f"\n\n📋 **Treatment Instructions ({instructions_count}):**"
                            for instruction in medical_data.get("instructions", [])[:3]:  # Show up to 3
                                name = instruction.get('name', 'Unknown')
                                summary += f"\n- {name}"
                        
                        if allergies_count > 0:
                            summary += f"\n\n⚠️ **Known Allergies ({allergies_count}):**"
                            for allergy in medical_data.get("allergies", []):
                                name = allergy.get('name', 'Unknown')
                                summary += f"\n- {name}"
                        elif basic_info['allergies']:
                            summary += f"\n\n⚠️ **Known Allergies:**\n- {basic_info['allergies']}"
                        
                        if basic_info['basic_medical_history']:
                            summary += f"\n\n📝 **Additional Medical History:**\n{basic_info['basic_medical_history']}"
                        
                        summary += f"\n\n*This information is extracted from uploaded medical documents with AI assistance.*"
                        
                        return {
                            "success": True,
                            "patient_info": basic_info,
                            "detailed_history": medical_data,
                            "summary": summary,
                            "total_documents": total_documents
                        }
                    
            except Exception as e:
                print(f"Failed to get detailed medical history: {e}")
            
            # Fallback to basic patient information only
            if basic_info['allergies'] or basic_info['basic_medical_history'] or basic_info['blood_type']:
                summary = f"""
📋 **Basic Medical Information for {basic_info['name']} (Patient #{patient.patient_number})**

👤 **Patient Details:**
- Date of Birth: {basic_info['date_of_birth']}
- Gender: {basic_info['gender'] or 'Not specified'}
- Blood Type: {basic_info['blood_type'] or 'Not recorded'}
- Phone: {basic_info['phone'] or 'Not recorded'}
- Email: {basic_info['email'] or 'Not recorded'}

⚠️ **Known Allergies:** {basic_info['allergies'] or 'None recorded'}

📝 **Medical History:** {basic_info['basic_medical_history'] or 'No detailed history recorded'}

📄 **Medical Documents:** No processed documents found. Upload medical documents for detailed history.
"""
            else:
                summary = f"""
📋 **Limited Medical Information for {basic_info['name']} (Patient #{patient.patient_number})**

👤 **Basic Patient Details:**
- Date of Birth: {basic_info['date_of_birth']}
- Gender: {basic_info['gender'] or 'Not specified'}

⚠️ **Current Medical Records:** This patient has minimal information in the system. No detailed medical history, allergies, or blood type are currently recorded.

📄 **Recommendation:** Please upload medical documents or update patient records to build a comprehensive medical history.
"""
            
            self.log_interaction(
                query=f"Get medical history summary for {basic_info['name']}",
                response=f"Retrieved medical summary for patient {patient.patient_number}",
                tool_used="get_patient_medical_history_summary"
            )
            
            return {
                "success": True,
                "patient_info": basic_info,
                "summary": summary,
                "has_detailed_history": False
            }
            
        except Exception as e:
            return {"success": False, "message": f"Failed to get medical history: {str(e)}"}
        finally:
            if 'db' in locals():
                db.close()
