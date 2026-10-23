"""
Master Hospital Management Integration System
===========================================

Master orchestration system that integrates all advanced LangChain/LangGraph agents
for comprehensive AI-powered hospital management.
"""

from typing import Any, Dict, List, Optional, TypedDict, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import json
import uuid
import asyncio
from langgraph.graph import StateGraph, END, START
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
import logging

# Import all our advanced agents
from .enhanced_orchestrator_agent import EnhancedOrchestratorAgent
from .real_time_monitoring_agent import RealTimeMonitoringAgent
from .predictive_analytics_agent import AdvancedPredictiveSystem
from .multilingual_support_agent import MultiLanguageSupport
from .equipment_lifecycle_agent import EquipmentLifecycleManager

class SystemModule(Enum):
    ORCHESTRATOR = "orchestrator"
    MONITORING = "monitoring"
    PREDICTIVE = "predictive"
    MULTILINGUAL = "multilingual"
    EQUIPMENT = "equipment"
    PATIENT_CARE = "patient_care"
    STAFF_MANAGEMENT = "staff_management"
    RESOURCE_PLANNING = "resource_planning"

class IntegrationLevel(Enum):
    BASIC = "basic"
    STANDARD = "standard"
    ADVANCED = "advanced"
    ENTERPRISE = "enterprise"

class SystemStatus(Enum):
    INITIALIZING = "initializing"
    OPERATIONAL = "operational"
    MAINTENANCE = "maintenance"
    ERROR = "error"
    OFFLINE = "offline"

@dataclass
class SystemHealth:
    module: SystemModule
    status: SystemStatus
    performance_score: float
    last_check: datetime
    error_count: int = 0
    warnings: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)

class MasterSystemState(TypedDict):
    """State for master integration system"""
    user_request: str
    request_type: str
    priority_level: str
    affected_modules: List[str]
    conversation_context: Dict[str, Any]
    orchestrator_response: Dict[str, Any]
    monitoring_data: Dict[str, Any]
    predictive_insights: Dict[str, Any]
    multilingual_support: Dict[str, Any]
    equipment_status: Dict[str, Any]
    integrated_response: Dict[str, Any]
    execution_log: List[Dict[str, Any]]

