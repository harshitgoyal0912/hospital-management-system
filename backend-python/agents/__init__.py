"""
Multi-Agent System for Hospital Management
Contains specialized agents for different hospital operations
"""

from .base_agent import BaseAgent
from .user_agent import UserAgent
from .department_agent import DepartmentAgent
from .patient_agent import PatientAgent
from .room_bed_agent import RoomBedAgent
from .staff_agent import StaffAgent
from .equipment_agent import EquipmentAgent
from .inventory_agent import InventoryAgent
from .orchestrator_agent import OrchestratorAgent

__all__ = [
    'BaseAgent',
    'UserAgent',
    'DepartmentAgent', 
    'PatientAgent',
    'RoomBedAgent',
    'StaffAgent',
    'EquipmentAgent',
    'InventoryAgent',
    'OrchestratorAgent'
]
