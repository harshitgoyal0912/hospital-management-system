"""Base Agent Class for Hospital Management System Multi-Agent Architecture"""

import uuid
from datetime import datetime, date
from decimal import Decimal
from typing import Any, Dict, List, Optional
from abc import ABC, abstractmethod
from sqlalchemy.orm import Session

# Import database modules
try:
    from database import (
        User, Department, Patient, Room, Bed, Staff, Equipment, EquipmentCategory,
        Supply, SupplyCategory, InventoryTransaction, AgentInteraction,
        LegacyUser, SessionLocal
    )
    DATABASE_AVAILABLE = True
except ImportError:
    DATABASE_AVAILABLE = False
    print("WARNING: Database modules not available. Install dependencies: pip install sqlalchemy psycopg2-binary")


class BaseAgent(ABC):
    """Base class for all hospital management agents"""
    
    def __init__(self, agent_name: str, agent_type: str):
        self.agent_name = agent_name
        self.agent_type = agent_type
        self.tools = []
        self.capabilities = []
        
    def get_db_session(self) -> Session:
        """Get database session."""
        return SessionLocal()
    
    def serialize_model(self, obj):
        """Convert SQLAlchemy model to dictionary."""
        if obj is None:
            return None
        
        result = {}
        for column in obj.__table__.columns:
            value = getattr(obj, column.name)
            if isinstance(value, uuid.UUID):
                result[column.name] = str(value)
            elif isinstance(value, (datetime, date)):
                result[column.name] = value.isoformat()
            elif isinstance(value, Decimal):
                result[column.name] = float(value)
            else:
                result[column.name] = value
        return result
    
    def log_interaction(self, query: str, response: str, user_id: str = None, 
                       tool_used: str = None, metadata: Dict = None) -> Dict[str, Any]:
        """Log agent interaction for auditing and analytics."""
        if not DATABASE_AVAILABLE:
            return {"success": False, "message": "Database not available"}
        
        try:
            db = self.get_db_session()
            interaction = AgentInteraction(
                agent_type=self.agent_type,
                query=query,
                response=response,
                user_id=uuid.UUID(user_id) if user_id else None,
                tool_used=tool_used,
                metadata=metadata or {}
            )
            db.add(interaction)
            db.commit()
            db.refresh(interaction)
            result = self.serialize_model(interaction)
            db.close()
            
            return {"success": True, "message": "Interaction logged", "data": result}
        except Exception as e:
            return {"success": False, "message": f"Failed to log interaction: {str(e)}"}
    
    @abstractmethod
    def get_tools(self) -> List[str]:
        """Return list of tools this agent provides"""
        pass
    
    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """Return list of capabilities this agent has"""
        pass
    
    def get_agent_info(self) -> Dict[str, Any]:
        """Get agent information"""
        return {
            "name": self.agent_name,
            "type": self.agent_type,
            "tools": self.get_tools(),
            "capabilities": self.get_capabilities(),
            "status": "active"
        }
    
    def can_handle_request(self, request_type: str, request_data: Dict = None) -> bool:
        """Check if this agent can handle the given request type"""
        return request_type.lower() in [tool.lower() for tool in self.get_tools()]
