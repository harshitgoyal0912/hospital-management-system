"""Department Management Agent - Handles all department-related operations"""

import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from .base_agent import BaseAgent

try:
    from database import Department, User, SessionLocal
    DATABASE_AVAILABLE = True
except ImportError:
    DATABASE_AVAILABLE = False


class DepartmentAgent(BaseAgent):
    """Agent specialized in department management operations"""
    
    def __init__(self):
        super().__init__("Department Management Agent", "department_agent")
    
    def get_tools(self) -> List[str]:
        """Return list of department management tools"""
        return [
            "create_department",
            "list_departments",
            "get_department_by_id",
            "update_department",
            "delete_department"
        ]
    
    def get_capabilities(self) -> List[str]:
        """Return list of department management capabilities"""
        return [
            "Department creation and configuration",
            "Department hierarchy management",
            "Head doctor assignments",
            "Department information retrieval",
            "Hospital organizational structure"
        ]
    
    def create_department(self, name: str, description: str = None, head_doctor_id: str = None,
                         floor_number: int = None, phone: str = None, email: str = None) -> Dict[str, Any]:
        """Create a new department."""
        if not DATABASE_AVAILABLE:
            return {"success": False, "message": "Database not available"}
        
        try:
            db = self.get_db_session()
            department = Department(
                name=name,
                description=description,
                head_doctor_id=uuid.UUID(head_doctor_id) if head_doctor_id else None,
                floor_number=floor_number,
                phone=phone,
                email=email
            )
            db.add(department)
            db.commit()
            db.refresh(department)
            result = self.serialize_model(department)
            db.close()
            
            # Log the interaction
            self.log_interaction(
                query=f"Create department: {name}",
                response=f"Department created successfully with ID: {result['id']}",
                tool_used="create_department"
            )
            
            return {"success": True, "message": "Department created successfully", "data": result}
        except Exception as e:
            return {"success": False, "message": f"Failed to create department: {str(e)}"}

    def list_departments(self) -> Dict[str, Any]:
        """List all departments - brief information only."""
        if not DATABASE_AVAILABLE:
            return {"error": "Database not available"}
        
        try:
            db = self.get_db_session()
            departments = db.query(Department).all()
            
            # Return only essential information for list views
            result = []
            for dept in departments:
                brief_info = {
                    "id": str(dept.id),
                    "name": dept.name,
                    "description": dept.description,
                    "floor": dept.floor_number  # Use the correct attribute name
                }
                result.append(brief_info)
            
            db.close()
            
            # Log the interaction
            self.log_interaction(
                query="List all departments",
                response=f"Found {len(result)} departments",
                tool_used="list_departments"
            )
            
            return {"data": result}
        except Exception as e:
            return {"error": f"Failed to list departments: {str(e)}"}

    def get_department_by_id(self, department_id: str) -> Dict[str, Any]:
        """Get a department by ID."""
        if not DATABASE_AVAILABLE:
            return {"error": "Database not available"}
        
        try:
            db = self.get_db_session()
            department = db.query(Department).filter(Department.id == uuid.UUID(department_id)).first()
            result = self.serialize_model(department) if department else None
            db.close()
            
            if result:
                # Log the interaction
                self.log_interaction(
                    query=f"Get department by ID: {department_id}",
                    response=f"Department found: {result.get('name', 'N/A')}",
                    tool_used="get_department_by_id"
                )
                return {"data": result}
            else:
                return {"error": "Department not found"}
        except Exception as e:
            return {"error": f"Failed to get department: {str(e)}"}

    def update_department(self, department_id: str, name: str = None, description: str = None,
                         head_doctor_id: str = None, floor_number: int = None,
                         phone: str = None, email: str = None) -> Dict[str, Any]:
        """Update department information."""
        if not DATABASE_AVAILABLE:
            return {"success": False, "message": "Database not available"}
        
        try:
            db = self.get_db_session()
            department = db.query(Department).filter(Department.id == uuid.UUID(department_id)).first()
            
            if not department:
                db.close()
                return {"success": False, "message": "Department not found"}
            
            # Update provided fields
            update_fields = []
            if name is not None:
                department.name = name
                update_fields.append("name")
            if description is not None:
                department.description = description
                update_fields.append("description")
            if head_doctor_id is not None:
                department.head_doctor_id = uuid.UUID(head_doctor_id) if head_doctor_id else None
                update_fields.append("head_doctor_id")
            if floor_number is not None:
                department.floor_number = floor_number
                update_fields.append("floor_number")
            if phone is not None:
                department.phone = phone
                update_fields.append("phone")
            if email is not None:
                department.email = email
                update_fields.append("email")
            
            db.commit()
            db.refresh(department)
            result = self.serialize_model(department)
            db.close()
            
            # Log the interaction
            self.log_interaction(
                query=f"Update department {department_id}: {', '.join(update_fields)}",
                response=f"Department updated successfully",
                tool_used="update_department"
            )
            
            return {"success": True, "message": "Department updated successfully", "data": result}
        except Exception as e:
            return {"success": False, "message": f"Failed to update department: {str(e)}"}

    def delete_department(self, department_id: str) -> Dict[str, Any]:
        """Delete a department."""
        if not DATABASE_AVAILABLE:
            return {"success": False, "message": "Database not available"}
        
        try:
            db = self.get_db_session()
            department = db.query(Department).filter(Department.id == uuid.UUID(department_id)).first()
            
            if not department:
                db.close()
                return {"success": False, "message": "Department not found"}
            
            dept_name = department.name  # Store for logging
            db.delete(department)
            db.commit()
            db.close()
            
            # Log the interaction
            self.log_interaction(
                query=f"Delete department: {department_id}",
                response=f"Department {dept_name} deleted successfully",
                tool_used="delete_department"
            )
            
            return {"success": True, "message": "Department deleted successfully"}
        except Exception as e:
            return {"success": False, "message": f"Failed to delete department: {str(e)}"}
