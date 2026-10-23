"""
Multi-Language Support System
============================

Comprehensive multi-language support for international patients including
real-time translation, cultural adaptation, and localized medical terminology.
"""

from typing import Any, Dict, List, Optional, TypedDict, Set, Tuple
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
import json
import uuid
from langgraph.graph import StateGraph, END, START
from langchain_core.messages import BaseMessage
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
import logging

class LanguageCode(Enum):
    ENGLISH = "en"
    SPANISH = "es"
    FRENCH = "fr"
    GERMAN = "de"
    ITALIAN = "it"
    PORTUGUESE = "pt"
    RUSSIAN = "ru"
    CHINESE_SIMPLIFIED = "zh-cn"
    CHINESE_TRADITIONAL = "zh-tw"
    JAPANESE = "ja"
    KOREAN = "ko"
    ARABIC = "ar"
    HINDI = "hi"
    VIETNAMESE = "vi"
    THAI = "th"
    TAGALOG = "tl"
    POLISH = "pl"
    DUTCH = "nl"
    SWEDISH = "sv"
    NORWEGIAN = "no"

class ContentType(Enum):
    MEDICAL_FORMS = "medical_forms"
    DISCHARGE_INSTRUCTIONS = "discharge_instructions"
    CONSENT_FORMS = "consent_forms"
    MEDICATION_LABELS = "medication_labels"
    TREATMENT_PLANS = "treatment_plans"
    APPOINTMENT_REMINDERS = "appointment_reminders"
    BILLING_STATEMENTS = "billing_statements"
    GENERAL_COMMUNICATION = "general_communication"
    EMERGENCY_INSTRUCTIONS = "emergency_instructions"
    DIETARY_GUIDELINES = "dietary_guidelines"

class CulturalContext(Enum):
    WESTERN = "western"
    EASTERN = "eastern"
    MIDDLE_EASTERN = "middle_eastern"
    AFRICAN = "african"
    LATIN_AMERICAN = "latin_american"
    SOUTHEAST_ASIAN = "southeast_asian"
    NORDIC = "nordic"
    MEDITERRANEAN = "mediterranean"

@dataclass
class TranslationRequest:
    request_id: str
    source_language: LanguageCode
    target_language: LanguageCode
    content_type: ContentType
    original_text: str
    cultural_context: Optional[CulturalContext] = None
    medical_speciality: Optional[str] = None
    urgency_level: Optional[str] = "normal"
    patient_id: Optional[str] = None

@dataclass
class TranslationResult:
    request_id: str
    translated_text: str
    confidence_score: float
    cultural_adaptations: List[str]
    medical_terminology_notes: List[str]
    alternative_translations: List[str]
    timestamp: datetime
    translator_notes: Optional[str] = None

class MultiLanguageState(TypedDict):
    """State for multi-language translation workflow"""
    translation_request: Dict[str, Any]
    source_text: str
    target_language: str
    content_type: str
    cultural_context: str
    medical_context: Dict[str, Any]
    translated_text: str
    cultural_adaptations: List[str]
    quality_score: float
    alternative_versions: List[str]
    terminology_notes: List[str]

