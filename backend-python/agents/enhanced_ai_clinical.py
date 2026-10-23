"""
Enhanced AI Clinical Assistant using LangChain
Advanced clinical decision support with chain-of-thought reasoning
"""

import os
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableParallel
from langchain_openai import ChatOpenAI
from agents.base_agent import BaseAgent

# Database imports
try:
    from database import Patient, Staff, Department, SessionLocal
    DATABASE_AVAILABLE = True
except ImportError:
    DATABASE_AVAILABLE = False
    print("WARNING: Database not available for Enhanced AI Clinical Assistant")

# Initialize LangChain components
OPENAI_API_KEY = os.getenv('VITE_OPENAI_API_KEY') or os.getenv('OPENAI_API_KEY')
if OPENAI_API_KEY:
    llm = ChatOpenAI(
        api_key=OPENAI_API_KEY,
        model="gpt-4",
        temperature=0.1
    )
    ENHANCED_AI_AVAILABLE = True
    print("✅ Enhanced AI Clinical Assistant with LangChain initialized")
else:
    llm = None
    ENHANCED_AI_AVAILABLE = False
    print("⚠️ OpenAI API key not found - Enhanced AI features disabled")

class EnhancedAIClinicalAssistant(BaseAgent):
    """Enhanced AI Clinical Assistant using LangChain for advanced reasoning"""
    
    def __init__(self):
        super().__init__("Enhanced AI Clinical Assistant", "enhanced_ai_clinical")
        self.llm = llm
        self.setup_chains()
    
    def setup_chains(self):
        """Setup LangChain chains for different clinical tasks"""
        if not ENHANCED_AI_AVAILABLE:
            self.chains = {}
            return
        
        # Symptom Analysis Chain
        self.symptom_analysis_chain = self._create_symptom_analysis_chain()
        
        # Differential Diagnosis Chain
        self.diagnosis_chain = self._create_diagnosis_chain()
        
        # Treatment Recommendation Chain
        self.treatment_chain = self._create_treatment_chain()
        
        # Drug Interaction Chain
        self.drug_interaction_chain = self._create_drug_interaction_chain()
        
        # Vital Signs Analysis Chain
        self.vitals_chain = self._create_vitals_analysis_chain()
        
        # Risk Assessment Chain
        self.risk_assessment_chain = self._create_risk_assessment_chain()
        
        print("✅ LangChain clinical chains initialized")
    
    def _create_symptom_analysis_chain(self):
        """Create chain for symptom analysis"""
        symptom_prompt = ChatPromptTemplate.from_template("""
        You are an expert clinical assistant. Analyze the following symptoms and provide structured insights.
        
        Patient presents with: {symptoms}
        Patient history: {patient_history}
        
        Provide a comprehensive analysis in JSON format:
        {{
            "primary_symptoms": ["symptom1", "symptom2"],
            "secondary_symptoms": ["symptom3", "symptom4"],
            "symptom_severity": "mild|moderate|severe",
            "symptom_duration": "duration if mentioned",
            "associated_symptoms": ["related1", "related2"],
            "red_flags": ["urgent1", "urgent2"],
            "system_involvement": ["cardiovascular", "respiratory", "etc"],
            "urgency_level": "low|medium|high|critical",
            "triage_recommendation": "discharge|observation|admission|icu"
        }}
        
        Base your analysis on evidence-based medicine and clinical guidelines.
        """)
        
        return symptom_prompt | self.llm | JsonOutputParser()
    
    def _create_diagnosis_chain(self):
        """Create chain for differential diagnosis"""
        diagnosis_prompt = ChatPromptTemplate.from_template("""
        As a senior clinician, generate a differential diagnosis based on the clinical presentation.
        
        Clinical Information:
        - Symptoms: {symptoms}
        - Patient History: {patient_history}
        - Vital Signs: {vital_signs}
        - Physical Exam: {physical_exam}
        
        Generate a structured differential diagnosis:
        {{
            "differential_diagnoses": [
                {{
                    "condition": "condition name",
                    "probability": 0.85,
                    "supporting_evidence": ["evidence1", "evidence2"],
                    "contradicting_evidence": ["contra1", "contra2"],
                    "pathophysiology": "brief explanation",
                    "icd_10_code": "ICD code if applicable"
                }}
            ],
            "most_likely_diagnosis": "primary diagnosis",
            "alternative_diagnoses": ["diagnosis2", "diagnosis3"],
            "rule_out_conditions": ["serious condition1", "serious condition2"],
            "diagnostic_certainty": "low|moderate|high",
            "next_steps": ["diagnostic step1", "diagnostic step2"]
        }}
        
        Consider epidemiology, patient demographics, and clinical presentation patterns.
        """)
        
        return diagnosis_prompt | self.llm | JsonOutputParser()
    
    def _create_treatment_chain(self):
        """Create chain for treatment recommendations"""
        treatment_prompt = ChatPromptTemplate.from_template("""
        Provide evidence-based treatment recommendations for this clinical scenario.
        
        Patient Information:
        - Diagnosis: {diagnosis}
        - Patient Age: {age}
        - Allergies: {allergies}
        - Current Medications: {current_medications}
        - Comorbidities: {comorbidities}
        
        Generate comprehensive treatment plan:
        {{
            "immediate_interventions": [
                {{
                    "intervention": "intervention name",
                    "priority": "high|medium|low",
                    "rationale": "clinical reasoning",
                    "contraindications": ["contra1", "contra2"]
                }}
            ],
            "pharmacological_treatment": [
                {{
                    "medication": "drug name",
                    "dosage": "dose and frequency",
                    "duration": "treatment duration",
                    "monitoring": "parameters to monitor",
                    "alternatives": ["alternative1", "alternative2"]
                }}
            ],
            "non_pharmacological_treatment": ["therapy1", "therapy2"],
            "monitoring_plan": {{
                "vital_signs": "frequency",
                "laboratory_tests": ["test1", "test2"],
                "imaging": ["study1", "study2"],
                "follow_up_timeline": "when to reassess"
            }},
            "patient_education": ["education point1", "education point2"],
            "discharge_criteria": ["criteria1", "criteria2"],
            "complications_to_watch": ["complication1", "complication2"]
        }}
        
        Follow evidence-based guidelines and consider patient-specific factors.
        """)
        
        return treatment_prompt | self.llm | JsonOutputParser()
    
    def _create_drug_interaction_chain(self):
        """Create chain for drug interaction analysis"""
        interaction_prompt = ChatPromptTemplate.from_template("""
        Analyze potential drug interactions for this medication regimen.
        
        Current Medications: {current_medications}
        New Medication: {new_medication}
        Patient Factors: {patient_factors}
        
        Provide detailed interaction analysis:
        {{
            "major_interactions": [
                {{
                    "drugs": ["drug1", "drug2"],
                    "interaction_type": "pharmacokinetic|pharmacodynamic",
                    "mechanism": "detailed mechanism",
                    "clinical_significance": "severe|moderate|mild",
                    "management": "how to manage",
                    "monitoring": "what to monitor"
                }}
            ],
            "moderate_interactions": [...],
            "minor_interactions": [...],
            "contraindications": [
                {{
                    "medication": "drug name",
                    "contraindication": "condition or drug",
                    "reason": "clinical reason",
                    "alternative": "suggested alternative"
                }}
            ],
            "dosage_adjustments": [
                {{
                    "medication": "drug name",
                    "adjustment": "how to adjust",
                    "reason": "renal/hepatic/age/etc"
                }}
            ],
            "monitoring_recommendations": ["parameter1", "parameter2"],
            "overall_safety_assessment": "safe|caution|contraindicated"
        }}
        
        Consider pharmacokinetics, pharmacodynamics, and patient-specific factors.
        """)
        
        return interaction_prompt | self.llm | JsonOutputParser()
    
    def _create_vitals_analysis_chain(self):
        """Create chain for vital signs analysis"""
        vitals_prompt = ChatPromptTemplate.from_template("""
        Analyze the vital signs and provide clinical interpretation.
        
        Vital Signs:
        - Heart Rate: {heart_rate} bpm
        - Blood Pressure: {blood_pressure} mmHg
        - Respiratory Rate: {respiratory_rate} /min
        - Temperature: {temperature}°C
        - Oxygen Saturation: {oxygen_saturation}%
        - Pain Scale: {pain_scale}/10
        
        Patient Context:
        - Age: {age}
        - Medical History: {medical_history}
        - Current Medications: {medications}
        
        Provide structured analysis:
        {{
            "vital_signs_interpretation": {{
                "heart_rate": {{
                    "value": {heart_rate},
                    "interpretation": "normal|bradycardia|tachycardia",
                    "severity": "mild|moderate|severe",
                    "clinical_significance": "explanation"
                }},
                "blood_pressure": {{
                    "systolic": "interpretation",
                    "diastolic": "interpretation", 
                    "category": "normal|elevated|hypertension_stage1|hypertension_stage2|crisis",
                    "clinical_significance": "explanation"
                }},
                "respiratory_rate": {{
                    "interpretation": "normal|tachypnea|bradypnea",
                    "clinical_significance": "explanation"
                }},
                "temperature": {{
                    "interpretation": "normal|fever|hypothermia",
                    "severity": "low_grade|moderate|high_grade",
                    "clinical_significance": "explanation"
                }},
                "oxygen_saturation": {{
                    "interpretation": "normal|mild_hypoxemia|moderate_hypoxemia|severe_hypoxemia",
                    "clinical_significance": "explanation"
                }}
            }},
            "overall_assessment": "stable|concerning|critical",
            "immediate_actions": ["action1", "action2"],
            "monitoring_frequency": "continuous|hourly|q4h|q8h|daily",
            "alert_conditions": ["condition1", "condition2"],
            "hemodynamic_status": "stable|unstable|shock"
        }}
        
        Consider age-appropriate normal ranges and clinical context.
        """)
        
        return vitals_prompt | self.llm | JsonOutputParser()
    
    def _create_risk_assessment_chain(self):
        """Create chain for clinical risk assessment"""
        risk_prompt = ChatPromptTemplate.from_template("""
        Perform a comprehensive clinical risk assessment.
        
        Patient Information:
        - Age: {age}
        - Gender: {gender}
        - Medical History: {medical_history}
        - Current Condition: {current_condition}
        - Medications: {medications}
        - Social History: {social_history}
        
        Assess clinical risks:
        {{
            "cardiovascular_risk": {{
                "risk_level": "low|moderate|high|very_high",
                "risk_factors": ["factor1", "factor2"],
                "10_year_risk": "percentage if calculable",
                "recommendations": ["recommendation1", "recommendation2"]
            }},
            "thromboembolic_risk": {{
                "risk_level": "low|moderate|high",
                "cha2ds2_vasc_score": "score if applicable",
                "anticoagulation_recommendation": "recommendation"
            }},
            "bleeding_risk": {{
                "risk_level": "low|moderate|high",
                "has_bled_score": "score if applicable",
                "precautions": ["precaution1", "precaution2"]
            }},
            "infection_risk": {{
                "risk_level": "low|moderate|high",
                "risk_factors": ["immunosuppression", "invasive_devices"],
                "prophylaxis_needed": "yes|no|consider"
            }},
            "fall_risk": {{
                "risk_level": "low|moderate|high",
                "risk_factors": ["age", "medications", "mobility"],
                "interventions": ["intervention1", "intervention2"]
            }},
            "medication_adherence_risk": {{
                "risk_level": "low|moderate|high",
                "barriers": ["cost", "complexity", "side_effects"],
                "strategies": ["strategy1", "strategy2"]
            }},
            "overall_prognosis": "excellent|good|fair|poor|grave",
            "discharge_planning": ["planning_point1", "planning_point2"],
            "follow_up_intensity": "routine|close|intensive"
        }}
        
        Use validated risk assessment tools where applicable.
        """)
        
        return risk_prompt | self.llm | JsonOutputParser()
    
    # Public methods for clinical analysis
    
    def analyze_symptoms(self, symptoms: str, patient_history: str = "") -> Dict[str, Any]:
        """Analyze symptoms using LangChain"""
        if not ENHANCED_AI_AVAILABLE:
            return {"error": "Enhanced AI not available"}
        
        try:
            result = self.symptom_analysis_chain.invoke({
                "symptoms": symptoms,
                "patient_history": patient_history
            })
            
            self.log_interaction(
                query=f"Analyze symptoms: {symptoms[:100]}...",
                response="Symptom analysis completed",
                tool_used="analyze_symptoms"
            )
            
            return {"success": True, "analysis": result}
            
        except Exception as e:
            return {"success": False, "error": f"Symptom analysis failed: {str(e)}"}
    
    def generate_differential_diagnosis(self, clinical_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate differential diagnosis using LangChain"""
        if not ENHANCED_AI_AVAILABLE:
            return {"error": "Enhanced AI not available"}
        
        try:
            result = self.diagnosis_chain.invoke({
                "symptoms": clinical_data.get("symptoms", ""),
                "patient_history": clinical_data.get("patient_history", ""),
                "vital_signs": clinical_data.get("vital_signs", ""),
                "physical_exam": clinical_data.get("physical_exam", "")
            })
            
            self.log_interaction(
                query="Generate differential diagnosis",
                response=f"Generated {len(result.get('differential_diagnoses', []))} diagnoses",
                tool_used="generate_differential_diagnosis"
            )
            
            return {"success": True, "diagnosis": result}
            
        except Exception as e:
            return {"success": False, "error": f"Diagnosis generation failed: {str(e)}"}
    
    def recommend_treatment(self, treatment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Recommend treatment using LangChain"""
        if not ENHANCED_AI_AVAILABLE:
            return {"error": "Enhanced AI not available"}
        
        try:
            result = self.treatment_chain.invoke({
                "diagnosis": treatment_data.get("diagnosis", ""),
                "age": treatment_data.get("age", "unknown"),
                "allergies": treatment_data.get("allergies", "none"),
                "current_medications": treatment_data.get("current_medications", "none"),
                "comorbidities": treatment_data.get("comorbidities", "none")
            })
            
            self.log_interaction(
                query=f"Recommend treatment for: {treatment_data.get('diagnosis', 'unknown')}",
                response="Treatment recommendations generated",
                tool_used="recommend_treatment"
            )
            
            return {"success": True, "treatment": result}
            
        except Exception as e:
            return {"success": False, "error": f"Treatment recommendation failed: {str(e)}"}
    
    def analyze_drug_interactions(self, medication_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze drug interactions using LangChain"""
        if not ENHANCED_AI_AVAILABLE:
            return {"error": "Enhanced AI not available"}
        
        try:
            result = self.drug_interaction_chain.invoke({
                "current_medications": medication_data.get("current_medications", []),
                "new_medication": medication_data.get("new_medication", ""),
                "patient_factors": medication_data.get("patient_factors", {})
            })
            
            self.log_interaction(
                query="Analyze drug interactions",
                response=f"Found {len(result.get('major_interactions', []))} major interactions",
                tool_used="analyze_drug_interactions"
            )
            
            return {"success": True, "interactions": result}
            
        except Exception as e:
            return {"success": False, "error": f"Drug interaction analysis failed: {str(e)}"}
    
    def analyze_vital_signs(self, vitals_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze vital signs using LangChain"""
        if not ENHANCED_AI_AVAILABLE:
            return {"error": "Enhanced AI not available"}
        
        try:
            result = self.vitals_chain.invoke({
                "heart_rate": vitals_data.get("heart_rate", "unknown"),
                "blood_pressure": vitals_data.get("blood_pressure", "unknown"),
                "respiratory_rate": vitals_data.get("respiratory_rate", "unknown"),
                "temperature": vitals_data.get("temperature", "unknown"),
                "oxygen_saturation": vitals_data.get("oxygen_saturation", "unknown"),
                "pain_scale": vitals_data.get("pain_scale", "unknown"),
                "age": vitals_data.get("age", "unknown"),
                "medical_history": vitals_data.get("medical_history", ""),
                "medications": vitals_data.get("medications", "")
            })
            
            self.log_interaction(
                query="Analyze vital signs",
                response=f"Assessment: {result.get('overall_assessment', 'unknown')}",
                tool_used="analyze_vital_signs"
            )
            
            return {"success": True, "vitals_analysis": result}
            
        except Exception as e:
            return {"success": False, "error": f"Vital signs analysis failed: {str(e)}"}
    
    def assess_clinical_risk(self, risk_data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess clinical risk using LangChain"""
        if not ENHANCED_AI_AVAILABLE:
            return {"error": "Enhanced AI not available"}
        
        try:
            result = self.risk_assessment_chain.invoke({
                "age": risk_data.get("age", "unknown"),
                "gender": risk_data.get("gender", "unknown"),
                "medical_history": risk_data.get("medical_history", ""),
                "current_condition": risk_data.get("current_condition", ""),
                "medications": risk_data.get("medications", ""),
                "social_history": risk_data.get("social_history", "")
            })
            
            self.log_interaction(
                query="Assess clinical risk",
                response=f"Overall prognosis: {result.get('overall_prognosis', 'unknown')}",
                tool_used="assess_clinical_risk"
            )
            
            return {"success": True, "risk_assessment": result}
            
        except Exception as e:
            return {"success": False, "error": f"Risk assessment failed: {str(e)}"}
    
    def get_tools(self) -> List[str]:
        """Return list of enhanced AI clinical tools"""
        return [
            "analyze_symptoms",
            "generate_differential_diagnosis",
            "recommend_treatment",
            "analyze_drug_interactions",
            "analyze_vital_signs",
            "assess_clinical_risk"
        ]
    
    def get_capabilities(self) -> List[str]:
        """Return list of enhanced capabilities"""
        capabilities = [
            "Advanced symptom analysis with LangChain",
            "Multi-step differential diagnosis reasoning",
            "Evidence-based treatment recommendations",
            "Comprehensive drug interaction analysis",
            "Intelligent vital signs interpretation",
            "Clinical risk stratification",
            "Chain-of-thought clinical reasoning"
        ]
        
        if ENHANCED_AI_AVAILABLE:
            capabilities.append("LangChain-powered AI reasoning")
        else:
            capabilities.append("Enhanced AI features disabled")
            
        return capabilities

# Initialize the enhanced clinical assistant
if ENHANCED_AI_AVAILABLE:
    enhanced_clinical_assistant = EnhancedAIClinicalAssistant()
    print("✅ Enhanced AI Clinical Assistant initialized and ready")
else:
    enhanced_clinical_assistant = None
    print("⚠️ Enhanced AI Clinical Assistant not available")

if __name__ == "__main__":
    # Test the enhanced clinical assistant
    if enhanced_clinical_assistant:
        print("🧪 Testing Enhanced AI Clinical Assistant...")
        
        # Test symptom analysis
        symptom_result = enhanced_clinical_assistant.analyze_symptoms(
            "Patient presents with chest pain, shortness of breath, and sweating",
            "History of hypertension and diabetes"
        )
        print(f"Symptom analysis: {symptom_result.get('success', False)}")
        
        # Test differential diagnosis
        clinical_data = {
            "symptoms": "chest pain, dyspnea, diaphoresis",
            "patient_history": "HTN, DM",
            "vital_signs": "HR 110, BP 150/95, RR 22",
            "physical_exam": "S3 gallop, bilateral rales"
        }
        diagnosis_result = enhanced_clinical_assistant.generate_differential_diagnosis(clinical_data)
        print(f"Differential diagnosis: {diagnosis_result.get('success', False)}")
        
        print("✅ Enhanced AI Clinical Assistant testing complete")
    else:
        print("❌ Enhanced AI Clinical Assistant not available for testing")
