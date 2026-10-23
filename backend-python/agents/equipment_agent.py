"""Equipment Management Agent - Handles all equipment-related operations"""

import uuid
from datetime import datetime, date
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from .base_agent import BaseAgent

try:
    from database import Equipment, EquipmentCategory, Department, SessionLocal
    DATABASE_AVAILABLE = True
except ImportError:
    DATABASE_AVAILABLE = False


class EquipmentAgent(BaseAgent):
    """Agent specialized in equipment management operations"""
    
    def __init__(self):
        super().__init__("Equipment Management Agent", "equipment_agent")
    
    def get_tools(self) -> List[str]:
        """Return list of equipment management tools"""
        return [
            "create_equipment_category",
            "list_equipment_categories",
            "create_equipment",
            "list_equipment",
            "get_equipment_by_id",
            "update_equipment_status",
            "update_equipment",
            "delete_equipment",
            "schedule_equipment_maintenance",
            "get_equipment_by_status"
        ]
    
    def get_capabilities(self) -> List[str]:
        """Return list of equipment management capabilities"""
        return [
            "Medical equipment tracking and monitoring",
            "Equipment maintenance scheduling",
            "Equipment status management",
            "Equipment category management",
            "Asset lifecycle management",
            "Equipment allocation and availability"
        ]
    
    # EQUIPMENT CATEGORY METHODS
    
    def create_equipment_category(self, name: str, description: str = None) -> Dict[str, Any]:
        """Create a new equipment category."""
        if not DATABASE_AVAILABLE:
            return {"success": False, "message": "Database not available"}
        
        try:
            db = self.get_db_session()
            category = EquipmentCategory(
                name=name,
                description=description
            )
            db.add(category)
            db.commit()
            db.refresh(category)
            result = self.serialize_model(category)
            db.close()
            
            # Log the interaction
            self.log_interaction(
                query=f"Create equipment category: {name}",
                response=f"Equipment category created successfully with ID: {result['id']}",
                tool_used="create_equipment_category"
            )
            
            return {"success": True, "message": "Equipment category created successfully", "data": result}
        except Exception as e:
            return {"success": False, "message": f"Failed to create equipment category: {str(e)}"}

    def list_equipment_categories(self) -> Dict[str, Any]:
        """List all equipment categories - brief information only."""
        if not DATABASE_AVAILABLE:
            return {"error": "Database not available"}
        
        try:
            db = self.get_db_session()
            categories = db.query(EquipmentCategory).all()
            
            # Return only essential information for list views
            result = []
            for category in categories:
                brief_info = {
                    "id": str(category.id),
                    "name": category.name,
                    "description": category.description
                }
                result.append(brief_info)
            
            db.close()
            
            # Log the interaction
            self.log_interaction(
                query="List all equipment categories",
                response=f"Found {len(result)} equipment categories",
                tool_used="list_equipment_categories"
            )
            
            return {"data": result}
        except Exception as e:
            return {"error": f"Failed to list equipment categories: {str(e)}"}

    # EQUIPMENT METHODS
    
    def create_equipment(self, equipment_id: str, name: str, category_id: str, model: str = None,
                        manufacturer: str = None, serial_number: str = None, purchase_date: str = None,
                        warranty_expiry: str = None, status: str = "available", 
                        department_id: str = None, location: str = None, cost: float = None,
                        last_maintenance: str = None, next_maintenance: str = None) -> Dict[str, Any]:
        """Create a new equipment record."""
        if not DATABASE_AVAILABLE:
            return {"success": False, "message": "Database not available"}
        
        try:
            # Parse dates
            purchase_dt = datetime.strptime(purchase_date, "%Y-%m-%d").date() if purchase_date else None
            warranty_dt = datetime.strptime(warranty_expiry, "%Y-%m-%d").date() if warranty_expiry else None
            last_maint_dt = datetime.strptime(last_maintenance, "%Y-%m-%d").date() if last_maintenance else None
            next_maint_dt = datetime.strptime(next_maintenance, "%Y-%m-%d").date() if next_maintenance else None
            
            db = self.get_db_session()
            equipment = Equipment(
                equipment_id=equipment_id,
                name=name,
                category_id=uuid.UUID(category_id),
                model=model,
                manufacturer=manufacturer,
                serial_number=serial_number,
                purchase_date=purchase_dt,
                warranty_expiry=warranty_dt,
                status=status,
                department_id=uuid.UUID(department_id) if department_id else None,
                location=location,
                cost=cost,
                last_maintenance=last_maint_dt,
                next_maintenance=next_maint_dt
            )
            db.add(equipment)
            db.commit()
            db.refresh(equipment)
            result = self.serialize_model(equipment)
            db.close()
            
            # Log the interaction
            self.log_interaction(
                query=f"Create equipment: {equipment_id} - {name}",
                response=f"Equipment created successfully with ID: {result['id']}",
                tool_used="create_equipment"
            )
            
            return {"success": True, "message": "Equipment created successfully", "data": result}
        except Exception as e:
            return {"success": False, "message": f"Failed to create equipment: {str(e)}"}

    def list_equipment(self, status: str = None, department_id: str = None, 
                      category_id: str = None) -> Dict[str, Any]:
        """List equipment with optional filtering."""
        if not DATABASE_AVAILABLE:
            return {"error": "Database not available"}
        
        try:
            db = self.get_db_session()
            query = db.query(Equipment)
            
            filters = []
            if status:
                query = query.filter(Equipment.status == status)
                filters.append(f"status: {status}")
            if department_id:
                query = query.filter(Equipment.department_id == uuid.UUID(department_id))
                filters.append(f"department_id: {department_id}")
            if category_id:
                query = query.filter(Equipment.category_id == uuid.UUID(category_id))
                filters.append(f"category_id: {category_id}")
            
            equipment_list = query.all()
            
            # Return only essential information for list views
            result = []
            for equipment in equipment_list:
                brief_info = {
                    "id": str(equipment.id),
                    "equipment_id": equipment.equipment_id,
                    "name": equipment.name,
                    "status": equipment.status,
                    "department_id": str(equipment.department_id) if equipment.department_id else None,
                    "category_id": str(equipment.category_id) if equipment.category_id else None,
                    "location": equipment.location
                }
                result.append(brief_info)
            
            db.close()
            
            # Log the interaction
            filter_text = f" with filters: {', '.join(filters)}" if filters else ""
            self.log_interaction(
                query=f"List equipment{filter_text}",
                response=f"Found {len(result)} equipment items",
                tool_used="list_equipment"
            )
            
            return {"data": result}
        except Exception as e:
            return {"error": f"Failed to list equipment: {str(e)}"}

    def get_equipment_by_id(self, equipment_id: str) -> Dict[str, Any]:
        """Get equipment by ID."""
        if not DATABASE_AVAILABLE:
            return {"error": "Database not available"}
        
        try:
            db = self.get_db_session()
            equipment = db.query(Equipment).filter(Equipment.id == uuid.UUID(equipment_id)).first()
            result = self.serialize_model(equipment) if equipment else None
            db.close()
            
            if result:
                # Log the interaction
                self.log_interaction(
                    query=f"Get equipment by ID: {equipment_id}",
                    response=f"Equipment found: {result.get('name', 'N/A')} ({result.get('equipment_id', 'N/A')})",
                    tool_used="get_equipment_by_id"
                )
                return {"data": result}
            else:
                return {"error": "Equipment not found"}
        except Exception as e:
            return {"error": f"Failed to get equipment: {str(e)}"}

    def get_equipment_by_status(self, status: str) -> Dict[str, Any]:
        """Get all equipment with a specific status."""
        if not DATABASE_AVAILABLE:
            return {"error": "Database not available"}
        
        try:
            db = self.get_db_session()
            equipment_list = db.query(Equipment).filter(Equipment.status == status).all()
            result = [self.serialize_model(equipment) for equipment in equipment_list]
            db.close()
            
            # Log the interaction
            self.log_interaction(
                query=f"Get equipment by status: {status}",
                response=f"Found {len(result)} equipment items with status {status}",
                tool_used="get_equipment_by_status"
            )
            
            return {"data": result}
        except Exception as e:
            return {"error": f"Failed to get equipment by status: {str(e)}"}

    def update_equipment_status(self, equipment_id: str, status: str, notes: str = None) -> Dict[str, Any]:
        """Update equipment status (available, in_use, maintenance, out_of_service)."""
        if not DATABASE_AVAILABLE:
            return {"success": False, "message": "Database not available"}
        
        try:
            db = self.get_db_session()
            equipment = db.query(Equipment).filter(Equipment.id == uuid.UUID(equipment_id)).first()
            
            if not equipment:
                db.close()
                return {"success": False, "message": "Equipment not found"}
            
            old_status = equipment.status
            equipment.status = status
            if hasattr(equipment, 'notes') and notes:
                equipment.notes = notes
            
            db.commit()
            db.refresh(equipment)
            result = self.serialize_model(equipment)
            db.close()
            
            # Log the interaction
            self.log_interaction(
                query=f"Update equipment {equipment_id} status from {old_status} to {status}",
                response=f"Equipment status updated successfully",
                tool_used="update_equipment_status"
            )
            
            return {"success": True, "message": "Equipment status updated successfully", "data": result}
        except Exception as e:
            return {"success": False, "message": f"Failed to update equipment status: {str(e)}"}

    def update_equipment(self, equipment_id: str, name: str = None, model: str = None,
                        manufacturer: str = None, location: str = None, 
                        department_id: str = None) -> Dict[str, Any]:
        """Update equipment information."""
        if not DATABASE_AVAILABLE:
            return {"success": False, "message": "Database not available"}
        
        try:
            db = self.get_db_session()
            equipment = db.query(Equipment).filter(Equipment.id == uuid.UUID(equipment_id)).first()
            
            if not equipment:
                db.close()
                return {"success": False, "message": "Equipment not found"}
            
            # Update provided fields
            update_fields = []
            if name is not None:
                equipment.name = name
                update_fields.append("name")
            if model is not None:
                equipment.model = model
                update_fields.append("model")
            if manufacturer is not None:
                equipment.manufacturer = manufacturer
                update_fields.append("manufacturer")
            if location is not None:
                equipment.location = location
                update_fields.append("location")
            if department_id is not None:
                equipment.department_id = uuid.UUID(department_id) if department_id else None
                update_fields.append("department_id")
            
            db.commit()
            db.refresh(equipment)
            result = self.serialize_model(equipment)
            db.close()
            
            # Log the interaction
            self.log_interaction(
                query=f"Update equipment {equipment_id}: {', '.join(update_fields)}",
                response=f"Equipment updated successfully",
                tool_used="update_equipment"
            )
            
            return {"success": True, "message": "Equipment updated successfully", "data": result}
        except Exception as e:
            return {"success": False, "message": f"Failed to update equipment: {str(e)}"}

    def schedule_equipment_maintenance(self, equipment_id: str, maintenance_date: str,
                                     maintenance_type: str = "routine", notes: str = None) -> Dict[str, Any]:
        """Schedule maintenance for equipment."""
        if not DATABASE_AVAILABLE:
            return {"success": False, "message": "Database not available"}
        
        try:
            db = self.get_db_session()
            equipment = db.query(Equipment).filter(Equipment.id == uuid.UUID(equipment_id)).first()
            
            if not equipment:
                db.close()
                return {"success": False, "message": "Equipment not found"}
            
            # Update equipment status to maintenance and schedule next maintenance
            equipment.status = "maintenance"
            equipment.next_maintenance = datetime.strptime(maintenance_date, "%Y-%m-%d").date()
            if notes:
                equipment.notes = f"{equipment.notes or ''}\nMaintenance scheduled ({maintenance_type}): {notes}".strip()
            
            db.commit()
            db.refresh(equipment)
            result = self.serialize_model(equipment)
            db.close()
            
            # Log the interaction
            self.log_interaction(
                query=f"Schedule maintenance for equipment {equipment_id} on {maintenance_date}",
                response=f"Equipment maintenance scheduled successfully",
                tool_used="schedule_equipment_maintenance"
            )
            
            return {"success": True, "message": "Equipment maintenance scheduled successfully", "data": result}
        except Exception as e:
            return {"success": False, "message": f"Failed to schedule equipment maintenance: {str(e)}"}

    def delete_equipment(self, equipment_id: str) -> Dict[str, Any]:
        """Delete equipment record."""
        if not DATABASE_AVAILABLE:
            return {"success": False, "message": "Database not available"}
        
        try:
            db = self.get_db_session()
            equipment = db.query(Equipment).filter(Equipment.id == uuid.UUID(equipment_id)).first()
            
            if not equipment:
                db.close()
                return {"success": False, "message": "Equipment not found"}
            
            equipment_name = equipment.name  # Store for logging
            db.delete(equipment)
            db.commit()
            db.close()
            
            # Log the interaction
            self.log_interaction(
                query=f"Delete equipment: {equipment_id}",
                response=f"Equipment {equipment_name} deleted successfully",
                tool_used="delete_equipment"
            )
            
            return {"success": True, "message": "Equipment deleted successfully"}
        except Exception as e:
            return {"success": False, "message": f"Failed to delete equipment: {str(e)}"}
