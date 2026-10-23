"""Hospital Management System Multi-Agent MCP Server"""

import json
import os
import random
import sys
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure") and sys.stdout:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure") and sys.stderr:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
import traceback
import uuid
import re
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional
import uvicorn

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Environment variables loaded from .env file")
except ImportError:
    print("⚠️ python-dotenv not available, using system environment variables only")

from sqlalchemy.orm import Session
from sqlalchemy import Date, text, func
from mcp.server.fastmcp import FastMCP
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

# Import database modules
try:
    from database import (
        User, Department, Patient, Room, Bed, Staff, Equipment, EquipmentCategory,
        Supply, SupplyCategory, InventoryTransaction, AgentInteraction,
        LegacyUser, DischargeReport, SessionLocal
    )
    DATABASE_AVAILABLE = True
except ImportError:
    DATABASE_AVAILABLE = False
    print("WARNING: Database modules not available. Install dependencies: pip install sqlalchemy psycopg2-binary")

# Import multi-agent system
try:
    from agents.orchestrator_agent import OrchestratorAgent
    MULTI_AGENT_AVAILABLE = True
except ImportError:
    MULTI_AGENT_AVAILABLE = False
    print("WARNING: Multi-agent system not available")

# Import advanced LangChain/LangGraph systems
try:
    from agents.master_integration_system import MasterHospitalManagementSystem, IntegrationLevel
    from agents.enhanced_orchestrator_agent import EnhancedOrchestratorAgent
    from agents.real_time_monitoring_agent import RealTimeMonitoringAgent
    from agents.predictive_analytics_agent import AdvancedPredictiveSystem, PredictionType, ForecastHorizon
    from agents.multilingual_support_agent import MultiLanguageSupport, LanguageCode, ContentType
    from agents.equipment_lifecycle_agent import EquipmentLifecycleManager
    ADVANCED_AI_AVAILABLE = True
    print("✅ Advanced LangChain/LangGraph systems loaded successfully")
except ImportError as e:
    ADVANCED_AI_AVAILABLE = False
    print(f"⚠️ Advanced AI systems not available: {e}")

# Initialize FastMCP server
mcp = FastMCP("hospital-management-system-multi-agent")

# Initialize orchestrator agent (legacy)
orchestrator = None
if MULTI_AGENT_AVAILABLE:
    try:
        orchestrator = OrchestratorAgent()
        print("🤖 Legacy multi-agent system initialized successfully!")
    except Exception as e:
        print(f"❌ Failed to initialize legacy multi-agent system: {str(e)}")
        MULTI_AGENT_AVAILABLE = False

# Initialize Advanced AI Master System
master_ai_system = None
if ADVANCED_AI_AVAILABLE and not os.getenv("OPENAI_API_KEY"):
    # The Master AI system (enhanced orchestrator) cannot run without OpenAI.
    # Skip it cleanly instead of failing; core hospital tools are unaffected.
    ADVANCED_AI_AVAILABLE = False
    print("ℹ️  OPENAI_API_KEY not set - Master AI system skipped (AI chat/orchestrator features off; "
          "patients, beds and discharge work normally). Add OPENAI_API_KEY to .env to enable.")
if ADVANCED_AI_AVAILABLE:
    try:
        master_ai_system = MasterHospitalManagementSystem(IntegrationLevel.ENTERPRISE)
        print("🚀 Master AI Hospital Management System initialized successfully!")
        print(f"   - Enhanced Orchestrator: ✅")
        print(f"   - Real-time Monitoring: ✅")
        print(f"   - Predictive Analytics: ✅")
        print(f"   - Multi-language Support: ✅")
        print(f"   - Equipment Lifecycle: ✅")
    except Exception as e:
        print(f"❌ Failed to initialize Master AI system: {str(e)}")
        ADVANCED_AI_AVAILABLE = False

# Database helper functions (kept for backward compatibility)
def get_db_session() -> Session:
    """Get database session."""
    return SessionLocal()

def serialize_model(obj):
    """Convert SQLAlchemy model to dictionary."""
    if obj is None:
        return None
    
    result = {}
    for column in obj.__table__.columns:
        value = getattr(obj, column.name)
        if isinstance(value, uuid.UUID):
            result[column.name] = str(value)
        elif isinstance(value, (datetime, date)):
            result[column.name] = value.isoformat()
        elif isinstance(value, Decimal):
            result[column.name] = float(value)
        else:
            result[column.name] = value
    return result

# ================================
# MULTI-AGENT SYSTEM TOOLS
# ================================

@mcp.tool()
def get_system_status() -> Dict[str, Any]:
    """Get comprehensive system status from the orchestrator."""
    if not MULTI_AGENT_AVAILABLE or not orchestrator:
        return {"error": "Multi-agent system not available"}
    
    try:
        if hasattr(orchestrator, 'get_system_status'):
            return orchestrator.get_system_status()
        else:
            # Fallback: provide basic system status
            return {
                "success": True,
                "status": "operational",
                "database": "connected" if DATABASE_AVAILABLE else "disconnected",
                "multi_agent": "active",
                "agents_count": len(orchestrator.agents),
                "total_tools": len(orchestrator.get_tools()) if hasattr(orchestrator, 'get_tools') else 0,
                "agents": {name: {
                    "status": "active",
                    "tools_count": len(agent.get_tools()) if hasattr(agent, 'get_tools') else 0
                } for name, agent in orchestrator.agents.items()}
            }
    except Exception as e:
        return {"error": f"Failed to get system status: {str(e)}"}

@mcp.tool()
def get_agent_info(agent_name: str = None) -> Dict[str, Any]:
    """Get information about agents in the system."""
    if not MULTI_AGENT_AVAILABLE or not orchestrator:
        return {"error": "Multi-agent system not available"}
    
    try:
        if hasattr(orchestrator, 'get_agent_info'):
            return orchestrator.get_agent_info(agent_name)
        else:
            # Fallback: provide basic agent information
            agents_info = {}
            for name, agent in orchestrator.agents.items():
                agents_info[name] = {
                    "name": agent.agent_name,
                    "description": f"{agent.agent_name} handles {agent.agent_name.lower()}-related operations",
                    "tools_count": len(agent.get_tools()) if hasattr(agent, 'get_tools') else 0,
                    "status": "active"
                }
            
            if agent_name:
                return agents_info.get(agent_name, {"error": f"Agent '{agent_name}' not found"})
            else:
                return {
                    "total_agents": len(agents_info),
                    "agents": agents_info
                }
    except Exception as e:
        return {"error": f"Failed to get agent info: {str(e)}"}

@mcp.tool()
def list_agents() -> Dict[str, Any]:
    """List all available agents in the multi-agent system."""
    if not MULTI_AGENT_AVAILABLE or not orchestrator:
        return {"error": "Multi-agent system not available"}
    
    try:
        agents_list = []
        for name, agent in orchestrator.agents.items():
            agents_list.append({
                "name": agent.agent_name,
                "description": f"Handles {agent.agent_name.lower()}-related hospital operations",
                "tools_count": len(agent.get_tools()) if hasattr(agent, 'get_tools') else 0
            })
        
        return {
            "success": True,
            "total_agents": len(agents_list),
            "agents": agents_list
        }
    except Exception as e:
        return {"error": f"Failed to list agents: {str(e)}"}

@mcp.tool()
def execute_workflow(workflow_name: str, workflow_params: Dict[str, Any]) -> Dict[str, Any]:
    """Execute complex multi-agent workflows."""
    if not MULTI_AGENT_AVAILABLE or not orchestrator:
        return {"error": "Multi-agent system not available"}
    
    try:
        return orchestrator.execute_workflow(workflow_name, workflow_params)
    except Exception as e:
        return {"error": f"Failed to execute workflow: {str(e)}"}

# ================================
# LANGRAPH WORKFLOW TOOLS
# ================================

@mcp.tool()
def execute_langraph_patient_admission(patient_data: Dict[str, Any], existing_patient_id: str = None) -> Dict[str, Any]:
    """Execute patient admission using LangGraph workflow with intelligent state management."""
    if not MULTI_AGENT_AVAILABLE or not orchestrator:
        return {"error": "Multi-agent system not available"}
    
    try:
        if hasattr(orchestrator, 'execute_langraph_patient_admission'):
            return orchestrator.execute_langraph_patient_admission(patient_data, existing_patient_id)
        else:
            return {"error": "LangGraph patient admission not available"}
    except Exception as e:
        return {"error": f"Failed to execute LangGraph patient admission: {str(e)}"}

@mcp.tool()
def execute_langraph_clinical_decision(query: str, patient_context: Dict[str, Any] = None) -> Dict[str, Any]:
    """Execute clinical decision support using LangGraph workflow with multi-step reasoning."""
    if not MULTI_AGENT_AVAILABLE or not orchestrator:
        return {"error": "Multi-agent system not available"}
    
    try:
        if hasattr(orchestrator, 'execute_langraph_clinical_decision'):
            return orchestrator.execute_langraph_clinical_decision(query, patient_context)
        else:
            return {"error": "LangGraph clinical decision not available"}
    except Exception as e:
        return {"error": f"Failed to execute LangGraph clinical decision: {str(e)}"}

@mcp.tool()
def get_langraph_workflow_status() -> Dict[str, Any]:
    """Get status of LangGraph workflows and integration."""
    if not MULTI_AGENT_AVAILABLE or not orchestrator:
        return {"error": "Multi-agent system not available"}
    
    try:
        if hasattr(orchestrator, 'get_langraph_workflow_status'):
            return orchestrator.get_langraph_workflow_status()
        else:
            return {"error": "LangGraph workflow status not available"}
    except Exception as e:
        return {"error": f"Failed to get LangGraph workflow status: {str(e)}"}

@mcp.tool()
def route_to_langraph_workflow(workflow_type: str, workflow_params: Dict[str, Any]) -> Dict[str, Any]:
    """Intelligent routing between LangGraph and legacy workflows."""
    if not MULTI_AGENT_AVAILABLE or not orchestrator:
        return {"error": "Multi-agent system not available"}
    
    try:
        if hasattr(orchestrator, 'route_to_langraph_or_legacy'):
            return orchestrator.route_to_langraph_or_legacy(workflow_type, **workflow_params)
        else:
            return {"error": "LangGraph workflow routing not available"}
    except Exception as e:
        return {"error": f"Failed to route workflow: {str(e)}"}

# ================================
# ENHANCED AI CLINICAL TOOLS
# ================================

@mcp.tool()
def enhanced_symptom_analysis(symptoms: str, patient_history: str = "") -> Dict[str, Any]:
    """Analyze symptoms using enhanced LangChain-powered clinical reasoning."""
    try:
        from agents.enhanced_ai_clinical import enhanced_clinical_assistant
        
        if enhanced_clinical_assistant:
            return enhanced_clinical_assistant.analyze_symptoms(symptoms, patient_history)
        else:
            return {"error": "Enhanced AI Clinical Assistant not available"}
    except Exception as e:
        return {"error": f"Enhanced symptom analysis failed: {str(e)}"}

@mcp.tool()
def enhanced_differential_diagnosis(clinical_data: Dict[str, Any]) -> Dict[str, Any]:
    """Generate differential diagnosis using LangChain multi-step reasoning."""
    try:
        from agents.enhanced_ai_clinical import enhanced_clinical_assistant
        
        if enhanced_clinical_assistant:
            return enhanced_clinical_assistant.generate_differential_diagnosis(clinical_data)
        else:
            return {"error": "Enhanced AI Clinical Assistant not available"}
    except Exception as e:
        return {"error": f"Enhanced differential diagnosis failed: {str(e)}"}

@mcp.tool()
def enhanced_treatment_recommendations(treatment_data: Dict[str, Any]) -> Dict[str, Any]:
    """Recommend treatment using evidence-based LangChain reasoning."""
    try:
        from agents.enhanced_ai_clinical import enhanced_clinical_assistant
        
        if enhanced_clinical_assistant:
            return enhanced_clinical_assistant.recommend_treatment(treatment_data)
        else:
            return {"error": "Enhanced AI Clinical Assistant not available"}
    except Exception as e:
        return {"error": f"Enhanced treatment recommendations failed: {str(e)}"}

