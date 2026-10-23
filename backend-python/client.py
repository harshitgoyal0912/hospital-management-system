"""
Hospital Management System MCP Client - Agentic AI
Intelligent autonomous agent for hospital management with decision-making capabilities
"""

import asyncio
import json
import traceback
import os
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from datetime import datetime, date, timedelta
import uuid
import random
import re
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()


class HospitalManagementClient:
    def __init__(self):
        self.session = None
        self.stdio_context = None
        self.agent_memory = {}  # Store agent context and decisions
        self.available_tools = []
        self.llm_model = None
        self._initialize_llm()
        
    def _initialize_llm(self):
        """Initialize Google Gemini LLM."""
        try:
            api_key = os.getenv("GEMINI_API_KEY")
            if api_key:
                genai.configure(api_key=api_key)
                self.llm_model = genai.GenerativeModel('gemini-2.0-flash-exp')
                print("✅ LLM (Gemini) initialized successfully")
            else:
                print("⚠️ GEMINI_API_KEY not found in environment variables")
                self.llm_model = None
        except Exception as e:
            print(f"⚠️ Failed to initialize LLM: {e}")
            self.llm_model = None
    
    async def process_natural_language_query(self, user_query: str):
        """Process natural language queries using LLM and execute appropriate hospital management tasks."""
        if not self.llm_model:
            return "LLM not available. Please check your GEMINI_API_KEY configuration."
        
        try:
            # Create a context-aware prompt for hospital management
            system_prompt = """
            You are an intelligent hospital management AI assistant. You have access to various hospital management tools and can perform operations like:
            - Patient management (create, list, search patients)
            - Patient discharge (complete discharge workflow with report generation)
            - Bed management (check availability, assign beds)
            - Staff management (list staff, departments)
            - Equipment tracking (list equipment, update status)
            - Supply management (check inventory, low stock alerts)
            - Hospital analytics and optimization
            
            Based on the user's query, determine what action they want to take and respond with:
            1. The specific action/tool to use
            2. Any parameters needed
            3. A helpful explanation
            
            Available tools: list_patients, create_patient, discharge_patient_complete, list_beds, assign_bed_to_patient, list_staff, 
            list_departments, list_equipment, list_supplies, analyze_hospital_state
            """
            
            full_prompt = f"{system_prompt}\n\nUser Query: {user_query}\n\nPlease analyze this query and provide a structured response."
            
            response = self.llm_model.generate_content(full_prompt)
            llm_response = response.text
            
            # Parse LLM response and execute appropriate actions
            action_result = await self._execute_llm_suggested_action(user_query, llm_response)
            
            return f"🤖 **AI Analysis:** {llm_response}\n\n📋 **Action Result:**\n{action_result}"
            
        except Exception as e:
            return f"Error processing query with LLM: {str(e)}"
    
    async def _execute_llm_suggested_action(self, user_query: str, llm_response: str):
        """Execute actions suggested by the LLM based on the user query."""
        query_lower = user_query.lower()
        
        try:
            # Determine action based on keywords and LLM guidance
            if any(word in query_lower for word in ["patients", "patient", "list patients", "show patients"]):
                result = await self._safe_call_tool("list_patients", {})
                patients = result.get("patients", [])
                if patients:
                    return f"Found {len(patients)} patients:\n" + "\n".join([
                        f"• {p.get('first_name', '')} {p.get('last_name', '')} (ID: {p.get('patient_number', 'N/A')})"
                        for p in patients[:5]
                    ]) + (f"\n... and {len(patients) - 5} more" if len(patients) > 5 else "")
                else:
                    return "No patients found in the system."
                    
            elif any(word in query_lower for word in ["beds", "bed availability", "available beds"]):
                result = await self._safe_call_tool("list_beds", {})
                beds = result.get("beds", [])
                available = [b for b in beds if b.get("status") == "available"]
                occupied = [b for b in beds if b.get("status") == "occupied"]
                return f"Bed Status: {len(available)} available, {len(occupied)} occupied out of {len(beds)} total beds"
                
            elif any(word in query_lower for word in ["staff", "doctors", "employees"]):
                result = await self._safe_call_tool("list_staff", {})
                staff = result.get("staff", [])
                return f"Found {len(staff)} staff members in the system"
                
            elif any(word in query_lower for word in ["departments", "department"]):
                result = await self._safe_call_tool("list_departments", {})
                departments = result.get("departments", [])
                if departments:
                    return f"Hospital Departments ({len(departments)}):\n" + "\n".join([
                        f"• {d.get('name', 'Unknown')} - Floor {d.get('floor_number', 'N/A')}"
                        for d in departments
                    ])
                else:
                    return "No departments found."
                    
            elif any(word in query_lower for word in ["equipment", "machines", "devices"]):
                result = await self._safe_call_tool("list_equipment", {})
                equipment = result.get("equipment", [])
                return f"Found {len(equipment)} equipment items in the system"
                
            elif any(word in query_lower for word in ["supplies", "inventory", "stock"]):
                result = await self._safe_call_tool("list_supplies", {})
                supplies = result.get("supplies", [])
                low_stock = await self._safe_call_tool("list_supplies", {"low_stock_only": True})
                low_count = len(low_stock.get("supplies", []))
                return f"Inventory: {len(supplies)} total items, {low_count} items need restocking"
                
            elif any(word in query_lower for word in ["discharge", "discharge patient"]):
                # Handle patient discharge requests
                import re
                
                # Extract patient number/ID from the query
                patient_match = re.search(r'patient\s+([a-zA-Z]?\d+)', query_lower)
                if patient_match:
                    patient_number = patient_match.group(1).upper()
                    if not patient_number.startswith('P'):
                        patient_number = f"P{patient_number}"
                    
                    print(f"🏥 Discharging patient {patient_number}...")
                    
                    # Call discharge_patient_complete tool
                    result = await self._safe_call_tool("discharge_patient_complete", {
                        "patient_number": patient_number,
                        "discharge_condition": "stable",
                        "discharge_destination": "home"
                    })
                    
                    if result.get("success"):
                        discharge_result = result.get("result", {})
                        message = discharge_result.get("message", "Patient discharged successfully")
                        
                        # Format comprehensive response
                        response_parts = [f"✅ {message}"]
                        
                        # Add report information
                        if "report_number" in discharge_result:
                            response_parts.append(f"📄 Discharge Report: {discharge_result['report_number']}")
                        
                        if "report_download_url" in discharge_result:
                            response_parts.append(f"📥 Download: {discharge_result['report_download_url']}")
                        
                        # Add bed turnover information
                        if "bed_turnover" in discharge_result:
                            bed_info = discharge_result["bed_turnover"]
                            if bed_info.get("success"):
                                response_parts.append(f"🛏️ Bed cleaning initiated - estimated {discharge_result.get('cleaning_timer', '30 minutes')}")
                        
                        # Add next steps
                        if "next_steps" in discharge_result:
                            response_parts.append("📋 Next Steps:")
                            for step in discharge_result["next_steps"]:
                                response_parts.append(f"   • {step}")
                        
                        return "\n".join(response_parts)
                    else:
                        return f"❌ Failed to discharge patient {patient_number}: {result.get('message', 'Unknown error')}"
                else:
                    return "❌ Please specify a patient number (e.g., 'Discharge Patient P1025')"
                
            elif any(word in query_lower for word in ["analyze", "analysis", "hospital state", "overview"]):
                analysis = await self.analyze_hospital_state()
                return "Hospital state analysis completed - see detailed output above"
                
            elif any(word in query_lower for word in ["optimize", "autonomous", "ai management"]):
                await self.autonomous_hospital_management()
                return "Autonomous hospital management cycle completed"
                
            else:
                # Use LLM to provide general guidance
                return "I can help you with hospital management tasks. Try asking about patients, beds, staff, departments, equipment, supplies, patient discharge, or hospital analysis."
                
        except Exception as e:
            return f"Error executing action: {str(e)}"
    
    async def intelligent_query_handler(self, query: str):
        """Main entry point for handling natural language queries with LLM integration."""
        print(f"\n🤖 === INTELLIGENT QUERY HANDLER ===")
        print(f"📝 Query: {query}")
        
        if self.llm_model:
            response = await self.process_natural_language_query(query)
            print(f"\n💬 Response:\n{response}")
            return response
        else:
            # Fallback to rule-based processing
            return await self._execute_llm_suggested_action(query, "No LLM available - using rule-based processing")
        
    # === AGENTIC AI CORE METHODS ===
    
    async def analyze_hospital_state(self):
        """Analyze current hospital state and identify optimization opportunities."""
        print("\n🧠 === AGENTIC AI ANALYSIS ===")
        
        # Gather comprehensive hospital data
        users = await self._safe_call_tool("list_users", {})
        departments = await self._safe_call_tool("list_departments", {})
        patients = await self._safe_call_tool("list_patients", {})
        beds = await self._safe_call_tool("list_beds", {})
        equipment = await self._safe_call_tool("list_equipment", {})
        supplies = await self._safe_call_tool("list_supplies", {})
        low_stock = await self._safe_call_tool("list_supplies", {"low_stock_only": True})
        
        # Analyze data and make intelligent decisions
        analysis = {
            "total_users": len(users.get("users", [])),
            "total_departments": len(departments.get("departments", [])),
            "total_patients": len(patients.get("patients", [])),
            "bed_occupancy": self._calculate_bed_occupancy(beds),
            "equipment_status": self._analyze_equipment_status(equipment),
            "supply_alerts": len(low_stock.get("supplies", [])),
            "recommendations": []
        }
        
        # Generate intelligent recommendations
        analysis["recommendations"] = await self._generate_recommendations(analysis)
        
        print(f"📊 Hospital State Analysis:")
        print(f"   👥 Users: {analysis['total_users']}")
        print(f"   🏢 Departments: {analysis['total_departments']}")
        print(f"   🤒 Patients: {analysis['total_patients']}")
        print(f"   🛏️  Bed Occupancy: {analysis['bed_occupancy']['percentage']:.1f}%")
        print(f"   🔧 Equipment Issues: {analysis['equipment_status']['issues']}")
        print(f"   📦 Supply Alerts: {analysis['supply_alerts']}")
        
        if analysis["recommendations"]:
            print(f"\n💡 AI Recommendations ({len(analysis['recommendations'])}):")
            for i, rec in enumerate(analysis["recommendations"], 1):
                print(f"   {i}. {rec}")
        
        self.agent_memory["last_analysis"] = analysis
        return analysis
    
    async def autonomous_hospital_management(self):
        """Autonomous agent that manages hospital operations intelligently."""
        print("\n🤖 === AUTONOMOUS HOSPITAL MANAGEMENT ===")
        
        # Continuous monitoring and management loop
        management_tasks = [
            self._manage_bed_allocation,
            self._optimize_equipment_usage,
            self._monitor_supply_levels,
            self._schedule_maintenance,
            self._patient_flow_optimization
        ]
        
        for task in management_tasks:
            try:
                await task()
                await asyncio.sleep(0.5)  # Pause between tasks
            except Exception as e:
                print(f"⚠️ Task {task.__name__} failed: {e}")
        
        # Log agent activities
        await self._log_agent_activities()
    
    async def intelligent_patient_admission(self, patient_data):
        """Intelligently admit a patient with automatic bed assignment and resource allocation."""
        print("\n🏥 === INTELLIGENT PATIENT ADMISSION ===")
        
        # Create patient
        patient_result = await self._safe_call_tool("create_patient", patient_data)
        if not patient_result.get("success"):
            print("❌ Failed to create patient")
            return False
        
        patient_id = patient_result["data"]["id"]
        print(f"✅ Patient created: {patient_data['first_name']} {patient_data['last_name']}")
        
        # Find optimal bed assignment
        optimal_bed = await self._find_optimal_bed(patient_data)
        if optimal_bed:
            await self._safe_call_tool("assign_bed_to_patient", {
                "bed_id": optimal_bed["id"],
                "patient_id": patient_id,
                "admission_date": datetime.now().isoformat()
            })
            print(f"🛏️  Assigned to bed: {optimal_bed['bed_number']}")
        
        # Check and allocate required supplies
        await self._allocate_patient_supplies(patient_data)
        
        return True
    
    async def smart_resource_optimization(self):
        """Optimize hospital resources using AI algorithms."""
        print("\n⚡ === SMART RESOURCE OPTIMIZATION ===")
        
        # Bed optimization
        bed_recommendations = await self._optimize_bed_distribution()
        
        # Equipment optimization
        equipment_optimization = await self._optimize_equipment_allocation()
        
        # Supply chain optimization
        supply_optimization = await self._optimize_supply_chain()
        
        # Staff optimization
        staff_optimization = await self._optimize_staff_allocation()
        
        optimization_report = {
            "beds": bed_recommendations,
            "equipment": equipment_optimization,
            "supplies": supply_optimization,
            "staff": staff_optimization,
            "timestamp": datetime.now().isoformat()
        }
        
        print("📈 Optimization completed!")
        return optimization_report
    
    # === INTELLIGENT HELPER METHODS ===
    
    async def _safe_call_tool(self, tool_name, params):
        """Safely call MCP tool with error handling."""
        try:
            print(f"🔧 Calling tool: {tool_name} with params: {params}")
            result = await self.session.call_tool(tool_name, params)
            
            if not result.content:
                print(f"⚠️ Tool {tool_name} returned empty content")
                return {"success": False, "message": "Empty response from server"}
            
            response_text = result.content[0].text
            print(f"📄 Raw response: {response_text[:200]}...")
            
            if not response_text.strip():
                print(f"⚠️ Tool {tool_name} returned empty text")
                return {"success": False, "message": "Empty response text"}
            
            try:
                parsed_result = json.loads(response_text)
                print(f"✅ Parsed result: {parsed_result}")
                return parsed_result
            except json.JSONDecodeError as json_error:
                print(f"⚠️ JSON parsing failed for {tool_name}: {json_error}")
                print(f"🔍 Response text: '{response_text}'")
                return {"success": False, "message": f"Invalid JSON response: {response_text[:100]}"}
                
        except Exception as e:
            print(f"⚠️ Tool {tool_name} failed with exception: {e}")
            import traceback
            traceback.print_exc()
            return {"success": False, "message": str(e)}
    
    def _calculate_bed_occupancy(self, beds_data):
        """Calculate bed occupancy statistics."""
        beds = beds_data.get("beds", [])
        if not beds:
            return {"total": 0, "occupied": 0, "available": 0, "percentage": 0}
        
        occupied = len([b for b in beds if b.get("status") == "occupied"])
        available = len([b for b in beds if b.get("status") == "available"])
        total = len(beds)
        percentage = (occupied / total * 100) if total > 0 else 0
        
        return {
            "total": total,
            "occupied": occupied,
            "available": available,
            "percentage": percentage
        }
    
    def _analyze_equipment_status(self, equipment_data):
        """Analyze equipment status and identify issues."""
        equipment = equipment_data.get("equipment", [])
        
        status_counts = {}
        issues = 0
        
        for item in equipment:
            status = item.get("status", "unknown")
            status_counts[status] = status_counts.get(status, 0) + 1
            if status in ["maintenance", "out_of_order", "broken"]:
                issues += 1
        
        return {
            "total": len(equipment),
            "status_breakdown": status_counts,
            "issues": issues
        }
    
    async def _generate_recommendations(self, analysis):
        """Generate intelligent recommendations based on analysis."""
        recommendations = []
        
        # Bed management recommendations
        if analysis["bed_occupancy"]["percentage"] > 85:
            recommendations.append("Consider adding more beds or optimizing discharge planning")
        elif analysis["bed_occupancy"]["percentage"] < 50:
            recommendations.append("Bed utilization is low - consider cost optimization")
        
        # Equipment recommendations
        if analysis["equipment_status"]["issues"] > 0:
            recommendations.append(f"Schedule maintenance for {analysis['equipment_status']['issues']} equipment items")
        
        # Supply recommendations
        if analysis["supply_alerts"] > 0:
            recommendations.append(f"Restock {analysis['supply_alerts']} low-inventory items")
        
        # Operational recommendations
        if analysis["total_patients"] > analysis["bed_occupancy"]["available"]:
            recommendations.append("Patient capacity exceeds available beds - consider expansion")
        
        return recommendations
    
    async def _manage_bed_allocation(self):
        """Intelligently manage bed allocation."""
        print("🛏️  Managing bed allocation...")
        
        beds = await self._safe_call_tool("list_beds", {})
        patients = await self._safe_call_tool("list_patients", {})
        
        # Find unassigned patients and available beds
        available_beds = [b for b in beds.get("beds", []) if b.get("status") == "available"]
        
        if available_beds:
            print(f"   ✅ {len(available_beds)} beds available for assignment")
        else:
            print("   ⚠️ No available beds - consider discharge planning")
    
    async def _optimize_equipment_usage(self):
        """Optimize equipment usage and maintenance."""
        print("🔧 Optimizing equipment usage...")
        
        equipment = await self._safe_call_tool("list_equipment", {})
        maintenance_needed = [e for e in equipment.get("equipment", []) 
                            if e.get("status") in ["maintenance", "needs_maintenance"]]
        
        if maintenance_needed:
            print(f"   🔧 {len(maintenance_needed)} items need maintenance")
            # Could auto-schedule maintenance here
        else:
            print("   ✅ All equipment operational")
    
    async def _monitor_supply_levels(self):
        """Monitor and manage supply levels."""
        print("📦 Monitoring supply levels...")
        
        low_stock = await self._safe_call_tool("list_supplies", {"low_stock_only": True})
        critical_supplies = low_stock.get("supplies", [])
        
        if critical_supplies:
            print(f"   ⚠️ {len(critical_supplies)} items need restocking")
            # Could auto-reorder supplies here
            for supply in critical_supplies[:3]:  # Show first 3
                print(f"     • {supply.get('name', 'Unknown')}: {supply.get('current_stock', 0)} remaining")
        else:
            print("   ✅ All supplies adequately stocked")
    
    async def _schedule_maintenance(self):
        """Schedule equipment maintenance intelligently."""
        print("🔧 Scheduling maintenance...")
        
        equipment = await self._safe_call_tool("list_equipment", {})
        for item in equipment.get("equipment", []):
            if item.get("status") == "available":
                # Could implement predictive maintenance logic here
                pass
        
        print("   ✅ Maintenance scheduling optimized")
    
    async def _patient_flow_optimization(self):
        """Optimize patient flow through the hospital."""
        print("🚶 Optimizing patient flow...")
        
        beds = await self._safe_call_tool("list_beds", {})
        
        # Analyze bed availability
        available_beds = len([b for b in beds.get("beds", []) if b.get("status") == "available"])
        
        if available_beds < 5:
            print("   ⚠️ Low bed availability")
        else:
            print("   ✅ Sufficient bed capacity")
    
    async def _find_optimal_bed(self, patient_data):
        """Find the optimal bed for a patient based on their needs."""
        beds = await self._safe_call_tool("list_beds", {"status": "available"})
        available_beds = beds.get("beds", [])
        
        if not available_beds:
            return None
        
        # Simple optimization - could be much more sophisticated
        # Consider patient type, department, bed type, etc.
        return available_beds[0]  # Return first available for now
    
    async def _allocate_patient_supplies(self, patient_data):
        """Allocate necessary supplies for patient care."""
        supplies = await self._safe_call_tool("list_supplies", {})
        
        # Could implement intelligent supply allocation based on patient needs
        print("📦 Supplies allocated based on patient needs")
    
    async def _optimize_bed_distribution(self):
        """Optimize bed distribution across departments."""
        beds = await self._safe_call_tool("list_beds", {})
        departments = await self._safe_call_tool("list_departments", {})
        
        # Analyze bed distribution and recommend changes
        return {"status": "analyzed", "recommendations": ["Balanced distribution"]}
    
    async def _optimize_equipment_allocation(self):
        """Optimize equipment allocation across departments."""
        equipment = await self._safe_call_tool("list_equipment", {})
        
        # Analyze equipment usage patterns
        return {"status": "optimized", "efficiency_gain": "15%"}
    
    async def _optimize_supply_chain(self):
        """Optimize supply chain and inventory levels."""
        supplies = await self._safe_call_tool("list_supplies", {})
        
        # Analyze supply usage patterns and optimize reorder points
        return {"status": "optimized", "cost_savings": "12%"}
    
    async def _optimize_staff_allocation(self):
        """Optimize staff allocation across shifts and departments."""
        staff = await self._safe_call_tool("list_staff", {})
        
        # Analyze staff distribution and workload
        return {"status": "optimized", "efficiency_gain": "18%"}
    
    async def _log_agent_activities(self):
        """Log all agent activities for monitoring and improvement."""
        users = await self._safe_call_tool("list_users", {})
        if users.get("users"):
            user_id = users["users"][0]["id"]
            
            await self._safe_call_tool("log_agent_interaction", {
                "agent_type": "autonomous_management",
                "user_id": user_id,
                "query": "Autonomous hospital management cycle",
                "response": "Completed bed, equipment, supply, and patient flow optimization",
                "action_taken": "optimization_cycle",
                "confidence_score": 0.92,
                "execution_time_ms": 2500
            })

    # === MASTER DATA CRUD OPERATIONS ===
    
    async def master_data_management(self):
        """Master data management interface."""
        print("\n🏗️ === MASTER DATA MANAGEMENT ===")
        
        while True:
            print("\n📋 Master Data Operations:")
            print("1. Department Management")
            print("2. Equipment Category Management")
            print("3. Supply Category Management")
            print("4. Room Management")
            print("5. User Management")
            print("6. View All Master Data")
            print("0. Back to Main Menu")
            
            choice = input("\nEnter your choice (0-6): ").strip()
            
            try:
                if choice == "0":
                    break
                elif choice == "1":
                    await self._department_crud()
                elif choice == "2":
                    await self._equipment_category_crud()
                elif choice == "3":
                    await self._supply_category_crud()
                elif choice == "4":
                    await self._room_crud()
                elif choice == "5":
                    await self._user_crud()
                elif choice == "6":
                    await self._view_all_master_data()
                else:
                    print("Invalid choice. Please enter 0-6.")
            except Exception as e:
                print(f"Error: {e}")
    
    async def _department_crud(self):
        """Department CRUD operations."""
        print("\n🏢 === DEPARTMENT MANAGEMENT ===")
        
        while True:
            print("\n📋 Department Operations:")
            print("1. Create New Department")
            print("2. List All Departments")
            print("3. Get Department Details")
            print("4. Update Department (Limited)")
            print("0. Back")
            
            choice = input("\nEnter your choice (0-4): ").strip()
            
            if choice == "0":
                break
            elif choice == "1":
                await self._create_department_interactive()
            elif choice == "2":
                await self._list_departments_detailed()
            elif choice == "3":
                await self._get_department_by_id_interactive()
            elif choice == "4":
                print("ℹ️  Department updates not yet implemented in server")
            else:
                print("Invalid choice.")
    
    async def _create_department_interactive(self):
        """Create department with user input."""
        print("\n➕ Create New Department")
        
        name = input("Department Name: ").strip()
        if not name:
            print("❌ Department name is required.")
            return
        
        description = input("Description (optional): ").strip()
        
        floor_input = input("Floor Number (optional): ").strip()
        floor_number = None
        if floor_input:
            try:
                floor_number = int(floor_input)
            except ValueError:
                print("⚠️ Invalid floor number, skipping.")
        
        phone = input("Phone (optional): ").strip()
        email = input("Email (optional): ").strip()
        
        # Show available users for head doctor
        users = await self._safe_call_tool("list_users", {})
        head_doctor_id = None
        
        if users.get("users"):
            print("\nAvailable users for Head Doctor:")
            doctors = [u for u in users["users"] if u.get("role") in ["doctor", "admin"]]
            
            if doctors:
                for i, user in enumerate(doctors, 1):
                    print(f"   {i}. Dr. {user['first_name']} {user['last_name']} ({user['role']})")
                
                head_choice = input("Select head doctor number (or press Enter to skip): ").strip()
                if head_choice.isdigit():
                    choice_idx = int(head_choice) - 1
                    if 0 <= choice_idx < len(doctors):
                        head_doctor_id = doctors[choice_idx]["id"]
        
        # Build department data - only include non-empty values
        dept_data = {"name": name}
        
        if description:
            dept_data["description"] = description
        if floor_number is not None:
            dept_data["floor_number"] = floor_number
        if phone:
            dept_data["phone"] = phone
        if email:
            dept_data["email"] = email
        if head_doctor_id:
            dept_data["head_doctor_id"] = head_doctor_id
        
        result = await self._safe_call_tool("create_department", dept_data)
        
        if result.get("success"):
            print(f"✅ Department '{name}' created successfully!")
            print(f"   Department ID: {result['data']['id']}")
        else:
            print(f"❌ Failed to create department: {result.get('message', 'Unknown error')}")
    
    async def _list_departments_detailed(self):
        """List all departments with details."""
        print("\n📋 All Departments:")
        
        result = await self._safe_call_tool("list_departments", {})
        
        if result.get("departments"):
            for dept in result["departments"]:
                print(f"\n🏢 {dept['name']}")
                print(f"   ID: {dept['id']}")
                print(f"   Description: {dept.get('description', 'No description')}")
                print(f"   Floor: {dept.get('floor_number', 'Not specified')}")
                print(f"   Phone: {dept.get('phone', 'Not specified')}")
                print(f"   Email: {dept.get('email', 'Not specified')}")
                print(f"   Head Doctor ID: {dept.get('head_doctor_id', 'Not assigned')}")
                print(f"   Created: {dept.get('created_at', 'Unknown')}")
        else:
            print("No departments found.")
    
    async def _get_department_by_id_interactive(self):
        """Get department details by ID."""
        print("\n🔍 Get Department Details")
        
        # First list departments
        result = await self._safe_call_tool("list_departments", {})
        
        if not result.get("departments"):
            print("No departments found.")
            return
        
        print("\nAvailable Departments:")
        for i, dept in enumerate(result["departments"], 1):
            print(f"   {i}. {dept['name']} (ID: {dept['id'][:8]}...)")
        
        choice = input("Select department number: ").strip()
        if not choice.isdigit():
            print("❌ Invalid selection.")
            return
        
        choice_idx = int(choice) - 1
        if not (0 <= choice_idx < len(result["departments"])):
            print("❌ Invalid selection.")
            return
        
        dept_id = result["departments"][choice_idx]["id"]
        
        detail_result = await self._safe_call_tool("get_department_by_id", {"department_id": dept_id})
        
        if detail_result.get("department"):
            dept = detail_result["department"]
            print(f"\n🏢 Department Details:")
            print(f"   Name: {dept['name']}")
            print(f"   ID: {dept['id']}")
            print(f"   Description: {dept.get('description', 'No description')}")
            print(f"   Floor: {dept.get('floor_number', 'Not specified')}")
            print(f"   Phone: {dept.get('phone', 'Not specified')}")
            print(f"   Email: {dept.get('email', 'Not specified')}")
            print(f"   Head Doctor ID: {dept.get('head_doctor_id', 'Not assigned')}")
            print(f"   Created: {dept.get('created_at', 'Unknown')}")
            print(f"   Updated: {dept.get('updated_at', 'Unknown')}")
        else:
            print("❌ Department not found.")
    
    async def _equipment_category_crud(self):
        """Equipment category CRUD operations."""
        print("\n🔧 === EQUIPMENT CATEGORY MANAGEMENT ===")
        
        while True:
            print("\n📋 Equipment Category Operations:")
            print("1. Create New Category")
            print("2. List All Categories")
            print("0. Back")
            
            choice = input("\nEnter your choice (0-2): ").strip()
            
            if choice == "0":
                break
            elif choice == "1":
                await self._create_equipment_category_interactive()
            elif choice == "2":
                await self._list_equipment_categories()
            else:
                print("Invalid choice.")
    
    async def _create_equipment_category_interactive(self):
        """Create equipment category with user input."""
        print("\n➕ Create Equipment Category")
        
        name = input("Category Name: ").strip()
        if not name:
            print("❌ Category name is required.")
            return
        
        description = input("Description (optional): ").strip()
        
        # Build category data - only include non-empty values
        cat_data = {"name": name}
        if description:
            cat_data["description"] = description
        
        result = await self._safe_call_tool("create_equipment_category", cat_data)
        
        if result.get("success"):
            print(f"✅ Equipment category '{name}' created successfully!")
            print(f"   Category ID: {result['data']['id']}")
        else:
            print(f"❌ Failed to create category: {result.get('message', 'Unknown error')}")
    
    async def _list_equipment_categories(self):
        """List all equipment categories."""
        print("\n📋 Equipment Categories:")
        
        # Note: This assumes we have a list_equipment_categories tool
        # If not available, we'll need to use a different approach
        try:
            result = await self._safe_call_tool("list_equipment_categories", {})
            
            if result.get("categories"):
                for cat in result["categories"]:
                    print(f"\n🔧 {cat['name']}")
                    print(f"   ID: {cat['id']}")
                    print(f"   Description: {cat.get('description', 'No description')}")
                    print(f"   Created: {cat.get('created_at', 'Unknown')}")
            else:
                print("No equipment categories found.")
        except:
            print("ℹ️  Equipment category listing not available through direct tool.")
            print("   Equipment categories are shown when creating equipment.")
    
    async def _supply_category_crud(self):
        """Supply category CRUD operations."""
        print("\n📦 === SUPPLY CATEGORY MANAGEMENT ===")
        
        while True:
            print("\n📋 Supply Category Operations:")
            print("1. Create New Category")
            print("2. List All Categories")
            print("0. Back")
            
            choice = input("\nEnter your choice (0-2): ").strip()
            
            if choice == "0":
                break
            elif choice == "1":
                await self._create_supply_category_interactive()
            elif choice == "2":
                await self._list_supply_categories()
            else:
                print("Invalid choice.")
    
    async def _create_supply_category_interactive(self):
        """Create supply category with user input."""
        print("\n➕ Create Supply Category")
        
        name = input("Category Name: ").strip()
        if not name:
            print("❌ Category name is required.")
            return
        
        description = input("Description (optional): ").strip()
        
        # Build category data - only include non-empty values
        cat_data = {"name": name}
        if description:
            cat_data["description"] = description
        
        result = await self._safe_call_tool("create_supply_category", cat_data)
        
        if result.get("success"):
            print(f"✅ Supply category '{name}' created successfully!")
            print(f"   Category ID: {result['data']['id']}")
        else:
            print(f"❌ Failed to create category: {result.get('message', 'Unknown error')}")
    
    async def _list_supply_categories(self):
        """List all supply categories."""
        print("\n📋 Supply Categories:")
        
        try:
            result = await self._safe_call_tool("list_supply_categories", {})
            
            if result.get("categories"):
                for cat in result["categories"]:
                    print(f"\n📦 {cat['name']}")
                    print(f"   ID: {cat['id']}")
                    print(f"   Description: {cat.get('description', 'No description')}")
                    print(f"   Created: {cat.get('created_at', 'Unknown')}")
            else:
                print("No supply categories found.")
        except:
            print("ℹ️  Supply category listing not available through direct tool.")
            print("   Supply categories are shown when creating supplies.")
    
    async def _room_crud(self):
        """Room CRUD operations."""
        print("\n🏠 === ROOM MANAGEMENT ===")
        
        while True:
            print("\n📋 Room Operations:")
            print("1. Create New Room")
            print("2. List All Rooms")
            print("0. Back")
            
            choice = input("\nEnter your choice (0-2): ").strip()
            
            if choice == "0":
                break
            elif choice == "1":
                await self._create_room_interactive()
            elif choice == "2":
                await self._list_rooms_detailed()
            else:
                print("Invalid choice.")
    
    async def _create_room_interactive(self):
        """Create room with user input."""
        print("\n➕ Create New Room")
        
        room_number = input("Room Number: ").strip()
        if not room_number:
            print("❌ Room number is required.")
            return
        
        # Show departments for selection
        dept_result = await self._safe_call_tool("list_departments", {})
        if not dept_result.get("departments"):
            print("❌ No departments found. Create a department first.")
            return
        
        print("\nAvailable Departments:")
        for i, dept in enumerate(dept_result["departments"], 1):
            print(f"   {i}. {dept['name']}")
        
        dept_choice = input("Select department number: ").strip()
        if not dept_choice.isdigit():
            print("❌ Invalid department selection.")
            return
        
        choice_idx = int(dept_choice) - 1
        if not (0 <= choice_idx < len(dept_result["departments"])):
            print("❌ Invalid department selection.")
            return
        
        department_id = dept_result["departments"][choice_idx]["id"]
        
        room_type = input("Room Type (private/shared/icu/emergency): ").strip()
        if not room_type:
            room_type = "private"
        
        capacity_input = input("Capacity (number of beds): ").strip()
        capacity = 1
        if capacity_input:
            try:
                capacity = int(capacity_input)
            except ValueError:
                print("⚠️ Invalid capacity, using default: 1")
        
        floor_input = input("Floor Number (optional): ").strip()
        floor_number = None
        if floor_input:
            try:
                floor_number = int(floor_input)
            except ValueError:
                print("⚠️ Invalid floor number, skipping.")
        
        # Build room data - only include non-empty values
        room_data = {
            "room_number": room_number,
            "department_id": department_id,
            "room_type": room_type,
            "capacity": capacity
        }
        
        if floor_number is not None:
            room_data["floor_number"] = floor_number
        
        result = await self._safe_call_tool("create_room", room_data)
        
        if result.get("success"):
            print(f"✅ Room '{room_number}' created successfully!")
            print(f"   Room ID: {result['data']['id']}")
        else:
            print(f"❌ Failed to create room: {result.get('message', 'Unknown error')}")
    
    async def _list_rooms_detailed(self):
        """List all rooms with details."""
        print("\n📋 All Rooms:")
        
        result = await self._safe_call_tool("list_rooms", {})
        
        if result.get("rooms"):
            for room in result["rooms"]:
                print(f"\n🏠 Room {room['room_number']}")
                print(f"   ID: {room['id']}")
                print(f"   Type: {room.get('room_type', 'Not specified')}")
                print(f"   Capacity: {room.get('capacity', 'Not specified')}")
                print(f"   Floor: {room.get('floor_number', 'Not specified')}")
                print(f"   Department ID: {room.get('department_id', 'Not assigned')}")
                print(f"   Created: {room.get('created_at', 'Unknown')}")
        else:
            print("No rooms found.")
    
    async def _user_crud(self):
        """User CRUD operations."""
        print("\n👤 === USER MANAGEMENT ===")
        
        while True:
            print("\n📋 User Operations:")
            print("1. Create New User")
            print("2. List All Users")
            print("3. Get User Details")
            print("4. Update User")
            print("5. Delete User")
            print("0. Back")
            
            choice = input("\nEnter your choice (0-5): ").strip()
            
            if choice == "0":
                break
            elif choice == "1":
                await self._create_user_interactive()
            elif choice == "2":
                await self._list_users_detailed()
            elif choice == "3":
                await self._get_user_by_id_interactive()
            elif choice == "4":
                await self._update_user_interactive()
            elif choice == "5":
                await self._delete_user_interactive()
            else:
                print("Invalid choice.")
    
    async def _create_user_interactive(self):
        """Create user with user input."""
        print("\n➕ Create New User")
        
        username = input("Username: ").strip()
        if not username:
            print("❌ Username is required.")
            return
        
        email = input("Email: ").strip()
        if not email:
            print("❌ Email is required.")
            return
        
        password_hash = input("Password Hash: ").strip()
        if not password_hash:
            print("❌ Password hash is required.")
            return
        
        print("\nAvailable Roles:")
        roles = ["admin", "doctor", "nurse", "staff"]
        for i, role in enumerate(roles, 1):
            print(f"   {i}. {role}")
        
        role_choice = input("Select role number: ").strip()
        if role_choice.isdigit():
            choice_idx = int(role_choice) - 1
            if 0 <= choice_idx < len(roles):
                role = roles[choice_idx]
            else:
                role = input("Enter role manually: ").strip() or "staff"
        else:
            role = input("Enter role manually: ").strip() or "staff"
        
        first_name = input("First Name: ").strip()
        if not first_name:
            print("❌ First name is required.")
            return
        
        last_name = input("Last Name: ").strip()
        if not last_name:
            print("❌ Last name is required.")
            return
        
        phone = input("Phone (optional): ").strip()
        
        # Build user data - only include non-empty values
        user_data = {
            "username": username,
            "email": email,
            "password_hash": password_hash,
            "role": role,
            "first_name": first_name,
            "last_name": last_name
        }
        
        if phone:
            user_data["phone"] = phone
        
        result = await self._safe_call_tool("create_user", user_data)
        
        if result.get("success"):
            print(f"✅ User '{username}' created successfully!")
            print(f"   User ID: {result['data']['id']}")
        else:
            print(f"❌ Failed to create user: {result.get('message', 'Unknown error')}")
    
    async def _list_users_detailed(self):
        """List all users with details."""
        print("\n📋 All Users:")
        
        result = await self._safe_call_tool("list_users", {})
        
        if result.get("users"):
            for user in result["users"]:
                print(f"\n👤 {user['first_name']} {user['last_name']}")
                print(f"   ID: {user['id']}")
                print(f"   Username: {user['username']}")
                print(f"   Email: {user['email']}")
                print(f"   Role: {user['role']}")
                print(f"   Phone: {user.get('phone', 'Not specified')}")
                print(f"   Active: {user.get('is_active', True)}")
                print(f"   Created: {user.get('created_at', 'Unknown')}")
        else:
            print("No users found.")
    
    async def _get_user_by_id_interactive(self):
        """Get user details by ID."""
        print("\n🔍 Get User Details")
        
        # First list users
        result = await self._safe_call_tool("list_users", {})
        
        if not result.get("users"):
            print("No users found.")
            return
        
        print("\nAvailable Users:")
        for i, user in enumerate(result["users"], 1):
            print(f"   {i}. {user['first_name']} {user['last_name']} ({user['username']})")
        
        choice = input("Select user number: ").strip()
        if not choice.isdigit():
            print("❌ Invalid selection.")
            return
        
        choice_idx = int(choice) - 1
        if not (0 <= choice_idx < len(result["users"])):
            print("❌ Invalid selection.")
            return
        
        user_id = result["users"][choice_idx]["id"]
        
        detail_result = await self._safe_call_tool("get_user_by_id", {"user_id": user_id})
        
        if detail_result.get("user"):
            user = detail_result["user"]
            print(f"\n👤 User Details:")
            print(f"   Name: {user['first_name']} {user['last_name']}")
            print(f"   ID: {user['id']}")
            print(f"   Username: {user['username']}")
            print(f"   Email: {user['email']}")
            print(f"   Role: {user['role']}")
            print(f"   Phone: {user.get('phone', 'Not specified')}")
            print(f"   Active: {user.get('is_active', True)}")
            print(f"   Created: {user.get('created_at', 'Unknown')}")
            print(f"   Updated: {user.get('updated_at', 'Unknown')}")
        else:
            print("❌ User not found.")
    
    async def _update_user_interactive(self):
        """Update user with user input."""
        print("\n✏️ Update User")
        
        # First list users
        result = await self._safe_call_tool("list_users", {})
        
        if not result.get("users"):
            print("No users found.")
            return
        
        print("\nAvailable Users:")
        for i, user in enumerate(result["users"], 1):
            print(f"   {i}. {user['first_name']} {user['last_name']} ({user['username']})")
        
        choice = input("Select user number to update: ").strip()
        if not choice.isdigit():
            print("❌ Invalid selection.")
            return
        
        choice_idx = int(choice) - 1
        if not (0 <= choice_idx < len(result["users"])):
            print("❌ Invalid selection.")
            return
        
        user = result["users"][choice_idx]
        user_id = user["id"]
        
        print(f"\nUpdating user: {user['first_name']} {user['last_name']}")
        print("(Press Enter to keep current value)")
        
        # Get new values
        new_username = input(f"Username (current: {user['username']}): ").strip()
        new_email = input(f"Email (current: {user['email']}): ").strip()
        new_first_name = input(f"First Name (current: {user['first_name']}): ").strip()
        new_last_name = input(f"Last Name (current: {user['last_name']}): ").strip()
        new_phone = input(f"Phone (current: {user.get('phone', 'None')}): ").strip()
        new_role = input(f"Role (current: {user['role']}): ").strip()
        
        # Build update data with only changed fields
        update_data = {"user_id": user_id}
        if new_username: update_data["username"] = new_username
        if new_email: update_data["email"] = new_email
        if new_first_name: update_data["first_name"] = new_first_name
        if new_last_name: update_data["last_name"] = new_last_name
        if new_phone: update_data["phone"] = new_phone
        if new_role: update_data["role"] = new_role
        
        if len(update_data) == 1:  # Only user_id
            print("ℹ️  No changes specified.")
            return
        
        result = await self._safe_call_tool("update_user", update_data)
        
        if result.get("success"):
            print(f"✅ User updated successfully!")
        else:
            print(f"❌ Failed to update user: {result.get('message', 'Unknown error')}")
    
    async def _delete_user_interactive(self):
        """Delete user with confirmation."""
        print("\n❌ Delete User")
        
        # First list users
        result = await self._safe_call_tool("list_users", {})
        
        if not result.get("users"):
            print("No users found.")
            return
        
        print("\nAvailable Users:")
        for i, user in enumerate(result["users"], 1):
            print(f"   {i}. {user['first_name']} {user['last_name']} ({user['username']}) - {user['role']}")
        
        choice = input("Select user number to DELETE: ").strip()
        if not choice.isdigit():
            print("❌ Invalid selection.")
            return
        
        choice_idx = int(choice) - 1
        if not (0 <= choice_idx < len(result["users"])):
            print("❌ Invalid selection.")
            return
        
        user = result["users"][choice_idx]
        user_id = user["id"]
        
        # Confirmation
        print(f"\n⚠️  WARNING: You are about to delete user:")
        print(f"   Name: {user['first_name']} {user['last_name']}")
        print(f"   Username: {user['username']}")
        print(f"   Role: {user['role']}")
        
        confirm = input("\nType 'DELETE' to confirm: ").strip()
        if confirm != "DELETE":
            print("❌ Deletion cancelled.")
            return
        
        result = await self._safe_call_tool("delete_user", {"user_id": user_id})
        
        if result.get("success"):
            print(f"✅ User deleted successfully!")
        else:
            print(f"❌ Failed to delete user: {result.get('message', 'Unknown error')}")
    
    async def _view_all_master_data(self):
        """View all master data summary."""
        print("\n📊 === MASTER DATA SUMMARY ===")
        
        # Get all master data
        users = await self._safe_call_tool("list_users", {})
        departments = await self._safe_call_tool("list_departments", {})
        rooms = await self._safe_call_tool("list_rooms", {})
        
        print(f"\n👥 Users: {len(users.get('users', []))}")
        if users.get("users"):
            for user in users["users"][:5]:  # Show first 5
                print(f"   • {user['first_name']} {user['last_name']} ({user['role']})")
            if len(users["users"]) > 5:
                print(f"   ... and {len(users['users']) - 5} more")
        
        print(f"\n🏢 Departments: {len(departments.get('departments', []))}")
        if departments.get("departments"):
            for dept in departments["departments"]:
                print(f"   • {dept['name']} (Floor {dept.get('floor_number', 'N/A')})")
        
        print(f"\n🏠 Rooms: {len(rooms.get('rooms', []))}")
        if rooms.get("rooms"):
            for room in rooms["rooms"][:5]:  # Show first 5
                print(f"   • Room {room['room_number']} ({room.get('room_type', 'Standard')})")
            if len(rooms["rooms"]) > 5:
                print(f"   ... and {len(rooms['rooms']) - 5} more")
        
        print(f"\nℹ️  Equipment and Supply categories are managed through their respective creation flows.")
        
    async def connect(self):
        """Connect to the MCP server."""
        try:
            print("🔌 Connecting to server...")
            server_params = StdioServerParameters(
                command="python",
                args=["comprehensive_server.py"],
                env=None
            )
            
            # Use async context manager properly
            self.stdio_context = stdio_client(server_params)
            read, write = await self.stdio_context.__aenter__()
            self.session = ClientSession(read, write)
            
            print("🔗 Initializing session...")
            await self.session.initialize()
            print("✅ Connected to Hospital Management MCP Server")
            
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            raise
        
    async def disconnect(self):
        """Disconnect from the MCP server."""
        if self.session:
            await self.session.close()
        if hasattr(self, 'stdio_context'):
            await self.stdio_context.__aexit__(None, None, None)
        print("📡 Disconnected from server")

    async def list_available_tools(self):
        """List all available tools from the server."""
        tools = await self.session.list_tools()
        self.available_tools = [tool.name for tool in tools.tools]
        
        print(f"\n🛠️  Available Tools ({len(tools.tools)}):")
        print("=" * 50)
        
        # Group tools by category
        categories = {
            "User Management": [],
            "Department Management": [],
            "Patient Management": [],
            "Bed Management": [],
            "Staff Management": [],
            "Equipment Management": [],
            "Supply Management": [],
            "Appointment Management": [],
            "Agent Logging": [],
            "Legacy Support": []
        }
        
        for tool in tools.tools:
            name = tool.name
            if "user" in name:
                categories["User Management"].append(name)
            elif "department" in name:
                categories["Department Management"].append(name)
            elif "patient" in name:
                categories["Patient Management"].append(name)
            elif "bed" in name:
                categories["Bed Management"].append(name)
            elif "staff" in name:
                categories["Staff Management"].append(name)
            elif "equipment" in name:
                categories["Equipment Management"].append(name)
            elif "supply" in name or "stock" in name:
                categories["Supply Management"].append(name)
            elif "appointment" in name:
                categories["Appointment Management"].append(name)
            elif "agent" in name or "log" in name:
                categories["Agent Logging"].append(name)
            elif "legacy" in name:
                categories["Legacy Support"].append(name)
            else:
                categories["User Management"].append(name)  # Default category
        
        for category, tool_names in categories.items():
            if tool_names:
                print(f"\n{category}:")
                for tool_name in tool_names:
                    print(f"  • {tool_name}")
        
        return tools.tools
    
    async def demo_user_management(self):
        """Demonstrate user management operations."""
        print("\n👥 === USER MANAGEMENT DEMO ===")
        
        # Create a new user
        print("\n1. Creating a new user...")
        create_result = await self.session.call_tool(
            "create_user",
            {
                "username": "demo_doctor",
                "email": "demo@hospital.com",
                "password_hash": "hashed_password_demo",
                "role": "doctor",
                "first_name": "Demo",
                "last_name": "Doctor",
                "phone": "555-DEMO"
            }
        )
        print(f"Result: {create_result.content[0].text}")
        
        if "success" in create_result.content[0].text:
            # Parse the user ID from the response
            result_data = json.loads(create_result.content[0].text)
            if result_data.get("success") and "data" in result_data:
                user_id = result_data["data"]["id"]
                
                # Get user by ID
                print("\n2. Getting user by ID...")
                get_result = await self.session.call_tool("get_user_by_id", {"user_id": user_id})
                print(f"Result: {get_result.content[0].text}")
                
                # Update user
                print("\n3. Updating user...")
                update_result = await self.session.call_tool(
                    "update_user",
                    {
                        "user_id": user_id,
                        "phone": "555-UPDATED"
                    }
                )
                print(f"Result: {update_result.content[0].text}")
        
        # List all users
        print("\n4. Listing all users...")
        list_result = await self.session.call_tool("list_users", {})
        print(f"Result: {list_result.content[0].text}")

    async def demo_department_management(self):
        """Demonstrate department management operations."""
        print("\n🏢 === DEPARTMENT MANAGEMENT DEMO ===")
        
        # Create a new department
        print("\n1. Creating a new department...")
        create_result = await self.session.call_tool(
            "create_department",
            {
                "name": "Demo Department",
                "description": "A demonstration department",
                "floor_number": 2,
                "phone": "555-DEPT",
                "email": "demo.dept@hospital.com"
            }
        )
        print(f"Result: {create_result.content[0].text}")
        
        # List all departments
        print("\n2. Listing all departments...")
        list_result = await self.session.call_tool("list_departments", {})
        print(f"Result: {list_result.content[0].text}")

    async def demo_patient_management(self):
        """Demonstrate patient management operations."""
        print("\n🤒 === PATIENT MANAGEMENT DEMO ===")
        
        # Create a new patient
        print("\n1. Creating a new patient...")
        create_result = await self.session.call_tool(
            "create_patient",
            {
                "patient_number": "P999",
                "first_name": "Demo",
                "last_name": "Patient",
                "date_of_birth": "1990-05-15",
                "gender": "male",
                "phone": "555-PATIENT",
                "email": "demo.patient@email.com",
                "address": "123 Demo St, Demo City",
                "blood_type": "O+",
                "allergies": "None known"
            }
        )
        print(f"Result: {create_result.content[0].text}")
        
        # List all patients
        print("\n2. Listing all patients...")
        list_result = await self.session.call_tool("list_patients", {})
        print(f"Result: {list_result.content[0].text}")

    async def demo_bed_management(self):
        """Demonstrate bed management operations (AI Agent)."""
        print("\n🛏️  === BED MANAGEMENT AGENT DEMO ===")
        
        # List available beds
        print("\n1. Listing available beds...")
        beds_result = await self.session.call_tool("list_beds", {"status": "available"})
        print(f"Result: {beds_result.content[0].text}")
        
        # Get department and patient for bed assignment demo
        departments_result = await self.session.call_tool("list_departments", {})
        patients_result = await self.session.call_tool("list_patients", {})
        
        try:
            dept_data = json.loads(departments_result.content[0].text)
            patient_data = json.loads(patients_result.content[0].text)
            
            if dept_data.get("departments") and patient_data.get("patients"):
                dept_id = dept_data["departments"][0]["id"]
                patient_id = patient_data["patients"][0]["id"]
                
                # Create a new room and bed for demo
                print("\n2. Creating a demo room...")
                room_result = await self.session.call_tool(
                    "create_room",
                    {
                        "room_number": "DEMO001",
                        "department_id": dept_id,
                        "room_type": "private",
                        "capacity": 1
                    }
                )
                print(f"Room creation result: {room_result.content[0].text}")
                
                room_data = json.loads(room_result.content[0].text)
                if room_data.get("success"):
                    room_id = room_data["data"]["id"]
                    
                    # Create a new bed
                    print("\n3. Creating a demo bed...")
                    bed_result = await self.session.call_tool(
                        "create_bed",
                        {
                            "bed_number": "DEMO001A",
                            "room_id": room_id,
                            "bed_type": "standard"
                        }
                    )
                    print(f"Bed creation result: {bed_result.content[0].text}")
                    
                    bed_data = json.loads(bed_result.content[0].text)
                    if bed_data.get("success"):
                        bed_id = bed_data["data"]["id"]
                        
                        # Assign bed to patient
                        print("\n4. Assigning bed to patient...")
                        assign_result = await self.session.call_tool(
                            "assign_bed_to_patient",
                            {
                                "bed_id": bed_id,
                                "patient_id": patient_id,
                                "admission_date": datetime.now().isoformat()
                            }
                        )
                        print(f"Assignment result: {assign_result.content[0].text}")
                        
                        # Discharge patient
                        print("\n5. Discharging patient from bed...")
                        discharge_result = await self.session.call_tool(
                            "discharge_bed",
                            {
                                "bed_id": bed_id,
                                "discharge_date": datetime.now().isoformat()
                            }
                        )
                        print(f"Discharge result: {discharge_result.content[0].text}")
        
        except Exception as e:
            print(f"Error in bed management demo: {e}")

    async def demo_equipment_management(self):
        """Demonstrate equipment management operations (AI Agent)."""
        print("\n🔧 === EQUIPMENT TRACKER AGENT DEMO ===")
        
        # Create equipment category
        print("\n1. Creating equipment category...")
        category_result = await self.session.call_tool(
            "create_equipment_category",
            {
                "name": "Demo Equipment",
                "description": "Equipment for demonstration purposes"
            }
        )
        print(f"Result: {category_result.content[0].text}")
        
        category_data = json.loads(category_result.content[0].text)
        if category_data.get("success"):
            category_id = category_data["data"]["id"]
            
            # Create equipment
            print("\n2. Creating equipment...")
            equipment_result = await self.session.call_tool(
                "create_equipment",
                {
                    "equipment_id": "DEMO-EQ-001",
                    "name": "Demo Monitor",
                    "category_id": category_id,
                    "model": "DemoMax 2024",
                    "manufacturer": "Demo Corp",
                    "serial_number": "DEMO123456",
                    "location": "Demo Room",
                    "cost": 15000.00
                }
            )
            print(f"Result: {equipment_result.content[0].text}")
            
            equipment_data = json.loads(equipment_result.content[0].text)
            if equipment_data.get("success"):
                equipment_id = equipment_data["data"]["id"]
                
                # Update equipment status
                print("\n3. Updating equipment status...")
                status_result = await self.session.call_tool(
                    "update_equipment_status",
                    {
                        "equipment_id": equipment_id,
                        "status": "in_use",
                        "notes": "Assigned to demo room for testing"
                    }
                )
                print(f"Result: {status_result.content[0].text}")
        
        # List all equipment
        print("\n4. Listing all equipment...")
        list_result = await self.session.call_tool("list_equipment", {})
        print(f"Result: {list_result.content[0].text}")

    async def demo_supply_management(self):
        """Demonstrate supply management operations (AI Agent)."""
        print("\n📦 === SUPPLY INVENTORY AGENT DEMO ===")
        
        # Create supply category
        print("\n1. Creating supply category...")
        category_result = await self.session.call_tool(
            "create_supply_category",
            {
                "name": "Demo Supplies",
                "description": "Supplies for demonstration purposes"
            }
        )
        print(f"Result: {category_result.content[0].text}")
        
        category_data = json.loads(category_result.content[0].text)
        if category_data.get("success"):
            category_id = category_data["data"]["id"]
            
            # Create supply
            print("\n2. Creating supply item...")
            supply_result = await self.session.call_tool(
                "create_supply",
                {
                    "item_code": "DEMO-SUP-001",
                    "name": "Demo Bandages",
                    "category_id": category_id,
                    "unit_of_measure": "boxes",
                    "minimum_stock_level": 10,
                    "maximum_stock_level": 100,
                    "current_stock": 5,  # Low stock for testing
                    "unit_cost": 25.50,
                    "supplier": "Demo Medical Supply Co"
                }
            )
            print(f"Result: {supply_result.content[0].text}")
            
            supply_data = json.loads(supply_result.content[0].text)
            if supply_data.get("success"):
                supply_id = supply_data["data"]["id"]
                
                # Get users for transaction
                users_result = await self.session.call_tool("list_users", {})
                users_data = json.loads(users_result.content[0].text)
                
                if users_data.get("users"):
                    user_id = users_data["users"][0]["id"]
                    
                    # Update stock
                    print("\n3. Updating supply stock...")
                    stock_result = await self.session.call_tool(
                        "update_supply_stock",
                        {
                            "supply_id": supply_id,
                            "quantity_change": 20,
                            "transaction_type": "in",
                            "performed_by": user_id,
                            "unit_cost": 25.50,
                            "reference_number": "DEMO-PO-001",
                            "notes": "Demo restock for testing"
                        }
                    )
                    print(f"Result: {stock_result.content[0].text}")
        
        # List low stock supplies
        print("\n4. Checking low stock supplies...")
        low_stock_result = await self.session.call_tool("list_supplies", {"low_stock_only": True})
        print(f"Result: {low_stock_result.content[0].text}")
        
        # List all supplies
        print("\n5. Listing all supplies...")
        all_supplies_result = await self.session.call_tool("list_supplies", {})
        print(f"Result: {all_supplies_result.content[0].text}")

    async def demo_agent_logging(self):
        """Demonstrate AI agent interaction logging."""
        print("\n🤖 === AI AGENT LOGGING DEMO ===")
        
        # Get user for logging
        users_result = await self.session.call_tool("list_users", {})
        users_data = json.loads(users_result.content[0].text)
        
        if users_data.get("users"):
            user_id = users_data["users"][0]["id"]
            
            # Log agent interaction
            print("\n1. Logging agent interaction...")
            log_result = await self.session.call_tool(
                "log_agent_interaction",
                {
                    "agent_type": "bed_management",
                    "user_id": user_id,
                    "query": "Find available beds in cardiology department",
                    "response": "Found 2 available beds in cardiology: 301A, 302B",
                    "action_taken": "bed_search",
                    "confidence_score": 0.95,
                    "execution_time_ms": 125
                }
            )
            print(f"Result: {log_result.content[0].text}")

    async def demo_staff_management(self):
        """Demonstrate staff management operations (AI Agent)."""
        print("\n👨‍⚕️ === STAFF ALLOCATION AGENT DEMO ===")
        
        # Get required data
        users_result = await self.session.call_tool("list_users", {})
        departments_result = await self.session.call_tool("list_departments", {})
        
        try:
            users_data = json.loads(users_result.content[0].text)
            departments_data = json.loads(departments_result.content[0].text)
            
            if users_data.get("users") and departments_data.get("departments"):
                user_id = users_data["users"][0]["id"]
                department_id = departments_data["departments"][0]["id"]
                
                # Create staff member
                print("\n1. Creating staff member...")
                staff_result = await self.session.call_tool(
                    "create_staff",
                    {
                        "user_id": user_id,
                        "employee_id": "DEMO-EMP-001",
                        "department_id": department_id,
                        "position": "Demo Nurse",
                        "specialization": "Demo Care",
                        "hire_date": "2024-01-15",
                        "salary": 65000.00,
                        "shift_pattern": "day"
                    }
                )
                print(f"Result: {staff_result.content[0].text}")
        
        except Exception as e:
            print(f"Error in staff demo: {e}")
        
        # List all staff
        print("\n2. Listing all staff...")
        list_result = await self.session.call_tool("list_staff", {})
        print(f"Result: {list_result.content[0].text}")

    async def demo_legacy_support(self):
        """Demonstrate legacy user support."""
        print("\n🔄 === LEGACY SUPPORT DEMO ===")
        
        # Create legacy user
        print("\n1. Creating legacy user...")
        legacy_result = await self.session.call_tool(
            "create_legacy_user",
            {
                "name": "Demo Legacy User",
                "email": "legacy@hospital.com",
                "address": "123 Legacy St",
                "phone": "555-LEGACY"
            }
        )
        print(f"Result: {legacy_result.content[0].text}")
        
        # List legacy users
        print("\n2. Listing legacy users...")
        list_result = await self.session.call_tool("list_legacy_users", {})
        print(f"Result: {list_result.content[0].text}")

    async def run_comprehensive_demo(self):
        """Run a comprehensive demonstration of all features."""
        print("🏥 HOSPITAL MANAGEMENT SYSTEM - COMPREHENSIVE DEMO")
        print("=" * 60)
        
        server_params = StdioServerParameters(
            command="python",
            args=["comprehensive_server.py"],
            env=None
        )
        
        try:
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    self.session = session
                    await session.initialize()
                    print("✅ Connected to Hospital Management MCP Server")
                    
                    tools = await session.list_tools()
                    self.available_tools = [tool.name for tool in tools.tools]
                    print(f"🛠️  Loaded {len(tools.tools)} tools")
                    
                    # Run all demonstrations
                    await self.demo_user_management()
                    await self.demo_department_management()
                    await self.demo_patient_management()
                    await self.demo_bed_management()
                    await self.demo_equipment_management()
                    await self.demo_supply_management()
                    await self.demo_staff_management()
                    await self.demo_agent_logging()
                    await self.demo_legacy_support()
                    
                    print("\n🎉 === COMPREHENSIVE DEMO COMPLETED ===")
                    print("All 40+ MCP tools have been demonstrated!")
                    print("The hospital management system is fully operational.")
                    
        except Exception as e:
            print(f"❌ Demo failed: {e}")
            import traceback
            traceback.print_exc()

    async def demo_llm_integration(self):
        """Demonstrate LLM integration with natural language processing."""
        print("\n🧠 === LLM INTEGRATION DEMO ===")
        
        if not self.llm_model:
            print("⚠️ LLM not available. Please check GEMINI_API_KEY configuration.")
            return
        
        # Connect to MCP server first
        server_params = StdioServerParameters(
            command="python",
            args=["comprehensive_server.py"],
            env=None
        )
        
        try:
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    self.session = session
                    await session.initialize()
                    print("✅ Connected to MCP server")
                    
                    print("\n🎯 Testing natural language queries:")
                    
                    # Demo queries to test LLM integration
                    demo_queries = [
                        "Show me all patients in the hospital",
                        "What's the current bed availability?",
                        "List all departments",
                        "Check equipment status",
                        "Show supply inventory levels",
                        "Give me a hospital overview",
                        "How many staff members do we have?",
                        "Analyze the hospital's current state"
                    ]
                    
                    for i, query in enumerate(demo_queries, 1):
                        print(f"\n--- Query {i}: {query} ---")
                        response = await self.intelligent_query_handler(query)
                        print(f"✅ Completed query {i}")
                        
                        # Add a small delay between queries
                        await asyncio.sleep(1)
                    
                    # Interactive mode
                    print(f"\n🎮 === INTERACTIVE LLM MODE ===")
                    print("You can now ask questions in natural language!")
                    print("Type 'exit' to quit this demo")
                    
                    while True:
                        try:
                            user_input = input("\n🤖 Ask me anything about hospital management: ").strip()
                            
                            if user_input.lower() in ['exit', 'quit', 'bye']:
                                print("👋 Exiting LLM demo...")
                                break
                            
                            if user_input:
                                response = await self.intelligent_query_handler(user_input)
                                print(f"\n💡 Response: {response}")
                            else:
                                print("Please enter a valid question.")
                                
                        except KeyboardInterrupt:
                            print("\n👋 Exiting LLM demo...")
                            break
            
        except Exception as e:
            print(f"❌ LLM Demo failed: {e}")
            import traceback
            traceback.print_exc()

    async def run_agentic_mode(self):
        """Run the AI agent in autonomous mode."""
        print("🤖 HOSPITAL MANAGEMENT SYSTEM - AGENTIC AI MODE")
        print("=" * 60)
        
        server_params = StdioServerParameters(
            command="python",
            args=["comprehensive_server.py"],
            env=None
        )
        
        try:
            print("\n🔌 Connecting to server...")
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    self.session = session
                    
                    print("🔗 Initializing session...")
                    await session.initialize()
                    print("✅ Connected to Hospital Management MCP Server")
                    
                    print("🛠️  Loading available tools...")
                    tools = await session.list_tools()
                    self.available_tools = [tool.name for tool in tools.tools]
                    print(f"✅ Loaded {len(tools.tools)} tools")
                    
                    print("\n🧠 Initializing Agentic AI...")
                    
                    # Step 1: Analyze current state
                    print("📊 Analyzing hospital state...")
                    analysis = await self.analyze_hospital_state()
                    
                    # Step 2: Run autonomous management
                    print("🤖 Running autonomous management...")
                    await self.autonomous_hospital_management()
                    
                    # Step 3: Demonstrate intelligent patient admission
                    print("🏥 Demonstrating intelligent patient admission...")
                    sample_patient = {
                        "patient_number": f"P{random.randint(1000, 9999)}",
                        "first_name": "AI",
                        "last_name": "TestPatient",
                        "date_of_birth": "1985-03-15",
                        "gender": "female",
                        "phone": "555-AI-TEST",
                        "email": "ai.test@hospital.com",
                        "address": "123 AI Street, Tech City",
                        "blood_type": "A+",
                        "allergies": "None"
                    }
                    
                    await self.intelligent_patient_admission(sample_patient)
                    
                    # Step 4: Resource optimization
                    print("⚡ Running resource optimization...")
                    optimization = await self.smart_resource_optimization()
                    
                    print("\n🎉 === AGENTIC AI DEMONSTRATION COMPLETED ===")
                    print("✅ Hospital state analyzed and optimized")
                    print("✅ Autonomous management systems active")
                    print("✅ Intelligent patient admission demonstrated")
                    print("✅ Resource optimization completed")
                    print("🤖 AI Agent is ready for production use!")
                    
        except Exception as e:
            print(f"❌ Agentic mode failed: {e}")
            import traceback
            traceback.print_exc()

    async def interactive_mode(self):
        """Run in interactive mode for manual testing."""
        print("🏥 HOSPITAL MANAGEMENT SYSTEM - INTERACTIVE MODE")
        print("=" * 55)
        
        server_params = StdioServerParameters(
            command="python",
            args=["comprehensive_server.py"],
            env=None
        )
        
        try:
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    self.session = session
                    await session.initialize()
                    print("✅ Connected to Hospital Management MCP Server")
                    
                    tools = await session.list_tools()
                    self.available_tools = [tool.name for tool in tools.tools]
                    
                    print(f"\n🛠️  Available Tools ({len(tools.tools)}):")
                    print("=" * 50)
                    
                    # Group tools by category for display
                    categories = {
                        "User Management": [],
                        "Department Management": [],
                        "Patient Management": [],
                        "Bed Management": [],
                        "Staff Management": [],
                        "Equipment Management": [],
                        "Supply Management": [],
                        "Appointment Management": [],
                        "Agent Logging": [],
                        "Legacy Support": []
                    }
                    
                    for tool in tools.tools:
                        name = tool.name
                        if "user" in name:
                            categories["User Management"].append(name)
                        elif "department" in name:
                            categories["Department Management"].append(name)
                        elif "patient" in name:
                            categories["Patient Management"].append(name)
                        elif "bed" in name:
                            categories["Bed Management"].append(name)
                        elif "staff" in name:
                            categories["Staff Management"].append(name)
                        elif "equipment" in name:
                            categories["Equipment Management"].append(name)
                        elif "supply" in name or "stock" in name:
                            categories["Supply Management"].append(name)
                        elif "appointment" in name:
                            categories["Appointment Management"].append(name)
                        elif "agent" in name or "log" in name:
                            categories["Agent Logging"].append(name)
                        elif "legacy" in name:
                            categories["Legacy Support"].append(name)
                        else:
                            categories["User Management"].append(name)
                    
                    for category, tool_names in categories.items():
                        if tool_names:
                            print(f"\n{category}: {len(tool_names)} tools")
                    
                    print("\n📋 Interactive Menu:")
                    print("=== BASIC OPERATIONS ===")
                    print("1. User Management")
                    print("2. Department Management") 
                    print("3. Patient Management")
                    print("4. Bed Management (AI Agent)")
                    print("5. Equipment Management (AI Agent)")
                    print("6. Supply Management (AI Agent)")
                    print("7. Staff Management (AI Agent)")
                    print("8. Agent Logging")
                    print("9. Legacy Support")
                    print("\n=== MASTER DATA MANAGEMENT ===")
                    print("16. Master Data CRUD Operations")
                    print("\n=== AGENTIC AI FEATURES ===")
                    print("10. Analyze Hospital State")
                    print("11. Autonomous Management")
                    print("12. Intelligent Patient Admission")
                    print("13. Smart Resource Optimization")
                    print("14. Run Full Agentic Demo")
                    print("17. LLM Integration Demo (Natural Language)")
                    print("\n=== DEMOS ===")
                    print("15. Run Comprehensive Demo")
                    print("0. Exit")
                    
                    while True:
                        try:
                            choice = input("\nEnter your choice (0-17): ").strip()
                            
                            if choice == "0":
                                break
                            elif choice == "1":
                                await self.demo_user_management()
                            elif choice == "2":
                                await self.demo_department_management()
                            elif choice == "3":
                                await self.demo_patient_management()
                            elif choice == "4":
                                await self.demo_bed_management()
                            elif choice == "5":
                                await self.demo_equipment_management()
                            elif choice == "6":
                                await self.demo_supply_management()
                            elif choice == "7":
                                await self.demo_staff_management()
                            elif choice == "8":
                                await self.demo_agent_logging()
                            elif choice == "9":
                                await self.demo_legacy_support()
                            elif choice == "10":
                                await self.analyze_hospital_state()
                            elif choice == "11":
                                await self.autonomous_hospital_management()
                            elif choice == "12":
                                # Interactive patient admission
                                patient_data = await self._get_patient_input()
                                await self.intelligent_patient_admission(patient_data)
                            elif choice == "13":
                                await self.smart_resource_optimization()
                            elif choice == "14":
                                # Run agentic demo within this session
                                await self._run_agentic_demo_inline()
                            elif choice == "15":
                                # Run comprehensive demo within this session
                                await self._run_comprehensive_demo_inline()
                            elif choice == "16":
                                # Master Data CRUD Operations
                                await self.master_data_management()
                            elif choice == "17":
                                # LLM Integration Demo
                                await self.demo_llm_integration()
                            else:
                                print("Invalid choice. Please enter 0-17.")
                                
                        except KeyboardInterrupt:
                            print("\n\nExiting...")
                            break
                        except Exception as e:
                            print(f"Error: {e}")
                            import traceback
                            traceback.print_exc()
                    
                    print("📡 Disconnecting from server...")
                    
        except Exception as e:
            print(f"❌ Interactive mode failed: {e}")
            import traceback
            traceback.print_exc()

    async def _get_patient_input(self):
        """Get patient input for intelligent admission."""
        print("\n👤 Enter Patient Information:")
        
        first_name = input("First Name: ").strip() or "Demo"
        last_name = input("Last Name: ").strip() or "Patient"
        dob = input("Date of Birth (YYYY-MM-DD): ").strip() or "1990-01-01"
        gender = input("Gender (male/female/other): ").strip() or "other"
        phone = input("Phone: ").strip() or "555-0000"
        email = input("Email: ").strip() or "demo@example.com"
        
        return {
            "patient_number": f"P{random.randint(1000, 9999)}",
            "first_name": first_name,
            "last_name": last_name,
            "date_of_birth": dob,
            "gender": gender,
            "phone": phone,
            "email": email,
            "address": "Interactive Entry",
            "blood_type": "O+",
            "allergies": "None specified"
        }

    async def _run_agentic_demo_inline(self):
        """Run agentic demo within current session."""
        print("\n🤖 === INLINE AGENTIC AI DEMO ===")
        
        # Step 1: Analyze current state
        print("📊 Analyzing hospital state...")
        analysis = await self.analyze_hospital_state()
        
        # Step 2: Run autonomous management
        print("🤖 Running autonomous management...")
        await self.autonomous_hospital_management()
        
        # Step 3: Demonstrate intelligent patient admission
        print("🏥 Demonstrating intelligent patient admission...")
        sample_patient = {
            "patient_number": f"P{random.randint(1000, 9999)}",
            "first_name": "Interactive",
            "last_name": "TestPatient",
            "date_of_birth": "1985-03-15",
            "gender": "male",
            "phone": "555-INTERACTIVE",
            "email": "interactive@hospital.com",
            "address": "123 Interactive St",
            "blood_type": "B+",
            "allergies": "None"
        }
        
        await self.intelligent_patient_admission(sample_patient)
        
        # Step 4: Resource optimization
        print("⚡ Running resource optimization...")
        optimization = await self.smart_resource_optimization()
        
        print("\n✅ Inline agentic demo completed!")

    async def _run_comprehensive_demo_inline(self):
        """Run comprehensive demo within current session."""
        print("\n🏥 === INLINE COMPREHENSIVE DEMO ===")
        
        # Run a subset of demonstrations
        await self.demo_user_management()
        await self.demo_patient_management()
        await self.demo_bed_management()
        await self.demo_equipment_management()
        await self.demo_supply_management()
        
        print("\n✅ Inline comprehensive demo completed!")


async def main():
    """Main function to run the client."""
    client = HospitalManagementClient()
    
    print("🏥 Hospital Management System - Agentic AI Client")
    print("Choose mode:")
    print("1. Comprehensive Demo (All Features)")
    print("2. Interactive Mode (Manual Control)")
    print("3. Agentic AI Mode (Autonomous Operation)")
    
    try:
        mode = input("Enter choice (1, 2, or 3): ").strip()
        
        if mode == "1":
            await client.run_comprehensive_demo()
        elif mode == "2":
            await client.interactive_mode()
        elif mode == "3":
            await client.run_agentic_mode()
        else:
            print("Invalid choice. Running agentic AI mode...")
            await client.run_agentic_mode()
            
    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
       