class MultiLanguageSupport:
    """
    Comprehensive Multi-Language Support System
    
    Features:
    - Real-time medical translation
    - Cultural adaptation and sensitivity
    - Medical terminology localization
    - Document translation with formatting preservation
    - Audio translation support
    - Quality assurance and validation
    - Cultural context awareness
    - Emergency translation protocols
    """
    
    def __init__(self):
        self.setup_translation_engine()
        self.setup_cultural_databases()
        self.setup_medical_terminology()
        self.setup_workflows()
        self.load_language_models()
        
        # Translation cache and quality metrics
        self.translation_cache = {}
        self.quality_metrics = {}
        self.cultural_guidelines = {}
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def setup_translation_engine(self):
        """Initialize the AI-powered translation engine"""
        import os
        api_key = os.getenv('OPENAI_API_KEY') or os.getenv('VITE_OPENAI_API_KEY')
        
        if api_key:
            self.llm = ChatOpenAI(
                api_key=api_key,
                model="gpt-4",
                temperature=0.1
            )
        
        # Language detection patterns
        self.language_detection_patterns = {
            "es": ["el", "la", "los", "las", "un", "una", "por favor", "gracias", "sí", "no"],
            "fr": ["le", "la", "les", "un", "une", "s'il vous plaît", "merci", "oui", "non"],
            "de": ["der", "die", "das", "ein", "eine", "bitte", "danke", "ja", "nein"],
            "it": ["il", "la", "gli", "le", "un", "una", "per favore", "grazie", "sì", "no"],
            "pt": ["o", "a", "os", "as", "um", "uma", "por favor", "obrigado", "sim", "não"],
            "ru": ["это", "что", "как", "где", "когда", "почему", "пожалуйста", "спасибо"],
            "zh-cn": ["的", "是", "在", "有", "我", "你", "他", "她", "它", "们"],
            "ja": ["は", "が", "を", "に", "で", "と", "から", "まで", "です", "ます"],
            "ko": ["은", "는", "이", "가", "을", "를", "에", "에서", "와", "과"],
            "ar": ["في", "من", "إلى", "على", "مع", "هذا", "ذلك", "التي", "الذي"],
            "hi": ["है", "में", "से", "को", "का", "की", "के", "यह", "वह", "और"],
            "vi": ["là", "của", "trong", "với", "và", "có", "được", "này", "đó", "tôi"],
            "th": ["ใน", "ของ", "และ", "เป็น", "มี", "ได้", "ที่", "นี้", "นั้น", "ไป"],
            "tl": ["ang", "ng", "sa", "at", "na", "ay", "mga", "ito", "iyan", "ako"]
        }
    
    def setup_cultural_databases(self):
        """Initialize cultural context databases"""
        self.cultural_guidelines = {
            CulturalContext.WESTERN: {
                "communication_style": "direct",
                "family_involvement": "patient_autonomy",
                "religious_considerations": "secular_approach",
                "gender_sensitivity": "high",
                "time_orientation": "punctual",
                "medical_decision_making": "individual_choice"
            },
            
            CulturalContext.EASTERN: {
                "communication_style": "indirect",
                "family_involvement": "family_centered",
                "religious_considerations": "buddhist_hindu_influences",
                "gender_sensitivity": "high",
                "time_orientation": "flexible",
                "medical_decision_making": "family_consensus"
            },
            
            CulturalContext.MIDDLE_EASTERN: {
                "communication_style": "respectful_formal",
                "family_involvement": "patriarchal_structure",
                "religious_considerations": "islamic_guidelines",
                "gender_sensitivity": "very_high",
                "time_orientation": "relationship_focused",
                "medical_decision_making": "male_family_head"
            },
            
            CulturalContext.LATIN_AMERICAN: {
                "communication_style": "warm_personal",
                "family_involvement": "extended_family",
                "religious_considerations": "catholic_influences",
                "gender_sensitivity": "moderate",
                "time_orientation": "flexible",
                "medical_decision_making": "family_consultation"
            },
            
            CulturalContext.AFRICAN: {
                "communication_style": "respectful_community",
                "family_involvement": "community_centered",
                "religious_considerations": "diverse_spiritual",
                "gender_sensitivity": "varies_by_region",
                "time_orientation": "event_based",
                "medical_decision_making": "elder_consultation"
            },
            
            CulturalContext.SOUTHEAST_ASIAN: {
                "communication_style": "harmony_preserving",
                "family_involvement": "hierarchical_respect",
                "religious_considerations": "buddhist_muslim_mix",
                "gender_sensitivity": "high",
                "time_orientation": "cyclical",
                "medical_decision_making": "family_hierarchy"
            }
        }
    
    def setup_medical_terminology(self):
        """Initialize medical terminology databases"""
        self.medical_terminology = {
            "emergency_terms": {
                "en": ["emergency", "urgent", "pain", "bleeding", "difficulty breathing", "chest pain", "allergic reaction"],
                "es": ["emergencia", "urgente", "dolor", "sangrado", "dificultad para respirar", "dolor de pecho", "reacción alérgica"],
                "fr": ["urgence", "urgent", "douleur", "saignement", "difficulté à respirer", "douleur thoracique", "réaction allergique"],
                "de": ["Notfall", "dringend", "Schmerz", "Blutung", "Atembeschwerden", "Brustschmerz", "allergische Reaktion"],
                "zh-cn": ["紧急", "急迫", "疼痛", "出血", "呼吸困难", "胸痛", "过敏反应"],
                "ar": ["طوارئ", "عاجل", "ألم", "نزيف", "صعوبة في التنفس", "ألم في الصدر", "رد فعل تحسسي"]
            },
            
            "body_parts": {
                "en": ["head", "chest", "abdomen", "arm", "leg", "back", "neck", "heart", "lungs", "stomach"],
                "es": ["cabeza", "pecho", "abdomen", "brazo", "pierna", "espalda", "cuello", "corazón", "pulmones", "estómago"],
                "fr": ["tête", "poitrine", "abdomen", "bras", "jambe", "dos", "cou", "cœur", "poumons", "estomac"],
                "de": ["Kopf", "Brust", "Bauch", "Arm", "Bein", "Rücken", "Hals", "Herz", "Lungen", "Magen"],
                "zh-cn": ["头", "胸", "腹部", "手臂", "腿", "背", "颈", "心脏", "肺", "胃"],
                "ar": ["رأس", "صدر", "بطن", "ذراع", "ساق", "ظهر", "رقبة", "قلب", "رئتين", "معدة"]
            },
            
            "medications": {
                "en": ["take", "tablet", "capsule", "liquid", "injection", "before meals", "after meals", "twice daily"],
                "es": ["tomar", "tableta", "cápsula", "líquido", "inyección", "antes de las comidas", "después de las comidas", "dos veces al día"],
                "fr": ["prendre", "comprimé", "capsule", "liquide", "injection", "avant les repas", "après les repas", "deux fois par jour"],
                "de": ["nehmen", "Tablette", "Kapsel", "Flüssigkeit", "Injektion", "vor den Mahlzeiten", "nach den Mahlzeiten", "zweimal täglich"],
                "zh-cn": ["服用", "片剂", "胶囊", "液体", "注射", "饭前", "饭后", "每日两次"],
                "ar": ["تناول", "قرص", "كبسولة", "سائل", "حقنة", "قبل الوجبات", "بعد الوجبات", "مرتين يومياً"]
            }
        }
    
    def setup_workflows(self):
        """Initialize translation workflows"""
        self.workflows = {
            "medical_translation": self.build_medical_translation_workflow(),
            "cultural_adaptation": self.build_cultural_adaptation_workflow(),
            "emergency_translation": self.build_emergency_translation_workflow(),
            "document_translation": self.build_document_translation_workflow()
        }
    
    def build_medical_translation_workflow(self) -> StateGraph:
        """Build medical translation workflow"""
        
        def detect_language_and_context(state: MultiLanguageState) -> MultiLanguageState:
            """Detect source language and cultural context"""
            source_text = state["source_text"]
            
            # Use AI to detect language and cultural context
            detection_prompt = ChatPromptTemplate.from_messages([
                ("system", """You are a language and cultural context detection AI for medical settings.
                
                Analyze the provided text and identify:
                1. Source language (ISO code)
                2. Cultural context indicators
                3. Medical terminology used
                4. Urgency level
                5. Content type (form, instruction, etc.)
                
                Return as JSON:
                {{
                    "detected_language": "language_code",
                    "confidence": 0.95,
                    "cultural_indicators": ["indicator1", "indicator2"],
                    "medical_terms": ["term1", "term2"],
                    "urgency_level": "normal/urgent/emergency",
                    "content_type": "medical_forms/instructions/etc"
                }}"""),
                ("user", f"Analyze this text: {source_text}")
            ])
            
            try:
                detection_chain = detection_prompt | self.llm | JsonOutputParser()
                result = detection_chain.invoke({"source_text": source_text})
                
                return {
                    **state,
                    "source_language": result.get("detected_language", "en"),
                    "cultural_context": self.determine_cultural_context(result.get("cultural_indicators", [])),
                    "medical_context": {
                        "terms": result.get("medical_terms", []),
                        "urgency": result.get("urgency_level", "normal"),
                        "content_type": result.get("content_type", "general_communication")
                    }
                }
                
            except Exception as e:
                self.logger.error(f"Error in language detection: {e}")
                return {
                    **state,
                    "source_language": "en",
                    "cultural_context": "western",
                    "medical_context": {"terms": [], "urgency": "normal", "content_type": "general_communication"}
                }
        
        def perform_medical_translation(state: MultiLanguageState) -> MultiLanguageState:
            """Perform medical-grade translation"""
            source_text = state["source_text"]
            target_language = state["target_language"]
            medical_context = state.get("medical_context", {})
            cultural_context = state.get("cultural_context", "western")
            
            translation_prompt = ChatPromptTemplate.from_messages([
                ("system", """You are a specialized medical translator with expertise in healthcare terminology and cultural sensitivity.
                
                Translate the medical text with:
                1. Accurate medical terminology
                2. Cultural sensitivity for {cultural_context} context
                3. Appropriate formality level
                4. Preservation of critical medical information
                5. Clear, patient-friendly language
                
                Medical context: {medical_context}
                Target language: {target_language}
                
                Provide:
                1. Primary translation
                2. Alternative phrasings
                3. Cultural adaptation notes
                4. Medical terminology explanations
                5. Quality confidence score
                
                Return as JSON:
                {{
                    "primary_translation": "translated text",
                    "alternative_translations": ["alt1", "alt2"],
                    "cultural_adaptations": ["adaptation1", "adaptation2"],
                    "terminology_notes": ["note1", "note2"],
                    "confidence_score": 0.95,
                    "translator_notes": "additional context"
                }}"""),
                ("user", f"Translate this medical text: {source_text}")
            ])
            
            try:
                translation_chain = translation_prompt | self.llm | JsonOutputParser()
                result = translation_chain.invoke({
                    "source_text": source_text,
                    "target_language": target_language,
                    "medical_context": json.dumps(medical_context),
                    "cultural_context": cultural_context
                })
                
                return {
                    **state,
                    "translated_text": result.get("primary_translation", ""),
                    "alternative_versions": result.get("alternative_translations", []),
                    "cultural_adaptations": result.get("cultural_adaptations", []),
                    "terminology_notes": result.get("terminology_notes", []),
                    "quality_score": result.get("confidence_score", 0.0),
                    "translator_notes": result.get("translator_notes", "")
                }
                
            except Exception as e:
                self.logger.error(f"Error in medical translation: {e}")
                return {
                    **state,
                    "translated_text": "Translation error occurred. Please consult human translator.",
                    "alternative_versions": [],
                    "cultural_adaptations": [],
                    "terminology_notes": [],
                    "quality_score": 0.0
                }
        
        def validate_translation_quality(state: MultiLanguageState) -> MultiLanguageState:
            """Validate translation quality and accuracy"""
            translated_text = state.get("translated_text", "")
            source_text = state["source_text"]
            medical_context = state.get("medical_context", {})
            
            validation_prompt = ChatPromptTemplate.from_messages([
                ("system", """You are a medical translation quality assurance specialist.
                
                Review the translation for:
                1. Medical accuracy
                2. Cultural appropriateness
                3. Completeness
                4. Clarity for patients
                5. Critical information preservation
                
                Original: {source_text}
                Translation: {translated_text}
                Medical context: {medical_context}
                
                Return validation results as JSON:
                {{
                    "quality_score": 0.95,
                    "accuracy_issues": ["issue1", "issue2"],
                    "suggestions": ["suggestion1", "suggestion2"],
                    "cultural_concerns": ["concern1", "concern2"],
                    "approved": true,
                    "revision_needed": false
                }}"""),
                ("user", "Validate this medical translation.")
            ])
            
            try:
                validation_chain = validation_prompt | self.llm | JsonOutputParser()
                result = validation_chain.invoke({
                    "source_text": source_text,
                    "translated_text": translated_text,
                    "medical_context": json.dumps(medical_context)
                })
                
                quality_score = result.get("quality_score", 0.0)
                
                return {
                    **state,
                    "quality_score": quality_score,
                    "validation_results": result,
                    "approved": result.get("approved", False)
                }
                
            except Exception as e:
                self.logger.error(f"Error in translation validation: {e}")
                return {
                    **state,
                    "quality_score": 0.5,
                    "approved": False
                }
        
        # Build workflow graph
        workflow = StateGraph(MultiLanguageState)
        
        workflow.add_node("detect_context", detect_language_and_context)
        workflow.add_node("translate", perform_medical_translation)
        workflow.add_node("validate", validate_translation_quality)
        
        workflow.add_edge(START, "detect_context")
        workflow.add_edge("detect_context", "translate")
        workflow.add_edge("translate", "validate")
        workflow.add_edge("validate", END)
        
        return workflow.compile()
    
    def build_cultural_adaptation_workflow(self) -> StateGraph:
        """Build cultural adaptation workflow"""
        # Implementation for cultural adaptation
        pass
    
    def build_emergency_translation_workflow(self) -> StateGraph:
        """Build emergency translation workflow"""
        # Implementation for emergency translation
        pass
    
    def build_document_translation_workflow(self) -> StateGraph:
        """Build document translation workflow"""
        # Implementation for document translation
        pass
    
    def load_language_models(self):
        """Load language-specific models and resources"""
        self.language_models = {
            LanguageCode.SPANISH: {
                "region_variants": ["es-MX", "es-AR", "es-ES"],
                "medical_resources": "spanish_medical_dict.json",
                "cultural_notes": "hispanic_cultural_guide.json"
            },
            LanguageCode.CHINESE_SIMPLIFIED: {
                "region_variants": ["zh-CN", "zh-SG"],
                "medical_resources": "chinese_medical_dict.json",
                "cultural_notes": "chinese_cultural_guide.json"
            },
            LanguageCode.ARABIC: {
                "region_variants": ["ar-SA", "ar-EG", "ar-AE"],
                "medical_resources": "arabic_medical_dict.json",
                "cultural_notes": "arabic_cultural_guide.json"
            }
        }
    
    def determine_cultural_context(self, cultural_indicators: List[str]) -> str:
        """Determine cultural context from indicators"""
        # Simple mapping - in real implementation would be more sophisticated
        if any(indicator in ["hispanic", "latino", "mexican", "spanish"] for indicator in cultural_indicators):
            return "latin_american"
        elif any(indicator in ["chinese", "japanese", "korean", "asian"] for indicator in cultural_indicators):
            return "eastern"
        elif any(indicator in ["arabic", "muslim", "middle_east"] for indicator in cultural_indicators):
            return "middle_eastern"
        else:
            return "western"
    
    async def translate_text(self, 
                           text: str, 
                           target_language: LanguageCode,
                           content_type: ContentType = ContentType.GENERAL_COMMUNICATION,
                           patient_id: Optional[str] = None) -> TranslationResult:
        """Translate text with medical and cultural context"""
        
        request_id = str(uuid.uuid4())
        
        workflow = self.workflows["medical_translation"]
        
        state = MultiLanguageState(
            translation_request={
                "request_id": request_id,
                "target_language": target_language.value,
                "content_type": content_type.value,
                "patient_id": patient_id
            },
            source_text=text,
            target_language=target_language.value,
            content_type=content_type.value,
            cultural_context="western",
            medical_context={},
            translated_text="",
            cultural_adaptations=[],
            quality_score=0.0,
            alternative_versions=[],
            terminology_notes=[]
        )
        
        try:
            result = await workflow.ainvoke(state)
            
            translation_result = TranslationResult(
                request_id=request_id,
                translated_text=result.get("translated_text", ""),
                confidence_score=result.get("quality_score", 0.0),
                cultural_adaptations=result.get("cultural_adaptations", []),
                medical_terminology_notes=result.get("terminology_notes", []),
                alternative_translations=result.get("alternative_versions", []),
                timestamp=datetime.now(),
                translator_notes=result.get("translator_notes")
            )
            
            # Cache the translation
            self.translation_cache[request_id] = translation_result
            
            return translation_result
            
        except Exception as e:
            self.logger.error(f"Error in translation: {e}")
            raise
    
    def get_supported_languages(self) -> List[Dict[str, str]]:
        """Get list of supported languages"""
        return [
            {"code": lang.value, "name": lang.name.replace("_", " ").title()}
            for lang in LanguageCode
        ]
    
    def get_cultural_guidelines(self, cultural_context: CulturalContext) -> Dict[str, Any]:
        """Get cultural guidelines for specific context"""
        return self.cultural_guidelines.get(cultural_context, {})
    
    def get_emergency_phrases(self, language: LanguageCode) -> List[Dict[str, str]]:
        """Get emergency phrases in specified language"""
        emergency_phrases = []
        
        if language.value in self.medical_terminology["emergency_terms"]:
            terms = self.medical_terminology["emergency_terms"][language.value]
            english_terms = self.medical_terminology["emergency_terms"]["en"]
            
            for i, term in enumerate(terms):
                if i < len(english_terms):
                    emergency_phrases.append({
                        "english": english_terms[i],
                        "translation": term,
                        "pronunciation": self.get_pronunciation_guide(term, language)
                    })
        
        return emergency_phrases
    
    def get_pronunciation_guide(self, text: str, language: LanguageCode) -> str:
        """Get pronunciation guide for text (simplified implementation)"""
        # In real implementation, would use phonetic transcription
        pronunciation_guides = {
            LanguageCode.SPANISH: text.lower(),
            LanguageCode.FRENCH: text.lower(),
            LanguageCode.GERMAN: text.lower(),
            LanguageCode.CHINESE_SIMPLIFIED: "[Chinese pronunciation guide needed]",
            LanguageCode.ARABIC: "[Arabic pronunciation guide needed]"
        }
        
        return pronunciation_guides.get(language, text)
    
    def create_multilingual_form(self, form_template: Dict[str, Any], 
                                language: LanguageCode) -> Dict[str, Any]:
        """Create multilingual version of a form"""
        # Implementation for form translation
        pass
    
    def get_translation_statistics(self) -> Dict[str, Any]:
        """Get translation system statistics"""
        total_translations = len(self.translation_cache)
        
        if total_translations == 0:
            return {"total_translations": 0, "average_quality": 0}
        
        quality_scores = [result.confidence_score for result in self.translation_cache.values()]
        average_quality = sum(quality_scores) / len(quality_scores)
        
        language_distribution = {}
        for result in self.translation_cache.values():
            # Would track target languages in real implementation
            pass
        
        return {
            "total_translations": total_translations,
            "average_quality": average_quality,
            "language_distribution": language_distribution,
            "cache_size": len(self.translation_cache)
        }
    
    def translate_medical_term(self, term: str, target_language: str) -> str:
        """Simple synchronous translation for testing"""
        try:
            # Use OpenAI for quick translation
            prompt = f"Translate this medical term to {target_language}: '{term}'. Respond with just the translation."
            
            response = self.llm.invoke(prompt)
            return response.content.strip()
            
        except Exception as e:
            self.logger.error(f"Translation error: {e}")
            return f"Translation failed: {term}"