@mcp.tool()
def enhanced_drug_interaction_analysis(medication_data: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze drug interactions using comprehensive LangChain analysis."""
    try:
        from agents.enhanced_ai_clinical import enhanced_clinical_assistant
        
        if enhanced_clinical_assistant:
            return enhanced_clinical_assistant.analyze_drug_interactions(medication_data)
        else:
            return {"error": "Enhanced AI Clinical Assistant not available"}
    except Exception as e:
        return {"error": f"Enhanced drug interaction analysis failed: {str(e)}"}

@mcp.tool()
def enhanced_vital_signs_analysis(vitals_data: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze vital signs using intelligent LangChain interpretation."""
    try:
        from agents.enhanced_ai_clinical import enhanced_clinical_assistant
        
        if enhanced_clinical_assistant:
            return enhanced_clinical_assistant.analyze_vital_signs(vitals_data)
        else:
            return {"error": "Enhanced AI Clinical Assistant not available"}
    except Exception as e:
        return {"error": f"Enhanced vital signs analysis failed: {str(e)}"}

@mcp.tool()
def enhanced_clinical_risk_assessment(risk_data: Dict[str, Any]) -> Dict[str, Any]:
    """Assess clinical risk using comprehensive LangChain risk stratification."""
    try:
        from agents.enhanced_ai_clinical import enhanced_clinical_assistant
        
        if enhanced_clinical_assistant:
            return enhanced_clinical_assistant.assess_clinical_risk(risk_data)
        else:
            return {"error": "Enhanced AI Clinical Assistant not available"}
    except Exception as e:
        return {"error": f"Enhanced clinical risk assessment failed: {str(e)}"}

# ================================
# ADVANCED AI MASTER SYSTEM TOOLS
# ================================

@mcp.tool()
async def ai_master_request(user_request: str, user_id: str = "anonymous", 
                          context: Dict[str, Any] = None) -> Dict[str, Any]:
    """Process requests through the Master AI Hospital Management System with all advanced features."""
    if not ADVANCED_AI_AVAILABLE or not master_ai_system:
        return {"error": "Advanced AI Master System not available"}
    
    try:
        result = await master_ai_system.process_request(user_request, user_id, context)
        return result
    except Exception as e:
        return {"error": f"Master AI request failed: {str(e)}"}

@mcp.tool()
async def get_ai_system_dashboard() -> Dict[str, Any]:
    """Get comprehensive AI system dashboard with all metrics and insights."""
    if not ADVANCED_AI_AVAILABLE or not master_ai_system:
        return {"error": "Advanced AI Master System not available"}
    
    try:
        dashboard = await master_ai_system.get_comprehensive_dashboard()
        return dashboard
    except Exception as e:
        return {"error": f"Failed to get AI dashboard: {str(e)}"}

@mcp.tool()
async def run_predictive_forecast(prediction_type: str, forecast_horizon: str = "daily", 
                                periods: int = 30) -> Dict[str, Any]:
    """Run predictive analytics forecast for hospital planning."""
    if not ADVANCED_AI_AVAILABLE or not master_ai_system:
        return {"error": "Advanced AI Master System not available"}
    
    try:
        # Map string inputs to enums
        pred_type_map = {
            "bed_demand": PredictionType.BED_DEMAND,
            "staff_requirements": PredictionType.STAFF_REQUIREMENTS,
            "supply_consumption": PredictionType.SUPPLY_CONSUMPTION,
            "equipment_failure": PredictionType.EQUIPMENT_FAILURE,
            "patient_length_of_stay": PredictionType.PATIENT_LENGTH_OF_STAY,
            "readmission_risk": PredictionType.READMISSION_RISK
        }
        
        horizon_map = {
            "hourly": ForecastHorizon.HOURLY,
            "daily": ForecastHorizon.DAILY,
            "weekly": ForecastHorizon.WEEKLY,
            "monthly": ForecastHorizon.MONTHLY
        }
        
        pred_type = pred_type_map.get(prediction_type, PredictionType.BED_DEMAND)
        horizon = horizon_map.get(forecast_horizon, ForecastHorizon.DAILY)
        
        forecast = await master_ai_system.predictive_system.run_prediction(pred_type, horizon, periods)
        
        return {
            "prediction_id": forecast.prediction_id,
            "prediction_type": forecast.prediction_type.value,
            "forecast_horizon": forecast.forecast_horizon.value,
            "predictions": forecast.predictions,
            "confidence_intervals": forecast.confidence_intervals,
            "accuracy_metrics": forecast.accuracy_metrics,
            "recommendations": forecast.recommendations,
            "timestamp": forecast.timestamp.isoformat()
        }
    except Exception as e:
        return {"error": f"Predictive forecast failed: {str(e)}"}

@mcp.tool()
async def translate_medical_text(text: str, target_language: str, 
                               content_type: str = "general_communication",
                               patient_id: str = None) -> Dict[str, Any]:
    """Translate medical text with cultural adaptation and medical terminology."""
    if not ADVANCED_AI_AVAILABLE or not master_ai_system:
        return {"error": "Advanced AI Master System not available"}
    
    try:
        # Map string inputs to enums
        lang_map = {
            "spanish": LanguageCode.SPANISH, "es": LanguageCode.SPANISH,
            "french": LanguageCode.FRENCH, "fr": LanguageCode.FRENCH,
            "german": LanguageCode.GERMAN, "de": LanguageCode.GERMAN,
            "chinese": LanguageCode.CHINESE_SIMPLIFIED, "zh": LanguageCode.CHINESE_SIMPLIFIED,
            "japanese": LanguageCode.JAPANESE, "ja": LanguageCode.JAPANESE,
            "korean": LanguageCode.KOREAN, "ko": LanguageCode.KOREAN,
            "arabic": LanguageCode.ARABIC, "ar": LanguageCode.ARABIC,
            "hindi": LanguageCode.HINDI, "hi": LanguageCode.HINDI,
            "portuguese": LanguageCode.PORTUGUESE, "pt": LanguageCode.PORTUGUESE,
            "russian": LanguageCode.RUSSIAN, "ru": LanguageCode.RUSSIAN
        }
        
        content_map = {
            "medical_forms": ContentType.MEDICAL_FORMS,
            "discharge_instructions": ContentType.DISCHARGE_INSTRUCTIONS,
            "consent_forms": ContentType.CONSENT_FORMS,
            "medication_labels": ContentType.MEDICATION_LABELS,
            "treatment_plans": ContentType.TREATMENT_PLANS,
            "general_communication": ContentType.GENERAL_COMMUNICATION,
            "emergency_instructions": ContentType.EMERGENCY_INSTRUCTIONS
        }
        
        target_lang = lang_map.get(target_language.lower(), LanguageCode.SPANISH)
        content_t = content_map.get(content_type, ContentType.GENERAL_COMMUNICATION)
        
        translation = await master_ai_system.multilingual_agent.translate_text(
            text, target_lang, content_t, patient_id
        )
        
        return {
            "request_id": translation.request_id,
            "translated_text": translation.translated_text,
            "confidence_score": translation.confidence_score,
            "cultural_adaptations": translation.cultural_adaptations,
            "medical_terminology_notes": translation.medical_terminology_notes,
            "alternative_translations": translation.alternative_translations,
            "timestamp": translation.timestamp.isoformat()
        }
    except Exception as e:
        return {"error": f"Medical translation failed: {str(e)}"}

@mcp.tool()
async def manage_equipment_lifecycle(asset_id: str) -> Dict[str, Any]:
    """Run comprehensive equipment lifecycle management analysis."""
    if not ADVANCED_AI_AVAILABLE or not master_ai_system:
        return {"error": "Advanced AI Master System not available"}
    
    try:
        result = await master_ai_system.equipment_manager.manage_equipment_lifecycle(asset_id)
        return result
    except Exception as e:
        return {"error": f"Equipment lifecycle management failed: {str(e)}"}

@mcp.tool()
def get_equipment_dashboard(asset_id: str) -> Dict[str, Any]:
    """Get comprehensive equipment dashboard for specific asset."""
    if not ADVANCED_AI_AVAILABLE or not master_ai_system:
        return {"error": "Advanced AI Master System not available"}
    
    try:
        dashboard = master_ai_system.equipment_manager.get_equipment_dashboard(asset_id)
        return dashboard
    except Exception as e:
        return {"error": f"Equipment dashboard failed: {str(e)}"}

@mcp.tool()
def get_fleet_overview() -> Dict[str, Any]:
    """Get overview of entire equipment fleet with lifecycle analytics."""
    if not ADVANCED_AI_AVAILABLE or not master_ai_system:
        return {"error": "Advanced AI Master System not available"}
    
    try:
        overview = master_ai_system.equipment_manager.get_fleet_overview()
        return overview
    except Exception as e:
        return {"error": f"Fleet overview failed: {str(e)}"}

@mcp.tool()
def get_supported_languages() -> List[Dict[str, str]]:
    """Get list of supported languages for translation."""
    if not ADVANCED_AI_AVAILABLE or not master_ai_system:
        return []
    
    try:
        languages = master_ai_system.multilingual_agent.get_supported_languages()
        return languages
    except Exception as e:
        return []

@mcp.tool()
def get_emergency_phrases(language: str) -> List[Dict[str, str]]:
    """Get emergency medical phrases in specified language."""
    if not ADVANCED_AI_AVAILABLE or not master_ai_system:
        return []
    
    try:
        lang_map = {
            "spanish": LanguageCode.SPANISH, "es": LanguageCode.SPANISH,
            "french": LanguageCode.FRENCH, "fr": LanguageCode.FRENCH,
            "german": LanguageCode.GERMAN, "de": LanguageCode.GERMAN,
            "chinese": LanguageCode.CHINESE_SIMPLIFIED, "zh": LanguageCode.CHINESE_SIMPLIFIED,
            "arabic": LanguageCode.ARABIC, "ar": LanguageCode.ARABIC
        }
        
        target_lang = lang_map.get(language.lower(), LanguageCode.SPANISH)
        phrases = master_ai_system.multilingual_agent.get_emergency_phrases(target_lang)
        return phrases
    except Exception as e:
        return []

@mcp.tool()
def get_ai_system_health() -> Dict[str, Any]:
    """Get comprehensive AI system health status."""
    if not ADVANCED_AI_AVAILABLE or not master_ai_system:
        return {"error": "Advanced AI Master System not available"}
    
    try:
        health = master_ai_system.get_system_health_summary()
        return health
    except Exception as e:
        return {"error": f"System health check failed: {str(e)}"}

# ================================
# USER MANAGEMENT TOOLS
# ================================

@mcp.tool()
def create_user(username: str, email: str, password_hash: str, role: str, 
                first_name: str, last_name: str, phone: str = None, is_active: bool = True) -> Dict[str, Any]:
    """Create a new user in the database."""
    if MULTI_AGENT_AVAILABLE and orchestrator:
        result = orchestrator.route_request("create_user", 
                                           username=username, email=email, password_hash=password_hash,
                                           role=role, first_name=first_name, last_name=last_name, 
                                           phone=phone, is_active=is_active)
        return result.get("result", result)
    
    # Fallback to direct implementation if multi-agent not available
    if not DATABASE_AVAILABLE:
        return {"success": False, "message": "Database not available"}
    
    try:
        db = get_db_session()
        user = User(
            username=username, email=email, password_hash=password_hash, role=role,
            first_name=first_name, last_name=last_name, phone=phone
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        result = serialize_model(user)
        db.close()
        return {"success": True, "message": "User created successfully", "data": result}
    except Exception as e:
        return {"success": False, "message": f"Failed to create user: {str(e)}"}

@mcp.tool()
def get_user_by_id(user_id: str) -> Dict[str, Any]:
    """Get a user by ID."""
    if MULTI_AGENT_AVAILABLE and orchestrator:
        result = orchestrator.route_request("get_user_by_id", user_id=user_id)
        return result.get("result", result)
    
    # Fallback implementation
    if not DATABASE_AVAILABLE:
        return {"error": "Database not available"}
    
    try:
        db = get_db_session()
        user = db.query(User).filter(User.id == uuid.UUID(user_id)).first()
        result = serialize_model(user) if user else None
        db.close()
        return {"data": result} if result else {"error": "User not found"}
    except Exception as e:
        return {"error": f"Failed to get user: {str(e)}"}

@mcp.tool()
def list_users() -> Dict[str, Any]:
    """List all users in the database."""
    if MULTI_AGENT_AVAILABLE and orchestrator:
        result = orchestrator.route_request("list_users")
        return result.get("result", result)
    
    # Fallback implementation
    if not DATABASE_AVAILABLE:
        return {"error": "Database not available"}
    
    try:
        db = get_db_session()
        users = db.query(User).all()
        result = [serialize_model(user) for user in users]
        db.close()
        return {"data": result}
    except Exception as e:
        return {"error": f"Failed to list users: {str(e)}"}

@mcp.tool()
def update_user(user_id: str, username: str = None, email: str = None, role: str = None,
               first_name: str = None, last_name: str = None, phone: str = None, 
               is_active: bool = None) -> Dict[str, Any]:
    """Update user information."""
    if MULTI_AGENT_AVAILABLE and orchestrator:
        result = orchestrator.route_request("update_user", 
                                           user_id=user_id, username=username, email=email, role=role,
                                           first_name=first_name, last_name=last_name, phone=phone, is_active=is_active)
        return result.get("result", result)
    
    # Fallback implementation would go here
    return {"success": False, "message": "Multi-agent system required for this operation"}

@mcp.tool()
def delete_user(user_id: str) -> Dict[str, Any]:
    """Delete a user from the database."""
    if MULTI_AGENT_AVAILABLE and orchestrator:
        result = orchestrator.route_request("delete_user", user_id=user_id)
        return result.get("result", result)
    
    return {"success": False, "message": "Multi-agent system required for this operation"}

# ================================
# PATIENT MANAGEMENT TOOLS
# ================================

@mcp.tool()
def create_patient(first_name: str, last_name: str, date_of_birth: str,
                  gender: str = None, phone: str = None, email: str = None,
                  address: str = None, emergency_contact_name: str = None,
                  emergency_contact_phone: str = None, blood_type: str = None,
                  allergies: str = None, medical_history: str = None,
                  patient_number: str = None) -> Dict[str, Any]:
    """Create a new patient record."""
    if MULTI_AGENT_AVAILABLE and orchestrator:
        result = orchestrator.route_request("create_patient",
                                           first_name=first_name, last_name=last_name, date_of_birth=date_of_birth,
                                           gender=gender, phone=phone, email=email, address=address,
                                           emergency_contact_name=emergency_contact_name,
                                           emergency_contact_phone=emergency_contact_phone,
                                           blood_type=blood_type, allergies=allergies, medical_history=medical_history,
                                           patient_number=patient_number)
        return result.get("result", result)
    
    return {"success": False, "message": "Multi-agent system required for this operation"}

@mcp.tool()
def check_bed_status(bed_id: str) -> Dict[str, Any]:
    """🎯 PRIMARY TOOL: Check specific bed status (e.g., bed 302A) - USE THIS for individual bed queries!
    
    ✅ Use when user asks: "check bed 302A status", "is bed cleaning done", "bed status after discharge"
    ❌ NEVER use list_beds for individual bed queries - it returns ALL beds unnecessarily!
    
    This tool shows:
    - Current bed status (cleaning, available, occupied)
    - Time remaining for cleaning process
    - Cleaning progress percentage
    - Estimated completion time
    
    Args:
        bed_id: Bed number (e.g., "302A") or bed UUID
        
    Returns:
        Detailed bed status including cleaning time remaining and progress
    """
    if MULTI_AGENT_AVAILABLE and orchestrator:
        result = orchestrator.route_request("get_bed_status_with_time_remaining", bed_id=bed_id)
        return result.get("result", result)
    
    return {"error": "Multi-agent system required for this operation"}

@mcp.tool()
def auto_update_expired_cleaning_beds() -> Dict[str, Any]:
    """🔄 Automatically update beds that completed their 30-minute cleaning to 'available' status.
    
    This tool:
    - Checks all beds in 'cleaning' status
    - Updates beds to 'available' if cleaning time (30 min) has elapsed
    - Fixes orphaned beds stuck in cleaning status
    - Returns list of updated beds
    
    Use this to:
    - Force update of expired cleaning beds
    - Fix beds stuck in cleaning status
    - Ensure beds become available after cleaning time completes
    """
    if MULTI_AGENT_AVAILABLE and orchestrator:
        result = orchestrator.route_request("auto_update_expired_cleaning_beds")
        return result.get("result", result)
    
    return {"error": "Multi-agent system required for this operation"}

@mcp.tool()
def list_patients(status: str = "active") -> Dict[str, Any]:
    """List patients with optional status filtering.
    
    Args:
        status: Filter by patient status - "active" (default), "discharged", "all"
    """
    if MULTI_AGENT_AVAILABLE and orchestrator:
        result = orchestrator.route_request("list_patients", status=status)
        return result.get("result", result)
    
    return {"error": "Multi-agent system required for this operation"}

@mcp.tool()
def get_patient_by_id(patient_id: str) -> Dict[str, Any]:
    """Get a patient by ID."""
    if MULTI_AGENT_AVAILABLE and orchestrator:
        result = orchestrator.route_request("get_patient_by_id", patient_id=patient_id)
        return result.get("result", result)
    
    return {"error": "Multi-agent system required for this operation"}

@mcp.tool()
def search_patients(patient_number: str = None, first_name: str = None, 
                   last_name: str = None, phone: str = None, email: str = None) -> Dict[str, Any]:
    """Search for patients by various criteria."""
    if MULTI_AGENT_AVAILABLE and orchestrator:
        result = orchestrator.route_request("search_patients",
                                           patient_number=patient_number, first_name=first_name,
                                           last_name=last_name, phone=phone, email=email)
        return result.get("result", result)
    
    return {"error": "Multi-agent system required for this operation"}

@mcp.tool()
def update_patient(patient_id: str, first_name: str = None, last_name: str = None,
                   gender: str = None, phone: str = None, email: str = None,
                   address: str = None, emergency_contact_name: str = None,
                   emergency_contact_phone: str = None, blood_type: str = None,
                   allergies: str = None, medical_history: str = None) -> Dict[str, Any]:
    """Update an existing patient record in PostgreSQL."""
    if MULTI_AGENT_AVAILABLE and orchestrator:
        result = orchestrator.route_request("update_patient",
                                           patient_id=patient_id, first_name=first_name,
                                           last_name=last_name, gender=gender, phone=phone,
                                           email=email, address=address,
                                           emergency_contact_name=emergency_contact_name,
                                           emergency_contact_phone=emergency_contact_phone,
                                           blood_type=blood_type, allergies=allergies,
                                           medical_history=medical_history)
        return result.get("result", result)
    return {"error": "Multi-agent system required for this operation"}

# ================================
# DEPARTMENT MANAGEMENT TOOLS
# ================================

@mcp.tool()
def create_department(name: str, description: str = None, head_doctor_id: str = None,
                     floor_number: int = None, phone: str = None, email: str = None) -> Dict[str, Any]:
    """Create a new department."""
    if MULTI_AGENT_AVAILABLE and orchestrator:
        result = orchestrator.route_request("create_department",
                                           name=name, description=description, head_doctor_id=head_doctor_id,
                                           floor_number=floor_number, phone=phone, email=email)
        return result.get("result", result)
    # Direct DB fallback
    if not DATABASE_AVAILABLE:
        return {"success": False, "message": "Database not available"}
    try:
        db = get_db_session()
        department = Department(
            name=name,
            description=description,
            head_doctor_id=uuid.UUID(head_doctor_id) if head_doctor_id else None,
            floor_number=floor_number,
            phone=phone,
            email=email
        )
        db.add(department)
        db.commit()
        db.refresh(department)
        result = serialize_model(department)
        db.close()
        return {"success": True, "message": "Department created successfully", "data": result}
    except Exception as e:
        return {"success": False, "message": f"Failed to create department: {str(e)}"}

@mcp.tool()
def list_departments() -> Dict[str, Any]:
    """List all departments."""
    if MULTI_AGENT_AVAILABLE and orchestrator:
        result = orchestrator.route_request("list_departments")
        return result.get("result", result)
    
    return {"error": "Multi-agent system required for this operation"}

@mcp.tool()
def get_department_by_id(department_id: str) -> Dict[str, Any]:
    """Get a department by ID."""
    if MULTI_AGENT_AVAILABLE and orchestrator:
        result = orchestrator.route_request("get_department_by_id", department_id=department_id)
        return result.get("result", result)
    
    return {"error": "Multi-agent system required for this operation"}

# ================================
# ROOM & BED MANAGEMENT TOOLS
# ================================

@mcp.tool()
def create_room(room_number: str, department_id: str, room_type: str = None,
               floor_number: int = None, capacity: int = None, status: str = "available") -> Dict[str, Any]:
    """Create a new room."""
    if MULTI_AGENT_AVAILABLE and orchestrator:
        result = orchestrator.route_request("create_room",
                                           room_number=room_number, department_id=department_id,
                                           room_type=room_type, floor_number=floor_number, 
                                           capacity=capacity, status=status)
        return result.get("result", result)
    # Direct DB fallback
    if not DATABASE_AVAILABLE:
        return {"success": False, "message": "Database not available"}
    try:
        db = get_db_session()
        room = Room(
            room_number=room_number,
            department_id=uuid.UUID(department_id),
            room_type=room_type,
            floor_number=floor_number,
            capacity=capacity
        )
        db.add(room)
        db.commit()
        db.refresh(room)
        result = serialize_model(room)
        db.close()
        return {"success": True, "message": "Room created successfully", "data": result}
    except Exception as e:
        return {"success": False, "message": f"Failed to create room: {str(e)}"}

@mcp.tool()
def list_rooms(department_id: str = None, status: str = None) -> Dict[str, Any]:
    """List rooms with optional filtering."""
    if MULTI_AGENT_AVAILABLE and orchestrator:
        result = orchestrator.route_request("list_rooms", department_id=department_id, status=status)
        return result.get("result", result)
    
    return {"error": "Multi-agent system required for this operation"}

@mcp.tool()
def create_bed(bed_number: str, room_id: str, bed_type: str = None, status: str = "available") -> Dict[str, Any]:
    """Create a new bed."""
    if MULTI_AGENT_AVAILABLE and orchestrator:
        result = orchestrator.route_request("create_bed",
                                           bed_number=bed_number, room_id=room_id,
                                           bed_type=bed_type, status=status)
        return result.get("result", result)
    # Direct DB fallback
    if not DATABASE_AVAILABLE:
        return {"success": False, "message": "Database not available"}
    try:
        db = get_db_session()
        bed = Bed(
            bed_number=bed_number,
            room_id=uuid.UUID(room_id),
            bed_type=bed_type,
            status=status
        )
        db.add(bed)
        db.commit()
        db.refresh(bed)
        result = serialize_model(bed)
        db.close()
        return {"success": True, "message": "Bed created successfully", "data": result}
    except Exception as e:
        return {"success": False, "message": f"Failed to create bed: {str(e)}"}

@mcp.tool()
def list_beds(status: str = None, room_id: str = None, bed_number: str = None) -> Dict[str, Any]:
    """❌ WARNING: DO NOT USE for checking individual bed status! Returns ALL beds unnecessarily.
    
    ❌ WRONG: "check bed 302A status" - use get_bed_status_with_time_remaining() instead!
    ❌ WRONG: "is bed cleaning done" - use get_bed_status_with_time_remaining() instead!
    
    ✅ ONLY use list_beds for:
    - Getting overview of multiple beds
    - Finding available beds for assignment
    - General bed inventory management
    
    For individual bed queries, use get_bed_status_with_time_remaining() which shows cleaning time remaining!
    
    🔄 SMART REDIRECT: If bed_number is provided, automatically redirects to proper bed status check.
    """
    # SMART REDIRECT: If this looks like an individual bed query, use the correct tool
    if bed_number:
        print(f"🔄 SMART REDIRECT: list_beds called with bed_number '{bed_number}' - redirecting to get_bed_status_with_time_remaining")
        if MULTI_AGENT_AVAILABLE and orchestrator:
            result = orchestrator.route_request("get_bed_status_with_time_remaining", bed_id=bed_number)
            redirect_result = result.get("result", result)
            # Add redirect notice to the response
            if isinstance(redirect_result, dict) and redirect_result.get("success"):
                redirect_result["redirect_notice"] = f"✅ Auto-redirected from list_beds to get_bed_status_with_time_remaining for bed {bed_number}"
            return redirect_result
    
    if MULTI_AGENT_AVAILABLE and orchestrator:
        result = orchestrator.route_request("list_beds", status=status, room_id=room_id)
        list_result = result.get("result", result)
        
        # SMART HELPER: Add guidance message if this looks like an individual bed search
        if isinstance(list_result, dict) and "data" in list_result:
            beds_data = list_result["data"]
            # Check if we have bed 302A in the results
            bed_302a = next((bed for bed in beds_data if bed.get("bed_number") == "302A"), None)
            
            if bed_302a:
                # Add helpful guidance to the response
                list_result["bed_302a_found"] = bed_302a
                list_result["helpful_message"] = (
                    f"🛏️ Found bed 302A: Status = {bed_302a.get('status', 'unknown')}. "
                    f"For detailed bed status with cleaning time remaining, "
                    f"use 'get_bed_status_with_time_remaining' tool instead of 'list_beds'."
                )
                
                # If bed is available, add completion message
                if bed_302a.get("status") == "available":
                    list_result["helpful_message"] += (
                        f" ✅ Bed 302A is ready for new patients!"
                    )
        
        return list_result
    
    return {"error": "Multi-agent system required for this operation"}

@mcp.tool()
def get_bed_by_id(bed_id: str) -> Dict[str, Any]:
    """Get bed details by bed ID."""
    if MULTI_AGENT_AVAILABLE and orchestrator:
        result = orchestrator.route_request("get_bed_by_id", bed_id=bed_id)
        return result.get("result", result)
    
    return {"error": "Multi-agent system required for this operation"}

@mcp.tool()
def get_bed_by_number(bed_number: str) -> Dict[str, Any]:
    """Get bed details by bed number."""
    if MULTI_AGENT_AVAILABLE and orchestrator:
        result = orchestrator.route_request("get_bed_by_number", bed_number=bed_number)
        return result.get("result", result)
    
    return {"error": "Multi-agent system required for this operation"}

@mcp.tool()
def assign_bed_to_patient(bed_id: str, patient_id: str, admission_date: str = None) -> Dict[str, Any]:
    """Assign a bed to a patient."""
    if MULTI_AGENT_AVAILABLE and orchestrator:
        result = orchestrator.route_request("assign_bed_to_patient",
                                           bed_id=bed_id, patient_id=patient_id, admission_date=admission_date)
        return result.get("result", result)
    
    return {"success": False, "message": "Multi-agent system required for this operation"}

@mcp.tool()
def discharge_bed(bed_id: str, discharge_date: str = None) -> Dict[str, Any]:
    """Discharge a patient from a bed.
    Attempts full discharge workflow (report + turnover) before falling back to simple bed discharge.
    """
    if MULTI_AGENT_AVAILABLE and orchestrator:
        # Prefer comprehensive workflow to ensure report generation before clearing bed
        try:
            comp = orchestrator.route_request("discharge_patient_complete", bed_id=bed_id)
            comp_result = comp.get("result", comp)
            if isinstance(comp_result, dict) and comp_result.get("success"):
                return comp_result
        except Exception as e:
            print(f"⚠️ Comprehensive discharge failed for bed {bed_id}: {e}")
        
        # Fallback to simple discharge if comprehensive fails
        try:
            result = orchestrator.route_request("discharge_bed", bed_id=bed_id, discharge_date=discharge_date)
            return result.get("result", result)
        except Exception as e:
            return {"success": False, "message": f"Failed to discharge bed: {e}"}
    
    return {"error": "Multi-agent system required for bed discharge"}

# ================================
# PATIENT SUPPLY USAGE TOOLS
@mcp.tool()
def record_patient_supply_usage(patient_id: str = None, patient_number: str = None,
                               supply_id: str = None, supply_item_code: str = None, 
                               quantity_used: int = 1, dosage: str = None, frequency: str = None, 
                               prescribed_by_id: str = None, administered_by_id: str = None,
                               staff_id: str = None, employee_id: str = None,
                               bed_id: str = None, administration_route: str = "oral",
                               indication: str = None, start_date: str = None, 
                               end_date: str = None, notes: str = None) -> Dict[str, Any]:
    """Record medication or supply usage for a patient. Use either patient_id/patient_number and supply_id/supply_item_code."""
    if MULTI_AGENT_AVAILABLE and orchestrator:
        result = orchestrator.route_request("record_patient_supply_usage",
                                           patient_id=patient_id, patient_number=patient_number,
                                           supply_id=supply_id, supply_item_code=supply_item_code,
                                           quantity_used=quantity_used, dosage=dosage,
                                           frequency=frequency, prescribed_by_id=prescribed_by_id,
                                           administered_by_id=administered_by_id, staff_id=staff_id,
                                           employee_id=employee_id, bed_id=bed_id,
                                           administration_route=administration_route,
                                           indication=indication, start_date=start_date,
                                           end_date=end_date, notes=notes)
        return result.get("result", result)
    
    return {"error": "Multi-agent system required for this operation"}

@mcp.tool()
def get_patient_supply_usage(usage_id: str) -> Dict[str, Any]:
    """Get specific supply usage record by ID."""
    if MULTI_AGENT_AVAILABLE and orchestrator:
        result = orchestrator.route_request("get_patient_supply_usage", usage_id=usage_id)
        return result.get("result", result)
    
    return {"error": "Multi-agent system required for this operation"}

@mcp.tool()
def update_supply_usage_status(usage_id: str, status: str, administration_date: str = None,
                             effectiveness: str = None, side_effects: str = None,
                             notes: str = None) -> Dict[str, Any]:
    """Update status of supply usage (administered, completed, discontinued)."""
    if MULTI_AGENT_AVAILABLE and orchestrator:
        result = orchestrator.route_request("update_supply_usage_status",
                                           usage_id=usage_id, status=status,
                                           administration_date=administration_date,
                                           effectiveness=effectiveness,
                                           side_effects=side_effects, notes=notes)
        return result.get("result", result)
    
    return {"error": "Multi-agent system required for this operation"}

@mcp.tool()
def get_supply_usage_for_discharge_report(patient_id: str, admission_date: str = None,
                                        discharge_date: str = None) -> Dict[str, Any]:
    """Get all supply usage for a patient's discharge report."""
    if MULTI_AGENT_AVAILABLE and orchestrator:
        result = orchestrator.route_request("get_supply_usage_for_discharge_report",
                                           patient_id=patient_id,
                                           admission_date=admission_date,
                                           discharge_date=discharge_date)
        return result.get("result", result)
    
    return {"error": "Multi-agent system required for this operation"}

@mcp.tool()
def record_patient_supply_usage_by_code(patient_number: str = None, patient_id: str = None, 
                                       supply_item_code: str = None, quantity_used: int = 1, 
                                       staff_id: str = None, employee_id: str = None,
                                       date_of_usage: str = None, notes: str = None) -> Dict[str, Any]:
    """Record patient supply usage using user-friendly codes (patient number, item code, employee ID)."""
    if MULTI_AGENT_AVAILABLE and orchestrator:
        # Convert date_of_usage to start_date format
        start_date = date_of_usage if date_of_usage else None
        
        result = orchestrator.route_request("record_patient_supply_usage",
                                           patient_id=patient_id,
                                           patient_number=patient_number, 
                                           supply_item_code=supply_item_code,
                                           quantity_used=quantity_used, 
                                           staff_id=staff_id,
                                           employee_id=employee_id,
                                           start_date=start_date,
                                           notes=notes)
        return result.get("result", result)
    
    return {"error": "Multi-agent system required for this operation"}

@mcp.tool()
def list_patient_medications(patient_id: str) -> Dict[str, Any]:
    """List all medications/supplies used by a patient."""
    if MULTI_AGENT_AVAILABLE and orchestrator:
        result = orchestrator.route_request("list_patient_medications", patient_id=patient_id)
        return result.get("result", result)
    
    return {"error": "Multi-agent system required for this operation"}

@mcp.tool()
def search_supply_usage_by_patient(patient_name: str = None, patient_number: str = None,
                                 supply_name: str = None, status: str = None) -> Dict[str, Any]:
    """Search supply usage records for a specific patient."""
    if MULTI_AGENT_AVAILABLE and orchestrator:
        result = orchestrator.route_request("search_supply_usage_by_patient",
                                           patient_name=patient_name,
                                           patient_number=patient_number,
                                           supply_name=supply_name, status=status)
        return result.get("result", result)
    
    return {"error": "Multi-agent system required for this operation"}

@mcp.tool()
def calculate_patient_medication_costs(patient_id: str, admission_date: str = None,
                                     discharge_date: str = None) -> Dict[str, Any]:
    """Calculate total medication costs for a patient stay."""
    if MULTI_AGENT_AVAILABLE and orchestrator:
        result = orchestrator.route_request("calculate_patient_medication_costs",
                                           patient_id=patient_id,
                                           admission_date=admission_date,
                                           discharge_date=discharge_date)
        return result.get("result", result)
    
    return {"error": "Multi-agent system required for this operation"}

# ================================
# STAFF MANAGEMENT TOOLS
@mcp.tool()
def create_equipment(equipment_id: str, name: str, category_id: str, model: str = None,
                    manufacturer: str = None, serial_number: str = None, purchase_date: str = None,
                    warranty_expiry: str = None, location: str = None, department_id: str = None,
                    cost: float = None, last_maintenance: str = None, next_maintenance: str = None) -> Dict[str, Any]:
    """Create a new equipment item."""
    if MULTI_AGENT_AVAILABLE and orchestrator:
        result = orchestrator.route_request("create_equipment",
                                           equipment_id=equipment_id, name=name, category_id=category_id,
                                           model=model, manufacturer=manufacturer, serial_number=serial_number,
                                           purchase_date=purchase_date, warranty_expiry=warranty_expiry,
                                           location=location, department_id=department_id, cost=cost,
                                           last_maintenance=last_maintenance, next_maintenance=next_maintenance)
        return result.get("result", result)
    # Direct DB fallback
    if not DATABASE_AVAILABLE:
        return {"success": False, "message": "Database not available"}
    try:
        db = get_db_session()
        equipment = Equipment(
            equipment_id=equipment_id,
            name=name,
            category_id=uuid.UUID(category_id),
            model=model,
            manufacturer=manufacturer,
            serial_number=serial_number,
            purchase_date=datetime.strptime(purchase_date, "%Y-%m-%d").date() if purchase_date else None,
            warranty_expiry=datetime.strptime(warranty_expiry, "%Y-%m-%d").date() if warranty_expiry else None,
            location=location,
            department_id=uuid.UUID(department_id) if department_id else None,
            cost=Decimal(str(cost)) if cost else None
        )
        db.add(equipment)
        db.commit()
        db.refresh(equipment)
        result = serialize_model(equipment)
        db.close()
        return {"success": True, "message": "Equipment created successfully", "data": result}
    except Exception as e:
        return {"success": False, "message": f"Failed to create equipment: {str(e)}"}

@mcp.tool()
def create_supply(item_code: str, name: str, category_id: str, unit_of_measure: str,
                 description: str = None, minimum_stock_level: int = 0, maximum_stock_level: int = None,
                 current_stock: int = 0, unit_cost: float = None, supplier: str = None,
                 expiry_date: str = None, location: str = None) -> Dict[str, Any]:
    """Create a new supply item."""
    if MULTI_AGENT_AVAILABLE and orchestrator:
        result = orchestrator.route_request("create_supply",
                                           item_code=item_code, name=name, category_id=category_id,
                                           unit_of_measure=unit_of_measure, description=description,
                                           minimum_stock_level=minimum_stock_level, maximum_stock_level=maximum_stock_level,
                                           current_stock=current_stock, unit_cost=unit_cost, supplier=supplier,
                                           expiry_date=expiry_date, location=location)
        return result.get("result", result)

@mcp.tool()
def schedule_equipment_maintenance(equipment_id: str, maintenance_date: str,
                                 maintenance_type: str = "routine", notes: str = None) -> Dict[str, Any]:
    """Schedule maintenance for equipment."""
    if MULTI_AGENT_AVAILABLE and orchestrator:
        result = orchestrator.route_request("schedule_equipment_maintenance",
                                           equipment_id=equipment_id, maintenance_date=maintenance_date,
                                           maintenance_type=maintenance_type, notes=notes)
        return result.get("result", result)
    
    return {"success": False, "message": "Multi-agent system required for this operation"}

@mcp.tool()
def list_equipment(status: str = None, department_id: str = None, category_id: str = None) -> Dict[str, Any]:
    """List equipment with optional filtering."""
    if MULTI_AGENT_AVAILABLE and orchestrator:
        result = orchestrator.route_request("list_equipment",
                                           status=status, department_id=department_id, category_id=category_id)
        return result.get("result", result)
    
    return {"error": "Multi-agent system required for this operation"}

@mcp.tool()
def create_equipment_category(name: str, description: str = None) -> Dict[str, Any]:
    """Create a new equipment category."""
    if MULTI_AGENT_AVAILABLE and orchestrator:
        result = orchestrator.route_request("create_equipment_category",
                                           name=name, description=description)
        return result.get("result", result)
    
    return {"error": "Multi-agent system required for this operation"}

@mcp.tool()
def list_equipment_categories() -> Dict[str, Any]:
    """List all equipment categories."""
    if MULTI_AGENT_AVAILABLE and orchestrator:
        result = orchestrator.route_request("list_equipment_categories")
        return result.get("result", result)
    
    return {"error": "Multi-agent system required for this operation"}

@mcp.tool()
def get_equipment_by_id(equipment_id: str) -> Dict[str, Any]:
    """Get equipment by ID."""
    if MULTI_AGENT_AVAILABLE and orchestrator:
        result = orchestrator.route_request("get_equipment_by_id", equipment_id=equipment_id)
        return result.get("result", result)
    
    return {"error": "Multi-agent system required for this operation"}

@mcp.tool()
def update_equipment_status(equipment_id: str, status: str, notes: str = None) -> Dict[str, Any]:
    """Update equipment status."""
    if MULTI_AGENT_AVAILABLE and orchestrator:
        result = orchestrator.route_request("update_equipment_status",
                                           equipment_id=equipment_id, status=status, notes=notes)
        return result.get("result", result)
    
    return {"error": "Multi-agent system required for this operation"}

@mcp.tool()
def update_equipment(equipment_id: str, name: str = None, model: str = None, 
                    manufacturer: str = None, location: str = None, 
                    department_id: str = None, status: str = None) -> Dict[str, Any]:
    """Update equipment information."""
    if MULTI_AGENT_AVAILABLE and orchestrator:
        result = orchestrator.route_request("update_equipment",
                                           equipment_id=equipment_id, name=name, model=model,
                                           manufacturer=manufacturer, location=location,
                                           department_id=department_id, status=status)
        return result.get("result", result)
    
    return {"error": "Multi-agent system required for this operation"}

@mcp.tool()
def delete_equipment(equipment_id: str) -> Dict[str, Any]:
    """Delete equipment."""
    if MULTI_AGENT_AVAILABLE and orchestrator:
        result = orchestrator.route_request("delete_equipment", equipment_id=equipment_id)
        return result.get("result", result)
    
    return {"error": "Multi-agent system required for this operation"}

@mcp.tool()
def get_equipment_by_status(status: str) -> Dict[str, Any]:
    """Get all equipment with a specific status."""
    if MULTI_AGENT_AVAILABLE and orchestrator:
        result = orchestrator.route_request("get_equipment_by_status", status=status)
        return result.get("result", result)
    
    return {"error": "Multi-agent system required for this operation"}

@mcp.tool()
def list_supplies(low_stock_only: bool = False, category_id: str = None) -> Dict[str, Any]:
    """List supplies with optional filtering."""
    if MULTI_AGENT_AVAILABLE and orchestrator:
        result = orchestrator.route_request("list_supplies",
                                           low_stock_only=low_stock_only, category_id=category_id)
        return result.get("result", result)
    
    return {"error": "Multi-agent system required for this operation"}

@mcp.tool()
def get_supply_by_id(supply_id: str) -> Dict[str, Any]:
    """Get supply by ID."""
    if MULTI_AGENT_AVAILABLE and orchestrator:
        result = orchestrator.route_request("get_supply_by_id", supply_id=supply_id)
        return result.get("result", result)
    
    return {"error": "Multi-agent system required for this operation"}

@mcp.tool()
def update_supply_stock(supply_id: str, quantity_change: int, transaction_type: str,
                       performed_by: str = None, user_id: str = None, notes: str = None) -> Dict[str, Any]:
    """Update supply stock levels and log the transaction."""
    if MULTI_AGENT_AVAILABLE and orchestrator:
        result = orchestrator.route_request("update_supply_stock",
                                           supply_id=supply_id, quantity_change=quantity_change,
                                           transaction_type=transaction_type, performed_by=performed_by,
                                           user_id=user_id, notes=notes)
        return result.get("result", result)
    
    return {"error": "Multi-agent system required for this operation"}

@mcp.tool()
def update_supply(supply_id: str, name: str = None, unit_of_measure: str = None,
                 minimum_stock_level: int = None, maximum_stock_level: int = None,
                 unit_cost: float = None, supplier: str = None) -> Dict[str, Any]:
    """Update supply information."""
    if MULTI_AGENT_AVAILABLE and orchestrator:
        result = orchestrator.route_request("update_supply",
                                           supply_id=supply_id, name=name, unit_of_measure=unit_of_measure,
                                           minimum_stock_level=minimum_stock_level, maximum_stock_level=maximum_stock_level,
                                           unit_cost=unit_cost, supplier=supplier)
        return result.get("result", result)
    
    return {"error": "Multi-agent system required for this operation"}

@mcp.tool()
def delete_supply(supply_id: str) -> Dict[str, Any]:
    """Delete a supply item."""
    if MULTI_AGENT_AVAILABLE and orchestrator:
        result = orchestrator.route_request("delete_supply", supply_id=supply_id)
        return result.get("result", result)
    
    return {"error": "Multi-agent system required for this operation"}

@mcp.tool()
def get_low_stock_supplies() -> Dict[str, Any]:
    """Get all supplies that are below minimum stock level."""
    if MULTI_AGENT_AVAILABLE and orchestrator:
        result = orchestrator.route_request("get_low_stock_supplies")
        return result.get("result", result)
    
    return {"error": "Multi-agent system required for this operation"}

@mcp.tool()
def list_inventory_transactions(supply_id: str = None, transaction_type: str = None,
                              start_date: str = None, end_date: str = None) -> Dict[str, Any]:
    """List inventory transactions with optional filtering."""
    if MULTI_AGENT_AVAILABLE and orchestrator:
        result = orchestrator.route_request("list_inventory_transactions",
                                           supply_id=supply_id, transaction_type=transaction_type,
                                           start_date=start_date, end_date=end_date)
        return result.get("result", result)
    
    return {"error": "Multi-agent system required for this operation"}

@mcp.tool()
def get_supply_usage_report(supply_id: str = None, start_date: str = None, 
                           end_date: str = None) -> Dict[str, Any]:
    """Get supply usage report with optional filtering."""
    if MULTI_AGENT_AVAILABLE and orchestrator:
        result = orchestrator.route_request("get_supply_usage_report",
                                           supply_id=supply_id, start_date=start_date, end_date=end_date)
        return result.get("result", result)
    
    return {"error": "Multi-agent system required for this operation"}

@mcp.tool()
def create_staff(employee_id: str, department_id: str, position: str, user_id: str = None,
                first_name: str = None, last_name: str = None, email: str = None, phone: str = None,
                specialization: str = None, hire_date: str = None, salary: float = None,
                status: str = "active") -> Dict[str, Any]:
    """Create a new staff record.

    Pass user_id to link an existing user, or first_name/last_name to create
    the user account along with the staff record.
    """
    if MULTI_AGENT_AVAILABLE and orchestrator:
        result = orchestrator.route_request("create_staff",
                                           user_id=user_id, employee_id=employee_id, department_id=department_id,
                                           position=position, first_name=first_name, last_name=last_name,
                                           email=email, phone=phone, specialization=specialization,
                                           hire_date=hire_date, salary=salary, status=status)
        return result.get("result", result)
    # Direct DB fallback
    if not DATABASE_AVAILABLE:
        return {"success": False, "message": "Database not available"}
    if not user_id:
        return {"success": False, "message": "user_id is required when the multi-agent system is unavailable"}
    try:
        db = get_db_session()
        staff = Staff(
            user_id=uuid.UUID(user_id),
            employee_id=employee_id,
            department_id=uuid.UUID(department_id),
            position=position,
            hire_date=datetime.strptime(hire_date, "%Y-%m-%d").date() if hire_date else date.today(),
            salary=Decimal(str(salary)) if salary else None,
            status=status
        )
        db.add(staff)
        db.commit()
        db.refresh(staff)
        result = serialize_model(staff)
        db.close()
        return {"success": True, "message": "Staff created successfully", "data": result}
    except Exception as e:
        return {"success": False, "message": f"Failed to create staff: {str(e)}"}

@mcp.tool()
def list_staff(department_id: str = None, status: str = None, position: str = None) -> Dict[str, Any]:
    """List staff with optional filtering."""
    if MULTI_AGENT_AVAILABLE and orchestrator:
        result = orchestrator.route_request("list_staff",
                                           department_id=department_id, status=status, position=position)
        return result.get("result", result)
    
    return {"error": "Multi-agent system required for this operation"}

@mcp.tool()
def get_staff_by_id(staff_id: str) -> Dict[str, Any]:
    """Get a staff member by ID."""
    if MULTI_AGENT_AVAILABLE and orchestrator:
        result = orchestrator.route_request("get_staff_by_id", staff_id=staff_id)
        return result.get("result", result)
    
    return {"error": "Multi-agent system required for this operation"}

@mcp.tool()
def update_staff(staff_id: str, employee_id: str = None, department_id: str = None,
                position: str = None, salary: float = None, status: str = None) -> Dict[str, Any]:
    """Update staff information (supports both UUID and employee_id)."""
    if MULTI_AGENT_AVAILABLE and orchestrator:
        result = orchestrator.route_request("update_staff",
                                           staff_id=staff_id, employee_id=employee_id,
                                           department_id=department_id, position=position,
                                           salary=salary, status=status)
        return result.get("result", result)
    
    return {"error": "Multi-agent system required for this operation"}

@mcp.tool()
def update_staff_status(staff_id: str, status: str, notes: str = None) -> Dict[str, Any]:
    """Update staff status (active, inactive, on_leave, terminated)."""
    if MULTI_AGENT_AVAILABLE and orchestrator:
        result = orchestrator.route_request("update_staff_status",
                                           staff_id=staff_id, status=status, notes=notes)
        return result.get("result", result)
    
    return {"error": "Multi-agent system required for this operation"}

# Continue with remaining tools...
# [The file would continue with all other tools following the same pattern]

# ================================
# MEDICAL DOCUMENT MANAGEMENT TOOLS  
# ================================

@mcp.tool()
def upload_medical_document(patient_id: str, file_content: str, file_name: str, 
                          document_type: str = "prescription", mime_type: str = None) -> Dict[str, Any]:
    """Upload a medical document for a patient."""
    if MULTI_AGENT_AVAILABLE and orchestrator:
        result = orchestrator.route_request("upload_medical_document",
                                           patient_id=patient_id, file_content=file_content,
                                           file_name=file_name, document_type=document_type, 
                                           mime_type=mime_type)
        return result.get("result", result)
    
    return {"error": "Multi-agent system required for this operation"}

@mcp.tool()
def process_medical_document(document_id: str) -> Dict[str, Any]:
    """Process uploaded medical document with OCR and AI extraction."""
    if MULTI_AGENT_AVAILABLE and orchestrator:
        result = orchestrator.route_request("process_medical_document", document_id=document_id)
        return result.get("result", result)
    
    return {"error": "Multi-agent system required for this operation"}

@mcp.tool()
def get_patient_medical_history(patient_id: str) -> Dict[str, Any]:
    """Get comprehensive medical history for a patient from uploaded documents."""
    if MULTI_AGENT_AVAILABLE and orchestrator:
        result = orchestrator.route_request("get_patient_medical_history", patient_id=patient_id)
        return result.get("result", result)
    
    return {"error": "Multi-agent system required for this operation"}

@mcp.tool()
def search_medical_documents(patient_id: str = None, document_type: str = None, 
                           date_from: str = None, date_to: str = None) -> Dict[str, Any]:
    """Search medical documents with filters."""
    if MULTI_AGENT_AVAILABLE and orchestrator:
        result = orchestrator.route_request("search_medical_documents",
                                           patient_id=patient_id, document_type=document_type,
                                           date_from=date_from, date_to=date_to)
        return result.get("result", result)
    
    return {"error": "Multi-agent system required for this operation"}

@mcp.tool()
def query_medical_knowledge(query: str, patient_id: str = None) -> Dict[str, Any]:
    """Query medical documents using RAG system for intelligent answers."""
    if MULTI_AGENT_AVAILABLE and orchestrator:
        result = orchestrator.route_request("query_medical_knowledge", 
                                           query=query, patient_id=patient_id)
        return result.get("result", result)
    
    return {"error": "Multi-agent system required for this operation"}

@mcp.tool()
def extract_medical_entities(text: str) -> Dict[str, Any]:
    """Extract medical entities from text using AI."""
    if MULTI_AGENT_AVAILABLE and orchestrator:
        result = orchestrator.route_request("extract_medical_entities", text=text)
        return result.get("result", result)
    
    return {"error": "Multi-agent system required for this operation"}

@mcp.tool()
def get_medical_timeline(patient_id: str) -> Dict[str, Any]:
    """Get chronological medical timeline for a patient."""
    if MULTI_AGENT_AVAILABLE and orchestrator:
        result = orchestrator.route_request("get_medical_timeline", patient_id=patient_id)
        return result.get("result", result)
    
    return {"error": "Multi-agent system required for this operation"}

# ================================
# MEETING SCHEDULING TOOLS
# ================================

@mcp.tool()
def schedule_meeting(query: str) -> Dict[str, Any]:
    """Schedule a meeting using natural language.
    
    Args:
        query: Natural language description of the meeting to schedule
               (e.g., "Schedule a patient consultation with Dr. Smith tomorrow at 2 PM")
    """
    if MULTI_AGENT_AVAILABLE and orchestrator:
        result = orchestrator.route_request("schedule_meeting", query=query)
        return result.get("result", result)
    
    return {"error": "Multi-agent system required for meeting scheduling"}

@mcp.tool()
def list_meetings(date_str: str = None, days_ahead: int = 7) -> Dict[str, Any]:
    """List meetings with optional date filter.
    
    Args:
        date_str: Specific date in YYYY-MM-DD format (optional)
        days_ahead: Number of days ahead to look for upcoming meetings (default 7)
    """
    if MULTI_AGENT_AVAILABLE and orchestrator:
        result = orchestrator.route_request("list_meetings",
                                           date_str=date_str,
                                           days_ahead=days_ahead)
        return result.get("result", result)
    
    return {"error": "Multi-agent system required for listing meetings"}

@mcp.tool()
def get_meeting_by_id(meeting_id: str) -> Dict[str, Any]:
    """Get detailed information about a specific meeting.
    
    Args:
        meeting_id: The ID of the meeting to retrieve
    """
    if MULTI_AGENT_AVAILABLE and orchestrator:
        result = orchestrator.route_request("get_meeting_by_id", meeting_id=meeting_id)
        return result.get("result", result)
    
    return {"error": "Multi-agent system required for meeting retrieval"}

@mcp.tool()
def update_meeting_status(meeting_id: str = None, status: str = None, query: str = None) -> Dict[str, Any]:
    """Update the status of a meeting.

    This wrapper accepts either structured (meeting_id + status) updates or a
    natural-language `query`. If the incoming parameters look like a natural
    language cancel/reschedule request (contain words like 'cancel',
    'reschedule', 'postpone', or include times/dates), we forward the raw
    query to the `update_meeting` tool so the richer updater (which handles
    rescheduling and cancellation flows) runs. Otherwise we call the
    structured `update_meeting_status` route on the orchestrator.

    Args:
        meeting_id: The ID of the meeting to update (optional when using `query`)
        status: New status (scheduled, in_progress, completed, cancelled)
        query: Optional natural language update command (e.g., "Cancel the 'X' meeting")
    """
    if not MULTI_AGENT_AVAILABLE or not orchestrator:
        return {"error": "Multi-agent system required for meeting updates"}

    # Prefer explicit natural language query when provided
    nl = (query or "").strip()
    if not nl:
        # If no explicit query, sometimes assistants pass the status as a free-text
        # natural language string (e.g., "Cancel the meeting titled X tomorrow at 5pm").
        nl = (status or "").strip()

    # Detect NL cancel/reschedule/update intent heuristically
    if nl and re.search(r"\b(cancel|cancelled|cancellation|call off|postpone|reschedul|move|shift|postponed|abort)\b", nl, re.IGNORECASE):
        # Build a reasonable query string including meeting id if provided
        composed_query = nl
        if meeting_id:
            composed_query = f"{nl} meeting id {meeting_id}"

        # Route to update_meeting which handles cancellations and reschedules
        result = orchestrator.route_request("update_meeting", query=composed_query)
        return result.get("result", result)

    # If here, treat as a structured status update
    try:
        result = orchestrator.route_request("update_meeting_status",
                                           meeting_id=meeting_id,
                                           status=status)
        return result.get("result", result)
    except Exception as e:
        return {"error": f"Failed to update meeting status: {e}"}

@mcp.tool()
def add_meeting_notes(meeting_id: str, notes: str, action_items: str = None) -> Dict[str, Any]:
    """Add notes to a meeting.
    
    Args:
        meeting_id: The ID of the meeting
        notes: The notes to add
        action_items: Optional action items from the meeting
    """
    if MULTI_AGENT_AVAILABLE and orchestrator:
        result = orchestrator.route_request("add_meeting_notes",
                                           meeting_id=meeting_id,
                                           notes=notes,
                                           action_items=action_items)
        return result.get("result", result)
    
    return {"error": "Multi-agent system required for adding meeting notes"}

@mcp.tool()
def send_email(to_emails: str, subject: str, message: str, from_name: str = "Hospital Management System") -> Dict[str, Any]:
    """Send email notifications to staff members.
    
    Args:
        to_emails: Comma-separated list of email addresses
        subject: Email subject line
        message: Email message content
        from_name: Sender name (default: Hospital Management System)
    """
    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        from dotenv import load_dotenv
        import os
        
        # Load email configuration
        load_dotenv()
        
        smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        smtp_port = int(os.getenv('SMTP_PORT', '587'))
        email_username = os.getenv('EMAIL_USERNAME')
        email_password = os.getenv('EMAIL_PASSWORD')
        from_email = os.getenv('EMAIL_FROM_ADDRESS', email_username)
        
        if not email_username or not email_password:
            return {"success": False, "message": "Email credentials not configured"}
        
        # Parse email addresses
        email_list = [email.strip() for email in to_emails.split(',')]
        
        # Create email message
        msg = MIMEMultipart()
        msg['From'] = f"{from_name} <{from_email}>"
        msg['Subject'] = subject
        msg.attach(MIMEText(message, 'plain'))
        
        # Send emails
        sent_count = 0
        failed_emails = []
        
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(email_username, email_password)
            
            for email_addr in email_list:
                try:
                    msg['To'] = email_addr
                    server.send_message(msg)
                    sent_count += 1
                except Exception as e:
                    failed_emails.append(f"{email_addr}: {str(e)}")
                finally:
                    del msg['To']  # Remove for next iteration
        
        return {
            "success": True,
            "message": f"Sent {sent_count}/{len(email_list)} emails successfully",
            "sent_count": sent_count,
            "total_emails": len(email_list),
            "failed_emails": failed_emails
        }
        
    except Exception as e:
        return {"success": False, "message": f"Email sending failed: {str(e)}"}

# ================================
# DISCHARGE REPORT TOOLS
# ================================

@mcp.tool()
def generate_discharge_report(
    bed_id: str,
    discharge_condition: str = "stable",
    discharge_destination: str = "home"
) -> Dict[str, Any]:
    """Generate a comprehensive patient discharge report.
    
    Args:
        bed_id: The bed ID where the patient is located
        discharge_condition: Condition of patient at discharge (default: stable)
        discharge_destination: Where patient is going (default: home)
    """
    if MULTI_AGENT_AVAILABLE and orchestrator:
        result = orchestrator.route_request("generate_discharge_report",
                                           bed_id=bed_id,
                                           discharge_condition=discharge_condition,
                                           discharge_destination=discharge_destination)
        return result.get("result", result)
    
    return {"error": "Multi-agent system required for discharge report generation"}

@mcp.tool()
def discharge_patient_complete(
    patient_id: str = None,
    bed_id: str = None,
    patient_name: str = None,
    patient_number: str = None,
    discharge_condition: str = "stable",
    discharge_destination: str = "home"
) -> Dict[str, Any]:
    """Complete comprehensive patient discharge workflow including bed turnover.
    
    Args:
        patient_id: The ID of the patient to discharge (optional if bed_id, patient_name, or patient_number provided)
        bed_id: The bed ID where the patient is located (optional if patient_id, patient_name, or patient_number provided)
        patient_name: The name of the patient to discharge (optional if patient_id, bed_id, or patient_number provided)
        patient_number: The patient number (e.g., P1025) to discharge (optional if patient_id, bed_id, or patient_name provided)
        discharge_condition: Condition of patient at discharge (default: stable)
        discharge_destination: Where patient is going (default: home)
    """
    if MULTI_AGENT_AVAILABLE and orchestrator:
        result = orchestrator.route_request("discharge_patient_complete",
                                           patient_id=patient_id,
                                           bed_id=bed_id,
                                           patient_name=patient_name,
                                           patient_number=patient_number,
                                           discharge_condition=discharge_condition,
                                           discharge_destination=discharge_destination)
        return result.get("result", result)
    
    return {"error": "Multi-agent system required for complete discharge workflow"}

@mcp.tool()
def get_dashboard_stats() -> Dict[str, Any]:
    """Get real-time hospital statistics for dashboard display."""
    if not DATABASE_AVAILABLE:
        return {"error": "Database not available"}
    
    try:
        db = SessionLocal()
        
        # Get patient statistics
        total_patients = db.query(Patient).filter(Patient.status != "discharged").count()
        total_all_patients = db.query(Patient).count()
        
        # Get admissions today
        from datetime import date
        today = date.today()
        admissions_today = db.query(Patient).filter(
            func.date(Patient.created_at) == today
        ).count()
        
        # Get discharges today (assuming we track this in patient status changes)
        discharged_today = db.query(Patient).filter(
            Patient.status == "discharged",
            func.date(Patient.updated_at) == today
        ).count()
        
        # Get bed statistics
        total_beds = db.query(Bed).count()
        occupied_beds = db.query(Bed).filter(Bed.status == "occupied").count()
        available_beds = db.query(Bed).filter(Bed.status == "available").count()
        cleaning_beds = db.query(Bed).filter(Bed.status == "cleaning").count()
        maintenance_beds = db.query(Bed).filter(Bed.status == "maintenance").count()
        
        # Get staff statistics
        total_staff = db.query(Staff).filter(Staff.status == "active").count()
        on_duty_staff = db.query(Staff).filter(
            Staff.status == "active",
            Staff.availability_status == "available"
        ).count()
        
        # Calculate trends (simplified - you can enhance this)
        patient_trend = f"+{admissions_today - discharged_today}" if admissions_today > discharged_today else f"{admissions_today - discharged_today}"
        bed_trend = f"-{occupied_beds - (total_beds - occupied_beds - cleaning_beds - maintenance_beds)}"
        
        db.close()
        
        return {
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "patients": {
                "total": total_patients,
                "total_all_time": total_all_patients,
                "admissions_today": admissions_today,
                "discharges_today": discharged_today,
                "trend": patient_trend
            },
            "beds": {
                "total": total_beds,
                "occupied": occupied_beds,
                "available": available_beds,
                "cleaning": cleaning_beds,
                "maintenance": maintenance_beds,
                "occupancy_rate": round((occupied_beds / total_beds * 100), 1) if total_beds > 0 else 0
            },
            "staff": {
                "total_active": total_staff,
                "on_duty": on_duty_staff,
                "off_duty": total_staff - on_duty_staff
            }
        }
        
    except Exception as e:
        return {"success": False, "error": f"Failed to get dashboard stats: {str(e)}"}

@mcp.tool()
def get_live_bed_occupancy() -> Dict[str, Any]:
    """Get real-time bed occupancy by department for dashboard charts."""
    if not DATABASE_AVAILABLE:
        return {"error": "Database not available"}
    
    try:
        db = SessionLocal()
        
        # Get bed occupancy by department
        from sqlalchemy import func
        
        bed_occupancy = db.query(
            Department.name.label('department_name'),
            func.count(Bed.id).label('total_beds'),
            func.sum(func.case([(Bed.status == 'occupied', 1)], else_=0)).label('occupied_beds'),
            func.sum(func.case([(Bed.status == 'available', 1)], else_=0)).label('available_beds'),
            func.sum(func.case([(Bed.status == 'cleaning', 1)], else_=0)).label('cleaning_beds'),
            func.sum(func.case([(Bed.status == 'maintenance', 1)], else_=0)).label('maintenance_beds')
        ).join(Room, Department.id == Room.department_id)\
         .join(Bed, Room.id == Bed.room_id)\
         .group_by(Department.name)\
         .all()
        
        departments = []
        for dept in bed_occupancy:
            total = int(dept.total_beds) if dept.total_beds else 0
            occupied = int(dept.occupied_beds) if dept.occupied_beds else 0
            available = int(dept.available_beds) if dept.available_beds else 0
            cleaning = int(dept.cleaning_beds) if dept.cleaning_beds else 0
            maintenance = int(dept.maintenance_beds) if dept.maintenance_beds else 0
            
            occupancy_rate = round((occupied / total * 100), 1) if total > 0 else 0
            
            departments.append({
                "name": dept.department_name,
                "total_beds": total,
                "occupied": occupied,
                "available": available,
                "cleaning": cleaning,
                "maintenance": maintenance,
                "occupancy_rate": occupancy_rate,
                "status_color": "red" if occupancy_rate > 90 else "orange" if occupancy_rate > 75 else "green"
            })
        
        db.close()
        
        return {
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "departments": departments
        }
        
    except Exception as e:
        return {"success": False, "error": f"Failed to get bed occupancy data: {str(e)}"}

@mcp.tool()
def get_patient_flow_data(hours: int = 24) -> Dict[str, Any]:
    """Get patient admission and discharge flow data for the specified time period."""
    if not DATABASE_AVAILABLE:
        return {"error": "Database not available"}
    
    try:
        db = SessionLocal()
        
        from datetime import datetime, timedelta
        
        # Calculate time range
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        
        # Get hourly admissions
        admissions = db.query(
            func.date_trunc('hour', Patient.created_at).label('hour'),
            func.count(Patient.id).label('count')
        ).filter(
            Patient.created_at >= start_time,
            Patient.created_at <= end_time
        ).group_by(func.date_trunc('hour', Patient.created_at)).all()
        
        # Get hourly discharges (patients with status changed to discharged)
        discharges = db.query(
            func.date_trunc('hour', Patient.updated_at).label('hour'),
            func.count(Patient.id).label('count')
        ).filter(
            Patient.status == "discharged",
            Patient.updated_at >= start_time,
            Patient.updated_at <= end_time
        ).group_by(func.date_trunc('hour', Patient.updated_at)).all()
        
        # Format data for charts
        admission_data = [{"time": admission.hour.isoformat(), "admissions": admission.count} for admission in admissions]
        discharge_data = [{"time": discharge.hour.isoformat(), "discharges": discharge.count} for discharge in discharges]
        
        db.close()
        
        return {
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "time_range_hours": hours,
            "admissions": admission_data,
            "discharges": discharge_data
        }
        
    except Exception as e:
        return {"success": False, "error": f"Failed to get patient flow data: {str(e)}"}

@mcp.tool()
def get_emergency_alerts() -> Dict[str, Any]:
    """Get active emergency alerts and critical notifications for dashboard."""
    if not DATABASE_AVAILABLE:
        return {"error": "Database not available"}
    
    try:
        db = SessionLocal()
        alerts = []
        
        # Critical bed shortages (less than 10% available)
        total_beds = db.query(Bed).count()
        available_beds = db.query(Bed).filter(Bed.status == "available").count()
        if total_beds > 0:
            availability_rate = (available_beds / total_beds) * 100
            if availability_rate < 10:
                alerts.append({
                    "id": "bed_shortage",
                    "type": "critical",
                    "priority": "high",
                    "message": f"Critical bed shortage: Only {available_beds} beds available ({availability_rate:.1f}%)",
                    "timestamp": datetime.now().isoformat(),
                    "icon": "🔴",
                    "action_required": True
                })
        
        # Equipment maintenance alerts
        maintenance_equipment = db.query(Equipment).filter(Equipment.status == "maintenance").count()
        if maintenance_equipment > 0:
            alerts.append({
                "id": "equipment_maintenance",
                "type": "warning",
                "priority": "medium",
                "message": f"{maintenance_equipment} equipment items under maintenance",
                "timestamp": datetime.now().isoformat(),
                "icon": "🟡",
                "action_required": False
            })
        
        # Low supply alerts (assuming we have supply quantity tracking)
        try:
            low_supplies = db.query(Supply).filter(Supply.current_stock < Supply.minimum_threshold).count()
            if low_supplies > 0:
                alerts.append({
                    "id": "low_supplies",
                    "type": "warning", 
                    "priority": "medium",
                    "message": f"{low_supplies} supplies running low",
                    "timestamp": datetime.now().isoformat(),
                    "icon": "🟠",
                    "action_required": True
                })
        except:
            # Handle case where supply tracking fields don't exist yet
            pass
        
        # High occupancy warnings
        occupied_beds = db.query(Bed).filter(Bed.status == "occupied").count()
        if total_beds > 0:
            occupancy_rate = (occupied_beds / total_beds) * 100
            if occupancy_rate > 90:
                alerts.append({
                    "id": "high_occupancy",
                    "type": "warning",
                    "priority": "medium", 
                    "message": f"High bed occupancy: {occupancy_rate:.1f}% ({occupied_beds}/{total_beds})",
                    "timestamp": datetime.now().isoformat(),
                    "icon": "🟡",
                    "action_required": False
                })
        
        db.close()
        
        return {
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "alerts": alerts,
            "total_alerts": len(alerts),
            "critical_count": len([a for a in alerts if a["type"] == "critical"]),
            "warning_count": len([a for a in alerts if a["type"] == "warning"])
        }
        
    except Exception as e:
        return {"success": False, "error": f"Failed to get emergency alerts: {str(e)}"}

@mcp.tool()
def get_recent_activity(limit: int = 10) -> Dict[str, Any]:
    """Get recent hospital activity for dashboard activity feed."""
    if not DATABASE_AVAILABLE:
        return {"error": "Database not available"}
    
    try:
        db = SessionLocal()
        activities = []
        
        # Recent patient admissions
        recent_patients = db.query(Patient).order_by(Patient.created_at.desc()).limit(5).all()
        for patient in recent_patients:
            activities.append({
                "id": f"patient_{patient.id}",
                "type": "admission",
                "message": f"Patient {patient.first_name} {patient.last_name} admitted",
                "timestamp": patient.created_at.isoformat(),
                "icon": "👥"
            })
        
        # Recent bed status changes (you may need to add a bed_status_history table for this)
        # For now, we'll show cleaning beds as recent activity
        cleaning_beds = db.query(Bed).filter(Bed.status == "cleaning").limit(3).all()
        for bed in cleaning_beds:
            activities.append({
                "id": f"bed_{bed.id}",
                "type": "bed_cleaning",
                "message": f"Bed {bed.bed_number} cleaning started",
                "timestamp": (datetime.now() - timedelta(minutes=random.randint(5, 30))).isoformat(),
                "icon": "🛏️"
            })
        
        # Recent agent interactions (if available)
        try:
            recent_interactions = db.query(AgentInteraction).order_by(AgentInteraction.interaction_time.desc()).limit(3).all()
            for interaction in recent_interactions:
                activities.append({
                    "id": f"agent_{interaction.id}",
                    "type": "system_activity",
                    "message": f"{interaction.agent_type}: {interaction.action_taken[:50]}...",
                    "timestamp": interaction.interaction_time.isoformat(),
                    "icon": "🤖"
                })
        except:
            pass
        
        # Sort activities by timestamp and limit
        activities.sort(key=lambda x: x["timestamp"], reverse=True)
        activities = activities[:limit]
        
        db.close()
        
        return {
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "activities": activities,
            "total_count": len(activities)
        }
        
    except Exception as e:
        return {"success": False, "error": f"Failed to get recent activity: {str(e)}"}

@mcp.tool()
def get_patient_discharge_status(
    patient_id: str = None,
    patient_name: str = None
) -> Dict[str, Any]:
    """Get patient discharge status and related information.
    
    Args:
        patient_id: The ID of the patient (optional if patient_name provided)
        patient_name: The name of the patient (optional if patient_id provided)
    """
    if MULTI_AGENT_AVAILABLE and orchestrator:
        result = orchestrator.route_request("get_patient_discharge_status",
                                           patient_id=patient_id,
                                           patient_name=patient_name)
        return result.get("result", result)
    
    return {"error": "Multi-agent system required for discharge status"}

@mcp.tool()
def add_treatment_record_simple(
    patient_id: str,
    doctor_id: str,
    treatment_type: str,
    treatment_name: str
) -> Dict[str, Any]:
    """Add a simple treatment record for discharge reporting.
    
    Args:
        patient_id: The ID of the patient
        doctor_id: The ID of the doctor who provided treatment
        treatment_type: Type of treatment
        treatment_name: Name of the treatment
    """
    if MULTI_AGENT_AVAILABLE and orchestrator:
        result = orchestrator.route_request("add_treatment_record_simple",
                                           patient_id=patient_id,
                                           doctor_id=doctor_id,
                                           treatment_type=treatment_type,
                                           treatment_name=treatment_name)
        return result.get("result", result)
    
    return {"error": "Multi-agent system required for adding treatment records"}

@mcp.tool()
def add_equipment_usage_with_codes(
    patient_id: str = None,
    equipment_id: str = None,
    staff_id: str = None,
    used_by: str = None,  # Alternative name for staff_id
    purpose: str = None,
    purpose_of_use: str = None,  # Alternative parameter name for frontend compatibility
    start_time: str = None,
    start_date_time: str = None,  # Alternative name for start_time
    end_time: str = None,
    end_date_time: str = None,  # Alternative name for end_time
    notes: str = None
) -> Dict[str, Any]:
    """Add equipment usage with automatic code-to-UUID conversion (RECOMMENDED FOR CODES).
    
    This tool intelligently converts user-friendly codes like P002, EQ001, EMP001 to internal UUIDs
    before recording equipment usage. Use this when you have patient numbers, equipment codes, and employee IDs.
    
    Args:
        patient_id: Patient identifier (e.g., 'P002', 'P123456', or internal UUID)
        equipment_id: Equipment identifier (e.g., 'EQ001', 'EQ123', or internal UUID) 
        staff_id: Staff identifier (e.g., 'EMP001', 'EMP123', or internal UUID)
        purpose: Purpose of equipment usage (e.g., 'ECG monitoring during cardiac evaluation')
        start_time: Start time (ISO string like '2025-08-25 09:15', optional)
        end_time: End time (ISO string like '2025-08-25 10:00', optional)
        notes: Additional notes (optional)
    
    Examples:
        patient_id: P002, EQ001, EMP001 (user-friendly codes) - PREFERRED
        patient_id: 123e4567-e89b-12d3-a456-426614174000 (internal UUIDs)
    """
    if not MULTI_AGENT_AVAILABLE or not orchestrator:
        return {"success": False, "message": "Multi-agent system required for equipment usage"}
    
    # Validate required parameters
    if not patient_id:
        return {"success": False, "message": "patient_id is required (e.g., 'P002', 'P001', or UUID)"}
    if not equipment_id:
        return {"success": False, "message": "equipment_id is required (e.g., 'EQ001', 'EQ002', or UUID)"}
    
    # Handle alternative staff_id parameter names
    actual_staff_id = staff_id or used_by
    if not actual_staff_id:
        return {"success": False, "message": "staff_id or used_by is required (e.g., 'EMP001', 'EMP002', or UUID)"}
    
    # Handle both 'purpose' and 'purpose_of_use' parameter names for frontend compatibility
    actual_purpose = purpose or purpose_of_use
    if not actual_purpose:
        return {"success": False, "message": "Purpose is required (use 'purpose' or 'purpose_of_use' parameter)"}
    
    # Handle alternative time parameter names
    actual_start_time = start_time or start_date_time
    actual_end_time = end_time or end_date_time
    
    # Check if inputs are user-friendly codes (short strings without hyphens)
    is_patient_code = patient_id and len(patient_id) < 20 and '-' not in patient_id
    is_equipment_code = equipment_id and len(equipment_id) < 20 and '-' not in equipment_id  
    is_staff_code = actual_staff_id and len(actual_staff_id) < 20 and '-' not in actual_staff_id
    
    if is_patient_code or is_equipment_code or is_staff_code:
        # Perform code-to-UUID conversion locally
        try:
            resolved_patient_id = patient_id
            resolved_equipment_id = equipment_id
            resolved_staff_id = actual_staff_id
            
            # Resolve patient code to UUID
            if is_patient_code:
                patient_lookup = orchestrator.route_request("search_patients", patient_number=patient_id)
                patient_result = patient_lookup.get("result", {})
                if patient_result.get("data"):
                    resolved_patient_id = patient_result["data"][0]["id"]
                else:
                    return {"success": False, "message": f"Patient '{patient_id}' not found in database"}
            
            # Resolve equipment code to UUID
            if is_equipment_code:
                equipment_lookup = orchestrator.route_request("list_equipment")
                equipment_result = equipment_lookup.get("result", {})
                resolved_equipment_id = None
                if equipment_result.get("data"):
                    for eq in equipment_result["data"]:
                        if eq.get("equipment_id") == equipment_id:
                            resolved_equipment_id = eq["id"]
                            break
                if not resolved_equipment_id:
                    return {"success": False, "message": f"Equipment '{equipment_id}' not found in database"}
            
            # Resolve staff code to UUID  
            if is_staff_code:
                staff_lookup = orchestrator.route_request("list_staff")
                staff_result = staff_lookup.get("result", {})
                resolved_staff_id = None
                if staff_result.get("data"):
                    for staff in staff_result["data"]:
                        if staff.get("employee_id") == actual_staff_id:
                            resolved_staff_id = staff["id"]
                            break
                if not resolved_staff_id:
                    return {"success": False, "message": f"Staff member '{actual_staff_id}' not found in database"}
            
            # Success: call with resolved UUIDs - use a different tool name to avoid routing conflicts
            result = orchestrator.route_request("add_equipment_usage_simple",
                                               patient_id=resolved_patient_id,
                                               equipment_id=resolved_equipment_id,
                                               staff_id=resolved_staff_id,
                                               purpose=actual_purpose,
                                               start_time=actual_start_time,
                                               end_time=actual_end_time,
                                               notes=notes)
            
            # Add success metadata showing what was resolved
            response = result.get("result", result)
            if isinstance(response, dict) and response.get("success"):
                response["codes_resolved"] = {
                    "original_patient": patient_id,
                    "original_equipment": equipment_id,
                    "original_staff": actual_staff_id,
                    "resolved_patient": resolved_patient_id,
                    "resolved_equipment": resolved_equipment_id,
                    "resolved_staff": resolved_staff_id
                }
                response["message"] = "Equipment usage recorded successfully with automatic code resolution"
            return response
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Code resolution failed: {str(e)}",
                "codes_provided": {
                    "patient": patient_id,
                    "equipment": equipment_id,
                    "staff": staff_id
                },
                "suggestion": "Verify that all codes exist in the database"
            }
    else:
        # Use UUIDs directly
        result = orchestrator.route_request("add_equipment_usage_simple",
                                           patient_id=patient_id,
                                           equipment_id=equipment_id,
                                           staff_id=staff_id,
                                           purpose=purpose,
                                           start_time=start_time,
                                           end_time=end_time,
                                           notes=notes)
        return result.get("result", result)


@mcp.tool()
def add_equipment_usage_simple(
    patient_id: str,
    equipment_id: str,
    staff_id: str,
    purpose: str,
    start_time: str = None,
    end_time: str = None,
    notes: str = None
) -> Dict[str, Any]:
    """Add equipment usage using patient codes, equipment codes, and staff codes (PREFERRED METHOD).
    
    This tool intelligently handles both internal UUIDs and user-friendly codes like P002, EQ001, EMP001.
    Use this tool for all equipment usage operations.
    
    Args:
        patient_id: Patient identifier (e.g., 'P002', 'P123456', or internal UUID)
        equipment_id: Equipment identifier (e.g., 'EQ001', 'EQ123', or internal UUID) 
        staff_id: Staff identifier (e.g., 'EMP001', 'EMP123', or internal UUID)
        purpose: Purpose of equipment usage (e.g., 'ECG monitoring during cardiac evaluation')
        start_time: Start time (ISO string like '2025-08-25 09:15', optional)
        end_time: End time (ISO string like '2025-08-25 10:00', optional)
        notes: Additional notes (optional)
    
    Examples:
        patient_id: P002, EQ001, EMP001 (user-friendly codes)
        patient_id: 123e4567-e89b-12d3-a456-426614174000 (internal UUIDs)
    """
    if not MULTI_AGENT_AVAILABLE or not orchestrator:
        return {"success": False, "message": "Multi-agent system required for equipment usage"}
    
    # Check if inputs are user-friendly codes (short strings)
    is_patient_code = patient_id and len(patient_id) < 20 and not '-' in patient_id
    is_equipment_code = equipment_id and len(equipment_id) < 20 and not '-' in equipment_id  
    is_staff_code = staff_id and len(staff_id) < 20 and not '-' in staff_id
    
    if is_patient_code or is_equipment_code or is_staff_code:
        # Perform code-to-UUID conversion locally
        try:
            resolved_patient_id = patient_id
            resolved_equipment_id = equipment_id
            resolved_staff_id = staff_id
            
            # Resolve patient code to UUID
            if is_patient_code:
                patient_lookup = orchestrator.route_request("search_patients", patient_number=patient_id)
                patient_result = patient_lookup.get("result", {})
                if patient_result.get("data"):
                    resolved_patient_id = patient_result["data"][0]["id"]
                else:
                    return {"success": False, "message": f"Patient '{patient_id}' not found in database"}
            
            # Resolve equipment code to UUID
            if is_equipment_code:
                equipment_lookup = orchestrator.route_request("list_equipment")
                equipment_result = equipment_lookup.get("result", {})
                resolved_equipment_id = None
                if equipment_result.get("data"):
                    for eq in equipment_result["data"]:
                        if eq.get("equipment_id") == equipment_id:
                            resolved_equipment_id = eq["id"]
                            break
                if not resolved_equipment_id:
                    return {"success": False, "message": f"Equipment '{equipment_id}' not found in database"}
            
            # Resolve staff code to UUID  
            if is_staff_code:
                staff_lookup = orchestrator.route_request("list_staff")
                staff_result = staff_lookup.get("result", {})
                resolved_staff_id = None
                if staff_result.get("data"):
                    for staff in staff_result["data"]:
                        if staff.get("employee_id") == staff_id:
                            resolved_staff_id = staff["id"]
                            break
                if not resolved_staff_id:
                    return {"success": False, "message": f"Staff member '{staff_id}' not found in database"}
            
            # Success: call with resolved UUIDs
            result = orchestrator.route_request("add_equipment_usage_simple",
                                               patient_id=resolved_patient_id,
                                               equipment_id=resolved_equipment_id,
                                               staff_id=resolved_staff_id,
                                               purpose=purpose,
                                               start_time=start_time,
                                               end_time=end_time,
                                               notes=notes)
            
            # Add success metadata
            response = result.get("result", result)
            if isinstance(response, dict) and response.get("success"):
                response["codes_resolved"] = {
                    "original_patient": patient_id,
                    "original_equipment": equipment_id,
                    "original_staff": staff_id,
                    "resolved_patient": resolved_patient_id,
                    "resolved_equipment": resolved_equipment_id,
                    "resolved_staff": resolved_staff_id
                }
            return response
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Code resolution failed: {str(e)}",
                "codes_provided": {
                    "patient": patient_id,
                    "equipment": equipment_id,
                    "staff": staff_id
                },
                "suggestion": "Verify that all codes exist in the database"
            }
    else:
        # Use UUIDs directly
        result = orchestrator.route_request("add_equipment_usage_simple",
                                           patient_id=patient_id,
                                           equipment_id=equipment_id,
                                           staff_id=staff_id,
                                           purpose=purpose,
                                           start_time=start_time,
                                           end_time=end_time,
                                           notes=notes)
        return result.get("result", result)
    
    return {"error": "Multi-agent system required for adding equipment usage records"}

