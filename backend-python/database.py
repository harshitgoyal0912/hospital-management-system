"""Database configuration and connection management for PostgreSQL."""

import os
import sys
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure") and sys.stdout:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure") and sys.stderr:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
import uuid
from datetime import datetime, date
from typing import List, Optional
from sqlalchemy import create_engine, text, Column, Integer, String, DateTime, Date, Boolean, Text, DECIMAL, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from sqlalchemy.sql import func
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/hospital_management")

# SQLAlchemy setup
Base = declarative_base()
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# --- New imports for meeting & legacy models registration ---
# Note: Meeting models will be imported when needed to avoid circular imports

# Import discharge report models at module level
try:
    # We'll import these at the end to avoid circular imports
    pass
except ImportError:
    pass

# Database Models

class Meeting(Base):
    """Meeting table model."""
    __tablename__ = "meetings"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(100), nullable=False)
    description = Column(Text)
    meeting_datetime = Column(DateTime, nullable=False)
    duration_minutes = Column(Integer)
    location = Column(String(100))
    google_meet_link = Column(String(255))
    google_event_id = Column(String(255))
    google_meet_room_code = Column(String(50))
    organizer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    department_id = Column(UUID(as_uuid=True), ForeignKey("departments.id"))
    meeting_type = Column(String(50))
    status = Column(String(50))
    priority = Column(String(20))
    email_sent = Column(Boolean)
    calendar_invites_sent = Column(Boolean)
    reminder_sent = Column(Boolean)
    agenda = Column(Text)
    meeting_notes = Column(Text)
    action_items = Column(Text)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    cancelled_at = Column(DateTime)

    # Relationships
    organizer = relationship("User", foreign_keys=[organizer_id])
    department = relationship("Department")
    participants = relationship("MeetingParticipant", back_populates="meeting")

class MeetingParticipant(Base):
    """Meeting participant table model."""
    __tablename__ = "meeting_participants"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    meeting_id = Column(UUID(as_uuid=True), ForeignKey("meetings.id"), nullable=False)
    staff_id = Column(UUID(as_uuid=True), ForeignKey("staff.id"), nullable=False)
    attendance_status = Column(String(50))
    response_datetime = Column(DateTime)
    join_datetime = Column(DateTime)
    leave_datetime = Column(DateTime)

    # Relationships
    meeting = relationship("Meeting", back_populates="participants")
    staff = relationship("Staff")

class User(Base):
    """User table model for authentication and basic user info."""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False)  # admin, doctor, nurse, manager, receptionist
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    phone = Column(String(20))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    staff = relationship("Staff", back_populates="user", uselist=False)
    inventory_transactions = relationship("InventoryTransaction", back_populates="performed_by_user")
    agent_interactions = relationship("AgentInteraction", back_populates="user")
    generated_discharge_reports = relationship("DischargeReport", foreign_keys="DischargeReport.generated_by", back_populates="generated_by_user")
    prescribed_supply_usage = relationship("PatientSupplyUsage", foreign_keys="PatientSupplyUsage.prescribed_by_id", back_populates="prescribed_by")
    administered_supply_usage = relationship("PatientSupplyUsage", foreign_keys="PatientSupplyUsage.administered_by_id", back_populates="administered_by")

class Department(Base):
    """Department table model."""
    __tablename__ = "departments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    head_doctor_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    floor_number = Column(Integer)
    phone = Column(String(20))
    email = Column(String(100))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    head_doctor = relationship("User", foreign_keys=[head_doctor_id])
    staff = relationship("Staff", back_populates="department")
    rooms = relationship("Room", back_populates="department")
    equipment = relationship("Equipment", back_populates="department")

class Patient(Base):
    """Patient table model."""
    __tablename__ = "patients"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_number = Column(String(20), unique=True, nullable=False)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    date_of_birth = Column(Date, nullable=False)
    gender = Column(String(10))  # male, female, other
    phone = Column(String(20))
    email = Column(String(100))
    address = Column(Text)
    emergency_contact_name = Column(String(100))
    emergency_contact_phone = Column(String(20))
    blood_type = Column(String(5))
    allergies = Column(Text)
    medical_history = Column(Text)
    status = Column(String(20), default="active")  # active, discharged, transferred, deceased
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    bed = relationship("Bed", back_populates="patient")
    medical_documents = relationship("MedicalDocument", back_populates="patient")
    extracted_medical_data = relationship("ExtractedMedicalData", back_populates="patient")
    discharge_reports = relationship("DischargeReport", back_populates="patient")
    supply_usage = relationship("PatientSupplyUsage", back_populates="patient")
    # Discharge report related relationships (will be available after models are imported)
    treatments = relationship("TreatmentRecord", back_populates="patient", lazy="dynamic")
    equipment_usage = relationship("EquipmentUsage", back_populates="patient", lazy="dynamic")
    staff_assignments = relationship("StaffAssignment", back_populates="patient", lazy="dynamic")

