"""
AI Clinical Assistant Agent - Intelligent Virtual Assistant for Clinical Decision Support
Provides AI-powered clinical assistance, drug dosage recommendations, treatment protocols, and diagnostic support.
"""

import json
import re
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from agents.base_agent import BaseAgent

# Database imports
try:
    from database import Patient, Staff, Department, Equipment, Supply, SessionLocal
    DATABASE_AVAILABLE = True
except ImportError:
    DATABASE_AVAILABLE = False
    print("WARNING: Database not available for AI Clinical Assistant")

# AI and NLP imports
try:
    # OpenAI for primary AI functionality
    import openai
    import os
    
    # Configure OpenAI
    openai_api_key = os.getenv('VITE_OPENAI_API_KEY') or os.getenv('OPENAI_API_KEY')
    if openai_api_key:
        AI_AVAILABLE = True
        AI_PROVIDER = "openai"
        print("✅ OpenAI configured for clinical assistant")
    else:
        AI_AVAILABLE = False
        AI_PROVIDER = None
        print("⚠️ OpenAI API key not found - AI features disabled")

    # ChromaDB for RAG capabilities
    import chromadb
    from chromadb.utils import embedding_functions
    RAG_AVAILABLE = True
    print("✅ ChromaDB available for RAG")

except ImportError as e:
    AI_AVAILABLE = False
    RAG_AVAILABLE = False
    AI_PROVIDER = None
    print(f"⚠️ AI/RAG libraries not available: {e}")

# Medical knowledge base for clinical assistance
MEDICAL_KNOWLEDGE = {
    "drug_interactions": {
        "warfarin": ["aspirin", "ibuprofen", "phenytoin", "rifampin"],
        "digoxin": ["quinidine", "verapamil", "amiodarone"],
        "lithium": ["thiazides", "nsaids", "ace_inhibitors"],
        "phenytoin": ["warfarin", "carbamazepine", "valproic_acid"]
    },
    "contraindications": {
        "pregnancy": ["warfarin", "phenytoin", "lithium", "ace_inhibitors"],
        "kidney_disease": ["nsaids", "lithium", "metformin"],
        "liver_disease": ["acetaminophen", "statins", "phenytoin"],
        "heart_failure": ["nsaids", "certain_calcium_blockers"]
    },
    "dosage_guidelines": {
        "acetaminophen": {"adult": "325-650mg q4-6h, max 3g/day", "pediatric": "10-15mg/kg q4-6h"},
        "ibuprofen": {"adult": "200-400mg q4-6h, max 1.2g/day", "pediatric": "5-10mg/kg q6-8h"},
        "amoxicillin": {"adult": "250-500mg q8h", "pediatric": "20-40mg/kg/day divided q8h"},
        "metformin": {"adult": "500mg BID, titrate to max 2g/day", "pediatric": "Not recommended <10 years"}
    },
    "vital_signs_normal": {
        "adult": {
            "heart_rate": (60, 100),
            "blood_pressure": (90, 140, 60, 90),  # systolic_min, systolic_max, diastolic_min, diastolic_max
            "respiratory_rate": (12, 20),
            "temperature": (36.1, 37.2),  # Celsius
            "oxygen_saturation": (95, 100)
        },
        "pediatric": {
            "heart_rate": (80, 130),
            "blood_pressure": (80, 120, 50, 80),
            "respiratory_rate": (20, 30),
            "temperature": (36.1, 37.2),
            "oxygen_saturation": (95, 100)
        }
    }
}

