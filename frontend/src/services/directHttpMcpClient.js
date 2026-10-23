/**
 * Direct HTTP MCP Client - Connects directly to FastMCP HTTP server
 * Uses HTTP requests for MCP communication
 *
 * Tool calls route through apiClient, which attaches the bearer token and
 * interprets the guarded response envelope. See ToolNotExecutedError below for
 * why a non-executed outcome throws rather than returning.
 */

import apiClient, { Outcome } from './apiClient';

/**
 * Raised when the backend accepted the request but did NOT perform the action:
 * denied by policy, awaiting approval, rejected by schema, or failed.
 *
 * This throws rather than returning a value on purpose. Callers already wrap
 * tool calls in try/catch, and an exception cannot be mistaken for a result —
 * whereas a returned object can be, and an approval-pending action rendered as
 * "done" is exactly the failure this architecture exists to prevent.
 */
export class ToolNotExecutedError extends Error {
  constructor(outcome) {
    super(outcome.error?.message || outcome.reason || `${outcome.tool} was not executed`);
    this.name = 'ToolNotExecutedError';
    this.outcome = outcome.outcome;
    this.tool = outcome.tool;
    this.runId = outcome.runId;
    this.reason = outcome.reason || '';
    this.violations = outcome.violations || [];
    this.executed = false;
  }

  /** True when a person needs to approve or confirm before this can proceed. */
  get awaitingHuman() {
    return (
      this.outcome === Outcome.AWAITING_APPROVAL ||
      this.outcome === Outcome.AWAITING_CONFIRMATION
    );
  }

  /** Message suitable for showing a user. */
  get userMessage() {
    switch (this.outcome) {
      case Outcome.AWAITING_APPROVAL:
        return `This action needs approval before it can be carried out. ${this.reason}`.trim();
      case Outcome.AWAITING_CONFIRMATION:
        return `Please confirm this action before it is carried out. ${this.reason}`.trim();
      case Outcome.DENIED:
        return `You do not have permission to do this. ${this.message}`.trim();
      case Outcome.INVALID:
        return `The request was incomplete or invalid. ${this.message}`.trim();
      case Outcome.UNKNOWN_TOOL:
        return `That operation is not available.`;
      default:
        return `The action could not be completed. ${this.message}`.trim();
    }
  }
}

class DirectHttpMCPClient {
  constructor() {
    this.serverUrl = `http://${window.location.hostname}:8000`;
    this.isConnected = false;
    this.serverInfo = {};
    this.tools = [];
    this.agents = [];
    this.pendingRequests = new Map();
    this.requestId = 0;
    
    // In-memory data store - starts empty, user adds data through agent
    this.dataStore = {
      patients: [],
      staff: [],
      departments: [],
      beds: [],
      equipment: [],
      supplies: [],
      rooms: [],
      users: [],
      equipment_categories: [],
      supply_categories: []
    };
  }

  /**
   * Connect to MCP server via HTTP
   */
  async connect() {
    console.log('🔗 Connecting to FastMCP HTTP server...');
    console.log('🌐 Server URL:', this.serverUrl);
    
    try {
      // Test connection with health check
      console.log('1. Testing server connection...');
      const healthResponse = await fetch(`${this.serverUrl}/health`);
      if (!healthResponse.ok) {
        throw new Error(`Health check failed: ${healthResponse.status}`);
      }
      
      console.log('✅ Server connection established');
      this.isConnected = true;
      
      // Load tools
      console.log('2. Loading available tools...');
      await this.loadTools();
      
      // Load agents
      console.log('3. Loading available agents...');
      await this.loadAgents();
      
      this.serverInfo = {
        name: "hospital-management-system",
        url: this.serverUrl,
        toolCount: this.tools.length,
        agentCount: this.agents.length,
        version: "1.0.0",
        transport: "http"
      };
      
      console.log('✅ Connected to FastMCP server:', this.serverInfo);
      console.log(`📋 Loaded ${this.tools.length} tools`);
      console.log(`👥 Loaded ${this.agents.length} agents`);
      
      return true;
      
    } catch (error) {
      console.error('❌ MCP connection failed:', error);
      console.error('📍 Error details:', {
        message: error.message,
        stack: error.stack,
        serverUrl: this.serverUrl
      });
      this.isConnected = false;
      return false;
    }
  }

  /**
   * Initialize the client by fetching available tools
   */
  async initialize() {
    try {
      const response = await this.sendRequest('initialize', {
        protocolVersion: '2024-11-05',
        capabilities: {},
        clientInfo: {
          name: 'hospital-management-frontend',
          version: '1.0.0'
        }
      });

      // Fetch available tools
      const toolsResponse = await this.sendRequest('tools/list');

      if (toolsResponse.result && toolsResponse.result.tools) {
        this.tools = toolsResponse.result.tools;
      }

      return response;
    } catch (error) {
      console.error('❌ Failed to initialize client:', error);
      throw error;
    }
  }

  /**
   * Call a tool on the server.
   *
   * Returns the legacy JSON-RPC shape so existing callers keep working, but
   * only ever for an action that actually executed. Anything else throws
   * ToolNotExecutedError.
   */
  async callTool(toolName, args = {}) {
    const outcome = await apiClient.callTool(toolName, args);

    if (!outcome.executed) {
      throw new ToolNotExecutedError(outcome);
    }

    return {
      jsonrpc: '2.0',
      id: this.generateId(),
      result: {
        content: [
          {
            type: 'text',
            text:
              typeof outcome.result === 'string'
                ? outcome.result
                : JSON.stringify(outcome.result),
          },
        ],
      },
      executed: true,
      outcome: outcome.outcome,
      runId: outcome.runId,
    };
  }

  /**
   * Call a tool and get the normalised outcome without exceptions.
   *
   * Preferred for new UI code that wants to render "awaiting approval" or
   * "denied" states rather than treat them as errors.
   */
  async callToolDetailed(toolName, args = {}) {
    return await apiClient.callTool(toolName, args);
  }

