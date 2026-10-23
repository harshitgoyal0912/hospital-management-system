"""Patient Supply Usage Agent - manages medication and supply usage tr            # Verify patient exists
            patient = db.query(Patient).filter(Patient.id == uuid.UUID(patient_id)).first()
            if not patient:
                db.close()
                return {"success": False, "message": "Patient not found"}
            
            # Verify supply exists and get needed data while session is active
            supply = db.query(Supply).filter(Supply.id == uuid.UUID(supply_id)).first()
            if not supply:
                db.close()
                return {"success": False, "message": "Supply not found"}
            
            # Get supply data while session is active
            unit_cost = supply.unit_cost or 0
            current_stock = supply.current_stock
            
            # Calculate costs
            total_cost = float(unit_cost) * quantity_used if unit_cost else 0ents."""
import uuid
from datetime import datetime, date
from typing import Any, Dict, List, Optional
from .base_agent import BaseAgent

try:
    from database import SessionLocal, PatientSupplyUsage, Patient, Supply, User, Bed
    from sqlalchemy import and_, or_, desc
    DATABASE_AVAILABLE = True
except ImportError:
    DATABASE_AVAILABLE = False

class PatientSupplyUsageAgent(BaseAgent):
    def __init__(self):
        super().__init__("Patient Supply Usage Agent", "supply_usage_agent")
        self.available_tools = [
            "record_patient_supply_usage",
            "record_patient_supply_usage_by_code",  # Convenience method for user-friendly codes
            "get_patient_supply_usage",
            "update_supply_usage_status",
            "get_supply_usage_for_discharge_report",
            "list_patient_medications",
            "search_supply_usage_by_patient",
            "calculate_patient_medication_costs"
        ]
        
        self.tool_descriptions = {
            "record_patient_supply_usage": "Record medication or supply usage for a patient",
            "record_patient_supply_usage_by_code": "Record patient supply usage using user-friendly codes (patient number, item code, employee ID)",
            "get_patient_supply_usage": "Get specific supply usage record by ID",
            "update_supply_usage_status": "Update status of supply usage (administered, completed, discontinued)",
            "get_supply_usage_for_discharge_report": "Get all supply usage for a patient's discharge report",
            "list_patient_medications": "List all medications/supplies used by a patient",
            "search_supply_usage_by_patient": "Search supply usage records for a specific patient",
            "calculate_patient_medication_costs": "Calculate total medication costs for a patient stay"
        }

    def get_capabilities(self) -> List[str]:
        """Get list of agent capabilities."""
        return [
            "Record patient medication and supply usage",
            "Track medication administration and effectiveness",
            "Generate medication summaries for discharge reports",
            "Calculate medication costs and billing",
            "Monitor supply inventory depletion",
            "Search and filter medication records"
        ]

    def get_tools(self) -> List[str]:
        """Get list of available tools."""
        return self.available_tools

    def get_db_session(self):
        """Get database session"""
        if not DATABASE_AVAILABLE:
            raise Exception("Database not available")
        return SessionLocal()

    def record_patient_supply_usage(self, patient_id: str = None, patient_number: str = None,
                                  supply_id: str = None, supply_item_code: str = None, 
                                  quantity_used: int = 1, dosage: str = None, frequency: str = None, 
                                  prescribed_by_id: str = None, administered_by_id: str = None, 
                                  staff_id: str = None, employee_id: str = None,
                                  bed_id: str = None, administration_route: str = "oral", 
                                  indication: str = None, start_date: str = None, 
                                  end_date: str = None, notes: str = None) -> Dict[str, Any]:
        """
        Record medication or supply usage for a patient.
        
        Enhanced to automatically handle Employee IDs (e.g., 'EMP1005') for staff identification.
        
        Args:
            patient_id: Patient UUID or patient_number for patient identification
            patient_number: Patient number (e.g., 'P1009') 
            supply_id: Supply UUID or supply_item_code for supply identification
            supply_item_code: Supply item code (e.g., 'SUP00006')
            staff_id: Staff identifier - supports both Employee IDs (e.g., 'EMP1005') and User UUIDs
            prescribed_by_id: Prescribing staff - supports Employee IDs and User UUIDs
            administered_by_id: Administering staff - supports Employee IDs and User UUIDs
            employee_id: Alternative parameter for Employee ID
            
        Returns:
            Dict with success status and usage record details
        """
        if not DATABASE_AVAILABLE:
            return {"success": False, "message": "Database not available"}

        try:
            db = self.get_db_session()
            
            # Debug: Print incoming parameters
            print(f"🔍 SUPPLY USAGE DEBUG: Recording supply usage")
            print(f"  - patient_id: {patient_id} (type: {type(patient_id)})")
            print(f"  - patient_number: {patient_number}")
            print(f"  - supply_id: {supply_id}")
            print(f"  - staff_id: {staff_id}")
            
            # Find patient by ID or patient number
            patient = None
            if patient_id:
                try:
                    patient = db.query(Patient).filter(Patient.id == uuid.UUID(patient_id)).first()
                    print(f"🔍 SUPPLY USAGE DEBUG: Found patient by ID: {patient.id if patient else 'None'}")
                except ValueError:
                    print(f"❌ SUPPLY USAGE DEBUG: Invalid patient ID format: {patient_id}")
                    db.close()
                    return {"success": False, "message": "Invalid patient ID format"}
            elif patient_number:
                patient = db.query(Patient).filter(Patient.patient_number == patient_number).first()
                print(f"🔍 SUPPLY USAGE DEBUG: Found patient by number: {patient.id if patient else 'None'}")
            else:
                db.close()
                return {"success": False, "message": "Either patient_id or patient_number must be provided"}
            
            if not patient:
                db.close()
                return {"success": False, "message": f"Patient not found with {'ID: ' + patient_id if patient_id else 'number: ' + patient_number}"}
            
            print(f"✅ SUPPLY USAGE DEBUG: Using patient UUID: {patient.id} for {patient.first_name} {patient.last_name}")
            
            # Find supply by ID or item code
            supply = None
            if supply_id:
                # Look up by supply ID (UUID)
                try:
                    supply = db.query(Supply).filter(Supply.id == uuid.UUID(supply_id)).first()
                except ValueError:
                    db.close()
                    return {"success": False, "message": "Invalid supply ID format"}
            elif supply_item_code:
                # Look up by item code
                supply = db.query(Supply).filter(Supply.item_code == supply_item_code).first()
            else:
                db.close()
                return {"success": False, "message": "Either supply_id or supply_item_code must be provided"}
            
            if not supply:
                db.close()
                return {"success": False, "message": f"Supply not found with {'ID: ' + supply_id if supply_id else 'item code: ' + supply_item_code}"}
            
            # Resolve staff/administered_by
            administered_by_uuid = None
            if administered_by_id:
                try:
                    administered_by_uuid = uuid.UUID(administered_by_id)
                except ValueError:
                    db.close()
                    return {"success": False, "message": "Invalid administered_by_id format"}
            elif staff_id:
                # Enhanced staff_id handling: support both Employee IDs and User UUIDs
                try:
                    # First, try to parse as UUID (User ID)
                    administered_by_uuid = uuid.UUID(staff_id)
                except ValueError:
                    # If UUID parsing fails, treat as Employee ID and look up staff
                    from database import Staff
                    staff = db.query(Staff).filter(Staff.employee_id == staff_id).first()
                    if staff:
                        administered_by_uuid = staff.user_id  # Staff references User table
                    else:
                        db.close()
                        return {"success": False, "message": f"Staff not found with employee ID: {staff_id}"}
            elif employee_id:
                # Look up staff by employee_id
                from database import Staff
                staff = db.query(Staff).filter(Staff.employee_id == employee_id).first()
                if staff:
                    administered_by_uuid = staff.user_id  # Staff references User table
                else:
                    db.close()
                    return {"success": False, "message": f"Staff not found with employee ID: {employee_id}"}
            
            # Resolve prescribed_by if provided (Enhanced to handle Employee IDs)
            prescribed_by_uuid = None
            if prescribed_by_id:
                try:
                    # First, try to parse as UUID (User ID)
                    prescribed_by_uuid = uuid.UUID(prescribed_by_id)
                except ValueError:
                    # If UUID parsing fails, treat as Employee ID and look up staff
                    from database import Staff
                    staff = db.query(Staff).filter(Staff.employee_id == prescribed_by_id).first()
                    if staff:
                        prescribed_by_uuid = staff.user_id  # Staff references User table
                    else:
                        db.close()
                        return {"success": False, "message": f"Prescribing staff not found with employee ID: {prescribed_by_id}"}
            
            # Calculate costs
            unit_cost = supply.unit_cost or 0
            total_cost = float(unit_cost) * quantity_used if unit_cost else 0
            
            # Parse dates
            start_date_obj = datetime.fromisoformat(start_date).date() if start_date else date.today()
            end_date_obj = datetime.fromisoformat(end_date).date() if end_date else None
            
            # Debug: Print what we're about to record
            print(f"📝 SUPPLY USAGE DEBUG: Creating usage record")
            print(f"  - patient.id: {patient.id} (type: {type(patient.id)})")
            print(f"  - supply.id: {supply.id}")
            print(f"  - quantity_used: {quantity_used}")
            
            # Create usage record
            usage = PatientSupplyUsage(
                patient_id=patient.id,  # Use the resolved patient ID
                supply_id=supply.id,  # Use the resolved supply ID
                quantity_used=quantity_used,
                unit_cost=unit_cost,
                total_cost=total_cost,
                prescribed_by_id=prescribed_by_uuid,
                administered_by_id=administered_by_uuid,
                bed_id=uuid.UUID(bed_id) if bed_id else None,
                dosage=dosage,
                frequency=frequency,
                administration_route=administration_route,
                indication=indication if indication else notes,  # Use notes as indication if provided
                prescribed_date=datetime.now(),
                start_date=start_date_obj,
                end_date=end_date_obj,
                status="prescribed"
            )
            
            db.add(usage)
            db.commit()
            db.refresh(usage)
            
            print(f"✅ SUPPLY USAGE DEBUG: Record created with ID: {usage.id}, patient_id: {usage.patient_id}")
            
            # Update supply inventory
            supply.current_stock -= quantity_used
            db.commit()
            
            # Force-load all attributes to avoid detached instance issues
            usage_dict = {
                'id': str(usage.id),
                'patient_id': str(usage.patient_id),
                'supply_id': str(usage.supply_id),
                'quantity_used': usage.quantity_used,
                'unit_cost': float(usage.unit_cost) if usage.unit_cost else 0,
                'total_cost': float(usage.total_cost) if usage.total_cost else 0,
                'dosage': usage.dosage,
                'frequency': usage.frequency,
                'administration_route': usage.administration_route,
                'indication': usage.indication,
                'status': usage.status,
                'prescribed_date': usage.prescribed_date.isoformat() if usage.prescribed_date else None,
                'start_date': usage.start_date.isoformat() if usage.start_date else None,
                'end_date': usage.end_date.isoformat() if usage.end_date else None
            }
            
            # Get additional data for logging before closing session
            supply_name = supply.name
            supply_unit = supply.unit_of_measure
            patient_name = f"{patient.first_name} {patient.last_name}"
            
            db.close()
            
            # Log the interaction
            self.log_interaction(
                query=f"Record {quantity_used} {supply_unit} of {supply_name} for patient {patient_name}",
                response=f"Supply usage recorded successfully",
                tool_used="record_patient_supply_usage"
            )
            
            return {"success": True, "message": "Supply usage recorded successfully", "data": usage_dict}
            
        except Exception as e:
            db.rollback()
            db.close()
            return {"success": False, "message": f"Failed to record supply usage: {str(e)}"}

    def record_patient_supply_usage_by_code(self, patient_number: str = None, patient_id: str = None, 
                                          supply_item_code: str = None, quantity_used: int = 1, 
                                          staff_id: str = None, employee_id: str = None,
                                          date_of_usage: str = None, notes: str = None) -> Dict[str, Any]:
        """Record patient supply usage using user-friendly codes (patient number, item code, employee ID)."""
        # Convert date_of_usage to start_date format
        start_date = date_of_usage if date_of_usage else None
        
        # Call the main method with the converted parameters
        return self.record_patient_supply_usage(
            patient_id=patient_id,
            patient_number=patient_number, 
            supply_item_code=supply_item_code,
            quantity_used=quantity_used, 
            staff_id=staff_id,
            employee_id=employee_id,
            start_date=start_date,
            notes=notes
        )

    def get_patient_supply_usage(self, usage_id: str) -> Dict[str, Any]:
        """Get specific supply usage record by ID."""
        if not DATABASE_AVAILABLE:
            return {"success": False, "message": "Database not available"}

        try:
            db = self.get_db_session()
            
            usage = db.query(PatientSupplyUsage).filter(
                PatientSupplyUsage.id == uuid.UUID(usage_id)
            ).first()
            
            if not usage:
                db.close()
                return {"success": False, "message": "Supply usage record not found"}
            
            result = self.serialize_model(usage)
            
            # Add related information
            if usage.supply:
                result["supply_name"] = usage.supply.name
                result["supply_category"] = usage.supply.category.name if usage.supply.category else None
            
            if usage.prescribed_by:
                result["prescribed_by_name"] = f"{usage.prescribed_by.first_name} {usage.prescribed_by.last_name}"
            
            if usage.administered_by:
                result["administered_by_name"] = f"{usage.administered_by.first_name} {usage.administered_by.last_name}"
            
            db.close()
            
            return {"success": True, "data": result}
            
        except Exception as e:
            db.close()
            return {"success": False, "message": f"Failed to get supply usage: {str(e)}"}

    def update_supply_usage_status(self, usage_id: str, status: str, 
                                 administration_date: str = None, 
                                 effectiveness: str = None,
                                 side_effects: str = None, 
                                 notes: str = None) -> Dict[str, Any]:
        """Update status of supply usage (administered, completed, discontinued)."""
        if not DATABASE_AVAILABLE:
            return {"success": False, "message": "Database not available"}

        valid_statuses = ["prescribed", "administered", "completed", "discontinued"]
        if status not in valid_statuses:
            return {"success": False, "message": f"Invalid status. Valid options: {', '.join(valid_statuses)}"}

        try:
            db = self.get_db_session()
            
            usage = db.query(PatientSupplyUsage).filter(
                PatientSupplyUsage.id == uuid.UUID(usage_id)
            ).first()
            
            if not usage:
                db.close()
                return {"success": False, "message": "Supply usage record not found"}
            
            # Update fields
            usage.status = status
            if administration_date:
                usage.administration_date = datetime.fromisoformat(administration_date)
            if effectiveness:
                usage.effectiveness = effectiveness
            if side_effects:
                usage.side_effects = side_effects
            if notes:
                usage.notes = notes
            
            db.commit()
            db.refresh(usage)
            
            result = self.serialize_model(usage)
            db.close()
            
            # Log the interaction
            self.log_interaction(
                query=f"Update supply usage {usage_id} status to {status}",
                response=f"Supply usage status updated successfully",
                tool_used="update_supply_usage_status"
            )
            
            return {"success": True, "message": "Supply usage status updated successfully", "data": result}
            
        except Exception as e:
            db.rollback()
            db.close()
            return {"success": False, "message": f"Failed to update supply usage status: {str(e)}"}

    def get_supply_usage_for_discharge_report(self, patient_id: str, 
                                            admission_date: str = None, 
                                            discharge_date: str = None) -> Dict[str, Any]:
        """Get all supply usage for a patient's discharge report."""
        if not DATABASE_AVAILABLE:
            return {"success": False, "message": "Database not available"}

        try:
            db = self.get_db_session()
            
            # Build query
            query = db.query(PatientSupplyUsage).filter(
                PatientSupplyUsage.patient_id == uuid.UUID(patient_id)
            )
            
            # Add date filters if provided
            if admission_date:
                admission_dt = datetime.fromisoformat(admission_date)
                query = query.filter(PatientSupplyUsage.prescribed_date >= admission_dt)
            
            if discharge_date:
                discharge_dt = datetime.fromisoformat(discharge_date)
                query = query.filter(PatientSupplyUsage.prescribed_date <= discharge_dt)
            
            # Order by prescribed date
            usage_records = query.order_by(PatientSupplyUsage.prescribed_date).all()
            
            if not usage_records:
                db.close()
                return {"success": True, "data": [], "message": "No supply usage found for this patient"}
            
            # Group by supply type for better reporting
            medications = []
            supplies = []
            total_cost = 0
            
            for usage in usage_records:
                usage_data = self.serialize_model(usage)
                
                # Add supply information
                if usage.supply:
                    usage_data["supply_name"] = usage.supply.name
                    usage_data["supply_category"] = usage.supply.category.name if usage.supply.category else None
                    usage_data["unit_of_measure"] = usage.supply.unit_of_measure
                
                # Add prescriber information
                if usage.prescribed_by:
                    usage_data["prescribed_by_name"] = f"{usage.prescribed_by.first_name} {usage.prescribed_by.last_name}"
                
                # Calculate costs
                total_cost += float(usage.total_cost or 0)
                
                # Categorize as medication or supply
                if usage.supply and usage.supply.category:
                    category_name = usage.supply.category.name.lower()
                    if any(med_keyword in category_name for med_keyword in ['medication', 'drug', 'pharmaceutical', 'medicine']):
                        medications.append(usage_data)
                    else:
                        supplies.append(usage_data)
                else:
                    supplies.append(usage_data)
            
            db.close()
            
            result = {
                "medications": medications,
                "medical_supplies": supplies,
                "total_items": len(usage_records),
                "total_cost": round(total_cost, 2),
                "summary": {
                    "medications_count": len(medications),
                    "supplies_count": len(supplies),
                    "total_cost": round(total_cost, 2)
                }
            }
            
            # Log the interaction
            self.log_interaction(
                query=f"Get supply usage for discharge report - patient {patient_id}",
                response=f"Retrieved {len(usage_records)} usage records for discharge report",
                tool_used="get_supply_usage_for_discharge_report"
            )
            
            return {"success": True, "data": result}
            
        except Exception as e:
            db.close()
            return {"success": False, "message": f"Failed to get supply usage for discharge report: {str(e)}"}

    def list_patient_medications(self, patient_id: str) -> Dict[str, Any]:
        """List all medications/supplies used by a patient."""
        if not DATABASE_AVAILABLE:
            return {"success": False, "message": "Database not available"}

        try:
            db = self.get_db_session()
            
            usage_records = db.query(PatientSupplyUsage).filter(
                PatientSupplyUsage.patient_id == uuid.UUID(patient_id)
            ).order_by(desc(PatientSupplyUsage.prescribed_date)).all()
            
            if not usage_records:
                db.close()
                return {"success": True, "data": [], "message": "No medications or supplies found for this patient"}
            
            results = []
            for usage in usage_records:
                usage_data = self.serialize_model(usage)
                
                # Add supply information
                if usage.supply:
                    usage_data["supply_name"] = usage.supply.name
                    usage_data["supply_category"] = usage.supply.category.name if usage.supply.category else None
                    usage_data["unit_of_measure"] = usage.supply.unit_of_measure
                
                # Add prescriber information
                if usage.prescribed_by:
                    usage_data["prescribed_by_name"] = f"{usage.prescribed_by.first_name} {usage.prescribed_by.last_name}"
                
                results.append(usage_data)
            
            db.close()
            
            # Log the interaction
            self.log_interaction(
                query=f"List medications for patient {patient_id}",
                response=f"Found {len(results)} medication/supply records",
                tool_used="list_patient_medications"
            )
            
            return {"success": True, "data": results}
            
        except Exception as e:
            db.close()
            return {"success": False, "message": f"Failed to list patient medications: {str(e)}"}

    def search_supply_usage_by_patient(self, patient_name: str = None, 
                                     patient_number: str = None,
                                     supply_name: str = None,
                                     status: str = None) -> Dict[str, Any]:
        """Search supply usage records for a specific patient."""
        if not DATABASE_AVAILABLE:
            return {"success": False, "message": "Database not available"}

        try:
            db = self.get_db_session()
            
            # Start with base query
            query = db.query(PatientSupplyUsage)
            
            # Filter by patient if specified
            if patient_name or patient_number:
                patient_query = db.query(Patient)
                
                if patient_number:
                    patient_query = patient_query.filter(Patient.patient_number == patient_number)
                elif patient_name:
                    name_parts = patient_name.strip().split()
                    if len(name_parts) >= 2:
                        first_name, last_name = name_parts[0], name_parts[1]
                        patient_query = patient_query.filter(
                            and_(
                                Patient.first_name.ilike(f"%{first_name}%"),
                                Patient.last_name.ilike(f"%{last_name}%")
                            )
                        )
                    else:
                        patient_query = patient_query.filter(
                            or_(
                                Patient.first_name.ilike(f"%{patient_name}%"),
                                Patient.last_name.ilike(f"%{patient_name}%")
                            )
                        )
                
                patient = patient_query.first()
                if not patient:
                    db.close()
                    return {"success": False, "message": "Patient not found"}
                
                query = query.filter(PatientSupplyUsage.patient_id == patient.id)
            
            # Filter by supply name if specified
            if supply_name:
                supply_ids = db.query(Supply.id).filter(
                    Supply.name.ilike(f"%{supply_name}%")
                ).subquery()
                query = query.filter(PatientSupplyUsage.supply_id.in_(supply_ids))
            
            # Filter by status if specified
            if status:
                query = query.filter(PatientSupplyUsage.status == status)
            
            usage_records = query.order_by(desc(PatientSupplyUsage.prescribed_date)).all()
            
            if not usage_records:
                db.close()
                return {"success": True, "data": [], "message": "No supply usage records found matching criteria"}
            
            results = []
            for usage in usage_records:
                usage_data = self.serialize_model(usage)
                
                # Add related information
                if usage.patient:
                    usage_data["patient_name"] = f"{usage.patient.first_name} {usage.patient.last_name}"
                    usage_data["patient_number"] = usage.patient.patient_number
                
                if usage.supply:
                    usage_data["supply_name"] = usage.supply.name
                    usage_data["supply_category"] = usage.supply.category.name if usage.supply.category else None
                
                if usage.prescribed_by:
                    usage_data["prescribed_by_name"] = f"{usage.prescribed_by.first_name} {usage.prescribed_by.last_name}"
                
                results.append(usage_data)
            
            db.close()
            
            # Log the interaction
            self.log_interaction(
                query=f"Search supply usage - patient: {patient_name or patient_number}, supply: {supply_name}, status: {status}",
                response=f"Found {len(results)} supply usage records",
                tool_used="search_supply_usage_by_patient"
            )
            
            return {"success": True, "data": results}
            
        except Exception as e:
            db.close()
            return {"success": False, "message": f"Failed to search supply usage: {str(e)}"}

    def calculate_patient_medication_costs(self, patient_id: str, 
                                         admission_date: str = None,
                                         discharge_date: str = None) -> Dict[str, Any]:
        """Calculate total medication costs for a patient stay."""
        if not DATABASE_AVAILABLE:
            return {"success": False, "message": "Database not available"}

        try:
            db = self.get_db_session()
            
            # Build query
            query = db.query(PatientSupplyUsage).filter(
                PatientSupplyUsage.patient_id == uuid.UUID(patient_id)
            )
            
            # Add date filters if provided
            if admission_date:
                admission_dt = datetime.fromisoformat(admission_date)
                query = query.filter(PatientSupplyUsage.prescribed_date >= admission_dt)
            
            if discharge_date:
                discharge_dt = datetime.fromisoformat(discharge_date)
                query = query.filter(PatientSupplyUsage.prescribed_date <= discharge_dt)
            
            usage_records = query.all()
            
            if not usage_records:
                db.close()
                return {"success": True, "data": {"total_cost": 0, "breakdown": []}, 
                       "message": "No supply usage found for cost calculation"}
            
            # Calculate costs by category
            cost_breakdown = {}
            total_cost = 0
            
            for usage in usage_records:
                cost = float(usage.total_cost or 0)
                total_cost += cost
                
                category = "Unknown"
                if usage.supply and usage.supply.category:
                    category = usage.supply.category.name
                
                if category not in cost_breakdown:
                    cost_breakdown[category] = {
                        "category": category,
                        "total_cost": 0,
                        "item_count": 0,
                        "items": []
                    }
                
                cost_breakdown[category]["total_cost"] += cost
                cost_breakdown[category]["item_count"] += 1
                cost_breakdown[category]["items"].append({
                    "supply_name": usage.supply.name if usage.supply else "Unknown",
                    "quantity": usage.quantity_used,
                    "unit_cost": float(usage.unit_cost or 0),
                    "total_cost": cost,
                    "prescribed_date": usage.prescribed_date.isoformat() if usage.prescribed_date else None
                })
            
            db.close()
            
            result = {
                "total_cost": round(total_cost, 2),
                "breakdown": list(cost_breakdown.values()),
                "summary": {
                    "total_items": len(usage_records),
                    "total_categories": len(cost_breakdown),
                    "average_cost_per_item": round(total_cost / len(usage_records), 2) if usage_records else 0
                }
            }
            
            # Log the interaction
            self.log_interaction(
                query=f"Calculate medication costs for patient {patient_id}",
                response=f"Total cost: ${total_cost:.2f} for {len(usage_records)} items",
                tool_used="calculate_patient_medication_costs"
            )
            
            return {"success": True, "data": result}
            
        except Exception as e:
            db.close()
            return {"success": False, "message": f"Failed to calculate medication costs: {str(e)}"}
