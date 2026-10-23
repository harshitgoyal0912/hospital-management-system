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
        
        print("1. Creating users...")
        users = []
        
        # Create 30 diverse users with different roles
        roles = ["doctor", "nurse", "admin", "manager", "receptionist", "support_staff"]
        first_names = ["John", "Jane", "Michael", "Sarah", "David", "Emily", "Robert", "Lisa", 
                      "William", "Jessica", "James", "Ashley", "Christopher", "Amanda", "Daniel",
                      "Stephanie", "Matthew", "Jennifer", "Anthony", "Elizabeth", "Mark", "Deborah",
                      "Donald", "Rachel", "Steven", "Carolyn", "Paul", "Janet", "Andrew", "Maria"]
        last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
                     "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
                     "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson",
                     "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson"]
        
        for i in range(30):
            role = random.choice(roles)
            first_name = random.choice(first_names)
            last_name = random.choice(last_names)
            
            user = User(
                username=f"{first_name.lower()}.{last_name.lower()}{i}",
                email=f"{first_name.lower()}.{last_name.lower()}{i}@hospital.com",
                password_hash=f"hashed_password_{100+i}",
                role=role,
                first_name=first_name,
                last_name=last_name,
                phone=f"555-{1000+i:04d}"
            )
            users.append(user)
        
        db.add_all(users)
        db.commit()
        
        print("2. Creating departments...")
        departments = []
        
        dept_data = [
            ("Emergency Medicine", "Emergency and trauma care"),
            ("Internal Medicine", "General internal medicine and primary care"),
            ("Cardiology", "Heart and cardiovascular care"),
            ("Neurology", "Brain and nervous system care"),
            ("Orthopedics", "Bone and joint care"),
            ("Pediatrics", "Children's healthcare"),
            ("Oncology", "Cancer treatment and care"),
            ("Radiology", "Imaging and diagnostic services"),
            ("Surgery", "Surgical procedures and care"),
            ("ICU", "Intensive care unit"),
            ("Pharmacy", "Medication management"),
            ("Administration", "Hospital administration")
        ]
        
        for i, (name, description) in enumerate(dept_data):
            dept = Department(
                name=name,
                description=description,
                head_doctor_id=random.choice(users).id,
                floor_number=random.randint(1, 5),
                phone=f"555-{2000+i:04d}",
                email=f"{name.lower().replace(' ', '.')}@hospital.com"
            )
            departments.append(dept)
        
        db.add_all(departments)
        db.commit()
        
        print("3. Creating staff...")
        staff = []
        
        specializations = [
            "Emergency Medicine", "Internal Medicine", "Cardiology", "Neurology",
            "Orthopedics", "Pediatrics", "Oncology", "Radiology", "Surgery",
            "Nursing", "Administration", "Pharmacy"
        ]
        
        positions = ["Doctor", "Nurse", "Manager", "Technician", "Administrator"]
        
        for i, user in enumerate(users):
            if user.role in ["doctor", "nurse", "manager"]:
                staff_member = Staff(
                    user_id=user.id,
                    employee_id=f"EMP{1000+i:04d}",
                    department_id=random.choice(departments).id,
                    position=random.choice(positions),
                    specialization=random.choice(specializations),
                    license_number=f"LIC{random.randint(10000, 99999)}",
                    hire_date=date.today() - timedelta(days=random.randint(30, 3650)),
                    status="active",
                    shift_pattern=random.choice(["day", "night", "rotating"]),
                    salary=Decimal(f"{random.randint(50000, 200000)}.00")
                )
                staff.append(staff_member)
        
        db.add_all(staff)
        db.commit()
        
        print("4. Creating patients...")
        patients = []
        
        blood_types = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]
        
        for i in range(25):
            first_name = random.choice(first_names)
            last_name = random.choice(last_names)
            
            patient = Patient(
                patient_number=f"P{1000+i:04d}",
                first_name=first_name,
                last_name=last_name,
                date_of_birth=date.today() - timedelta(days=random.randint(365, 30000)),
                gender=random.choice(["M", "F"]),
                phone=f"555-2{i:03d}",
                email=f"{first_name.lower()}.{last_name.lower()}.patient{i}@email.com",
                address=f"{random.randint(100, 9999)} {random.choice(['Main', 'Oak', 'Pine', 'First', 'Second'])} St",
                emergency_contact_name=f"Emergency Contact {i}",
                emergency_contact_phone=f"555-3{i:03d}",
                blood_type=random.choice(blood_types),
                allergies=random.choice(["None", "Penicillin", "Shellfish", "Latex", "Peanuts"]),
                medical_history=f"Patient {i} medical history: {random.choice(['diabetes', 'hypertension', 'asthma', 'none significant'])}",
                status="active"
            )
            patients.append(patient)
        
        db.add_all(patients)
        db.commit()
        
        print("5. Creating rooms...")
        rooms = []
        
        # Create diverse room types across multiple floors
        room_types = ["ICU", "General", "Private", "Emergency", "Surgery", "Recovery"]
        
        for floor in range(1, 6):  # 5 floors
            for room_num in range(1, 21):  # 20 rooms per floor
                room_number = f"{floor}{room_num:02d}"
                
                room = Room(
                    room_number=room_number,
                    room_type=random.choice(room_types),
                    department_id=random.choice(departments).id,
                    capacity=random.randint(1, 4),
                    floor_number=floor,
                    status=random.choice(["available", "occupied", "maintenance", "cleaning"])
                )
                rooms.append(room)
        
        db.add_all(rooms)
        db.commit()
        
        print("6. Creating beds...")
        beds = []
        
        # Create 1-3 beds per room based on capacity
        for room in rooms:
            for bed_num in range(room.capacity):
                bed_letter = chr(65 + bed_num)  # A, B, C, D
                bed_number = f"{room.room_number}{bed_letter}"
                
                # Assign some beds to patients
                patient_id = None
                bed_status = "available"
                if random.random() < 0.7 and patients:  # 70% occupancy rate
                    patient_id = random.choice(patients).id
                    bed_status = "occupied"
                
                bed = Bed(
                    bed_number=bed_number,
                    room_id=room.id,
                    patient_id=patient_id,
                    bed_type=random.choice(["standard", "ICU", "pediatric", "bariatric"]),
                    status=bed_status
                )
                beds.append(bed)
        
        db.add_all(beds)
        db.commit()
        
        print("7. Creating equipment categories...")
        equipment_categories = [
            ("Monitoring Equipment", "Patient monitoring and vital signs equipment"),
            ("Life Support", "Life support and respiratory equipment"),
            ("Surgical Equipment", "Surgical tools and operating room equipment"),
            ("Diagnostic Equipment", "Imaging and diagnostic tools"),
            ("Transport Equipment", "Patient transport and mobility aids"),
            ("Laboratory Equipment", "Lab testing and analysis equipment"),
            ("Emergency Equipment", "Emergency response and trauma equipment"),
            ("Rehabilitation Equipment", "Physical therapy and rehabilitation tools"),
            ("Sterilization Equipment", "Cleaning and sterilization equipment"),
            ("Communication Equipment", "Communication and information systems")
        ]
        
        eq_categories = []
        for name, description in equipment_categories:
            category = EquipmentCategory(
                name=name,
                description=description
            )
            eq_categories.append(category)
        
        db.add_all(eq_categories)
        db.commit()
        
        print("8. Creating equipment...")
        equipment = []
        
        # Equipment by category
        equipment_data = {
            "Monitoring Equipment": [
                ("ECG Monitor", "Electrocardiogram monitoring device"),
                ("Pulse Oximeter", "Blood oxygen saturation monitor"),
                ("Blood Pressure Monitor", "Automated blood pressure measurement"),
                ("Heart Rate Monitor", "Continuous heart rate monitoring"),
                ("Temperature Monitor", "Digital temperature measurement"),
                ("Multi-Parameter Monitor", "Comprehensive vital signs monitoring"),
                ("Cardiac Monitor", "Advanced cardiac rhythm monitoring"),
                ("Fetal Monitor", "Fetal heart rate and contraction monitoring"),
                ("Sleep Monitor", "Sleep study monitoring equipment"),
                ("Telemetry Monitor", "Wireless patient monitoring")
            ],
            "Life Support": [
                ("Ventilator", "Mechanical breathing assistance"),
                ("CPAP Machine", "Continuous positive airway pressure"),
                ("BiPAP Machine", "Bilevel positive airway pressure"),
                ("Oxygen Concentrator", "Oxygen therapy equipment"),
                ("Nebulizer", "Medication delivery via inhalation"),
                ("Suction Machine", "Airway clearance equipment"),
                ("Defibrillator", "Emergency cardiac resuscitation"),
                ("Infusion Pump", "Intravenous medication delivery"),
                ("Feeding Pump", "Enteral nutrition delivery"),
                ("Dialysis Machine", "Kidney function replacement")
            ]
        }
        
        # Create equipment for each category with sequential IDs
        equipment_counter = 1
        for category_name, items in equipment_data.items():
            category = next(c for c in eq_categories if c.name == category_name)
            
            for item_name, description in items:
                for i in range(random.randint(8, 15)):  # 8-15 of each type
                    equipment_item = Equipment(
                        equipment_id=f"EQ{equipment_counter:05d}",
                        name=f"{item_name} {i+1:03d}",
                        serial_number=f"SN{random.randint(100000, 999999)}",
                        model=f"Model-{random.randint(1000, 9999)}",
                        manufacturer=random.choice(["Philips", "GE Healthcare", "Siemens", "Medtronic", "Abbott"]),
                        category_id=category.id,
                        location=f"Room {random.choice(rooms).room_number}",
                        department_id=random.choice(departments).id,
                        status=random.choice(["available", "in_use", "maintenance", "out_of_order"]),
                        purchase_date=date.today() - timedelta(days=random.randint(1, 3650)),
                        cost=Decimal(f"{random.randint(5000, 100000)}.00"),
                        warranty_expiry=date.today() + timedelta(days=random.randint(30, 3650)),
                        last_maintenance=date.today() - timedelta(days=random.randint(1, 365))
                    )
                    equipment.append(equipment_item)
                    equipment_counter += 1
        
        db.add_all(equipment)
        db.commit()
        
        print("9. Creating supply categories...")
        supply_categories_data = [
            ("Medications", "Pharmaceuticals and medical drugs"),
            ("Surgical Supplies", "Items used in surgical procedures"),
            ("Wound Care", "Supplies for wound treatment and dressing"),
            ("IV and Injection", "Intravenous and injection related supplies"),
            ("Diagnostic Supplies", "Items for patient diagnosis and testing"),
            ("Personal Protective Equipment", "Safety equipment for staff and patients"),
            ("Patient Care", "General patient care and comfort items"),
            ("Laboratory Supplies", "Lab testing and analysis materials"),
            ("Emergency Supplies", "Emergency response and trauma care items"),
            ("Rehabilitation", "Physical therapy and recovery supplies"),
            ("Nutrition", "Dietary and nutritional supplements"),
            ("Sterilization", "Cleaning and sterilization materials"),
            ("Respiratory Care", "Breathing and oxygen therapy supplies"),
            ("Cardiac Care", "Heart and cardiovascular care supplies"),
            ("Pediatric Care", "Children's healthcare specific supplies")
        ]
        
        supply_categories = []
        for name, description in supply_categories_data:
            category = SupplyCategory(
                name=name,
                description=description
            )
            supply_categories.append(category)
        
        db.add_all(supply_categories)
        db.commit()
        
        print("10. Creating supplies...")
        supplies_by_category = {
            "Medications": [
                ("Acetaminophen 500mg", "Pain reliever and fever reducer", "tablet"),
                ("Ibuprofen 200mg", "Anti-inflammatory pain reliever", "tablet"),
                ("Morphine 10mg/ml", "Strong pain medication", "ml"),
                ("Insulin (Regular)", "Diabetes medication", "unit"),
                ("Epinephrine 1mg/ml", "Emergency allergy/cardiac medication", "ml"),
                ("Amoxicillin 500mg", "Antibiotic medication", "tablet"),
                ("Lisinopril 10mg", "Blood pressure medication", "tablet"),
                ("Albuterol Inhaler", "Respiratory bronchodilator", "inhaler"),
                ("Normal Saline 0.9%", "IV fluid solution", "ml"),
                ("Heparin 5000u/ml", "Blood thinner injection", "ml")
            ],
            "Surgical Supplies": [
                ("Surgical Gloves (Size 7)", "Sterile latex surgical gloves", "pair"),
                ("Surgical Mask", "Disposable surgical face mask", "piece"),
                ("Surgical Gown", "Sterile surgical protection gown", "piece"),
                ("Scalpel Blade #15", "Disposable surgical blade", "piece"),
                ("Surgical Suture 3-0", "Non-absorbable suture material", "piece"),
                ("Surgical Staples", "Wound closure staples", "piece"),
                ("Surgical Sponges", "Absorbent surgical sponges", "piece"),
                ("Endotracheal Tube 7.0", "Airway intubation tube", "piece"),
                ("Trocar 5mm", "Laparoscopic port", "piece"),
                ("Hemostatic Agent", "Bleeding control powder", "g")
            ],
            "Wound Care": [
                ("Gauze Pads 4x4", "Sterile wound dressing pads", "piece"),
                ("Medical Tape 1 inch", "Adhesive medical tape", "roll"),
                ("Transparent Dressing", "Clear adhesive wound cover", "piece"),
                ("Antibiotic Ointment", "Topical infection prevention", "g"),
                ("Betadine Solution", "Antiseptic wound cleaner", "ml"),
                ("Alcohol Prep Pads", "Skin preparation wipes", "piece"),
                ("Elastic Bandage 4 inch", "Compression support bandage", "roll"),
                ("Pressure Bandage", "Emergency bleeding control", "piece"),
                ("Hydrocolloid Dressing", "Advanced wound healing dressing", "piece"),
                ("Silver Sulfadiazine Cream", "Antimicrobial wound cream", "g")
            ],
            "IV and Injection": [
                ("IV Catheter 18G", "Large bore IV catheter", "piece"),
                ("IV Catheter 20G", "Medium bore IV catheter", "piece"),
                ("Syringe 5ml", "Standard injection syringe", "piece"),
                ("Needle 23G 1 inch", "Standard injection needle", "piece"),
                ("IV Bag 500ml Normal Saline", "IV fluid bag", "bag"),
                ("Blood Collection Tube", "Vacuum blood draw tube", "piece"),
                ("Butterfly Needle 23G", "Winged blood collection needle", "piece"),
                ("IV Tubing Set", "Standard IV administration set", "piece"),
                ("Tourniquet", "Blood draw compression band", "piece"),
                ("IV Site Dressing", "Catheter site protection", "piece")
            ],
            "Personal Protective Equipment": [
                ("N95 Respirator Mask", "High filtration respiratory protection", "piece"),
                ("Nitrile Gloves Medium", "Powder-free examination gloves", "piece"),
                ("Face Shield", "Full face protection shield", "piece"),
                ("Isolation Gown", "Protective clothing garment", "piece"),
                ("Hand Sanitizer 500ml", "Alcohol-based hand disinfectant", "bottle"),
                ("Disinfectant Wipes", "Surface cleaning wipes", "piece"),
                ("Biohazard Bag", "Infectious waste disposal bag", "piece"),
                ("Sharps Container", "Needle disposal container", "piece"),
                ("Safety Goggles", "Eye protection glasses", "piece"),
                ("Shoe Covers", "Disposable foot protection", "pair")
            ]
        }
        
        supplies = []
        supply_counter = 1
        
        for category_name, supply_items in supplies_by_category.items():
            # Find the category
            category = next(c for c in supply_categories if c.name == category_name)
            
            for name, description, unit in supply_items:
                supply = Supply(
                    item_code=f"SUP{supply_counter:05d}",
                    name=name,
                    category_id=category.id,
                    description=description,
                    unit_of_measure=unit,
                    minimum_stock_level=random.randint(10, 50),
                    maximum_stock_level=random.randint(100, 500),
                    current_stock=random.randint(25, 200),
                    unit_cost=Decimal(f"{random.uniform(0.5, 50.0):.2f}"),
                    supplier=random.choice([
                        "MedSupply Corp", "Healthcare Solutions", "Medical Distributors Inc",
                        "Premier Medical", "Cardinal Health"
                    ]),
                    expiry_date=date.today() + timedelta(days=random.randint(180, 1095)),
                    location=random.choice([
                        "Pharmacy", "Supply Room A", "Central Storage", "Emergency Stock"
                    ])
                )
                supplies.append(supply)
                supply_counter += 1
        
        db.add_all(supplies)
        db.commit()
        
        print("11. Creating operational data for the 23 empty tables...")
        
        # Get the created data for foreign key relationships
        all_users = db.query(User).all()
        all_departments = db.query(Department).all()
        all_staff = db.query(Staff).all()
        all_patients = db.query(Patient).all()
        all_rooms = db.query(Room).all()
        all_beds = db.query(Bed).all()
        all_equipment = db.query(Equipment).all()
        all_supplies = db.query(Supply).all()
        
        # 11.1 Create Agent Interactions
        print("   11.1 Creating agent interactions...")
        agent_interactions = []
        agent_types = [
            "orchestrator", "patient_agent", "staff_agent", "equipment_agent", 
            "supply_agent", "discharge_agent", "room_bed_agent", "medical_document_agent"
        ]
        
        for i in range(50):  # 50 agent interactions
            interaction = AgentInteraction(
                agent_type=random.choice(agent_types),
                query=f"Sample query {i+1}: {random.choice(['Patient admission', 'Bed assignment', 'Equipment check', 'Supply request', 'Discharge process'])}",
                response=f"Agent response {i+1}: Completed successfully",
                user_id=random.choice(all_users).id if random.random() > 0.3 else None,
                action_taken=random.choice(["bed_assigned", "equipment_allocated", "supply_ordered", "patient_discharged", "information_retrieved"]),
                confidence_score=random.uniform(0.8, 1.0),
                execution_time_ms=random.randint(100, 2000),
                created_at=datetime.now() - timedelta(days=random.randint(0, 30))
            )
            agent_interactions.append(interaction)
        
        db.add_all(agent_interactions)
        db.commit()
        
        # 11.2 Create Bed Staff Assignments
        print("   11.2 Creating bed staff assignments...")
        bed_staff_assignments = []
        
        for i in range(80):  # 80 bed staff assignments
            bed = random.choice(all_beds)
            # Use any staff member, not just specific positions
            staff_member = random.choice(all_staff)
            patient = random.choice(all_patients) if random.random() > 0.3 else None
            
            assignment = BedStaffAssignment(
                bed_id=bed.id,
                staff_id=staff_member.id,
                patient_id=patient.id if patient else None,
                assignment_type=random.choice(["primary_nurse", "secondary_nurse", "attending_physician", "resident"]),
                shift_type=random.choice(["day", "night", "evening"]),
                assigned_at=datetime.now() - timedelta(days=random.randint(0, 30)),
                released_at=datetime.now() + timedelta(days=random.randint(1, 60)) if random.random() > 0.3 else None,
                status=random.choice(["active", "completed", "transferred"])
            )
            bed_staff_assignments.append(assignment)
        
        db.add_all(bed_staff_assignments)
        db.commit()
        
        # 11.3 Create Equipment Usage Records
        print("   11.3 Creating equipment usage records...")
        equipment_usage_records = []
        
        for i in range(120):  # 120 equipment usage records
            equipment = random.choice(all_equipment)
            patient = random.choice(all_patients)
            staff_member = random.choice(all_staff)
            bed = random.choice(all_beds) if random.random() > 0.3 else None
            
            start_time = datetime.now() - timedelta(hours=random.randint(1, 720))  # Last 30 days
            
            usage = EquipmentUsage(
                equipment_id=equipment.id,
                patient_id=patient.id,
                staff_id=staff_member.id,
                bed_id=bed.id if bed else None,
                start_time=start_time,
                end_time=start_time + timedelta(hours=random.randint(1, 24)) if random.random() > 0.2 else None,
                duration_minutes=random.randint(15, 480),
                purpose=random.choice(["monitoring", "treatment", "diagnostic", "therapy"]),
                settings=f"Settings: {random.randint(80, 120)}/80 mmHg, Rate: {random.randint(60, 100)}",
                readings=f"Readings: BP {random.randint(90, 140)}/{random.randint(60, 90)}, HR {random.randint(60, 100)}",
                notes=f"Equipment usage notes for {equipment.name}",
                status=random.choice(["active", "completed", "interrupted"])
            )
            equipment_usage_records.append(usage)
        
        db.add_all(equipment_usage_records)
        db.commit()
        
        # 11.4 Create Staff Assignments
        print("   11.4 Creating staff assignments...")
        staff_assignments = []
        
        for i in range(100):  # 100 staff assignments
            staff_member = random.choice(all_staff)
            patient = random.choice(all_patients)
            bed = random.choice(all_beds) if random.random() > 0.4 else None
            
            assignment = StaffAssignment(
                staff_id=staff_member.id,
                patient_id=patient.id,
                bed_id=bed.id if bed else None,
                assignment_type=random.choice(["primary_care", "secondary_care", "consultation", "emergency"]),
                start_date=datetime.now() - timedelta(days=random.randint(0, 60)),
                end_date=datetime.now() + timedelta(days=random.randint(1, 30)) if random.random() > 0.4 else None,
                shift=random.choice(["day", "night", "evening"]),
                responsibilities=random.choice([
                    "Patient monitoring and care", "Medication administration", 
                    "Surgical assistance", "Emergency response", "Patient education"
                ]),
                notes=f"Assignment for {staff_member.position}"
            )
            staff_assignments.append(assignment)
        
        db.add_all(staff_assignments)
        db.commit()
        
        # 11.5 Create Patient Supply Usage
        print("   11.5 Creating patient supply usage records...")
        patient_supply_usage_records = []
        
        for i in range(150):  # 150 supply usage records
            patient = random.choice(all_patients)
            supply = random.choice(all_supplies)
            staff_prescribed = random.choice(all_staff)  # Use any staff member
            staff_administered = random.choice(all_staff)  # Use any staff member
            bed = random.choice(all_beds) if random.random() > 0.3 else None
            
            usage_date = datetime.now() - timedelta(days=random.randint(0, 30))
            
            usage = PatientSupplyUsage(
                patient_id=patient.id,
                supply_id=supply.id,
                quantity_used=random.randint(1, 5),
                prescribed_by_id=staff_prescribed.user_id,
                administered_by_id=staff_administered.user_id,
                bed_id=bed.id if bed else None,
                dosage=f"{random.randint(1, 4)} {random.choice(['tablets', 'mg', 'ml', 'units'])}",
                frequency=random.choice(["once daily", "twice daily", "three times daily", "as needed", "every 4 hours"]),
                administration_route=random.choice(["oral", "intravenous", "intramuscular", "topical", "subcutaneous"]),
                indication=random.choice([
                    "Pain management", "Infection prevention", "Blood pressure control", 
                    "Diabetes management", "Cardiac support", "Respiratory therapy"
                ]),
                prescribed_date=usage_date,
                administration_date=usage_date + timedelta(hours=random.randint(1, 12)),
                start_date=usage_date.date(),
                end_date=usage_date.date() + timedelta(days=random.randint(1, 14)) if random.random() > 0.3 else None,
                effectiveness=random.choice(["effective", "partial", "ineffective"]) if random.random() > 0.5 else None,
                side_effects=random.choice(["none", "mild nausea", "dizziness", "fatigue"]) if random.random() > 0.7 else None,
                notes=f"Supply usage for patient {patient.patient_number}",
                unit_cost=supply.unit_cost,
                total_cost=supply.unit_cost * random.randint(1, 5),
                insurance_covered=random.choice([True, False]),
                billed=random.choice([True, False]),
                status=random.choice(["prescribed", "administered", "completed", "discontinued"])
            )
            patient_supply_usage_records.append(usage)
        
        db.add_all(patient_supply_usage_records)
        db.commit()
        
        # 11.6 Create Inventory Transactions
        print("   11.6 Creating inventory transactions...")
        inventory_transactions = []
        
        for i in range(80):  # 80 inventory transactions
            supply = random.choice(all_supplies)
            staff_member = random.choice(all_staff)
            
            transaction = InventoryTransaction(
                supply_id=supply.id,
                transaction_type=random.choice(["in", "out", "adjustment"]),
                quantity=random.randint(1, 100) if random.random() > 0.2 else -random.randint(1, 50),
                unit_cost=supply.unit_cost,
                total_cost=supply.unit_cost * abs(random.randint(1, 100)),
                performed_by=staff_member.user_id,
                reference_number=f"TXN{1000+i:04d}",
                notes=f"Inventory transaction for {supply.name}",
                transaction_date=datetime.now() - timedelta(days=random.randint(0, 60))
            )
            inventory_transactions.append(transaction)
        
        db.add_all(inventory_transactions)
        db.commit()
        
        # 11.7 Create Treatment Records
        print("   11.7 Creating treatment records...")
        treatment_records = []
        
        for i in range(90):  # 90 treatment records
            patient = random.choice(all_patients)
            doctor = random.choice(all_staff)  # Use any staff member as doctor
            bed = random.choice(all_beds) if random.random() > 0.4 else None
            
            start_date = datetime.now() - timedelta(days=random.randint(0, 90))
            end_date = start_date + timedelta(days=random.randint(1, 30)) if random.random() > 0.3 else None
            
            treatment = TreatmentRecord(
                patient_id=patient.id,
                doctor_id=doctor.user_id,
                bed_id=bed.id if bed else None,
                treatment_type=random.choice(["medication", "procedure", "therapy"]),
                treatment_name=random.choice([
                    "Antibiotic Treatment", "Physical Therapy", "Blood Pressure Management",
                    "Diabetes Care", "Pain Management", "Wound Care", "Respiratory Therapy"
                ]),
                description=f"Comprehensive treatment plan for patient {patient.patient_number}",
                dosage=random.choice(["10mg", "20mg", "500mg", "1g"]) if random.random() > 0.5 else None,
                frequency=random.choice(["daily", "twice_daily", "three_times_daily", "weekly", "as_needed"]),
                duration=random.choice(["7_days", "2_weeks", "1_month", "ongoing"]),
                start_date=start_date,
                end_date=end_date,
                status=random.choice(["active", "completed", "discontinued"]),
                notes=f"Treatment notes for patient {patient.patient_number}",
                side_effects=random.choice(["none", "mild nausea", "dizziness", "fatigue"]) if random.random() > 0.7 else None,
                effectiveness=random.choice(["excellent", "good", "fair", "poor"]) if random.random() > 0.6 else None
            )
            treatment_records.append(treatment)
        
        db.add_all(treatment_records)
        db.commit()
        
        # 11.8 Create Meetings
        print("   11.8 Creating meetings...")
        meetings = []
        
        for i in range(40):  # 40 meetings
            organizer = random.choice(all_users)
            department = random.choice(all_departments)
            
            meeting_date = datetime.now() + timedelta(days=random.randint(1, 30))
            
            meeting = Meeting(
                title=f"Meeting {i+1}: {random.choice(['Department Review', 'Case Discussion', 'Quality Improvement', 'Staff Training', 'Emergency Planning'])}",
                description=f"Meeting description for {random.choice(['patient care review', 'policy updates', 'training session', 'budget planning'])}",
                meeting_datetime=meeting_date,
                duration_minutes=random.choice([30, 60, 90, 120]),
                location=f"Conference Room {random.randint(1, 10)}",
                organizer_id=organizer.id,
                department_id=department.id,
                meeting_type=random.choice(["department", "multidisciplinary", "emergency", "training", "administrative"]),
                status=random.choice(["scheduled", "in_progress", "completed", "cancelled"]),
                priority=random.choice(["low", "medium", "high"]),
                agenda=f"Agenda item {i+1}: {random.choice(['Patient case reviews', 'Policy updates', 'Equipment training', 'Quality metrics'])}",
                meeting_notes=f"Meeting notes for session {i+1}" if random.random() > 0.5 else None,
                action_items=f"Action item {i+1}: Follow up on patient care protocols",
                google_meet_link=f"https://meet.google.com/meeting-{i+1}" if random.random() > 0.6 else None,
                email_sent=random.choice([True, False]),
                calendar_invites_sent=random.choice([True, False]),
                reminder_sent=random.choice([True, False])
            )
            meetings.append(meeting)
        
        db.add_all(meetings)
        db.commit()
        
        # 11.9 Create Meeting Participants
        print("   11.9 Creating meeting participants...")
        meeting_participants = []
        all_meetings = db.query(Meeting).all()
        
        for meeting in all_meetings:
            # Add 3-8 participants per meeting
            num_participants = random.randint(3, 8)
            selected_staff = random.sample(all_staff, min(num_participants, len(all_staff)))
            
            for staff in selected_staff:
                participant = MeetingParticipant(
                    meeting_id=meeting.id,
                    staff_id=staff.id,
                    attendance_status=random.choice(["invited", "accepted", "declined", "tentative", "attended"]),
                    response_datetime=datetime.now() - timedelta(days=random.randint(0, 5)) if random.random() > 0.3 else None,
                    join_datetime=datetime.now() + timedelta(minutes=random.randint(-5, 15)) if random.random() > 0.5 else None,
                    leave_datetime=datetime.now() + timedelta(minutes=random.randint(30, 120)) if random.random() > 0.6 else None
                )
                meeting_participants.append(participant)
        
        db.add_all(meeting_participants)
        db.commit()
        
        # 11.10 Create Discharge Reports
        print("   11.10 Creating discharge reports...")
        discharge_reports = []
        
        for i in range(60):  # 60 discharge reports
            patient = random.choice(all_patients)
            bed = random.choice(all_beds)
            discharging_doctor = random.choice(all_staff)  # Use any staff member
            
            admission_date = datetime.now() - timedelta(days=random.randint(1, 30))
            discharge_date = admission_date + timedelta(days=random.randint(1, 14))
            length_of_stay = (discharge_date - admission_date).days
            
            report = DischargeReport(
                patient_id=patient.id,
                bed_id=bed.id,
                generated_by=discharging_doctor.user_id,
                report_number=f"DR{1000+i:04d}",
                admission_date=admission_date,
                discharge_date=discharge_date,
                length_of_stay_days=length_of_stay,
                patient_summary=f"Patient {patient.patient_number} summary",
                treatment_summary=f"Treatment provided during {length_of_stay} day stay",
                equipment_summary="Equipment used: monitoring devices, IV pumps",
                staff_summary="Attended by multidisciplinary team",
                medications="Medications administered as per protocol",
                supply_usage="Supplies used appropriately throughout stay",
                procedures="Standard procedures performed",
                discharge_instructions="Follow discharge instructions carefully",
                follow_up_required="Follow up with primary care in 1-2 weeks",
                discharge_condition=random.choice(["improved", "stable", "critical"]),
                discharge_destination=random.choice(["home", "transfer", "rehabilitation", "nursing_home"])
            )
            discharge_reports.append(report)
        
        db.add_all(discharge_reports)
        db.commit()
        
        # 11.11 Create Bed Turnovers
        print("   11.11 Creating bed turnovers...")
        bed_turnovers = []
        
        for i in range(70):  # 70 bed turnovers
            bed = random.choice(all_beds)
            previous_patient = random.choice(all_patients) if random.random() > 0.2 else None
            next_patient = random.choice(all_patients) if random.random() > 0.3 else None
            cleaner = random.choice(all_staff)
            inspector = random.choice(all_staff)
            
            discharge_time = datetime.now() - timedelta(hours=random.randint(1, 48))
            cleaning_start_time = discharge_time + timedelta(minutes=random.randint(15, 60))
            cleaning_end_time = cleaning_start_time + timedelta(minutes=random.randint(30, 120))
            ready_time = cleaning_end_time + timedelta(minutes=random.randint(15, 30))
            
            turnover = BedTurnover(
                bed_id=bed.id,
                previous_patient_id=previous_patient.id if previous_patient else None,
                next_patient_id=next_patient.id if next_patient else None,
                status=random.choice(["initiated", "cleaning", "cleaning_complete", "ready", "assigned"]),
                turnover_type=random.choice(["standard", "deep_clean", "maintenance"]),
                discharge_time=discharge_time,
                cleaning_start_time=cleaning_start_time,
                cleaning_end_time=cleaning_end_time,
                ready_time=ready_time,
                next_assignment_time=ready_time + timedelta(minutes=random.randint(30, 180)) if next_patient else None,
                estimated_cleaning_duration=random.randint(30, 90),
                assigned_cleaner_id=cleaner.user_id,
                assigned_inspector_id=inspector.user_id,
                equipment_requiring_cleaning="[]",  # Empty JSON array
                equipment_to_be_returned="[]",  # Empty JSON array
                equipment_cleaning_complete=random.choice([True, False]),
                cleaning_checklist="{}",  # Empty JSON object
                inspection_passed=random.choice([True, False]),
                inspector_notes=f"Inspection notes for bed {bed.bed_number}",
                priority_level=random.choice(["urgent", "high", "normal", "low"]),
                notes=f"Bed turnover completed for bed {bed.bed_number}"
            )
            bed_turnovers.append(turnover)
        
        db.add_all(bed_turnovers)
        db.commit()
        
        # 11.12 Create remaining tables with sample data
        print("   11.12 Creating additional operational records...")
        
        # Skip BedCleaningTask for now - requires BedTurnoverLog
        
        # Patient Queue
        patient_queues = []
        for i in range(35):
            patient = random.choice(all_patients)
            department = random.choice(all_departments)
            doctor = random.choice(all_staff)
            target_bed = random.choice(all_beds) if random.random() > 0.6 else None
            assigned_bed = random.choice(all_beds) if random.random() > 0.7 else None
            
            queue_entry = PatientQueue(
                patient_id=patient.id,
                department_id=department.id,
                queue_position=random.randint(1, 20),
                bed_type_required=random.choice(["ICU", "General", "Private", "Emergency"]),
                priority_level=random.choice(["urgent", "high", "normal", "low"]),
                admission_type=random.choice(["emergency", "scheduled", "transfer"]),
                estimated_wait_time=random.randint(15, 180),
                target_bed_id=target_bed.id if target_bed else None,
                medical_condition=random.choice([
                    "Chest pain", "Shortness of breath", "Abdominal pain", 
                    "Cardiac monitoring", "Post-operative care"
                ]),
                special_requirements="{}",  # Empty JSON object
                doctor_id=doctor.user_id,
                status=random.choice(["waiting", "assigned", "admitted", "cancelled"]),
                assigned_bed_id=assigned_bed.id if assigned_bed else None,
                assignment_time=datetime.now() - timedelta(minutes=random.randint(0, 120)) if assigned_bed else None
            )
            patient_queues.append(queue_entry)
        
        db.add_all(patient_queues)
        db.commit()
        
        # Medical Documents
        medical_documents = []
        for i in range(45):
            patient = random.choice(all_patients)
            uploaded_by = random.choice(all_staff)
            
            document = MedicalDocument(
                patient_id=patient.id,
                document_type=random.choice([
                    "prescription", "lab_result", "imaging", "discharge_summary", 
                    "consultation_note", "operative_report", "pathology_report"
                ]),
                file_name=f"document_{i+1:03d}.pdf",
                file_path=f"/medical_docs/patient_{patient.patient_number}/document_{i+1:03d}.pdf",
                file_size=random.randint(100000, 5000000),
                mime_type="application/pdf",
                extracted_text=f"Sample extracted text from medical document {i+1}",
                processing_status=random.choice(['pending', 'processing', 'completed', 'failed']),
                extracted_metadata=f'{{"document_type": "{random.choice(["lab", "imaging", "report"])}", "confidence": 0.85}}',
                confidence_score=round(random.uniform(0.70, 0.99), 2)
            )
            medical_documents.append(document)
        
        db.add_all(medical_documents)
        db.commit()
        
        # Additional empty tables with minimal records for completeness
        # Staff Interactions
        staff_interactions = []
        for i in range(30):
            patient = random.choice(all_patients)
            staff = random.choice(all_staff)
            
            interaction = StaffInteraction(
                patient_id=patient.patient_number,  # Using patient_number as string
                staff_name=f"Staff Member {i+1}",  # Simple staff name
                staff_role=staff.position,
                interaction_type=random.choice(["consultation", "treatment", "monitoring", "assessment"]),
                description=f"Staff interaction with patient {patient.patient_number}",
                interaction_date=date.today() - timedelta(days=random.randint(0, 30)),
                duration_minutes=random.randint(10, 60)
            )
            staff_interactions.append(interaction)
        
        db.add_all(staff_interactions)
        db.commit()
        
        # 11.13 Create ExtractedMedicalData
        print("   11.13 Creating extracted medical data...")
        extracted_medical_data = []
        all_medical_documents = db.query(MedicalDocument).all()
        
        for i, document in enumerate(all_medical_documents):
            # Create 2-3 extracted data entries per document
            num_extractions = random.randint(2, 3)
            
            for j in range(num_extractions):
                extraction = ExtractedMedicalData(
                    document_id=document.id,
                    patient_id=document.patient_id,
                    data_type=random.choice(["medication", "condition", "procedure", "allergy", "vital_sign"]),
                    entity_name=random.choice([
                        "Lisinopril", "Hypertension", "Blood Pressure Check", "Penicillin Allergy",
                        "Temperature 98.6°F", "Diabetes Type 2", "X-ray Chest", "Aspirin 81mg",
                        "Heart Rate 72 bpm", "Surgical Procedure"
                    ]),
                    entity_value=random.choice(["10mg daily", "Stage 1", "Normal", "Severe", "120/80"]),
                    entity_unit=random.choice(["mg", "mmHg", "bpm", "°F", "units"]) if random.random() > 0.5 else None,
                    date_prescribed=date.today() - timedelta(days=random.randint(0, 30)),
                    date_recorded=date.today() - timedelta(days=random.randint(0, 15)),
                    doctor_name=f"Dr. {random.choice(['Smith', 'Johnson', 'Wilson', 'Brown'])}",
                    hospital_name="General Hospital",
                    department_name=random.choice(["Cardiology", "Internal Medicine", "Emergency"]),
                    extraction_confidence=round(random.uniform(0.80, 0.99), 2),
                    extraction_method=random.choice(["OCR", "AI_PARSING", "MANUAL"]),
                    verified=random.choice([True, False]),
                    notes=f"Extracted from document {document.file_name}"
                )
                extracted_medical_data.append(extraction)
        
        db.add_all(extracted_medical_data)
        db.commit()
        
        # 11.14 Create BedEquipmentAssignments
        print("   11.14 Creating bed equipment assignments...")
        bed_equipment_assignments = []
        
        for i in range(85):  # 85 bed equipment assignments
            bed = random.choice(all_beds)
            equipment = random.choice(all_equipment)
            patient = random.choice(all_patients) if random.random() > 0.3 else None
            staff = random.choice(all_staff)
            
            assigned_at = datetime.now() - timedelta(hours=random.randint(1, 168))  # Last week
            released_at = assigned_at + timedelta(hours=random.randint(2, 72)) if random.random() > 0.4 else None
            
            assignment = BedEquipmentAssignment(
                bed_id=bed.id,
                equipment_id=equipment.id,
                patient_id=patient.id if patient else None,
                assigned_at=assigned_at,
                released_at=released_at,
                status=random.choice(["assigned", "in_use", "released", "maintenance"]),
                assigned_by_staff_id=staff.id,
                notes=f"Equipment {equipment.name} assigned to bed {bed.bed_number}"
            )
            bed_equipment_assignments.append(assignment)
        
        db.add_all(bed_equipment_assignments)
        db.commit()
        
        # 11.15 Create StaffMeetings
        print("   11.15 Creating staff meetings...")
        staff_meetings = []
        
        for i in range(25):  # 25 staff meetings
            organizer = random.choice(all_staff)
            department = random.choice(all_departments)
            
            meeting_time = datetime.now() + timedelta(days=random.randint(1, 45))
            
            staff_meeting = StaffMeeting(
                title=f"Staff Meeting {i+1}: {random.choice(['Monthly Review', 'Training Session', 'Policy Update', 'Quality Improvement', 'Emergency Preparedness'])}",
                description=f"Department meeting for {random.choice(['staff training', 'policy review', 'case discussion', 'quality metrics'])}",
                meeting_time=meeting_time,
                duration_minutes=random.choice([60, 90, 120]),
                location=f"Conference Room {random.choice(['A', 'B', 'C', 'Main', 'Training'])}",
                organizer_id=organizer.id,
                department_id=department.id if random.random() > 0.3 else None,
                status=random.choice(["scheduled", "in_progress", "completed", "cancelled"])
            )
            staff_meetings.append(staff_meeting)
        
        db.add_all(staff_meetings)
        db.commit()
        
        # 11.16 Create StaffMeetingParticipants
        print("   11.16 Creating staff meeting participants...")
        staff_meeting_participants = []
        all_staff_meetings = db.query(StaffMeeting).all()
        
        for meeting in all_staff_meetings:
            # Add 4-8 staff members to each meeting
            num_participants = random.randint(4, 8)
            selected_staff = random.sample(all_staff, min(num_participants, len(all_staff)))
            
            for staff_member in selected_staff:
                participant = StaffMeetingParticipant(
                    meeting_id=meeting.id,
                    staff_id=staff_member.id
                )
                staff_meeting_participants.append(participant)
        
        db.add_all(staff_meeting_participants)
        db.commit()
        
        # 11.17 Create LegacyUsers
        print("   11.17 Creating legacy users...")
        legacy_users = []
        
        legacy_names = ["Alice Johnson", "Bob Smith", "Carol Davis", "David Wilson", "Emma Brown",
                       "Frank Miller", "Grace Taylor", "Henry Anderson", "Iris Martinez", "Jack Thompson"]
        
        for i, name in enumerate(legacy_names):
            legacy_user = LegacyUser(
                name=name,
                email=f"{name.lower().replace(' ', '.')}@legacy.hospital.com",
                address=f"{random.randint(100, 9999)} Legacy {random.choice(['Street', 'Avenue', 'Boulevard', 'Drive'])}",
                phone=f"555-{4000+i:04d}"
            )
            legacy_users.append(legacy_user)
        
        db.add_all(legacy_users)
        db.commit()
        
        print("✅ All additional 5 tables populated successfully!")
        
        print("✅ All 23 operational tables populated successfully!")
        
        # Print comprehensive summary
        print(f"\n📊 Database Summary:")
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
        
        print(f"\n🔥 NEW OPERATIONAL DATA:")
        print(f"Agent Interactions: {db.query(AgentInteraction).count()}")
        print(f"Bed Staff Assignments: {db.query(BedStaffAssignment).count()}")
        print(f"Equipment Usage: {db.query(EquipmentUsage).count()}")
        print(f"Staff Assignments: {db.query(StaffAssignment).count()}")
        print(f"Patient Supply Usage: {db.query(PatientSupplyUsage).count()}")
        print(f"Inventory Transactions: {db.query(InventoryTransaction).count()}")
        print(f"Treatment Records: {db.query(TreatmentRecord).count()}")
        print(f"Meetings: {db.query(Meeting).count()}")
        print(f"Meeting Participants: {db.query(MeetingParticipant).count()}")
        print(f"Discharge Reports: {db.query(DischargeReport).count()}")
        print(f"Bed Turnovers: {db.query(BedTurnover).count()}")
        print(f"Bed Cleaning Tasks: {db.query(BedCleaningTask).count()}")
        print(f"Patient Queue: {db.query(PatientQueue).count()}")
        print(f"Medical Documents: {db.query(MedicalDocument).count()}")
        print(f"Staff Interactions: {db.query(StaffInteraction).count()}")
        
        print(f"Extracted Medical Data: {db.query(ExtractedMedicalData).count()}")
        print(f"Bed Equipment Assignments: {db.query(BedEquipmentAssignment).count()}")
        print(f"Staff Meetings: {db.query(StaffMeeting).count()}")
        print(f"Staff Meeting Participants: {db.query(StaffMeetingParticipant).count()}")
        print(f"Legacy Users: {db.query(LegacyUser).count()}")
        
        print(f"\n📈 Data Statistics:")
        total_records = sum([
            db.query(User).count(), db.query(Department).count(), db.query(Staff).count(),
            db.query(Patient).count(), db.query(Room).count(), db.query(Bed).count(),
            db.query(Equipment).count(), db.query(Supply).count(), db.query(SupplyCategory).count(),
            db.query(AgentInteraction).count(), db.query(BedStaffAssignment).count(),
            db.query(EquipmentUsage).count(), db.query(StaffAssignment).count(),
            db.query(PatientSupplyUsage).count(), db.query(InventoryTransaction).count(),
            db.query(TreatmentRecord).count(), db.query(Meeting).count(),
            db.query(MeetingParticipant).count(), db.query(DischargeReport).count(),
            db.query(BedTurnover).count(), db.query(BedCleaningTask).count(),
            db.query(PatientQueue).count(), db.query(MedicalDocument).count(),
            db.query(StaffInteraction).count(), db.query(ExtractedMedicalData).count(),
            db.query(BedEquipmentAssignment).count(), db.query(StaffMeeting).count(),
            db.query(StaffMeetingParticipant).count(), db.query(LegacyUser).count()
        ])
        print(f"Total Records Created: {total_records}")
        
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
        return
    
    # Create sample data
    print("3. Creating sample data...")
    try:
        create_sample_data()
        print("✅ Sample data created successfully!")
    except Exception as e:
        print(f"❌ Error creating sample data: {e}")
    
    print("\n🎉 Database setup completed successfully!")

if __name__ == "__main__":
    main()