class Room(Base):
    """Room table model."""
    __tablename__ = "rooms"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    room_number = Column(String(10), unique=True, nullable=False)
    floor_number = Column(Integer)  # Match the actual database schema
    room_type = Column(String(20))  # Match database varchar(20)
    department_id = Column(UUID(as_uuid=True), ForeignKey("departments.id"))
    capacity = Column(Integer, default=1)  # Add capacity field to match database
    status = Column(String(20), default="available")  # available, occupied, maintenance, cleaning
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    department = relationship("Department", back_populates="rooms")
    beds = relationship("Bed", back_populates="room")


class Bed(Base):
    """Bed table model."""
    __tablename__ = "beds"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bed_number = Column(String(10), nullable=False)
    room_id = Column(UUID(as_uuid=True), ForeignKey("rooms.id"), nullable=False)
    bed_type = Column(String(50))  # standard, icu, emergency
    status = Column(String(20), default="available")  # available, occupied, maintenance
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"))
    admission_date = Column(DateTime)
    discharge_date = Column(DateTime)
    notes = Column(Text)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    room = relationship("Room", back_populates="beds")
    patient = relationship("Patient", back_populates="bed")
    discharge_reports = relationship("DischargeReport", back_populates="bed")
    supply_usage = relationship("PatientSupplyUsage", back_populates="bed")


class Staff(Base):
    """Staff table model."""
    __tablename__ = "staff"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    employee_id = Column(String(20), unique=True, nullable=False)
    department_id = Column(UUID(as_uuid=True), ForeignKey("departments.id"), nullable=False)
    position = Column(String(50), nullable=False)
    specialization = Column(String(100))
    license_number = Column(String(50))
    hire_date = Column(Date, nullable=False)
    salary = Column(DECIMAL(10, 2))
    shift_pattern = Column(String(20))  # day, night, rotating
    status = Column(String(20), default="active")  # active, inactive, on_leave
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="staff")
    department = relationship("Department", back_populates="staff")

class EquipmentCategory(Base):
    """Equipment category table model."""
    __tablename__ = "equipment_categories"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=func.now())

    # Relationships
    equipment = relationship("Equipment", back_populates="category")

class Equipment(Base):
    """Equipment table model."""
    __tablename__ = "equipment"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    equipment_id = Column(String(20), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    category_id = Column(UUID(as_uuid=True), ForeignKey("equipment_categories.id"), nullable=False)
    model = Column(String(100))
    manufacturer = Column(String(100))
    serial_number = Column(String(100))
    purchase_date = Column(Date)
    warranty_expiry = Column(Date)
    location = Column(String(100))
    department_id = Column(UUID(as_uuid=True), ForeignKey("departments.id"))
    status = Column(String(20), default="available")  # available, in_use, maintenance, out_of_order
    last_maintenance = Column(Date)
    next_maintenance = Column(Date)
    cost = Column(DECIMAL(10, 2))
    notes = Column(Text)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    category = relationship("EquipmentCategory", back_populates="equipment")
    department = relationship("Department", back_populates="equipment")

class SupplyCategory(Base):
    """Supply category table model."""
    __tablename__ = "supply_categories"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=func.now())

    # Relationships
    supplies = relationship("Supply", back_populates="category")

