# 🏥 Hospital Management System - Multi-Agent Architecture

## 🤖 **Multi-Agent System Overview**

This hospital management system has been enhanced with a **specialized multi-agent architecture** where different AI agents handle specific hospital operations. Each agent is an expert in its domain, providing better performance, maintainability, and scalability.

## 🎯 **Agent Architecture**

```
🏥 Hospital Multi-Agent System
├── 🤖 Orchestrator Agent (Master Coordinator)
├── 👥 User Management Agent
├── 🏢 Department Management Agent
├── 🧾 Patient Management Agent
├── 🛏️ Room & Bed Management Agent
├── 👨‍⚕️ Staff Management Agent
├── 🔧 Equipment Management Agent
├── 📦 Inventory Management Agent
└── 🏗️ Infrastructure & Configuration
```

## 🔧 **Specialized Agents**

### **🎯 Orchestrator Agent (Master)**
- **Role**: Coordinates all other agents and handles complex workflows
- **Tools**: `get_system_status`, `route_request`, `execute_workflow`, `get_agent_info`
- **Workflows**: Patient admission, discharge, equipment maintenance, inventory restock, staff scheduling

### **👥 User Management Agent**
- **Role**: Handles user authentication, registration, and profile management
- **Tools**: `create_user`, `get_user_by_id`, `list_users`, `update_user`, `delete_user`, `create_legacy_user`, `list_legacy_users`
- **Capabilities**: User registration, role-based access control, profile management

### **🏢 Department Management Agent**
- **Role**: Manages hospital departments and organizational structure
- **Tools**: `create_department`, `list_departments`, `get_department_by_id`, `update_department`, `delete_department`
- **Capabilities**: Department creation, hierarchy management, head doctor assignments

### **🧾 Patient Management Agent**
- **Role**: Manages patient records, registration, and medical information
- **Tools**: `create_patient`, `list_patients`, `get_patient_by_id`, `search_patients`, `update_patient`, `delete_patient`
- **Capabilities**: Patient registration, medical records, demographics tracking, search functionality

### **🛏️ Room & Bed Management Agent**
- **Role**: Manages room allocation, bed assignments, and occupancy tracking
- **Tools**: `create_room`, `list_rooms`, `create_bed`, `list_beds`, `assign_bed_to_patient`, `discharge_bed`, `update_bed_status`
- **Capabilities**: Room allocation, bed inventory, patient assignments, occupancy monitoring

### **👨‍⚕️ Staff Management Agent**
- **Role**: Handles staff operations, scheduling, and human resources
- **Tools**: `create_staff`, `list_staff`, `get_staff_by_id`, `update_staff`, `update_staff_status`, `get_staff_by_department`
- **Capabilities**: Staff registration, department assignments, scheduling, status tracking

### **🔧 Equipment Management Agent**
- **Role**: Tracks medical equipment, maintenance, and asset lifecycle
- **Tools**: `create_equipment_category`, `create_equipment`, `list_equipment`, `get_equipment_by_id`, `update_equipment_status`, `schedule_equipment_maintenance`
- **Capabilities**: Equipment tracking, maintenance scheduling, status management, asset lifecycle

### **📦 Inventory Management Agent**
- **Role**: Manages medical supplies, stock levels, and inventory transactions
- **Tools**: `create_supply_category`, `create_supply`, `list_supplies`, `update_supply_stock`, `get_low_stock_supplies`, `list_inventory_transactions`
- **Capabilities**: Supply tracking, stock monitoring, automated reordering, usage analytics

### **🏗️ Infrastructure & Configuration**
- **Role**: System setup, deployment, and maintenance operations
- **Tools**: Database migration, system health checks, configuration management
- **Capabilities**: Environment setup, deployment automation, system monitoring

## 🚀 **Getting Started**

### **1. Test the Multi-Agent System**
```bash
cd backend-python
python test_multi_agent.py
```

### **2. Start the Multi-Agent Server**
```bash
# Option 1: Direct startup
python multi_agent_server.py

# Option 2: Using startup script
python start_multi_agent.py

# Option 3: Docker (recommended)
docker-compose up
```