class MasterHospitalManagementSystem:
    """
    Master Hospital Management Integration System
    
    Features:
    - Unified AI orchestration across all hospital systems
    - Real-time cross-system monitoring and alerting
    - Predictive analytics for proactive management
    - Multi-language support for international patients
    - Equipment lifecycle optimization
    - Intelligent routing and task distribution
    - Comprehensive performance analytics
    - Emergency response coordination
    - Compliance and quality assurance
    - Resource optimization across departments
    """
    
    def __init__(self, integration_level: IntegrationLevel = IntegrationLevel.ENTERPRISE):
        self.integration_level = integration_level
        self.system_id = str(uuid.uuid4())
        self.startup_time = datetime.now()

        # Initialize logging first
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Initialize core attributes
        self.system_health = {}
        self.performance_metrics = {}
        self.active_sessions = {}
        
        # Memory and context management
        self.memory_saver = MemorySaver()
        self.conversation_contexts = {}
        
        # Initialize core systems
        self.initialize_core_systems()
        self.setup_integration_workflows()
        self.setup_monitoring_and_alerts()
        self.setup_performance_tracking()
        
        self.logger.info(f"Master Hospital Management System initialized with {integration_level.value} integration level")
    
    def initialize_core_systems(self):
        """Initialize all core AI systems"""
        try:
            # Enhanced Orchestrator for conversational AI and intelligent routing
            self.orchestrator = EnhancedOrchestratorAgent()
            self.system_health[SystemModule.ORCHESTRATOR] = SystemHealth(
                module=SystemModule.ORCHESTRATOR,
                status=SystemStatus.OPERATIONAL,
                performance_score=1.0,
                last_check=datetime.now()
            )
            
            # Real-time Monitoring for alerts and system health
            self.monitoring_agent = RealTimeMonitoringAgent()
            self.system_health[SystemModule.MONITORING] = SystemHealth(
                module=SystemModule.MONITORING,
                status=SystemStatus.OPERATIONAL,
                performance_score=1.0,
                last_check=datetime.now()
            )
            
            # Predictive Analytics for forecasting and optimization
            self.predictive_system = AdvancedPredictiveSystem()
            self.system_health[SystemModule.PREDICTIVE] = SystemHealth(
                module=SystemModule.PREDICTIVE,
                status=SystemStatus.OPERATIONAL,
                performance_score=1.0,
                last_check=datetime.now()
            )
            
            # Multi-language Support for international patients
            self.multilingual_agent = MultiLanguageSupport()
            self.system_health[SystemModule.MULTILINGUAL] = SystemHealth(
                module=SystemModule.MULTILINGUAL,
                status=SystemStatus.OPERATIONAL,
                performance_score=1.0,
                last_check=datetime.now()
            )
            
            # Equipment Lifecycle Management
            self.equipment_manager = EquipmentLifecycleManager()
            self.system_health[SystemModule.EQUIPMENT] = SystemHealth(
                module=SystemModule.EQUIPMENT,
                status=SystemStatus.OPERATIONAL,
                performance_score=1.0,
                last_check=datetime.now()
            )
            
            # Initialize AI engine for master coordination
            import os
            api_key = os.getenv('OPENAI_API_KEY') or os.getenv('VITE_OPENAI_API_KEY')
            
            if api_key:
                self.llm = ChatOpenAI(
                    api_key=api_key,
                    model="gpt-4",
                    temperature=0.1
                )
            
            self.logger.info("All core systems initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Error initializing core systems: {e}")
            raise
    
    def setup_integration_workflows(self):
        """Setup master integration workflows"""
        self.workflows = {
            "unified_request_processing": self.build_unified_request_workflow(),
            "emergency_response": self.build_emergency_response_workflow(),
            "predictive_optimization": self.build_predictive_optimization_workflow(),
            "cross_system_monitoring": self.build_cross_system_monitoring_workflow()
        }
    
    def build_unified_request_workflow(self) -> StateGraph:
        """Build unified request processing workflow"""
        
        def analyze_request(state: MasterSystemState) -> MasterSystemState:
            """Analyze incoming request and determine routing"""
            user_request = state["user_request"]
            
            analysis_prompt = ChatPromptTemplate.from_messages([
                ("system", """You are the master AI coordinator for a comprehensive hospital management system.
                
                Analyze the user request and determine:
                1. Request type and priority level
                2. Which system modules should handle this request
                3. Required integration level
                4. Emergency status
                5. Language requirements
                6. Expected response time
                
                Available modules:
                - Orchestrator: Conversational AI, intelligent routing
                - Monitoring: Real-time alerts, system health
                - Predictive: Forecasting, analytics, optimization
                - Multilingual: Translation, cultural adaptation
                - Equipment: Lifecycle management, maintenance
                - Patient Care: Clinical workflows, care coordination
                - Staff Management: Scheduling, resource allocation
                - Resource Planning: Capacity, supply chain
                
                Return analysis as JSON:
                {{
                    "request_type": "patient_care/staff_management/equipment/emergency/etc",
                    "priority_level": "low/medium/high/critical",
                    "affected_modules": ["module1", "module2"],
                    "language_detected": "en/es/fr/etc",
                    "emergency_indicators": ["indicator1", "indicator2"],
                    "estimated_complexity": "simple/moderate/complex",
                    "response_time_target": "immediate/5min/30min/1hour"
                }}"""),
                ("user", f"Analyze this request: {user_request}")
            ])
            
            try:
                analysis_chain = analysis_prompt | self.llm | JsonOutputParser()
                result = analysis_chain.invoke({"user_request": user_request})
                
                return {
                    **state,
                    "request_type": result.get("request_type", "general"),
                    "priority_level": result.get("priority_level", "medium"),
                    "affected_modules": result.get("affected_modules", ["orchestrator"]),
                    "language_detected": result.get("language_detected", "en"),
                    "emergency_indicators": result.get("emergency_indicators", []),
                    "complexity": result.get("estimated_complexity", "moderate"),
                    "response_target": result.get("response_time_target", "5min")
                }
                
            except Exception as e:
                self.logger.error(f"Error analyzing request: {e}")
                return {
                    **state,
                    "request_type": "general",
                    "priority_level": "medium",
                    "affected_modules": ["orchestrator"]
                }
        
        def route_to_orchestrator(state: MasterSystemState) -> MasterSystemState:
            """Route request to enhanced orchestrator"""
            user_request = state["user_request"]
            request_type = state.get("request_type", "general")
            
            try:
                # Use orchestrator's conversational capabilities
                orchestrator_response = asyncio.run(
                    self.orchestrator.handle_conversation(
                        message=user_request,
                        user_id=state.get("user_id", "anonymous"),
                        context=state.get("conversation_context", {})
                    )
                )
                
                return {
                    **state,
                    "orchestrator_response": orchestrator_response
                }
                
            except Exception as e:
                self.logger.error(f"Error routing to orchestrator: {e}")
                return {
                    **state,
                    "orchestrator_response": {"error": "Orchestrator unavailable"}
                }
        
        def gather_monitoring_data(state: MasterSystemState) -> MasterSystemState:
            """Gather real-time monitoring data"""
            affected_modules = state.get("affected_modules", [])
            
            try:
                # Get current system health and alerts
                monitoring_data = {
                    "system_health": {
                        module.name: {
                            "status": health.status.value,
                            "performance": health.performance_score,
                            "last_check": health.last_check.isoformat()
                        }
                        for module, health in self.system_health.items()
                    },
                    "active_alerts": self.get_active_alerts(),
                    "performance_metrics": self.get_current_performance_metrics()
                }
                
                return {
                    **state,
                    "monitoring_data": monitoring_data
                }
                
            except Exception as e:
                self.logger.error(f"Error gathering monitoring data: {e}")
                return {
                    **state,
                    "monitoring_data": {"error": "Monitoring data unavailable"}
                }
        
        def get_predictive_insights(state: MasterSystemState) -> MasterSystemState:
            """Get predictive analytics insights"""
            request_type = state.get("request_type", "general")
            
            try:
                # Import at function level to avoid scope issues
                from .predictive_analytics_agent import PredictionType, ForecastHorizon
                
                # Get relevant predictions based on request type
                predictive_insights = {}
                
                if request_type in ["patient_care", "resource_planning"]:
                    # Get bed demand predictions
                    bed_prediction = asyncio.run(
                        self.predictive_system.run_prediction(
                            PredictionType.BED_DEMAND,
                            ForecastHorizon.DAILY,
                            7
                        )
                    )
                    predictive_insights["bed_demand"] = {
                        "predictions": bed_prediction.predictions[:3],  # Next 3 days
                        "confidence": bed_prediction.confidence_score,
                        "recommendations": bed_prediction.recommendations[:2]
                    }
                
                if request_type in ["staff_management", "resource_planning"]:
                    # Get staff requirement predictions
                    staff_prediction = asyncio.run(
                        self.predictive_system.run_prediction(
                            PredictionType.STAFF_REQUIREMENTS,
                            ForecastHorizon.HOURLY,
                            24
                        )
                    )
                    predictive_insights["staff_requirements"] = {
                        "predictions": staff_prediction.predictions[:6],  # Next 6 hours
                        "confidence": staff_prediction.confidence_score,
                        "recommendations": staff_prediction.recommendations[:2]
                    }
                
                return {
                    **state,
                    "predictive_insights": predictive_insights
                }
                
            except Exception as e:
                self.logger.error(f"Error getting predictive insights: {e}")
                return {
                    **state,
                    "predictive_insights": {"error": "Predictive insights unavailable"}
                }
        
        def integrate_response(state: MasterSystemState) -> MasterSystemState:
            """Integrate responses from all systems"""
            orchestrator_response = state.get("orchestrator_response", {})
            monitoring_data = state.get("monitoring_data", {})
            predictive_insights = state.get("predictive_insights", {})
            language_detected = state.get("language_detected", "en")
            user_request = state.get("user_request", "")
            
            integration_prompt = ChatPromptTemplate.from_messages([
                ("system", """You are the master integration AI that combines responses from multiple hospital management systems.
                
                Original User Request: {user_request}
                Orchestrator Response: {orchestrator_response}
                Monitoring Data: {monitoring_data}
                Predictive Insights: {predictive_insights}
                
                Create a unified response that:
                1. DIRECTLY addresses the specific user request: "{user_request}"
                2. Uses the orchestrator response as the primary answer
                3. Incorporates relevant real-time monitoring data only if applicable
                4. Includes predictive insights only if relevant to the request
                5. Maintains focus on what the user actually asked for
                6. Provides actionable information specific to their question
                
                Important: Do NOT default to bed occupancy information unless the user specifically asked about beds or occupancy.
                
                Return as JSON:
                {{
                    "primary_response": "Direct answer to the user's specific request",
                    "real_time_insights": ["relevant insights only"],
                    "predictive_recommendations": ["relevant predictions only"],
                    "urgent_items": ["urgent items if any"],
                    "next_steps": ["specific next steps for this request"],
                    "confidence_score": 0.95,
                    "requires_followup": false
                }}"""),
                ("user", "Integrate these system responses to answer: {user_request}")
            ])
            
            try:
                integration_chain = integration_prompt | self.llm | JsonOutputParser()
                result = integration_chain.invoke({
                    "user_request": user_request,
                    "orchestrator_response": json.dumps(orchestrator_response),
                    "monitoring_data": json.dumps(monitoring_data),
                    "predictive_insights": json.dumps(predictive_insights)
                })
                
                # If language is not English, translate the response
                integrated_response = result
                if language_detected != "en":
                    try:
                        from .multilingual_support_agent import LanguageCode, ContentType
                        
                        # Map common language codes
                        lang_mapping = {
                            "es": LanguageCode.SPANISH,
                            "fr": LanguageCode.FRENCH,
                            "de": LanguageCode.GERMAN,
                            "zh": LanguageCode.CHINESE_SIMPLIFIED
                        }
                        
                        if language_detected in lang_mapping:
                            translation_result = asyncio.run(
                                self.multilingual_agent.translate_text(
                                    result.get("primary_response", ""),
                                    lang_mapping[language_detected],
                                    ContentType.GENERAL_COMMUNICATION
                                )
                            )
                            integrated_response["translated_response"] = translation_result.translated_text
                            integrated_response["language"] = language_detected
                    
                    except Exception as e:
                        self.logger.warning(f"Translation failed: {e}")
                
                return {
                    **state,
                    "integrated_response": integrated_response
                }
                
            except Exception as e:
                self.logger.error(f"Error integrating response: {e}")
                return {
                    **state,
                    "integrated_response": {
                        "primary_response": "System integration error occurred.",
                        "error": str(e)
                    }
                }
        
        # Build workflow graph
        workflow = StateGraph(MasterSystemState)
        
        workflow.add_node("analyze", analyze_request)
        workflow.add_node("orchestrate", route_to_orchestrator)
        workflow.add_node("monitor", gather_monitoring_data)
        workflow.add_node("predict", get_predictive_insights)
        workflow.add_node("integrate", integrate_response)
        
        workflow.add_edge(START, "analyze")
        workflow.add_edge("analyze", "orchestrate")
        workflow.add_edge("orchestrate", "monitor")
        workflow.add_edge("monitor", "predict")
        workflow.add_edge("predict", "integrate")
        workflow.add_edge("integrate", END)
        
        return workflow.compile(checkpointer=self.memory_saver)
    
    def build_emergency_response_workflow(self) -> StateGraph:
        """Build emergency response coordination workflow"""
        # Implementation for emergency response
        pass
    
    def build_predictive_optimization_workflow(self) -> StateGraph:
        """Build predictive optimization workflow"""
        # Implementation for predictive optimization
        pass
    
    def build_cross_system_monitoring_workflow(self) -> StateGraph:
        """Build cross-system monitoring workflow"""
        # Implementation for cross-system monitoring
        pass
    
    def setup_monitoring_and_alerts(self):
        """Setup comprehensive monitoring and alerting"""
        self.alert_thresholds = {
            "system_performance": {"warning": 0.80, "critical": 0.60},
            "response_time": {"warning": 5.0, "critical": 10.0},  # seconds
            "error_rate": {"warning": 0.05, "critical": 0.10},
            "memory_usage": {"warning": 0.80, "critical": 0.90}
        }
        
        self.notification_channels = {
            "system_admin": {"email": "admin@hospital.com", "sms": "+1234567890"},
            "on_call_engineer": {"email": "oncall@hospital.com", "pager": "12345"},
            "operations_center": {"dashboard": "ops_dashboard", "alert_system": "central_alerts"}
        }
    
    def setup_performance_tracking(self):
        """Setup performance tracking and analytics"""
        self.performance_trackers = {
            "request_processing_time": [],
            "system_response_accuracy": [],
            "user_satisfaction_scores": [],
            "system_uptime": [],
            "integration_success_rate": []
        }
    
    async def process_request(self, user_request: str, user_id: str = "anonymous", 
                            context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process user request through master integration system"""
        
        request_id = str(uuid.uuid4())
        start_time = datetime.now()
        
        try:
            # Log request
            self.logger.info(f"Processing request {request_id}: {user_request[:100]}...")
            
            # Prepare initial state
            state = MasterSystemState(
                user_request=user_request,
                request_type="unknown",
                priority_level="medium",
                affected_modules=[],
                conversation_context=context or {},
                orchestrator_response={},
                monitoring_data={},
                predictive_insights={},
                multilingual_support={},
                equipment_status={},
                integrated_response={},
                execution_log=[]
            )
            
            # Process through unified workflow
            workflow = self.workflows["unified_request_processing"]
            
            config = {"configurable": {"thread_id": f"user_{user_id}"}}
            result = await workflow.ainvoke(state, config=config)
            
            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Update performance metrics
            self.performance_trackers["request_processing_time"].append(processing_time)
            
            # Prepare final response
            final_response = {
                "request_id": request_id,
                "status": "completed",
                "processing_time_seconds": processing_time,
                "response": result.get("integrated_response", {}),
                "system_health": self.get_system_health_summary(),
                "timestamp": datetime.now().isoformat()
            }
            
            self.logger.info(f"Request {request_id} completed in {processing_time:.2f}s")
            
            return final_response
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            self.logger.error(f"Error processing request {request_id}: {e}")
            
            return {
                "request_id": request_id,
                "status": "error",
                "processing_time_seconds": processing_time,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def get_system_health_summary(self) -> Dict[str, Any]:
        """Get comprehensive system health summary"""
        total_modules = len(self.system_health)
        operational_modules = sum(
            1 for health in self.system_health.values()
            if health.status == SystemStatus.OPERATIONAL
        )
        
        average_performance = sum(
            health.performance_score for health in self.system_health.values()
        ) / total_modules if total_modules > 0 else 0
        
        return {
            "overall_status": "healthy" if operational_modules == total_modules else "degraded",
            "operational_modules": operational_modules,
            "total_modules": total_modules,
            "average_performance": average_performance,
            "uptime_hours": (datetime.now() - self.startup_time).total_seconds() / 3600,
            "last_health_check": datetime.now().isoformat()
        }
    
    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get list of active system alerts"""
        alerts = []
        
        for module, health in self.system_health.items():
            if health.status != SystemStatus.OPERATIONAL:
                alerts.append({
                    "module": module.value,
                    "status": health.status.value,
                    "performance": health.performance_score,
                    "error_count": health.error_count,
                    "warnings": health.warnings,
                    "last_check": health.last_check.isoformat()
                })
        
        return alerts
    
    def get_current_performance_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics"""
        return {
            "average_response_time": sum(self.performance_trackers["request_processing_time"][-10:]) / 
                                   max(len(self.performance_trackers["request_processing_time"][-10:]), 1),
            "total_requests_processed": len(self.performance_trackers["request_processing_time"]),
            "system_uptime_hours": (datetime.now() - self.startup_time).total_seconds() / 3600,
            "integration_level": self.integration_level.value,
            "active_sessions": len(self.active_sessions),
            "memory_usage_mb": self.get_memory_usage()
        }
    
    def get_memory_usage(self) -> float:
        """Get current memory usage (simplified implementation)"""
        # In real implementation, would use psutil or similar
        return len(self.conversation_contexts) * 0.1  # Simplified estimate
    
    async def get_comprehensive_dashboard(self) -> Dict[str, Any]:
        """Get comprehensive system dashboard data"""
        return {
            "system_overview": {
                "integration_level": self.integration_level.value,
                "startup_time": self.startup_time.isoformat(),
                "system_id": self.system_id,
                "version": "2.0.0"
            },
            
            "health_status": self.get_system_health_summary(),
            
            "active_alerts": self.get_active_alerts(),
            
            "performance_metrics": self.get_current_performance_metrics(),
            
            "module_status": {
                module.value: {
                    "status": health.status.value,
                    "performance": health.performance_score,
                    "last_check": health.last_check.isoformat()
                }
                for module, health in self.system_health.items()
            },
            
            "recent_activity": {
                "total_requests_today": len(self.performance_trackers["request_processing_time"]),
                "average_response_time": self.get_current_performance_metrics()["average_response_time"],
                "error_rate": len([h for h in self.system_health.values() if h.error_count > 0]) / len(self.system_health)
            },
            
            "predictive_insights": await self.get_predictive_dashboard_data(),
            
            "timestamp": datetime.now().isoformat()
        }
    
    async def get_predictive_dashboard_data(self) -> Dict[str, Any]:
        """Get predictive analytics data for dashboard"""
        try:
            # Get key predictions for dashboard
            from .predictive_analytics_agent import PredictionType, ForecastHorizon
            
            bed_forecast = await self.predictive_system.run_prediction(
                PredictionType.BED_DEMAND, ForecastHorizon.DAILY, 7
            )
            
            return {
                "bed_demand_forecast": {
                    "next_7_days": bed_forecast.predictions[:7],
                    "confidence": bed_forecast.confidence_score,
                    "key_insights": bed_forecast.recommendations[:3]
                },
                "system_recommendations": [
                    "Monitor bed capacity closely for next 3 days",
                    "Consider staff scheduling adjustments",
                    "Review supply inventory levels"
                ]
            }
            
        except Exception as e:
            self.logger.error(f"Error getting predictive dashboard data: {e}")
            return {"error": "Predictive data unavailable"}
    
    def shutdown(self):
        """Gracefully shutdown the master system"""
        self.logger.info("Shutting down Master Hospital Management System...")
        
        # Update all module statuses
        for module in self.system_health:
            self.system_health[module].status = SystemStatus.OFFLINE
        
        # Save any pending data
        # In real implementation, would persist important state
        
        self.logger.info("Master system shutdown completed")
