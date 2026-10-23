"""Test script to verify database setup and create sample data."""

import sys
import os
import uuid
import random
from datetime import datetime, date, timedelta
from decimal import Decimal

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import (
    test_connection, create_tables, SessionLocal,
    User, Department, Patient, Room, Bed, Staff, Equipment, EquipmentCategory,
    Supply, SupplyCategory, InventoryTransaction, AgentInteraction,
    LegacyUser, Meeting, MeetingParticipant, MedicalDocument, ExtractedMedicalData,
    DocumentEmbedding, DischargeReport, BedTurnover, PatientQueue, EquipmentTurnover,
    BedCleaningTask, BedEquipmentAssignment, BedStaffAssignment, BedTurnoverLog,
    EquipmentUsage, StaffAssignment, StaffInteraction, StaffMeetingParticipant,
    StaffMeeting, TreatmentRecord, PatientSupplyUsage
)

def create_sample_data():
    """Create comprehensive sample data for testing with proper foreign key relationships."""
    db = SessionLocal()
    
    try:
        print("Creating comprehensive sample data...")
        
        # === STEP 1: Create Users (No foreign key dependencies) ===
        print("1. Creating users...")
        
        # Admin Users
        admin_user = User(
            username="admin",
            email="admin@hospital.com",
            password_hash="hashed_password_123",
            role="admin",
            first_name="Admin",
            last_name="User",
            phone="555-0001"
        )
        
        admin_user_2 = User(
            username="admin.jones",
            email="admin.jones@hospital.com",
            password_hash="hashed_password_124",
            role="admin",
            first_name="Robert",
            last_name="Jones",
            phone="555-0051"
        )
        
        # Doctor Users
        doctor_user_1 = User(
            username="dr.smith",
            email="dr.smith@hospital.com",
            password_hash="hashed_password_456",
            role="doctor",
            first_name="John",
            last_name="Smith",
            phone="555-0002"
        )
        
        doctor_user_2 = User(
            username="dr.johnson",
            email="mrmshamil1786@gmail.com",
            password_hash="hashed_password_789",
            role="doctor",
            first_name="Mohamed",
            last_name="Shamil",
            phone="555-0003"
        )
        
        doctor_user_3 = User(
            username="dr.wilson",
            email="dr.wilson@hospital.com",
            password_hash="hashed_password_790",
            role="doctor",
            first_name="Emily",
            last_name="Wilson",
            phone="555-0052"
        )
        
        doctor_user_4 = User(
            username="dr.garcia",
            email="dr.garcia@hospital.com",
            password_hash="hashed_password_791",
            role="doctor",
            first_name="Carlos",
            last_name="Garcia",
            phone="555-0053"
        )
        
        doctor_user_5 = User(
            username="dr.patel",
            email="dr.patel@hospital.com",
            password_hash="hashed_password_792",
            role="doctor",
            first_name="Raj",
            last_name="Patel",
            phone="555-0054"
        )
        
        doctor_user_6 = User(
            username="dr.thompson",
            email="dr.thompson@hospital.com",
            password_hash="hashed_password_793",
            role="doctor",
            first_name="Lisa",
            last_name="Thompson",
            phone="555-0055"
        )
        
        doctor_user_7 = User(
            username="dr.anderson",
            email="dr.anderson@hospital.com",
            password_hash="hashed_password_794",
            role="doctor",
            first_name="Michael",
            last_name="Anderson",
            phone="555-0056"
        )
        
        doctor_user_8 = User(
            username="dr.lee",
            email="dr.lee@hospital.com",
            password_hash="hashed_password_795",
            role="doctor",
            first_name="Jennifer",
            last_name="Lee",
            phone="555-0057"
        )
        
        # Nurse Users
        nurse_user_1 = User(
            username="nurse.brown",
            email="nurse.brown@hospital.com",
            password_hash="hashed_password_101",
            role="nurse",
            first_name="Mary",
            last_name="Brown",
            phone="555-0004"
        )
        
        nurse_user_2 = User(
            username="nurse.davis",
            email="nurse.davis@hospital.com",
            password_hash="hashed_password_102",
            role="nurse",
            first_name="Sarah",
            last_name="Davis",
            phone="555-0005"
        )
        
        nurse_user_3 = User(
            username="nurse.martinez",
            email="nurse.martinez@hospital.com",
            password_hash="hashed_password_103",
            role="nurse",
            first_name="Ana",
            last_name="Martinez",
            phone="555-0058"
        )
        
        nurse_user_4 = User(
            username="nurse.white",
            email="nurse.white@hospital.com",
            password_hash="hashed_password_104",
            role="nurse",
            first_name="Jessica",
            last_name="White",
            phone="555-0059"
        )
        
        nurse_user_5 = User(
            username="nurse.kim",
            email="nurse.kim@hospital.com",
            password_hash="hashed_password_105",
            role="nurse",
            first_name="Susan",
            last_name="Kim",
            phone="555-0060"
        )
        
        nurse_user_6 = User(
            username="nurse.rodriguez",
            email="nurse.rodriguez@hospital.com",
            password_hash="hashed_password_106",
            role="nurse",
            first_name="Maria",
            last_name="Rodriguez",
            phone="555-0061"
        )
        
        nurse_user_7 = User(
            username="nurse.clark",
            email="nurse.clark@hospital.com",
            password_hash="hashed_password_107",
            role="nurse",
            first_name="Rebecca",
            last_name="Clark",
            phone="555-0062"
        )
        
        nurse_user_8 = User(
            username="nurse.taylor",
            email="nurse.taylor2@hospital.com",
            password_hash="hashed_password_108",
            role="nurse",
            first_name="Amanda",
            last_name="Taylor",
            phone="555-0063"
        )
        
        # Manager Users
        manager_user = User(
            username="manager.wilson",
            email="mn4385293@gmail.com",
            password_hash="hashed_password_103",
            role="manager",
            first_name="Mohamed",
            last_name="nazif",
            phone="555-0006"
        )
        
        manager_user_2 = User(
            username="manager.harris",
            email="manager.harris@hospital.com",
            password_hash="hashed_password_109",
            role="manager",
            first_name="David",
            last_name="Harris",
            phone="555-0064"
        )
        
        manager_user_3 = User(
            username="manager.lewis",
            email="manager.lewis@hospital.com",
            password_hash="hashed_password_110",
            role="manager",
            first_name="Linda",
            last_name="Lewis",
            phone="555-0065"
        )
        
        # Receptionist Users
        receptionist_user = User(
            username="receptionist.taylor",
            email="receptionist.taylor@hospital.com",
            password_hash="hashed_password_104",
            role="receptionist",
            first_name="Lisa",
            last_name="Taylor",
            phone="555-0007"
        )
        
        receptionist_user_2 = User(
            username="receptionist.moore",
            email="receptionist.moore@hospital.com",
            password_hash="hashed_password_111",
            role="receptionist",
            first_name="Karen",
            last_name="Moore",
            phone="555-0066"
        )
        
        receptionist_user_3 = User(
            username="receptionist.walker",
            email="receptionist.walker@hospital.com",
            password_hash="hashed_password_112",
            role="receptionist",
            first_name="Nancy",
            last_name="Walker",
            phone="555-0067"
        )
        
        # Staff Users (Cleaners, Technicians, etc.)
        cleaner_user = User(
            username="cleaner.martinez",
            email="cleaner.martinez@hospital.com",
            password_hash="hashed_password_105",
            role="staff",
            first_name="Carlos",
            last_name="Martinez",
            phone="555-0008"
        )
        
        cleaner_user_2 = User(
            username="cleaner.johnson",
            email="cleaner.johnson@hospital.com",
            password_hash="hashed_password_113",
            role="staff",
            first_name="James",
            last_name="Johnson",
            phone="555-0068"
        )
        
        technician_user_1 = User(
            username="tech.adams",
            email="tech.adams@hospital.com",
            password_hash="hashed_password_114",
            role="staff",
            first_name="Brian",
            last_name="Adams",
            phone="555-0069"
        )
        
        technician_user_2 = User(
            username="tech.baker",
            email="tech.baker@hospital.com",
            password_hash="hashed_password_115",
            role="staff",
            first_name="Michelle",
            last_name="Baker",
            phone="555-0070"
        )
        
        pharmacist_user_1 = User(
            username="pharmacist.green",
            email="pharmacist.green@hospital.com",
            password_hash="hashed_password_116",
            role="staff",
            first_name="Robert",
            last_name="Green",
            phone="555-0071"
        )
        
        pharmacist_user_2 = User(
            username="pharmacist.hall",
            email="pharmacist.hall@hospital.com",
            password_hash="hashed_password_117",
            role="staff",
            first_name="Patricia",
            last_name="Hall",
            phone="555-0072"
        )
        
        all_users = [
            admin_user, admin_user_2,
            doctor_user_1, doctor_user_2, doctor_user_3, doctor_user_4, doctor_user_5, doctor_user_6, doctor_user_7, doctor_user_8,
            nurse_user_1, nurse_user_2, nurse_user_3, nurse_user_4, nurse_user_5, nurse_user_6, nurse_user_7, nurse_user_8,
            manager_user, manager_user_2, manager_user_3,
            receptionist_user, receptionist_user_2, receptionist_user_3,
            cleaner_user, cleaner_user_2, technician_user_1, technician_user_2, pharmacist_user_1, pharmacist_user_2
        ]
        
        db.add_all(all_users)
        db.commit()
        for user in all_users:
            db.refresh(user)
        
        # === STEP 2: Create Departments (Depends on Users for head_doctor_id) ===
        print("2. Creating departments...")
        cardiology_dept = Department(
            name="Cardiology",
            description="Heart and cardiovascular care",
            head_doctor_id=doctor_user_1.id,
            floor_number=3,
            phone="555-1001",
            email="cardiology@hospital.com"
        )
        
        emergency_dept = Department(
            name="Emergency",
            description="Emergency medical care",
            head_doctor_id=doctor_user_2.id,
            floor_number=1,
            phone="555-1002",
            email="emergency@hospital.com"
        )
        
        icu_dept = Department(
            name="ICU",
            description="Intensive Care Unit",
            head_doctor_id=doctor_user_3.id,
            floor_number=4,
            phone="555-1003",
            email="icu@hospital.com"
        )
        
        surgery_dept = Department(
            name="Surgery",
            description="Surgical operations",
            head_doctor_id=doctor_user_4.id,
            floor_number=5,
            phone="555-1004",
            email="surgery@hospital.com"
        )
        
        orthopedics_dept = Department(
            name="Orthopedics",
            description="Bone and joint care",
            head_doctor_id=doctor_user_5.id,
            floor_number=6,
            phone="555-1005",
            email="orthopedics@hospital.com"
        )
        
        pediatrics_dept = Department(
            name="Pediatrics",
            description="Children's healthcare",
            head_doctor_id=doctor_user_6.id,
            floor_number=2,
            phone="555-1006",
            email="pediatrics@hospital.com"
        )
        
        neurology_dept = Department(
            name="Neurology",
            description="Brain and nervous system care",
            head_doctor_id=doctor_user_7.id,
            floor_number=7,
            phone="555-1007",
            email="neurology@hospital.com"
        )
        
        oncology_dept = Department(
            name="Oncology",
            description="Cancer treatment and care",
            head_doctor_id=doctor_user_8.id,
            floor_number=8,
            phone="555-1008",
            email="oncology@hospital.com"
        )
        
        psychiatry_dept = Department(
            name="Psychiatry",
            description="Mental health care",
            floor_number=9,
            phone="555-1009",
            email="psychiatry@hospital.com"
        )
        
        radiology_dept = Department(
            name="Radiology",
            description="Medical imaging and diagnostics",
            floor_number=1,
            phone="555-1010",
            email="radiology@hospital.com"
        )
        
        pharmacy_dept = Department(
            name="Pharmacy",
            description="Medication management and dispensing",
            floor_number=1,
            phone="555-1011",
            email="pharmacy@hospital.com"
        )
        
        laboratory_dept = Department(
            name="Laboratory",
            description="Medical testing and analysis",
            floor_number=1,
            phone="555-1012",
            email="laboratory@hospital.com"
        )
        
        all_departments = [
            cardiology_dept, emergency_dept, icu_dept, surgery_dept, orthopedics_dept, 
            pediatrics_dept, neurology_dept, oncology_dept, psychiatry_dept, 
            radiology_dept, pharmacy_dept, laboratory_dept
        ]
        
        db.add_all(all_departments)
        db.commit()
        for dept in all_departments:
            db.refresh(dept)
        
        # === STEP 3: Create Staff (Depends on Users and Departments) ===
        print("3. Creating staff...")
        
        # Doctor Staff
        staff_doctor_1 = Staff(
            user_id=doctor_user_1.id,
            employee_id="EMP001",
            department_id=cardiology_dept.id,
            position="Cardiologist",
            specialization="Interventional Cardiology",
            license_number="MD123456",
            hire_date=date(2020, 1, 15),
            salary=Decimal("200000.00"),
            shift_pattern="day",
            status="active"
        )
        
        staff_doctor_2 = Staff(
            user_id=doctor_user_2.id,
            employee_id="EMP002",
            department_id=emergency_dept.id,
            position="Emergency Physician",
            specialization="Emergency Medicine",
            license_number="MD789012",
            hire_date=date(2019, 3, 1),
            salary=Decimal("180000.00"),
            shift_pattern="rotating",
            status="active"
        )
        
        staff_doctor_3 = Staff(
            user_id=doctor_user_3.id,
            employee_id="EMP003",
            department_id=icu_dept.id,
            position="ICU Physician",
            specialization="Critical Care Medicine",
            license_number="MD456789",
            hire_date=date(2018, 6, 1),
            salary=Decimal("220000.00"),
            shift_pattern="rotating",
            status="active"
        )
        
        staff_doctor_4 = Staff(
            user_id=doctor_user_4.id,
            employee_id="EMP004",
            department_id=surgery_dept.id,
            position="Surgeon",
            specialization="General Surgery",
            license_number="MD987654",
            hire_date=date(2017, 9, 15),
            salary=Decimal("250000.00"),
            shift_pattern="day",
            status="active"
        )
        
        staff_doctor_5 = Staff(
            user_id=doctor_user_5.id,
            employee_id="EMP005",
            department_id=orthopedics_dept.id,
            position="Orthopedic Surgeon",
            specialization="Orthopedic Surgery",
            license_number="MD654321",
            hire_date=date(2019, 4, 1),
            salary=Decimal("240000.00"),
            shift_pattern="day",
            status="active"
        )
        
        staff_doctor_6 = Staff(
            user_id=doctor_user_6.id,
            employee_id="EMP006",
            department_id=pediatrics_dept.id,
            position="Pediatrician",
            specialization="Pediatric Medicine",
            license_number="MD321654",
            hire_date=date(2020, 8, 1),
            salary=Decimal("170000.00"),
            shift_pattern="day",
            status="active"
        )
        
        staff_doctor_7 = Staff(
            user_id=doctor_user_7.id,
            employee_id="EMP007",
            department_id=neurology_dept.id,
            position="Neurologist",
            specialization="Neurology",
            license_number="MD147258",
            hire_date=date(2018, 11, 1),
            salary=Decimal("210000.00"),
            shift_pattern="day",
            status="active"
        )
        
        staff_doctor_8 = Staff(
            user_id=doctor_user_8.id,
            employee_id="EMP008",
            department_id=oncology_dept.id,
            position="Oncologist",
            specialization="Medical Oncology",
            license_number="MD852741",
            hire_date=date(2019, 2, 1),
            salary=Decimal("230000.00"),
            shift_pattern="day",
            status="active"
        )
        
        # Nurse Staff
        staff_nurse_1 = Staff(
            user_id=nurse_user_1.id,
            employee_id="EMP009",
            department_id=emergency_dept.id,
            position="Registered Nurse",
            specialization="Emergency Care",
            license_number="RN789012",
            hire_date=date(2021, 3, 1),
            salary=Decimal("75000.00"),
            shift_pattern="rotating",
            status="active"
        )
        
        staff_nurse_2 = Staff(
            user_id=nurse_user_2.id,
            employee_id="EMP010",
            department_id=icu_dept.id,
            position="ICU Nurse",
            specialization="Critical Care",
            license_number="RN345678",
            hire_date=date(2020, 6, 15),
            salary=Decimal("80000.00"),
            shift_pattern="night",
            status="active"
        )
        
        staff_nurse_3 = Staff(
            user_id=nurse_user_3.id,
            employee_id="EMP011",
            department_id=cardiology_dept.id,
            position="Cardiac Nurse",
            specialization="Cardiac Care",
            license_number="RN567890",
            hire_date=date(2020, 1, 15),
            salary=Decimal("77000.00"),
            shift_pattern="day",
            status="active"
        )
        
        staff_nurse_4 = Staff(
            user_id=nurse_user_4.id,
            employee_id="EMP012",
            department_id=surgery_dept.id,
            position="Surgical Nurse",
            specialization="Perioperative Care",
            license_number="RN234567",
            hire_date=date(2019, 8, 1),
            salary=Decimal("82000.00"),
            shift_pattern="day",
            status="active"
        )
        
        staff_nurse_5 = Staff(
            user_id=nurse_user_5.id,
            employee_id="EMP013",
            department_id=pediatrics_dept.id,
            position="Pediatric Nurse",
            specialization="Pediatric Care",
            license_number="RN456789",
            hire_date=date(2021, 1, 1),
            salary=Decimal("74000.00"),
            shift_pattern="day",
            status="active"
        )
        
        staff_nurse_6 = Staff(
            user_id=nurse_user_6.id,
            employee_id="EMP014",
            department_id=orthopedics_dept.id,
            position="Orthopedic Nurse",
            specialization="Orthopedic Care",
            license_number="RN678901",
            hire_date=date(2020, 5, 1),
            salary=Decimal("76000.00"),
            shift_pattern="day",
            status="active"
        )
        
        staff_nurse_7 = Staff(
            user_id=nurse_user_7.id,
            employee_id="EMP015",
            department_id=neurology_dept.id,
            position="Neuro Nurse",
            specialization="Neurological Care",
            license_number="RN890123",
            hire_date=date(2021, 7, 1),
            salary=Decimal("78000.00"),
            shift_pattern="rotating",
            status="active"
        )
        
        staff_nurse_8 = Staff(
            user_id=nurse_user_8.id,
            employee_id="EMP016",
            department_id=oncology_dept.id,
            position="Oncology Nurse",
            specialization="Cancer Care",
            license_number="RN012345",
            hire_date=date(2020, 10, 1),
            salary=Decimal("79000.00"),
            shift_pattern="day",
            status="active"
        )
        
        # Manager Staff
        staff_manager = Staff(
            user_id=manager_user.id,
            employee_id="EMP017",
            department_id=cardiology_dept.id,
            position="Department Manager",
            hire_date=date(2018, 1, 1),
            salary=Decimal("95000.00"),
            shift_pattern="day",
            status="active"
        )
        
        staff_manager_2 = Staff(
            user_id=manager_user_2.id,
            employee_id="EMP018",
            department_id=emergency_dept.id,
            position="Emergency Manager",
            hire_date=date(2019, 3, 1),
            salary=Decimal("98000.00"),
            shift_pattern="day",
            status="active"
        )
        
        staff_manager_3 = Staff(
            user_id=manager_user_3.id,
            employee_id="EMP019",
            department_id=surgery_dept.id,
            position="Surgical Services Manager",
            hire_date=date(2017, 6, 1),
            salary=Decimal("105000.00"),
            shift_pattern="day",
            status="active"
        )
        
        # Support Staff
        staff_cleaner = Staff(
            user_id=cleaner_user.id,
            employee_id="EMP020",
            department_id=emergency_dept.id,
            position="Cleaning Staff",
            hire_date=date(2022, 1, 1),
            salary=Decimal("35000.00"),
            shift_pattern="day",
            status="active"
        )
        
        staff_cleaner_2 = Staff(
            user_id=cleaner_user_2.id,
            employee_id="EMP021",
            department_id=surgery_dept.id,
            position="Cleaning Staff",
            hire_date=date(2021, 8, 1),
            salary=Decimal("36000.00"),
            shift_pattern="night",
            status="active"
        )
        
        staff_technician_1 = Staff(
            user_id=technician_user_1.id,
            employee_id="EMP022",
            department_id=radiology_dept.id,
            position="Radiology Technician",
            specialization="Medical Imaging",
            license_number="RT123456",
            hire_date=date(2020, 4, 1),
            salary=Decimal("65000.00"),
            shift_pattern="day",
            status="active"
        )
        
        staff_technician_2 = Staff(
            user_id=technician_user_2.id,
            employee_id="EMP023",
            department_id=laboratory_dept.id,
            position="Lab Technician",
            specialization="Clinical Laboratory",
            license_number="LT789012",
            hire_date=date(2021, 2, 1),
            salary=Decimal("58000.00"),
            shift_pattern="day",
            status="active"
        )
        
        staff_pharmacist_1 = Staff(
            user_id=pharmacist_user_1.id,
            employee_id="EMP024",
            department_id=pharmacy_dept.id,
            position="Pharmacist",
            specialization="Clinical Pharmacy",
            license_number="PharmD123456",
            hire_date=date(2019, 1, 1),
            salary=Decimal("125000.00"),
            shift_pattern="day",
            status="active"
        )
        
        staff_pharmacist_2 = Staff(
            user_id=pharmacist_user_2.id,
            employee_id="EMP025",
            department_id=pharmacy_dept.id,
            position="Clinical Pharmacist",
            specialization="Hospital Pharmacy",
            license_number="PharmD789012",
            hire_date=date(2020, 7, 1),
            salary=Decimal("120000.00"),
            shift_pattern="day",
            status="active"
        )
        
        all_staff = [
            staff_doctor_1, staff_doctor_2, staff_doctor_3, staff_doctor_4, staff_doctor_5, staff_doctor_6, staff_doctor_7, staff_doctor_8,
            staff_nurse_1, staff_nurse_2, staff_nurse_3, staff_nurse_4, staff_nurse_5, staff_nurse_6, staff_nurse_7, staff_nurse_8,
            staff_manager, staff_manager_2, staff_manager_3,
            staff_cleaner, staff_cleaner_2, staff_technician_1, staff_technician_2, staff_pharmacist_1, staff_pharmacist_2
        ]
        
        db.add_all(all_staff)
        db.commit()
        for staff in all_staff:
            db.refresh(staff)
        
        # === STEP 4: Create Patients (No foreign key dependencies) ===
        print("4. Creating patients...")
        
        # Create a comprehensive list of patients with realistic data
        patients_data = [
            {"patient_number": "P001", "first_name": "Alice", "last_name": "Williams", "dob": date(1985, 5, 15), "gender": "female", "phone": "555-2001", "email": "alice.williams@email.com", "address": "123 Main St, City, State", "emergency_contact_name": "Bob Williams", "emergency_contact_phone": "555-2002", "blood_type": "A+", "allergies": "Penicillin", "medical_history": "Hypertension"},
            {"patient_number": "P002", "first_name": "Robert", "last_name": "Brown", "dob": date(1970, 8, 22), "gender": "male", "phone": "555-2003", "email": "robert.brown@email.com", "address": "456 Oak Ave, City, State", "emergency_contact_name": "Lisa Brown", "emergency_contact_phone": "555-2004", "blood_type": "O-", "allergies": None, "medical_history": "Diabetes Type 2"},
            {"patient_number": "P003", "first_name": "Maria", "last_name": "Garcia", "dob": date(1992, 12, 3), "gender": "female", "phone": "555-2005", "email": "maria.garcia@email.com", "address": "789 Pine St, City, State", "emergency_contact_name": "Jose Garcia", "emergency_contact_phone": "555-2006", "blood_type": "B+", "allergies": "Shellfish", "medical_history": "Asthma"},
            {"patient_number": "P004", "first_name": "David", "last_name": "Jones", "dob": date(1965, 7, 10), "gender": "male", "phone": "555-2007", "email": "david.jones@email.com", "address": "321 Elm Ave, City, State", "emergency_contact_name": "Susan Jones", "emergency_contact_phone": "555-2008", "blood_type": "AB+", "allergies": None, "medical_history": "Heart disease, Hypertension"},
            {"patient_number": "P005", "first_name": "Jennifer", "last_name": "Wilson", "dob": date(1978, 3, 25), "gender": "female", "phone": "555-2009", "email": "jennifer.wilson@email.com", "address": "654 Maple Dr, City, State", "emergency_contact_name": "Michael Wilson", "emergency_contact_phone": "555-2010", "blood_type": "A-", "allergies": "Latex", "medical_history": "None"},
            {"patient_number": "P006", "first_name": "Michael", "last_name": "Thompson", "dob": date(1989, 11, 18), "gender": "male", "phone": "555-2011", "email": "michael.thompson@email.com", "address": "987 Cedar Ln, City, State", "emergency_contact_name": "Sarah Thompson", "emergency_contact_phone": "555-2012", "blood_type": "O+", "allergies": "Nuts", "medical_history": "High cholesterol"},
            {"patient_number": "P007", "first_name": "Sarah", "last_name": "Davis", "dob": date(1995, 6, 8), "gender": "female", "phone": "555-2013", "email": "sarah.davis@email.com", "address": "159 Birch St, City, State", "emergency_contact_name": "John Davis", "emergency_contact_phone": "555-2014", "blood_type": "B-", "allergies": None, "medical_history": "Anxiety"},
            {"patient_number": "P008", "first_name": "Christopher", "last_name": "Miller", "dob": date(1982, 9, 14), "gender": "male", "phone": "555-2015", "email": "christopher.miller@email.com", "address": "753 Willow Ave, City, State", "emergency_contact_name": "Amanda Miller", "emergency_contact_phone": "555-2016", "blood_type": "AB-", "allergies": "Iodine", "medical_history": "Back injury"},
            {"patient_number": "P009", "first_name": "Amanda", "last_name": "Anderson", "dob": date(1987, 1, 30), "gender": "female", "phone": "555-2017", "email": "amanda.anderson@email.com", "address": "357 Spruce Rd, City, State", "emergency_contact_name": "James Anderson", "emergency_contact_phone": "555-2018", "blood_type": "A+", "allergies": "Sulfa drugs", "medical_history": "Migraine"},
            {"patient_number": "P010", "first_name": "James", "last_name": "Taylor", "dob": date(1973, 4, 12), "gender": "male", "phone": "555-2019", "email": "james.taylor@email.com", "address": "951 Poplar Ct, City, State", "emergency_contact_name": "Linda Taylor", "emergency_contact_phone": "555-2020", "blood_type": "O-", "allergies": None, "medical_history": "Arthritis"},
            {"patient_number": "P011", "first_name": "Linda", "last_name": "White", "dob": date(1960, 12, 5), "gender": "female", "phone": "555-2021", "email": "linda.white@email.com", "address": "258 Ash Blvd, City, State", "emergency_contact_name": "Richard White", "emergency_contact_phone": "555-2022", "blood_type": "B+", "allergies": "Morphine", "medical_history": "Osteoporosis"},
            {"patient_number": "P012", "first_name": "Richard", "last_name": "Harris", "dob": date(1956, 8, 28), "gender": "male", "phone": "555-2023", "email": "richard.harris@email.com", "address": "456 Hickory Way, City, State", "emergency_contact_name": "Carol Harris", "emergency_contact_phone": "555-2024", "blood_type": "A-", "allergies": None, "medical_history": "COPD"},
            {"patient_number": "P013", "first_name": "Carol", "last_name": "Martin", "dob": date(1969, 2, 17), "gender": "female", "phone": "555-2025", "email": "carol.martin@email.com", "address": "789 Dogwood St, City, State", "emergency_contact_name": "Paul Martin", "emergency_contact_phone": "555-2026", "blood_type": "AB+", "allergies": "Codeine", "medical_history": "Thyroid disorder"},
            {"patient_number": "P014", "first_name": "Paul", "last_name": "Jackson", "dob": date(1991, 10, 9), "gender": "male", "phone": "555-2027", "email": "paul.jackson@email.com", "address": "123 Redwood Dr, City, State", "emergency_contact_name": "Mary Jackson", "emergency_contact_phone": "555-2028", "blood_type": "O+", "allergies": None, "medical_history": "None"},
            {"patient_number": "P015", "first_name": "Mary", "last_name": "Moore", "dob": date(1984, 7, 23), "gender": "female", "phone": "555-2029", "email": "mary.moore@email.com", "address": "654 Pine Ridge, City, State", "emergency_contact_name": "Kevin Moore", "emergency_contact_phone": "555-2030", "blood_type": "B-", "allergies": "Aspirin", "medical_history": "Depression"},
            {"patient_number": "P016", "first_name": "Kevin", "last_name": "Lee", "dob": date(1977, 5, 19), "gender": "male", "phone": "555-2031", "email": "kevin.lee@email.com", "address": "987 Oak Hill, City, State", "emergency_contact_name": "Susan Lee", "emergency_contact_phone": "555-2032", "blood_type": "A+", "allergies": "Vancomycin", "medical_history": "Kidney stones"},
            {"patient_number": "P017", "first_name": "Susan", "last_name": "Garcia", "dob": date(1963, 11, 2), "gender": "female", "phone": "555-2033", "email": "susan.garcia@email.com", "address": "159 Maple Heights, City, State", "emergency_contact_name": "Carlos Garcia", "emergency_contact_phone": "555-2034", "blood_type": "O-", "allergies": None, "medical_history": "Diabetes Type 1"},
            {"patient_number": "P018", "first_name": "Carlos", "last_name": "Rodriguez", "dob": date(1988, 3, 16), "gender": "male", "phone": "555-2035", "email": "carlos.rodriguez@email.com", "address": "753 Cedar Grove, City, State", "emergency_contact_name": "Ana Rodriguez", "emergency_contact_phone": "555-2036", "blood_type": "AB-", "allergies": "Contrast dye", "medical_history": "Epilepsy"},
            {"patient_number": "P019", "first_name": "Ana", "last_name": "Lopez", "dob": date(1994, 9, 7), "gender": "female", "phone": "555-2037", "email": "ana.lopez@email.com", "address": "357 Birch Valley, City, State", "emergency_contact_name": "Miguel Lopez", "emergency_contact_phone": "555-2038", "blood_type": "B+", "allergies": "NSAIDs", "medical_history": "Fibromyalgia"},
            {"patient_number": "P020", "first_name": "Miguel", "last_name": "Gonzalez", "dob": date(1971, 12, 11), "gender": "male", "phone": "555-2039", "email": "miguel.gonzalez@email.com", "address": "951 Elm Crest, City, State", "emergency_contact_name": "Rosa Gonzalez", "emergency_contact_phone": "555-2040", "blood_type": "A-", "allergies": None, "medical_history": "Sleep apnea"},
            {"patient_number": "P021", "first_name": "Rosa", "last_name": "Hernandez", "dob": date(1980, 4, 26), "gender": "female", "phone": "555-2041", "email": "rosa.hernandez@email.com", "address": "258 Willow Creek, City, State", "emergency_contact_name": "Juan Hernandez", "emergency_contact_phone": "555-2042", "blood_type": "O+", "allergies": "Antibiotics", "medical_history": "Lupus"},
            {"patient_number": "P022", "first_name": "Juan", "last_name": "Perez", "dob": date(1986, 8, 13), "gender": "male", "phone": "555-2043", "email": "juan.perez@email.com", "address": "456 Spruce Canyon, City, State", "emergency_contact_name": "Elena Perez", "emergency_contact_phone": "555-2044", "blood_type": "B-", "allergies": None, "medical_history": "Chronic pain"},
            {"patient_number": "P023", "first_name": "Elena", "last_name": "Sanchez", "dob": date(1992, 1, 8), "gender": "female", "phone": "555-2045", "email": "elena.sanchez@email.com", "address": "789 Poplar Ridge, City, State", "emergency_contact_name": "Diego Sanchez", "emergency_contact_phone": "555-2046", "blood_type": "AB+", "allergies": "Eggs", "medical_history": "Eating disorder"},
            {"patient_number": "P024", "first_name": "Diego", "last_name": "Rivera", "dob": date(1975, 6, 21), "gender": "male", "phone": "555-2047", "email": "diego.rivera@email.com", "address": "123 Ash Meadow, City, State", "emergency_contact_name": "Carmen Rivera", "emergency_contact_phone": "555-2048", "blood_type": "A+", "allergies": "Zinc", "medical_history": "Hypertension"},
            {"patient_number": "P025", "first_name": "Carmen", "last_name": "Torres", "dob": date(1968, 10, 15), "gender": "female", "phone": "555-2049", "email": "carmen.torres@email.com", "address": "654 Hickory Point, City, State", "emergency_contact_name": "Roberto Torres", "emergency_contact_phone": "555-2050", "blood_type": "O-", "allergies": None, "medical_history": "Cancer survivor"}
        ]
        
        all_patients = []
        for p_data in patients_data:
            patient = Patient(
                patient_number=p_data["patient_number"],
                first_name=p_data["first_name"],
                last_name=p_data["last_name"],
                date_of_birth=p_data["dob"],
                gender=p_data["gender"],
                phone=p_data["phone"],
                email=p_data["email"],
                address=p_data["address"],
                emergency_contact_name=p_data["emergency_contact_name"],
                emergency_contact_phone=p_data["emergency_contact_phone"],
                blood_type=p_data["blood_type"],
                allergies=p_data["allergies"],
                medical_history=p_data["medical_history"]
            )
            all_patients.append(patient)
        
        db.add_all(all_patients)
        db.commit()
        for patient in all_patients:
            db.refresh(patient)
        
        # Store specific patients for later reference
        patient1, patient2, patient3, patient4 = all_patients[0], all_patients[1], all_patients[2], all_patients[3]
        
        # === STEP 5: Create Rooms (Depends on Departments) ===
        print("5. Creating rooms...")
        
        # Cardiology Department Rooms (Floor 3)
        cardiology_rooms = []
        for i in range(1, 11):  # 10 rooms
            room = Room(
                room_number=f"30{i}",
                department_id=cardiology_dept.id,
                room_type="private" if i <= 5 else "semi-private",
                floor_number=3,
                capacity=1 if i <= 5 else 2
            )
            cardiology_rooms.append(room)
        
        # Emergency Department Rooms (Floor 1)
        emergency_rooms = []
        for i in range(1, 16):  # 15 rooms
            room = Room(
                room_number=f"10{i}",
                department_id=emergency_dept.id,
                room_type="emergency",
                floor_number=1,
                capacity=4 if i <= 10 else 2
            )
            emergency_rooms.append(room)
        
        # ICU Department Rooms (Floor 4)
        icu_rooms = []
        for i in range(1, 21):  # 20 rooms
            room = Room(
                room_number=f"40{i}",
                department_id=icu_dept.id,
                room_type="icu",
                floor_number=4,
                capacity=1
            )
            icu_rooms.append(room)
        
        # Surgery Department Rooms (Floor 5)
        surgery_rooms = []
        for i in range(1, 9):  # 8 operating rooms
            room = Room(
                room_number=f"50{i}",
                department_id=surgery_dept.id,
                room_type="operating_room",
                floor_number=5,
                capacity=1
            )
            surgery_rooms.append(room)
        
        # Orthopedics Department Rooms (Floor 6)
        orthopedics_rooms = []
        for i in range(1, 13):  # 12 rooms
            room = Room(
                room_number=f"60{i}",
                department_id=orthopedics_dept.id,
                room_type="private" if i <= 6 else "semi-private",
                floor_number=6,
                capacity=1 if i <= 6 else 2
            )
            orthopedics_rooms.append(room)
        
        # Pediatrics Department Rooms (Floor 2)
        pediatrics_rooms = []
        for i in range(1, 15):  # 14 rooms
            room = Room(
                room_number=f"20{i}",
                department_id=pediatrics_dept.id,
                room_type="pediatric",
                floor_number=2,
                capacity=2 if i <= 10 else 4
            )
            pediatrics_rooms.append(room)
        
        # Neurology Department Rooms (Floor 7)
        neurology_rooms = []
        for i in range(1, 11):  # 10 rooms
            room = Room(
                room_number=f"70{i}",
                department_id=neurology_dept.id,
                room_type="private",
                floor_number=7,
                capacity=1
            )
            neurology_rooms.append(room)
        
        # Oncology Department Rooms (Floor 8)
        oncology_rooms = []
        for i in range(1, 13):  # 12 rooms
            room = Room(
                room_number=f"80{i}",
                department_id=oncology_dept.id,
                room_type="private" if i <= 8 else "treatment_room",
                floor_number=8,
                capacity=1
            )
            oncology_rooms.append(room)
        
        # Psychiatry Department Rooms (Floor 9)
        psychiatry_rooms = []
        for i in range(1, 9):  # 8 rooms
            room = Room(
                room_number=f"90{i}",
                department_id=psychiatry_dept.id,
                room_type="private",
                floor_number=9,
                capacity=1
            )
            psychiatry_rooms.append(room)
        
        all_rooms = (cardiology_rooms + emergency_rooms + icu_rooms + surgery_rooms + 
                    orthopedics_rooms + pediatrics_rooms + neurology_rooms + 
                    oncology_rooms + psychiatry_rooms)
        
        db.add_all(all_rooms)
        db.commit()
        for room in all_rooms:
            db.refresh(room)
        
        # Store specific rooms for later reference
        room301 = cardiology_rooms[0]
        room302 = cardiology_rooms[1]
        room101 = emergency_rooms[0]
        room401 = icu_rooms[0]
        room402 = icu_rooms[1]
        
        # === STEP 6: Create Beds (Depends on Rooms and optionally Patients) ===
        print("6. Creating beds...")
        
        all_beds = []
        bed_counter = 0
        
        # Create beds for all rooms
        for room in all_rooms:
            capacity = room.capacity
            for bed_num in range(1, capacity + 1):
                bed_letter = chr(ord('A') + bed_num - 1)  # A, B, C, D
                bed_number = f"{room.room_number}{bed_letter}"
                
                # Assign patients to some beds (first 25 patients get beds)
                patient_id = None
                admission_date = None
                status = "available"
                
                if bed_counter < 25 and bed_counter < len(all_patients):
                    patient_id = all_patients[bed_counter].id
                    admission_date = datetime.now() - timedelta(days=random.randint(1, 14))
                    status = "occupied"
                    bed_counter += 1
                elif bed_counter < 30:  # Some beds in maintenance
                    status = "maintenance"
                    bed_counter += 1
                
                # Determine bed type based on room type
                if room.room_type == "icu":
                    bed_type = "icu"
                elif room.room_type == "emergency":
                    bed_type = "emergency"
                elif room.room_type == "operating_room":
                    bed_type = "surgical"
                elif room.room_type == "pediatric":
                    bed_type = "pediatric"
                else:
                    bed_type = "standard"
                
                bed = Bed(
                    bed_number=bed_number,
                    room_id=room.id,
                    bed_type=bed_type,
                    status=status,
                    patient_id=patient_id,
                    admission_date=admission_date,
                    notes=f"Bed {bed_number} in {room.room_type} room"
                )
                all_beds.append(bed)
        
        db.add_all(all_beds)
        db.commit()
        for bed in all_beds:
            db.refresh(bed)
        
        # Store specific beds for later reference
        bed301a = all_beds[0]  # First bed (301A)
        bed302a = all_beds[1]  # Second bed (302A)
        bed302b = all_beds[2] if len(all_beds) > 2 else all_beds[0]  # Third bed or fallback
        bed101a = next((b for b in all_beds if b.bed_number.startswith("101")), all_beds[0])
        bed401a = next((b for b in all_beds if b.bed_number.startswith("401")), all_beds[0])
        
        # === STEP 7: Create Equipment Categories (No dependencies) ===
        print("7. Creating equipment categories...")
        medical_devices = EquipmentCategory(
            name="Medical Devices",
            description="Various medical equipment and devices"
        )
        
        monitoring_equipment = EquipmentCategory(
            name="Monitoring Equipment",
            description="Patient monitoring systems"
        )
        
        surgical_equipment = EquipmentCategory(
            name="Surgical Equipment",
            description="Equipment for surgical procedures"
        )
        
        life_support = EquipmentCategory(
            name="Life Support",
            description="Life support and ventilation equipment"
        )
        
        diagnostic_equipment = EquipmentCategory(
            name="Diagnostic Equipment",
            description="Equipment for medical diagnosis and imaging"
        )
        
        laboratory_equipment = EquipmentCategory(
            name="Laboratory Equipment",
            description="Equipment for laboratory testing and analysis"
        )
        
        therapeutic_equipment = EquipmentCategory(
            name="Therapeutic Equipment",
            description="Equipment for patient treatment and therapy"
        )
        
        emergency_equipment = EquipmentCategory(
            name="Emergency Equipment",
            description="Critical emergency response equipment"
        )
        
        mobility_equipment = EquipmentCategory(
            name="Mobility Equipment",
            description="Wheelchairs, beds, and mobility aids"
        )
        
        communication_equipment = EquipmentCategory(
            name="Communication Equipment",
            description="Communication and alert systems"
        )
        
        all_equipment_categories = [
            medical_devices, monitoring_equipment, surgical_equipment, life_support,
            diagnostic_equipment, laboratory_equipment, therapeutic_equipment,
            emergency_equipment, mobility_equipment, communication_equipment
        ]
        
        db.add_all(all_equipment_categories)
        db.commit()
        for cat in all_equipment_categories:
            db.refresh(cat)
        
        # === STEP 8: Create Equipment (Depends on Categories and Departments) ===
        print("8. Creating equipment...")
        
        # Monitoring Equipment
        equipment_list = []
        
        # ECG Machines
        for i in range(1, 16):  # 15 ECG machines
            ecg = Equipment(
                equipment_id=f"EQ{i:03d}",
                name="ECG Machine",
                category_id=monitoring_equipment.id,
                model=f"CardioMax {3000 + i}",
                manufacturer="MedTech Corp",
                serial_number=f"CM{3000 + i}-{i:03d}",
                purchase_date=date(2022, random.randint(1, 12), random.randint(1, 28)),
                warranty_expiry=date(2025, random.randint(1, 12), random.randint(1, 28)),
                location=f"Room {random.choice([r.room_number for r in all_rooms[:20]])}",
                department_id=random.choice([cardiology_dept.id, emergency_dept.id, icu_dept.id]),
                status=random.choice(["available", "in_use", "maintenance"]),
                cost=Decimal(f"{random.randint(20000, 30000)}.00")
            )
            equipment_list.append(ecg)
        
        # Ventilators
        for i in range(1, 21):  # 20 ventilators
            ventilator = Equipment(
                equipment_id=f"VT{i:03d}",
                name="Ventilator",
                category_id=life_support.id,
                model=f"BreathEasy Pro {i}",
                manufacturer="LifeSupport Inc",
                serial_number=f"BEP-{i:03d}",
                purchase_date=date(2023, random.randint(1, 12), random.randint(1, 28)),
                warranty_expiry=date(2026, random.randint(1, 12), random.randint(1, 28)),
                location=f"Room {random.choice([r.room_number for r in all_rooms if r.room_type in ['icu', 'emergency']])}",
                department_id=random.choice([icu_dept.id, emergency_dept.id]),
                status=random.choice(["available", "in_use"]),
                cost=Decimal(f"{random.randint(40000, 50000)}.00")
            )
            equipment_list.append(ventilator)
        
        # Defibrillators
        for i in range(1, 11):  # 10 defibrillators
            defib = Equipment(
                equipment_id=f"DF{i:03d}",
                name="Defibrillator",
                category_id=emergency_equipment.id,
                model=f"LifeSaver {2000 + i}",
                manufacturer="Emergency Corp",
                serial_number=f"LS{2000 + i}-{i:03d}",
                purchase_date=date(2021, random.randint(1, 12), random.randint(1, 28)),
                warranty_expiry=date(2024, random.randint(1, 12), random.randint(1, 28)),
                location=f"Floor {random.randint(1, 9)}",
                department_id=emergency_dept.id,
                status=random.choice(["available", "in_use"]),
                cost=Decimal(f"{random.randint(12000, 18000)}.00")
            )
            equipment_list.append(defib)
        
        # X-Ray Machines
        for i in range(1, 6):  # 5 X-ray machines
            xray = Equipment(
                equipment_id=f"XR{i:03d}",
                name="X-Ray Machine",
                category_id=diagnostic_equipment.id,
                model=f"RadiMax {1000 + i}",
                manufacturer="Imaging Solutions",
                serial_number=f"RM{1000 + i}-{i:03d}",
                purchase_date=date(2020, random.randint(1, 12), random.randint(1, 28)),
                warranty_expiry=date(2025, random.randint(1, 12), random.randint(1, 28)),
                location="Radiology Suite",
                department_id=radiology_dept.id,
                status=random.choice(["available", "in_use", "maintenance"]),
                cost=Decimal(f"{random.randint(80000, 120000)}.00")
            )
            equipment_list.append(xray)
        
        # CT Scanners
        for i in range(1, 4):  # 3 CT scanners
            ct = Equipment(
                equipment_id=f"CT{i:03d}",
                name="CT Scanner",
                category_id=diagnostic_equipment.id,
                model=f"ScanPro {500 + i}",
                manufacturer="Advanced Imaging",
                serial_number=f"SP{500 + i}-{i:03d}",
                purchase_date=date(2019, random.randint(1, 12), random.randint(1, 28)),
                warranty_expiry=date(2024, random.randint(1, 12), random.randint(1, 28)),
                location="Radiology Suite",
                department_id=radiology_dept.id,
                status=random.choice(["available", "in_use"]),
                cost=Decimal(f"{random.randint(300000, 500000)}.00")
            )
            equipment_list.append(ct)
        
        # MRI Machines
        for i in range(1, 3):  # 2 MRI machines
            mri = Equipment(
                equipment_id=f"MR{i:03d}",
                name="MRI Machine",
                category_id=diagnostic_equipment.id,
                model=f"MagnetMax {100 + i}",
                manufacturer="Magnetic Imaging Corp",
                serial_number=f"MM{100 + i}-{i:03d}",
                purchase_date=date(2018, random.randint(1, 12), random.randint(1, 28)),
                warranty_expiry=date(2023, random.randint(1, 12), random.randint(1, 28)),
                location="Advanced Imaging",
                department_id=radiology_dept.id,
                status=random.choice(["available", "in_use"]),
                cost=Decimal(f"{random.randint(800000, 1200000)}.00")
            )
            equipment_list.append(mri)
        
        # Ultrasound Machines
        for i in range(1, 9):  # 8 ultrasound machines
            ultrasound = Equipment(
                equipment_id=f"US{i:03d}",
                name="Ultrasound Machine",
                category_id=diagnostic_equipment.id,
                model=f"SonicView {200 + i}",
                manufacturer="Sound Imaging",
                serial_number=f"SV{200 + i}-{i:03d}",
                purchase_date=date(2021, random.randint(1, 12), random.randint(1, 28)),
                warranty_expiry=date(2026, random.randint(1, 12), random.randint(1, 28)),
                location=f"Room {random.choice([r.room_number for r in all_rooms[:30]])}",
                department_id=random.choice([cardiology_dept.id, emergency_dept.id, pediatrics_dept.id]),
                status=random.choice(["available", "in_use"]),
                cost=Decimal(f"{random.randint(50000, 80000)}.00")
            )
            equipment_list.append(ultrasound)
        
        # Surgical Equipment
        for i in range(1, 13):  # 12 surgical instruments sets
            surgical = Equipment(
                equipment_id=f"SR{i:03d}",
                name="Surgical Instrument Set",
                category_id=surgical_equipment.id,
                model=f"SurgiPro {i}",
                manufacturer="Surgical Solutions",
                serial_number=f"SS{i:03d}",
                purchase_date=date(2022, random.randint(1, 12), random.randint(1, 28)),
                warranty_expiry=date(2027, random.randint(1, 12), random.randint(1, 28)),
                location=f"OR {i % 8 + 1}",
                department_id=surgery_dept.id,
                status=random.choice(["available", "in_use", "maintenance"]),
                cost=Decimal(f"{random.randint(15000, 25000)}.00")
            )
            equipment_list.append(surgical)
        
        # Patient Monitors
        for i in range(1, 31):  # 30 patient monitors
            monitor = Equipment(
                equipment_id=f"PM{i:03d}",
                name="Patient Monitor",
                category_id=monitoring_equipment.id,
                model=f"VitalWatch {i}",
                manufacturer="Monitor Systems",
                serial_number=f"VW{i:03d}",
                purchase_date=date(2022, random.randint(1, 12), random.randint(1, 28)),
                warranty_expiry=date(2027, random.randint(1, 12), random.randint(1, 28)),
                location=f"Room {random.choice([r.room_number for r in all_rooms[:50]])}",
                department_id=random.choice([icu_dept.id, cardiology_dept.id, emergency_dept.id]),
                status=random.choice(["available", "in_use"]),
                cost=Decimal(f"{random.randint(8000, 15000)}.00")
            )
            equipment_list.append(monitor)
        
        # Wheelchairs
        for i in range(1, 21):  # 20 wheelchairs
            wheelchair = Equipment(
                equipment_id=f"WC{i:03d}",
                name="Wheelchair",
                category_id=mobility_equipment.id,
                model=f"ComfortRide {i}",
                manufacturer="Mobility Solutions",
                serial_number=f"CR{i:03d}",
                purchase_date=date(2021, random.randint(1, 12), random.randint(1, 28)),
                warranty_expiry=date(2026, random.randint(1, 12), random.randint(1, 28)),
                location=f"Floor {random.randint(1, 9)}",
                department_id=random.choice(all_departments).id,
                status=random.choice(["available", "in_use"]),
                cost=Decimal(f"{random.randint(800, 1500)}.00")
            )
            equipment_list.append(wheelchair)
        
        # Infusion Pumps
        for i in range(1, 26):  # 25 infusion pumps
            pump = Equipment(
                equipment_id=f"IP{i:03d}",
                name="Infusion Pump",
                category_id=therapeutic_equipment.id,
                model=f"FlowMaster {i}",
                manufacturer="Infusion Tech",
                serial_number=f"FM{i:03d}",
                purchase_date=date(2022, random.randint(1, 12), random.randint(1, 28)),
                warranty_expiry=date(2027, random.randint(1, 12), random.randint(1, 28)),
                location=f"Room {random.choice([r.room_number for r in all_rooms[:40]])}",
                department_id=random.choice([icu_dept.id, oncology_dept.id, emergency_dept.id]),
                status=random.choice(["available", "in_use"]),
                cost=Decimal(f"{random.randint(3000, 6000)}.00")
            )
            equipment_list.append(pump)
        
        db.add_all(equipment_list)
        db.commit()
        for equipment in equipment_list:
            db.refresh(equipment)
        
        # Store specific equipment for later reference
        ecg_machine = equipment_list[0]
        ventilator1 = next((e for e in equipment_list if e.name == "Ventilator"), equipment_list[0])
        defibrillator = next((e for e in equipment_list if e.name == "Defibrillator"), equipment_list[0])
        
        # === STEP 9: Create Supply Categories (No dependencies) ===
        print("9. Creating supply categories...")
        medications = SupplyCategory(
            name="Medications",
            description="Pharmaceutical supplies and drugs"
        )
        
        medical_supplies = SupplyCategory(
            name="Medical Supplies",
            description="General medical supplies and consumables"
        )
        
        surgical_supplies = SupplyCategory(
            name="Surgical Supplies",
            description="Supplies for surgical procedures"
        )
        
        emergency_supplies = SupplyCategory(
            name="Emergency Supplies",
            description="Critical emergency medical supplies"
        )
        
        diagnostic_supplies = SupplyCategory(
            name="Diagnostic Supplies",
            description="Supplies for medical testing and diagnosis"
        )
        
        protective_equipment = SupplyCategory(
            name="Protective Equipment",
            description="Personal protective equipment and safety supplies"
        )
        
        wound_care = SupplyCategory(
            name="Wound Care",
            description="Supplies for wound treatment and care"
        )
        
        respiratory_supplies = SupplyCategory(
            name="Respiratory Supplies",
            description="Supplies for respiratory care and support"
        )
        
        iv_supplies = SupplyCategory(
            name="IV Supplies",
            description="Intravenous therapy supplies"
        )
        
        laboratory_supplies = SupplyCategory(
            name="Laboratory Supplies",
            description="Supplies for laboratory testing"
        )
        
        all_supply_categories = [
            medications, medical_supplies, surgical_supplies, emergency_supplies,
            diagnostic_supplies, protective_equipment, wound_care, respiratory_supplies,
            iv_supplies, laboratory_supplies
        ]
        
        db.add_all(all_supply_categories)
        db.commit()
        for cat in all_supply_categories:
            db.refresh(cat)
        
        # === STEP 10: Create Supplies (Depends on Categories) ===
        print("10. Creating supplies...")
        
        supplies_data = [
            # Medications
            {"item_code": "MED001", "name": "Aspirin 81mg", "category": medications, "description": "Low-dose aspirin tablets", "unit": "tablets", "min_stock": 100, "max_stock": 1000, "current": 500, "cost": "0.05", "supplier": "PharmaCorp", "expiry": date(2025, 12, 31), "location": "Pharmacy Storage"},
            {"item_code": "MED002", "name": "Morphine 10mg/ml", "category": medications, "description": "Morphine injection for pain management", "unit": "vials", "min_stock": 10, "max_stock": 100, "current": 45, "cost": "15.50", "supplier": "PharmaCorp", "expiry": date(2024, 12, 31), "location": "Controlled Substances Cabinet"},
            {"item_code": "MED003", "name": "Acetaminophen 500mg", "category": medications, "description": "Pain and fever reducer", "unit": "tablets", "min_stock": 200, "max_stock": 2000, "current": 1200, "cost": "0.03", "supplier": "GenericMeds", "expiry": date(2025, 8, 15), "location": "Pharmacy Storage"},
            {"item_code": "MED004", "name": "Ibuprofen 200mg", "category": medications, "description": "Anti-inflammatory medication", "unit": "tablets", "min_stock": 150, "max_stock": 1500, "current": 800, "cost": "0.04", "supplier": "GenericMeds", "expiry": date(2025, 10, 20), "location": "Pharmacy Storage"},
            {"item_code": "MED005", "name": "Lisinopril 10mg", "category": medications, "description": "ACE inhibitor for hypertension", "unit": "tablets", "min_stock": 100, "max_stock": 1000, "current": 350, "cost": "0.25", "supplier": "CardioMeds", "expiry": date(2024, 11, 30), "location": "Pharmacy Storage"},
            {"item_code": "MED006", "name": "Metformin 500mg", "category": medications, "description": "Diabetes medication", "unit": "tablets", "min_stock": 200, "max_stock": 2000, "current": 1100, "cost": "0.15", "supplier": "DiabetesCare", "expiry": date(2025, 6, 10), "location": "Pharmacy Storage"},
            {"item_code": "MED007", "name": "Amoxicillin 500mg", "category": medications, "description": "Antibiotic", "unit": "capsules", "min_stock": 100, "max_stock": 1000, "current": 425, "cost": "0.45", "supplier": "AntibioticCorp", "expiry": date(2024, 9, 25), "location": "Pharmacy Storage"},
            {"item_code": "MED008", "name": "Prednisone 5mg", "category": medications, "description": "Corticosteroid", "unit": "tablets", "min_stock": 50, "max_stock": 500, "current": 175, "cost": "0.12", "supplier": "SteroidMeds", "expiry": date(2025, 3, 18), "location": "Pharmacy Storage"},
            {"item_code": "MED009", "name": "Warfarin 5mg", "category": medications, "description": "Anticoagulant", "unit": "tablets", "min_stock": 50, "max_stock": 500, "current": 125, "cost": "0.35", "supplier": "BloodMeds", "expiry": date(2024, 12, 5), "location": "Pharmacy Storage"},
            {"item_code": "MED010", "name": "Insulin Glargine", "category": medications, "description": "Long-acting insulin", "unit": "vials", "min_stock": 20, "max_stock": 200, "current": 85, "cost": "125.00", "supplier": "InsulinTech", "expiry": date(2024, 8, 12), "location": "Refrigerated Storage"},
            
            # Medical Supplies
            {"item_code": "SUP001", "name": "Disposable Syringes 10ml", "category": medical_supplies, "description": "Sterile disposable syringes", "unit": "pieces", "min_stock": 50, "max_stock": 500, "current": 25, "cost": "0.75", "supplier": "MedSupply Co", "location": "Supply Room A"},
            {"item_code": "SUP002", "name": "Sterile Gauze Pads 4x4", "category": medical_supplies, "description": "4x4 inch sterile gauze pads", "unit": "pieces", "min_stock": 200, "max_stock": 2000, "current": 1500, "cost": "0.25", "supplier": "MedSupply Co", "location": "Supply Room A"},
            {"item_code": "SUP003", "name": "Medical Gloves (Nitrile)", "category": protective_equipment, "description": "Powder-free nitrile examination gloves", "unit": "boxes", "min_stock": 50, "max_stock": 500, "current": 275, "cost": "8.50", "supplier": "SafetyFirst", "location": "Supply Room B"},
            {"item_code": "SUP004", "name": "Adhesive Bandages", "category": wound_care, "description": "Assorted sizes adhesive bandages", "unit": "boxes", "min_stock": 30, "max_stock": 300, "current": 150, "cost": "3.25", "supplier": "WoundCare Inc", "location": "Supply Room A"},
            {"item_code": "SUP005", "name": "Alcohol Prep Pads", "category": medical_supplies, "description": "70% isopropyl alcohol prep pads", "unit": "boxes", "min_stock": 40, "max_stock": 400, "current": 225, "cost": "4.75", "supplier": "MedSupply Co", "location": "Supply Room A"},
            {"item_code": "SUP006", "name": "Thermometer Covers", "category": medical_supplies, "description": "Disposable thermometer probe covers", "unit": "boxes", "min_stock": 20, "max_stock": 200, "current": 95, "cost": "12.50", "supplier": "TempCare", "location": "Supply Room C"},
            {"item_code": "SUP007", "name": "Cotton Swabs", "category": medical_supplies, "description": "Sterile cotton swabs", "unit": "packages", "min_stock": 30, "max_stock": 300, "current": 180, "cost": "2.25", "supplier": "CottonCorp", "location": "Supply Room A"},
            {"item_code": "SUP008", "name": "Medical Tape", "category": wound_care, "description": "1-inch medical adhesive tape", "unit": "rolls", "min_stock": 25, "max_stock": 250, "current": 135, "cost": "1.85", "supplier": "TapeMedical", "location": "Supply Room A"},
            {"item_code": "SUP009", "name": "Tongue Depressors", "category": medical_supplies, "description": "Wooden tongue depressors", "unit": "boxes", "min_stock": 15, "max_stock": 150, "current": 75, "cost": "5.50", "supplier": "WoodMed", "location": "Supply Room C"},
            {"item_code": "SUP010", "name": "Blood Pressure Cuffs", "category": medical_supplies, "description": "Disposable blood pressure cuffs", "unit": "pieces", "min_stock": 20, "max_stock": 200, "current": 85, "cost": "12.75", "supplier": "VitalSupply", "location": "Supply Room B"},
            
            # Surgical Supplies
            {"item_code": "SUR001", "name": "Surgical Masks", "category": surgical_supplies, "description": "Level 3 surgical masks", "unit": "boxes", "min_stock": 30, "max_stock": 300, "current": 185, "cost": "15.25", "supplier": "SurgicalSafe", "location": "OR Supply"},
            {"item_code": "SUR002", "name": "Surgical Gowns", "category": surgical_supplies, "description": "Sterile surgical gowns", "unit": "pieces", "min_stock": 25, "max_stock": 250, "current": 125, "cost": "8.75", "supplier": "SterileWear", "location": "OR Supply"},
            {"item_code": "SUR003", "name": "Surgical Drapes", "category": surgical_supplies, "description": "Sterile surgical drapes", "unit": "pieces", "min_stock": 20, "max_stock": 200, "current": 95, "cost": "12.50", "supplier": "DrapeMax", "location": "OR Supply"},
            {"item_code": "SUR004", "name": "Suture Material 3-0", "category": surgical_supplies, "description": "Non-absorbable suture material", "unit": "pieces", "min_stock": 50, "max_stock": 500, "current": 275, "cost": "3.25", "supplier": "SutureCorporation", "location": "OR Supply"},
            {"item_code": "SUR005", "name": "Surgical Scalpels", "category": surgical_supplies, "description": "Disposable surgical scalpels", "unit": "pieces", "min_stock": 30, "max_stock": 300, "current": 155, "cost": "2.85", "supplier": "SharpMed", "location": "OR Supply"},
            
            # Emergency Supplies
            {"item_code": "EMR001", "name": "Emergency Airways", "category": emergency_supplies, "description": "Oropharyngeal airways", "unit": "pieces", "min_stock": 15, "max_stock": 150, "current": 65, "cost": "8.50", "supplier": "AirwayMed", "location": "Emergency Cart"},
            {"item_code": "EMR002", "name": "IV Catheters 18G", "category": iv_supplies, "description": "18 gauge IV catheters", "unit": "pieces", "min_stock": 25, "max_stock": 250, "current": 125, "cost": "2.15", "supplier": "IVSupply", "location": "Emergency Cart"},
            {"item_code": "EMR003", "name": "Saline Solution 0.9%", "category": iv_supplies, "description": "Normal saline 1000ml bags", "unit": "bags", "min_stock": 50, "max_stock": 500, "current": 275, "cost": "4.25", "supplier": "FluidMed", "location": "IV Storage"},
            {"item_code": "EMR004", "name": "Epinephrine 1:1000", "category": emergency_supplies, "description": "Emergency epinephrine injection", "unit": "vials", "min_stock": 10, "max_stock": 100, "current": 45, "cost": "25.75", "supplier": "EmergencyMeds", "expiry": date(2024, 10, 15), "location": "Emergency Cart"},
            {"item_code": "EMR005", "name": "Oxygen Masks", "category": respiratory_supplies, "description": "Non-rebreather oxygen masks", "unit": "pieces", "min_stock": 20, "max_stock": 200, "current": 95, "cost": "3.85", "supplier": "OxygenSupply", "location": "Respiratory Storage"},
            
            # Diagnostic Supplies
            {"item_code": "DIA001", "name": "Blood Collection Tubes", "category": laboratory_supplies, "description": "Vacutainer blood collection tubes", "unit": "pieces", "min_stock": 100, "max_stock": 1000, "current": 575, "cost": "0.85", "supplier": "LabSupply", "expiry": date(2025, 7, 20), "location": "Lab Storage"},
            {"item_code": "DIA002", "name": "Urine Collection Cups", "category": laboratory_supplies, "description": "Sterile urine collection containers", "unit": "pieces", "min_stock": 50, "max_stock": 500, "current": 225, "cost": "0.65", "supplier": "LabSupply", "location": "Lab Storage"},
            {"item_code": "DIA003", "name": "ECG Electrodes", "category": diagnostic_supplies, "description": "Disposable ECG electrodes", "unit": "packages", "min_stock": 30, "max_stock": 300, "current": 165, "cost": "12.25", "supplier": "CardioSupply", "location": "Cardiology Storage"},
            {"item_code": "DIA004", "name": "X-Ray Film", "category": diagnostic_supplies, "description": "Medical X-ray film", "unit": "boxes", "min_stock": 10, "max_stock": 100, "current": 45, "cost": "85.50", "supplier": "ImagingSupply", "expiry": date(2025, 4, 30), "location": "Radiology Storage"},
            {"item_code": "DIA005", "name": "Contrast Media", "category": diagnostic_supplies, "description": "Iodinated contrast media", "unit": "vials", "min_stock": 15, "max_stock": 150, "current": 75, "cost": "45.75", "supplier": "ContrastCorp", "expiry": date(2024, 11, 18), "location": "Radiology Storage"},
            
            # Respiratory Supplies
            {"item_code": "RES001", "name": "Nasal Cannulas", "category": respiratory_supplies, "description": "Adult nasal cannulas", "unit": "pieces", "min_stock": 30, "max_stock": 300, "current": 185, "cost": "2.45", "supplier": "RespiratoryMax", "location": "Respiratory Storage"},
            {"item_code": "RES002", "name": "Nebulizer Masks", "category": respiratory_supplies, "description": "Pediatric and adult nebulizer masks", "unit": "pieces", "min_stock": 25, "max_stock": 250, "current": 115, "cost": "4.85", "supplier": "NebulizerCorp", "location": "Respiratory Storage"},
            {"item_code": "RES003", "name": "Ventilator Circuits", "category": respiratory_supplies, "description": "Single-use ventilator circuits", "unit": "pieces", "min_stock": 20, "max_stock": 200, "current": 85, "cost": "35.50", "supplier": "VentSupply", "location": "ICU Storage"},
            
            # Wound Care
            {"item_code": "WND001", "name": "Hydrocolloid Dressings", "category": wound_care, "description": "Advanced wound dressings", "unit": "pieces", "min_stock": 20, "max_stock": 200, "current": 95, "cost": "8.75", "supplier": "WoundHeal", "location": "Wound Care Storage"},
            {"item_code": "WND002", "name": "Antiseptic Solution", "category": wound_care, "description": "Povidone iodine solution", "unit": "bottles", "min_stock": 15, "max_stock": 150, "current": 65, "cost": "6.25", "supplier": "AntisepticCorp", "expiry": date(2025, 2, 28), "location": "Wound Care Storage"},
            {"item_code": "WND003", "name": "Compression Bandages", "category": wound_care, "description": "Elastic compression bandages", "unit": "rolls", "min_stock": 25, "max_stock": 250, "current": 135, "cost": "4.15", "supplier": "BandagePlus", "location": "Wound Care Storage"}
        ]
        
        all_supplies = []
        for supply_data in supplies_data:
            supply = Supply(
                item_code=supply_data["item_code"],
                name=supply_data["name"],
                category_id=supply_data["category"].id,
                description=supply_data["description"],
                unit_of_measure=supply_data["unit"],
                minimum_stock_level=supply_data["min_stock"],
                maximum_stock_level=supply_data["max_stock"],
                current_stock=supply_data["current"],
                unit_cost=Decimal(supply_data["cost"]),
                supplier=supply_data["supplier"],
                expiry_date=supply_data.get("expiry"),
                location=supply_data["location"]
            )
            all_supplies.append(supply)
        
        db.add_all(all_supplies)
        db.commit()
        for supply in all_supplies:
            db.refresh(supply)
        
        # Store specific supplies for later reference
        aspirin = all_supplies[0]
        morphine = all_supplies[1]
        syringes = all_supplies[10]
        gauze = all_supplies[11]
        
        # === STEP 11: Create Inventory Transactions (Depends on Supplies and Users) ===
        print("11. Creating inventory transactions...")
        
        transactions = []
        
        # Create multiple transactions for different supplies
        for i, supply in enumerate(all_supplies[:20]):  # First 20 supplies
            # Incoming stock transactions
            in_transaction = InventoryTransaction(
                supply_id=supply.id,
                transaction_type="in",
                quantity=random.randint(50, 200),
                unit_cost=supply.unit_cost,
                total_cost=supply.unit_cost * random.randint(50, 200),
                reference_number=f"PO2024{i+1:03d}",
                notes=f"Monthly restock for {supply.name}",
                performed_by=random.choice([admin_user.id, admin_user_2.id, pharmacist_user_1.id])
            )
            transactions.append(in_transaction)
            
            # Outgoing stock transactions
            if i % 3 == 0:  # Every third supply gets an outgoing transaction
                out_transaction = InventoryTransaction(
                    supply_id=supply.id,
                    transaction_type="out",
                    quantity=random.randint(5, 50),
                    unit_cost=supply.unit_cost,
                    total_cost=supply.unit_cost * random.randint(5, 50),
                    reference_number=f"REQ2024{i+1:03d}",
                    notes=f"Department usage for {supply.name}",
                    performed_by=random.choice([nurse_user_1.id, nurse_user_2.id, pharmacist_user_2.id])
                )
                transactions.append(out_transaction)
            
            # Adjustment transactions
            if i % 5 == 0:  # Every fifth supply gets an adjustment
                adj_transaction = InventoryTransaction(
                    supply_id=supply.id,
                    transaction_type="adjustment",
                    quantity=random.randint(-10, 10),
                    unit_cost=supply.unit_cost,
                    total_cost=supply.unit_cost * random.randint(-10, 10),
                    reference_number=f"ADJ2024{i+1:03d}",
                    notes=f"Inventory adjustment for {supply.name}",
                    performed_by=random.choice([admin_user.id, pharmacist_user_1.id])
                )
                transactions.append(adj_transaction)
        
        db.add_all(transactions)
        db.commit()
        
        # === STEP 12: Create Meetings (Depends on Users and Departments) ===
        print("12. Creating meetings...")
        
        meetings_data = [
            {
                "title": "Weekly Cardiology Department Meeting",
                "description": "Weekly cardiology department meeting to discuss patient cases and department updates",
                "datetime": datetime(2024, 9, 20, 15, 0),
                "duration": 60,
                "location": "Conference Room A",
                "organizer": manager_user,
                "department": cardiology_dept,
                "type": "department",
                "priority": "normal",
                "agenda": "Discuss patient cases, equipment updates, staffing schedule"
            },
            {
                "title": "Emergency Protocol Review",
                "description": "Monthly review of emergency protocols and procedures",
                "datetime": datetime(2024, 9, 21, 11, 0),
                "duration": 90,
                "location": "Emergency Conference Room",
                "organizer": doctor_user_2,
                "department": emergency_dept,
                "type": "training",
                "priority": "high",
                "agenda": "Update on new emergency protocols, code blue procedures"
            },
            {
                "title": "ICU Staff Training Session",
                "description": "Training session for new ICU equipment and procedures",
                "datetime": datetime(2024, 9, 22, 14, 0),
                "duration": 120,
                "location": "ICU Training Room",
                "organizer": doctor_user_3,
                "department": icu_dept,
                "type": "training",
                "priority": "high",
                "agenda": "New ventilator training, patient monitoring protocols"
            },
            {
                "title": "Surgical Department Planning Meeting",
                "description": "Monthly planning meeting for surgical schedules and resource allocation",
                "datetime": datetime(2024, 9, 23, 10, 0),
                "duration": 75,
                "location": "Surgical Conference Room",
                "organizer": doctor_user_4,
                "department": surgery_dept,
                "type": "planning",
                "priority": "normal",
                "agenda": "Schedule planning, equipment maintenance, staffing allocation"
            },
            {
                "title": "Pediatrics Case Review",
                "description": "Weekly case review for pediatric patients",
                "datetime": datetime(2024, 9, 24, 13, 0),
                "duration": 45,
                "location": "Pediatrics Meeting Room",
                "organizer": doctor_user_6,
                "department": pediatrics_dept,
                "type": "case_review",
                "priority": "normal",
                "agenda": "Patient case discussions, treatment protocols"
            },
            {
                "title": "Neurology Grand Rounds",
                "description": "Weekly neurology grand rounds presentation",
                "datetime": datetime(2024, 9, 25, 16, 0),
                "duration": 60,
                "location": "Main Auditorium",
                "organizer": doctor_user_7,
                "department": neurology_dept,
                "type": "education",
                "priority": "normal",
                "agenda": "Case presentations, latest research findings"
            },
            {
                "title": "Oncology Multidisciplinary Team Meeting",
                "description": "Weekly MDT meeting to discuss cancer patient treatment plans",
                "datetime": datetime(2024, 9, 26, 12, 0),
                "duration": 90,
                "location": "Oncology Conference Room",
                "organizer": doctor_user_8,
                "department": oncology_dept,
                "type": "multidisciplinary",
                "priority": "high",
                "agenda": "Patient treatment planning, multidisciplinary case discussions"
            },
            {
                "title": "Hospital Safety Committee Meeting",
                "description": "Monthly hospital safety and quality improvement meeting",
                "datetime": datetime(2024, 9, 27, 9, 0),
                "duration": 120,
                "location": "Main Conference Room",
                "organizer": admin_user,
                "department": None,
                "type": "committee",
                "priority": "high",
                "agenda": "Safety incidents review, quality improvement initiatives"
            },
            {
                "title": "Pharmacy and Therapeutics Committee",
                "description": "Monthly P&T committee meeting",
                "datetime": datetime(2024, 9, 28, 14, 30),
                "duration": 90,
                "location": "Pharmacy Conference Room",
                "organizer": pharmacist_user_1,
                "department": pharmacy_dept,
                "type": "committee",
                "priority": "normal",
                "agenda": "Drug formulary review, medication safety updates"
            },
            {
                "title": "Infection Control Committee Meeting",
                "description": "Monthly infection control and prevention meeting",
                "datetime": datetime(2024, 9, 29, 11, 30),
                "duration": 60,
                "location": "Administration Conference Room",
                "organizer": manager_user_2,
                "department": None,
                "type": "committee",
                "priority": "high",
                "agenda": "Infection control protocols, outbreak prevention strategies"
            }
        ]
        
        all_meetings = []
        for meeting_data in meetings_data:
            meeting = Meeting(
                title=meeting_data["title"],
                description=meeting_data["description"],
                meeting_datetime=meeting_data["datetime"],
                duration_minutes=meeting_data["duration"],
                location=meeting_data["location"],
                google_meet_link=f"https://meet.google.com/{random.randint(100000, 999999)}-{random.randint(1000, 9999)}-{random.randint(100, 999)}",
                organizer_id=meeting_data["organizer"].id,
                department_id=meeting_data["department"].id if meeting_data["department"] else None,
                meeting_type=meeting_data["type"],
                status="scheduled",
                priority=meeting_data["priority"],
                agenda=meeting_data["agenda"]
            )
            all_meetings.append(meeting)
        
        db.add_all(all_meetings)
        db.commit()
        for meeting in all_meetings:
            db.refresh(meeting)
        
        # === STEP 14: Create Meeting Participants (Depends on Meetings and Staff) ===
        print("14. Creating meeting participants...")
        
        participants = []
        
        # Create participants for each meeting
        for i, meeting in enumerate(all_meetings):
            # Add organizer as participant
            organizer_staff = next((s for s in all_staff if s.user_id == meeting.organizer_id), None)
            if organizer_staff:
                participant = MeetingParticipant(
                    meeting_id=meeting.id,
                    staff_id=organizer_staff.id,
                    attendance_status="confirmed"
                )
                participants.append(participant)
            
            # Add 2-5 random staff members from the same department or related departments
            num_participants = random.randint(2, 5)
            department_staff = [s for s in all_staff if s.department_id == meeting.department_id] if meeting.department_id else all_staff
            
            if len(department_staff) > 1:
                selected_staff = random.sample(department_staff, min(num_participants, len(department_staff)))
                for staff_member in selected_staff:
                    if staff_member.id != (organizer_staff.id if organizer_staff else None):
                        participant = MeetingParticipant(
                            meeting_id=meeting.id,
                            staff_id=staff_member.id,
                            attendance_status=random.choice(["confirmed", "pending", "declined", "tentative"])
                        )
                        participants.append(participant)
        
        db.add_all(participants)
        db.commit()
        
        # === STEP 15: Create Medical Documents (Depends on Patients) ===
        print("15. Creating medical documents...")
        
        medical_docs = []
        
        # Create multiple documents for different patients
        doc_types = ["prescription", "lab_result", "imaging", "discharge_summary", "consultation", "procedure_note"]
        
        for i, patient in enumerate(all_patients[:15]):  # First 15 patients get documents
            num_docs = random.randint(1, 4)  # Each patient gets 1-4 documents
            
            for doc_num in range(num_docs):
                doc_type = random.choice(doc_types)
                
                doc = MedicalDocument(
                    patient_id=patient.id,
                    document_type=doc_type,
                    file_name=f"{doc_type}_{patient.patient_number}_{doc_num+1:03d}.pdf",
                    file_path=f"/medical_docs/{doc_type}s/{doc_type}_{patient.patient_number}_{doc_num+1:03d}.pdf",
                    file_size=random.randint(50000, 500000),
                    mime_type="application/pdf",
                    extracted_text=f"Patient: {patient.first_name} {patient.last_name}. Document type: {doc_type}. Medical content extracted...",
                    processing_status="completed",
                    confidence_score=Decimal(f"0.{random.randint(85, 99)}")
                )
                medical_docs.append(doc)
        
        db.add_all(medical_docs)
        db.commit()
        for doc in medical_docs:
            db.refresh(doc)
        
        # === STEP 16: Create Extracted Medical Data (Depends on Documents and Patients) ===
        print("16. Creating extracted medical data...")
        
        extracted_data_list = []
        data_types = ["medication", "condition", "procedure", "allergy", "vital_sign", "lab_result"]
        
        for doc in medical_docs[:20]:  # First 20 documents get extracted data
            num_extractions = random.randint(1, 3)  # Each document gets 1-3 extractions
            
            for ext_num in range(num_extractions):
                data_type = random.choice(data_types)
                
                # Generate realistic entity names based on type
                entity_names = {
                    "medication": ["Lisinopril", "Metformin", "Aspirin", "Ibuprofen", "Amoxicillin"],
                    "condition": ["Hypertension", "Diabetes", "Asthma", "Heart Disease", "Arthritis"],
                    "procedure": ["Blood Draw", "X-Ray", "ECG", "CT Scan", "Ultrasound"],
                    "allergy": ["Penicillin", "Shellfish", "Nuts", "Latex", "Sulfa"],
                    "vital_sign": ["Blood Pressure", "Heart Rate", "Temperature", "Oxygen Saturation"],
                    "lab_result": ["Blood Glucose", "Hemoglobin A1c", "Cholesterol", "Creatinine"]
                }
                
                entity_name = random.choice(entity_names.get(data_type, ["Unknown"]))
                
                extracted_data = ExtractedMedicalData(
                    document_id=doc.id,
                    patient_id=doc.patient_id,
                    data_type=data_type,
                    entity_name=entity_name,
                    entity_value=f"{random.randint(10, 200)}" if data_type in ["vital_sign", "lab_result"] else None,
                    entity_unit="mg/dL" if data_type == "lab_result" else "mg" if data_type == "medication" else None,
                    date_recorded=date.today() - timedelta(days=random.randint(1, 30)),
                    doctor_name=f"Dr. {random.choice(['Smith', 'Johnson', 'Brown', 'Davis', 'Wilson'])}",
                    hospital_name="General Hospital",
                    department_name=random.choice(["Cardiology", "Emergency", "Internal Medicine", "Surgery"]),
                    extraction_confidence=Decimal(f"0.{random.randint(85, 99)}"),
                    extraction_method="AI_PARSING",
                    verified=random.choice([True, False])
                )
                extracted_data_list.append(extracted_data)
        
        db.add_all(extracted_data_list)
        db.commit()
        
        # === STEP 17: Create Discharge Reports (Depends on Patients, Beds, Users) ===
        print("17. Creating discharge reports...")
        discharge_report1 = DischargeReport(
            patient_id=patient1.id,
            bed_id=bed301a.id,
            generated_by=doctor_user_1.id,
            report_number="DR-20240818-ABC12345",
            admission_date=datetime.now() - timedelta(days=3),
            discharge_date=datetime.now(),
            length_of_stay_days=3,
            patient_summary='{"age": 39, "gender": "female", "condition": "stable"}',
            treatment_summary='{"treatments": ["medication", "monitoring"]}',
            equipment_summary='{"equipment_used": ["ECG Machine"]}',
            staff_summary='{"primary_doctor": "Dr. Smith", "nurses": ["Nurse Brown"]}',
            medications='{"discharge_meds": ["Lisinopril 10mg daily"]}',
            procedures='{"procedures": ["ECG monitoring"]}',
            discharge_instructions="Continue medication as prescribed. Follow up in 2 weeks.",
            follow_up_required="Cardiology follow-up in 2 weeks",
            discharge_condition="stable",
            discharge_destination="home"
        )
        
        db.add(discharge_report1)
        db.commit()
        
        # === STEP 18: Create Patient Queue (Depends on Patients, Departments, Beds, Users) ===
        print("18. Creating patient queue...")
        
        # Find available ICU bed for reference
        available_icu_bed = next((b for b in all_beds if b.bed_type == "icu" and b.status == "available"), all_beds[0])
        
        queue_entry1 = PatientQueue(
            patient_id=patient3.id,
            department_id=icu_dept.id,
            queue_position=1,
            bed_type_required="icu",
            priority_level="high",
            admission_type="emergency",
            estimated_wait_time=30,
            target_bed_id=available_icu_bed.id,
            medical_condition="Respiratory distress",
            special_requirements='{"ventilator": true, "isolation": false}',
            doctor_id=doctor_user_2.id,
            status="waiting"
        )
        
        # Create more queue entries
        queue_entries = [queue_entry1]
        
        for i in range(2, 8):  # Create 6 more queue entries
            if i < len(all_patients):
                available_bed = next((b for b in all_beds if b.status == "available"), all_beds[0])
                queue_entry = PatientQueue(
                    patient_id=all_patients[i].id,
                    department_id=random.choice(all_departments).id,
                    queue_position=i,
                    bed_type_required=random.choice(["standard", "icu", "emergency"]),
                    priority_level=random.choice(["low", "normal", "high", "urgent"]),
                    admission_type=random.choice(["scheduled", "emergency", "transfer"]),
                    estimated_wait_time=random.randint(15, 120),
                    target_bed_id=available_bed.id,
                    medical_condition=random.choice(["Chest pain", "Shortness of breath", "Abdominal pain", "Fever", "Headache"]),
                    special_requirements='{"isolation": false}',
                    doctor_id=random.choice([doctor_user_1.id, doctor_user_2.id, doctor_user_3.id]),
                    status="waiting"
                )
                queue_entries.append(queue_entry)
        
        db.add_all(queue_entries)
        db.commit()
        
        # === STEP 19: Create Bed Turnover Records (Depends on Beds, Patients, Users) ===
        print("19. Creating bed turnover records...")
        bed_turnover1 = BedTurnover(
            bed_id=bed301a.id,
            previous_patient_id=patient1.id,
            status="cleaning",
            turnover_type="standard",
            discharge_time=datetime.now() - timedelta(hours=2),
            cleaning_start_time=datetime.now() - timedelta(hours=1),
            estimated_cleaning_duration=45,
            assigned_cleaner_id=cleaner_user.id,
            equipment_requiring_cleaning='["EQ001"]',
            cleaning_checklist='{"bed_sheets": false, "surfaces": false, "equipment": false}',
            priority_level="normal",
            notes="Standard cleaning after discharge"
        )
        
        db.add(bed_turnover1)
        db.commit()
        db.refresh(bed_turnover1)
        
        # === STEP 20: Create Equipment Turnover (Depends on Bed Turnover and Equipment) ===
        print("20. Creating equipment turnover...")
        equipment_turnover1 = EquipmentTurnover(
            bed_turnover_id=bed_turnover1.id,
            equipment_id=ecg_machine.id,
            status="needs_cleaning",
            cleaning_required=True,
            cleaning_type="surface",
            release_time=datetime.now() - timedelta(hours=2),
            released_by_staff_id=nurse_user_1.id,
            cleaning_checklist='{"surface_cleaning": false, "calibration": false}',
            notes="ECG machine needs cleaning after patient use"
        )
        
        db.add(equipment_turnover1)
        db.commit()
        
        # === STEP 21: Create Agent Interactions (Depends on Users) ===
        print("21. Creating agent interactions...")
        
        agent_interactions = []
        agent_types = ["bed_management", "equipment_tracker", "supply_inventory", "staff_allocation", "patient_scheduling"]
        
        # Create 50 diverse agent interactions
        for i in range(50):
            agent_type = random.choice(agent_types)
            user = random.choice(all_users[:20])  # Use first 20 users
            
            # Generate realistic queries and responses based on agent type
            queries_responses = {
                "bed_management": [
                    ("Find available beds in ICU", "Found 3 available ICU beds: 401B, 402A, 403C"),
                    ("Check bed occupancy status", "Current occupancy: 85% (127/150 beds occupied)"),
                    ("Reserve bed for incoming patient", "Bed 302A reserved for patient admission"),
                    ("Update bed status to maintenance", "Bed 101C status updated to maintenance mode")
                ],
                "equipment_tracker": [
                    ("Locate ventilator VT001", "Ventilator VT001 is in Room 401, currently in use"),
                    ("Check ECG machine availability", "3 ECG machines available in Cardiology wing"),
                    ("Schedule equipment maintenance", "Maintenance scheduled for Equipment EQ015 on 2024-09-15"),
                    ("Equipment usage report", "Generated usage report for monitoring equipment")
                ],
                "supply_inventory": [
                    ("Check morphine stock levels", "Morphine 10mg/ml: 45 vials (Normal stock level)"),
                    ("Low stock alert for syringes", "Alert: Disposable syringes below minimum threshold (25/50)"),
                    ("Order medical supplies", "Purchase order created for medical supplies restock"),
                    ("Medication expiry check", "5 medications expiring within 30 days identified")
                ],
                "staff_allocation": [
                    ("Find available nurses for night shift", "2 nurses available for night shift assignment"),
                    ("Check doctor on-call schedule", "Dr. Smith is on-call for Cardiology until 8 AM"),
                    ("Staff scheduling conflict", "Scheduling conflict resolved for nurse rotation"),
                    ("Coverage request for emergency", "Emergency coverage assigned to Dr. Johnson")
                ],
                "patient_scheduling": [
                    ("Schedule patient for surgery", "Surgery scheduled for Patient P003 on 2024-09-20"),
                    ("Check appointment availability", "3 appointment slots available for cardiology"),
                    ("Patient transfer request", "Transfer approved from Emergency to ICU"),
                    ("Discharge planning", "Discharge plan initiated for Patient P001")
                ]
            }
            
            query, response = random.choice(queries_responses[agent_type])
            
            interaction = AgentInteraction(
                agent_type=agent_type,
                user_id=user.id,
                query=query,
                response=response,
                action_taken=agent_type.replace("_", " "),
                confidence_score=Decimal(f"0.{random.randint(85, 99)}"),
                execution_time_ms=random.randint(50, 500)
            )
            agent_interactions.append(interaction)
        
        db.add_all(agent_interactions)
        db.commit()
        
        # === STEP 22: Create Legacy Users (For backward compatibility) ===
        print("22. Creating legacy users...")
        legacy_users = []
        for i in range(10):
            legacy_user = LegacyUser(
                name=f"Legacy User {i+1}",
                email=f"legacy.user{i+1}@hospital.com",
                address=f"{100+i} Legacy Street, City, State",
                phone=f"555-90{i+10:02d}"
            )
            legacy_users.append(legacy_user)
        
        db.add_all(legacy_users)
        db.commit()
        
        # 23. Creating patient supply usage (medications and treatments)
        print("23. Creating patient supply usage records...")
        
        patient_supply_usages = []
        
        # Create realistic medication/supply usage for each patient
        for i, patient in enumerate(patients):
            # Each patient gets 2-5 supply usage records
            num_usages = random.randint(2, 5)
            
            for j in range(num_usages):
                # Select appropriate supplies based on patient condition
                supply = random.choice(supplies)
                doctor = random.choice([u for u in users if 'doctor' in u.role.lower()])
                nurse = random.choice([u for u in users if 'nurse' in u.role.lower()])
                patient_bed = random.choice([b for b in beds if b.patient_id == patient.id])
                
                # Create realistic usage dates
                prescribed_date = datetime.now() - timedelta(days=random.randint(1, 30))
                admin_date = prescribed_date + timedelta(hours=random.randint(1, 24))
                
                usage = PatientSupplyUsage(
                    id=uuid.uuid4(),
                    patient_id=patient.id,
                    supply_id=supply.id,
                    quantity_used=random.randint(1, 10),
                    unit_cost=supply.unit_cost,
                    total_cost=supply.unit_cost * random.randint(1, 10),
                    prescribed_by_id=doctor.id,
                    administered_by_id=nurse.id,
                    bed_id=patient_bed.id if patient_bed else None,
                    dosage=random.choice(["250mg", "500mg", "1g", "2 tablets", "5ml", "10ml"]),
                    frequency=random.choice(["Once daily", "Twice daily", "Three times daily", "As needed", "Every 6 hours"]),
                    administration_route=random.choice(["Oral", "IV", "Injection", "Topical", "Inhalation"]),
                    indication=random.choice(["Pain management", "Infection treatment", "Blood pressure", "Diabetes", "Wound care"]),
                    prescribed_date=prescribed_date,
                    administration_date=admin_date,
                    start_date=prescribed_date.date(),
                    end_date=(prescribed_date + timedelta(days=random.randint(3, 14))).date(),
                    status=random.choice(["prescribed", "administered", "completed"]),
                    effectiveness=random.choice(["effective", "partial", "effective"]),  # Weighted toward effective
                    billed=random.choice([True, False]),
                    insurance_covered=random.choice([True, True, True, False])  # Mostly covered
                )
                patient_supply_usages.append(usage)
        
        db.add_all(patient_supply_usages)
        db.commit()
        
        # 24. Creating document embeddings for RAG system
        print("24. Creating document embeddings...")
        
        document_embeddings = []
        
        for doc in medical_documents:
            # Create 2-4 chunks per document
            num_chunks = random.randint(2, 4)
            
            for chunk_idx in range(num_chunks):
                embedding = DocumentEmbedding(
                    id=uuid.uuid4(),
                    document_id=doc.id,
                    patient_id=doc.patient_id,
                    chunk_text=f"Medical document chunk {chunk_idx + 1} for {doc.document_type}. Contains relevant clinical information and treatment details.",
                    chunk_index=chunk_idx,
                    embedding_vector=f"[{', '.join([str(random.uniform(-1, 1)) for _ in range(384)])}]"  # Mock embedding vector
                )
                document_embeddings.append(embedding)
        
        db.add_all(document_embeddings)
        db.commit()
        
        # 25. Creating bed equipment assignments
        print("25. Creating bed equipment assignments...")
        
        bed_equipment_assignments = []
        
        for bed in beds:
            if bed.status == "occupied" and bed.patient_id:
                # Assign 1-3 pieces of equipment to occupied beds
                num_assignments = random.randint(1, 3)
                assigned_equipment = random.sample([e for e in equipment if e.status == "available"], 
                                                 min(num_assignments, len([e for e in equipment if e.status == "available"])))
                
                for eq in assigned_equipment:
                    assignment = BedEquipmentAssignment(
                        id=uuid.uuid4(),
                        bed_id=bed.id,
                        equipment_id=eq.id,
                        patient_id=bed.patient_id,
                        assigned_at=datetime.now() - timedelta(days=random.randint(1, 10)),
                        status=random.choice(["assigned", "in_use"]),
                        assigned_by_staff_id=random.choice(staff).id,
                        notes=f"Equipment assigned for patient care in {bed.bed_number}"
                    )
                    bed_equipment_assignments.append(assignment)
        
        db.add_all(bed_equipment_assignments)
        db.commit()
        
        # 26. Creating bed staff assignments
        print("26. Creating bed staff assignments...")
        
        bed_staff_assignments = []
        
        for bed in beds:
            if bed.status == "occupied" and bed.patient_id:
                # Assign 2-4 staff members to each occupied bed
                assigned_staff = random.sample(staff, min(random.randint(2, 4), len(staff)))
                
                for idx, staff_member in enumerate(assigned_staff):
                    assignment_type = ["primary_nurse", "secondary_nurse", "attending_doctor", "resident"][idx] if idx < 4 else "support_staff"
                    
                    assignment = BedStaffAssignment(
                        id=uuid.uuid4(),
                        bed_id=bed.id,
                        staff_id=staff_member.id,
                        patient_id=bed.patient_id,
                        assignment_type=assignment_type,
                        assigned_at=datetime.now() - timedelta(days=random.randint(1, 10)),
                        status="active",
                        shift_type=random.choice(["day", "night", "evening"])
                    )
                    bed_staff_assignments.append(assignment)
        
        db.add_all(bed_staff_assignments)
        db.commit()
        
        # 27. Creating equipment usage records
        print("27. Creating equipment usage records...")
        
        equipment_usages = []
        
        for eq in equipment:
            if eq.status in ["in_use", "maintenance"]:
                # Create 1-3 usage records per equipment
                num_usages = random.randint(1, 3)
                
                for _ in range(num_usages):
                    usage = EquipmentUsage(
                        id=uuid.uuid4(),
                        equipment_id=eq.id,
                        patient_id=random.choice(patients).id,
                        staff_id=random.choice(staff).id,
                        usage_start=datetime.now() - timedelta(days=random.randint(1, 30)),
                        usage_end=datetime.now() - timedelta(days=random.randint(0, 5)),
                        purpose=random.choice(["Patient monitoring", "Treatment", "Diagnostics", "Life support"]),
                        notes=f"Equipment used for {random.choice(['vital signs monitoring', 'patient treatment', 'diagnostic procedures'])}"
                    )
                    equipment_usages.append(usage)
        
        db.add_all(equipment_usages)
        db.commit()
        
        # 28. Creating staff assignments
        print("28. Creating staff assignments...")
        
        staff_assignments = []
        
        for staff_member in staff:
            # Create 1-2 current assignments per staff member
            num_assignments = random.randint(1, 2)
            
            for _ in range(num_assignments):
                assignment = StaffAssignment(
                    id=uuid.uuid4(),
                    staff_id=staff_member.id,
                    department_id=staff_member.department_id,
                    patient_id=random.choice(patients).id,
                    assignment_type=random.choice(["primary_care", "secondary_care", "consultation", "monitoring"]),
                    assigned_at=datetime.now() - timedelta(days=random.randint(1, 7)),
                    status="active",
                    shift_type=random.choice(["day", "night", "evening"]),
                    notes=f"Staff assignment for {staff_member.specialization} duties"
                )
                staff_assignments.append(assignment)
        
        db.add_all(staff_assignments)
        db.commit()
        
        # 29. Creating staff interactions
        print("29. Creating staff interactions...")
        
        staff_interactions = []
        
        # Create 30 staff interactions
        for i in range(30):
            interaction = StaffInteraction(
                id=uuid.uuid4(),
                primary_staff_id=random.choice(staff).id,
                secondary_staff_id=random.choice(staff).id,
                patient_id=random.choice(patients).id,
                interaction_type=random.choice(["consultation", "handoff", "collaboration", "emergency_response"]),
                interaction_date=datetime.now() - timedelta(days=random.randint(1, 30)),
                duration_minutes=random.randint(5, 60),
                notes=f"Staff interaction regarding patient care coordination and treatment planning.",
                outcome=random.choice(["resolved", "referred", "ongoing", "escalated"])
            )
            staff_interactions.append(interaction)
        
        db.add_all(staff_interactions)
        db.commit()
        
        # 30. Creating staff meetings
        print("30. Creating staff meetings...")
        
        staff_meetings = []
        
        # Create 8 staff meetings
        for i in range(8):
            meeting = StaffMeeting(
                id=uuid.uuid4(),
                title=f"Department Meeting #{i+1}",
                description=f"Regular departmental meeting for {random.choice(['clinical updates', 'policy review', 'case discussions', 'training session'])}",
                meeting_date=datetime.now() + timedelta(days=random.randint(1, 30)),
                duration_minutes=random.randint(30, 120),
                department_id=random.choice(departments).id,
                organizer_staff_id=random.choice(staff).id,
                meeting_type=random.choice(["departmental", "clinical_review", "training", "emergency"]),
                location=f"Conference Room {chr(65 + i)}"
            )
            staff_meetings.append(meeting)
        
        db.add_all(staff_meetings)
        db.commit()
        
        # 31. Creating staff meeting participants
        print("31. Creating staff meeting participants...")
        
        staff_meeting_participants = []
        
        for meeting in staff_meetings:
            # Each meeting has 3-8 participants
            num_participants = random.randint(3, 8)
            participants = random.sample(staff, min(num_participants, len(staff)))
            
            for participant in participants:
                participant_record = StaffMeetingParticipant(
                    id=uuid.uuid4(),
                    meeting_id=meeting.id,
                    staff_id=participant.id,
                    attendance_status=random.choice(["confirmed", "tentative", "declined"]),
                    role=random.choice(["presenter", "attendee", "facilitator"])
                )
                staff_meeting_participants.append(participant_record)
        
        db.add_all(staff_meeting_participants)
        db.commit()
        
        # 32. Creating treatment records
        print("32. Creating treatment records...")
        
        treatment_records = []
        
        # Create 40 treatment records
        for i in range(40):
            treatment = TreatmentRecord(
                id=uuid.uuid4(),
                patient_id=random.choice(patients).id,
                staff_id=random.choice(staff).id,
                treatment_type=random.choice(["medication", "procedure", "therapy", "surgery", "consultation"]),
                treatment_name=f"Treatment {i+1}",
                treatment_description=f"Comprehensive treatment for {random.choice(['acute condition', 'chronic management', 'preventive care', 'emergency intervention'])}",
                treatment_date=datetime.now() - timedelta(days=random.randint(1, 30)),
                duration_minutes=random.randint(15, 180),
                outcome=random.choice(["successful", "improved", "stable", "requires_followup"]),
                notes=f"Treatment administered with appropriate clinical protocols and patient monitoring.",
                cost=Decimal(str(random.uniform(100, 5000)))
            )
            treatment_records.append(treatment)
        
        db.add_all(treatment_records)
        db.commit()
        
        # 33. Creating bed turnover logs (detailed turnover tracking)
        print("33. Creating bed turnover logs...")
        
        bed_turnover_logs = []
        
        # Create 15 detailed bed turnover logs
        for i in range(15):
            bed = random.choice(beds)
            prev_patient = random.choice(patients)
            next_patient = random.choice(patients)
            
            discharge_time = datetime.now() - timedelta(days=random.randint(1, 30))
            
            turnover_log = BedTurnoverLog(
                id=uuid.uuid4(),
                bed_id=bed.id,
                previous_patient_id=prev_patient.id,
                next_patient_id=next_patient.id,
                discharge_started_at=discharge_time,
                discharge_completed_at=discharge_time + timedelta(minutes=random.randint(30, 90)),
                cleaning_started_at=discharge_time + timedelta(minutes=random.randint(30, 120)),
                cleaning_expected_duration=random.randint(30, 90),
                cleaning_estimated_completion=discharge_time + timedelta(minutes=random.randint(60, 180)),
                cleaning_actual_completion=discharge_time + timedelta(minutes=random.randint(45, 200)),
                cleaning_status=random.choice(["completed", "in_progress", "pending"]),
                cleaning_assigned_staff_id=random.choice(staff).id,
                cleaning_notes=f"Bed turnover cleaning for {bed.bed_number}",
                equipment_released_at=discharge_time + timedelta(minutes=random.randint(15, 60)),
                equipment_reassigned_at=discharge_time + timedelta(minutes=random.randint(90, 180)),
                staff_released_at=discharge_time + timedelta(minutes=random.randint(10, 45)),
                staff_reassigned_at=discharge_time + timedelta(minutes=random.randint(120, 240)),
                next_patient_assigned_at=discharge_time + timedelta(minutes=random.randint(180, 360)),
                turnover_completed_at=discharge_time + timedelta(minutes=random.randint(240, 480)),
                status=random.choice(["completed", "in_progress", "delayed"]),
                total_turnover_time=random.randint(180, 480),
                delays=f'["{random.choice(["equipment_cleaning", "deep_sanitization", "maintenance_required", "staffing_shortage"])}"]',
                priority=random.choice(["normal", "high", "urgent"])
            )
            bed_turnover_logs.append(turnover_log)
        
        db.add_all(bed_turnover_logs)
        db.commit()
        
        # 34. Creating bed cleaning tasks
        print("34. Creating bed cleaning tasks...")
        
        bed_cleaning_tasks = []
        
        # Create 2-4 cleaning tasks for each turnover log
        for turnover_log in bed_turnover_logs:
            num_tasks = random.randint(2, 4)
            
            task_names = ["Surface disinfection", "Bed linen replacement", "Equipment sanitization", "Floor cleaning", "Bathroom cleaning", "Air filtration check"]
            
            for i in range(num_tasks):
                task_name = random.choice(task_names)
                
                task = BedCleaningTask(
                    id=uuid.uuid4(),
                    turnover_log_id=turnover_log.id,
                    task_name=task_name,
                    task_description=f"Detailed {task_name.lower()} as part of bed turnover process",
                    estimated_duration=random.randint(10, 45),
                    actual_duration=random.randint(8, 60),
                    status=random.choice(["completed", "in_progress", "pending"]),
                    started_at=turnover_log.cleaning_started_at + timedelta(minutes=i*10),
                    completed_at=turnover_log.cleaning_started_at + timedelta(minutes=i*10 + random.randint(10, 45)),
                    assigned_staff_id=random.choice(staff).id,
                    quality_check_passed=random.choice([True, True, True, False]),  # Mostly pass
                    notes=f"Task {task_name} completed according to hospital cleaning protocols"
                )
                bed_cleaning_tasks.append(task)
        
        db.add_all(bed_cleaning_tasks)
        db.commit()
        
        print("✅ Comprehensive sample data created successfully!")
        
        # Print detailed summary
        print("\n📊 Database Summary:")
        print(f"Users: {db.query(User).count()}")
        print(f"Departments: {db.query(Department).count()}")
        print(f"Staff: {db.query(Staff).count()}")
        print(f"Patients: {db.query(Patient).count()}")
        print(f"Rooms: {db.query(Room).count()}")
        print(f"Beds: {db.query(Bed).count()}")
        print(f"Equipment Categories: {db.query(EquipmentCategory).count()}")
        print(f"Equipment: {db.query(Equipment).count()}")
        print(f"Supply Categories: {db.query(SupplyCategory).count()}")
        print(f"Supplies: {db.query(Supply).count()}")
        print(f"Inventory Transactions: {db.query(InventoryTransaction).count()}")
        print(f"Meetings: {db.query(Meeting).count()}")
        print(f"Meeting Participants: {db.query(MeetingParticipant).count()}")
        print(f"Medical Documents: {db.query(MedicalDocument).count()}")
        print(f"Extracted Medical Data: {db.query(ExtractedMedicalData).count()}")
        print(f"Patient Queue: {db.query(PatientQueue).count()}")
        print(f"Agent Interactions: {db.query(AgentInteraction).count()}")
        print(f"Legacy Users: {db.query(LegacyUser).count()}")
        print(f"Discharge Reports: {db.query(DischargeReport).count()}")
        print(f"Bed Turnovers: {db.query(BedTurnover).count()}")
        print(f"Equipment Turnovers: {db.query(EquipmentTurnover).count()}")
        print(f"Patient Supply Usage: {db.query(PatientSupplyUsage).count()}")
        print(f"Document Embeddings: {db.query(DocumentEmbedding).count()}")
        print(f"Bed Equipment Assignments: {db.query(BedEquipmentAssignment).count()}")
        print(f"Bed Staff Assignments: {db.query(BedStaffAssignment).count()}")
        print(f"Equipment Usage: {db.query(EquipmentUsage).count()}")
        print(f"Staff Assignments: {db.query(StaffAssignment).count()}")
        print(f"Staff Interactions: {db.query(StaffInteraction).count()}")
        print(f"Staff Meetings: {db.query(StaffMeeting).count()}")
        print(f"Staff Meeting Participants: {db.query(StaffMeetingParticipant).count()}")
        print(f"Treatment Records: {db.query(TreatmentRecord).count()}")
        print(f"Bed Turnover Logs: {db.query(BedTurnoverLog).count()}")
        print(f"Bed Cleaning Tasks: {db.query(BedCleaningTask).count()}")
        
        print(f"\n📈 Data Statistics:")
        print(f"Total Records Created: {sum([
            db.query(User).count(), db.query(Department).count(), db.query(Staff).count(),
            db.query(Patient).count(), db.query(Room).count(), db.query(Bed).count(),
            db.query(Equipment).count(), db.query(Supply).count(), 
            db.query(InventoryTransaction).count(), db.query(Meeting).count(),
            db.query(MeetingParticipant).count(), db.query(MedicalDocument).count(),
            db.query(ExtractedMedicalData).count(), db.query(PatientQueue).count(),
            db.query(AgentInteraction).count(), db.query(LegacyUser).count(),
            db.query(DischargeReport).count(), db.query(BedTurnover).count(),
            db.query(EquipmentTurnover).count(), db.query(PatientSupplyUsage).count(),
            db.query(DocumentEmbedding).count(), db.query(BedEquipmentAssignment).count(),
            db.query(BedStaffAssignment).count(), db.query(EquipmentUsage).count(),
            db.query(StaffAssignment).count(), db.query(StaffInteraction).count(),
            db.query(StaffMeeting).count(), db.query(StaffMeetingParticipant).count(),
            db.query(TreatmentRecord).count(), db.query(BedTurnoverLog).count(),
            db.query(BedCleaningTask).count()
        ])}")
        
        print(f"\n🏥 Hospital Capacity Overview:")
        occupied_beds = db.query(Bed).filter(Bed.status == "occupied").count()
        total_beds = db.query(Bed).count()
        occupancy_rate = (occupied_beds / total_beds * 100) if total_beds > 0 else 0
        print(f"Bed Occupancy: {occupied_beds}/{total_beds} ({occupancy_rate:.1f}%)")
        print(f"Available Equipment: {db.query(Equipment).filter(Equipment.status == 'available').count()}")
        print(f"Low Stock Supplies: {db.query(Supply).filter(Supply.current_stock <= Supply.minimum_stock_level).count()}")
        
        # Show some sample data
        print(f"\n📋 Sample Data Preview:")
        print(f"Departments: {', '.join([d.name for d in db.query(Department).limit(5)])}")
        print(f"Patient Types: {', '.join(set([p.blood_type for p in db.query(Patient).limit(10) if p.blood_type]))}")
        print(f"Equipment Types: {', '.join(set([e.name for e in db.query(Equipment).limit(8)]))}")
        print(f"Medication Categories: {', '.join([sc.name for sc in db.query(SupplyCategory).filter(SupplyCategory.name.like('%Med%')).limit(3)])}")
        
    except Exception as e:
        print(f"❌ Error creating sample data: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        raise
    finally:
        db.close()

def main():
    """Main function to test database setup."""
    print("🏥 Hospital Management System Database Setup")
    print("=" * 50)
    
    # Test connection
    print("1. Testing database connection...")
    if not test_connection():
        print("❌ Database connection failed. Please check your PostgreSQL setup.")
        return
    
    # Create tables
    print("2. Creating database tables...")
    print("⚠️  This will drop and recreate all tables!")
    
    try:
        create_tables()
        print("✅ Tables created successfully!")
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        print("\n💡 Troubleshooting tips:")
        print("- Make sure PostgreSQL is running")
        print("- Check your DATABASE_URL in .env file")
        print("- Ensure the database 'hospital_management' exists")
        print("- Try creating the database: createdb hospital_management")
        return
    
    # Create sample data
    print("3. Creating sample data...")
    try:
        create_sample_data()
        print("✅ Sample data created successfully!")
    except Exception as e:
        print(f"❌ Error creating sample data: {e}")
        print("⚠️  Continuing without sample data...")
    
    print("\n🎉 Database setup completed successfully!")
    print("\nYou can now:")
    print("- Run the comprehensive_server.py for full CRUD operations")
    print("- Use the MCP tools to interact with all database tables")
    print("- Test the AI agents with the sample data")

if __name__ == "__main__":
    main()