@mcp.tool()
def add_equipment_usage_by_codes(
    patient_number: str,
    equipment_id: str,
    employee_id: str,
    purpose: str,
    start_time: str = None,
    end_time: str = None,
    notes: str = None
) -> Dict[str, Any]:
    """Add equipment usage using human-readable codes (PREFERRED METHOD).
    
    Use this tool when you have patient numbers, equipment codes, and employee IDs.
    This is the recommended way to add equipment usage records.
    
    Args:
        patient_number: The patient number (e.g., 'P002', 'P123456')
        equipment_id: The equipment code (e.g., 'EQ001', 'EQ123')
        employee_id: The staff employee code (e.g., 'EMP001', 'EMP123')
        purpose: Purpose of equipment usage (e.g., 'ECG monitoring during cardiac evaluation')
        start_time: Start time (ISO string like '2025-08-25 09:15', optional)
        end_time: End time (ISO string like '2025-08-25 10:00', optional)
        notes: Additional notes (optional)
    
    Example:
        patient_number: P002
        equipment_id: EQ001
        employee_id: EMP001
        purpose: ECG monitoring during cardiac evaluation
        start_time: 2025-08-25 09:15
        end_time: 2025-08-25 10:00
    """
    if MULTI_AGENT_AVAILABLE and orchestrator:
        result = orchestrator.route_request("add_equipment_usage_by_codes",
                                           patient_number=patient_number,
                                           equipment_id=equipment_id,
                                           employee_id=employee_id,
                                           purpose=purpose,
                                           start_time=start_time,
                                           end_time=end_time,
                                           notes=notes)
        return result.get("result", result)
    return {"error": "Multi-agent system required for adding equipment usage records by codes"}

