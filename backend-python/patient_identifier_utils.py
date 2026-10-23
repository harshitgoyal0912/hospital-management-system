#!/usr/bin/env python3
"""Utility functions for patient identifier conversion."""

import uuid
from database import SessionLocal, Patient

def resolve_patient_identifier(identifier):
    """
    Resolve a patient identifier to UUID format.
    
    Args:
        identifier (str): Can be either a patient number (like "P1022") or UUID string
        
    Returns:
        tuple: (patient_uuid, patient_data) or (None, None) if not found
    """
    db = SessionLocal()
    try:
        patient = None
        
        # First, try to parse as UUID
        try:
            patient_uuid = uuid.UUID(identifier)
            patient = db.query(Patient).filter(Patient.id == patient_uuid).first()
        except ValueError:
            # If not a valid UUID, treat as patient number
            patient = db.query(Patient).filter(Patient.patient_number == identifier).first()
        
        if patient:
            return str(patient.id), {
                'id': str(patient.id),
                'patient_number': patient.patient_number,
                'name': f"{patient.first_name} {patient.last_name}",
                'first_name': patient.first_name,
                'last_name': patient.last_name,
                'email': patient.email,
                'phone': patient.phone
            }
        else:
            return None, None
            
    except Exception as e:
        print(f"Error resolving patient identifier: {e}")
        return None, None
    finally:
        db.close()

def get_patient_uuid_by_number(patient_number):
    """Get patient UUID by patient number."""
    patient_uuid, _ = resolve_patient_identifier(patient_number)
    return patient_uuid

def get_patient_info_by_identifier(identifier):
    """Get complete patient info by any identifier."""
    _, patient_data = resolve_patient_identifier(identifier)
    return patient_data

if __name__ == "__main__":
    # Test the functions
    print("🧪 Testing Patient Identifier Resolution")
    print("=" * 50)
    
    # Test with patient number
    test_patient_number = "P1022"
    patient_uuid, patient_data = resolve_patient_identifier(test_patient_number)
    
    if patient_uuid:
        print(f"✅ Resolved {test_patient_number}:")
        print(f"   UUID: {patient_uuid}")
        print(f"   Name: {patient_data['name']}")
        print(f"   Email: {patient_data['email']}")
        
        # Test with the UUID
        uuid_result, uuid_data = resolve_patient_identifier(patient_uuid)
        print(f"\n✅ Reverse lookup with UUID:")
        print(f"   Patient Number: {uuid_data['patient_number']}")
        print(f"   Name: {uuid_data['name']}")
    else:
        print(f"❌ Could not resolve {test_patient_number}")