class Supply(Base):
    """Supply table model."""
    __tablename__ = "supplies"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    item_code = Column(String(20), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    category_id = Column(UUID(as_uuid=True), ForeignKey("supply_categories.id"), nullable=False)
    description = Column(Text)
    unit_of_measure = Column(String(20), nullable=False)
    minimum_stock_level = Column(Integer, default=0)
    maximum_stock_level = Column(Integer)
    current_stock = Column(Integer, default=0)
    unit_cost = Column(DECIMAL(8, 2))
    supplier = Column(String(100))
    expiry_date = Column(Date)
    location = Column(String(100))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    category = relationship("SupplyCategory", back_populates="supplies")
    transactions = relationship("InventoryTransaction", back_populates="supply")
    patient_usage = relationship("PatientSupplyUsage", back_populates="supply")

class InventoryTransaction(Base):
    """Inventory transaction table model."""
    __tablename__ = "inventory_transactions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    supply_id = Column(UUID(as_uuid=True), ForeignKey("supplies.id"), nullable=False)
    transaction_type = Column(String(20), nullable=False)  # in, out, adjustment
    quantity = Column(Integer, nullable=False)
    unit_cost = Column(DECIMAL(8, 2))
    total_cost = Column(DECIMAL(10, 2))
    reference_number = Column(String(50))
    notes = Column(Text)
    performed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    transaction_date = Column(DateTime, default=func.now())

    # Relationships
    supply = relationship("Supply", back_populates="transactions")
    performed_by_user = relationship("User", back_populates="inventory_transactions")

class AgentInteraction(Base):
    """Agent interaction table model."""
    __tablename__ = "agent_interactions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_type = Column(String(50), nullable=False)  # bed_management, equipment_tracker, staff_allocation, supply_inventory
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    query = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    action_taken = Column(String(100))
    confidence_score = Column(DECIMAL(3, 2))
    execution_time_ms = Column(Integer)
    created_at = Column(DateTime, default=func.now())

    # Relationships
    user = relationship("User", back_populates="agent_interactions")



class MedicalDocument(Base):
    """Medical documents table model for storing uploaded medical files."""
    __tablename__ = "medical_documents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)
    document_type = Column(String(50), nullable=False)  # prescription, lab_result, imaging, discharge_summary, etc.
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)  # Local path or S3 URL
    file_size = Column(Integer)  # File size in bytes
    mime_type = Column(String(100))  # File MIME type
    upload_date = Column(DateTime, default=func.now())
    extracted_text = Column(Text)  # OCR extracted text
    processing_status = Column(String(20), default='pending')  # pending, processing, completed, failed
    extracted_metadata = Column(Text)  # JSON string of extracted medical data
    confidence_score = Column(DECIMAL(3, 2))  # AI extraction confidence (0.00-1.00)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    patient = relationship("Patient", back_populates="medical_documents")
    extracted_medical_data = relationship("ExtractedMedicalData", back_populates="document")

class ExtractedMedicalData(Base):
    """Structured medical data extracted from documents."""
    __tablename__ = "extracted_medical_data"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("medical_documents.id"), nullable=False)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)
    data_type = Column(String(50), nullable=False)  # medication, condition, procedure, allergy, vital_sign
    
    # Medical entity fields
    entity_name = Column(String(200), nullable=False)  # Name of medication, condition, etc.
    entity_value = Column(String(200))  # Dosage, measurement value, etc.
    entity_unit = Column(String(50))  # mg, ml, mmHg, etc.
    
    # Temporal information
    date_prescribed = Column(Date)
    date_recorded = Column(Date)
    date_effective = Column(Date)
    
    # Context information
    doctor_name = Column(String(100))
    hospital_name = Column(String(100))
    department_name = Column(String(100))
    
    # AI extraction metadata
    extraction_confidence = Column(DECIMAL(3, 2))  # Confidence score for this extraction
    extraction_method = Column(String(50))  # OCR, AI_PARSING, MANUAL
    verified = Column(Boolean, default=False)  # Human verified
    
    # Additional context
    notes = Column(Text)  # Additional notes or context
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    document = relationship("MedicalDocument", back_populates="extracted_medical_data")
    patient = relationship("Patient", back_populates="extracted_medical_data")

class DocumentEmbedding(Base):
    """Vector embeddings for RAG system."""
    __tablename__ = "document_embeddings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("medical_documents.id"), nullable=False)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)
    chunk_text = Column(Text, nullable=False)  # Text chunk for embedding
    chunk_index = Column(Integer, nullable=False)  # Order of chunk in document
    embedding_vector = Column(Text)  # JSON serialized embedding vector
    created_at = Column(DateTime, default=func.now())

    # Relationships
    document = relationship("MedicalDocument")
    patient = relationship("Patient")

