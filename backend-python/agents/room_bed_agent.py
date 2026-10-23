"""Room & Bed Management Agent - Handles room and bed operations"""

import uuid
from datetime import datetime, date
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from .base_agent import BaseAgent

try:
    from database import Room, Bed, Patient, Department, SessionLocal
    DATABASE_AVAILABLE = True
except ImportError:
    DATABASE_AVAILABLE = False


class RoomBedAgent(BaseAgent):
    """Agent specialized in room and bed management operations"""
    
    def __init__(self):
        super().__init__("Room & Bed Management Agent", "room_bed_agent")
    
    def get_tools(self) -> List[str]:
        """Return list of room and bed management tools"""
        return [
            "create_room",
            "list_rooms",
            "get_room_by_id",
            "update_room",
            "delete_room",
            "create_bed",
            "list_beds",
            "get_bed_by_id",
            "get_bed_by_number",
            "assign_bed_to_patient",
            "discharge_bed",
            "update_bed_status"
        ]
    
    def get_capabilities(self) -> List[str]:
        """Return list of room and bed management capabilities"""
        return [
            "Room allocation and management",
            "Bed inventory tracking",
            "Patient bed assignments",
            "Bed occupancy monitoring",
            "Room and bed availability checking",
            "Patient admission and discharge"
        ]
    
    # ROOM MANAGEMENT METHODS
    
    def create_room(self, room_number: str, department_id: str, room_type: str = None,
                   floor_number: int = None, capacity: int = None) -> Dict[str, Any]:
        """Create a new room."""
        if not DATABASE_AVAILABLE:
            return {"success": False, "message": "Database not available"}
        
        room_number = (room_number or "").strip()
        if not room_number:
            return {"success": False, "message": "Room number is required"}
        if len(room_number) > 10:
            return {"success": False, "message": "Room number must be 10 characters or fewer"}
        if not department_id:
            return {"success": False, "message": "Department is required"}

        try:
            db = self.get_db_session()
            if db.query(Room).filter(Room.room_number == room_number).first():
                db.close()
                return {"success": False, "message": f"Room {room_number} already exists"}
            room = Room(
                room_number=room_number,
                department_id=uuid.UUID(department_id),
                room_type=room_type,
                floor_number=floor_number,
                capacity=capacity
            )
            db.add(room)
            db.commit()
            db.refresh(room)
            result = self.serialize_model(room)
            db.close()
            
            # Log the interaction
            self.log_interaction(
                query=f"Create room: {room_number}",
                response=f"Room created successfully with ID: {result['id']}",
                tool_used="create_room"
            )
            
            return {"success": True, "message": "Room created successfully", "data": result}
        except Exception as e:
            return {"success": False, "message": f"Failed to create room: {str(e)}"}

    def list_rooms(self, department_id: str = None, status: str = None) -> Dict[str, Any]:
        """List rooms with optional filtering - brief information only."""
        if not DATABASE_AVAILABLE:
            return {"error": "Database not available"}
        
        try:
            db = self.get_db_session()
            query = db.query(Room)
            
            filters = []
            if department_id:
                query = query.filter(Room.department_id == uuid.UUID(department_id))
                filters.append(f"department_id: {department_id}")
            
            if status:
                query = query.filter(Room.status == status)
                filters.append(f"status: {status}")
            
            rooms = query.all()
            
            # Return only essential information for list views
            result = []
            for room in rooms:
                brief_info = {
                    "id": str(room.id),
                    "room_number": room.room_number,
                    "room_type": room.room_type,
                    "department_id": str(room.department_id) if room.department_id else None,
                    "capacity": room.capacity,
                    "status": room.status
                }
                result.append(brief_info)
            
            db.close()
            
            # Log the interaction
            filter_text = f" with filters: {', '.join(filters)}" if filters else ""
            self.log_interaction(
                query=f"List rooms{filter_text}",
                response=f"Found {len(result)} rooms",
                tool_used="list_rooms"
            )
            
            return {"data": result}
        except Exception as e:
            return {"error": f"Failed to list rooms: {str(e)}"}

    def get_room_by_id(self, room_id: str) -> Dict[str, Any]:
        """Get a room by ID."""
        if not DATABASE_AVAILABLE:
            return {"error": "Database not available"}
        
        try:
            db = self.get_db_session()
            room = db.query(Room).filter(Room.id == uuid.UUID(room_id)).first()
            result = self.serialize_model(room) if room else None
            db.close()
            
            if result:
                # Log the interaction
                self.log_interaction(
                    query=f"Get room by ID: {room_id}",
                    response=f"Room found: {result.get('room_number', 'N/A')}",
                    tool_used="get_room_by_id"
                )
                return {"data": result}
            else:
                return {"error": "Room not found"}
        except Exception as e:
            return {"error": f"Failed to get room: {str(e)}"}

    def update_room(self, room_id: str, room_number: str = None, room_type: str = None,
                   capacity: int = None) -> Dict[str, Any]:
        """Update room information."""
        if not DATABASE_AVAILABLE:
            return {"success": False, "message": "Database not available"}
        
        try:
            db = self.get_db_session()
            room = db.query(Room).filter(Room.id == uuid.UUID(room_id)).first()
            
            if not room:
                db.close()
                return {"success": False, "message": "Room not found"}
            
            # Update provided fields
            update_fields = []
            if room_number is not None:
                room.room_number = room_number
                update_fields.append("room_number")
            if room_type is not None:
                room.room_type = room_type
                update_fields.append("room_type")
            if capacity is not None:
                room.capacity = capacity
                update_fields.append("capacity")
            
            db.commit()
            db.refresh(room)
            result = self.serialize_model(room)
            db.close()
            
            # Log the interaction
            self.log_interaction(
                query=f"Update room {room_id}: {', '.join(update_fields)}",
                response=f"Room updated successfully",
                tool_used="update_room"
            )
            
            return {"success": True, "message": "Room updated successfully", "data": result}
        except Exception as e:
            return {"success": False, "message": f"Failed to update room: {str(e)}"}

    def delete_room(self, room_id: str) -> Dict[str, Any]:
        """Delete a room."""
        if not DATABASE_AVAILABLE:
            return {"success": False, "message": "Database not available"}
        
        try:
            db = self.get_db_session()
            room = db.query(Room).filter(Room.id == uuid.UUID(room_id)).first()
            
            if not room:
                db.close()
                return {"success": False, "message": "Room not found"}
            
            room_number = room.room_number  # Store for logging
            db.delete(room)
            db.commit()
            db.close()
            
            # Log the interaction
            self.log_interaction(
                query=f"Delete room: {room_id}",
                response=f"Room {room_number} deleted successfully",
                tool_used="delete_room"
            )
            
            return {"success": True, "message": "Room deleted successfully"}
        except Exception as e:
            return {"success": False, "message": f"Failed to delete room: {str(e)}"}

    # BED MANAGEMENT METHODS
    
    def create_bed(self, bed_number: str, room_id: str, bed_type: str = None, 
                  status: str = "available") -> Dict[str, Any]:
        """Create a new bed."""
        if not DATABASE_AVAILABLE:
            return {"success": False, "message": "Database not available"}
        
        bed_number = (bed_number or "").strip()
        if not bed_number:
            return {"success": False, "message": "Bed number is required"}
        if len(bed_number) > 10:
            return {"success": False, "message": "Bed number must be 10 characters or fewer"}
        if not room_id:
            return {"success": False, "message": "Room is required"}

        try:
            db = self.get_db_session()
            if not db.query(Room).filter(Room.id == uuid.UUID(room_id)).first():
                db.close()
                return {"success": False, "message": "Room not found"}
            if db.query(Bed).filter(Bed.room_id == uuid.UUID(room_id), Bed.bed_number == bed_number).first():
                db.close()
                return {"success": False, "message": f"Bed {bed_number} already exists in this room"}
            bed = Bed(
                bed_number=bed_number,
                room_id=uuid.UUID(room_id),
                bed_type=bed_type,
                status=status
            )
            db.add(bed)
            db.commit()
            db.refresh(bed)
            result = self.serialize_model(bed)
            db.close()
            
            # Log the interaction
            self.log_interaction(
                query=f"Create bed: {bed_number}",
                response=f"Bed created successfully with ID: {result['id']}",
                tool_used="create_bed"
            )
            
            return {"success": True, "message": "Bed created successfully", "data": result}
        except Exception as e:
            return {"success": False, "message": f"Failed to create bed: {str(e)}"}

    def list_beds(self, status: str = None, room_id: str = None) -> Dict[str, Any]:
        """❌ DO NOT USE for checking individual bed status! Returns ALL beds.
        
        ⚠️ For checking ONE specific bed (e.g. "check bed 302A"), 
        use 'get_bed_status_with_time_remaining' instead!
        
        This tool is only for:
        - Getting overview of MULTIPLE beds
        - Finding beds by status (available, occupied, cleaning)
        - Listing beds in a specific room
        
        Returns basic info without cleaning time details.
        """
        if not DATABASE_AVAILABLE:
            return {"error": "Database not available"}
        
        try:
            db = self.get_db_session()
            query = db.query(Bed)
            
            filters = []
            if status:
                query = query.filter(Bed.status == status)
                filters.append(f"status: {status}")
            if room_id:
                query = query.filter(Bed.room_id == uuid.UUID(room_id))
                filters.append(f"room_id: {room_id}")
            
            beds = query.all()
            
            # Return only essential information for list views
            result = []
            for bed in beds:
                brief_info = {
                    "id": str(bed.id),
                    "bed_number": bed.bed_number,
                    "room_id": str(bed.room_id) if bed.room_id else None,
                    "room_number": getattr(bed.room, 'room_number', None) if bed.room else None,
                    "status": bed.status,
                    "patient_id": str(bed.patient_id) if bed.patient_id else None,
                    "admission_date": bed.admission_date.isoformat() if bed.admission_date else None
                }
                result.append(brief_info)
            
            db.close()
            
            # Log the interaction
            filter_text = f" with filters: {', '.join(filters)}" if filters else ""
            self.log_interaction(
                query=f"List beds{filter_text}",
                response=f"Found {len(result)} beds",
                tool_used="list_beds"
            )
            
            return {"data": result}
        except Exception as e:
            return {"error": f"Failed to list beds: {str(e)}"}

    def get_bed_by_id(self, bed_id: str) -> Dict[str, Any]:
        """Get a bed by ID."""
        if not DATABASE_AVAILABLE:
            return {"error": "Database not available"}
        
        try:
            db = self.get_db_session()
            bed = db.query(Bed).filter(Bed.id == uuid.UUID(bed_id)).first()
            result = self.serialize_model(bed) if bed else None
            db.close()
            
            if result:
                # Log the interaction
                self.log_interaction(
                    query=f"Get bed by ID: {bed_id}",
                    response=f"Bed found: {result.get('bed_number', 'N/A')}",
                    tool_used="get_bed_by_id"
                )
                return {"data": result}
            else:
                return {"error": "Bed not found"}
        except Exception as e:
            return {"error": f"Failed to get bed: {str(e)}"}

    def get_bed_by_number(self, bed_number: str) -> Dict[str, Any]:
        """Get a bed by bed number."""
        if not DATABASE_AVAILABLE:
            return {"error": "Database not available"}
        
        try:
            db = self.get_db_session()
            bed = db.query(Bed).filter(Bed.bed_number == bed_number).first()
            result = self.serialize_model(bed) if bed else None
            db.close()
            
            if result:
                # Log the interaction
                self.log_interaction(
                    query=f"Get bed by number: {bed_number}",
                    response=f"Bed {bed_number} found with ID: {result.get('id', 'N/A')}",
                    tool_used="get_bed_by_number"
                )
                return {"data": result}
            else:
                return {"error": f"Bed not found with number: {bed_number}"}
        except Exception as e:
            return {"error": f"Failed to get bed by number: {str(e)}"}

    def assign_bed_to_patient(self, bed_id: str, patient_id: str, 
                             admission_date: str = None) -> Dict[str, Any]:
        """Assign a bed to a patient."""
        if not DATABASE_AVAILABLE:
            return {"success": False, "message": "Database not available"}
        
        try:
            db = self.get_db_session()

            # Lock the bed row for the remainder of this transaction.
            #
            # Without the lock two concurrent requests both read status
            # "available", both pass the check below, and both assign the same
            # bed. Idempotency does not help here: those are two *different*
            # requests, each legitimately entitled to run once.
            #
            # FOR UPDATE makes the second request wait until the first commits,
            # after which it re-reads the row and sees "occupied". The
            # availability check below is therefore evaluated against state that
            # cannot change underneath it.
            #
            # Note: SQLite silently ignores FOR UPDATE, so this protection only
            # exists on PostgreSQL. The concurrency test is Postgres-only for
            # that reason.
            bed = (
                db.query(Bed)
                .filter(Bed.id == uuid.UUID(bed_id))
                .with_for_update()
                .first()
            )
            patient = db.query(Patient).filter(Patient.id == uuid.UUID(patient_id)).first()

            if not bed:
                db.rollback()
                db.close()
                return {"success": False, "message": "Bed not found"}
            if not patient:
                db.rollback()
                db.close()
                return {"success": False, "message": "Patient not found"}
            if bed.status != "available":
                # Re-checked while holding the lock, so this is authoritative.
                # Read the status into a local BEFORE rolling back: rollback
                # expires the instance, and touching an expired attribute on a
                # closed session raises instead of returning the value.
                current_status = bed.status
                db.rollback()
                db.close()
                return {"success": False, "message": f"Bed is not available (current status: {current_status})"}

            existing_bed = db.query(Bed).filter(Bed.patient_id == patient.id, Bed.id != bed.id).first()
            if existing_bed:
                existing_bed_number = existing_bed.bed_number
                db.rollback()
                db.close()
                return {"success": False, "message": f"Patient is already assigned to bed {existing_bed_number}"}

            # Assigning a bed to a previously discharged patient re-admits them
            if patient.status == "discharged":
                patient.status = "active"
                patient.updated_at = datetime.now()

            # Assign bed to patient
            bed.patient_id = uuid.UUID(patient_id)
            bed.status = "occupied"
            if admission_date:
                bed.admission_date = datetime.strptime(admission_date, "%Y-%m-%d").date()
            else:
                bed.admission_date = date.today()
            
            db.commit()
            db.refresh(bed)
            result = self.serialize_model(bed)
            db.close()
            
            # Log the interaction (avoid accessing patient object after session close)
            self.log_interaction(
                query=f"Assign bed {bed_id} to patient {patient_id}",
                response=f"Bed {bed.bed_number} assigned to patient {patient_id}",
                tool_used="assign_bed_to_patient"
            )
            
            return {"success": True, "message": "Bed assigned successfully", "data": result}
        except Exception as e:
            db.rollback()
            db.close()
            return {"success": False, "message": f"Failed to assign bed: {str(e)}"}

    def discharge_bed(self, bed_id: str, discharge_date: str = None) -> Dict[str, Any]:
        """Discharge a patient from a bed."""
        if not DATABASE_AVAILABLE:
            return {"success": False, "message": "Database not available"}
        
        try:
            db = self.get_db_session()
            bed = db.query(Bed).filter(Bed.id == uuid.UUID(bed_id)).first()
            
            if not bed:
                db.close()
                return {"success": False, "message": "Bed not found"}
            if bed.status != "occupied":
                db.close()
                return {"success": False, "message": f"Bed is not occupied (current status: {bed.status})"}
            
            # Preserve previous patient before clearing
            previous_patient_id = bed.patient_id
            
            # Discharge patient from bed and start cleaning process
            bed.patient_id = None
            bed.status = "cleaning"  # Set to cleaning, not available
            if discharge_date:
                bed.discharge_date = datetime.strptime(discharge_date, "%Y-%m-%d").date()
            else:
                bed.discharge_date = date.today()
            
            # Create a BedTurnover record and start cleaning immediately
            try:
                from database import BedTurnover
                from datetime import datetime as dt
                turnover = BedTurnover(
                    bed_id=bed.id,
                    previous_patient_id=previous_patient_id,
                    status="cleaning",  # Start cleaning immediately
                    turnover_type="standard",
                    discharge_time=dt.now(),
                    cleaning_start_time=dt.now(),  # Start cleaning now
                    estimated_cleaning_duration=30,
                    priority_level="normal"
                )
                db.add(turnover)
            except Exception as e:
                # If turnover creation fails, continue with basic discharge
                print(f"⚠️ Failed to create BedTurnover during discharge: {e}")
                # Still set bed to cleaning status even if turnover fails
                bed.status = "cleaning"
            
            db.commit()
            db.refresh(bed)
            result = self.serialize_model(bed)
            db.close()
            
            # Log the interaction
            self.log_interaction(
                query=f"Discharge bed {bed_id}",
                response=f"Bed {bed.bed_number} discharged, patient {previous_patient_id} released",
                tool_used="discharge_bed"
            )
            
            return {"success": True, "message": "Bed discharged successfully", "data": result}
        except Exception as e:
            return {"success": False, "message": f"Failed to discharge bed: {str(e)}"}

    def update_bed_status(self, bed_id: str, status: str, notes: str = None) -> Dict[str, Any]:
        """Update bed status (available, occupied, maintenance, out_of_service)."""
        if not DATABASE_AVAILABLE:
            return {"success": False, "message": "Database not available"}
        
        try:
            db = self.get_db_session()
            bed = db.query(Bed).filter(Bed.id == uuid.UUID(bed_id)).first()
            
            if not bed:
                db.close()
                return {"success": False, "message": "Bed not found"}
            
            old_status = bed.status
            bed.status = status
            if notes:
                bed.notes = notes
            
            db.commit()
            db.refresh(bed)
            result = self.serialize_model(bed)
            db.close()
            
            # Log the interaction
            self.log_interaction(
                query=f"Update bed {bed_id} status from {old_status} to {status}",
                response=f"Bed status updated successfully",
                tool_used="update_bed_status"
            )
            
            return {"success": True, "message": "Bed status updated successfully", "data": result}
        except Exception as e:
            return {"success": False, "message": f"Failed to update bed status: {str(e)}"}