@mcp.tool()
def assign_staff_to_patient_simple(
    patient_id: str,
    staff_id: str,
    role: str
) -> Dict[str, Any]:
    """Assign staff to patient for discharge reporting.
    
    Args:
        patient_id: The ID of the patient
        staff_id: The ID of the staff member
        role: Role of staff member in patient care
    """
    if MULTI_AGENT_AVAILABLE and orchestrator:
        result = orchestrator.route_request("assign_staff_to_patient_simple",
                                           patient_id=patient_id,
                                           staff_id=staff_id,
                                           role=role)
        return result.get("result", result)
    
    return {"error": "Multi-agent system required for staff assignment"}

@mcp.tool()
def complete_equipment_usage_simple(usage_id: str) -> Dict[str, Any]:
    """Complete equipment usage record.
    
    Args:
        usage_id: The ID of the equipment usage record to complete
    """
    if MULTI_AGENT_AVAILABLE and orchestrator:
        result = orchestrator.route_request("complete_equipment_usage_simple", usage_id=usage_id)
        return result.get("result", result)
    
    return {"error": "Multi-agent system required for completing equipment usage"}

@mcp.tool()
def list_discharge_reports(patient_id: str = None) -> Dict[str, Any]:
    """List discharge reports.
    
    Args:
        patient_id: Filter by patient ID (optional)
    """
    if MULTI_AGENT_AVAILABLE and orchestrator:
        result = orchestrator.route_request("list_discharge_reports", patient_id=patient_id)
        return result.get("result", result)
    
    return {"error": "Multi-agent system required for listing discharge reports"}