# Legacy User model for backward compatibility
class LegacyUser(Base):
    """Legacy User table model for backward compatibility."""
    __tablename__ = "legacy_users"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    address = Column(String, nullable=False)
    phone = Column(String, nullable=False)

class DischargeReport(Base):
    """Comprehensive discharge report table model."""
    __tablename__ = "discharge_reports"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)
    bed_id = Column(UUID(as_uuid=True), ForeignKey("beds.id"), nullable=False)
    generated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    report_number = Column(String(50), unique=True, nullable=False)
    admission_date = Column(DateTime, nullable=False)
    discharge_date = Column(DateTime, nullable=False)
    length_of_stay_days = Column(Integer)
    
    # Report sections as JSON
    patient_summary = Column(Text)  # JSON
    treatment_summary = Column(Text)  # JSON
    equipment_summary = Column(Text)  # JSON
    staff_summary = Column(Text)  # JSON
    medications = Column(Text)  # JSON
    supply_usage = Column(Text)  # JSON - New field for supply/medication usage
    procedures = Column(Text)  # JSON
    discharge_instructions = Column(Text)
    follow_up_required = Column(Text)
    
    # Discharge conditions
    discharge_condition = Column(String(50))  # improved, stable, critical, deceased
    discharge_destination = Column(String(100))  # home, transfer, rehabilitation, nursing_home
    
    created_at = Column(DateTime, default=func.now())

    # Relationships
    patient = relationship("Patient", back_populates="discharge_reports")
    bed = relationship("Bed")
    generated_by_user = relationship("User", foreign_keys=[generated_by])

# Patient Supply Usage Tracking Models

class PatientSupplyUsage(Base):
    """Track supply/medication usage per patient for discharge reporting."""
    __tablename__ = "patient_supply_usage"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)
    supply_id = Column(UUID(as_uuid=True), ForeignKey("supplies.id"), nullable=False)
    
    # Usage details
    quantity_used = Column(Integer, nullable=False)
    unit_cost = Column(DECIMAL(8, 2))  # Cost per unit at time of usage
    total_cost = Column(DECIMAL(10, 2))  # Total cost for this usage
    
    # Medical context
    prescribed_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))  # Doctor who prescribed
    administered_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))  # Staff who administered
    bed_id = Column(UUID(as_uuid=True), ForeignKey("beds.id"))  # Where administered
    
    # Clinical details
    dosage = Column(String(100))  # e.g., "500mg", "2 tablets"
    frequency = Column(String(100))  # e.g., "twice daily", "as needed"
    administration_route = Column(String(50))  # oral, IV, injection, topical
    indication = Column(String(200))  # Why was this prescribed/used
    
    # Timing
    prescribed_date = Column(DateTime, nullable=False)
    administration_date = Column(DateTime)
    start_date = Column(Date)  # Treatment start
    end_date = Column(Date)    # Treatment end
    
    # Status and notes
    status = Column(String(20), default="prescribed")  # prescribed, administered, completed, discontinued
    effectiveness = Column(String(20))  # effective, partial, ineffective, unknown
    side_effects = Column(Text)  # Any reported side effects
    notes = Column(Text)
    
    # Billing integration
    billed = Column(Boolean, default=False)
    insurance_covered = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    patient = relationship("Patient", back_populates="supply_usage")
    supply = relationship("Supply", back_populates="patient_usage")
    prescribed_by = relationship("User", foreign_keys=[prescribed_by_id], back_populates="prescribed_supply_usage")
    administered_by = relationship("User", foreign_keys=[administered_by_id], back_populates="administered_supply_usage")
    bed = relationship("Bed", back_populates="supply_usage")

# Bed Turnover Management Models