class AIClinicalAssistantAgent(BaseAgent):
    def __init__(self):
        super().__init__("AI Clinical Assistant Agent", "ai_clinical_assistant")
        self.agent_name = "AI Clinical Assistant"
        self.agent_description = "Intelligent virtual assistant providing clinical decision support, drug recommendations, and diagnostic assistance"
        
        # Set instance variables for AI and RAG availability
        self.ai_available = AI_AVAILABLE
        self.rag_available = RAG_AVAILABLE
        
        # Initialize OpenAI client
        if AI_AVAILABLE:
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=os.getenv('VITE_OPENAI_API_KEY') or os.getenv('OPENAI_API_KEY'))
                print("✅ OpenAI client initialized for AI Clinical Assistant")
            except Exception as e:
                print(f"⚠️ Failed to initialize OpenAI client: {e}")
                self.client = None
        else:
            self.client = None
        
        # Initialize ChromaDB for RAG
        if self.rag_available:
            try:
                # Determine the best path for ChromaDB storage
                # Enhanced Docker detection
                is_docker = (
                    os.path.exists('/.dockerenv') or 
                    os.environ.get('HOSTNAME', '').startswith('hospital-backend') or
                    os.path.exists('/proc/self/cgroup') and 'docker' in open('/proc/self/cgroup').read()
                )
                
                if is_docker:
                    # In Docker, prefer mounted volume with fallback to /tmp
                    db_paths = [
                        "/app/medical_knowledge_db",
                        "/tmp/medical_knowledge_db",
                        "/app/tmp_medical_db"
                    ]
                else:
                    # In local development, prefer current directory then temp
                    import tempfile
                    temp_path = os.path.join(tempfile.gettempdir(), "medical_knowledge_db")
                    db_paths = [
                        "./medical_knowledge_db", 
                        temp_path,
                        "/tmp/medical_knowledge_db"  # Additional fallback
                    ]
                
                db_path = None
                for path in db_paths:
                    try:
                        os.makedirs(path, exist_ok=True)
                        # Test write permission
                        test_file = os.path.join(path, "test_write.tmp")
                        with open(test_file, 'w') as f:
                            f.write("test")
                        os.remove(test_file)
                        db_path = path
                        print(f"✅ ChromaDB directory writable: {path}")
                        break
                    except (OSError, PermissionError) as e:
                        print(f"⚠️ Cannot use path {path}: {e}")
                        continue
                
                if not db_path:
                    # Final fallback - use memory-only ChromaDB
                    print("⚠️ No writable path found, using in-memory ChromaDB")
                    self.chroma_client = chromadb.Client()
                else:
                    print(f"📂 Using ChromaDB path: {db_path}")
                    self.chroma_client = chromadb.PersistentClient(path=db_path)
                
                # Get or create collection for medical knowledge
                self.knowledge_collection = self.chroma_client.get_or_create_collection(
                    name="medical_knowledge",
                    embedding_function=embedding_functions.DefaultEmbeddingFunction()
                )
                self._initialize_medical_knowledge()
                print("✅ Medical knowledge RAG initialized")
            except Exception as e:
                print(f"⚠️ Failed to initialize RAG: {e}")
                self.rag_available = False
    
    def get_tools(self) -> List[str]:
        """Return list of AI clinical assistant tools"""
        return [
            "ai_clinical_assistant",
            "process_clinical_notes", 
            "get_drug_interactions",
            "analyze_vital_signs",
            "generate_differential_diagnosis"
        ]
    
    def get_capabilities(self) -> List[str]:
        """Return list of agent capabilities"""
        capabilities = [
            "Clinical decision support",
            "Drug interaction checking", 
            "Vital signs analysis",
            "Differential diagnosis generation",
            "Clinical notes processing",
            "Treatment recommendations"
        ]
        
        if self.ai_available:
            capabilities.append(f"AI-powered analysis ({AI_PROVIDER})")
        if self.rag_available:
            capabilities.append("RAG-enhanced medical knowledge")
            
        return capabilities
    
    def _call_openai(self, prompt: str, temperature: float = 0.3) -> str:
        """Call OpenAI API with error handling"""
        try:
            if not self.client:
                return "OpenAI client not available. Please check your API key configuration."
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert clinical decision support AI assistant. Provide evidence-based medical guidance while emphasizing the need for professional medical judgment and clinical correlation."},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=1500
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"OpenAI API error: {e}")
            return f"AI analysis temporarily unavailable: {str(e)}"
    
    def _search_medical_knowledge(self, query: str, n_results: int = 5) -> List[str]:
        """Search medical knowledge base using RAG"""
        if not self.rag_available:
            return []
        
        try:
            results = self.knowledge_collection.query(
                query_texts=[query],
                n_results=n_results
            )
            return results.get('documents', [[]])[0]
        except Exception as e:
            print(f"RAG search error: {e}")
            return []
    
    def _initialize_medical_knowledge(self):
        """Initialize medical knowledge base with clinical information"""
        try:
            # Check if knowledge base is already populated
            collection_count = self.knowledge_collection.count()
            if collection_count > 0:
                print(f"Medical knowledge base already contains {collection_count} entries")
                return
            
            # Add medical knowledge entries
            medical_knowledge_entries = [
                {
                    "id": "drug_interactions_warfarin",
                    "text": "Warfarin interactions: Aspirin increases bleeding risk, Phenytoin affects metabolism, Rifampin decreases effectiveness. Monitor INR closely with any changes.",
                    "category": "drug_interactions"
                },
                {
                    "id": "acetaminophen_dosing",
                    "text": "Acetaminophen: Adults 325-650mg q4-6h, max 3g/day. Pediatric 10-15mg/kg q4-6h. Reduce dose in liver disease. Avoid with alcohol use.",
                    "category": "dosage_guidelines"
                },
                {
                    "id": "vital_signs_normal_adult",
                    "text": "Normal adult vital signs: HR 60-100 bpm, BP <140/90 mmHg, RR 12-20/min, Temp 36.1-37.2°C, O2 Sat >95%. Age-specific variations apply.",
                    "category": "vital_signs"
                },
                {
                    "id": "chest_pain_differential",
                    "text": "Chest pain differential: MI, PE, aortic dissection, pneumothorax, GERD, costochondritis. Consider cardiac causes first in risk factors present.",
                    "category": "differential_diagnosis"
                },
                {
                    "id": "pneumonia_antibiotics",
                    "text": "Community-acquired pneumonia: Amoxicillin 500mg TID or azithromycin 500mg daily. Severe cases: ceftriaxone + azithromycin. Adjust for local resistance.",
                    "category": "treatment_guidelines"
                }
            ]
            
            # Add to ChromaDB
            for entry in medical_knowledge_entries:
                self.knowledge_collection.add(
                    documents=[entry["text"]],
                    ids=[entry["id"]],
                    metadatas=[{"category": entry["category"]}]
                )
            
            print("✅ Medical knowledge base initialized with clinical guidelines")
            
        except Exception as e:
            print(f"⚠️ Failed to initialize medical knowledge: {e}")
    
    def get_capabilities(self) -> List[str]:
        """Return list of AI clinical assistant capabilities"""
        return [
            "clinical_decision_support",
            "drug_interaction_checking",
            "vital_signs_analysis", 
            "differential_diagnosis",
            "clinical_note_processing",
            "natural_language_processing",
            "medical_knowledge_base",
            "ai_powered_insights"
        ]
    
    def ai_clinical_assistant(self, query: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        AI assistant for clinical decision support
        
        Args:
            query: Clinical question or scenario
            context: Additional context (patient_id, medical_history, etc.)
        
        Returns:
            Dict containing AI recommendations and clinical insights
        """
        try:
            if not AI_AVAILABLE:
                return {
                    "success": False,
                    "error": "AI services are not available. Please check API configuration.",
                    "recommendations": []
                }
            
            # Parse context
            patient_id = context.get('patient_id') if context else None
            patient_data = None
            
            if patient_id:
                db = self.get_db_session()
                try:
                    patient = db.query(Patient).filter(Patient.id == patient_id).first()
                    if patient:
                        patient_data = {
                            "age": self._calculate_age(patient.date_of_birth) if patient.date_of_birth else None,
                            "gender": patient.gender,
                            "medical_history": patient.medical_history,
                            "allergies": patient.allergies,
                            "current_medications": patient.current_medications
                        }
                finally:
                    db.close()
            
            # Prepare AI prompt with medical context
            prompt = self._build_clinical_prompt(query, patient_data, context)
            
            # Search RAG knowledge base for relevant information
            rag_context = ""
            if self.rag_available:
                relevant_docs = self._search_medical_knowledge(query)
                if relevant_docs:
                    rag_context = "\n\nRelevant clinical knowledge:\n" + "\n".join(relevant_docs)
                    prompt += rag_context
            
            # Get AI response
            ai_response = self._call_openai(prompt)
            
            # Parse AI response and add structured recommendations
            structured_response = self._parse_ai_clinical_response(ai_response, query)
            
            # Add safety checks and contraindication warnings
            safety_checks = self._perform_safety_checks(query, patient_data)
            
            # Combine AI response with rule-based checks
            result = {
                "success": True,
                "query": query,
                "ai_response": ai_response,
                "structured_recommendations": structured_response,
                "safety_checks": safety_checks,
                "patient_context": patient_data,
                "timestamp": datetime.now().isoformat(),
                "disclaimer": "This is AI-generated clinical assistance. Always verify with current medical guidelines and consult with qualified healthcare professionals."
            }
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": f"AI clinical assistant error: {str(e)}",
                "query": query,
                "timestamp": datetime.now().isoformat()
            }
    
    def process_clinical_notes(self, document_text: str, extract_type: str = "comprehensive") -> Dict[str, Any]:
        """
        Extract structured data from clinical notes using NLP
        
        Args:
            document_text: Raw clinical notes text
            extract_type: Type of extraction (symptoms, diagnosis, treatment, medications, comprehensive)
        
        Returns:
            Dict containing extracted structured clinical data
        """
        try:
            if not AI_AVAILABLE:
                return {
                    "success": False,
                    "error": "AI services are not available for clinical note processing.",
                    "extracted_data": {}
                }
            
            # Prepare extraction prompt based on type
            extraction_prompt = self._build_extraction_prompt(document_text, extract_type)
            
            # Search RAG for relevant clinical extraction examples
            rag_context = ""
            if self.rag_available:
                relevant_docs = self._search_medical_knowledge(f"clinical notes {extract_type} extraction")
                if relevant_docs:
                    rag_context = "\n\nClinical extraction guidelines:\n" + "\n".join(relevant_docs[:2])
                    extraction_prompt += rag_context
            
            # Get AI extraction
            ai_response = self._call_openai(extraction_prompt)
            
            # Parse structured data from AI response
            extracted_data = self._parse_clinical_extraction(ai_response, extract_type)
            
            # Apply rule-based validation and enhancement
            validated_data = self._validate_extracted_data(extracted_data)
            
            # Add confidence scores and metadata
            result = {
                "success": True,
                "original_text": document_text,
                "extract_type": extract_type,
                "extracted_data": validated_data,
                "ai_raw_response": ai_response,
                "processing_timestamp": datetime.now().isoformat(),
                "confidence_score": self._calculate_extraction_confidence(validated_data),
                "validation_notes": self._get_validation_notes(validated_data)
            }
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Clinical note processing error: {str(e)}",
                "original_text": document_text,
                "extract_type": extract_type,
                "timestamp": datetime.now().isoformat()
            }
    
    def get_drug_interactions(self, medications: List[str], patient_context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Check for drug interactions and contraindications
        
        Args:
            medications: List of medication names
            patient_context: Patient information (allergies, conditions, etc.)
        
        Returns:
            Dict containing interaction warnings and recommendations
        """
        try:
            interactions = []
            contraindications = []
            warnings = []
            
            # Check drug-drug interactions
            for i, med1 in enumerate(medications):
                for med2 in medications[i+1:]:
                    interaction = self._check_drug_interaction(med1.lower(), med2.lower())
                    if interaction:
                        interactions.append(interaction)
            
            # Check contraindications
            if patient_context:
                for medication in medications:
                    contraindication = self._check_contraindications(medication.lower(), patient_context)
                    if contraindication:
                        contraindications.append(contraindication)
            
            # Get AI-powered additional insights
            if AI_AVAILABLE and medications:
                ai_insights = self._get_ai_drug_insights(medications, patient_context)
            else:
                ai_insights = "AI drug analysis not available"
            
            return {
                "success": True,
                "medications": medications,
                "interactions": interactions,
                "contraindications": contraindications,
                "warnings": warnings,
                "ai_insights": ai_insights,
                "recommendation": self._generate_medication_recommendation(interactions, contraindications),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Drug interaction check error: {str(e)}",
                "medications": medications,
                "timestamp": datetime.now().isoformat()
            }
    
    def analyze_vital_signs(self, vital_signs: Dict[str, float], patient_age: Optional[int] = None) -> Dict[str, Any]:
        """
        Analyze vital signs and provide clinical insights
        
        Args:
            vital_signs: Dict of vital sign measurements
            patient_age: Patient age for age-appropriate normal ranges
        
        Returns:
            Dict containing vital signs analysis and recommendations
        """
        try:
            age_group = "pediatric" if patient_age and patient_age < 18 else "adult"
            normal_ranges = MEDICAL_KNOWLEDGE["vital_signs_normal"][age_group]
            
            analysis = {}
            alerts = []
            
            # Analyze each vital sign
            for vital, value in vital_signs.items():
                if vital in ["heart_rate", "respiratory_rate", "oxygen_saturation"]:
                    min_val, max_val = normal_ranges.get(vital, (0, 999))
                    status = "normal"
                    if value < min_val:
                        status = "low"
                        alerts.append(f"{vital.replace('_', ' ').title()} is below normal range")
                    elif value > max_val:
                        status = "high"
                        alerts.append(f"{vital.replace('_', ' ').title()} is above normal range")
                    
                    analysis[vital] = {
                        "value": value,
                        "normal_range": f"{min_val}-{max_val}",
                        "status": status
                    }
                
                elif vital == "blood_pressure" and isinstance(value, tuple) and len(value) == 2:
                    systolic, diastolic = value
                    sys_min, sys_max, dia_min, dia_max = normal_ranges["blood_pressure"]
                    
                    sys_status = "normal" if sys_min <= systolic <= sys_max else ("low" if systolic < sys_min else "high")
                    dia_status = "normal" if dia_min <= diastolic <= dia_max else ("low" if diastolic < dia_min else "high")
                    
                    if sys_status != "normal":
                        alerts.append(f"Systolic BP is {sys_status}")
                    if dia_status != "normal":
                        alerts.append(f"Diastolic BP is {dia_status}")
                    
                    analysis["blood_pressure"] = {
                        "systolic": {"value": systolic, "status": sys_status},
                        "diastolic": {"value": diastolic, "status": dia_status},
                        "normal_range": f"{sys_min}-{sys_max}/{dia_min}-{dia_max}"
                    }
            
            # Generate AI-powered insights if available
            ai_insights = ""
            if AI_AVAILABLE:
                vital_prompt = f"""
                Analyze these vital signs for a {age_group} patient:
                {json.dumps(vital_signs, indent=2)}
                
                Current analysis shows: {alerts}
                
                Provide clinical insights, potential causes, and recommendations.
                """
                
                try:
                    ai_response = self._call_openai(vital_prompt)
                    ai_insights = ai_response
                except:
                    ai_insights = "AI analysis temporarily unavailable"
            
            return {
                "success": True,
                "vital_signs": vital_signs,
                "age_group": age_group,
                "analysis": analysis,
                "alerts": alerts,
                "ai_insights": ai_insights,
                "overall_status": "critical" if any("high" in alert.lower() or "low" in alert.lower() for alert in alerts) else "normal",
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Vital signs analysis error: {str(e)}",
                "vital_signs": vital_signs,
                "timestamp": datetime.now().isoformat()
            }
    
    def generate_differential_diagnosis(self, symptoms: List[str], patient_context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Generate differential diagnosis based on symptoms
        
        Args:
            symptoms: List of patient symptoms
            patient_context: Patient demographics and history
        
        Returns:
            Dict containing differential diagnosis suggestions
        """
        try:
            if not AI_AVAILABLE:
                return {
                    "success": False,
                    "error": "AI services required for differential diagnosis generation",
                    "symptoms": symptoms
                }
            
            # Build comprehensive prompt for differential diagnosis
            context_str = ""
            if patient_context:
                age = patient_context.get('age', 'unknown')
                gender = patient_context.get('gender', 'unknown')
                history = patient_context.get('medical_history', 'none provided')
                context_str = f"Patient: {age} years old, {gender}, Medical history: {history}"
            
            diagnosis_prompt = f"""
            As a clinical decision support system, generate a differential diagnosis for the following case:
            
            {context_str}
            
            Presenting symptoms:
            {', '.join(symptoms)}
            
            Please provide:
            1. Top 5 most likely diagnoses with probability estimates
            2. Additional symptoms to assess
            3. Recommended diagnostic tests
            4. Red flag symptoms to watch for
            5. Immediate actions if needed
            
            Format as structured JSON.
            """
            
            # Search RAG for relevant differential diagnosis information
            rag_context = ""
            if self.rag_available:
                relevant_docs = self._search_medical_knowledge(" ".join(symptoms))
                if relevant_docs:
                    rag_context = "\n\nRelevant clinical knowledge:\n" + "\n".join(relevant_docs[:3])
                    diagnosis_prompt += rag_context

            ai_response = self._call_openai(diagnosis_prompt)
            
            # Parse AI response
            parsed_diagnosis = self._parse_differential_diagnosis(ai_response)
            
            return {
                "success": True,
                "symptoms": symptoms,
                "patient_context": patient_context,
                "differential_diagnosis": parsed_diagnosis,
                "ai_raw_response": ai_response,
                "generated_at": datetime.now().isoformat(),
                "disclaimer": "This is AI-generated diagnostic assistance. Clinical correlation and professional medical judgment are essential."
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Differential diagnosis generation error: {str(e)}",
                "symptoms": symptoms,
                "timestamp": datetime.now().isoformat()
            }
    
    # Helper methods
    def _calculate_age(self, birth_date):
        """Calculate age from birth date"""
        if not birth_date:
            return None
        return (datetime.now().date() - birth_date).days // 365
    
    def _build_clinical_prompt(self, query: str, patient_data: Optional[Dict], context: Optional[Dict]) -> str:
        """Build comprehensive clinical prompt for AI"""
        prompt = f"""
        You are an advanced clinical decision support AI assistant. Please provide evidence-based clinical guidance for the following query:

        Query: {query}
        """
        
        if patient_data:
            prompt += f"""
        
        Patient Context:
        - Age: {patient_data.get('age', 'unknown')}
        - Gender: {patient_data.get('gender', 'unknown')}
        - Medical History: {patient_data.get('medical_history', 'none provided')}
        - Known Allergies: {patient_data.get('allergies', 'none provided')}
        - Current Medications: {patient_data.get('current_medications', 'none provided')}
        """
        
        prompt += """
        
        Please provide:
        1. Clinical assessment and recommendations
        2. Relevant differential diagnoses if applicable
        3. Suggested diagnostic workup
        4. Treatment considerations
        5. Safety warnings and contraindications
        6. Follow-up recommendations
        
        Always emphasize the need for clinical correlation and professional medical judgment.
        """
        
        return prompt
    
    def _parse_ai_clinical_response(self, ai_response: str, query: str) -> Dict[str, Any]:
        """Parse AI response into structured format"""
        try:
            # Try to extract structured information
            structured = {
                "assessment": "",
                "recommendations": [],
                "warnings": [],
                "follow_up": ""
            }
            
            # Simple parsing - in production, this would be more sophisticated
            lines = ai_response.split('\n')
            current_section = "assessment"
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                if any(keyword in line.lower() for keyword in ["recommend", "suggest", "consider"]):
                    current_section = "recommendations"
                    if line not in structured["recommendations"]:
                        structured["recommendations"].append(line)
                elif any(keyword in line.lower() for keyword in ["warning", "caution", "contraindic", "avoid"]):
                    current_section = "warnings"
                    if line not in structured["warnings"]:
                        structured["warnings"].append(line)
                elif any(keyword in line.lower() for keyword in ["follow", "monitor", "reassess"]):
                    current_section = "follow_up"
                    structured["follow_up"] += line + " "
                else:
                    if current_section == "assessment":
                        structured["assessment"] += line + " "
            
            return structured
            
        except Exception:
            return {"raw_response": ai_response}
    
    def _perform_safety_checks(self, query: str, patient_data: Optional[Dict]) -> List[str]:
        """Perform rule-based safety checks"""
        warnings = []
        
        if not patient_data:
            return warnings
        
        # Check for pregnancy-related contraindications
        if patient_data.get('gender') == 'female':
            query_lower = query.lower()
            if any(drug in query_lower for drug in MEDICAL_KNOWLEDGE["contraindications"]["pregnancy"]):
                warnings.append("WARNING: Some medications mentioned may be contraindicated in pregnancy. Verify pregnancy status.")
        
        # Check for age-related concerns
        age = patient_data.get('age')
        if age and age > 65:
            warnings.append("GERIATRIC ALERT: Consider age-related dose adjustments and increased monitoring.")
        elif age and age < 18:
            warnings.append("PEDIATRIC ALERT: Verify pediatric dosing and contraindications.")
        
        return warnings
    
    def _build_extraction_prompt(self, text: str, extract_type: str) -> str:
        """Build prompt for clinical note extraction"""
        base_prompt = f"""
        Extract structured clinical information from the following medical note:

        {text}

        Extract and format as JSON:
        """
        
        if extract_type == "symptoms":
            return base_prompt + """
            {
                "chief_complaint": "",
                "symptoms": [],
                "duration": "",
                "severity": "",
                "associated_symptoms": []
            }
            """
        elif extract_type == "diagnosis":
            return base_prompt + """
            {
                "primary_diagnosis": "",
                "secondary_diagnoses": [],
                "differential_diagnosis": [],
                "icd_codes": []
            }
            """
        elif extract_type == "treatment":
            return base_prompt + """
            {
                "medications": [],
                "procedures": [],
                "treatments": [],
                "follow_up_plan": ""
            }
            """
        elif extract_type == "medications":
            return base_prompt + """
            {
                "current_medications": [],
                "new_prescriptions": [],
                "discontinued_medications": [],
                "allergies": []
            }
            """
        else:  # comprehensive
            return base_prompt + """
            {
                "patient_info": {
                    "chief_complaint": "",
                    "history_present_illness": ""
                },
                "symptoms": [],
                "vital_signs": {},
                "physical_exam": {},
                "diagnoses": {
                    "primary": "",
                    "secondary": []
                },
                "medications": [],
                "procedures": [],
                "plan": "",
                "follow_up": ""
            }
            """
    
    def _parse_clinical_extraction(self, ai_response: str, extract_type: str) -> Dict[str, Any]:
        """Parse AI extraction response"""
        try:
            # Try to parse JSON response
            if '{' in ai_response and '}' in ai_response:
                start = ai_response.find('{')
                end = ai_response.rfind('}') + 1
                json_str = ai_response[start:end]
                return json.loads(json_str)
        except:
            pass
        
        # Fallback to simple parsing
        return {"raw_extraction": ai_response, "parsing_method": "fallback"}
    
    def _validate_extracted_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and enhance extracted data"""
        # Add validation logic here
        validated = data.copy()
        
        # Add validation flags
        validated["validation"] = {
            "has_medications": bool(data.get("medications")),
            "has_diagnoses": bool(data.get("diagnoses") or data.get("primary_diagnosis")),
            "has_symptoms": bool(data.get("symptoms")),
            "completeness_score": self._calculate_completeness(data)
        }
        
        return validated
    
    def _calculate_completeness(self, data: Dict[str, Any]) -> float:
        """Calculate data completeness score"""
        fields = ["symptoms", "diagnoses", "medications", "vital_signs", "plan"]
        present_fields = sum(1 for field in fields if data.get(field))
        return present_fields / len(fields)
    
    def _calculate_extraction_confidence(self, data: Dict[str, Any]) -> float:
        """Calculate confidence score for extraction"""
        if "validation" in data:
            return data["validation"]["completeness_score"]
        return 0.5
    
    def _get_validation_notes(self, data: Dict[str, Any]) -> List[str]:
        """Get validation notes for extracted data"""
        notes = []
        if data.get("parsing_method") == "fallback":
            notes.append("Used fallback parsing - manual review recommended")
        return notes
    
    def _check_drug_interaction(self, med1: str, med2: str) -> Optional[Dict[str, str]]:
        """Check for drug-drug interactions"""
        interactions = MEDICAL_KNOWLEDGE["drug_interactions"]
        
        for drug, interacting_drugs in interactions.items():
            if (drug in med1 and any(interact in med2 for interact in interacting_drugs)) or \
               (drug in med2 and any(interact in med1 for interact in interacting_drugs)):
                return {
                    "medication_1": med1,
                    "medication_2": med2,
                    "interaction_type": "drug-drug",
                    "severity": "moderate",
                    "description": f"Potential interaction between {med1} and {med2}"
                }
        
        return None
    
    def _check_contraindications(self, medication: str, patient_context: Dict) -> Optional[Dict[str, str]]:
        """Check for medication contraindications"""
        contraindications = MEDICAL_KNOWLEDGE["contraindications"]
        
        # Check pregnancy
        if patient_context.get('gender') == 'female':
            if any(drug in medication for drug in contraindications["pregnancy"]):
                return {
                    "medication": medication,
                    "contraindication": "pregnancy",
                    "severity": "high",
                    "description": f"{medication} may be contraindicated in pregnancy"
                }
        
        # Additional contraindication checks would go here
        return None
    
    def _get_ai_drug_insights(self, medications: List[str], patient_context: Optional[Dict]) -> str:
        """Get AI-powered drug insights"""
        try:
            prompt = f"""
            Analyze these medications for interactions and clinical considerations:
            Medications: {', '.join(medications)}
            Patient context: {patient_context or 'Limited'}
            
            Provide brief clinical insights about interactions, monitoring, and considerations.
            """
            
            response = self._call_openai(prompt)
            return response
            
        except:
            return "AI drug analysis temporarily unavailable"
    
    def _generate_medication_recommendation(self, interactions: List[Dict], contraindications: List[Dict]) -> str:
        """Generate medication recommendation based on findings"""
        if not interactions and not contraindications:
            return "No significant interactions or contraindications identified. Monitor as clinically indicated."
        
        rec = "RECOMMENDATIONS: "
        if interactions:
            rec += f"Monitor for {len(interactions)} potential drug interactions. "
        if contraindications:
            rec += f"Review {len(contraindications)} contraindications. "
        rec += "Consult pharmacist or specialist if needed."
        
        return rec
    
    def _parse_differential_diagnosis(self, ai_response: str) -> Dict[str, Any]:
        """Parse differential diagnosis from AI response"""
        try:
            # Try to parse structured response
            if '{' in ai_response:
                start = ai_response.find('{')
                end = ai_response.rfind('}') + 1
                return json.loads(ai_response[start:end])
        except:
            pass
        
        # Fallback parsing
        return {
            "raw_response": ai_response,
            "parsing_note": "Manual review recommended for complete differential diagnosis"
        }