@mcp.tool()
def start_bed_turnover_process(bed_id: str, previous_patient_id: str = None, 
                              turnover_type: str = "standard", priority_level: str = "normal") -> Dict[str, Any]:
    """Start bed turnover process.
    
    Args:
        bed_id: The ID of the bed to turnover
        previous_patient_id: ID of the previous patient (optional)
        turnover_type: Type of turnover (standard, deep_clean, maintenance)
        priority_level: Priority level (low, normal, high, urgent)
    """
    if MULTI_AGENT_AVAILABLE and orchestrator:
        result = orchestrator.route_request("start_bed_turnover_process",
                                           bed_id=bed_id, previous_patient_id=previous_patient_id,
                                           turnover_type=turnover_type, priority_level=priority_level)
        return result.get("result", result)
    
    return {"error": "Multi-agent system required for bed turnover"}

@mcp.tool()
def complete_bed_cleaning(bed_id: str, cleaned_by: str = None, cleaning_notes: str = None) -> Dict[str, Any]:
    """Complete bed cleaning task.
    
    Args:
        bed_id: The ID of the bed that was cleaned
        cleaned_by: Staff member who performed cleaning (optional)
        cleaning_notes: Notes about the cleaning process (optional)
    """
    if MULTI_AGENT_AVAILABLE and orchestrator:
        result = orchestrator.route_request("complete_bed_cleaning",
                                           bed_id=bed_id, cleaned_by=cleaned_by, 
                                           cleaning_notes=cleaning_notes)
        return result.get("result", result)
    
    return {"error": "Multi-agent system required for bed cleaning"}