class BedTurnover(Base):
    """Bed turnover process tracking model."""
    __tablename__ = "bed_turnovers"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bed_id = Column(UUID(as_uuid=True), ForeignKey("beds.id"), nullable=False)
    previous_patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"))
    next_patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"))
    
    # Turnover process stages
    status = Column(String(20), default="initiated")  # initiated, cleaning, cleaning_complete, ready, assigned
    turnover_type = Column(String(20), default="standard")  # standard, deep_clean, maintenance
    
    # Time tracking
    discharge_time = Column(DateTime, nullable=False)
    cleaning_start_time = Column(DateTime)
    cleaning_end_time = Column(DateTime)
    ready_time = Column(DateTime)
    next_assignment_time = Column(DateTime)
    
    # Estimated times (in minutes)
    estimated_cleaning_duration = Column(Integer, default=45)  # 45 minutes standard
    
    # Staff assignments
    assigned_cleaner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    assigned_inspector_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    # Equipment management
    equipment_requiring_cleaning = Column(Text)  # JSON array of equipment IDs
    equipment_to_be_returned = Column(Text)  # JSON array of equipment IDs
    equipment_cleaning_complete = Column(Boolean, default=False)
    
    # Quality control
    cleaning_checklist = Column(Text)  # JSON checklist
    inspection_passed = Column(Boolean, default=False)
    inspector_notes = Column(Text)
    
    # Priority and notes
    priority_level = Column(String(10), default="normal")  # urgent, high, normal, low
    notes = Column(Text)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    bed = relationship("Bed")
    previous_patient = relationship("Patient", foreign_keys=[previous_patient_id])
    next_patient = relationship("Patient", foreign_keys=[next_patient_id])
    assigned_cleaner = relationship("User", foreign_keys=[assigned_cleaner_id])
    assigned_inspector = relationship("User", foreign_keys=[assigned_inspector_id])

class PatientQueue(Base):
    """Patient queue management for bed assignments."""
    __tablename__ = "patient_queue"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)
    department_id = Column(UUID(as_uuid=True), ForeignKey("departments.id"), nullable=False)
    
    # Queue details
    queue_position = Column(Integer, nullable=False)
    bed_type_required = Column(String(20))  # ICU, General, Private, etc.
    priority_level = Column(String(10), default="normal")  # urgent, high, normal, low
    admission_type = Column(String(20))  # emergency, scheduled, transfer
    
    # Time tracking
    queue_entry_time = Column(DateTime, default=func.now())
    estimated_wait_time = Column(Integer)  # minutes
    target_bed_id = Column(UUID(as_uuid=True), ForeignKey("beds.id"))  # Specific bed if assigned
    
    # Patient condition and requirements
    medical_condition = Column(String(100))
    special_requirements = Column(Text)  # JSON for equipment, isolation, etc.
    doctor_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    # Status tracking
    status = Column(String(20), default="waiting")  # waiting, assigned, admitted, cancelled
    assigned_bed_id = Column(UUID(as_uuid=True), ForeignKey("beds.id"))
    assignment_time = Column(DateTime)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    patient = relationship("Patient")
    department = relationship("Department")
    target_bed = relationship("Bed", foreign_keys=[target_bed_id])
    assigned_bed = relationship("Bed", foreign_keys=[assigned_bed_id])
    doctor = relationship("User", foreign_keys=[doctor_id])

class EquipmentTurnover(Base):
    """Track equipment usage during bed turnovers."""
    __tablename__ = "equipment_turnovers"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bed_turnover_id = Column(UUID(as_uuid=True), ForeignKey("bed_turnovers.id"), nullable=False)
    equipment_id = Column(UUID(as_uuid=True), ForeignKey("equipment.id"), nullable=False)
    
    # Equipment status during turnover
    status = Column(String(20), default="in_use")  # in_use, needs_cleaning, cleaning, clean, returned
    cleaning_required = Column(Boolean, default=True)
    cleaning_type = Column(String(20))  # surface, deep, sterilization
    
    # Time tracking
    release_time = Column(DateTime)
    cleaning_start_time = Column(DateTime)
    cleaning_end_time = Column(DateTime)
    return_time = Column(DateTime)
    
    # Staff assignments
    released_by_staff_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    cleaned_by_staff_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    # Quality control
    cleaning_checklist = Column(Text)  # JSON
    inspection_passed = Column(Boolean, default=False)
    notes = Column(Text)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    bed_turnover = relationship("BedTurnover")
    equipment = relationship("Equipment")
    released_by_staff = relationship("User", foreign_keys=[released_by_staff_id])
    cleaned_by_staff = relationship("User", foreign_keys=[cleaned_by_staff_id])

# === MISSING MODELS FOR COMPLETE TABLE COVERAGE ===

