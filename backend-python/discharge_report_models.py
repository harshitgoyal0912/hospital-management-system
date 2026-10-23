"""
Database extensions for Patient Discharge Report System
=====================================================

Import models from database.py to avoid duplicate table definitions.
"""

# Import the models from database.py instead of redefining them
from database import TreatmentRecord, EquipmentUsage, StaffAssignment

# Re-export the models so they can be imported from this module
__all__ = ['TreatmentRecord', 'EquipmentUsage', 'StaffAssignment']

# All discharge report functionality now uses the models from database.py
# This prevents the "Table already defined" error that was occurring
# when the same tables were defined in both database.py and this file.