### **3. Verify System Status**
```bash
# Check health
curl http://localhost:8000/health

# List all tools
curl http://localhost:8000/tools/list

# Get system status
curl -X POST http://localhost:8000/tools/call \
  -H "Content-Type: application/json" \
  -d '{"tool": "get_system_status", "params": {}}'
```

## 🔄 **Complex Workflows**

The orchestrator agent can execute complex multi-agent workflows:

### **Patient Admission Workflow**
```json
{
  "tool": "execute_workflow",
  "params": {
    "workflow_name": "patient_admission",
    "workflow_params": {
      "patient_data": {
        "first_name": "John",
        "last_name": "Doe",
        "date_of_birth": "1990-01-15",
        "phone": "555-0123"
      },
      "bed_preferences": {
        "room_type": "private"
      }
    }
  }
}
```

### **Equipment Maintenance Workflow**
```json
{
  "tool": "execute_workflow",
  "params": {
    "workflow_name": "equipment_maintenance",
    "workflow_params": {
      "equipment_id": "uuid-here",
      "maintenance_type": "routine"
    }
  }
}
```

## 🎛️ **API Endpoints**

### **HTTP Endpoints**
- `GET /health` - System health check
- `GET /tools/list` - List all available tools
- `POST /tools/call` - Execute any tool

### **MCP Protocol Support**
- Full MCP (Model Context Protocol) compatibility
- Real-time tool execution
- Conversation memory and context

## 🔧 **Architecture Benefits**

### **🎯 Specialized Expertise**
- Each agent is optimized for specific hospital operations
- Domain-specific knowledge and capabilities
- Better error handling and validation

### **📈 Scalability**
- Individual agents can be scaled based on load
- Horizontal scaling of specific functionalities
- Load balancing between agents

### **🛠️ Maintainability**
- Modular codebase with clear separation of concerns
- Easy to update and extend individual agents
- Isolated testing and debugging

### **🔄 Parallel Processing**
- Multiple agents can work simultaneously
- Async operation support
- Improved system throughput

### **🛡️ Fault Tolerance**
- Issues in one agent don't affect others
- Graceful degradation of services
- Agent-level error isolation

## 📊 **System Monitoring**

### **Real-time Status**
```bash
# Get comprehensive system status
curl -X POST http://localhost:8000/tools/call \
  -H "Content-Type: application/json" \
  -d '{"tool": "get_system_status", "params": {}}'
```

### **Agent Information**
```bash
# Get all agent information
curl -X POST http://localhost:8000/tools/call \
  -H "Content-Type: application/json" \
  -d '{"tool": "get_agent_info", "params": {}}'

# Get specific agent info
curl -X POST http://localhost:8000/tools/call \
  -H "Content-Type: application/json" \
  -d '{"tool": "get_agent_info", "params": {"agent_name": "patient"}}'
```

## 🔮 **Future Enhancements**

- **LangGraph Integration**: For even more complex workflow orchestration
- **Agent Learning**: Machine learning capabilities for each agent
- **Load Balancing**: Intelligent request distribution
- **Event-Driven Architecture**: Real-time notifications and updates
- **Agent Performance Analytics**: Detailed metrics and optimization

## 🏗️ **File Structure**

```
backend-python/
├── agents/                          # Multi-agent system
│   ├── __init__.py                  # Agent module exports
│   ├── base_agent.py                # Base agent class
│   ├── user_agent.py                # User management agent
│   ├── department_agent.py          # Department management agent
│   ├── patient_agent.py             # Patient management agent
│   ├── room_bed_agent.py            # Room & bed management agent
│   ├── staff_agent.py               # Staff management agent
│   ├── equipment_agent.py           # Equipment management agent
│   ├── inventory_agent.py           # Inventory management agent
│   ├── infrastructure_agent.py     # System infrastructure management
│   └── orchestrator_agent.py        # Master orchestrator agent
├── multi_agent_server.py            # New multi-agent MCP server
├── start_multi_agent.py             # Startup script
├── test_multi_agent.py              # Test suite
├── comprehensive_server.py          # Legacy single-agent server (backup)
└── database.py                      # Database models and configuration
```

---

🎉 **Your hospital management system is now powered by a sophisticated multi-agent architecture!** 

Each agent specializes in specific hospital operations while the orchestrator coordinates complex workflows, providing a more scalable, maintainable, and intelligent system.