class BedCleaningTask(Base):
    """Individual cleaning tasks for bed turnover."""
    __tablename__ = "bed_cleaning_tasks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    turnover_log_id = Column(UUID(as_uuid=True), ForeignKey("bed_turnover_logs.id"), nullable=False)
    task_name = Column(String(100), nullable=False)
    task_description = Column(Text)
    estimated_duration = Column(Integer)  # minutes
    actual_duration = Column(Integer)  # minutes
    status = Column(String(20))  # pending, in_progress, completed, failed
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    assigned_staff_id = Column(UUID(as_uuid=True), ForeignKey("staff.id"))
    quality_check_passed = Column(Boolean)
    notes = Column(Text)
    
    # Relationships
    turnover_log = relationship("BedTurnoverLog")
    assigned_staff = relationship("Staff")

class BedEquipmentAssignment(Base):
    """Track equipment assignments to beds."""
    __tablename__ = "bed_equipment_assignments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bed_id = Column(UUID(as_uuid=True), ForeignKey("beds.id"), nullable=False)
    equipment_id = Column(UUID(as_uuid=True), ForeignKey("equipment.id"), nullable=False)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"))
    assigned_at = Column(DateTime)
    released_at = Column(DateTime)
    status = Column(String(20))  # assigned, in_use, released, maintenance
    assigned_by_staff_id = Column(UUID(as_uuid=True), ForeignKey("staff.id"))
    notes = Column(Text)
    
    # Relationships
    bed = relationship("Bed")
    equipment = relationship("Equipment")
    patient = relationship("Patient")
    assigned_by_staff = relationship("Staff")

class BedStaffAssignment(Base):
    """Track staff assignments to beds."""
    __tablename__ = "bed_staff_assignments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bed_id = Column(UUID(as_uuid=True), ForeignKey("beds.id"), nullable=False)
    staff_id = Column(UUID(as_uuid=True), ForeignKey("staff.id"), nullable=False)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"))
    assignment_type = Column(String(50))  # primary_nurse, secondary_nurse, doctor, etc.
    assigned_at = Column(DateTime)
    released_at = Column(DateTime)
    status = Column(String(20))  # active, completed, transferred
    shift_type = Column(String(20))  # day, night, evening
    
    # Relationships
    bed = relationship("Bed")
    staff = relationship("Staff")
    patient = relationship("Patient")

class BedTurnoverLog(Base):
    """Detailed bed turnover process tracking."""
    __tablename__ = "bed_turnover_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bed_id = Column(UUID(as_uuid=True), ForeignKey("beds.id"), nullable=False)
    previous_patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"))
    next_patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"))
    
    # Process timestamps
    discharge_started_at = Column(DateTime, nullable=False)
    discharge_completed_at = Column(DateTime)
    cleaning_started_at = Column(DateTime)
    cleaning_expected_duration = Column(Integer)  # minutes
    cleaning_estimated_completion = Column(DateTime)
    cleaning_actual_completion = Column(DateTime)
    cleaning_status = Column(String(30))  # pending, in_progress, completed, failed
    cleaning_assigned_staff_id = Column(UUID(as_uuid=True), ForeignKey("staff.id"))
    cleaning_notes = Column(Text)
    
    # Resource management
    equipment_released_at = Column(DateTime)
    equipment_reassigned_at = Column(DateTime)
    staff_released_at = Column(DateTime)
    staff_reassigned_at = Column(DateTime)
    next_patient_assigned_at = Column(DateTime)
    turnover_completed_at = Column(DateTime)
    
    # Tracking and metrics
    status = Column(String(30))  # initiated, in_progress, completed, delayed
    total_turnover_time = Column(Integer)  # minutes
    delays = Column(Text)  # JSON array of delay reasons
    priority = Column(String(20))  # low, normal, high, urgent
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    bed = relationship("Bed")
    previous_patient = relationship("Patient", foreign_keys=[previous_patient_id])
    next_patient = relationship("Patient", foreign_keys=[next_patient_id])
    cleaning_assigned_staff = relationship("Staff", foreign_keys=[cleaning_assigned_staff_id])
    cleaning_tasks = relationship("BedCleaningTask", back_populates="turnover_log")