@mcp.tool()
def get_bed_status_with_time_remaining(bed_id: str) -> Dict[str, Any]:
    """Get bed status with time remaining for current process (supports bed UUID or bed number).
    
    Args:
        bed_id: The ID of the bed to check (can be bed UUID like 'bed123' or bed number like '401A')
    """
    if MULTI_AGENT_AVAILABLE and orchestrator:
        result = orchestrator.route_request("get_bed_status_with_time_remaining", bed_id=bed_id)
        return result.get("result", result)
    
    return {"error": "Multi-agent system required for bed status"}

@mcp.tool()
def add_patient_to_queue(patient_id: str, queue_type: str, priority: str = "normal") -> Dict[str, Any]:
    """Add patient to queue.
    
    Args:
        patient_id: The ID of the patient
        queue_type: Type of queue (admission, discharge, surgery, etc.)
        priority: Priority level (low, normal, high, urgent)
    """
    if MULTI_AGENT_AVAILABLE and orchestrator:
        result = orchestrator.route_request("add_patient_to_queue",
                                           patient_id=patient_id, queue_type=queue_type, priority=priority)
        return result.get("result", result)
    
    return {"error": "Multi-agent system required for patient queue"}

@mcp.tool()
def get_patient_queue(queue_type: str = None) -> Dict[str, Any]:
    """Get patient queue.
    
    Args:
        queue_type: Filter by queue type (optional)
    """
    if MULTI_AGENT_AVAILABLE and orchestrator:
        result = orchestrator.route_request("get_patient_queue", queue_type=queue_type)
        return result.get("result", result)
    
    return {"error": "Multi-agent system required for patient queue"}

@mcp.tool()
def assign_next_patient_to_bed(bed_id: str, queue_type: str = "admission") -> Dict[str, Any]:
    """Assign next patient in queue to bed.
    
    Args:
        bed_id: The ID of the bed to assign
        queue_type: Type of queue to pull from
    """
    if MULTI_AGENT_AVAILABLE and orchestrator:
        result = orchestrator.route_request("assign_next_patient_to_bed",
                                           bed_id=bed_id, queue_type=queue_type)
        return result.get("result", result)
    
    return {"error": "Multi-agent system required for bed assignment"}

@mcp.tool()
def update_turnover_progress(bed_id: str, progress_step: str, notes: str = None) -> Dict[str, Any]:
    """Update bed turnover progress.
    
    Args:
        bed_id: The ID of the bed
        progress_step: Current progress step
        notes: Progress notes (optional)
    """
    if MULTI_AGENT_AVAILABLE and orchestrator:
        result = orchestrator.route_request("update_turnover_progress",
                                           bed_id=bed_id, progress_step=progress_step, notes=notes)
        return result.get("result", result)
    
    return {"error": "Multi-agent system required for turnover progress"}

@mcp.tool()
def get_bed_turnover_details(bed_id: str) -> Dict[str, Any]:
    """Get bed turnover details.
    
    Args:
        bed_id: The ID of the bed
    """
    if MULTI_AGENT_AVAILABLE and orchestrator:
        result = orchestrator.route_request("get_bed_turnover_details", bed_id=bed_id)
        return result.get("result", result)
    
    return {"error": "Multi-agent system required for turnover details"}

@mcp.tool()
def mark_equipment_for_cleaning(equipment_id: str, cleaning_type: str = "routine", priority: str = "normal") -> Dict[str, Any]:
    """Mark equipment for cleaning.
    
    Args:
        equipment_id: The ID of the equipment
        cleaning_type: Type of cleaning (routine, deep, maintenance)
        priority: Priority level (low, normal, high, urgent)
    """
    if MULTI_AGENT_AVAILABLE and orchestrator:
        result = orchestrator.route_request("mark_equipment_for_cleaning",
                                           equipment_id=equipment_id, cleaning_type=cleaning_type, priority=priority)
        return result.get("result", result)
    
    return {"error": "Multi-agent system required for equipment cleaning"}

@mcp.tool()
def complete_equipment_cleaning(equipment_id: str, cleaned_by: str = None, cleaning_notes: str = None) -> Dict[str, Any]:
    """Complete equipment cleaning.
    
    Args:
        equipment_id: The ID of the equipment
        cleaned_by: Staff member who cleaned the equipment (optional)
        cleaning_notes: Notes about the cleaning (optional)
    """
    if MULTI_AGENT_AVAILABLE and orchestrator:
        result = orchestrator.route_request("complete_equipment_cleaning",
                                           equipment_id=equipment_id, cleaned_by=cleaned_by, 
                                           cleaning_notes=cleaning_notes)
        return result.get("result", result)
    
    return {"error": "Multi-agent system required for equipment cleaning"}

@mcp.tool()
def get_equipment_turnover_status(equipment_id: str) -> Dict[str, Any]:
    """Get equipment turnover status.
    
    Args:
        equipment_id: The ID of the equipment
    """
    if MULTI_AGENT_AVAILABLE and orchestrator:
        result = orchestrator.route_request("get_equipment_turnover_status", equipment_id=equipment_id)
        return result.get("result", result)
    
    return {"error": "Multi-agent system required for equipment status"}

@mcp.tool()
def search_discharged_patients(patient_name: str = None, patient_number: str = None, 
                             discharge_date_from: str = None, discharge_date_to: str = None) -> Dict[str, Any]:
    """Search for discharged patients and get their discharge details.
    
    Args:
        patient_name: Partial name match (optional)
        patient_number: Exact patient number match (optional)
        discharge_date_from: Start date filter YYYY-MM-DD (optional)
        discharge_date_to: End date filter YYYY-MM-DD (optional)
    """
    if not DATABASE_AVAILABLE:
        return {"success": False, "message": "Database not available"}
    
    db = get_db_session()
    try:
        query = db.query(Patient).filter(Patient.status == "discharged")
        
        if patient_name:
            query = query.filter(
                (Patient.first_name.ilike(f"%{patient_name}%")) |
                (Patient.last_name.ilike(f"%{patient_name}%"))
            )
        
        if patient_number:
            query = query.filter(Patient.patient_number == patient_number)
        
        if discharge_date_from:
            try:
                from_date = datetime.fromisoformat(discharge_date_from)
                query = query.filter(Patient.updated_at >= from_date)
            except:
                pass
        
        if discharge_date_to:
            try:
                to_date = datetime.fromisoformat(discharge_date_to)
                query = query.filter(Patient.updated_at <= to_date)
            except:
                pass
        
        patients = query.order_by(Patient.updated_at.desc()).limit(50).all()
        
        result_data = []
        for patient in patients:
            # Get discharge reports for this patient
            discharge_reports = db.query(DischargeReport).filter(
                DischargeReport.patient_id == patient.id
            ).order_by(DischargeReport.created_at.desc()).all()
            
            patient_data = {
                "patient_id": str(patient.id),
                "patient_number": patient.patient_number,
                "name": f"{patient.first_name} {patient.last_name}",
                "status": patient.status,
                "discharge_date": patient.updated_at.isoformat() if patient.updated_at else None,
                "phone": patient.phone,
                "emergency_contact": patient.emergency_contact_name,
                "discharge_reports": [
                    {
                        "report_id": str(report.id),
                        "report_number": report.report_number,
                        "discharge_date": report.discharge_date.isoformat() if report.discharge_date else None,
                        "discharge_condition": report.discharge_condition,
                        "discharge_destination": report.discharge_destination,
                        "length_of_stay_days": report.length_of_stay_days,
                        "download_url": f"/discharge/{report.report_number}.pdf"
                    } for report in discharge_reports
                ]
            }
            result_data.append(patient_data)
        
        db.close()
        return {
            "success": True,
            "patients": result_data,
            "total_found": len(result_data),
            "message": f"Found {len(result_data)} discharged patients"
        }
        
    except Exception as e:
        db.close()
        return {"success": False, "message": f"Error searching discharged patients: {str(e)}"}

