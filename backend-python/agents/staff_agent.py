"""Staff Management Agent - Handles all staff-related operations"""

import uuid
from datetime import datetime, date
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from .base_agent import BaseAgent

try:
    from database import Staff, User, Department, SessionLocal
    DATABASE_AVAILABLE = True
except ImportError:
    DATABASE_AVAILABLE = False


class StaffAgent(BaseAgent):
    """Agent specialized in staff management operations"""
    
    def __init__(self):
        super().__init__("Staff Management Agent", "staff_agent")
    
    def serialize_model(self, staff):
        """Convert Staff model to dictionary with User relationship included."""
        if staff is None:
            return None
        
        # Get base staff data
        result = super().serialize_model(staff)
        
        # Add User relationship data if available
        if staff.user:
            result['first_name'] = staff.user.first_name
            result['last_name'] = staff.user.last_name  
            result['email'] = staff.user.email
            result['username'] = staff.user.username
            result['role'] = staff.user.role
            result['phone'] = staff.user.phone
            result['is_active'] = staff.user.is_active
        else:
            # Provide defaults if no user relationship
            result['first_name'] = "Unknown"
            result['last_name'] = "User"
            result['email'] = None
            result['username'] = None
            result['role'] = None
            result['phone'] = None
            result['is_active'] = False
            
        return result
    
    def get_tools(self) -> List[str]:
        """Return list of staff management tools"""
        return [
            "create_staff",
            "list_staff",
            "get_staff_by_id",
            "update_staff",
            "delete_staff",
            "get_staff_by_department",
            "update_staff_status"
        ]
    
    def get_capabilities(self) -> List[str]:
        """Return list of staff management capabilities"""
        return [
            "Staff registration and profile management",
            "Department assignment and transfers",
            "Staff scheduling and availability",
            "Employee status tracking",
            "Shift management",
            "Staff performance monitoring"
        ]
    
    # Staff position (as chosen in the UI) -> users.role
    POSITION_ROLES = {
        "doctor": "doctor", "surgeon": "doctor", "physician": "doctor",
        "nurse": "nurse",
        "receptionist": "receptionist",
        "administrator": "manager", "manager": "manager",
    }

    def _create_user_for_staff(self, db, first_name: str, last_name: str, employee_id: str,
                               position: str, email: str = None, phone: str = None):
        """Create the users row a staff record must link to.

        The password hash is a placeholder, which login treats as unusable
        (hms_agent/auth/passwords.needs_rehash): the account cannot sign in until
        an administrator sets a real password (scripts/reset_dev_users.py).
        """
        base = "".join(c for c in f"{first_name}.{last_name}".lower() if c.isalnum() or c == ".")[:40] or "staff"
        username, n = base, 1
        while db.query(User).filter(User.username == username).first():
            n += 1
            username = f"{base}{n}"
        email = email or f"{username}@hospital.local"
        if db.query(User).filter(User.email == email).first():
            raise ValueError(f"A user with email {email} already exists")

        user = User(
            username=username,
            email=email,
            password_hash=f"unset:{employee_id}",
            role=self.POSITION_ROLES.get((position or "").strip().lower(), "support_staff"),
            first_name=first_name,
            last_name=last_name or "-",
            phone=phone,
            is_active=True,
        )
        db.add(user)
        db.flush()
        return user

    def create_staff(self, employee_id: str, department_id: str, position: str, user_id: str = None,
                    first_name: str = None, last_name: str = None, email: str = None, phone: str = None,
                    specialization: str = None, license_number: str = None, hire_date: str = None,
                    salary: float = None, shift_pattern: str = None, status: str = "active") -> Dict[str, Any]:
        """Create a new staff record.

        Links to an existing user when user_id is given; otherwise creates the
        user account from first_name/last_name (as the Add Staff form does).
        """
        if not DATABASE_AVAILABLE:
            return {"success": False, "message": "Database not available"}

        db = None
        try:
            # Parse hire date
            hire_dt = datetime.strptime(hire_date, "%Y-%m-%d").date() if hire_date else date.today()

            db = self.get_db_session()

            if db.query(Staff).filter(Staff.employee_id == employee_id).first():
                db.close()
                return {"success": False, "message": f"Employee ID {employee_id} already exists"}

            if user_id:
                # Verify user exists
                user = db.query(User).filter(User.id == uuid.UUID(user_id)).first()
                if not user:
                    db.close()
                    return {"success": False, "message": "User not found"}
            elif first_name:
                user = self._create_user_for_staff(db, first_name, last_name, employee_id, position, email, phone)
            else:
                db.close()
                return {"success": False, "message": "Either user_id or first_name is required"}

            # Create the Staff record
            staff = Staff(
                user_id=user.id,
                employee_id=employee_id,
                department_id=uuid.UUID(department_id),
                position=position,
                specialization=specialization,
                license_number=license_number,
                hire_date=hire_dt,
                salary=salary,
                shift_pattern=shift_pattern,
                status=status
            )
            db.add(staff)
            db.commit()
            db.refresh(staff)
            
            # Get user data before closing session
            user_phone = user.phone
            user_username = user.username
            
            result = self.serialize_model(staff)
            db.close()
            
            # Add user data to result
            result['phone'] = user_phone
            result['username'] = user_username
            
            # Log the interaction
            self.log_interaction(
                query=f"Create staff: {employee_id} for user {result.get('user_id')} in department {department_id}",
                response=f"Staff record created successfully with ID: {result['id']}",
                tool_used="create_staff"
            )

            return {"success": True, "message": "Staff created successfully", "data": result}
        except Exception as e:
            if db is not None:
                db.rollback()
                db.close()
            return {"success": False, "message": f"Failed to create staff: {str(e)}"}

    def list_staff(self, department_id: str = None, status: str = None, position: str = None) -> Dict[str, Any]:
        """List staff with optional filtering - brief information only."""
        if not DATABASE_AVAILABLE:
            return {"error": "Database not available"}
        
        try:
            db = self.get_db_session()
            query = db.query(Staff)
            
            filters = []
            if department_id:
                query = query.filter(Staff.department_id == uuid.UUID(department_id))
                filters.append(f"department_id: {department_id}")
            if status:
                query = query.filter(Staff.status == status)
                filters.append(f"status: {status}")
            if position:
                query = query.filter(Staff.position.ilike(f"%{position}%"))
                filters.append(f"position: {position}")
            
            staff_list = query.all()
            
            # Use serialize_model for consistent data format
            result = [self.serialize_model(staff) for staff in staff_list]
            
            db.close()
            
            # Log the interaction
            filter_text = f" with filters: {', '.join(filters)}" if filters else ""
            self.log_interaction(
                query=f"List staff{filter_text}",
                response=f"Found {len(result)} staff members",
                tool_used="list_staff"
            )
            
            return {"data": result}
        except Exception as e:
            return {"error": f"Failed to list staff: {str(e)}"}

    def get_staff_by_id(self, staff_id: str) -> Dict[str, Any]:
        """Get a staff member by ID (supports both UUID and employee_id)."""
        if not DATABASE_AVAILABLE:
            return {"error": "Database not available"}
        
        try:
            db = self.get_db_session()
            staff = None
            
            # First try to find by employee_id (human-readable ID like EMP1112)
            staff = db.query(Staff).filter(Staff.employee_id == staff_id).first()
            
            # If not found by employee_id, try by UUID
            if not staff:
                try:
                    staff = db.query(Staff).filter(Staff.id == uuid.UUID(staff_id)).first()
                except ValueError:
                    # Invalid UUID format, stick with employee_id result (None)
                    pass
            
            result = self.serialize_model(staff) if staff else None
            db.close()
            
            if result:
                # Log the interaction
                self.log_interaction(
                    query=f"Get staff by ID: {staff_id}",
                    response=f"Staff found: {result.get('employee_id', 'N/A')} - {result.get('position', 'N/A')}",
                    tool_used="get_staff_by_id"
                )
                return {"data": result}
            else:
                return {"error": f"Staff member with ID '{staff_id}' not found"}
        except Exception as e:
            return {"error": f"Failed to get staff: {str(e)}"}

    def get_staff_by_department(self, department_id: str) -> Dict[str, Any]:
        """Get all staff members in a specific department."""
        if not DATABASE_AVAILABLE:
            return {"error": "Database not available"}
        
        try:
            db = self.get_db_session()
            staff_list = db.query(Staff).filter(Staff.department_id == uuid.UUID(department_id)).all()
            result = [self.serialize_model(staff) for staff in staff_list]
            db.close()
            
            # Log the interaction
            self.log_interaction(
                query=f"Get staff by department: {department_id}",
                response=f"Found {len(result)} staff members in department",
                tool_used="get_staff_by_department"
            )
            
            return {"data": result}
        except Exception as e:
            return {"error": f"Failed to get staff by department: {str(e)}"}

    def update_staff(self, staff_id: str, employee_id: str = None, department_id: str = None,
                    position: str = None, salary: float = None, status: str = None) -> Dict[str, Any]:
        """Update staff information (supports both UUID and employee_id)."""
        if not DATABASE_AVAILABLE:
            return {"success": False, "message": "Database not available"}
        
        try:
            db = self.get_db_session()
            staff = None
            
            # First try to find by employee_id (human-readable ID like EMP1112)
            staff = db.query(Staff).filter(Staff.employee_id == staff_id).first()
            
            # If not found by employee_id, try by UUID
            if not staff:
                try:
                    staff = db.query(Staff).filter(Staff.id == uuid.UUID(staff_id)).first()
                except ValueError:
                    # Invalid UUID format, stick with employee_id result (None)
                    pass
            
            if not staff:
                db.close()
                return {"success": False, "message": f"Staff member with ID '{staff_id}' not found"}
            
            # Update provided fields
            update_fields = []
            if employee_id is not None:
                staff.employee_id = employee_id
                update_fields.append("employee_id")
            if department_id is not None:
                staff.department_id = uuid.UUID(department_id)
                update_fields.append("department_id")
            if position is not None:
                staff.position = position
                update_fields.append("position")
            if salary is not None:
                staff.salary = salary
                update_fields.append("salary")
            if status is not None:
                staff.status = status
                update_fields.append("status")
            
            db.commit()
            db.refresh(staff)
            result = self.serialize_model(staff)
            db.close()
            
            # Log the interaction
            self.log_interaction(
                query=f"Update staff {staff_id}: {', '.join(update_fields)}",
                response=f"Staff updated successfully",
                tool_used="update_staff"
            )
            
            return {"success": True, "message": "Staff updated successfully", "data": result}
        except Exception as e:
            return {"success": False, "message": f"Failed to update staff: {str(e)}"}

    def update_staff_status(self, staff_id: str, status: str, notes: str = None) -> Dict[str, Any]:
        """Update staff status (active, inactive, on_leave, terminated) - supports both UUID and employee_id."""
        if not DATABASE_AVAILABLE:
            return {"success": False, "message": "Database not available"}
        
        try:
            db = self.get_db_session()
            staff = None
            
            # First try to find by employee_id (human-readable ID like EMP1112)
            staff = db.query(Staff).filter(Staff.employee_id == staff_id).first()
            
            # If not found by employee_id, try by UUID
            if not staff:
                try:
                    staff = db.query(Staff).filter(Staff.id == uuid.UUID(staff_id)).first()
                except ValueError:
                    # Invalid UUID format, stick with employee_id result (None)
                    pass
            
            if not staff:
                db.close()
                return {"success": False, "message": f"Staff member with ID '{staff_id}' not found"}
            
            old_status = staff.status
            staff.status = status
            
            # Add notes if provided (assuming there's a notes field)
            if hasattr(staff, 'notes') and notes:
                staff.notes = notes
            
            db.commit()
            db.refresh(staff)
            result = self.serialize_model(staff)
            db.close()
            
            # Log the interaction
            self.log_interaction(
                query=f"Update staff {staff_id} status from {old_status} to {status}",
                response=f"Staff status updated successfully",
                tool_used="update_staff_status"
            )
            
            return {"success": True, "message": "Staff status updated successfully", "data": result}
        except Exception as e:
            return {"success": False, "message": f"Failed to update staff status: {str(e)}"}

    def delete_staff(self, staff_id: str) -> Dict[str, Any]:
        """Delete a staff record."""
        if not DATABASE_AVAILABLE:
            return {"success": False, "message": "Database not available"}
        
        try:
            db = self.get_db_session()
            staff = db.query(Staff).filter(Staff.id == uuid.UUID(staff_id)).first()
            
            if not staff:
                db.close()
                return {"success": False, "message": "Staff member not found"}
            
            employee_id = staff.employee_id  # Store for logging
            db.delete(staff)
            db.commit()
            db.close()
            
            # Log the interaction
            self.log_interaction(
                query=f"Delete staff: {staff_id}",
                response=f"Staff {employee_id} deleted successfully",
                tool_used="delete_staff"
            )
            
            return {"success": True, "message": "Staff deleted successfully"}
        except Exception as e:
            return {"success": False, "message": f"Failed to delete staff: {str(e)}"}