class EquipmentUsage(Base):
    """Track equipment usage by patients."""
    __tablename__ = "equipment_usage"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)
    equipment_id = Column(UUID(as_uuid=True), ForeignKey("equipment.id"), nullable=False)
    staff_id = Column(UUID(as_uuid=True), ForeignKey("staff.id"), nullable=False)
    bed_id = Column(UUID(as_uuid=True), ForeignKey("beds.id"))
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime)
    duration_minutes = Column(Integer)
    purpose = Column(String(100))  # monitoring, treatment, diagnostic
    settings = Column(Text)  # JSON of equipment settings
    readings = Column(Text)  # JSON of readings/measurements
    status = Column(String(20))  # active, completed, interrupted
    notes = Column(Text)
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    patient = relationship("Patient")
    equipment = relationship("Equipment")
    staff = relationship("Staff")
    bed = relationship("Bed")

class StaffAssignment(Base):
    """Track staff assignments to patients."""
    __tablename__ = "staff_assignments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)
    staff_id = Column(UUID(as_uuid=True), ForeignKey("staff.id"), nullable=False)
    bed_id = Column(UUID(as_uuid=True), ForeignKey("beds.id"))
    assignment_type = Column(String(50), nullable=False)  # primary_care, secondary_care, consultation
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime)
    shift = Column(String(20))  # day, night, evening
    responsibilities = Column(Text)
    notes = Column(Text)
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    patient = relationship("Patient")
    staff = relationship("Staff")
    bed = relationship("Bed")

class StaffInteraction(Base):
    """Track staff interactions with patients."""
    __tablename__ = "staff_interactions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)  # Using Integer as per DB schema
    patient_id = Column(String(50), nullable=False)  # Using String as per DB schema
    staff_name = Column(String(100), nullable=False)
    staff_role = Column(String(50))
    interaction_type = Column(String(50))  # consultation, treatment, monitoring, etc.
    description = Column(Text)
    interaction_date = Column(Date)
    duration_minutes = Column(Integer)
    created_at = Column(DateTime, default=func.now())

class StaffMeetingParticipant(Base):
    """Link staff to staff meetings."""
    __tablename__ = "staff_meeting_participants"
    
    meeting_id = Column(UUID(as_uuid=True), ForeignKey("staff_meetings.id"), primary_key=True)
    staff_id = Column(UUID(as_uuid=True), ForeignKey("staff.id"), primary_key=True)
    
    # Relationships
    meeting = relationship("StaffMeeting", back_populates="participants")
    staff = relationship("Staff")

class StaffMeeting(Base):
    """Staff meetings management."""
    __tablename__ = "staff_meetings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(200), nullable=False)
    description = Column(String(500))
    meeting_time = Column(DateTime, nullable=False)
    duration_minutes = Column(Integer)
    location = Column(String(100))
    organizer_id = Column(UUID(as_uuid=True), ForeignKey("staff.id"), nullable=False)
    department_id = Column(UUID(as_uuid=True), ForeignKey("departments.id"))
    status = Column(String(30))  # scheduled, in_progress, completed, cancelled
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    organizer = relationship("Staff", foreign_keys=[organizer_id])
    department = relationship("Department")
    participants = relationship("StaffMeetingParticipant", back_populates="meeting")

class TreatmentRecord(Base):
    """Patient treatment records."""
    __tablename__ = "treatment_records"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)
    doctor_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    bed_id = Column(UUID(as_uuid=True), ForeignKey("beds.id"))
    treatment_type = Column(String(50), nullable=False)  # medication, procedure, therapy
    treatment_name = Column(String(100), nullable=False)
    description = Column(Text)
    dosage = Column(String(50))
    frequency = Column(String(50))  # daily, twice_daily, weekly, etc.
    duration = Column(String(50))  # 7_days, 2_weeks, ongoing
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime)
    status = Column(String(30))  # active, completed, discontinued
    notes = Column(Text)
    side_effects = Column(Text)
    effectiveness = Column(String(30))  # excellent, good, fair, poor
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    patient = relationship("Patient")
    doctor = relationship("User", foreign_keys=[doctor_id])
    bed = relationship("Bed")

def create_tables(force: bool = False):
    """Create all tables in the database."""
    try:
        if force:
            # Drop all tables first to avoid conflicts
            # Use CASCADE to handle dependencies
            with engine.connect() as conn:
                conn.execute(text("DROP SCHEMA public CASCADE"))
                conn.execute(text("CREATE SCHEMA public"))
                conn.execute(text("GRANT ALL ON SCHEMA public TO postgres"))
                conn.execute(text("GRANT ALL ON SCHEMA public TO public"))
                conn.commit()
            print("Dropped existing schema and recreated")
        
        # Create all tables fresh
        Base.metadata.create_all(bind=engine)
        print("Created all tables successfully")
    except Exception as e:
        print(f"Error creating tables: {e}")
        raise

