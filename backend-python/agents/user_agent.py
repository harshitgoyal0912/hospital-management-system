"""User Management Agent - Handles all user-related operations"""

import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from .base_agent import BaseAgent

try:
    from database import User, SessionLocal
    DATABASE_AVAILABLE = True
except ImportError:
    DATABASE_AVAILABLE = False


class UserAgent(BaseAgent):
    """Agent specialized in user management operations"""
    
    def __init__(self):
        super().__init__("User Management Agent", "user_agent")
    
    def get_tools(self) -> List[str]:
        """Return list of user management tools"""
        return [
            "create_user",
            "get_user_by_id", 
            "list_users",
            "update_user",
            "delete_user",
            "create_legacy_user",
            "list_legacy_users"
        ]
    
    def get_capabilities(self) -> List[str]:
        """Return list of user management capabilities"""
        return [
            "User registration and authentication",
            "User profile management",
            "Role-based access control",
            "User data retrieval and search",
            "Legacy user system integration"
        ]
    
    def create_user(self, username: str, email: str, password_hash: str, role: str, 
                    first_name: str, last_name: str, phone: str = None, is_active: bool = True) -> Dict[str, Any]:
        """Create a new user in the database."""
        if not DATABASE_AVAILABLE:
            return {"success": False, "message": "Database not available"}
        
        try:
            db = self.get_db_session()
            user = User(
                username=username,
                email=email,
                password_hash=password_hash,
                role=role,
                first_name=first_name,
                last_name=last_name,
                phone=phone,
                is_active=is_active
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            result = self.serialize_model(user)
            db.close()
            
            # Log the interaction
            self.log_interaction(
                query=f"Create user: {username}",
                response=f"User created successfully with ID: {result['id']}",
                tool_used="create_user"
            )
            
            return {"success": True, "message": "User created successfully", "data": result}
        except Exception as e:
            return {"success": False, "message": f"Failed to create user: {str(e)}"}

    def get_user_by_id(self, user_id: str) -> Dict[str, Any]:
        """Get a user by ID."""
        if not DATABASE_AVAILABLE:
            return {"error": "Database not available"}
        
        try:
            db = self.get_db_session()
            user = db.query(User).filter(User.id == uuid.UUID(user_id)).first()
            result = self.serialize_model(user) if user else None
            db.close()
            
            if result:
                # Log the interaction
                self.log_interaction(
                    query=f"Get user by ID: {user_id}",
                    response=f"User found: {result.get('username', 'N/A')}",
                    tool_used="get_user_by_id"
                )
                return {"data": result}
            else:
                return {"error": "User not found"}
        except Exception as e:
            return {"error": f"Failed to get user: {str(e)}"}

    def list_users(self) -> Dict[str, Any]:
        """List all users in the database - brief information only."""
        if not DATABASE_AVAILABLE:
            return {"error": "Database not available"}
        
        try:
            db = self.get_db_session()
            users = db.query(User).all()
            
            # Return only essential information for list views
            result = []
            for user in users:
                brief_info = {
                    "id": str(user.id),
                    "username": user.username,
                    "email": user.email,
                    "role": user.role,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "is_active": user.is_active
                }
                result.append(brief_info)
            
            db.close()
            
            # Log the interaction
            self.log_interaction(
                query="List all users",
                response=f"Found {len(result)} users",
                tool_used="list_users"
            )
            
            return {"data": result}
        except Exception as e:
            return {"error": f"Failed to list users: {str(e)}"}

    def update_user(self, user_id: str, username: str = None, email: str = None, role: str = None,
                   first_name: str = None, last_name: str = None, phone: str = None, 
                   is_active: bool = None) -> Dict[str, Any]:
        """Update user information."""
        if not DATABASE_AVAILABLE:
            return {"success": False, "message": "Database not available"}
        
        try:
            db = self.get_db_session()
            user = db.query(User).filter(User.id == uuid.UUID(user_id)).first()
            
            if not user:
                db.close()
                return {"success": False, "message": "User not found"}
            
            # Update provided fields
            update_fields = []
            if username is not None:
                user.username = username
                update_fields.append("username")
            if email is not None:
                user.email = email
                update_fields.append("email")
            if role is not None:
                user.role = role
                update_fields.append("role")
            if first_name is not None:
                user.first_name = first_name
                update_fields.append("first_name")
            if last_name is not None:
                user.last_name = last_name
                update_fields.append("last_name")
            if phone is not None:
                user.phone = phone
                update_fields.append("phone")
            if is_active is not None:
                user.is_active = is_active
                update_fields.append("is_active")
            
            db.commit()
            db.refresh(user)
            result = self.serialize_model(user)
            db.close()
            
            # Log the interaction
            self.log_interaction(
                query=f"Update user {user_id}: {', '.join(update_fields)}",
                response=f"User updated successfully",
                tool_used="update_user"
            )
            
            return {"success": True, "message": "User updated successfully", "data": result}
        except Exception as e:
            return {"success": False, "message": f"Failed to update user: {str(e)}"}

    def delete_user(self, user_id: str) -> Dict[str, Any]:
        """Delete a user from the database."""
        if not DATABASE_AVAILABLE:
            return {"success": False, "message": "Database not available"}
        
        try:
            db = self.get_db_session()
            user = db.query(User).filter(User.id == uuid.UUID(user_id)).first()
            
            if not user:
                db.close()
                return {"success": False, "message": "User not found"}
            
            username = user.username  # Store for logging
            db.delete(user)
            db.commit()
            db.close()
            
            # Log the interaction
            self.log_interaction(
                query=f"Delete user: {user_id}",
                response=f"User {username} deleted successfully",
                tool_used="delete_user"
            )
            
            return {"success": True, "message": "User deleted successfully"}
        except Exception as e:
            return {"success": False, "message": f"Failed to delete user: {str(e)}"}

    def create_legacy_user(self, name: str, email: str, address: str, phone: str) -> Dict[str, Any]:
        """Create a legacy user record."""
        if not DATABASE_AVAILABLE:
            return {"success": False, "message": "Database not available"}
        
        try:
            from database import LegacyUser
            db = self.get_db_session()
            legacy_user = LegacyUser(
                name=name,
                email=email,
                address=address,
                phone=phone
            )
            db.add(legacy_user)
            db.commit()
            db.refresh(legacy_user)
            result = self.serialize_model(legacy_user)
            db.close()
            
            # Log the interaction
            self.log_interaction(
                query=f"Create legacy user: {name}",
                response=f"Legacy user created with ID: {result['id']}",
                tool_used="create_legacy_user"
            )
            
            return {"success": True, "message": "Legacy user created successfully", "data": result}
        except Exception as e:
            return {"success": False, "message": f"Failed to create legacy user: {str(e)}"}

    def list_legacy_users(self) -> Dict[str, Any]:
        """List all legacy users - brief information only."""
        if not DATABASE_AVAILABLE:
            return {"error": "Database not available"}
        
        try:
            from database import LegacyUser
            db = self.get_db_session()
            legacy_users = db.query(LegacyUser).all()
            
            # Return only essential information for list views
            result = []
            for user in legacy_users:
                brief_info = {
                    "id": str(user.id),
                    "name": user.name,
                    "email": user.email,
                    "phone": user.phone,
                    "address": user.address
                }
                result.append(brief_info)
            
            db.close()
            
            # Log the interaction
            self.log_interaction(
                query="List all legacy users",
                response=f"Found {len(result)} legacy users",
                tool_used="list_legacy_users"
            )
            
            return {"data": result}
        except Exception as e:
            return {"error": f"Failed to list legacy users: {str(e)}"}