  /**
   * Load available tools from server
   */
  async loadTools() {
    try {
      console.log('📋 Loading tools from backend...');
      
      // Use direct fetch for tools/list endpoint since it's a GET request
      const response = await fetch(`${this.serverUrl}/tools/list`, {
        method: 'GET',
        headers: {
          'Accept': 'application/json'
        }
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      if (data.result && data.result.tools) {
        const backendTools = data.result.tools;
        console.log(`✅ Loaded ${backendTools.length} tools from backend`);
        
        // Merge backend tools with detailed schemas for better AI understanding
        this.tools = this.enhanceToolsWithSchemas(backendTools);
      } else {
        throw new Error('Invalid tools response format');
      }
    } catch (loadError) {
      console.warn('⚠️ Failed to load tools from backend, using fallback list:', loadError.message);
      this.tools = [
        // Patient Management
        { 
          name: 'list_patients', 
          description: 'List all patients in the database',
          inputSchema: {
            type: 'object',
            properties: {},
            required: []
          }
        },
        { 
          name: 'create_patient', 
          description: 'Create a new patient record',
          inputSchema: {
            type: 'object',
            properties: {
              patient_number: { type: 'string', description: 'Patient number (auto-generated if not provided)' },
              first_name: { type: 'string', description: 'Patient first name' },
              last_name: { type: 'string', description: 'Patient last name' },
              date_of_birth: { type: 'string', description: 'Date of birth (YYYY-MM-DD)' },
              gender: { type: 'string', description: 'Gender (Male/Female/Other)' },
              phone: { type: 'string', description: 'Phone number' },
              email: { type: 'string', description: 'Email address' },
              address: { type: 'string', description: 'Home address' }
            },
            required: ['first_name', 'last_name', 'date_of_birth']
          }
        },
        { 
          name: 'get_patient_by_id', 
          description: 'Get a patient by ID or patient number',
          inputSchema: {
            type: 'object',
            properties: {
              patient_id: { type: 'string', description: 'Patient ID or patient number' }
            },
            required: ['patient_id']
          }
        },
        { 
          name: 'search_patients', 
          description: 'Search patients by various criteria',
          inputSchema: {
            type: 'object',
            properties: {
              patient_number: { type: 'string', description: 'Search by patient number' },
              first_name: { type: 'string', description: 'Search by first name' },
              last_name: { type: 'string', description: 'Search by last name' },
              phone: { type: 'string', description: 'Search by phone number' },
              email: { type: 'string', description: 'Search by email address' }
            },
            required: []
          }
        },
        
        // Department Management
        { 
          name: 'list_departments', 
          description: 'List all departments',
          inputSchema: {
            type: 'object',
            properties: {},
            required: []
          }
        },
        { 
          name: 'create_department', 
          description: 'Create a new department',
          inputSchema: {
            type: 'object',
            properties: {
              name: { type: 'string', description: 'Department name' },
              description: { type: 'string', description: 'Department description (optional)' },
              floor_number: { type: 'integer', description: 'Floor number (optional)' },
              head_doctor_id: { type: 'string', description: 'Head doctor ID (optional)' },
              phone: { type: 'string', description: 'Department phone (optional)' },
              email: { type: 'string', description: 'Department email (optional)' }
            },
            required: ['name']
          }
        },
        { 
          name: 'get_department_by_id', 
          description: 'Get a department by ID',
          inputSchema: {
            type: 'object',
            properties: {
              department_id: { type: 'string', description: 'Department ID' }
            },
            required: ['department_id']
          }
        },
        
        // Staff Management
        { 
          name: 'list_staff', 
          description: 'List all staff members',
          inputSchema: {
            type: 'object',
            properties: {
              department_id: { type: 'string', description: 'Filter by department ID (optional)' },
              status: { type: 'string', description: 'Filter by status (optional)' }
            },
            required: []
          }
        },
        { 
          name: 'create_staff', 
          description: 'Create a new staff member',
          inputSchema: {
            type: 'object',
            properties: {
              user_id: { type: 'string', description: 'User ID (UUID)' },
              employee_id: { type: 'string', description: 'Employee ID' },
              department_id: { type: 'string', description: 'Department ID (UUID)' },
              position: { type: 'string', description: 'Job position (Doctor, Nurse, etc.)' },
              specialization: { type: 'string', description: 'Medical specialization' },
              license_number: { type: 'string', description: 'Medical license number' },
              hire_date: { type: 'string', description: 'Hire date (YYYY-MM-DD)' },
              salary: { type: 'number', description: 'Salary amount' },
              shift_pattern: { type: 'string', description: 'Shift pattern (Day, Night, etc.)' },
              status: { type: 'string', description: 'Employment status (active, inactive)' }
            },
            required: ['user_id', 'employee_id', 'department_id', 'position']
          }
        },
        { 
          name: 'get_staff_by_id', 
          description: 'Get a staff member by ID',
          inputSchema: {
            type: 'object',
            properties: {
              staff_id: { type: 'string', description: 'Staff ID or employee ID' }
            },
            required: ['staff_id']
          }
        },
        
        // User Management
        { 
          name: 'list_users', 
          description: 'List all users',
          inputSchema: {
            type: 'object',
            properties: {},
            required: []
          }
        },
        { 
          name: 'create_user', 
          description: 'Create a new user',
          inputSchema: {
            type: 'object',
            properties: {
              username: { type: 'string', description: 'Username for the user' },
              email: { type: 'string', description: 'Email address' },
              password_hash: { type: 'string', description: 'Password hash (use "temp_password" for demo)' },
              role: { type: 'string', description: 'User role (admin, doctor, nurse, etc.)' },
              first_name: { type: 'string', description: 'First name' },
              last_name: { type: 'string', description: 'Last name' },
              phone: { type: 'string', description: 'Phone number (optional)' }
            },
            required: ['username', 'email', 'password_hash', 'role', 'first_name', 'last_name']
          }
        },
        { 
          name: 'get_user_by_id', 
          description: 'Get a user by ID',
          inputSchema: {
            type: 'object',
            properties: {
              user_id: { type: 'string', description: 'User ID' }
            },
            required: ['user_id']
          }
        },
        { 
          name: 'update_user', 
          description: 'Update user information',
          inputSchema: {
            type: 'object',
            properties: {
              user_id: { type: 'string', description: 'User ID' },
              username: { type: 'string', description: 'Username' },
              email: { type: 'string', description: 'Email address' },
              role: { type: 'string', description: 'User role' },
              first_name: { type: 'string', description: 'First name' },
              last_name: { type: 'string', description: 'Last name' },
              phone: { type: 'string', description: 'Phone number' },
              is_active: { type: 'boolean', description: 'Active status' }
            },
            required: ['user_id']
          }
        },
        { 
          name: 'delete_user', 
          description: 'Delete a user',
          inputSchema: {
            type: 'object',
            properties: {
              user_id: { type: 'string', description: 'User ID' }
            },
            required: ['user_id']
          }
        },
        
        // Room Management
        { 
          name: 'list_rooms', 
          description: 'List all rooms',
          inputSchema: {
            type: 'object',
            properties: {},
            required: []
          }
        },
        { 
          name: 'create_room', 
          description: 'Create a new room',
          inputSchema: {
            type: 'object',
            properties: {
              room_number: { type: 'string', description: 'Room number' },
              department_id: { type: 'string', description: 'Department ID (UUID)' },
              room_type: { type: 'string', description: 'Room type (ICU, General, etc.)' },
              capacity: { type: 'integer', description: 'Room capacity' },
              floor_number: { type: 'integer', description: 'Floor number' }
            },
            required: ['room_number', 'department_id']
          }
        },
        
        // Bed Management
        { 
          name: 'list_beds', 
          description: 'List all beds',
          inputSchema: {
            type: 'object',
            properties: {
              status: { type: 'string', description: 'Filter by bed status (available, occupied, maintenance)' }
            },
            required: []
          }
        },
        { 
          name: 'create_bed', 
          description: 'Create a new bed in a specific room',
          inputSchema: {
            type: 'object',
            properties: {
              bed_number: { type: 'string', description: 'Bed number (e.g., "B-101-01", "Bed-1")' },
              room_id: { type: 'string', description: 'Room ID (UUID) - if user provides room name/number, search list_rooms first' },
              bed_type: { type: 'string', description: 'Bed type (ICU, General, Private, etc.)' },
              status: { type: 'string', description: 'Bed status (available, occupied, maintenance)' }
            },
            required: ['bed_number', 'room_id']
          }
        },
        { 
          name: 'assign_bed_to_patient', 
          description: 'Assign a bed to a patient',
          inputSchema: {
            type: 'object',
            properties: {
              bed_id: { type: 'string', description: 'Bed ID' },
              patient_id: { type: 'string', description: 'Patient ID' },
              admission_date: { type: 'string', description: 'Admission date (YYYY-MM-DD)' }
            },
            required: ['bed_id', 'patient_id']
          }
        },
        { 
          name: 'discharge_bed', 
          description: 'Discharge a patient from a bed',
          inputSchema: {
            type: 'object',
            properties: {
              bed_id: { type: 'string', description: 'Bed ID' },
              discharge_date: { type: 'string', description: 'Discharge date (YYYY-MM-DD)' }
            },
            required: ['bed_id']
          }
        },
        
        // Equipment Management
        { 
          name: 'list_equipment', 
          description: 'List all equipment',
          inputSchema: {
            type: 'object',
            properties: {
              department_id: { type: 'string', description: 'Filter by department ID (optional)' },
              status: { type: 'string', description: 'Filter by status (optional)' }
            },
            required: []
          }
        },
        { 
          name: 'create_equipment', 
          description: 'Create a new equipment item',
          inputSchema: {
            type: 'object',
            properties: {
              equipment_id: { type: 'string', description: 'Equipment ID' },
              name: { type: 'string', description: 'Equipment name' },
              category_id: { type: 'string', description: 'Equipment category ID' },
              manufacturer: { type: 'string', description: 'Manufacturer' },
              model: { type: 'string', description: 'Model' },
              serial_number: { type: 'string', description: 'Serial number' },
              department_id: { type: 'string', description: 'Department ID' },
              location: { type: 'string', description: 'Equipment location' },
              purchase_date: { type: 'string', description: 'Purchase date (YYYY-MM-DD)' },
              cost: { type: 'number', description: 'Purchase cost' },
              warranty_expiry: { type: 'string', description: 'Warranty expiry date (YYYY-MM-DD)' }
            },
            required: ['equipment_id', 'name', 'category_id']
          }
        },
        { 
          name: 'get_equipment_by_id', 
          description: 'Get equipment by ID',
          inputSchema: {
            type: 'object',
            properties: {
              equipment_id: { type: 'string', description: 'Equipment ID' }
            },
            required: ['equipment_id']
          }
        },
        { 
          name: 'update_equipment_status', 
          description: 'Update equipment status',
          inputSchema: {
            type: 'object',
            properties: {
              equipment_id: { type: 'string', description: 'Equipment ID' },
              status: { type: 'string', description: 'New status (available, in_use, maintenance, retired)' },
              notes: { type: 'string', description: 'Additional notes about the status change' }
            },
            required: ['equipment_id', 'status']
          }
        },
        { 
          name: 'create_equipment_category', 
          description: 'Create an equipment category',
          inputSchema: {
            type: 'object',
            properties: {
              name: { type: 'string', description: 'Category name' },
              description: { type: 'string', description: 'Category description' }
            },
            required: ['name']
          }
        },
        
        // Supply Management
        { 
          name: 'list_supplies', 
          description: 'List all supplies',
          inputSchema: {
            type: 'object',
            properties: {
              low_stock_only: { type: 'boolean', description: 'Show only low stock items' }
            },
            required: []
          }
        },
        { 
          name: 'create_supply', 
          description: 'Create a new supply item',
          inputSchema: {
            type: 'object',
            properties: {
              item_code: { type: 'string', description: 'Item code' },
              name: { type: 'string', description: 'Supply name' },
              category_id: { type: 'string', description: 'Supply category ID' },
              unit_of_measure: { type: 'string', description: 'Unit of measure (pieces, kg, ml, etc.)' },
              description: { type: 'string', description: 'Supply description' },
              supplier: { type: 'string', description: 'Supplier name' },
              current_stock: { type: 'integer', description: 'Current stock level' },
              minimum_stock_level: { type: 'integer', description: 'Minimum stock level' },
              maximum_stock_level: { type: 'integer', description: 'Maximum stock level' },
              unit_cost: { type: 'number', description: 'Cost per unit' },
              location: { type: 'string', description: 'Storage location' },
              expiry_date: { type: 'string', description: 'Expiry date (YYYY-MM-DD)' }
            },
            required: ['item_code', 'name', 'category_id', 'unit_of_measure']
          }
        },
        { 
          name: 'update_supply_stock', 
          description: 'Update supply stock levels',
          inputSchema: {
            type: 'object',
            properties: {
              supply_id: { type: 'string', description: 'Supply ID' },
              quantity_change: { type: 'integer', description: 'Quantity change (positive for addition, negative for removal)' },
              transaction_type: { type: 'string', description: 'Transaction type (purchase, usage, adjustment, etc.)' },
              performed_by: { type: 'string', description: 'Person performing the transaction' },
              unit_cost: { type: 'number', description: 'Cost per unit (optional)' },
              reference_number: { type: 'string', description: 'Reference number (invoice, order, etc.)' },
              notes: { type: 'string', description: 'Additional notes' }
            },
            required: ['supply_id', 'quantity_change', 'transaction_type', 'performed_by']
          }
        },
        { 
          name: 'create_supply_category', 
          description: 'Create a supply category',
          inputSchema: {
            type: 'object',
            properties: {
              name: { type: 'string', description: 'Category name' },
              description: { type: 'string', description: 'Category description' }
            },
            required: ['name']
          }
        },
        
        // Medical Document Management
        { 
          name: 'upload_medical_document', 
          description: 'Upload and process a medical document for a patient',
          inputSchema: {
            type: 'object',
            properties: {
              patient_id: { type: 'string', description: 'Patient ID (UUID) - REQUIRED' },
              document_type: { type: 'string', description: 'Document type (prescription, lab_result, imaging, discharge_summary, etc.) - REQUIRED' },
              file_name: { type: 'string', description: 'Original file name - REQUIRED' },
              file_data: { type: 'string', description: 'Base64 encoded file data - REQUIRED' },
              mime_type: { type: 'string', description: 'MIME type of the file (application/pdf, image/jpeg, etc.)' },
              description: { type: 'string', description: 'Document description' }
            },
            required: ['patient_id', 'document_type', 'file_name', 'file_data']
          }
        },
        { 
          name: 'list_medical_documents', 
          description: 'List medical documents for a patient or all patients',
          inputSchema: {
            type: 'object',
            properties: {
              patient_id: { type: 'string', description: 'Patient ID (UUID) to filter by specific patient' },
              document_type: { type: 'string', description: 'Document type to filter by' },
              processing_status: { type: 'string', description: 'Processing status (pending, processing, completed, failed)' }
            },
            required: []
          }
        },
        { 
          name: 'get_medical_document_by_id', 
          description: 'Get a specific medical document by ID',
          inputSchema: {
            type: 'object',
            properties: {
              document_id: { type: 'string', description: 'Medical document ID (UUID) - REQUIRED' }
            },
            required: ['document_id']
          }
        },
        { 
          name: 'extract_medical_data', 
          description: 'Extract structured medical data from a document using AI',
          inputSchema: {
            type: 'object',
            properties: {
              document_id: { type: 'string', description: 'Medical document ID (UUID) - REQUIRED' }
            },
            required: ['document_id']
          }
        },
        { 
          name: 'query_medical_history', 
          description: 'Query patient medical history using natural language',
          inputSchema: {
            type: 'object',
            properties: {
              patient_id: { type: 'string', description: 'Patient ID (UUID) - REQUIRED' },
              query: { type: 'string', description: 'Natural language query about medical history - REQUIRED' },
              include_documents: { type: 'boolean', description: 'Include document references in response' }
            },
            required: ['patient_id', 'query']
          }
        },

        // Meeting Management
        { 
          name: 'schedule_meeting', 
          description: 'Schedule a meeting with natural language processing',
          inputSchema: {
            type: 'object',
            properties: {
              query: { type: 'string', description: 'Natural language meeting request (e.g., "Schedule a meeting with Dr. Smith tomorrow at 2 PM") - REQUIRED' }
            },
            required: ['query']
          }
        },
        { 
          name: 'list_meetings', 
          description: 'List upcoming meetings',
          inputSchema: {
            type: 'object',
            properties: {
              date_str: { type: 'string', description: 'Specific date to filter meetings (YYYY-MM-DD)' },
              days_ahead: { type: 'integer', description: 'Number of days ahead to look for meetings (default: 7)' }
            },
            required: []
          }
        },
        { 
          name: 'get_meeting_by_id', 
          description: 'Get detailed meeting information by ID',
          inputSchema: {
            type: 'object',
            properties: {
              meeting_id: { type: 'string', description: 'Meeting ID (UUID) - REQUIRED' }
            },
            required: ['meeting_id']
          }
        },
        { 
          name: 'update_meeting_status', 
          description: 'Update meeting status (scheduled, completed, cancelled)',
          inputSchema: {
            type: 'object',
            properties: {
              meeting_id: { type: 'string', description: 'Meeting ID (UUID) - REQUIRED' },
              status: { type: 'string', description: 'New status (scheduled, completed, cancelled) - REQUIRED' }
            },
            required: ['meeting_id', 'status']
          }
        },
        { 
          name: 'add_meeting_notes', 
          description: 'Add notes or action items to a meeting',
          inputSchema: {
            type: 'object',
            properties: {
              meeting_id: { type: 'string', description: 'Meeting ID (UUID) - REQUIRED' },
              notes: { type: 'string', description: 'Meeting notes or action items - REQUIRED' }
            },
            required: ['meeting_id', 'notes']
          }
        },
        { 
          name: 'update_meeting', 
          description: 'Update meeting date/time and notify all participants',
          inputSchema: {
            type: 'object',
            properties: {
              query: { type: 'string', description: 'Natural language meeting update request (e.g., "Postpone the Tasks Improvements meeting to tomorrow at 3 PM", "Reschedule meeting ID abc-123 to Friday at 2:30 PM") - REQUIRED' }
            },
            required: ['query']
          }
        },

        // Advanced Reporting & Analytics
        { 
          name: 'generate_discharge_report', 
          description: 'Generate a comprehensive discharge report for a patient',
          inputSchema: {
            type: 'object',
            properties: {
              bed_id: { type: 'string', description: 'Bed ID (UUID) - REQUIRED' },
              discharge_condition: { type: 'string', description: 'Patient discharge condition (stable, improved, etc.)' },
              discharge_destination: { type: 'string', description: 'Discharge destination (home, transfer, etc.)' }
            },
            required: ['bed_id']
          }
        },
        { 
          name: 'list_discharge_reports', 
          description: 'List all discharge reports with optional filtering',
          inputSchema: {
            type: 'object',
            properties: {
              patient_id: { type: 'string', description: 'Filter by patient ID' },
              date_range: { type: 'string', description: 'Date range filter (last_week, last_month, etc.)' }
            },
            required: []
          }
        },
        { 
          name: 'get_bed_turnover_status', 
          description: 'Get bed turnover and cleaning status',
          inputSchema: {
            type: 'object',
            properties: {
              bed_id: { type: 'string', description: 'Bed ID (UUID)' },
              department_id: { type: 'string', description: 'Department ID (UUID)' }
            },
            required: []
          }
        },
        { 
          name: 'get_hospital_statistics', 
          description: 'Get comprehensive hospital statistics and analytics',
          inputSchema: {
            type: 'object',
            properties: {
              report_type: { type: 'string', description: 'Type of report (occupancy, staff_utilization, equipment_usage, patient_flow)' },
              time_period: { type: 'string', description: 'Time period (daily, weekly, monthly, yearly)' },
              department_id: { type: 'string', description: 'Filter by specific department' }
            },
            required: []
          }
        },
        { 
          name: 'generate_patient_summary', 
          description: 'Generate a comprehensive patient summary report',
          inputSchema: {
            type: 'object',
            properties: {
              patient_id: { type: 'string', description: 'Patient ID (UUID) - REQUIRED' },
              include_medical_history: { type: 'boolean', description: 'Include medical history in summary' },
              include_documents: { type: 'boolean', description: 'Include document summaries' }
            },
            required: ['patient_id']
          }
        },

        // Legacy and System Management
        { 
          name: 'create_legacy_user', 
          description: 'Create a legacy user',
          inputSchema: {
            type: 'object',
            properties: {
              name: { type: 'string', description: 'Full name' },
              email: { type: 'string', description: 'Email address' },
              address: { type: 'string', description: 'Address' },
              phone: { type: 'string', description: 'Phone number' }
            },
            required: ['name', 'email', 'address', 'phone']
          }
        },
        { 
          name: 'list_legacy_users', 
          description: 'List all legacy users',
          inputSchema: {
            type: 'object',
            properties: {},
            required: []
          }
        },
        { 
          name: 'log_agent_interaction', 
          description: 'Log an AI agent interaction',
          inputSchema: {
            type: 'object',
            properties: {
              agent_type: { type: 'string', description: 'Agent type' },
              query: { type: 'string', description: 'Query' },
              response: { type: 'string', description: 'Response' },
              action_taken: { type: 'string', description: 'Action taken' },
              confidence_score: { type: 'number', description: 'Confidence score' },
              execution_time_ms: { type: 'integer', description: 'Execution time in milliseconds' },
              user_id: { type: 'string', description: 'User ID' }
            },
            required: ['agent_type', 'query', 'response']
          }
        }
      ];
    }
  }

  /**
   * Load available agents from server
   */
  async loadAgents() {
    try {
      console.log('👥 Loading agents from backend...');
      
      const response = await this.callTool('list_agents', {});
      console.log('👥 Raw agents response:', response);
      
      // Handle MCP response format - response.result.content[0].text contains JSON
      let agentsData = null;
      if (response.result && response.result.content && response.result.content[0] && response.result.content[0].text) {
        try {
          agentsData = JSON.parse(response.result.content[0].text);
          console.log('👥 Parsed agents data:', agentsData);
        } catch (parseError) {
          console.warn('⚠️ Failed to parse agents JSON:', parseError);
          agentsData = response;
        }
      } else {
        agentsData = response;
      }
      
      if (agentsData && agentsData.success && agentsData.agents) {
        this.agents = agentsData.agents;
        console.log(`✅ Loaded ${this.agents.length} agents from backend:`, this.agents);
        return this.agents;
      } else {
        throw new Error('Invalid agents response format');
      }
    } catch (loadError) {
      console.warn('⚠️ Failed to load agents from backend:', loadError.message);
      this.agents = [];
      return [];
    }
  }

  /**
   * Get available agents
   */
  getAgents() {
    return this.agents || [];
  }

  /**
   * Enhance backend tools with detailed schemas for better AI understanding
   */
  enhanceToolsWithSchemas(backendTools) {
    const detailedSchemas = {
      'add_equipment_usage_by_codes': {
        type: 'object',
        properties: {
          patient_number: { type: 'string', description: 'Patient number (e.g., "P591793") - REQUIRED' },
          equipment_id: { type: 'string', description: 'Equipment ID/code (e.g., "EQ001") - REQUIRED' },
          employee_id: { type: 'string', description: 'Employee ID (e.g., "EMP001") - REQUIRED' },
          purpose: { type: 'string', description: 'Purpose of equipment usage (e.g., "Monitoring", "Treatment") - REQUIRED' },
          start_time: { type: 'string', description: 'Start time (ISO string, optional)' },
          end_time: { type: 'string', description: 'End time (ISO string, optional)' },
          notes: { type: 'string', description: 'Additional notes (optional)' }
        },
        required: ['patient_number', 'equipment_id', 'employee_id', 'purpose']
      },
      'add_treatment_record_by_codes': {
        type: 'object',
        properties: {
          patient_number: { type: 'string', description: 'Patient number (e.g., "P591793") - REQUIRED' },
          employee_id: { type: 'string', description: 'Employee ID (e.g., "EMP001") - REQUIRED' },
          treatment_type: { type: 'string', description: 'Type of treatment (e.g., "Medication", "Surgery", "Therapy") - REQUIRED' },
          treatment_name: { type: 'string', description: 'Name of the treatment or procedure (e.g., "Paracetamol 500mg", "Appendectomy") - REQUIRED' },
          start_date: { type: 'string', description: 'Start date of treatment (YYYY-MM-DD) - REQUIRED' },
          end_date: { type: 'string', description: 'End date of treatment (YYYY-MM-DD, optional)' },
          notes: { type: 'string', description: 'Additional notes (optional)' }
        },
        required: ['patient_number', 'employee_id', 'treatment_type', 'treatment_name', 'start_date']
      },
      // BED MANAGEMENT
      'create_bed': {
        type: 'object',
        properties: {
          bed_number: { type: 'string', description: 'Bed number (e.g., "B-101-01", "Bed-1") - REQUIRED' },
          room_id: { type: 'string', description: 'Room ID (UUID) - if user provides room name/number, search list_rooms first' },
          bed_type: { type: 'string', description: 'Bed type (ICU, General, Private, etc.)' },
          status: { type: 'string', description: 'Bed status (available, occupied, maintenance)' }
        },
        required: ['bed_number', 'room_id']
      },
      'list_beds': {
        type: 'object',
        properties: {
          status: { type: 'string', description: 'Filter by bed status (available, occupied, maintenance)' }
        },
        required: []
      },
      'assign_bed_to_patient': {
        type: 'object',
        properties: {
          bed_id: { type: 'string', description: 'Bed ID (UUID) - REQUIRED' },
          patient_id: { type: 'string', description: 'Patient ID (UUID) - REQUIRED' },
          admission_date: { type: 'string', description: 'Admission date (YYYY-MM-DD)' }
        },
        required: ['bed_id', 'patient_id']
      },
      'discharge_bed': {
        type: 'object',
        properties: {
          bed_id: { type: 'string', description: 'Bed ID (UUID) - REQUIRED' },
          discharge_date: { type: 'string', description: 'Discharge date (YYYY-MM-DD)' }
        },
        required: ['bed_id']
      },

      // PATIENT MANAGEMENT
      'create_patient': {
        type: 'object',
        properties: {
          patient_number: { type: 'string', description: 'Patient number (auto-generated if not provided)' },
          first_name: { type: 'string', description: 'Patient first name - REQUIRED' },
          last_name: { type: 'string', description: 'Patient last name - REQUIRED' },
          date_of_birth: { type: 'string', description: 'Date of birth (YYYY-MM-DD) - REQUIRED' },
          gender: { type: 'string', description: 'Gender (Male/Female/Other)' },
          phone: { type: 'string', description: 'Phone number' },
          email: { type: 'string', description: 'Email address' },
          address: { type: 'string', description: 'Home address' },
          emergency_contact_name: { type: 'string', description: 'Emergency contact name' },
          emergency_contact_phone: { type: 'string', description: 'Emergency contact phone' },
          blood_type: { type: 'string', description: 'Blood type (A+, B+, O+, etc.)' },
          allergies: { type: 'string', description: 'Known allergies' },
          medical_history: { type: 'string', description: 'Medical history' }
        },
        required: ['first_name', 'last_name', 'date_of_birth']
      },
      'get_patient_by_id': {
        type: 'object',
        properties: {
          patient_id: { type: 'string', description: 'Patient ID or patient number - REQUIRED' }
        },
        required: ['patient_id']
      },
      'search_patients': {
        type: 'object',
        properties: {
          patient_number: { type: 'string', description: 'Search by patient number' },
          first_name: { type: 'string', description: 'Search by first name' },
          last_name: { type: 'string', description: 'Search by last name' },
          phone: { type: 'string', description: 'Search by phone number' },
          email: { type: 'string', description: 'Search by email address' }
        },
        required: []
      },
      'list_patients': {
        type: 'object',
        properties: {},
        required: []
      },

      // ROOM MANAGEMENT
      'create_room': {
        type: 'object',
        properties: {
          room_number: { type: 'string', description: 'Room number (e.g., "101", "ICU-01") - REQUIRED' },
          department_id: { type: 'string', description: 'Department ID (UUID) - REQUIRED - search list_departments first if user provides department name' },
          room_type: { type: 'string', description: 'Room type (ICU, General, Private, Emergency, etc.)' },
          capacity: { type: 'integer', description: 'Room capacity (number of beds)' },
          floor_number: { type: 'integer', description: 'Floor number' }
        },
        required: ['room_number', 'department_id']
      },
      'list_rooms': {
        type: 'object',
        properties: {},
        required: []
      },

      // USER MANAGEMENT
      'create_user': {
        type: 'object',
        properties: {
          username: { type: 'string', description: 'Username for the user - REQUIRED' },
          email: { type: 'string', description: 'Email address - REQUIRED' },
          password_hash: { type: 'string', description: 'Password hash (use "temp_password" for demo) - REQUIRED' },
          role: { type: 'string', description: 'User role (admin, doctor, nurse, receptionist, etc.) - REQUIRED' },
          first_name: { type: 'string', description: 'First name - REQUIRED' },
          last_name: { type: 'string', description: 'Last name - REQUIRED' },
          phone: { type: 'string', description: 'Phone number (optional)' }
        },
        required: ['username', 'email', 'password_hash', 'role', 'first_name', 'last_name']
      },
      'get_user_by_id': {
        type: 'object',
        properties: {
          user_id: { type: 'string', description: 'User ID (UUID) - REQUIRED' }
        },
        required: ['user_id']
      },
      'update_user': {
        type: 'object',
        properties: {
          user_id: { type: 'string', description: 'User ID (UUID) - REQUIRED' },
          username: { type: 'string', description: 'Username' },
          email: { type: 'string', description: 'Email address' },
          role: { type: 'string', description: 'User role' },
          first_name: { type: 'string', description: 'First name' },
          last_name: { type: 'string', description: 'Last name' },
          phone: { type: 'string', description: 'Phone number' },
          is_active: { type: 'boolean', description: 'Active status' }
        },
        required: ['user_id']
      },
      'delete_user': {
        type: 'object',
        properties: {
          user_id: { type: 'string', description: 'User ID (UUID) - REQUIRED' }
        },
        required: ['user_id']
      },
      'list_users': {
        type: 'object',
        properties: {},
        required: []
      },

      // DEPARTMENT MANAGEMENT
      'create_department': {
        type: 'object',
        properties: {
          name: { type: 'string', description: 'Department name (e.g., "Emergency", "Cardiology") - REQUIRED' },
          description: { type: 'string', description: 'Department description (optional)' },
          floor_number: { type: 'integer', description: 'Floor number (optional)' },
          head_doctor_id: { type: 'string', description: 'Head doctor ID (UUID) (optional)' },
          phone: { type: 'string', description: 'Department phone (optional)' },
          email: { type: 'string', description: 'Department email (optional)' }
        },
        required: ['name']
      },
      'get_department_by_id': {
        type: 'object',
        properties: {
          department_id: { type: 'string', description: 'Department ID (UUID) - REQUIRED' }
        },
        required: ['department_id']
      },
      'list_departments': {
        type: 'object',
        properties: {},
        required: []
      },

      // STAFF MANAGEMENT
      'create_staff': {
        type: 'object',
        properties: {
          user_id: { type: 'string', description: 'User ID (UUID) - REQUIRED - search list_users first if user provides name' },
          employee_id: { type: 'string', description: 'Employee ID (e.g., "EMP001") - REQUIRED' },
          department_id: { type: 'string', description: 'Department ID (UUID) - REQUIRED - search list_departments first if user provides department name' },
          position: { type: 'string', description: 'Job position (Doctor, Nurse, Technician, etc.) - REQUIRED' },
          specialization: { type: 'string', description: 'Medical specialization (Cardiology, Surgery, etc.)' },
          license_number: { type: 'string', description: 'Medical license number' },
          hire_date: { type: 'string', description: 'Hire date (YYYY-MM-DD)' },
          salary: { type: 'number', description: 'Salary amount' },
          shift_pattern: { type: 'string', description: 'Shift pattern (Day, Night, Rotating, etc.)' },
          status: { type: 'string', description: 'Employment status (active, inactive, on_leave)' }
        },
        required: ['user_id', 'employee_id', 'department_id', 'position']
      },
      'get_staff_by_id': {
        type: 'object',
        properties: {
          staff_id: { type: 'string', description: 'Staff ID or employee ID - REQUIRED' }
        },
        required: ['staff_id']
      },
      'list_staff': {
        type: 'object',
        properties: {
          department_id: { type: 'string', description: 'Filter by department ID (optional)' },
          status: { type: 'string', description: 'Filter by status (optional)' }
        },
        required: []
      },

      // EQUIPMENT MANAGEMENT
      'create_equipment': {
        type: 'object',
        properties: {
          equipment_id: { type: 'string', description: 'Equipment ID (e.g., "EQ001") - REQUIRED' },
          name: { type: 'string', description: 'Equipment name (e.g., "MRI Scanner", "X-Ray Machine") - REQUIRED' },
          category_id: { type: 'string', description: 'Equipment category ID (UUID) - REQUIRED' },
          manufacturer: { type: 'string', description: 'Manufacturer' },
          model: { type: 'string', description: 'Model' },
          serial_number: { type: 'string', description: 'Serial number' },
          department_id: { type: 'string', description: 'Department ID (UUID)' },
          location: { type: 'string', description: 'Equipment location' },
          purchase_date: { type: 'string', description: 'Purchase date (YYYY-MM-DD)' },
          cost: { type: 'number', description: 'Purchase cost' },
          warranty_expiry: { type: 'string', description: 'Warranty expiry date (YYYY-MM-DD)' }
        },
        required: ['equipment_id', 'name', 'category_id']
      },
      'get_equipment_by_id': {
        type: 'object',
        properties: {
          equipment_id: { type: 'string', description: 'Equipment ID - REQUIRED' }
        },
        required: ['equipment_id']
      },
      'update_equipment_status': {
        type: 'object',
        properties: {
          equipment_id: { type: 'string', description: 'Equipment ID - REQUIRED' },
          status: { type: 'string', description: 'New status (available, in_use, maintenance, retired) - REQUIRED' },
          notes: { type: 'string', description: 'Additional notes about the status change' }
        },
        required: ['equipment_id', 'status']
      },
      'create_equipment_category': {
        type: 'object',
        properties: {
          name: { type: 'string', description: 'Category name (e.g., "Imaging", "Laboratory") - REQUIRED' },
          description: { type: 'string', description: 'Category description' }
        },
        required: ['name']
      },
      'list_equipment': {
        type: 'object',
        properties: {
          department_id: { type: 'string', description: 'Filter by department ID (optional)' },
          status: { type: 'string', description: 'Filter by status (optional)' }
        },
        required: []
      },

      // SUPPLY MANAGEMENT
      'create_supply': {
        type: 'object',
        properties: {
          item_code: { type: 'string', description: 'Item code (e.g., "SUP001") - REQUIRED' },
          name: { type: 'string', description: 'Supply name (e.g., "Surgical Gloves", "Bandages") - REQUIRED' },
          category_id: { type: 'string', description: 'Supply category ID (UUID) - REQUIRED' },
          unit_of_measure: { type: 'string', description: 'Unit of measure (pieces, kg, ml, boxes, etc.) - REQUIRED' },
          description: { type: 'string', description: 'Supply description' },
          supplier: { type: 'string', description: 'Supplier name' },
          current_stock: { type: 'integer', description: 'Current stock level' },
          minimum_stock_level: { type: 'integer', description: 'Minimum stock level' },
          maximum_stock_level: { type: 'integer', description: 'Maximum stock level' },
          unit_cost: { type: 'number', description: 'Cost per unit' },
          location: { type: 'string', description: 'Storage location' },
          expiry_date: { type: 'string', description: 'Expiry date (YYYY-MM-DD)' }
        },
        required: ['item_code', 'name', 'category_id', 'unit_of_measure']
      },
      'update_supply_stock': {
        type: 'object',
        properties: {
          supply_id: { type: 'string', description: 'Supply ID (UUID) - REQUIRED' },
          quantity_change: { type: 'integer', description: 'Quantity change (positive for addition, negative for removal) - REQUIRED' },
          transaction_type: { type: 'string', description: 'Transaction type (purchase, usage, adjustment, etc.) - REQUIRED' },
          performed_by: { type: 'string', description: 'Person performing the transaction - REQUIRED' },
          unit_cost: { type: 'number', description: 'Cost per unit (optional)' },
          reference_number: { type: 'string', description: 'Reference number (invoice, order, etc.)' },
          notes: { type: 'string', description: 'Additional notes' }
        },
        required: ['supply_id', 'quantity_change', 'transaction_type', 'performed_by']
      },
      'create_supply_category': {
        type: 'object',
        properties: {
          name: { type: 'string', description: 'Category name (e.g., "Medical Supplies", "Pharmaceuticals") - REQUIRED' },
          description: { type: 'string', description: 'Category description' }
        },
        required: ['name']
      },
      'list_supplies': {
        type: 'object',
        properties: {
          low_stock_only: { type: 'boolean', description: 'Show only low stock items' }
        },
        required: []
      },

      // MEDICAL DOCUMENT MANAGEMENT
      'upload_medical_document': {
        type: 'object',
        properties: {
          patient_id: { type: 'string', description: 'Patient ID (UUID) - REQUIRED' },
          document_type: { type: 'string', description: 'Document type (prescription, lab_result, imaging, discharge_summary, report, x_ray, mri, ct_scan, blood_test, etc.) - REQUIRED' },
          file_name: { type: 'string', description: 'Original file name with extension - REQUIRED' },
          file_data: { type: 'string', description: 'Base64 encoded file data - REQUIRED' },
          mime_type: { type: 'string', description: 'MIME type (application/pdf, image/jpeg, image/png, etc.)' },
          description: { type: 'string', description: 'Document description or notes' }
        },
        required: ['patient_id', 'document_type', 'file_name', 'file_data']
      },
      'list_medical_documents': {
        type: 'object',
        properties: {
          patient_id: { type: 'string', description: 'Filter by patient ID (UUID)' },
          document_type: { type: 'string', description: 'Filter by document type' },
          processing_status: { type: 'string', description: 'Filter by processing status (pending, processing, completed, failed)' },
          limit: { type: 'integer', description: 'Maximum number of documents to return' }
        },
        required: []
      },
      'get_medical_document_by_id': {
        type: 'object',
        properties: {
          document_id: { type: 'string', description: 'Medical document ID (UUID) - REQUIRED' },
          include_extracted_data: { type: 'boolean', description: 'Include extracted medical data in response' }
        },
        required: ['document_id']
      },
      'extract_medical_data': {
        type: 'object',
        properties: {
          document_id: { type: 'string', description: 'Medical document ID (UUID) - REQUIRED' },
          force_reprocess: { type: 'boolean', description: 'Force reprocessing even if already processed' }
        },
        required: ['document_id']
      },
      'query_medical_history': {
        type: 'object',
        properties: {
          patient_id: { type: 'string', description: 'Patient ID (UUID) - REQUIRED' },
          query: { type: 'string', description: 'Natural language query (e.g., "What medications is the patient taking?", "Any recent lab results?") - REQUIRED' },
          include_documents: { type: 'boolean', description: 'Include document references and excerpts in response' },
          time_range: { type: 'string', description: 'Time range to search (last_week, last_month, last_year, all)' }
        },
        required: ['patient_id', 'query']
      },

      // MEETING MANAGEMENT
      'schedule_meeting': {
        type: 'object',
        properties: {
          query: { type: 'string', description: 'Natural language meeting request - REQUIRED. Examples: "Schedule meeting with Dr. Smith tomorrow at 2 PM about patient care", "Book conference room for team meeting Friday morning"' }
        },
        required: ['query']
      },
      'list_meetings': {
        type: 'object',
        properties: {
          date_str: { type: 'string', description: 'Specific date to filter meetings (YYYY-MM-DD format)' },
          days_ahead: { type: 'integer', description: 'Number of days ahead to look for meetings (default: 7, max: 30)' },
          participant_id: { type: 'string', description: 'Filter meetings by participant user ID' },
          status: { type: 'string', description: 'Filter by meeting status (scheduled, completed, cancelled)' }
        },
        required: []
      },
      'get_meeting_by_id': {
        type: 'object',
        properties: {
          meeting_id: { type: 'string', description: 'Meeting ID (UUID) - REQUIRED' },
          include_participants: { type: 'boolean', description: 'Include detailed participant information' },
          include_notes: { type: 'boolean', description: 'Include meeting notes and action items' }
        },
        required: ['meeting_id']
      },
      'update_meeting_status': {
        type: 'object',
        properties: {
          meeting_id: { type: 'string', description: 'Meeting ID (UUID) - REQUIRED' },
          status: { type: 'string', description: 'New meeting status (scheduled, in_progress, completed, cancelled, postponed) - REQUIRED' },
          notes: { type: 'string', description: 'Optional notes about the status change' }
        },
        required: ['meeting_id', 'status']
      },
      'add_meeting_notes': {
        type: 'object',
        properties: {
          meeting_id: { type: 'string', description: 'Meeting ID (UUID) - REQUIRED' },
          notes: { type: 'string', description: 'Meeting notes, action items, or decisions made - REQUIRED' },
          note_type: { type: 'string', description: 'Type of note (general, action_item, decision, follow_up)' }
        },
        required: ['meeting_id', 'notes']
      },
      'update_meeting': {
        type: 'object',
        properties: {
          query: { type: 'string', description: 'Natural language meeting update request - REQUIRED. Examples: "Postpone the Tasks Improvements meeting to tomorrow at 3 PM", "Reschedule meeting ID abc-123 to Friday at 2:30 PM", "Move the staff meeting to next Monday at 10 AM"' }
        },
        required: ['query']
      },

      // ADVANCED REPORTING & ANALYTICS
      'generate_discharge_report': {
        type: 'object',
        properties: {
          bed_id: { type: 'string', description: 'Bed ID (UUID) where patient is currently assigned - REQUIRED' },
          discharge_condition: { type: 'string', description: 'Patient discharge condition (stable, improved, recovered, transferred, deceased, etc.)' },
          discharge_destination: { type: 'string', description: 'Discharge destination (home, another_facility, rehabilitation, hospice, etc.)' },
          discharge_instructions: { type: 'string', description: 'Special discharge instructions or medications' },
          follow_up_required: { type: 'boolean', description: 'Whether follow-up care is required' }
        },
        required: ['bed_id']
      },
      'list_discharge_reports': {
        type: 'object',
        properties: {
          patient_id: { type: 'string', description: 'Filter by specific patient ID (UUID)' },
          department_id: { type: 'string', description: 'Filter by department ID (UUID)' },
          date_range: { type: 'string', description: 'Date range (today, yesterday, last_week, last_month, last_quarter, last_year)' },
          start_date: { type: 'string', description: 'Custom start date (YYYY-MM-DD)' },
          end_date: { type: 'string', description: 'Custom end date (YYYY-MM-DD)' },
          discharge_condition: { type: 'string', description: 'Filter by discharge condition' }
        },
        required: []
      },
      'get_bed_turnover_status': {
        type: 'object',
        properties: {
          bed_id: { type: 'string', description: 'Specific bed ID (UUID) to check status' },
          room_id: { type: 'string', description: 'Room ID (UUID) to check all beds in room' },
          department_id: { type: 'string', description: 'Department ID (UUID) to check all beds in department' },
          status_filter: { type: 'string', description: 'Filter by turnover status (cleaning, ready, occupied, maintenance)' }
        },
        required: []
      },
      'get_hospital_statistics': {
        type: 'object',
        properties: {
          report_type: { type: 'string', description: 'Report type: occupancy_rate, patient_flow, staff_utilization, equipment_usage, department_performance, financial_summary' },
          time_period: { type: 'string', description: 'Time period: hourly, daily, weekly, monthly, quarterly, yearly' },
          department_id: { type: 'string', description: 'Filter by specific department ID (UUID)' },
          start_date: { type: 'string', description: 'Custom start date (YYYY-MM-DD)' },
          end_date: { type: 'string', description: 'Custom end date (YYYY-MM-DD)' },
          include_trends: { type: 'boolean', description: 'Include trend analysis and comparisons' }
        },
        required: []
      },
      'generate_patient_summary': {
        type: 'object',
        properties: {
          patient_id: { type: 'string', description: 'Patient ID (UUID) - REQUIRED' },
          include_medical_history: { type: 'boolean', description: 'Include detailed medical history' },
          include_documents: { type: 'boolean', description: 'Include summaries of uploaded medical documents' },
          include_medications: { type: 'boolean', description: 'Include current and past medications' },
          summary_type: { type: 'string', description: 'Type of summary (brief, detailed, comprehensive)' }
        },
        required: ['patient_id']
      },

      // LEGACY USER MANAGEMENT
      'create_legacy_user': {
        type: 'object',
        properties: {
          name: { type: 'string', description: 'Full name - REQUIRED' },
          email: { type: 'string', description: 'Email address - REQUIRED' },
          address: { type: 'string', description: 'Address - REQUIRED' },
          phone: { type: 'string', description: 'Phone number - REQUIRED' }
        },
        required: ['name', 'email', 'address', 'phone']
      },
      'list_legacy_users': {
        type: 'object',
        properties: {},
        required: []
      },

      // SYSTEM MANAGEMENT
      'log_agent_interaction': {
        type: 'object',
        properties: {
          agent_type: { type: 'string', description: 'Agent type - REQUIRED' },
          query: { type: 'string', description: 'Query - REQUIRED' },
          response: { type: 'string', description: 'Response - REQUIRED' },
          action_taken: { type: 'string', description: 'Action taken' },
          confidence_score: { type: 'number', description: 'Confidence score' },
          execution_time_ms: { type: 'integer', description: 'Execution time in milliseconds' },
          user_id: { type: 'string', description: 'User ID' }
        },
        required: ['agent_type', 'query', 'response']
      }
    };

    return backendTools.map(tool => ({
      ...tool,
      inputSchema: detailedSchemas[tool.name] || {
        type: 'object',
        properties: {},
        required: []
      }
    }));
  }

  /**
   * Send request and wait for response
   */
  async sendRequest(method, params = {}) {
    const id = this.generateId();
    const message = {
      jsonrpc: '2.0',
      id: id,
      method: method,
      params: params
    };
    
    try {
      console.log(`📤 Sending HTTP request: ${method}`, params);
      
      // Use the correct endpoint based on method
      let endpoint = '/tools/call';
      if (method === 'tools/list') {
        endpoint = '/tools/list';
      }
      
      const response = await fetch(`${this.serverUrl}${endpoint}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify(message)
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const result = await response.json();
      console.log(`📥 Received HTTP response:`, result);
      
      if (result.error) {
        throw new Error(result.error.message || 'Tool call failed');
      }
      
      return result;
    } catch (error) {
      console.error(`❌ HTTP request failed:`, error);
      throw error;
    }
  }

  /**
   * Generate unique request ID
   */
  getRequestId() {
    return ++this.requestId;
  }

  /**
   * Generate unique request ID (alias for compatibility)
   */
  generateId() {
    return this.getRequestId();
  }

  /**
   * Get available tools
   */
  getTools() {
    return this.tools;
  }

  /**
   * Get server information
   */
  getServerInfo() {
    return this.serverInfo;
  }

  /**
   * Check connection status
   */
  isConnectedToServer() {
    return this.isConnected;
  }

  /**
   * Get tool by name
   */
  getTool(toolName) {
    return this.tools.find(tool => tool.name === toolName);
  }

  /**
   * Get all tools with their schemas
   */
  getToolSchemas() {
    return this.tools.map(tool => ({
      name: tool.name,
      description: tool.description,
      inputSchema: tool.inputSchema || {}
    }));
  }

  /**
   * Disconnect from server
   */
  disconnect() {
    this.isConnected = false;
    this.tools = [];
    this.serverInfo = {};
    this.pendingRequests.clear();
    console.log('🔌 Disconnected from MCP server');
  }

  /**
   * Fallback simulation method (for development when backend is unavailable)
   */
  simulateToolCall(message) {
    // Dynamic tool execution with in-memory data store
    const toolName = message.params?.name;
    const args = message.params?.arguments || {};
    let simulatedResult;
    
    try {
      switch (toolName) {
        // Patient operations
        case 'list_patients': {
          simulatedResult = {
            content: [{
              type: 'text',
              text: JSON.stringify(this.dataStore.patients, null, 2)
            }]
          };
          break;
        }
          
        case 'create_patient': {
          const newPatient = {
            patient_id: `P${String(this.dataStore.patients.length + 1).padStart(3, '0')}`,
            patient_number: args.patient_number || `PAT${Date.now()}`,
            first_name: args.first_name,
            last_name: args.last_name,
            date_of_birth: args.date_of_birth,
            gender: args.gender || null,
            phone: args.phone || null,
            email: args.email || null,
            address: args.address || null,
            blood_type: args.blood_type || null,
            allergies: args.allergies || null,
            medical_history: args.medical_history || null,
            created_at: new Date().toISOString()
          };
          this.dataStore.patients.push(newPatient);
          simulatedResult = {
            content: [{
              type: 'text',
              text: `Patient created successfully: ${JSON.stringify(newPatient, null, 2)}`
            }]
          };
          break;
        }
        
        default: {
          simulatedResult = {
            content: [{
              type: 'text',
              text: `Tool ${toolName} executed with arguments: ${JSON.stringify(args, null, 2)}`
            }]
          };
        }
      }
    } catch (err) {
      simulatedResult = {
        content: [{
          type: 'text',
          text: `Error executing ${toolName}: ${err.message}`
        }]
      };
    }
    
    const result = {
      jsonrpc: '2.0',
      id: message.id,
      result: simulatedResult
    };
    
    // Simulate async response
    setTimeout(() => {
      this.handleMessage(result);
    }, 100);
    
    return result;
  }

  /**
   * Health check
   */
  async healthCheck() {
    try {
      const response = await fetch(`${this.serverUrl}/`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json'
        }
      });

      return response.ok;
    } catch (error) {
      console.error('❌ Health check failed:', error);
      return false;
    }
  }

  /**
   * Get server statistics
   */
  async getStats() {
    try {
      const response = await fetch(`${this.serverUrl}/stats`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        return await response.json();
      }
      return null;
    } catch (error) {
      console.error('❌ Failed to get stats:', error);
      return null;
    }
  }
}

export default DirectHttpMCPClient;