def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Helper for session retrieval expected by some tooling files ---
def get_db_session():
    """Return a new database session (convenience wrapper)."""
    return SessionLocal()

def migrate_json_to_db():
    """Migrate existing users.json data to PostgreSQL database."""
    from pathlib import Path
    
    # Read existing JSON data
    json_file = Path(__file__).parent / "data" / "users.json"
    if not json_file.exists():
        print("No users.json file found to migrate")
        return
    
    with open(json_file, 'r') as f:
        users_data = json.load(f)
    
    # Create database session
    db = SessionLocal()
    try:
        # Check if users already exist
        existing_count = db.query(LegacyUser).count()
        if existing_count > 0:
            print(f"Database already has {existing_count} legacy users. Skipping migration.")
            return
        
        # Insert users into database
        for user_data in users_data:
            # Don't set the ID, let PostgreSQL auto-generate it
            user = LegacyUser(
                name=user_data["name"],
                email=user_data["email"],
                address=user_data["address"],
                phone=user_data["phone"]
            )
            db.add(user)
        
        db.commit()
        print(f"Successfully migrated {len(users_data)} users to PostgreSQL database")
        
    except Exception as e:
        db.rollback()
        print(f"Error migrating data: {e}")
    finally:
        db.close()

def test_connection():
    """Test database connection."""
    try:
        db = SessionLocal()
        result = db.execute(text("SELECT 1"))
        db.close()
        print("✅ PostgreSQL connection successful!")
        return True
    except Exception as e:
        print(f"❌ PostgreSQL connection failed: {e}")
        return False

if __name__ == "__main__":
    # Test connection and create tables
    print("Testing PostgreSQL connection...")
    if test_connection():
        print("Creating tables...")
        create_tables()
        print("Migrating data from JSON...")
        migrate_json_to_db()
        print("Database setup complete!")

# Import additional discharge report models after all base models are defined
# This prevents circular import issues
try:
    # Don't import TreatmentRecord, EquipmentUsage, StaffAssignment as they're now defined in this file
    # from discharge_report_models import TreatmentRecord, EquipmentUsage, StaffAssignment
    pass
    # Re-export for convenience
    __all__ = [
        'Base', 'engine', 'SessionLocal', 'get_db_session',
        'User', 'Patient', 'Department', 'Room', 'Bed', 'Staff', 'Appointment', 
        'Equipment', 'EquipmentCategory', 'Supply', 'SupplyCategory', 'InventoryTransaction', 
        'AgentInteraction', 'DischargeReport', 'BedTurnover', 'PatientQueue', 'EquipmentTurnover',
        'Meeting', 'MeetingParticipant', 'MedicalDocument', 'ExtractedMedicalData', 'DocumentEmbedding',
        'LegacyUser',
        # New missing models
        'BedCleaningTask', 'BedEquipmentAssignment', 'BedStaffAssignment', 'BedTurnoverLog',
        'EquipmentUsage', 'StaffAssignment', 'StaffInteraction', 'StaffMeetingParticipant',
        'StaffMeeting', 'TreatmentRecord'
    ]
except ImportError as e:
    # Discharge models not available - continue without them
    __all__ = [
        'Base', 'engine', 'SessionLocal', 'get_db_session',
        'User', 'Patient', 'Department', 'Room', 'Bed', 'Staff', 'Appointment', 
        'Equipment', 'EquipmentCategory', 'Supply', 'SupplyCategory', 'InventoryTransaction', 
        'AgentInteraction', 'DischargeReport', 'BedTurnover', 'PatientQueue', 'EquipmentTurnover',
        'Meeting', 'MeetingParticipant', 'MedicalDocument', 'ExtractedMedicalData', 'DocumentEmbedding',
        'LegacyUser',
        # New missing models
        'BedCleaningTask', 'BedEquipmentAssignment', 'BedStaffAssignment', 'BedTurnoverLog',
        'EquipmentUsage', 'StaffAssignment', 'StaffInteraction', 'StaffMeetingParticipant',
        'StaffMeeting', 'TreatmentRecord'
    ]
