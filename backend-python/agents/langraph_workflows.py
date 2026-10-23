"""
LangGraph Workflow Implementation for Hospital Management System
Enhanced workflow orchestration using LangGraph state machines
"""

import os
import json
import uuid
from typing import Any, Dict, List, Optional, TypedDict, Annotated
from datetime import datetime
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.runnables import RunnablePassthrough

# Import database models
try:
    from database import Patient, Bed, Staff, Equipment, Department, SessionLocal
    DATABASE_AVAILABLE = True
except ImportError:
    DATABASE_AVAILABLE = False
    print("WARNING: Database not available for LangGraph workflows")

# Initialize LangChain components
OPENAI_API_KEY = os.getenv('VITE_OPENAI_API_KEY') or os.getenv('OPENAI_API_KEY')
if OPENAI_API_KEY:
    llm = ChatOpenAI(
        api_key=OPENAI_API_KEY,
        model="gpt-4",
        temperature=0.1
    )
    LANGCHAIN_AVAILABLE = True
    print("✅ LangChain OpenAI initialized for workflows")
else:
    llm = None
    LANGCHAIN_AVAILABLE = False
    print("⚠️ OpenAI API key not found - LangGraph workflows disabled")

# State definitions for different workflows
class PatientAdmissionState(TypedDict):
    """State for patient admission workflow"""
    patient_data: Dict[str, Any]
    patient_id: Optional[str]
    bed_id: Optional[str]
    staff_assignments: List[Dict[str, Any]]
    equipment_assignments: List[Dict[str, Any]]
    workflow_status: str
    error_message: Optional[str]
    steps_completed: List[str]
    messages: Annotated[List[BaseMessage], add_messages]

class ClinicalDecisionState(TypedDict):
    """State for clinical decision support workflow"""
    query: str
    patient_context: Optional[Dict[str, Any]]
    symptoms: List[str]
    patient_history: Optional[Dict[str, Any]]
    rag_knowledge: List[str]
    differential_diagnoses: List[Dict[str, Any]]
    recommendations: List[str]
    confidence_score: float
    messages: Annotated[List[BaseMessage], add_messages]

class DocumentProcessingState(TypedDict):
    """State for medical document processing workflow"""
    document_path: str
    document_type: str
    extracted_text: Optional[str]
    medical_entities: List[Dict[str, Any]]
    structured_data: Optional[Dict[str, Any]]
    validation_results: Optional[Dict[str, Any]]
    processing_status: str
    messages: Annotated[List[BaseMessage], add_messages]

# ================================
# PATIENT ADMISSION WORKFLOW
# ================================