@mcp.tool()
def get_patient_with_discharge_details(patient_identifier: str) -> Dict[str, Any]:
    """Get complete patient information including discharge details by name, patient number, or ID.
    
    Args:
        patient_identifier: Patient name, patient number, or UUID
    """
    if not DATABASE_AVAILABLE:
        return {"success": False, "message": "Database not available"}
    
    db = get_db_session()
    try:
        patient = None
        
        # Try to find patient by UUID first
        try:
            patient = db.query(Patient).filter(Patient.id == uuid.UUID(patient_identifier)).first()
        except:
            pass
        
        # Try by patient number
        if not patient:
            patient = db.query(Patient).filter(Patient.patient_number == patient_identifier).first()
        
        # Try by name (partial match)
        if not patient:
            patient = db.query(Patient).filter(
                (Patient.first_name.ilike(f"%{patient_identifier}%")) |
                (Patient.last_name.ilike(f"%{patient_identifier}%"))
            ).first()
        
        if not patient:
            db.close()
            return {"success": False, "message": f"Patient not found: {patient_identifier}"}
        
        # Get discharge reports
        discharge_reports = db.query(DischargeReport).filter(
            DischargeReport.patient_id == patient.id
        ).order_by(DischargeReport.created_at.desc()).all()
        
        # Get current or last bed assignment
        bed_assignment = db.query(Bed).filter(
            (Bed.patient_id == patient.id) | 
            (Bed.discharge_date.isnot(None))
        ).order_by(Bed.updated_at.desc()).first()
        
        result = {
            "success": True,
            "patient": {
                "id": str(patient.id),
                "patient_number": patient.patient_number,
                "name": f"{patient.first_name} {patient.last_name}",
                "first_name": patient.first_name,
                "last_name": patient.last_name,
                "status": patient.status,
                "date_of_birth": patient.date_of_birth.isoformat() if patient.date_of_birth else None,
                "gender": patient.gender,
                "phone": patient.phone,
                "email": patient.email,
                "address": patient.address,
                "blood_type": patient.blood_type,
                "allergies": patient.allergies,
                "emergency_contact_name": patient.emergency_contact_name,
                "emergency_contact_phone": patient.emergency_contact_phone,
                "last_updated": patient.updated_at.isoformat() if patient.updated_at else None
            },
            "bed_assignment": {
                "bed_id": str(bed_assignment.id) if bed_assignment else None,
                "bed_number": bed_assignment.bed_number if bed_assignment else None,
                "room_number": bed_assignment.room.room_number if bed_assignment and bed_assignment.room else None,
                "status": bed_assignment.status if bed_assignment else None,
                "admission_date": bed_assignment.admission_date.isoformat() if bed_assignment and bed_assignment.admission_date else None,
                "discharge_date": bed_assignment.discharge_date.isoformat() if bed_assignment and bed_assignment.discharge_date else None
            } if bed_assignment else None,
            "discharge_reports": [
                {
                    "report_id": str(report.id),
                    "report_number": report.report_number,
                    "discharge_date": report.discharge_date.isoformat() if report.discharge_date else None,
                    "admission_date": report.admission_date.isoformat() if report.admission_date else None,
                    "length_of_stay_days": report.length_of_stay_days,
                    "discharge_condition": report.discharge_condition,
                    "discharge_destination": report.discharge_destination,
                    "discharge_instructions": report.discharge_instructions,
                    "follow_up_required": report.follow_up_required,
                    "created_at": report.created_at.isoformat() if report.created_at else None,
                    "download_url": f"/discharge/{report.report_number}.pdf",
                    "bed_number": db.query(Bed).filter(Bed.id == report.bed_id).first().bed_number if report.bed_id else None
                } for report in discharge_reports
            ],
            "total_discharge_reports": len(discharge_reports),
            "is_discharged": patient.status == "discharged"
        }
        
        db.close()
        return result
        
    except Exception as e:
        db.close()
        return {"success": False, "message": f"Error getting patient details: {str(e)}"}

@mcp.tool()
def download_discharge_report(report_number: str, download_format: str = "pdf") -> Dict[str, Any]:
    """Download a discharge report in the specified format.
    
    Args:
        report_number: The report number to download
        download_format: Format for download - "pdf", "markdown", or "zip" (default: pdf)
    """
    try:
        from report_manager import ReportManager
        manager = ReportManager()
        result = manager.download_report(report_number, download_format)
        return result
    except Exception as e:
        return {"success": False, "error": str(e), "message": f"Failed to download report: {str(e)}"}

@mcp.tool()
def get_discharge_report_storage_stats() -> Dict[str, Any]:
    """Get storage statistics for discharge reports system."""
    try:
        from report_manager import ReportManager
        manager = ReportManager()
        result = manager.get_storage_stats()
        return result
    except Exception as e:
        return {"success": False, "error": str(e), "message": f"Failed to get storage stats: {str(e)}"}

@mcp.tool()
def list_available_discharge_reports(status: str = "all", patient_name: str = None, 
                                   from_date: str = None, to_date: str = None, 
                                   limit: int = 50) -> Dict[str, Any]:
    """List available discharge reports with filtering options.
    
    Args:
        status: Report status filter - "current", "archived", or "all" (default: all)
        patient_name: Filter by patient name (partial match, optional)
        from_date: Start date filter in YYYY-MM-DD format (optional)
        to_date: End date filter in YYYY-MM-DD format (optional)
        limit: Maximum number of reports to return (default: 50)
    """
    try:
        from report_manager import ReportManager
        manager = ReportManager()
        reports = manager.list_reports(
            status=status, 
            patient_name=patient_name,
            from_date=from_date, 
            to_date=to_date, 
            limit=limit
        )
        return {"success": True, "data": reports, "count": len(reports)}
    except Exception as e:
        return {"success": False, "error": str(e), "message": f"Failed to list reports: {str(e)}"}

@mcp.tool()
def archive_old_discharge_reports(days_old: int = 30) -> Dict[str, Any]:
    """Archive discharge reports older than specified days.
    
    Args:
        days_old: Reports older than this many days will be archived (default: 30)
    """
    try:
        from report_manager import ReportManager
        manager = ReportManager()
        result = manager.archive_old_reports(days_old)
        return result
    except Exception as e:
        return {"success": False, "error": str(e), "message": f"Failed to archive reports: {str(e)}"}

# ================================
# AI CLINICAL ASSISTANT TOOLS
# ================================