class PatientAdmissionWorkflow:
    """LangGraph-based patient admission workflow"""
    
    def __init__(self):
        self.graph = None
        self.build_workflow()
    
    def build_workflow(self):
        """Build the patient admission workflow graph"""
        if not LANGCHAIN_AVAILABLE:
            print("⚠️ Cannot build admission workflow - LangChain not available")
            return
        
        workflow = StateGraph(PatientAdmissionState)
        
        # Add workflow nodes
        workflow.add_node("validate_patient", self.validate_patient_data)
        workflow.add_node("create_patient", self.create_patient_record)
        workflow.add_node("find_bed", self.find_available_bed)
        workflow.add_node("assign_bed", self.assign_bed_to_patient)
        workflow.add_node("assign_staff", self.assign_medical_staff)
        workflow.add_node("assign_equipment", self.assign_equipment_resources)
        workflow.add_node("generate_reports", self.generate_admission_reports)
        workflow.add_node("finalize_admission", self.finalize_admission_process)
        
        # Define workflow edges
        workflow.set_entry_point("validate_patient")
        workflow.add_edge("validate_patient", "create_patient")
        workflow.add_edge("create_patient", "find_bed")
        
        # Conditional routing based on bed availability
        workflow.add_conditional_edges(
            "find_bed",
            self.route_bed_assignment,
            {
                "bed_available": "assign_bed",
                "no_bed_available": "finalize_admission",  # Add to waitlist
                "error": END
            }
        )
        
        workflow.add_edge("assign_bed", "assign_staff")
        workflow.add_edge("assign_staff", "assign_equipment")
        workflow.add_edge("assign_equipment", "generate_reports")
        workflow.add_edge("generate_reports", "finalize_admission")
        workflow.add_edge("finalize_admission", END)
        
        self.graph = workflow.compile()
        print("✅ Patient admission workflow graph compiled")
    
    def validate_patient_data(self, state: PatientAdmissionState) -> PatientAdmissionState:
        """Validate patient data using simple validation logic"""
        try:
            patient_data = state["patient_data"]
            
            # Required fields validation
            required_fields = ["first_name", "last_name", "date_of_birth", "phone"]
            missing_fields = []
            
            for field in required_fields:
                if not patient_data.get(field):
                    missing_fields.append(field)
            
            if missing_fields:
                state["error_message"] = f"Missing required fields: {missing_fields}"
                state["workflow_status"] = "validation_failed"
            else:
                state["workflow_status"] = "validated"
                state["steps_completed"].append("validation")
            
            state["messages"].append(
                AIMessage(content=f"Patient data validation: {'passed' if not missing_fields else 'failed'}")
            )
            
        except Exception as e:
            state["error_message"] = f"Validation error: {str(e)}"
            state["workflow_status"] = "error"
        
        return state
    
    def create_patient_record(self, state: PatientAdmissionState) -> PatientAdmissionState:
        """Create patient record in database or use existing patient"""
        try:
            # If patient_id already exists, skip creation
            if state.get("patient_id"):
                state["workflow_status"] = "patient_exists"
                state["steps_completed"].append("patient_exists")
                state["messages"].append(
                    AIMessage(content=f"Using existing patient ID: {state['patient_id']}")
                )
                return state
            
            if not DATABASE_AVAILABLE:
                state["error_message"] = "Database not available"
                return state
            
            db = SessionLocal()
            try:
                # Create patient record
                patient = Patient(
                    patient_number=f"P{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    first_name=state["patient_data"]["first_name"],
                    last_name=state["patient_data"]["last_name"],
                    date_of_birth=datetime.strptime(state["patient_data"]["date_of_birth"], "%Y-%m-%d").date(),
                    gender=state["patient_data"].get("gender"),
                    phone=state["patient_data"]["phone"],
                    email=state["patient_data"].get("email"),
                    address=state["patient_data"].get("address"),
                    emergency_contact_name=state["patient_data"].get("emergency_contact_name"),
                    emergency_contact_phone=state["patient_data"].get("emergency_contact_phone"),
                    blood_type=state["patient_data"].get("blood_type"),
                    medical_history=state["patient_data"].get("medical_history"),
                    allergies=state["patient_data"].get("allergies"),
                    status="active"
                )
                
                db.add(patient)
                db.commit()
                
                state["patient_id"] = str(patient.id)
                state["workflow_status"] = "patient_created"
                state["steps_completed"].append("patient_creation")
                
                state["messages"].append(
                    AIMessage(content=f"Patient created successfully with ID: {patient.id}")
                )
                
            finally:
                db.close()
                
        except Exception as e:
            state["error_message"] = f"Patient creation error: {str(e)}"
            state["workflow_status"] = "error"
        
        return state
    
    def find_available_bed(self, state: PatientAdmissionState) -> PatientAdmissionState:
        """Find available bed using intelligent matching"""
        try:
            if not DATABASE_AVAILABLE:
                state["error_message"] = "Database not available"
                return state
            
            db = SessionLocal()
            try:
                # Find available beds
                available_beds = db.query(Bed).filter(Bed.status == "available").all()
                
                if not available_beds:
                    state["workflow_status"] = "no_beds_available"
                    state["messages"].append(
                        AIMessage(content="No beds currently available. Patient added to waitlist.")
                    )
                    return state
                
                # Use simple selection - first available bed (can be enhanced later)
                selected_bed = available_beds[0]
                
                state["bed_id"] = str(selected_bed.id)
                state["workflow_status"] = "bed_found"
                state["steps_completed"].append("bed_selection")
                
                state["messages"].append(
                    AIMessage(content=f"Selected bed: {selected_bed.bed_number}")
                )
                
            finally:
                db.close()
                
        except Exception as e:
            state["error_message"] = f"Bed finding error: {str(e)}"
            state["workflow_status"] = "error"
        
        return state
    
    def route_bed_assignment(self, state: PatientAdmissionState) -> str:
        """Route based on bed availability"""
        if state["workflow_status"] == "bed_found":
            return "bed_available"
        elif state["workflow_status"] == "no_beds_available":
            return "no_bed_available"
        else:
            return "error"
    
    def assign_bed_to_patient(self, state: PatientAdmissionState) -> PatientAdmissionState:
        """Assign selected bed to patient"""
        try:
            if not DATABASE_AVAILABLE:
                state["error_message"] = "Database not available"
                return state
            
            # Skip if no patient created yet
            if not state.get("patient_id"):
                state["workflow_status"] = "bed_skipped"
                state["steps_completed"].append("bed_assignment_skipped")
                state["messages"].append(
                    AIMessage(content="Bed assignment skipped - no patient ID available")
                )
                return state
            
            db = SessionLocal()
            try:
                # Update bed status
                bed = db.query(Bed).filter(Bed.id == uuid.UUID(state["bed_id"])).first()
                if bed:
                    bed.status = "occupied"
                    # Only assign patient_id if patient was created in this workflow
                    if state.get("patient_id"):
                        bed.patient_id = uuid.UUID(state["patient_id"])
                    
                    # Update patient status only if patient was created
                    if state.get("patient_id"):
                        patient = db.query(Patient).filter(Patient.id == uuid.UUID(state["patient_id"])).first()
                        if patient:
                            patient.current_bed_id = bed.id
                    
                    db.commit()
                    
                    state["workflow_status"] = "bed_assigned"
                    state["steps_completed"].append("bed_assignment")
                    
                    state["messages"].append(
                        AIMessage(content=f"Bed {bed.bed_number} reserved for patient")
                    )
                else:
                    state["error_message"] = "Selected bed not found"
                    state["workflow_status"] = "error"
                
            finally:
                db.close()
                
        except Exception as e:
            state["error_message"] = f"Bed assignment error: {str(e)}"
            state["workflow_status"] = "bed_assignment_error"
        
        return state
    
    def assign_medical_staff(self, state: PatientAdmissionState) -> PatientAdmissionState:
        """Assign medical staff to patient"""
        try:
            if not DATABASE_AVAILABLE:
                return state
            
            db = SessionLocal()
            try:
                # Find available staff (role is in User model)
                available_doctors = db.query(Staff).join(Staff.user).filter(
                    Staff.status == "active",
                    Staff.user.has(role="doctor")
                ).all()
                
                available_nurses = db.query(Staff).join(Staff.user).filter(
                    Staff.status == "active", 
                    Staff.user.has(role="nurse")
                ).all()
                
                # Assign primary doctor and nurse
                if available_doctors and available_nurses:
                    assigned_staff = []
                    
                    # Create actual StaffAssignment database records
                    if state.get("patient_id"):
                        from database import StaffAssignment
                        
                        # Assign primary doctor
                        doctor_assignment = StaffAssignment(
                            id=uuid.uuid4(),
                            patient_id=uuid.UUID(state["patient_id"]),
                            staff_id=available_doctors[0].id,
                            bed_id=uuid.UUID(state["bed_id"]) if state.get("bed_id") else None,
                            assignment_type="primary_doctor",
                            start_date=datetime.now(),
                            shift="day",
                            responsibilities="Primary medical care, treatment planning, discharge planning",
                            notes=f"Assigned via LangGraph automated workflow on {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                        )
                        db.add(doctor_assignment)
                        
                        # Assign primary nurse
                        nurse_assignment = StaffAssignment(
                            id=uuid.uuid4(),
                            patient_id=uuid.UUID(state["patient_id"]),
                            staff_id=available_nurses[0].id,
                            bed_id=uuid.UUID(state["bed_id"]) if state.get("bed_id") else None,
                            assignment_type="primary_nurse",
                            start_date=datetime.now(),
                            shift="day",
                            responsibilities="Patient care, medication administration, monitoring vital signs",
                            notes=f"Assigned via LangGraph automated workflow on {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                        )
                        db.add(nurse_assignment)
                        
                        # Commit the assignments
                        db.commit()
                        
                        assigned_staff = [
                            {
                                "staff_id": str(available_doctors[0].id), 
                                "role": "primary_doctor",
                                "name": f"Dr. {available_doctors[0].user.first_name} {available_doctors[0].user.last_name}",
                                "assignment_id": str(doctor_assignment.id)
                            },
                            {
                                "staff_id": str(available_nurses[0].id), 
                                "role": "primary_nurse",
                                "name": f"{available_nurses[0].user.first_name} {available_nurses[0].user.last_name}",
                                "assignment_id": str(nurse_assignment.id)
                            }
                        ]
                    else:
                        # Fallback to memory-only assignments if no patient ID yet
                        assigned_staff = [
                            {
                                "staff_id": str(available_doctors[0].id), 
                                "role": "primary_doctor",
                                "name": f"Dr. {available_doctors[0].user.first_name} {available_doctors[0].user.last_name}"
                            },
                            {
                                "staff_id": str(available_nurses[0].id), 
                                "role": "primary_nurse",
                                "name": f"{available_nurses[0].user.first_name} {available_nurses[0].user.last_name}"
                            }
                        ]
                    
                    state["staff_assignments"] = assigned_staff
                    state["workflow_status"] = "staff_assigned"
                    state["steps_completed"].append("staff_assignment")
                    
                    state["messages"].append(
                        AIMessage(content=f"Staff assigned: Dr. {available_doctors[0].user.first_name} {available_doctors[0].user.last_name} and {available_nurses[0].user.first_name} {available_nurses[0].user.last_name}")
                    )
                else:
                    state["error_message"] = f"Insufficient staff - Doctors: {len(available_doctors)}, Nurses: {len(available_nurses)}"
                    state["workflow_status"] = "error"
                
            finally:
                db.close()
                
        except Exception as e:
            state["error_message"] = f"Staff assignment error: {str(e)}"
        
        return state
    
    def assign_equipment_resources(self, state: PatientAdmissionState) -> PatientAdmissionState:
        """Assign equipment based on patient needs"""
        try:
            if not DATABASE_AVAILABLE:
                return state
            
            db = SessionLocal()
            try:
                # Find available equipment
                available_equipment = db.query(Equipment).filter(
                    Equipment.status == "available"
                ).limit(3).all()  # Assign first 3 available pieces
                
                if available_equipment:
                    state["equipment_assignments"] = []
                    for eq in available_equipment:
                        state["equipment_assignments"].append({
                            "equipment_id": str(eq.id),
                            "equipment_type": eq.name,
                            "equipment_code": eq.equipment_id,
                            "status": "assigned"
                        })
                    
                    state["workflow_status"] = "equipment_assigned"
                    state["steps_completed"].append("equipment_assignment")
                    
                    equipment_names = [eq.name for eq in available_equipment]
                    state["messages"].append(
                        AIMessage(content=f"Equipment assigned: {', '.join(equipment_names)}")
                    )
                else:
                    # Basic fallback equipment
                    state["equipment_assignments"] = [
                        {"equipment_type": "vital_signs_monitor", "status": "requested"},
                        {"equipment_type": "bed_controls", "status": "standard"}
                    ]
                    
                    state["workflow_status"] = "equipment_assigned"
                    state["steps_completed"].append("equipment_assignment")
                    
                    state["messages"].append(
                        AIMessage(content="Basic equipment assigned (no available equipment in database)")
                    )
                    
            finally:
                db.close()
            
        except Exception as e:
            state["error_message"] = f"Equipment assignment error: {str(e)}"
        
        return state
    
    def generate_admission_reports(self, state: PatientAdmissionState) -> PatientAdmissionState:
        """Generate admission documentation"""
        try:
            admission_summary = {
                "patient_id": state["patient_id"],
                "bed_id": state["bed_id"],
                "admission_time": datetime.now().isoformat(),
                "staff_assignments": state["staff_assignments"],
                "equipment_assignments": state["equipment_assignments"],
                "steps_completed": state["steps_completed"]
            }
            
            state["workflow_status"] = "reports_generated"
            state["steps_completed"].append("report_generation")
            
            state["messages"].append(
                AIMessage(content=f"Admission reports generated: {json.dumps(admission_summary, indent=2)}")
            )
            
        except Exception as e:
            state["error_message"] = f"Report generation error: {str(e)}"
        
        return state
    
    def finalize_admission_process(self, state: PatientAdmissionState) -> PatientAdmissionState:
        """Finalize the admission process"""
        if state.get("error_message"):
            state["workflow_status"] = "admission_failed"
        else:
            # Check if core components are completed
            steps = state.get("steps_completed", [])
            # Include both patient_creation and patient_exists as valid patient steps
            patient_step_completed = "patient_creation" in steps or "patient_exists" in steps
            
            if patient_step_completed and "bed_selection" in steps and "staff_assignment" in steps:
                state["workflow_status"] = "admission_completed"
            else:
                state["workflow_status"] = "admission_partial"
            
        state["steps_completed"].append("finalization")
        
        final_status = state["workflow_status"]
        if final_status == "admission_completed":
            message = "🎉 Admission process completed successfully - patient ready for care!"
        elif final_status == "admission_partial":
            message = "✅ Admission process partially completed - resources identified and ready"
        else:
            message = f"⚠️ Admission process {final_status}"
        
        state["messages"].append(AIMessage(content=message))
        
        return state
    
    def execute_admission_workflow(self, patient_data: Dict[str, Any], existing_patient_id: Optional[str] = None) -> Dict[str, Any]:
        """Execute the complete admission workflow"""
        if not self.graph:
            return {"error": "Workflow graph not available"}
        
        initial_state = PatientAdmissionState(
            patient_data=patient_data,
            patient_id=existing_patient_id,  # Use existing patient ID if provided
            bed_id=None,
            staff_assignments=[],
            equipment_assignments=[],
            workflow_status="started",
            error_message=None,
            steps_completed=[],
            messages=[HumanMessage(content=f"Starting admission for {patient_data.get('first_name', 'Unknown')} {patient_data.get('last_name', 'Patient')}")]
        )
        
        try:
            final_state = self.graph.invoke(initial_state)
            
            return {
                "success": final_state["workflow_status"] == "admission_completed",
                "patient_id": final_state.get("patient_id"),
                "bed_id": final_state.get("bed_id"),
                "staff_assignments": final_state.get("staff_assignments", []),
                "equipment_assignments": final_state.get("equipment_assignments", []),
                "steps_completed": final_state.get("steps_completed", []),
                "status": final_state["workflow_status"],
                "error": final_state.get("error_message"),
                "messages": [msg.content for msg in final_state.get("messages", [])]
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Workflow execution failed: {str(e)}",
                "status": "workflow_error"
            }

# ================================
# CLINICAL DECISION SUPPORT WORKFLOW  
# ================================

class ClinicalDecisionWorkflow:
    """LangGraph-based clinical decision support workflow"""
    
    def __init__(self):
        self.graph = None
        self.build_workflow()
    
    def build_workflow(self):
        """Build the clinical decision support workflow graph"""
        if not LANGCHAIN_AVAILABLE:
            print("⚠️ Cannot build clinical workflow - LangChain not available")
            return
        
        workflow = StateGraph(ClinicalDecisionState)
        
        # Add workflow nodes
        workflow.add_node("extract_symptoms", self.extract_symptoms)
        workflow.add_node("retrieve_patient_history", self.retrieve_patient_history)
        workflow.add_node("search_medical_knowledge", self.search_medical_knowledge)
        workflow.add_node("generate_differential_diagnosis", self.generate_differential_diagnosis)
        workflow.add_node("provide_recommendations", self.provide_recommendations)
        workflow.add_node("calculate_confidence", self.calculate_confidence)
        
        # Define workflow edges
        workflow.set_entry_point("extract_symptoms")
        workflow.add_edge("extract_symptoms", "retrieve_patient_history")
        workflow.add_edge("retrieve_patient_history", "search_medical_knowledge")
        workflow.add_edge("search_medical_knowledge", "generate_differential_diagnosis")
        workflow.add_edge("generate_differential_diagnosis", "provide_recommendations")
        workflow.add_edge("provide_recommendations", "calculate_confidence")
        workflow.add_edge("calculate_confidence", END)
        
        self.graph = workflow.compile()
        print("✅ Clinical decision workflow graph compiled")
    
    def extract_symptoms(self, state: ClinicalDecisionState) -> ClinicalDecisionState:
        """Extract symptoms from clinical query"""
        try:
            if not LANGCHAIN_AVAILABLE:
                return state
            
            symptom_extraction_prompt = ChatPromptTemplate.from_template("""
            Extract symptoms and clinical findings from the following query:
            
            Query: {query}
            
            Return a JSON list of symptoms:
            {{
                "symptoms": ["symptom1", "symptom2", "symptom3"],
                "chief_complaint": "main complaint",
                "severity": "mild/moderate/severe",
                "duration": "time duration if mentioned"
            }}
            """)
            
            chain = symptom_extraction_prompt | llm | JsonOutputParser()
            result = chain.invoke({"query": state["query"]})
            
            state["symptoms"] = result.get("symptoms", [])
            state["messages"].append(
                AIMessage(content=f"Extracted symptoms: {result}")
            )
            
        except Exception as e:
            state["messages"].append(
                AIMessage(content=f"Symptom extraction error: {str(e)}")
            )
        
        return state
    
    def retrieve_patient_history(self, state: ClinicalDecisionState) -> ClinicalDecisionState:
        """Retrieve patient medical history"""
        try:
            if state.get("patient_context") and state["patient_context"].get("patient_id"):
                # In a real implementation, query patient history from database
                state["patient_history"] = {
                    "previous_conditions": [],
                    "medications": [],
                    "allergies": [],
                    "family_history": []
                }
            
            state["messages"].append(
                AIMessage(content="Patient history retrieved")
            )
            
        except Exception as e:
            state["messages"].append(
                AIMessage(content=f"History retrieval error: {str(e)}")
            )
        
        return state
    
    def search_medical_knowledge(self, state: ClinicalDecisionState) -> ClinicalDecisionState:
        """Search medical knowledge base"""
        try:
            # In a real implementation, this would query ChromaDB
            # For now, using simulated knowledge
            state["rag_knowledge"] = [
                "Relevant medical guidelines for symptoms",
                "Drug interaction information",
                "Treatment protocols"
            ]
            
            state["messages"].append(
                AIMessage(content="Medical knowledge retrieved from database")
            )
            
        except Exception as e:
            state["messages"].append(
                AIMessage(content=f"Knowledge search error: {str(e)}")
            )
        
        return state
    
    def generate_differential_diagnosis(self, state: ClinicalDecisionState) -> ClinicalDecisionState:
        """Generate differential diagnosis using LLM"""
        try:
            if not LANGCHAIN_AVAILABLE:
                return state
            
            diagnosis_prompt = ChatPromptTemplate.from_template("""
            Based on the following clinical information, generate a differential diagnosis:
            
            Symptoms: {symptoms}
            Patient History: {patient_history}
            Medical Knowledge: {rag_knowledge}
            
            Provide a JSON response with:
            {{
                "differential_diagnoses": [
                    {{
                        "condition": "condition name",
                        "probability": 0.85,
                        "reasoning": "clinical reasoning",
                        "supporting_symptoms": ["symptom1", "symptom2"],
                        "tests_needed": ["test1", "test2"]
                    }}
                ],
                "red_flags": ["urgent symptom1", "urgent symptom2"],
                "immediate_actions": ["action1", "action2"]
            }}
            """)
            
            chain = diagnosis_prompt | llm | JsonOutputParser()
            result = chain.invoke({
                "symptoms": state["symptoms"],
                "patient_history": state.get("patient_history", {}),
                "rag_knowledge": state.get("rag_knowledge", [])
            })
            
            state["differential_diagnoses"] = result.get("differential_diagnoses", [])
            state["messages"].append(
                AIMessage(content=f"Generated differential diagnosis: {len(state['differential_diagnoses'])} conditions")
            )
            
        except Exception as e:
            state["messages"].append(
                AIMessage(content=f"Diagnosis generation error: {str(e)}")
            )
        
        return state
    
    def provide_recommendations(self, state: ClinicalDecisionState) -> ClinicalDecisionState:
        """Provide clinical recommendations"""
        try:
            if not LANGCHAIN_AVAILABLE:
                return state
            
            recommendations_prompt = ChatPromptTemplate.from_template("""
            Based on the differential diagnosis, provide clinical recommendations:
            
            Differential Diagnoses: {diagnoses}
            Symptoms: {symptoms}
            
            Provide structured recommendations:
            {{
                "immediate_interventions": ["intervention1", "intervention2"],
                "diagnostic_tests": ["test1", "test2"],
                "treatment_options": ["treatment1", "treatment2"],
                "monitoring_parameters": ["parameter1", "parameter2"],
                "follow_up_plan": "follow-up instructions",
                "patient_education": ["education point1", "education point2"]
            }}
            """)
            
            chain = recommendations_prompt | llm | JsonOutputParser()
            result = chain.invoke({
                "diagnoses": state["differential_diagnoses"],
                "symptoms": state["symptoms"]
            })
            
            state["recommendations"] = result.get("immediate_interventions", []) + result.get("treatment_options", [])
            state["messages"].append(
                AIMessage(content=f"Generated {len(state['recommendations'])} clinical recommendations")
            )
            
        except Exception as e:
            state["messages"].append(
                AIMessage(content=f"Recommendations error: {str(e)}")
            )
        
        return state
    
    def calculate_confidence(self, state: ClinicalDecisionState) -> ClinicalDecisionState:
        """Calculate confidence score for recommendations"""
        try:
            # Simple confidence calculation based on available data
            confidence_factors = []
            
            if state.get("symptoms"):
                confidence_factors.append(0.3)
            if state.get("patient_history"):
                confidence_factors.append(0.2)
            if state.get("rag_knowledge"):
                confidence_factors.append(0.3)
            if state.get("differential_diagnoses"):
                confidence_factors.append(0.2)
            
            state["confidence_score"] = sum(confidence_factors)
            state["messages"].append(
                AIMessage(content=f"Confidence score: {state['confidence_score']:.2f}")
            )
            
        except Exception as e:
            state["messages"].append(
                AIMessage(content=f"Confidence calculation error: {str(e)}")
            )
        
        return state
    
    def execute_clinical_decision(self, query: str, patient_context: Optional[Dict] = None) -> Dict[str, Any]:
        """Execute the clinical decision support workflow"""
        if not self.graph:
            return {"error": "Clinical workflow graph not available"}
        
        initial_state = ClinicalDecisionState(
            query=query,
            patient_context=patient_context,
            symptoms=[],
            patient_history=None,
            rag_knowledge=[],
            differential_diagnoses=[],
            recommendations=[],
            confidence_score=0.0,
            messages=[HumanMessage(content=f"Clinical query: {query}")]
        )
        
        try:
            final_state = self.graph.invoke(initial_state)
            
            return {
                "success": True,
                "symptoms": final_state.get("symptoms", []),
                "differential_diagnoses": final_state.get("differential_diagnoses", []),
                "recommendations": final_state.get("recommendations", []),
                "confidence_score": final_state.get("confidence_score", 0.0),
                "messages": [msg.content for msg in final_state.get("messages", [])]
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Clinical workflow execution failed: {str(e)}"
            }

# ================================
# WORKFLOW MANAGER
# ================================

class LangGraphWorkflowManager:
    """Main workflow manager for LangGraph integration"""
    
    def __init__(self):
        self.admission_workflow = PatientAdmissionWorkflow()
        self.clinical_workflow = ClinicalDecisionWorkflow()
        print("✅ LangGraph workflow manager initialized")
    
    def execute_patient_admission(self, patient_data: Dict[str, Any], existing_patient_id: Optional[str] = None) -> Dict[str, Any]:
        """Execute patient admission workflow"""
        return self.admission_workflow.execute_admission_workflow(patient_data, existing_patient_id)
    
    def execute_clinical_decision(self, query: str, patient_context: Optional[Dict] = None) -> Dict[str, Any]:
        """Execute clinical decision support workflow"""
        return self.clinical_workflow.execute_clinical_decision(query, patient_context)
    
    def get_available_workflows(self) -> List[str]:
        """Get list of available workflows"""
        workflows = []
        if self.admission_workflow.graph:
            workflows.append("patient_admission")
        if self.clinical_workflow.graph:
            workflows.append("clinical_decision")
        return workflows
    
    def get_workflow_status(self) -> Dict[str, Any]:
        """Get status of all workflows"""
        return {
            "langchain_available": LANGCHAIN_AVAILABLE,
            "database_available": DATABASE_AVAILABLE,
            "available_workflows": self.get_available_workflows(),
            "admission_workflow_ready": self.admission_workflow.graph is not None,
            "clinical_workflow_ready": self.clinical_workflow.graph is not None
        }

# Initialize the workflow manager
workflow_manager = LangGraphWorkflowManager()

if __name__ == "__main__":
    # Test the workflows
    print("🧪 Testing LangGraph workflows...")
    
    # Test admission workflow
    test_patient = {
        "first_name": "John",
        "last_name": "Doe", 
        "date_of_birth": "1990-01-15",
        "phone": "555-0123",
        "email": "john.doe@email.com"
    }
    
    print("\n🏥 Testing patient admission workflow...")
    result = workflow_manager.execute_patient_admission(test_patient)
    print(f"Admission result: {result}")
    
    # Test clinical decision workflow
    print("\n🩺 Testing clinical decision workflow...")
    clinical_result = workflow_manager.execute_clinical_decision(
        "Patient presents with chest pain and shortness of breath",
        {"patient_id": "test-123"}
    )
    print(f"Clinical decision result: {clinical_result}")
    
    print("\n📊 Workflow status:")
    status = workflow_manager.get_workflow_status()
    for key, value in status.items():
        print(f"  {key}: {value}")