@mcp.tool()
def ai_clinical_assistant(query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
    """AI assistant for clinical decision support and medical recommendations.
    
    Args:
        query: Clinical question or scenario needing assistance
        context: Optional context (patient_id, medical_history, etc.)
    """
    if not MULTI_AGENT_AVAILABLE or not orchestrator:
        return {"error": "Multi-agent system not available"}
    
    try:
        result = orchestrator.route_request("ai_clinical_assistant", query=query, context=context)
        return result.get("result", result)
    except Exception as e:
        return {"success": False, "error": f"AI clinical assistant error: {str(e)}"}

@mcp.tool()
def natural_language_query(query: str) -> Dict[str, Any]:
    """Process natural language queries for hospital management tasks.
    
    Args:
        query: Natural language query (e.g., "Discharge Patient P1025", "List all patients")
    """
    import asyncio
    from client import HospitalManagementClient
    
    try:
        # Create a client instance to handle the natural language query
        client = HospitalManagementClient()
        
        # Use asyncio to run the intelligent query handler
        result = asyncio.run(client.intelligent_query_handler(query))
        
        return {
            "success": True,
            "query": query,
            "response": result
        }
    except Exception as e:
        return {
            "success": False, 
            "error": f"Natural language query processing error: {str(e)}",
            "query": query
        }

@mcp.tool()
def process_clinical_notes(document_text: str, extract_type: str = "comprehensive") -> Dict[str, Any]:
    """Extract structured data from clinical notes using NLP.
    
    Args:
        document_text: Raw clinical notes text
        extract_type: Type of extraction (symptoms, diagnosis, treatment, medications, comprehensive)
    """
    if not MULTI_AGENT_AVAILABLE or not orchestrator:
        return {"error": "Multi-agent system not available"}
    
    try:
        result = orchestrator.route_request("process_clinical_notes", 
                                          document_text=document_text, extract_type=extract_type)
        return result.get("result", result)
    except Exception as e:
        return {"success": False, "error": f"Clinical note processing error: {str(e)}"}

@mcp.tool()
def get_drug_interactions(medications: List[str], patient_context: Dict[str, Any] = None) -> Dict[str, Any]:
    """Check for drug interactions and contraindications.
    
    Args:
        medications: List of medication names to check
        patient_context: Patient information (allergies, conditions, etc.)
    """
    if not MULTI_AGENT_AVAILABLE or not orchestrator:
        return {"error": "Multi-agent system not available"}
    
    try:
        result = orchestrator.route_request("get_drug_interactions", 
                                          medications=medications, patient_context=patient_context)
        return result.get("result", result)
    except Exception as e:
        return {"success": False, "error": f"Drug interaction check error: {str(e)}"}

@mcp.tool()
def analyze_vital_signs(vital_signs: Dict[str, float], patient_age: int = None) -> Dict[str, Any]:
    """Analyze vital signs and provide clinical insights.
    
    Args:
        vital_signs: Dict of vital sign measurements (heart_rate, blood_pressure, etc.)
        patient_age: Patient age for age-appropriate normal ranges
    """
    if not MULTI_AGENT_AVAILABLE or not orchestrator:
        return {"error": "Multi-agent system not available"}
    
    try:
        result = orchestrator.route_request("analyze_vital_signs", 
                                          vital_signs=vital_signs, patient_age=patient_age)
        return result.get("result", result)
    except Exception as e:
        return {"success": False, "error": f"Vital signs analysis error: {str(e)}"}

@mcp.tool()
def generate_differential_diagnosis(symptoms: List[str], patient_context: Dict[str, Any] = None) -> Dict[str, Any]:
    """Generate differential diagnosis based on symptoms.
    
    Args:
        symptoms: List of patient symptoms
        patient_context: Patient demographics and medical history
    """
    if not MULTI_AGENT_AVAILABLE or not orchestrator:
        return {"error": "Multi-agent system not available"}
    
    try:
        result = orchestrator.route_request("generate_differential_diagnosis", 
                                          symptoms=symptoms, patient_context=patient_context)
        return result.get("result", result)
    except Exception as e:
        return {"success": False, "error": f"Differential diagnosis error: {str(e)}"}

# ================================
# HTTP ENDPOINTS FOR FRONTEND
# ================================

# Define request model for tool calls
from pydantic import BaseModel
from fastapi import HTTPException, Request, Response
from starlette.routing import Route, Mount
from starlette.responses import JSONResponse

class ToolCallRequest(BaseModel):
    method: str
    id: int
    jsonrpc: str = "2.0"
    params: dict

class BulkUploadRequest(BaseModel):
    table: str
    data: List[Dict[str, Any]]

class NameMappingRequest(BaseModel):
    department_names: Optional[List[str]] = None
    category_names: Optional[List[str]] = None
    room_numbers: Optional[List[str]] = None
    type: Optional[str] = None

# Bulk data upload handler
async def bulk_upload_handler(request: Request):
    """Handle bulk data upload from CSV files."""
    try:
        body = await request.json()
        table_type = body.get('table')
        data = body.get('data', [])
        
        if not table_type or not data:
            return JSONResponse({
                "success": False,
                "message": "Missing table type or data"
            }, status_code=400)
        
        db = get_db_session()
        inserted_count = 0
        
        try:
            if table_type == 'beds':
                for item in data:
                    bed = Bed(
                        bed_number=item['bed_number'],
                        room_id=item['room_id'],
                        bed_type=item.get('bed_type'),
                        status=item.get('status', 'available'),
                        notes=item.get('notes')
                    )
                    db.add(bed)
                    inserted_count += 1
            
            elif table_type == 'equipment':
                for item in data:
                    # Handle date fields
                    purchase_date = None
                    if item.get('purchase_date'):
                        try:
                            purchase_date = datetime.strptime(item['purchase_date'], '%Y-%m-%d').date()
                        except ValueError:
                            pass
                    
                    warranty_expiry = None
                    if item.get('warranty_expiry'):
                        try:
                            warranty_expiry = datetime.strptime(item['warranty_expiry'], '%Y-%m-%d').date()
                        except ValueError:
                            pass
                    
                    last_maintenance = None
                    if item.get('last_maintenance'):
                        try:
                            last_maintenance = datetime.strptime(item['last_maintenance'], '%Y-%m-%d').date()
                        except ValueError:
                            pass
                    
                    next_maintenance = None
                    if item.get('next_maintenance'):
                        try:
                            next_maintenance = datetime.strptime(item['next_maintenance'], '%Y-%m-%d').date()
                        except ValueError:
                            pass
                    
                    equipment = Equipment(
                        equipment_id=item['equipment_id'],
                        name=item['name'],
                        category_id=item['category_id'],
                        model=item.get('model'),
                        manufacturer=item.get('manufacturer'),
                        serial_number=item.get('serial_number'),
                        purchase_date=purchase_date,
                        warranty_expiry=warranty_expiry,
                        department_id=item.get('department_id'),
                        status=item.get('status', 'operational'),
                        location=item.get('location'),
                        last_maintenance=last_maintenance,
                        next_maintenance=next_maintenance,
                        cost=item.get('cost'),
                        notes=item.get('notes')
                    )
                    db.add(equipment)
                    inserted_count += 1
            
            elif table_type == 'rooms':
                for item in data:
                    room = Room(
                        room_number=item['room_number'],
                        floor_number=item.get('floor_number'),
                        room_type=item.get('room_type'),
                        department_id=item.get('department_id'),
                        capacity=item.get('capacity', 1),
                        status=item.get('status', 'available')
                    )
                    db.add(room)
                    inserted_count += 1
            
            elif table_type == 'supplies':
                for item in data:
                    # Handle expiry date
                    expiry_date = None
                    if item.get('expiry_date'):
                        try:
                            expiry_date = datetime.strptime(item['expiry_date'], '%Y-%m-%d').date()
                        except ValueError:
                            pass
                    
                    supply = Supply(
                        item_code=item['item_code'],
                        name=item['name'],
                        category_id=item['category_id'],
                        description=item.get('description'),
                        unit_of_measure=item['unit_of_measure'],
                        minimum_stock_level=item.get('minimum_stock_level', 0),
                        maximum_stock_level=item.get('maximum_stock_level', 0),
                        current_stock=item.get('current_stock', 0),
                        unit_cost=item.get('unit_cost', 0),
                        supplier=item.get('supplier'),
                        expiry_date=expiry_date,
                        location=item.get('location')
                    )
                    db.add(supply)
                    inserted_count += 1
            
            else:
                return JSONResponse({
                    "success": False,
                    "message": f"Unsupported table type: {table_type}"
                }, status_code=400)
            
            db.commit()
            
            return JSONResponse({
                "success": True,
                "inserted": inserted_count,
                "message": f"Successfully inserted {inserted_count} records"
            })
            
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
            
    except Exception as e:
        return JSONResponse({
            "success": False,
            "message": str(e)
        }, status_code=500)

# Name to ID mapping handlers
async def get_room_mappings_handler(request: Request):
    """Get room number to ID mappings."""
    try:
        body = await request.json()
        room_numbers = body.get('room_numbers', [])
        
        db = get_db_session()
        try:
            rooms = db.query(Room).filter(Room.room_number.in_(room_numbers)).all()
            mappings = {room.room_number: str(room.id) for room in rooms}
            return JSONResponse(mappings)
        finally:
            db.close()
            
    except Exception as e:
        return JSONResponse({
            "error": str(e)
        }, status_code=500)

async def get_department_mappings_handler(request: Request):
    """Get department name to ID mappings."""
    try:
        body = await request.json()
        department_names = body.get('department_names', [])
        
        db = get_db_session()
        try:
            departments = db.query(Department).filter(Department.name.in_(department_names)).all()
            mappings = {dept.name: str(dept.id) for dept in departments}
            return JSONResponse(mappings)
        finally:
            db.close()
            
    except Exception as e:
        return JSONResponse({
            "error": str(e)
        }, status_code=500)

async def get_category_mappings_handler(request: Request):
    """Get category name to ID mappings."""
    try:
        body = await request.json()
        category_names = body.get('category_names', [])
        category_type = body.get('type', 'equipment')  # 'equipment' or 'supply'
        
        db = get_db_session()
        try:
            if category_type == 'equipment':
                categories = db.query(EquipmentCategory).filter(EquipmentCategory.name.in_(category_names)).all()
            else:  # supply
                categories = db.query(SupplyCategory).filter(SupplyCategory.name.in_(category_names)).all()
                
            mappings = {cat.name: str(cat.id) for cat in categories}
            
            # Create missing categories
            existing_names = set(mappings.keys())
            missing_names = set(category_names) - existing_names
            
            for name in missing_names:
                if category_type == 'equipment':
                    new_category = EquipmentCategory(name=name, description=f"Auto-created category: {name}")
                else:
                    new_category = SupplyCategory(name=name, description=f"Auto-created category: {name}")
                
                db.add(new_category)
                db.flush()  # Flush to get the ID
                mappings[name] = str(new_category.id)
            
            db.commit()
            return JSONResponse(mappings)
        finally:
            db.close()
            
    except Exception as e:
        return JSONResponse({
            "error": str(e)
        }, status_code=500)

# Tool call endpoint handler
async def call_tool_http(request: Request):
    try:
        data = await request.json()
        tool_name = data.get("params", {}).get("name")
        arguments = data.get("params", {}).get("arguments", {})
        
        if not tool_name:
            raise HTTPException(status_code=400, detail="Tool name is required")
        
        # System-level tools that should not be routed through orchestrator
        system_tools = ["get_system_status", "get_agent_info", "list_agents", "execute_workflow", 
                       "download_discharge_report", "get_discharge_report_storage_stats", 
                       "list_available_discharge_reports", "archive_old_discharge_reports",
                       "add_equipment_usage_with_codes", "search_discharged_patients", 
                       "get_patient_with_discharge_details", "check_bed_status"]
        
        if tool_name in system_tools:
            # Handle system tools directly
            if tool_name == "get_system_status":
                result = get_system_status()
            elif tool_name == "get_agent_info":
                result = get_agent_info(**arguments)
            elif tool_name == "list_agents":
                result = list_agents()
            elif tool_name == "execute_workflow":
                result = execute_workflow(**arguments)
            elif tool_name == "download_discharge_report":
                result = download_discharge_report(**arguments)
            elif tool_name == "add_equipment_usage_with_codes":
                result = add_equipment_usage_with_codes(**arguments)
            elif tool_name == "get_discharge_report_storage_stats":
                result = get_discharge_report_storage_stats(**arguments)
            elif tool_name == "list_available_discharge_reports":
                result = list_available_discharge_reports(**arguments)
            elif tool_name == "archive_old_discharge_reports":
                result = archive_old_discharge_reports(**arguments)
            elif tool_name == "search_discharged_patients":
                result = search_discharged_patients(**arguments)
            elif tool_name == "get_patient_with_discharge_details":
                result = get_patient_with_discharge_details(**arguments)
            elif tool_name == "check_bed_status":
                result = check_bed_status(**arguments)
            else:
                result = {"error": f"System tool {tool_name} not implemented"}
        else:
            # Try to execute through orchestrator for other tools
            if MULTI_AGENT_AVAILABLE and orchestrator:
                try:
                    result = orchestrator.route_request(tool_name, **arguments)
                except Exception as agent_error:
                    print(f"⚠️ Agent routing failed for {tool_name}: {agent_error}")
                    # Fall through to direct tool execution
                    result = {"error": f"Agent routing failed: {str(agent_error)}"}
            else:
                result = {"error": "Multi-agent system not available"}
        
        return JSONResponse({
            "jsonrpc": "2.0",
            "id": data.get("id", 1),
            "result": {
                "content": [{"type": "text", "text": json.dumps(result) if not isinstance(result, str) else result}]
            }
        })
        
    except Exception as e:
        # Detailed error logging for debugging
        error_details = {
            "error_type": type(e).__name__,
            "error_message": str(e),
            "tool_name": data.get("params", {}).get("name", "unknown"),
            "arguments": data.get("params", {}).get("arguments", {}),
            "traceback": traceback.format_exc()
        }
        
        print(f"❌ HTTP TOOL CALL ERROR: {error_details}")
        
        return JSONResponse({
            "jsonrpc": "2.0",
            "id": data.get("id", 1),
            "error": {
                "code": -32603,
                "message": f"Internal error: {str(e)}",
                "details": error_details
            }
        }, status_code=500)

# List tools endpoint handler
#: Set at startup when guarded mode is on: the canonical tool names, used to
#: stop /tools/list advertising capabilities that cannot be executed.
GUARDED_TOOL_NAMES = None
GUARDED_POLICY_ENGINE = None
GUARDED_TOKEN_ISSUER = None


def _visible_tool_names(request):
    """Names this caller could actually execute, or None when unguarded.

    Narrowed by role when the request carries a valid token. Without one the
    listing still never exceeds the canonical registry — advertising a tool that
    would be refused is a bad contract, and for an LLM client every unusable
    name is a plausible thing to propose and then be denied.
    """
    if GUARDED_TOOL_NAMES is None:
        return None

    visible = set(GUARDED_TOOL_NAMES)
    if GUARDED_POLICY_ENGINE is None or GUARDED_TOKEN_ISSUER is None:
        return visible

    try:
        from hms_agent.auth import principal_from_request

        principal = principal_from_request(request.headers, GUARDED_TOKEN_ISSUER)
    except Exception:
        return visible

    return visible & set(GUARDED_POLICY_ENGINE.tools_for_role(principal.role))


async def list_tools_http(request: Request):
    try:
        tools_list = []
        
        # Debug logging
        print(f"🔍 DEBUG: MULTI_AGENT_AVAILABLE = {MULTI_AGENT_AVAILABLE}")
        print(f"🔍 DEBUG: orchestrator = {orchestrator}")
        
        # Get tools from orchestrator if available
        if MULTI_AGENT_AVAILABLE and orchestrator:
            print("🔍 DEBUG: Getting tools with descriptions from orchestrator...")
            
            # Get tools with their actual descriptions from docstrings
            if hasattr(orchestrator, 'get_tools_with_descriptions'):
                tools_with_descriptions = orchestrator.get_tools_with_descriptions()
                print(f"🔍 DEBUG: Got {len(tools_with_descriptions)} tools with descriptions")
                
                for tool_name, description in tools_with_descriptions.items():
                    tools_list.append({
                        "name": tool_name,
                        "description": description
                    })
            else:
                # Fallback to old method
                orchestrator_tools = orchestrator.get_tools()
                print(f"🔍 DEBUG: Got {len(orchestrator_tools) if orchestrator_tools else 0} tools from orchestrator (fallback)")
                
                # Handle if get_tools() returns a list or dict
                if isinstance(orchestrator_tools, list):
                    for tool_name in orchestrator_tools:
                        tools_list.append({
                            "name": tool_name,
                            "description": f"Multi-agent tool: {tool_name}"
                        })
                elif isinstance(orchestrator_tools, dict):
                    for tool_name, tool_info in orchestrator_tools.items():
                        tools_list.append({
                            "name": tool_name,
                            "description": tool_info.get("description", "Multi-agent tool")
                        })
        
        # ALSO include MCP wrapper tools (like check_bed_status)
        print("🔍 DEBUG: Adding MCP wrapper tools...")
        if hasattr(mcp, '_tools'):
            for tool in mcp._tools:
                # Avoid duplicates - only add if not already in list
                if not any(t["name"] == tool.name for t in tools_list):
                    tools_list.append({
                        "name": tool.name,
                        "description": tool.description or "No description available"
                    })
                    print(f"🔍 DEBUG: Added MCP tool: {tool.name}")
        elif hasattr(mcp, 'registry') and hasattr(mcp.registry, 'tools'):
            for tool_name, tool in mcp.registry.tools.items():
                # Avoid duplicates - only add if not already in list
                if not any(t["name"] == tool_name for t in tools_list):
                    tools_list.append({
                        "name": tool_name,
                        "description": getattr(tool, 'description', "No description available")
                    })
                    print(f"🔍 DEBUG: Added MCP tool: {tool_name}")
        
        # If no orchestrator, fall back to MCP tools only
        if not MULTI_AGENT_AVAILABLE or not orchestrator:
            print("🔍 DEBUG: No orchestrator available, using MCP tools only...")
            # FastMCP stores tools in the registry
            if hasattr(mcp, '_tools'):
                for tool in mcp._tools:
                    tools_list.append({
                        "name": tool.name,
                        "description": tool.description or "No description available"
                    })
            elif hasattr(mcp, 'registry') and hasattr(mcp.registry, 'tools'):
                for tool_name, tool in mcp.registry.tools.items():
                    tools_list.append({
                        "name": tool_name,
                        "description": getattr(tool, 'description', "No description available")
                    })
        
        visible = _visible_tool_names(request)
        if visible is not None:
            tools_list = [x for x in tools_list if x.get("name") in visible]

        return JSONResponse({
            "jsonrpc": "2.0",
            "result": {
                "tools": tools_list
            }
        })
    except Exception as e:
        return JSONResponse({
            "jsonrpc": "2.0",
            "error": {
                "code": -32603,
                "message": f"Failed to list tools: {str(e)}"
            }
        }, status_code=500)

# Health check endpoint handler
async def health_check(request: Request):
    try:
        db_status = "connected" if DATABASE_AVAILABLE else "disconnected"
        agent_status = "active" if MULTI_AGENT_AVAILABLE and orchestrator else "inactive"
        
        return JSONResponse({
            "status": "healthy",
            "database": db_status,
            "server": "running",
            "multi_agent": agent_status,
            "agents_count": len(orchestrator.agents) if orchestrator else 0,
            "tools_count": len(orchestrator.get_tools()) if orchestrator else len(mcp.tools)
        })
    except Exception as e:
        return JSONResponse({
            "status": "error",
            "message": str(e)
        }, status_code=500)

# Root endpoint handler for http://localhost:8000/
async def root_handler(request: Request):
    db_status = "connected" if DATABASE_AVAILABLE else "disconnected"
    return JSONResponse({
        "status": "online",
        "service": "CarePulse Hospital Management System Backend",
        "database": f"PostgreSQL 15 ({db_status} locally in Docker container 'hospital_postgres')",
        "endpoints": {
            "health": "/health",
            "tools_list": "/tools/list",
            "tools_call": "/tools/call",
            "bulk_upload": "/api/bulk-upload"
        },
        "frontend": "http://localhost:5173",
        "message": "CarePulse backend server is active and healthy."
    })

if __name__ == "__main__":
    import uvicorn
    
    print("🏥 Starting Hospital Management System Multi-Agent MCP Server...")
    print(f"📊 Multi-agent system: {'✅ Available' if MULTI_AGENT_AVAILABLE else '❌ Not available'}")
    print(f"🗃️ Database: {'✅ Available' if DATABASE_AVAILABLE else '❌ Not available'}")
    
    if MULTI_AGENT_AVAILABLE and orchestrator:
        print(f"🤖 Agents initialized: {len(orchestrator.agents)}")
        print(f"🔧 Total tools available: {len(orchestrator.get_tools())}")
    
    try:
        import uvicorn
        
        # Get the SSE app from FastMCP
        app = mcp.sse_app()
        
        print("📡 Starting MCP server with HTTP/SSE support...")
        print("   Server will be available at: http://0.0.0.0:8000")
        print("   Health check: http://0.0.0.0:8000/health")
        
        # Add custom routes to the Starlette app
        import os
        reports_dir = os.path.join(os.path.dirname(__file__), "reports", "discharge")
        
        # ------------------------------------------------------------------
        # Guarded execution path (hms_agent).
        #
        # Controlled by TOOL_EXECUTION_MODE, which defaults to "legacy" so this
        # is inert until explicitly switched on:
        #   legacy  - only the original /tools/call is served (default)
        #   shadow  - guarded routes also mounted, legacy still serves /tools/call
        #   guarded - /tools/call is served by the guarded pipeline
        # ------------------------------------------------------------------
        guarded_routes = []
        sse_auth_wrapper = None
        try:
            from hms_agent.audit import SqlAlchemyAuditSink, create_audit_tables
            from hms_agent.idempotency import IdempotencyStore, create_idempotency_tables
            from hms_agent.auth import LoginService, SqlAlchemyUserRepository, TokenIssuer
            from hms_agent.config import ToolExecutionMode
            from hms_agent.http import ToolCallService, build_guarded_routes
            from hms_agent.http.app import build_login_route
            from hms_agent.policy import PolicyEngine
            from hms_agent.registry import CanonicalToolRegistry

            execution_mode = ToolExecutionMode.current()

            if execution_mode is not ToolExecutionMode.LEGACY:
                from database import SessionLocal
                from database import engine as db_engine

                token_issuer = TokenIssuer()          # raises unless HMS_JWT_SECRET is set

                # Audit events go to PostgreSQL. strict=True means an action that
                # cannot be recorded is not performed: ToolCallService writes the
                # EXECUTING event before dispatch, so a failed audit write stops
                # the call rather than producing an unlogged mutation.
                create_audit_tables(db_engine)
                audit_strict = (os.getenv("HMS_AUDIT_STRICT") or "true").lower() != "false"
                audit_sink = SqlAlchemyAuditSink(SessionLocal, strict=audit_strict)
                tool_registry = CanonicalToolRegistry.from_agents(orchestrator.agents)

                # Idempotency for state-changing tools. Without this the store
                # is None and the whole check is skipped, so a retried mutation
                # would execute twice -- the protection would exist in the tests
                # and not in the running server.
                create_idempotency_tables(db_engine)
                idempotency_store = IdempotencyStore(SessionLocal)

                tool_service = ToolCallService(
                    tool_registry, PolicyEngine(), token_issuer, audit_sink,
                    idempotency_store=idempotency_store,
                )
                login_service = LoginService(
                    SqlAlchemyUserRepository(SessionLocal), token_issuer
                )

                guarded_routes = (
                    build_login_route(login_service)
                    + build_guarded_routes(tool_service, path="/v2/tools/call")
                )

                # Agent endpoint. Mounted only when a planner can be built and a
                # checkpointer is available, because approval is not resumable
                # without one -- better to omit the route than to serve an agent
                # whose pauses cannot be resumed.
                try:
                    from langgraph.checkpoint.sqlite import SqliteSaver

                    from hms_agent.graph import LLMPlanner
                    from hms_agent.http import AgentRunService, build_agent_routes
                    from hms_agent.observability import MetricsRegistry

                    if not os.getenv("OPENAI_API_KEY"):
                        raise RuntimeError("OPENAI_API_KEY is not set")

                    checkpoint_path = os.getenv(
                        "HMS_CHECKPOINT_PATH",
                        os.path.join(os.path.dirname(__file__), "agent_checkpoints.sqlite"),
                    )
                    # Held open for the process lifetime: suspended runs must
                    # outlive the request that created them.
                    _checkpointer_cm = SqliteSaver.from_conn_string(checkpoint_path)
                    agent_checkpointer = _checkpointer_cm.__enter__()

                    agent_metrics = MetricsRegistry()
                    agent_service = AgentRunService(
                        planner=LLMPlanner(PolicyEngine(), tool_registry.names()),
                        policy_engine=PolicyEngine(),
                        tool_service=tool_service,
                        issuer=token_issuer,
                        checkpointer=agent_checkpointer,
                        metrics=agent_metrics,
                    )
                    guarded_routes += build_agent_routes(agent_service)
                    print(f"🤖 Agent endpoint enabled (checkpoints: {checkpoint_path})")
                except Exception as agent_error:
                    print(f"ℹ️  Agent endpoint not mounted: {agent_error}")
                if execution_mode is ToolExecutionMode.GUARDED:
                    guarded_routes += build_guarded_routes(tool_service, path="/tools/call")

                    # Close the SSE transport too. Guarding only HTTP would leave
                    # mcp.sse_app() serving the same agent methods unguarded.
                    from hms_agent.transport import RequireBearerAuth, guard_tool_manager

                    guard_tool_manager(
                        mcp,
                        PolicyEngine(),
                        allowed_tools=tool_registry.names(),
                        audit_sink=audit_sink,
                    )
                    sse_auth_wrapper = (RequireBearerAuth, token_issuer)
                    sse_state = "guarded"
                else:
                    sse_state = "UNGUARDED"

                # Publish to the /tools/list handler so it cannot advertise
                # capabilities the guarded path would refuse. This runs at module
                # scope, so plain assignment rebinds the module globals; a
                # `global` statement here is a SyntaxError because the names are
                # assigned earlier in the same scope.
                GUARDED_TOOL_NAMES = tool_registry.names()
                GUARDED_POLICY_ENGINE = PolicyEngine()
                GUARDED_TOKEN_ISSUER = token_issuer

                print(f"🔒 Guarded execution enabled (mode={execution_mode.value}, "
                      f"{len(tool_registry.names())} tools bound, sse={sse_state})")
            else:
                print("⚠️  TOOL_EXECUTION_MODE=legacy - /tools/call is unauthenticated")
        except Exception as guard_error:
            # Never take the server down for a guarded-path misconfiguration, but
            # never silently fall back to the open path either.
            if (os.getenv("TOOL_EXECUTION_MODE") or "legacy").strip().lower() != "legacy":
                raise RuntimeError(
                    f"TOOL_EXECUTION_MODE is not 'legacy' but the guarded path "
                    f"failed to initialise: {guard_error}"
                ) from guard_error
            print(f"⚠️  Guarded path unavailable: {guard_error}")

        custom_routes = guarded_routes + [
            Route("/", root_handler, methods=["GET"]),
            Route("/tools/call", call_tool_http, methods=["POST"]),
            Route("/tools/list", list_tools_http, methods=["GET"]),
            Route("/health", health_check, methods=["GET"]),
            Route("/api/bulk-upload", bulk_upload_handler, methods=["POST"]),
            Route("/api/rooms/by-numbers", get_room_mappings_handler, methods=["POST"]),
            Route("/api/departments/by-names", get_department_mappings_handler, methods=["POST"]),
            Route("/api/categories/by-names", get_category_mappings_handler, methods=["POST"]),
            Mount("/discharge", StaticFiles(directory=reports_dir), name="static"),
        ]
        
        # Add routes to existing app
        app.routes.extend(custom_routes)
        
        # Add CORS middleware for frontend communication
        app.add_middleware(
            CORSMiddleware,
            allow_origins=[
                "http://localhost:3000", "http://127.0.0.1:3000",
                "http://localhost:5173", "http://127.0.0.1:5173",
                "http://54.85.118.65", "http://54.85.118.65:80",
                "http://54.85.118.65:3000", "http://54.85.118.65:5173",
                "*"  # Allow all origins for deployment flexibility
            ],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        print("📡 Added custom HTTP endpoints:")
        print("   POST /tools/call - Call MCP tools via HTTP")
        print("   GET /tools/list - List available tools")
        print("   GET /health - Health check")
        print("   POST /api/bulk-upload - Bulk data upload from CSV")
        print("   POST /api/rooms/by-numbers - Get room ID mappings")
        print("   POST /api/departments/by-names - Get department ID mappings")
        print("   POST /api/categories/by-names - Get category ID mappings")
        
        # Applied last: RequireBearerAuth is a bare ASGI callable, so it must wrap
        # the app only after .routes and .add_middleware have been used.
        if sse_auth_wrapper is not None:
            wrapper_cls, wrapper_issuer = sse_auth_wrapper
            app = wrapper_cls(app, wrapper_issuer)
            print("🔒 SSE transport requires a bearer token")

        # Run with uvicorn - bind to 0.0.0.0 for Docker container access
        uvicorn.run(app, host="0.0.0.0", port=8000)
        
    except Exception as e:
        import sys
        sys.stderr.write(f"FATAL ERROR: Server failed to start: {e}\n")
        import traceback
        traceback.print_exc(file=sys.stderr)
        exit(1)