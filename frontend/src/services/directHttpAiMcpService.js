/**
 * Direct HTTP AI MCP Service - Claude Desktop Style
 * Uses HTTP transport directly to FastMCP server with OpenAI function calling
 */

import DirectHttpMCPClient from './directHttpMcpClient.js';

class DirectHttpAIMCPService {
  /**
   * Return the agent's 'today' as the actual current date (localized, readable)
   */
  getTodayDate() {
    const now = new Date();
    return now.toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' });
  }

  /**
   * Detect short supply-usage messages and call backend tool directly to persist
   * Returns the tool response when handled, or null when not applicable
   */
  async handleSupplyUsageShortcut(userMessage) {
    try {
      const textLower = (userMessage || '').toLowerCase();
      if (!textLower.includes('record patient supply usage') && !textLower.includes('record patient supply') && !textLower.includes('administered')) {
        return null;
      }

      // Simple field extraction using regexes for common fields
      const getField = (regex) => {
        const m = userMessage.match(regex);
        return m ? m[1].trim() : null;
      };

      const patient_number = getField(/patient\s*(?:id|number)[:\s]+(P[0-9A-Za-z\-]+)/i) || getField(/patient[:\s]+(P[0-9A-Za-z\-]+)/i);
      const supply_item_code = getField(/supply\s*(?:item\s*)?code[:\s]+([A-Z0-9_\-]+)/i);
      const quantity_used_raw = getField(/quantity\s*used[:\s]+(\d+)/i);
      const quantity_used = quantity_used_raw ? parseInt(quantity_used_raw, 10) || 1 : 1;
      const date_of_usage = getField(/date\s*of\s*usage[:\s]+([0-9\-\/]+)/i);
      const employee_id = getField(/staff\s*id[:\s]+([A-Z0-9_\-]+)/i) || getField(/employee\s*id[:\s]+([A-Z0-9_\-]+)/i);
      const notes = getField(/notes[:\s]+(.+)/i) || null;

      if (patient_number && supply_item_code) {
        const args = {
          patient_number,
          supply_item_code,
          quantity_used,
          employee_id,
          date_of_usage,
          notes
        };

        // ensure client connected / initialized
        if (!this.isInitialized) {
          console.warn('DirectHttpAIMCPService not initialized - cannot call tool directly');
          return null;
        }

        try {
          const resp = await this.callToolDirectly('record_patient_supply_usage_by_code', args);
          return resp;
        } catch (err) {
          console.warn('Error calling record_patient_supply_usage_by_code:', err);
          return { success: false, error: err && err.message ? err.message : String(err) };
        }
      }
    } catch (err) {
      console.warn('Supply usage parse error:', err);
    }

    return null;
  }

  /**
   * Detect discharge messages and call backend tool directly to execute discharge workflow
   * Returns the tool response when handled, or null when not applicable
   */
  async handleDischargeShortcut(userMessage) {
    try {
      const textLower = (userMessage || '').toLowerCase();
      
      // Check for discharge patterns
      if (!textLower.includes('discharge') || !textLower.includes('patient')) {
        return null;
      }

      console.log('🏥 Discharge request detected:', userMessage);

      // Extract patient number/ID from the message
      const getField = (regex) => {
        const m = userMessage.match(regex);
        return m ? m[1].trim() : null;
      };

      // Look for patient patterns like "Patient P1025" or "P1025"
      let patient_number = getField(/patient\s+([a-zA-Z]?\d+)/i) || getField(/\b([pP]\d+)\b/i);
      
      if (patient_number) {
        // Ensure patient number has P prefix
        if (!patient_number.toUpperCase().startsWith('P')) {
          patient_number = `P${patient_number}`;
        }
        patient_number = patient_number.toUpperCase();

        console.log(`🏥 Attempting to discharge patient: ${patient_number}`);

        // Extract optional discharge parameters
        const discharge_condition = getField(/condition[:\s]+(\w+)/i) || 'stable';
        const discharge_destination = getField(/destination[:\s]+(\w+)/i) || 'home';

        const args = {
          patient_number,
          discharge_condition,
          discharge_destination
        };

        // Ensure client is connected/initialized
        if (!this.isInitialized) {
          console.warn('DirectHttpAIMCPService not initialized - cannot call discharge tool directly');
          return null;
        }

        try {
          console.log('🔧 Calling discharge_patient_complete tool with args:', args);
          const resp = await this.callToolDirectly('discharge_patient_complete', args);
          console.log('✅ Discharge tool response:', resp);
          return resp;
        } catch (err) {
          console.warn('Error calling discharge_patient_complete:', err);
          return { success: false, error: err && err.message ? err.message : String(err) };
        }
      } else {
        console.warn('❌ No patient number found in discharge request:', userMessage);
        return { success: false, error: 'Please specify a patient number (e.g., "Discharge Patient P1025")' };
      }
    } catch (err) {
      console.warn('Discharge parsing error:', err);
      return { success: false, error: err && err.message ? err.message : String(err) };
    }

    return null;
  }

  constructor() {
    this.mcpClient = new DirectHttpMCPClient();
    this.openaiApiKey = import.meta.env.VITE_OPENAI_API_KEY; // Get from environment
    this.isInitialized = false;
    this.conversationHistory = []; // Add conversation memory
    this.maxHistoryLength = 6; // Keep last 6 messages to manage token usage better
    this.verboseMode = true; // Toggle for response style
    this.previousQuestions = []; // Track user's previous questions for duplicate detection
  }

  /**
   * Calculate Levenshtein distance for fuzzy matching
   */
  calculateLevenshteinDistance(str1, str2) {
    const matrix = [];
    
    // Initialize matrix
    for (let i = 0; i <= str2.length; i++) {
      matrix[i] = [i];
    }
    for (let j = 0; j <= str1.length; j++) {
      matrix[0][j] = j;
    }
    
    // Fill matrix
    for (let i = 1; i <= str2.length; i++) {
      for (let j = 1; j <= str1.length; j++) {
        if (str2.charAt(i - 1) === str1.charAt(j - 1)) {
          matrix[i][j] = matrix[i - 1][j - 1];
        } else {
          matrix[i][j] = Math.min(
            matrix[i - 1][j - 1] + 1, // substitution
            matrix[i][j - 1] + 1,     // insertion
            matrix[i - 1][j] + 1      // deletion
          );
        }
      }
    }
    
    return matrix[str2.length][str1.length];
  }

  /**
   * Calculate similarity percentage between two strings
   */
  calculateSimilarity(str1, str2) {
    const distance = this.calculateLevenshteinDistance(str1.toLowerCase(), str2.toLowerCase());
    const maxLength = Math.max(str1.length, str2.length);
    return ((maxLength - distance) / maxLength) * 100;
  }

  /**
   * Find similar patient names using fuzzy matching
   */
  async findSimilarPatientNames(searchName, threshold = 70) {
    try {
      // First get all patients
      const allPatientsResult = await this.mcpClient.callTool('list_patients', {});
      
      if (!allPatientsResult.content || !Array.isArray(allPatientsResult.content)) {
        return [];
      }

      const patients = allPatientsResult.content;
      const matches = [];

      // Check each patient for similar names
      for (const patient of patients) {
        const fullName = `${patient.first_name} ${patient.last_name}`.trim();
        const firstNameSimilarity = this.calculateSimilarity(searchName, patient.first_name);
        const lastNameSimilarity = this.calculateSimilarity(searchName, patient.last_name);
        const fullNameSimilarity = this.calculateSimilarity(searchName, fullName);

        // Check if any name component has similarity above threshold
        const maxSimilarity = Math.max(firstNameSimilarity, lastNameSimilarity, fullNameSimilarity);
        
        if (maxSimilarity >= threshold) {
          matches.push({
            patient,
            similarity: maxSimilarity,
            matchType: maxSimilarity === firstNameSimilarity ? 'first_name' : 
                      maxSimilarity === lastNameSimilarity ? 'last_name' : 'full_name'
          });
        }
      }

      // Sort by similarity (highest first)
      matches.sort((a, b) => b.similarity - a.similarity);
      
      return matches;
    } catch (error) {
      console.error('Error finding similar patient names:', error);
      return [];
    }
  }

  /**
   * Find similar doctor/staff names using fuzzy matching
   */
  async findSimilarDoctorNames(searchName, threshold = 70) {
    try {
      // First get all staff
      const allStaffResult = await this.mcpClient.callTool('list_staff', {});
      
      if (!allStaffResult.content || !Array.isArray(allStaffResult.content)) {
        return [];
      }

      const staff = allStaffResult.content;
      const matches = [];

      // Check each staff member for similar names (doctors and all staff)
      for (const member of staff) {
        const fullName = `${member.first_name} ${member.last_name}`.trim();
        const firstNameSimilarity = this.calculateSimilarity(searchName, member.first_name);
        const lastNameSimilarity = this.calculateSimilarity(searchName, member.last_name);
        const fullNameSimilarity = this.calculateSimilarity(searchName, fullName);

        // Check if any name component has similarity above threshold
        const maxSimilarity = Math.max(firstNameSimilarity, lastNameSimilarity, fullNameSimilarity);
        
        if (maxSimilarity >= threshold) {
          matches.push({
            staff: member,
            similarity: maxSimilarity,
            matchType: maxSimilarity === firstNameSimilarity ? 'first_name' : 
                      maxSimilarity === lastNameSimilarity ? 'last_name' : 'full_name'
          });
        }
      }

      // Sort by similarity (highest first)
      matches.sort((a, b) => b.similarity - a.similarity);
      
      return matches;
    } catch (error) {
      console.error('Error finding similar doctor/staff names:', error);
      return [];
    }
  }

  /**
   * Find similar department names using fuzzy matching
   */
  async findSimilarDepartmentNames(searchName, threshold = 70) {
    try {
      // First get all departments
      const allDepartmentsResult = await this.mcpClient.callTool('list_departments', {});
      
      if (!allDepartmentsResult.content || !Array.isArray(allDepartmentsResult.content)) {
        return [];
      }

      const departments = allDepartmentsResult.content;
      const matches = [];

      // Check each department for similar names
      for (const dept of departments) {
        const nameSimilarity = this.calculateSimilarity(searchName, dept.name);
        const descriptionSimilarity = dept.description ? 
          this.calculateSimilarity(searchName, dept.description) : 0;

        // Check if name or description has similarity above threshold
        const maxSimilarity = Math.max(nameSimilarity, descriptionSimilarity);
        
        if (maxSimilarity >= threshold) {
          matches.push({
            department: dept,
            similarity: maxSimilarity,
            matchType: maxSimilarity === nameSimilarity ? 'name' : 'description'
          });
        }
      }

      // Sort by similarity (highest first)
      matches.sort((a, b) => b.similarity - a.similarity);
      
      return matches;
    } catch (error) {
      console.error('Error finding similar department names:', error);
      return [];
    }
  }

  // Helper function to generate Google Meet-style links
  generateMeetingLink() {
    // Generate a simple Google Meet-style room code
    const chars = 'abcdefghijklmnopqrstuvwxyz';
    const generateSegment = (length) => {
      let result = '';
      for (let i = 0; i < length; i++) {
        result += chars.charAt(Math.floor(Math.random() * chars.length));
      }
      return result;
    };
    
    const segment1 = generateSegment(3);
    const segment2 = generateSegment(4);
    const segment3 = generateSegment(3);
    
    return `https://meet.google.com/${segment1}-${segment2}-${segment3}`;
  }

  /**
   * Initialize the service
   */
  async initialize() {
    console.log('🚀 Initializing Direct HTTP AI-MCP Service (Claude Desktop Style)...');
    
    if (!this.openaiApiKey) {
      console.error('❌ OpenAI API key not configured in environment variables');
      return false;
    }

    // Connect to the MCP server directly
    const connected = await this.mcpClient.connect();
    if (!connected) {
      console.error('❌ Failed to connect to MCP server');
      return false;
    }

    this.isInitialized = true;
    console.log('✅ Direct HTTP AI-MCP Service initialized successfully (Claude Desktop Style)');
    
    // 🔄 Setup automatic bed status updates
    this.setupPeriodicBedStatusUpdates();
    
    return true;
  }

  /**
   * Get server information
   */
  getServerInfo() {
    return this.mcpClient.getServerInfo();
  }

  /**
   * Get available tools in OpenAI function calling format
   */
  getToolsForOpenAI() {
    const tools = this.mcpClient.getTools();
    return tools.map(tool => ({
      type: 'function',
      function: {
        name: tool.name,
        description: tool.description,
        parameters: tool.inputSchema || {
          type: 'object',
          properties: {},
          required: []
        }
      }
    }));
  }

  /**
   * Get available agents information
   */
  getAgents() {
    return this.mcpClient.getAgents();
  }

  /**
   * Expose add_equipment_usage_by_codes for direct tool calls
   */
  async addEquipmentUsageByCodes(args) {
    // args: { patient_number, equipment_id, employee_id, purpose, start_time, end_time, notes }
    if (!this.isInitialized) {
      await this.initialize();
    }
    return this.mcpClient.callTool('add_equipment_usage_by_codes', args);
  }

  /**
   * Expose add_treatment_record_by_codes for direct tool calls
   */
  async addTreatmentRecordByCodes(args) {
    // args: { patient_number, employee_id, treatment_type, treatment_name, start_date, end_date, notes }
    if (!this.isInitialized) {
      await this.initialize();
    }
    return this.mcpClient.callTool('add_treatment_record_by_codes', args);
  }



  /**
   * Validate conversation history for proper tool call/response structure
   */
  validateConversationStructure() {
    const pendingToolCalls = new Set();
    
    for (const message of this.conversationHistory) {
      if (message.role === 'assistant' && message.tool_calls) {
        // Add all tool call IDs to pending set
        for (const toolCall of message.tool_calls) {
          pendingToolCalls.add(toolCall.id);
        }
      } else if (message.role === 'tool' && message.tool_call_id) {
        // Remove responded tool call ID
        pendingToolCalls.delete(message.tool_call_id);
      }
    }
    
    if (pendingToolCalls.size > 0) {
      console.warn(`⚠️ Found ${pendingToolCalls.size} unresolved tool calls:`, Array.from(pendingToolCalls));
      return false;
    }
    
    return true;
  }

  /**
   * Clear conversation history (useful for fresh context)
   */
  clearConversationHistory() {
    this.conversationHistory = [];
    console.log('🧹 Conversation history cleared');
  }

  /**
   * Check if service is connected
   */
  isConnected() {
    return this.isInitialized && this.mcpClient.isConnectedToServer();
  }

  /**
   * Call MCP tool directly without AI processing (for form submissions)
   */
  async callToolDirectly(toolName, arguments_obj) {
    if (!this.isInitialized) {
      throw new Error('Service not initialized');
    }

    try {
      console.log(`🔧 Direct tool call: ${toolName}`, arguments_obj);
      
      const result = await this.mcpClient.callTool(toolName, arguments_obj);
      console.log(`✅ Direct tool result:`, result);
      
      // Handle the response from the MCP client
      // The response format is: { jsonrpc: "2.0", id: X, result: { content: [{ type: "text", text: "JSON_STRING" }] } }
      if (result && result.result && result.result.content && Array.isArray(result.result.content) && result.result.content[0]?.text) {
        try {
          const parsedResult = JSON.parse(result.result.content[0].text);
          console.log(`✅ Parsed result:`, parsedResult);
          return parsedResult;
        } catch (parseError) {
          console.error(`❌ Failed to parse result JSON:`, parseError);
          // If parsing fails, return a structured error
          return {
            success: false,
            message: `Failed to parse response: ${result.result.content[0].text}`
          };
        }
      }
      
      // Fallback - if response format is unexpected
      console.warn(`⚠️ Unexpected response format:`, result);
      return {
        success: false,
        message: 'Unexpected response format from server',
        raw_response: result
      };
    } catch (error) {
      console.error(`❌ Direct tool call failed for ${toolName}:`, error);
      return {
        success: false,
        message: error.message || 'Unknown error occurred'
      };
    }
  }

  /**
   * Detect if the message is requesting one of the 11 CREATE popup forms
   * Returns the popup intent or null if it should use normal AI processing
   */
  detectCreatePopupIntent(userMessage) {
    const message = userMessage.toLowerCase();
    
    // FIRST: Check for USAGE patterns that should use AI processing (NOT popup forms)
    if (message.includes('equipment') && (message.includes('usage') || message.includes('used by') || message.includes('patient id') || message.includes('assign') || message.includes('inventory') || message.includes('tracking'))) {
      console.log('🤖 Equipment usage/inventory detected - using AI processing');
      return null; // Use AI processing, not popup
    }
    
    if (message.includes('supply') && (message.includes('usage') || message.includes('used by') || message.includes('patient id') || message.includes('assign') || message.includes('inventory') || message.includes('tracking') || message.includes('consumption'))) {
      console.log('🤖 Supply usage/inventory detected - using AI processing');
      return null; // Use AI processing, not popup
    }
    
    // CREATE operations that should trigger popup forms (11 total)
    const createIntents = {
      'create_patient': ['create patient', 'add patient', 'new patient', 'register patient', 'patient admission', 'admit patient'],
      'create_user': ['create user', 'add user', 'new user', 'register user'],
      'create_staff': ['create staff', 'add staff', 'new staff', 'hire staff', 'staff member', 'register staff'],
      'create_department': ['create department', 'add department', 'new department'],
      'create_room': ['create room', 'add room', 'new room'],
      'create_bed': ['create bed', 'add bed', 'new bed'],
      'create_equipment': ['create equipment', 'register equipment'],  // Removed broad "add equipment" and "new equipment"
      'create_supply': ['create supply', 'register supply'],  // Removed broad "add supply" and "new supply"
      'create_legacy_user': ['create legacy user', 'add legacy user', 'new legacy user', 'legacy user'],
      'create_equipment_category': ['create equipment category', 'add equipment category', 'new equipment category'],
      'create_supply_category': ['create supply category', 'add supply category', 'new supply category']
    };

    // Check for CREATE intents (only if not usage)
    for (const [intent, keywords] of Object.entries(createIntents)) {
      for (const keyword of keywords) {
        if (message.includes(keyword)) {
          console.log(`✅ CREATE Intent Detected: ${intent} (matched: "${keyword}")`);
          return intent;
        }
      }
    }

    return null; // No CREATE intent detected, use normal AI processing
  }

  /**
   * Get appropriate message for popup form intent
   */
  getPopupIntentMessage(createIntent) {
    const messages = {
      'create_patient': 'I detected you want to register a new patient! I\'ve opened the patient admission form for you.',
      'create_user': 'I detected you want to create a new user! I\'ve opened the user creation form for you.',
      'create_staff': 'I detected you want to add a new staff member! I\'ve opened the staff creation form for you.',
      'create_department': 'I detected you want to create a new department! I\'ve opened the department creation form for you.',
      'create_room': 'I detected you want to create a new room! I\'ve opened the room creation form for you.',
      'create_bed': 'I detected you want to add a new bed! I\'ve opened the bed creation form for you.',
      'create_equipment': 'I detected you want to add new equipment! I\'ve opened the equipment creation form for you.',
      'create_supply': 'I detected you want to add new supplies! I\'ve opened the supply creation form for you.',
      'create_legacy_user': 'I detected you want to create a legacy user! I\'ve opened the legacy user creation form for you.',
      'create_equipment_category': 'I detected you want to create an equipment category! I\'ve opened the equipment category creation form for you.',
      'create_supply_category': 'I detected you want to create a supply category! I\'ve opened the supply category creation form for you.'
    };

    return messages[createIntent] || 'I detected a create request! I\'ve opened the appropriate form for you.';
  }

  /**
   * Process natural language request with conversation memory (Claude Desktop Style)
   */
  async processRequest(userMessage) {
    if (!this.isInitialized) {
      throw new Error('Service not initialized');
    }

    // Validate userMessage to prevent null/undefined errors
    if (!userMessage || typeof userMessage !== 'string') {
      console.warn('⚠️ Invalid userMessage received:', userMessage);
      return {
        success: false,
        message: 'Invalid message received. Please try again.',
        response: 'Invalid message received. Please try again.',
        functionCalls: [],
        serverInfo: this.getServerInfo(),
        rawResponse: { choices: [{ message: { content: 'Invalid message received. Please try again.' } }] },
        conversationLength: this.conversationHistory.length,
        timing: { openAI: 0, tool: 0, agent: 0 }
      };
    }

    // 🚀 ADVANCED AI: Try using master AI system for complex requests
    const complexPatterns = [
      /predict/i, /forecast/i, /analysis/i, /insight/i, /trend/i, /analytics/i,
      /comprehensive/i, /dashboard/i, /overview/i, /summary/i, /report/i,
      /multi.*language/i, /translate/i, /equipment.*lifecycle/i, /maintenance/i,
      /monitor/i, /real.*time/i, /alert/i, /notification/i
    ];
    
    const isComplexRequest = complexPatterns.some(pattern => pattern.test(userMessage));
    
    if (isComplexRequest) {
      console.log('🚀 Complex request detected, using Master AI System:', userMessage);
      try {
        const masterResponse = await this.callToolDirectly('ai_master_request', {
          user_request: userMessage,
          user_id: 'frontend_user',
          context: { timestamp: new Date().toISOString() }
        });
        
        if (masterResponse && masterResponse.success) {
          const responseText = masterResponse.response || masterResponse.message || 'Request processed successfully';
          return {
            success: true,
            message: `🧠 **Advanced AI Response:**\n${responseText}`,
            response: `🧠 **Advanced AI Response:**\n${responseText}`,
            functionCalls: [{ function: 'ai_master_request', result: masterResponse }],
            serverInfo: this.getServerInfo(),
            rawResponse: { choices: [{ message: { content: responseText } }] },
            conversationLength: this.conversationHistory.length,
            timing: { openAI: 0, tool: 100, agent: 100 }
          };
        }
      } catch (error) {
        console.warn('Master AI system failed, falling back to standard processing:', error);
      }
    }

    const agentStart = Date.now();
    console.log('🤖 [Hospital AI] Processing request:', userMessage);
    
    // 🎯 FIRST: Check for CREATE popup intents (11 forms)
    const createIntent = this.detectCreatePopupIntent(userMessage);
    if (createIntent) {
      console.log(`🎯 CREATE POPUP INTENT DETECTED: ${createIntent}`);
      
      // Return special response indicating popup form should be shown
      const popupMessage = this.getPopupIntentMessage(createIntent);
      
      return {
        success: true,
        showPopupForm: true,
        popupIntent: createIntent,
        message: popupMessage,
        response: popupMessage,
        functionCalls: [],
        serverInfo: this.getServerInfo(),
        rawResponse: { choices: [{ message: { content: popupMessage } }] },
        conversationLength: this.conversationHistory.length,
        timing: { openAI: 0, tool: 0, agent: Date.now() - agentStart }
      };
    }
    
    // Safe date logging
    let currentDate;
    try {
      currentDate = this.getTodayDate();
    } catch (error) {
      console.warn('Error getting date for logging:', error);
      // Dynamic fallback - always gets current date
      currentDate = new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' });
    }
    console.log(`[Agent] Today is: ${currentDate}`);

    try {
      // Add user message to conversation history
      this.addToConversationHistory('user', userMessage);

      // Quick path: detect and persist supply usage messages without hitting OpenAI
      try {
        const supplyShortcutResp = await this.handleSupplyUsageShortcut(userMessage);
        if (supplyShortcutResp) {
          const success = supplyShortcutResp && (supplyShortcutResp.success === true || (supplyShortcutResp.result && supplyShortcutResp.result.success === true));
          const messageText = success ? `✅ Supply usage recorded.` : `⚠️ Failed to record supply usage: ${JSON.stringify(supplyShortcutResp)}`;

          return {
            success: success,
            message: messageText,
            response: messageText,
            functionCalls: [],
            toolResults: [supplyShortcutResp],
            serverInfo: this.getServerInfo(),
            rawResponse: { choices: [{ message: { content: messageText } }] },
            conversationLength: this.conversationHistory.length,
            timing: { openAI: 0, tool: 0, agent: Date.now() - agentStart }
          };
        }
      } catch (err) {
        console.warn('Supply shortcut handling failed:', err);
      }

      // Quick path: detect and handle discharge requests directly
      try {
        const dischargeResult = await this.handleDischargeShortcut(userMessage);
        if (dischargeResult) {
          const success = dischargeResult && (dischargeResult.success === true || (dischargeResult.result && dischargeResult.result.success === true));
          
          let messageText;
          if (success) {
            const result = dischargeResult.result || dischargeResult;
            messageText = `✅ ${result.message || 'Patient discharged successfully'}`;
            
            // Add additional details if available
            if (result.report_number) {
              messageText += `\n📄 Discharge Report: ${result.report_number}`;
            }
            if (result.report_download_url) {
              messageText += `\n📥 Download: ${result.report_download_url}`;
            }
            if (result.bed_turnover && result.bed_turnover.success) {
              messageText += `\n🛏️ Bed cleaning initiated - estimated ${result.cleaning_timer || '30 minutes'}`;
            }
            if (result.next_steps && result.next_steps.length > 0) {
              messageText += '\n📋 Next Steps:';
              result.next_steps.forEach(step => {
                messageText += `\n   • ${step}`;
              });
            }
          } else {
            messageText = `❌ Failed to discharge patient: ${dischargeResult.message || 'Unknown error'}`;
          }

          // Add to conversation history
          this.addToConversationHistory('assistant', messageText);

          return {
            success: success,
            message: messageText,
            response: messageText,
            functionCalls: [],
            toolResults: [dischargeResult],
            serverInfo: this.getServerInfo(),
            rawResponse: { choices: [{ message: { content: messageText } }] },
            conversationLength: this.conversationHistory.length,
            timing: { openAI: 0, tool: 0, agent: Date.now() - agentStart }
          };
        }
      } catch (err) {
        console.warn('Discharge shortcut handling failed:', err);
      }

      // Check if this is an assignment operation first
      const assignmentResult = await this.handleAssignmentOperations(userMessage, []);
      if (assignmentResult) {
        console.log('✅ Assignment operation handled directly');
        this.addToConversationHistory('assistant', assignmentResult);
        return {
          success: true,
          message: assignmentResult,
          response: assignmentResult,
          functionCalls: [],
          serverInfo: this.getServerInfo(),
          rawResponse: { choices: [{ message: { content: assignmentResult } }] },
          conversationLength: this.conversationHistory.length,
          timing: { openAI: 0, tool: 0, agent: Date.now() - agentStart }
        };
      }

      // Get current status and tools
      const availableTools = this.getToolsForOpenAI();
      const availableAgents = this.getAgents();
      const serverInfo = this.getServerInfo();
      
      console.log(`📋 Available tools: ${availableTools.length}`);
      console.log(`� Available agents: ${availableAgents.length}`);
      console.log(`�💭 Conversation history length: ${this.conversationHistory.length}`);
      
      // Log agent details for visibility
      if (availableAgents.length > 0) {
        console.log('🤖 Active agents:');
        availableAgents.forEach(agent => {
          console.log(`  • ${agent.name} (${agent.tools_count} tools) - ${agent.description}`);
        });
      }
      
      // Check for specific emergency/contextual scenarios first (very limited cases)
      console.log('🔍 Checking for emergency scenarios...');
      const emergencyTools = this.detectEmergencyScenario(userMessage);
      if (emergencyTools && emergencyTools.length > 0) {
        console.log('🚨 Emergency scenario detected, using manual tools:', emergencyTools);
        
        // Execute the emergency tools
        const toolStart = Date.now();
        const emergencyResults = [];
        for (const tool of emergencyTools) {
          try {
            console.log(`🔧 Executing emergency tool: ${tool.name}`);
            const result = await this.callTool(tool.name, tool.arguments || {});
            emergencyResults.push({
              function: tool.name,
              result: result,
              error: null
            });
          } catch (error) {
            console.error(`❌ Emergency tool error:`, error);
            emergencyResults.push({
              function: tool.name,
              result: null,
              error: error.message
            });
          }
        }
        
        const toolTime = Date.now() - toolStart;
        const formattedResponse = this.formatToolResults(userMessage, emergencyResults);
        
        this.addToConversationHistory('assistant', formattedResponse);
        
        return {
          success: true,
          message: formattedResponse,
          response: formattedResponse,
          functionCalls: emergencyResults,
          serverInfo: serverInfo,
          rawResponse: { choices: [{ message: { content: formattedResponse } }] },
          conversationLength: this.conversationHistory.length,
          timing: { openAI: 0, tool: toolTime, agent: Date.now() - agentStart }
        };
      }
      
      console.log('🤖 Using AI-powered tool selection (OpenAI function calling)...');
      
      // Call OpenAI with function calling and conversation history (CLAUDE DESKTOP STYLE)
      let gptResponse;
      let allFunctionResults = [];
      let iterationCount = 0;
      const maxIterations = 5; // Prevent infinite loops
      let openAITotal = 0;
      let toolTotal = 0;

      // Initial OpenAI call
      const openAIStart = Date.now();
      gptResponse = await this.callOpenAI(userMessage, availableTools, serverInfo);
      openAITotal += Date.now() - openAIStart;

      // Support multiple rounds of function calls (CLAUDE DESKTOP PATTERN)
      while (gptResponse.choices[0].message.tool_calls && iterationCount < maxIterations) {
        console.log(`� [Hospital AI] Function call iteration ${iterationCount + 1}`);

        // Execute function calls
        const toolStart = Date.now();
        const results = await this.executeFunctionCalls(gptResponse);
        toolTotal += Date.now() - toolStart;
        allFunctionResults.push(...results);

        // Add function call and results to conversation
        const assistantMessage = gptResponse.choices[0].message;
        this.addToConversationHistory('assistant', assistantMessage.content, assistantMessage.tool_calls);

        // Add function results to conversation
        for (const result of results) {
          this.addToConversationHistory('tool', JSON.stringify(result.result), null, result.function, result.tool_call_id);
        }

        // Continue conversation with updated context
        const openAIStart2 = Date.now();
        gptResponse = await this.callOpenAI(null, availableTools, serverInfo);
        openAITotal += Date.now() - openAIStart2;
        iterationCount++;
      }

      // Add final assistant response to history
      if (gptResponse.choices[0].message.content) {
        this.addToConversationHistory('assistant', gptResponse.choices[0].message.content);
      }

      const agentEnd = Date.now();
      console.log(`[Agent Timing] OpenAI total: ${openAITotal}ms, Tool total: ${toolTotal}ms, Agent total: ${agentEnd - agentStart}ms`);

      return {
        success: true,
        message: gptResponse.choices[0].message.content,
        response: gptResponse.choices[0].message.content, // For compatibility
        functionCalls: allFunctionResults,
        serverInfo: serverInfo,
        rawResponse: gptResponse,
        conversationLength: this.conversationHistory.length,
        timing: {
          openAI: openAITotal,
          tool: toolTotal,
          agent: agentEnd - agentStart
        }
      };

    } catch (error) {
      console.error('❌ Hospital AI processing failed:', error);
      return {
        success: false,
        error: error.message,
        message: `Failed to process request: ${error.message}`,
        response: `I encountered an error while processing your request: ${error.message}. Please try again.`
      };
    }
  }

  /**
   * Intelligent tool determination with AI assistance - Claude Desktop style
   */
  async determineRequiredToolsWithAI(userMessage, availableTools) {
    console.log('🤖 determineRequiredToolsWithAI called with:', userMessage);
    
    // 🛏️ CRITICAL BED STATUS FIX - Check this FIRST before AI processing!
    // BUT: Skip this override for discharge messages to allow discharge workflow
    if (userMessage.toLowerCase().includes('discharge') && userMessage.toLowerCase().includes('patient')) {
      console.log('🚨 DISCHARGE MESSAGE DETECTED: Skipping bed status override to allow discharge workflow');
    } else {
      const bedStatusPatterns = [
        /check\s+bed\s+(\w+)\s+status/i,
        /bed\s+(\w+)\s+status/i, 
        /status\s+of\s+bed\s+(\w+)/i,
        /is\s+bed\s+(\w+)\s+ready/i,
        /bed\s+(\w+)\s+ready/i,
        /check\s+bed\s+(\w+)/i
      ];
      
      for (const pattern of bedStatusPatterns) {
        const match = userMessage.match(pattern);
        if (match) {
          console.log(`🎯 BED STATUS OVERRIDE: "${userMessage}" -> Forcing get_bed_status_with_time_remaining for bed ${match[1]}`);
          return [{
            name: 'get_bed_status_with_time_remaining',
            arguments: { bed_id: match[1] }
          }];
        }
      }
    }
    
    // Additional bed status keyword detection  
    // BUT: Skip this override for discharge messages to allow discharge workflow
    if (!userMessage.toLowerCase().includes('discharge') || !userMessage.toLowerCase().includes('patient')) {
      if ((userMessage.includes('bed') && userMessage.includes('status')) ||
          (userMessage.includes('check') && userMessage.includes('bed'))) {
        console.log('🎯 BED STATUS KEYWORD OVERRIDE: Forcing get_bed_status_with_time_remaining');
        const bedParams = this.extractBedStatusParameters(userMessage);
        return [{
          name: 'get_bed_status_with_time_remaining',
          arguments: bedParams
        }];
      }
    }
    
    // Check conversation context for ongoing operations
    const contextualTools = this.analyzeConversationContext(userMessage);
    if (contextualTools.length > 0) {
      console.log('🤖 Returning contextual tools:', contextualTools);
      return contextualTools;
    }
    
    // This method now only handles emergency/contextual scenarios
    // No longer falls back to pattern matching - let AI handle everything else
    console.log('🤖 No contextual tools found, returning empty for AI processing');
    return [];
  }

  /**
   * Detect emergency or multi-step scenarios (only true emergencies)
   */
  detectEmergencyScenario(userMessage) {
    if (!userMessage || typeof userMessage !== 'string') {
      return [];
    }
    
    const message = userMessage.toLowerCase();
    const toolsNeeded = [];
    
    console.log('🚨 Emergency scenario detection for:', message);
    
    // Only handle true emergency patient scenarios with structured data
    if (message.includes('emergency') && (message.includes('patient') || message.includes('register')) && 
        this.containsStructuredData(userMessage)) {
      console.log('🚨 Emergency patient scenario detected');
      const structuredTool = this.parseStructuredInput(userMessage);
      if (structuredTool && structuredTool.name === 'create_patient') {
        // Multi-step emergency process
        toolsNeeded.push(structuredTool); // Create patient first
        toolsNeeded.push({ name: 'list_beds', arguments: { status: 'available' } }); // Check available beds
        toolsNeeded.push({ name: 'list_staff', arguments: {} }); // List available doctors
        console.log('🚨 Emergency tools added:', toolsNeeded);
        return toolsNeeded;
      }
    }
    
    console.log('🚨 No true emergency scenario detected');
    return [];
  }

  /**
   * Analyze conversation context for ongoing operations
   */
  analyzeConversationContext(userMessage) {
    if (!userMessage || typeof userMessage !== 'string') {
      return [];
    }
    
    const recentHistory = this.conversationHistory.slice(-5);
    const toolsNeeded = [];
    const message = userMessage.toLowerCase();
    
    // Priority: Check bed status after discharge operations
    // BUT: Skip this override for discharge messages to allow discharge workflow
    if (!message.includes('discharge') || !message.includes('patient')) {
      if ((message.includes('bed') && (message.includes('status') || message.includes('check'))) ||
          (message.includes('bed') && message.includes('cleaning')) ||
          (message.includes('availability') && message.includes('bed'))) {
        
        // Look for recent discharge operations in conversation history
        let hasRecentDischarge = false;
        for (const entry of recentHistory) {
          if (entry && entry.content && typeof entry.content === 'string') {
            if (entry.content.includes('discharge') || entry.content.includes('DISCHARGE') ||
                entry.content.includes('discharged') || entry.content.includes('DISCHARGED')) {
              hasRecentDischarge = true;
              break;
            }
          }
        }
        
        // If recent discharge detected or explicit bed status query, prioritize the time-remaining tool
        if (hasRecentDischarge || message.includes('time') || message.includes('cleaning') || 
            message.includes('ready') || message.includes('available')) {
          console.log('🛏️ Bed status priority: Using get_bed_status_with_time_remaining after discharge context');
          
          // Extract bed number if provided
          const bedNumberMatch = userMessage.match(/bed\s+([A-Z0-9]+)/i) || 
                                userMessage.match(/([A-Z]+\d+[A-Z]?)/i) ||
                                userMessage.match(/(\d+[A-Z])/i);
          const bedNumber = bedNumberMatch ? bedNumberMatch[1] : '';
          
          return [{ 
            name: 'get_bed_status_with_time_remaining', 
            arguments: bedNumber ? { bed_number: bedNumber } : {} 
          }];
        }
      }
    }
    
    // Look for incomplete operations in recent history
    for (const entry of recentHistory) {
      // Validate entry structure to prevent null reference errors
      if (!entry || !entry.role || typeof entry.role !== 'string') {
        continue;
      }
      
      if (entry.role === 'assistant' && entry.content && typeof entry.content === 'string' && entry.content.includes('What should I call this department')) {
        // User is in the middle of creating a department
        if (userMessage.trim().length > 0) {
          return [{ name: 'create_department', arguments: { name: userMessage.trim() } }];
        }
      }
      // Add more contextual analysis here for other ongoing operations
    }
    
    return toolsNeeded;
  }

  /**
   * Handle incomplete requests intelligently
   */
  async handleIncompleteRequest(tool) {
    const requestType = tool.name;

    switch (requestType) {
      case '_ask_for_department_details':
        return "I'd be happy to create a new department! What should I call this department? For example: 'Cardiology', 'Emergency', 'Pediatrics', etc.";

      case '_ask_for_patient_details':
        return "To create a new patient, I need:\n\n" +
               "📝 **Required:** First Name, Last Name, Date of Birth (YYYY-MM-DD)\n" +
               "📋 **Optional:** Gender, Phone, Email, Address\n\n" +
               "**Example:** *Create patient John Doe born 1985-05-15*";

      case 'add_equipment_usage_by_codes':
        return "To add a record of equipment usage, please provide the following details:\n\n" +
          "1. Patient Number (e.g., 'P591793'): The unique identifier of the patient who used or for whom the equipment was used.\n" +
          "2. Employee ID (e.g., 'EMP001'): The unique identifier of the staff member who operated or oversaw the equipment usage.\n" +
          "3. Equipment ID (e.g., 'EQ123'): The unique identifier of the equipment used.\n" +
          "4. Purpose: The reason or purpose for using the equipment.\n" +
          "5. Start Time (YYYY-MM-DD or YYYY-MM-DD HH:MM): The date and time when the equipment usage started.\n" +
          "6. End Time (YYYY-MM-DD or YYYY-MM-DD HH:MM, optional): The date and time when the equipment usage ended, if applicable.\n" +
          "7. Notes (optional): Any additional details or context about the equipment's usage.\n\n" +
          "Please provide these details in your response.";

      case '_ask_for_equipment_usage_details':
        return "To add a record of equipment usage, please provide the following details:\n\n" +
          "1. Patient Number (e.g., 'P002'): The unique identifier of the patient.\n" +
          "2. Employee ID (e.g., 'EMP001'): The unique identifier of the staff member.\n" +
          "3. Equipment ID (e.g., 'EQ001'): The unique identifier of the equipment.\n" +
          "4. Purpose: The reason for using the equipment (e.g., 'ECG monitoring during cardiac evaluation').\n" +
          "5. Start Time (YYYY-MM-DD HH:MM): When the equipment usage started.\n" +
          "6. End Time (YYYY-MM-DD HH:MM, optional): When the equipment usage ended.\n" +
          "7. Notes (optional): Any additional details.\n\n" +
          "**Example format:**\n" +
          "Equipment ID: EQ001\n" +
          "Employee ID: EMP001\n" +
          "Patient Number: P002\n" +
          "Purpose: ECG monitoring during cardiac evaluation\n" +
          "Usage Start Date and Time: 2025-08-25 09:15\n" +
          "Usage End Date and Time: 2025-08-25 10:00";

      // Add more intelligent prompts for other incomplete requests
      default:
        return "Please provide the required information for this operation.";
    }
  }

  /**
   * Resolve foreign keys by searching for IDs when users provide names
   */
  async resolveForeignKeys(tool) {
    const resolvedTool = { ...tool };
    const params = { ...tool.arguments };
    
    // Resolve department names to IDs with fuzzy matching
    if (params.department_name && !params.department_id) {
      try {
        const departments = await this.mcpClient.callTool('list_departments', {});
        const dept = departments.find(d => 
          d.name.toLowerCase().includes(params.department_name.toLowerCase())
        );
        
        if (dept) {
          params.department_id = dept.id;
          delete params.department_name;
        } else {
          // If exact search fails, try fuzzy matching
          console.log(`🔍 Exact search for department "${params.department_name}" failed, trying fuzzy matching...`);
          const similarMatches = await this.findSimilarDepartmentNames(params.department_name, 70);
          
          if (similarMatches.length > 0) {
            const bestMatch = similarMatches[0];
            console.log(`🎯 Found similar department: ${bestMatch.department.name} (${bestMatch.similarity.toFixed(1)}% match)`);
            params.department_id = bestMatch.department.id;
            params._fuzzy_match_info = {
              original_search: params.department_name,
              matched_name: bestMatch.department.name,
              similarity: bestMatch.similarity
            };
            delete params.department_name;
          }
        }
      } catch (error) {
        console.warn('Could not resolve department name:', params.department_name, error);
      }
    }
    
    // Resolve patient names to IDs with fuzzy matching
    if ((params.patient_name || (params.first_name && params.last_name)) && !params.patient_id) {
      try {
        let searchName = params.patient_name;
        let searchParams = {};
        
        if (params.first_name && params.last_name) {
          searchName = `${params.first_name} ${params.last_name}`;
          searchParams = {
            first_name: params.first_name,
            last_name: params.last_name
          };
        } else if (params.patient_name) {
          const nameParts = params.patient_name.split(' ');
          searchParams = {
            first_name: nameParts[0],
            last_name: nameParts[1]
          };
        }
        
        // First try exact search
        const patients = await this.mcpClient.callTool('search_patients', searchParams);
        
        if (patients.length > 0) {
          params.patient_id = patients[0].id;
          delete params.patient_name;
          delete params.first_name;
          delete params.last_name;
        } else {
          // If exact search fails, try fuzzy matching
          console.log(`🔍 Exact search for "${searchName}" failed, trying fuzzy matching...`);
          const similarMatches = await this.findSimilarPatientNames(searchName, 70);
          
          if (similarMatches.length > 0) {
            const bestMatch = similarMatches[0];
            console.log(`🎯 Found similar patient: ${bestMatch.patient.first_name} ${bestMatch.patient.last_name} (${bestMatch.similarity.toFixed(1)}% match)`);
            params.patient_id = bestMatch.patient.id;
            params._fuzzy_match_info = {
              original_search: searchName,
              matched_name: `${bestMatch.patient.first_name} ${bestMatch.patient.last_name}`,
              similarity: bestMatch.similarity
            };
            delete params.patient_name;
            delete params.first_name;
            delete params.last_name;
          }
        }
      } catch (error) {
        console.warn('Could not resolve patient name:', params.patient_name || `${params.first_name} ${params.last_name}`, error);
      }
    }
    
    // Resolve doctor names to IDs with fuzzy matching
    if (params.doctor_name && !params.doctor_id) {
      try {
        const staff = await this.mcpClient.callTool('list_staff', {});
        const doctor = staff.find(s => 
          s.position.toLowerCase().includes('doctor') &&
          (s.first_name + ' ' + s.last_name).toLowerCase().includes(params.doctor_name.toLowerCase())
        );
        
        if (doctor) {
          params.doctor_id = doctor.id;
          delete params.doctor_name;
        } else {
          // If exact search fails, try fuzzy matching for doctors
          console.log(`🔍 Exact search for doctor "${params.doctor_name}" failed, trying fuzzy matching...`);
          const similarMatches = await this.findSimilarDoctorNames(params.doctor_name, 70);
          
          // Filter to only doctors
          const doctorMatches = similarMatches.filter(match => 
            match.staff.position.toLowerCase().includes('doctor')
          );
          
          if (doctorMatches.length > 0) {
            const bestMatch = doctorMatches[0];
            console.log(`🎯 Found similar doctor: ${bestMatch.staff.first_name} ${bestMatch.staff.last_name} (${bestMatch.similarity.toFixed(1)}% match)`);
            params.doctor_id = bestMatch.staff.id;
            params._fuzzy_match_info = {
              original_search: params.doctor_name,
              matched_name: `${bestMatch.staff.first_name} ${bestMatch.staff.last_name}`,
              similarity: bestMatch.similarity
            };
            delete params.doctor_name;
          }
        }
      } catch (error) {
        console.warn('Could not resolve doctor name:', params.doctor_name, error);
      }
    }

    // Resolve staff names to IDs with fuzzy matching (for general staff, not just doctors)
    if (params.staff_name && !params.staff_id) {
      try {
        const staff = await this.mcpClient.callTool('list_staff', {});
        const staffMember = staff.find(s => 
          (s.first_name + ' ' + s.last_name).toLowerCase().includes(params.staff_name.toLowerCase())
        );
        
        if (staffMember) {
          params.staff_id = staffMember.id;
          delete params.staff_name;
        } else {
          // If exact search fails, try fuzzy matching for staff
          console.log(`🔍 Exact search for staff "${params.staff_name}" failed, trying fuzzy matching...`);
          const similarMatches = await this.findSimilarDoctorNames(params.staff_name, 70);
          
          if (similarMatches.length > 0) {
            const bestMatch = similarMatches[0];
            console.log(`🎯 Found similar staff member: ${bestMatch.staff.first_name} ${bestMatch.staff.last_name} (${bestMatch.similarity.toFixed(1)}% match)`);
            params.staff_id = bestMatch.staff.id;
            params._fuzzy_match_info = {
              original_search: params.staff_name,
              matched_name: `${bestMatch.staff.first_name} ${bestMatch.staff.last_name}`,
              similarity: bestMatch.similarity
            };
            delete params.staff_name;
          }
        }
      } catch (error) {
        console.warn('Could not resolve staff name:', params.staff_name, error);
      }
    }
    
    resolvedTool.arguments = params;
    return resolvedTool;
  }

  /**
   * Generate response with conversation context
   */
  async generateResponseWithContext(userMessage, toolResults, availableTools) {
    if (!this.openaiApiKey) {
      return this.formatToolResults(userMessage, toolResults);
    }

    // Build conversation context for OpenAI
    const conversationContext = this.conversationHistory.slice(-6).map(entry => ({
      role: entry.role === 'assistant' ? 'assistant' : 'user',
      content: entry.content
    }));

    const systemPrompt = `You are an intelligent hospital management assistant with advanced conversation capabilities and memory.

🏥 **Hospital Management System - AI Assistant with Context**

**Current Conversation Context:**
Remember the recent conversation and provide contextually appropriate responses. Don't repeat information unnecessarily.

**Enhanced Capabilities:**
1. **Smart Parameter Collection**: Ask for missing details conversationally, one at a time
2. **Multi-Tool Operations**: Automatically resolve names to IDs when needed
3. **Conversation Memory**: Build upon previous exchanges
4. **Contextual Responses**: Tailor responses based on conversation flow
5. **Fuzzy Name Matching**: Handle voice-to-text transcription errors and similar-sounding names

**Critical Behaviors:**

**INCOMPLETE REQUESTS:**
- For "create new department" → Ask: "What should I call this department?"
- For "add equipment usage" (add_equipment_usage_by_codes) → Ask for:
  * Patient Number (patient_number): The unique identifier for the patient who used the equipment.
  * Equipment ID/Code (equipment_id): The code for the equipment used (e.g., "EQ001").
  * Employee ID (employee_id): The identifier for the staff member who operated or supervised the equipment.
  * Purpose (purpose): The reason for equipment usage (e.g., "Monitoring", "Treatment").
  * Start Time (start_time, optional): When the equipment usage began (YYYY-MM-DD or ISO format).
  * End Time (end_time, optional): When the equipment usage ended (YYYY-MM-DD or ISO format).
  * Notes (notes, optional): Any relevant notes regarding the equipment usage.
- Never create with placeholder names
- Collect required information conversationally

**FOREIGN KEY RESOLUTION:**
- When users mention names instead of IDs, automatically search for matches
- Explain what you're doing: "Let me find John Doe in our patient records..."
- If multiple matches found, ask for clarification

**FUZZY NAME MATCHING:**
- The system automatically handles similar-sounding names for all entities:
  * Patients: "Nazif" vs "Nasif", "Mohammed" vs "Mohamed"
  * Doctors: "Ahmad" vs "Ahmed", "Hassan" vs "Hasan"
  * Staff: "Ali" vs "Aly", "Omar" vs "Umar"
  * Departments: "Cardiology" vs "Cardio", "Emergency" vs "ER"
- When fuzzy matching is used, inform the user: "I found a similar name: Mohamed Nazif. Is this the patient you're looking for?"
- Check tool results for "_fuzzy_match_info" to see if fuzzy matching was used
- Always confirm fuzzy matches with the user before proceeding

**VOICE-TO-TEXT CORRECTIONS:**
- Common transcription errors for all entity types:
  * Names: "Nazif" → "Nasif", "Mohammed" → "Mohamed", "Ahmad" → "Ahmed"
  * Departments: "Cardiology" → "Cardio", "Emergency" → "ER"
- When exact search fails, the system automatically tries fuzzy matching (70% similarity threshold)
- Explain when corrections are made: "I couldn't find 'Nasif' but found 'Nazif' which sounds similar"

**CONVERSATION FLOW:**
- Remember what the user is trying to accomplish
- Build upon previous responses
- Don't ask for information already provided
- Confirm actions before executing

**LIST TOOLS RESPONSE FORMAT:**
When using any LIST tools (list_patients, list_staff, list_departments, list_beds, list_rooms, list_equipment, list_supplies, list_users, list_meetings, list_discharge_reports, list_equipment_categories, list_supply_categories, list_inventory_transactions, list_legacy_users), provide ONLY essential information:

- **list_patients**: Only show patient names (first_name + last_name) and patient numbers
- **list_staff**: Only show staff names (first_name + last_name) and positions
- **list_departments**: Only show department names
- **list_beds**: Only show bed numbers and room assignments
- **list_rooms**: Only show room numbers and types
- **list_equipment**: Only show equipment names and status
- **list_supplies**: Only show supply names and current stock levels
- **list_users**: Only show usernames and roles
- **list_meetings**: Only show meeting topics and dates
- **All other list tools**: Only show names/titles and key status information

DO NOT show full details, IDs, or technical information unless specifically requested. This prevents "(Further details are truncated for brevity)" messages and keeps responses clean and readable.

Available tools: ${availableTools.map(tool => tool.name).join(', ')}

Tool Results:
${toolResults.map(result => {
  if (result.error) {
    return `❌ ${result.tool}: ${result.error}`;
  } else {
    // Check for fuzzy match information
    let resultText = `✅ ${result.tool}: Success`;
    if (result.content && result.content._fuzzy_match_info) {
      const fuzzyInfo = result.content._fuzzy_match_info;
      resultText += ` (Found similar name: "${fuzzyInfo.matched_name}" for search "${fuzzyInfo.original_search}" - ${fuzzyInfo.similarity.toFixed(1)}% match)`;
    }
    return resultText;
  }
}).join('\n')}

Respond naturally, conversationally, and contextually based on the conversation history and tool results.`;

    try {
      const messages = [
        { role: 'system', content: systemPrompt },
        ...conversationContext,
        { role: 'user', content: userMessage }
      ];

      const response = await fetch('https://api.openai.com/v1/chat/completions', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${this.openaiApiKey}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          model: 'gpt-4',
          messages: messages,
          temperature: 0.7,
          max_tokens: 4000
        })
      });

      if (!response.ok) {
        throw new Error(`OpenAI API error: ${response.status}`);
      }

      const data = await response.json();
      return data.choices[0].message.content;

    } catch (error) {
      console.error('❌ Failed to generate contextual response:', error);
      return this.formatToolResults(userMessage, toolResults);
    }
  }

  /**
   * Determine which tools are needed based on user input
   */
  async determineRequiredTools(userMessage) {
    // Simple keyword-based tool mapping for better reliability
    const message = userMessage.toLowerCase();
    const toolsNeeded = [];
    
    console.log('🔍 Analyzing message:', message);
    console.log('🔍 Full userMessage:', userMessage);
    
    // Check for structured data input (when user provides details directly)
    if (this.containsStructuredData(userMessage)) {
      console.log('📝 Contains structured data');
      const structuredTool = this.parseStructuredInput(userMessage);
      if (structuredTool) {
        console.log('🎯 Returning structured tool:', structuredTool);
        return [structuredTool];
      }
    }
    
    // Patient operations
    if (message.includes('list patients') || message.includes('show patients') || message.includes('all patients') || message.includes('patients')) {
      toolsNeeded.push({ name: 'list_patients', arguments: {} });
    }
    
    // Enhanced patient creation with parameter extraction
    if (message.includes('create patient') || message.includes('add patient') || message.includes('new patient')) {
      const patientParams = this.extractPatientParameters(userMessage);
      if (patientParams.first_name && patientParams.last_name && patientParams.date_of_birth) {
        // Generate patient number if not provided
        if (!patientParams.patient_number) {
          patientParams.patient_number = `PAT${String(Math.floor(Math.random() * 9000) + 1000)}`;
        }
        toolsNeeded.push({ name: 'create_patient', arguments: patientParams });
      } else {
        return [{ name: '_ask_for_patient_details', needsInput: true }];
      }
    }
    
    if (message.includes('search patient') || message.includes('find patient') || 
        message.includes('look for patient') || message.includes('show me patient') ||
        message.includes('patient named') || message.includes('patient called') ||
        message.includes('looking for') || message.includes('where is') ||
        // Common patterns from voice input
        message.match(/\b(nazif|nasif|mohammed|mohammad|ahmed)\b/i) ||
        // General patterns that might indicate patient search
        message.includes('patient') && (message.includes('details') || message.includes('information') || message.includes('record')) ||
        // Simple name patterns (likely from voice input)
        message.match(/^(mohamed|mohammed|ahmad|ahmed|hassan|ali|omar|nazif|nasif|khalid|saeed|abdullah)\s+\w+$/i) ||
        message.match(/^(nazif|nasif|mohammed|mohamed|ahmed|hassan|ali|omar|khalid|saeed|abdullah)$/i)) {
      const searchParams = this.extractPatientSearchParameters(userMessage);
      toolsNeeded.push({ name: 'search_patients', arguments: searchParams });
    }

    // Doctor/Staff search operations with voice input support
    if (message.includes('find doctor') || message.includes('search doctor') || 
        message.includes('look for doctor') || message.includes('show me doctor') ||
        message.includes('doctor named') || message.includes('doctor called') ||
        message.includes('find staff') || message.includes('search staff') || 
        message.includes('look for staff') || message.includes('show me staff') ||
        message.includes('staff named') || message.includes('staff called') ||
        // Voice patterns for common doctor names
        message.match(/\b(doctor|dr\.?)\s+(ahmad|ahmed|hassan|ali|omar|khalid|saeed|abdullah|mohamed|mohammed)\b/i)) {
      const searchParams = this.extractStaffSearchParameters(userMessage);
      toolsNeeded.push({ name: 'search_staff', arguments: searchParams });
    }

    // Department search operations with voice input support  
    if (message.includes('find department') || message.includes('search department') || 
        message.includes('look for department') || message.includes('show me department') ||
        message.includes('department named') || message.includes('department called') ||
        // Voice patterns for common department names
        message.match(/\b(cardiology|cardio|emergency|er|surgery|orthopedic|pediatric|neurology)\b/i)) {
      const searchParams = this.extractDepartmentSearchParameters(userMessage);
      toolsNeeded.push({ name: 'search_departments', arguments: searchParams });
    }
    
    // Staff operations
    if (message.includes('list staff') || message.includes('show staff') || message.includes('all staff') || message.includes('staff')) {
      toolsNeeded.push({ name: 'list_staff', arguments: {} });
    }
    
    // Enhanced staff creation with parameter extraction
    if (message.includes('create staff') || message.includes('add staff') || message.includes('new staff')) {
      const staffParams = this.extractStaffParameters(userMessage);
      if (staffParams.employee_id && staffParams.department_id && staffParams.position) {
        toolsNeeded.push({ name: 'create_staff', arguments: staffParams });
      } else {
        return [{ name: '_ask_for_staff_details', needsInput: true }];
      }
    }
    
    // Department operations
    if (message.includes('list departments') || message.includes('show departments') || message.includes('all departments') || message.includes('departments')) {
      toolsNeeded.push({ name: 'list_departments', arguments: {} });
    }
    
    // Enhanced department creation - don't auto-create with insufficient data
    if (message.includes('create department') || message.includes('add department') || message.includes('new department')) {
      const deptParams = this.extractDepartmentParameters(userMessage);
      // Only create if we have a meaningful name (not just "new" or generic words)
      if (deptParams.name && deptParams.name.length > 3 && 
          !['new', 'department', 'create', 'add'].includes(deptParams.name.toLowerCase())) {
        toolsNeeded.push({ name: 'create_department', arguments: deptParams });
      }
    }
    
    // Discharge workflow operations
    if (message.includes('discharge') && message.includes('patient')) {
      const dischargeParams = this.extractDischargeParameters(userMessage);
      
      // If we have bed_number, need to convert to bed_id first
      if (dischargeParams.bed_number) {
        toolsNeeded.push({ name: 'get_bed_by_number', arguments: { bed_number: dischargeParams.bed_number } });
        toolsNeeded.push({ name: 'discharge_patient_complete', arguments: { 
          ...dischargeParams,
          bed_id: '{{bed_id_from_lookup}}'
        }});
      } else if (dischargeParams.patient_id && dischargeParams.patient_id.startsWith('P')) {
        // If we have a patient number (P1025), use patient_number parameter
        // The backend tool now supports patient_number directly
        // IMPORTANT: Clear patient_id to avoid UUID conversion errors
        toolsNeeded.push({ name: 'discharge_patient_complete', arguments: { 
          patient_number: dischargeParams.patient_id, // Use patient number directly
          patient_id: undefined, // Clear this to avoid UUID conversion errors
          discharge_condition: dischargeParams.discharge_condition || 'stable',
          discharge_destination: dischargeParams.discharge_destination || 'home'
        }});
      } else if (dischargeParams.patient_name) {
        // If we have a patient name, use it directly
        toolsNeeded.push({ name: 'discharge_patient_complete', arguments: { 
          patient_name: dischargeParams.patient_name,
          discharge_condition: dischargeParams.discharge_condition || 'stable',
          discharge_destination: dischargeParams.discharge_destination || 'home'
        }});
      } else {
        // Fallback: try to use the extracted parameters as-is
        toolsNeeded.push({ name: 'discharge_patient_complete', arguments: dischargeParams });
      }
    }
    
    if (message.includes('discharge') && message.includes('status')) {
      const statusParams = this.extractDischargeStatusParameters(userMessage);
      toolsNeeded.push({ name: 'get_patient_discharge_status', arguments: statusParams });
    }
    
    // Check if this is a multi-assignment request
    const assignmentPatterns = [
      /assign\s+staff\s+([A-Z0-9]+)\s+to\s+patient\s+([a-zA-Z\s]+)/i,
      /assign\s+equipment\s+([a-zA-Z\s]+)\s+to\s+patient\s+([a-zA-Z\s]+)/i,
      /assign\s+supplies?\s+([a-zA-Z\s]+)\s+to\s+patient\s+([a-zA-Z\s]+)/i,
      /assign\s+bed\s+([A-Z0-9]+)\s+to\s+patient\s+([a-zA-Z\s]+)/i
    ];
    
    let hasAssignments = false;
    assignmentPatterns.forEach(pattern => {
      if (pattern.test(message)) {
        hasAssignments = true;
      }
    });
    
    if (hasAssignments) {
      // This will be handled by the new assignment handler
      return [{ name: '_handle_assignments', needsInput: true }];
    }
    
    // Department creation - check if we have sufficient data
    if (message.includes('create department') || message.includes('add department') || message.includes('new department')) {
      const deptParams = this.extractDepartmentParameters(userMessage);
      if (deptParams.name && deptParams.name.length > 3 && 
          !['new', 'department', 'create', 'add'].includes(deptParams.name.toLowerCase())) {
        toolsNeeded.push({ name: 'create_department', arguments: deptParams });
      } else {
        return [{ name: '_ask_for_department_details', needsInput: true }];
      }
    }
    
    // Meeting scheduling - Check for meeting requests
    if (message.includes('schedule meeting') || message.includes('create meeting') || 
        message.includes('book meeting') || message.includes('meeting') && 
        (message.includes('schedule') || message.includes('book') || message.includes('create') || 
         message.includes('need') || message.includes('want'))) {
      const meetingParams = this.extractMeetingParameters(userMessage);
      const query = this.buildMeetingQuery(userMessage, meetingParams);
      toolsNeeded.push({ name: 'schedule_meeting', arguments: { query } });
    }
    
    // Meeting updates - Check for meeting update requests
    if (message.includes('update meeting') || message.includes('reschedule meeting') || 
        message.includes('postpone meeting') || message.includes('change meeting') || 
        message.includes('move meeting') || message.includes('shift meeting') ||
        message.includes('delay meeting') || message.includes('earlier') || message.includes('later') ||
        (message.includes('meeting') && (message.includes('update') || message.includes('reschedule') || 
         message.includes('postpone') || message.includes('change') || message.includes('move')))) {
      toolsNeeded.push({ name: 'update_meeting', arguments: { query: userMessage } });
    }
    
    // Bed operations - prioritize bed status after discharge scenarios
    // BUT: Skip this override for discharge messages to allow discharge workflow
    if (!message.includes('discharge') || !message.includes('patient')) {
      console.log('🔍 DEBUGGING BED STATUS DETECTION for message:', message);
      console.log('🔍 message.includes("bed"):', message.includes('bed'));
      console.log('🔍 message.includes("status"):', message.includes('status'));
      console.log('🔍 message.includes("check"):', message.includes('check'));
      console.log('🔍 (message.includes("check") && message.includes("bed")):', (message.includes('check') && message.includes('bed')));
      
      if ((message.includes('bed') && (message.includes('status') || message.includes('cleaning') || 
           message.includes('turnover') || message.includes('remaining') || message.includes('time'))) ||
          (message.includes('bed') && (message.includes('ready') || message.includes('available'))) ||
          (message.includes('check') && message.includes('bed'))) {
        console.log('🎯 BED STATUS CHECK TRIGGERED!');
        const bedParams = this.extractBedStatusParameters(userMessage);
        console.log('🔍 Detected bed status query, parameters:', bedParams);
        toolsNeeded.push({ name: 'get_bed_status_with_time_remaining', arguments: bedParams });
        console.log('✅ Added get_bed_status_with_time_remaining to toolsNeeded');
      }
    }
    // Generic bed listing - avoid conflicts with specific bed queries
    else if (message.includes('list beds') || message.includes('show all beds') || message.includes('all beds') || 
             (message.includes('beds') && !message.match(/bed\s+[A-Z0-9]+/i))) {
      console.log('🏥 GENERIC BED LISTING TRIGGERED for message:', message);
      console.log('🏥 message.includes("list beds"):', message.includes('list beds'));
      console.log('🏥 message.includes("show all beds"):', message.includes('show all beds'));
      console.log('🏥 message.includes("all beds"):', message.includes('all beds'));
      console.log('🏥 message.includes("beds"):', message.includes('beds'));
      console.log('🏥 message.match(/bed\\s+[A-Z0-9]+/i):', message.match(/bed\s+[A-Z0-9]+/i));
      toolsNeeded.push({ name: 'list_beds', arguments: {} });
      console.log('⚠️ Added list_beds to toolsNeeded');
    }
    
    // Bed search by bed number (e.g., "details of bed 201B", "show bed 201B", "get bed 201B info")
    const bedNumberMatch = message.match(/bed\s+([A-Z0-9]+[A-Z]?)/i);
    if ((message.includes('details of bed') || message.includes('show bed') || message.includes('get bed') || 
         message.includes('bed number') || message.includes('find bed')) && bedNumberMatch) {
      const bedNumber = bedNumberMatch[1].toUpperCase();
      toolsNeeded.push({ name: 'get_bed_by_number', arguments: { bed_number: bedNumber } });
    }
    
    // Enhanced bed creation
    if (message.includes('create bed') || message.includes('add bed') || message.includes('new bed')) {
      const bedParams = this.extractBedParameters(userMessage);
      if (bedParams.bed_number && bedParams.room_id) {
        toolsNeeded.push({ name: 'create_bed', arguments: bedParams });
      } else {
        return [{ name: '_ask_for_bed_details', needsInput: true }];
      }
    }
    
    // Equipment operations
    if (message.includes('list equipment') || message.includes('show equipment') || message.includes('all equipment') || message.includes('equipment')) {
      toolsNeeded.push({ name: 'list_equipment', arguments: {} });
    }
    
    // Enhanced equipment creation
    if (message.includes('create equipment') || message.includes('add equipment') || message.includes('new equipment')) {
      const equipmentParams = this.extractEquipmentParameters(userMessage);
      if (equipmentParams.equipment_id && equipmentParams.name && equipmentParams.category_id) {
        toolsNeeded.push({ name: 'create_equipment', arguments: equipmentParams });
      } else {
        return [{ name: '_ask_for_equipment_details', needsInput: true }];
      }
    }

    // Equipment usage tracking operations - detect "add equipment usage"
    if (message.includes('add equipment usage') || message.includes('equipment usage') || 
        message.includes('record equipment') || message.includes('track equipment')) {
      if (this.containsStructuredData(userMessage)) {
        const structuredTool = this.parseStructuredInput(userMessage);
        if (structuredTool && structuredTool.name === 'add_equipment_usage_by_codes') {
          toolsNeeded.push(structuredTool);
        } else {
          return [{ name: '_ask_for_equipment_usage_details', needsInput: true }];
        }
      } else {
        return [{ name: '_ask_for_equipment_usage_details', needsInput: true }];
      }
    }
    
    // Supply operations
    if (message.includes('list supplies') || message.includes('show supplies') || message.includes('all supplies') || message.includes('supplies')) {
      toolsNeeded.push({ name: 'list_supplies', arguments: {} });
    }
    
    // Enhanced supply creation
    if (message.includes('create supply') || message.includes('add supply') || message.includes('new supply')) {
      const supplyParams = this.extractSupplyParameters(userMessage);
      if (supplyParams.item_code && supplyParams.name && supplyParams.category_id && supplyParams.unit_of_measure) {
        toolsNeeded.push({ name: 'create_supply', arguments: supplyParams });
      } else {
        return [{ name: '_ask_for_supply_details', needsInput: true }];
      }
    }
    
    // Room operations
    if (message.includes('list rooms') || message.includes('show rooms') || message.includes('all rooms') || message.includes('rooms')) {
      toolsNeeded.push({ name: 'list_rooms', arguments: {} });
    }
    
    // Enhanced room creation
    if (message.includes('create room') || message.includes('add room') || message.includes('new room')) {
      const roomParams = this.extractRoomParameters(userMessage);
      if (roomParams.room_number && roomParams.department_id) {
        toolsNeeded.push({ name: 'create_room', arguments: roomParams });
      } else {
        return [{ name: '_ask_for_room_details', needsInput: true }];
      }
    }
    
    // User operations
    if (message.includes('list users') || message.includes('show users') || message.includes('all users') || message.includes('users')) {
      toolsNeeded.push({ name: 'list_users', arguments: {} });
    }
    
    // Enhanced user creation
    if (message.includes('create user') || message.includes('add user') || message.includes('new user')) {
      const userParams = this.extractUserParameters(userMessage);
      if (userParams.username && userParams.email && userParams.role && userParams.first_name && userParams.last_name) {
        toolsNeeded.push({ name: 'create_user', arguments: userParams });
      } else {
        return [{ name: '_ask_for_user_details', needsInput: true }];
      }
    }
    
    // Get operations for specific records
    if (message.includes('get user') || message.includes('find user by id')) {
      const userId = this.extractId(userMessage, ['user', 'id']);
      if (userId) {
        toolsNeeded.push({ name: 'get_user_by_id', arguments: { user_id: userId } });
      }
    }
    
    if (message.includes('get patient') || message.includes('find patient by id')) {
      const patientId = this.extractId(userMessage, ['patient', 'id', 'pat']);
      if (patientId) {
        toolsNeeded.push({ name: 'get_patient_by_id', arguments: { patient_id: patientId } });
      }
    }
    
    if (message.includes('get staff') || message.includes('find staff by id')) {
      const staffId = this.extractId(userMessage, ['staff', 'employee', 'emp']);
      if (staffId) {
        toolsNeeded.push({ name: 'get_staff_by_id', arguments: { staff_id: staffId } });
      }
    }
    
    if (message.includes('get department') || message.includes('find department by id')) {
      const deptId = this.extractId(userMessage, ['department', 'dept']);
      if (deptId) {
        toolsNeeded.push({ name: 'get_department_by_id', arguments: { department_id: deptId } });
      }
    }
    
    if (message.includes('get equipment') || message.includes('find equipment by id')) {
      const equipId = this.extractId(userMessage, ['equipment', 'eq']);
      if (equipId) {
        toolsNeeded.push({ name: 'get_equipment_by_id', arguments: { equipment_id: equipId } });
      }
    }
    
    // Update operations
    if (message.includes('update user') || message.includes('edit user')) {
      const updateParams = this.extractUpdateUserParameters(userMessage);
      if (updateParams.user_id) {
        toolsNeeded.push({ name: 'update_user', arguments: updateParams });
      }
    }
    
    if (message.includes('update equipment status') || message.includes('equipment status')) {
      const statusParams = this.extractEquipmentStatusParameters(userMessage);
      if (statusParams.equipment_id && statusParams.status) {
        toolsNeeded.push({ name: 'update_equipment_status', arguments: statusParams });
      }
    }
    
    if (message.includes('update supply stock') || message.includes('stock update')) {
      const stockParams = this.extractSupplyStockParameters(userMessage);
      if (stockParams.supply_id && stockParams.quantity_change && stockParams.transaction_type) {
        toolsNeeded.push({ name: 'update_supply_stock', arguments: stockParams });
      }
    }
    
    // Assignment operations
    if (message.includes('assign bed') || message.includes('bed assignment') || message.includes('assign patient')) {
      const assignParams = this.extractBedAssignmentParameters(userMessage);
      
      // Check if we have bed_number (need to convert to bed_id) and patient info
      if (assignParams.bed_number && (assignParams.patient_id || assignParams.patient_name)) {
        // We need to lookup the bed by number to get the UUID first
        if (assignParams.patient_id) {
          // We have patient ID directly
          toolsNeeded.push({ name: 'get_bed_by_number', arguments: { bed_number: assignParams.bed_number } });
          toolsNeeded.push({ name: 'assign_bed_to_patient', arguments: { 
            bed_id: '{{bed_id_from_lookup}}', 
            patient_id: assignParams.patient_id,
            admission_date: assignParams.admission_date || new Date().toISOString().split('T')[0]
          }});
        } else if (assignParams.patient_name) {
          // We need to search for patient first, then lookup bed
          const searchParams = this.parsePatientNameForSearch(assignParams.patient_name);
          toolsNeeded.push({ name: 'search_patients', arguments: searchParams });
          toolsNeeded.push({ name: 'get_bed_by_number', arguments: { bed_number: assignParams.bed_number } });
          toolsNeeded.push({ name: 'assign_bed_to_patient', arguments: { 
            bed_id: '{{bed_id_from_lookup}}', 
            patient_id: '{{patient_id_from_search}}',
            admission_date: assignParams.admission_date || new Date().toISOString().split('T')[0]
          }});
        }
      }
      // If we have patient_name but no bed_number, find an available bed
      else if (assignParams.patient_name && !assignParams.bed_number) {
        const searchParams = this.parsePatientNameForSearch(assignParams.patient_name);
        toolsNeeded.push({ name: 'search_patients', arguments: searchParams });
        toolsNeeded.push({ name: 'list_beds', arguments: { status: 'available' } });
        toolsNeeded.push({ name: 'assign_bed_to_patient', arguments: { 
          bed_id: '{{available_bed_id}}', 
          patient_id: '{{patient_id_from_search}}', 
          admission_date: assignParams.admission_date || new Date().toISOString().split('T')[0]
        }});
      }
    }

    // Staff assignment operations
    if (message.includes('assign staff') || message.includes('staff assignment')) {
      const staffAssignParams = this.extractStaffAssignmentParameters(userMessage);
      console.log('🔧 Staff assignment params extracted:', staffAssignParams);
      
      // If we have both staff_id and patient_id, we can assign directly
      if (staffAssignParams.staff_id && staffAssignParams.patient_id) {
        toolsNeeded.push({ 
          name: 'assign_staff_to_patient_simple', 
          arguments: {
            ...staffAssignParams,
            assignment_type: 'primary_care' // Add required parameter
          }
        });
      }
      // If we have staff_id and patient_name, we need to search for patient first
      else if (staffAssignParams.staff_id && staffAssignParams.patient_name) {
        // First search for the patient
        const searchParams = this.parsePatientNameForSearch(staffAssignParams.patient_name);
        toolsNeeded.push({ name: 'search_patients', arguments: searchParams });
        // Note: The actual assignment will need to be done after patient search results
      }
    }

    // Equipment assignment operations
    if (message.includes('assign equipment') || message.includes('equipment assignment')) {
      const equipAssignParams = this.extractEquipmentAssignmentParameters(userMessage);
      console.log('🔧 Equipment assignment params extracted:', equipAssignParams);
      
      // If we have both equipment_id and patient_id, we can assign directly
      if (equipAssignParams.equipment_id && equipAssignParams.patient_id) {
        toolsNeeded.push({ 
          name: 'add_equipment_usage_by_codes', 
          arguments: {
            ...equipAssignParams,
            employee_id: 'EMP002', // Add required parameter
            purpose: 'patient_care' // Add required parameter
          }
        });
      }
      // If we have equipment_name and patient_name, we need to search for both
      else if (equipAssignParams.equipment_name && equipAssignParams.patient_name) {
        // First search for the patient and equipment
        const searchParams = this.parsePatientNameForSearch(equipAssignParams.patient_name);
        toolsNeeded.push({ name: 'search_patients', arguments: searchParams });
        toolsNeeded.push({ name: 'list_equipment', arguments: {} });
        // Note: The actual assignment will need to be done after search results
      }
    }

    // Supply assignment operations
    if (message.includes('assign supply') || message.includes('supply assignment') || message.includes('assign supplies')) {
      const supplyAssignParams = this.extractSupplyAssignmentParameters(userMessage);
      console.log('🔧 Supply assignment params extracted:', supplyAssignParams);
      
      // If we have both supply_id and patient_id, we can assign directly
      if (supplyAssignParams.supply_id && supplyAssignParams.patient_id) {
        toolsNeeded.push({ 
          name: 'update_supply_stock', 
          arguments: {
            ...supplyAssignParams,
            quantity_change: -1, // Reduce stock by 1
            transaction_type: 'patient_usage',
            performed_by: 'EMP002' // Add required parameter
          }
        });
      }
      // If we have supply_name and patient_name, search for both
      else if (supplyAssignParams.supply_name && supplyAssignParams.patient_name) {
        const searchParams = this.parsePatientNameForSearch(supplyAssignParams.patient_name);
        toolsNeeded.push({ name: 'search_patients', arguments: searchParams });
        toolsNeeded.push({ name: 'list_supplies', arguments: {} });
        toolsNeeded.push({ 
          name: 'update_supply_stock', 
          arguments: { 
            supply_id: '{{supply_id_from_search}}', 
            quantity_change: -1,
            transaction_type: 'patient_usage',
            performed_by: 'EMP002'
          }
        });
      }
    }
    
    // Handle bed discharge (different from patient discharge workflow)
    if (message.includes('discharge bed') || message.includes('bed discharge')) {
      const dischargeParams = this.extractBedDischargeParameters(userMessage);
      if (dischargeParams.bed_number) {
        // Need to lookup bed by number to get UUID first
        toolsNeeded.push({ name: 'get_bed_by_number', arguments: { bed_number: dischargeParams.bed_number } });
        toolsNeeded.push({ name: 'discharge_bed', arguments: { 
          bed_id: '{{bed_id_from_lookup}}',
          discharge_date: dischargeParams.discharge_date || new Date().toISOString().split('T')[0]
        }});
      }
    }
    
    // Delete operations
    if (message.includes('delete user') || message.includes('remove user')) {
      const userId = this.extractId(userMessage, ['user', 'id']);
      if (userId) {
        toolsNeeded.push({ name: 'delete_user', arguments: { user_id: userId } });
      }
    }
    
    // Category creation operations
    if (message.includes('create equipment category') || message.includes('add equipment category')) {
      const categoryParams = this.extractCategoryParameters(userMessage, 'equipment');
      if (categoryParams.name) {
        toolsNeeded.push({ name: 'create_equipment_category', arguments: categoryParams });
      }
    }
    
    if (message.includes('create supply category') || message.includes('add supply category')) {
      const categoryParams = this.extractCategoryParameters(userMessage, 'supply');
      if (categoryParams.name) {
        toolsNeeded.push({ name: 'create_supply_category', arguments: categoryParams });
      }
    }
    
    // Legacy operations
    if (message.includes('create legacy user') || message.includes('add legacy user')) {
      const legacyParams = this.extractLegacyUserParameters(userMessage);
      if (legacyParams.name && legacyParams.email) {
        toolsNeeded.push({ name: 'create_legacy_user', arguments: legacyParams });
      }
    }
    
    if (message.includes('list legacy users') || message.includes('show legacy users')) {
      toolsNeeded.push({ name: 'list_legacy_users', arguments: {} });
    }
    
    console.log('🔧 Tools needed:', toolsNeeded);
    console.log('🔧 Tools needed length:', toolsNeeded.length);
    console.log('🔧 First tool (if any):', toolsNeeded[0]);
    return toolsNeeded;
  }

  /**
   * Handle assignment operations intelligently
   */
  async handleAssignmentOperations(userMessage, toolResults) {
    console.log('🔧 Handling assignment operations...');
    
    // Check if this is a multi-assignment request
    const assignmentPatterns = [
      /assign\s+staff\s+([A-Z0-9]+)\s+to\s+patient\s+([a-zA-Z\s]+)/i,
      /assign\s+equipment\s+([a-zA-Z\s]+)\s+to\s+patient\s+([a-zA-Z\s]+)/i,
      /assign\s+supplies?\s+([a-zA-Z\s]+)\s+to\s+patient\s+([a-zA-Z\s]+)/i,
      /assign\s+bed\s+([A-Z0-9]+)\s+to\s+patient\s+([a-zA-Z\s]+)/i
    ];
    
    let hasAssignments = false;
    let assignments = [];
    
    // Extract all assignment requests
    assignmentPatterns.forEach((pattern, index) => {
      const match = userMessage.match(pattern);
      if (match) {
        hasAssignments = true;
        const [fullMatch, resource, patientName] = match;
        
        switch (index) {
          case 0: // Staff assignment
            assignments.push({
              type: 'staff',
              resource: resource.trim(),
              patientName: patientName.trim(),
              message: fullMatch
            });
            break;
          case 1: // Equipment assignment
            assignments.push({
              type: 'equipment',
              resource: resource.trim(),
              patientName: patientName.trim(),
              message: fullMatch
            });
            break;
          case 2: // Supply assignment
            assignments.push({
              type: 'supply',
              resource: resource.trim(),
              patientName: patientName.trim(),
              message: fullMatch
            });
            break;
          case 3: // Bed assignment
            assignments.push({
              type: 'bed',
              resource: resource.trim(),
              patientName: patientName.trim(),
              message: fullMatch
            });
            break;
        }
      }
    });
    
    if (!hasAssignments) {
      return null; // Not an assignment operation
    }
    
    console.log('🔧 Found assignments:', assignments);
    
    // Process each assignment
    let results = [];
    for (const assignment of assignments) {
      try {
        const result = await this.processAssignment(assignment);
        results.push(result);
      } catch (error) {
        console.error(`❌ Error processing assignment ${assignment.type}:`, error);
        results.push({
          type: assignment.type,
          success: false,
          message: `Error: ${error.message}`
        });
      }
    }
    
    return this.formatAssignmentResults(results);
  }

  /**
   * Process a single assignment
   */
  async processAssignment(assignment) {
    console.log(`🔧 Processing ${assignment.type} assignment...`);
    
    try {
      // First, find the patient
      const searchParams = this.parsePatientNameForSearch(assignment.patientName);
      const patientResponse = await this.callTool('search_patients', searchParams);
      if (!patientResponse.success || !patientResponse.result?.data?.[0]) {
        return {
          type: assignment.type,
          success: false,
          message: `Patient ${assignment.patientName} not found`
        };
      }
      
      const patient = patientResponse.result.data[0];
      const patientId = patient.id;
      console.log(`✅ Found patient: ${patient.first_name} ${patient.last_name} (ID: ${patientId})`);
      
      // Process based on assignment type
      switch (assignment.type) {
        case 'staff':
          return await this.assignStaffToPatient(assignment.resource, patientId);
        case 'equipment':
          return await this.assignEquipmentToPatient(assignment.resource, patientId);
        case 'supply':
          return await this.assignSupplyToPatient(assignment.resource, patientId);
        case 'bed':
          return await this.assignBedToPatient(assignment.resource, patientId);
        default:
          return {
            type: assignment.type,
            success: false,
            message: `Unknown assignment type: ${assignment.type}`
          };
      }
    } catch (error) {
      console.error(`❌ Error in processAssignment:`, error);
      return {
        type: assignment.type,
        success: false,
        message: `Error: ${error.message}`
      };
    }
  }

  /**
   * Assign staff to patient
   */
  async assignStaffToPatient(staffId, patientId) {
    console.log(`🔧 Assigning staff ${staffId} to patient ${patientId}...`);
    
    try {
      // If staffId looks like an employee ID (EMP001), find the actual staff UUID
      let actualStaffId = staffId;
      
      if (staffId.startsWith('EMP')) {
        const staffResponse = await this.callTool('list_staff', {});
        if (staffResponse.success && staffResponse.result?.data) {
          const staff = staffResponse.result.data.find(s => s.employee_id === staffId);
          if (!staff) {
            return {
              type: 'staff',
              success: false,
              message: `Staff with employee ID ${staffId} not found`
            };
          }
          actualStaffId = staff.id; // Use the UUID
          console.log(`✅ Found staff: ${staff.first_name} ${staff.last_name} (UUID: ${actualStaffId})`);
        } else {
          return {
            type: 'staff',
            success: false,
            message: 'Could not retrieve staff list'
          };
        }
      }
      
      const response = await this.callTool('assign_staff_to_patient_simple', {
        staff_id: actualStaffId,
        patient_id: patientId,
        assignment_type: 'primary_care'
      });
      
      return {
        type: 'staff',
        success: response.success && response.result?.success,
        message: response.result?.success ? 'Staff assigned successfully' : (response.result?.message || response.message || 'Assignment failed'),
        details: response
      };
    } catch (error) {
      return {
        type: 'staff',
        success: false,
        message: `Error assigning staff: ${error.message}`
      };
    }
  }

  /**
   * Assign equipment to patient
   */
  async assignEquipmentToPatient(equipmentName, patientId) {
    console.log(`🔧 Assigning equipment ${equipmentName} to patient ${patientId}...`);
    
    try {
      // First, find the equipment
      const equipmentResponse = await this.callTool('list_equipment', {});
      if (!equipmentResponse.success || !equipmentResponse.result?.data) {
        return {
          type: 'equipment',
          success: false,
          message: 'Could not retrieve equipment list'
        };
      }
      
      // Find equipment by name
      const equipment = equipmentResponse.result.data.find(eq => 
        eq.name.toLowerCase().includes(equipmentName.toLowerCase())
      );
      
      if (!equipment) {
        return {
          type: 'equipment',
          success: false,
          message: `Equipment ${equipmentName} not found`
        };
      }
      
      if (equipment.status !== 'available') {
        return {
          type: 'equipment',
          success: false,
          message: `Equipment ${equipmentName} is not available (status: ${equipment.status})`
        };
      }
      
      // Get a staff member for the assignment
      const staffResponse = await this.callTool('list_staff', {});
      if (!staffResponse.success || !staffResponse.result?.data?.length) {
        return {
          type: 'equipment',
          success: false,
          message: 'No staff available for equipment assignment'
        };
      }
      
      const staff = staffResponse.result.data[0]; // Use first available staff
      
      // Assign the equipment using the working tool
      const response = await this.callTool('add_equipment_usage_by_codes', {
        patient_number: patient.patient_number, // Use patient number
        equipment_id: equipment.equipment_id, // Use equipment code  
        employee_id: staff.employee_id, // Use staff employee code
        purpose: 'patient_care'
      });
      
      return {
        type: 'equipment',
        success: response.success && response.result?.success,
        message: response.result?.success ? `Equipment ${equipmentName} assigned successfully` : (response.result?.message || response.message || 'Assignment failed'),
        details: response
      };
    } catch (error) {
      return {
        type: 'equipment',
        success: false,
        message: `Error assigning equipment: ${error.message}`
      };
    }
  }

  /**
   * Assign supply to patient
   */
  async assignSupplyToPatient(supplyName, patientId) {
    console.log(`🔧 Assigning supply ${supplyName} to patient ${patientId}...`);
    
    try {
      // First, find the supply
      const supplyResponse = await this.callTool('list_supplies', {});
      if (!supplyResponse.success || !supplyResponse.result?.data) {
        return {
          type: 'supply',
          success: false,
          message: 'Could not retrieve supplies list'
        };
      }
      
      // Find supply by name
      const supply = supplyResponse.result.data.find(sup => 
        sup.name.toLowerCase().includes(supplyName.toLowerCase())
      );
      
      if (!supply) {
        return {
          type: 'supply',
          success: false,
          message: `Supply ${supplyName} not found`
        };
      }
      
      if (supply.current_stock <= 0) {
        return {
          type: 'supply',
          success: false,
          message: `Supply ${supplyName} is out of stock`
        };
      }
      
      // Get a staff member to perform the transaction
      const staffResponse = await this.callTool('list_staff', {});
      if (!staffResponse.success || !staffResponse.result?.data?.length) {
        return {
          type: 'supply',
          success: false,
          message: 'No staff available for supply allocation'
        };
      }
      
      const staff = staffResponse.result.data[0]; // Use first available staff
      
      // Assign the supply using correct parameters
      const response = await this.callTool('update_supply_stock', {
        supply_id: supply.id,
        quantity_change: -1, // Allocate 1 unit
        transaction_type: 'ALLOCATION',
        performed_by: staff.id,
        notes: `Allocated to patient ${patientId}`
      });
      
      return {
        type: 'supply',
        success: response.success,
        message: response.success ? `Supply ${supplyName} allocated successfully` : (response.message || 'Allocation failed'),
        details: response
      };
    } catch (error) {
      return {
        type: 'supply',
        success: false,
        message: `Error assigning supply: ${error.message}`
      };
    }
  }

  /**
   * Assign bed to patient
   */
  async assignBedToPatient(bedNumber, patientId) {
    console.log(`🔧 Assigning bed ${bedNumber} to patient ${patientId}...`);
    
    try {
      // First, find the bed
      const bedResponse = await this.callTool('get_bed_by_number', { bed_number: bedNumber });
      if (!bedResponse.success || !bedResponse.result?.data) {
        return {
          type: 'bed',
          success: false,
          message: `Bed ${bedNumber} not found`
        };
      }
      
      const bed = bedResponse.result.data;
      
      if (bed.status !== 'available') {
        return {
          type: 'bed',
          success: false,
          message: `Bed ${bedNumber} is not available (status: ${bed.status})`
        };
      }
      
      // Assign the bed with correct date format
      const response = await this.callTool('assign_bed_to_patient', {
        bed_id: bed.id,
        patient_id: patientId,
        admission_date: new Date().toISOString().split('T')[0] // Use YYYY-MM-DD format
      });
      
      return {
        type: 'bed',
        success: response.success && response.result?.success,
        message: response.result?.success ? `Bed ${bedNumber} assigned successfully` : (response.result?.message || response.message || 'Assignment failed'),
        details: response
      };
    } catch (error) {
      return {
        type: 'bed',
        success: false,
        message: `Error assigning bed: ${error.message}`
      };
    }
  }

  /**
   * Format assignment results
   */
  formatAssignmentResults(results) {
    let response = '## 🎯 **Assignment Results**\n\n';
    
    results.forEach(result => {
      if (result.success) {
        response += `✅ **${result.type.toUpperCase()} Assignment**: ${result.message}\n\n`;
      } else {
        response += `❌ **${result.type.toUpperCase()} Assignment**: ${result.message}\n\n`;
      }
    });
    
    return response;
  }

  /**
   * Call a tool directly
   */
  async callTool(toolName, args) {
    console.log(`🔧 CALLING TOOL: ${toolName} with args:`, args);
    try {
      const baseUrl = `http://${window.location.hostname}:8000`;
      
      const response = await fetch(`${baseUrl}/tools/call`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          jsonrpc: '2.0',
          id: 1,
          method: 'tools/call',
          params: {
            name: toolName,
            arguments: args
          }
        })
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const result = await response.json();
      console.log(`🔧 TOOL RESPONSE for ${toolName}:`, result);
      
  if (result.result?.content?.[0]?.text) {
        try {
          const parsedContent = JSON.parse(result.result.content[0].text);
          console.log(`🔧 PARSED CONTENT for ${toolName}:`, parsedContent);
          return {
            success: parsedContent.success || false,
            message: parsedContent.message || '',
            result: parsedContent.result || parsedContent
          };
        } catch {
          console.log(`🔧 PARSE ERROR for ${toolName}, raw text:`, result.result.content[0].text);
          return {
            success: false,
            message: 'Could not parse response',
            result: result.result.content[0].text
          };
        }
      }
      
      return {
        success: false,
        message: 'Invalid response format',
        result: result
      };
  } catch (error) {
      console.error(`❌ Error calling tool ${toolName}:`, error);
      return {
        success: false,
        message: `Error: ${error.message}`,
        result: null
      };
    }
  }

  /**
   * Generate response using OpenAI with enhanced system prompt for intelligent conversation
   */
  async generateResponse(userMessage, toolResults, availableTools) {
    // If no OpenAI API key, provide simple formatted response
    if (!this.openaiApiKey) {
      return this.formatToolResults(userMessage, toolResults);
    }

    const systemPrompt = `You are an intelligent hospital management assistant with advanced conversation capabilities. You can perform complex multi-step operations and have memory of previous interactions.

🏥 **Hospital Management System - AI Assistant**

**Core Capabilities:**
1. **Intelligent Parameter Collection**: When users request operations without complete information, ask for missing details conversationally
2. **Multi-Tool Operations**: Automatically resolve foreign keys by searching for IDs when users provide names
3. **Conversation Memory**: Remember context and avoid asking for information already provided
4. **Smart Validation**: Validate data before operations and provide helpful feedback

**Advanced Behaviors:**

**1. INCOMPLETE CREATE REQUESTS:**
When users say "create new department" without details:
- ASK: "I'd be happy to create a new department! What should I call this department? For example: 'Cardiology', 'Emergency', 'Pediatrics', etc."
- NEVER create with placeholder names like "New" or "Unnamed"
- Collect required fields conversationally before proceeding

**2. FOREIGN KEY RESOLUTION:**
When operations require IDs but users provide names:
- AUTOMATICALLY search for IDs using available list/search tools
- Example: "Schedule meeting with Dr. Smith in Cardiology"
  1. Search staff for "Dr. Smith" to get staff_id  
  2. Search departments for "Cardiology" to get department_id
  3. Then create meeting with resolved IDs

**3. CONVERSATION FLOW:**
- Remember what the user is trying to accomplish
- If missing information, ask ONE question at a time
- Provide examples of valid formats
- Confirm before executing operations

**4. ERROR HANDLING:**
- If foreign key lookups fail, suggest alternatives
- Provide helpful error messages with next steps
- Offer to list available options when searches fail

**5. LIST TOOLS RESPONSE FORMAT:**
When using any LIST tools (list_patients, list_staff, list_departments, list_beds, list_rooms, list_equipment, list_supplies, list_users, list_meetings, list_discharge_reports, list_equipment_categories, list_supply_categories, list_inventory_transactions, list_legacy_users), provide ONLY essential information:

- **list_patients**: Only show patient names (first_name + last_name) and patient numbers
- **list_staff**: Only show staff names (first_name + last_name) and positions
- **list_departments**: Only show department names
- **list_beds**: Only show bed numbers and room assignments
- **list_rooms**: Only show room numbers and types
- **list_equipment**: Only show equipment names and status
- **list_supplies**: Only show supply names and current stock levels
- **list_users**: Only show usernames and roles
- **list_meetings**: Only show meeting topics and dates
- **All other list tools**: Only show names/titles and key status information

DO NOT show full details, IDs, or technical information unless specifically requested. This prevents "(Further details are truncated for brevity)" messages and keeps responses clean and readable.

**Available Tools:**
${availableTools.map(tool => `- ${tool.name}: ${tool.description}`).join('\n')}

**Tool Execution Results:**
${toolResults.map(result => {
  if (result.error) {
    return `❌ ${result.tool}: Error - ${result.error}`;
  } else {
    return `✅ ${result.tool}: ${JSON.stringify(result.result, null, 2)}`;
  }
}).join('\n\n')}

**Response Guidelines:**
- Be conversational and helpful
- Ask clarifying questions when needed
- Explain what you're doing for multi-step operations
- Provide clear success/failure feedback
- Hide technical UUIDs from users
- Focus on user-friendly information
- Remember the conversation context

Respond naturally and helpfully based on the user's request and the tool results.`;

    try {
      const response = await fetch('https://api.openai.com/v1/chat/completions', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${this.openaiApiKey}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          model: 'gpt-4',
          messages: [
            { role: 'system', content: systemPrompt },
            { role: 'user', content: userMessage }
          ],
          temperature: 0.7,
          max_tokens: 4000
        })
      });

      if (!response.ok) {
        throw new Error(`OpenAI API error: ${response.status}`);
      }

      const data = await response.json();
      return data.choices[0].message.content;

    } catch (error) {
      console.error('❌ Failed to generate response:', error);
      return this.formatToolResults(userMessage, toolResults);
    }
  }

  /**
   * Format tool results without OpenAI
   */
  formatToolResults(userMessage, toolResults) {
    if (toolResults.length === 0) {
      return "I understand your request, but I couldn't find any specific operations to perform. Please try being more specific about what you'd like to do (e.g., 'list patients', 'show departments', etc.).";
    }

    let response = "";
    
    toolResults.forEach(result => {
      const toolName = result.tool || result.function; // Support both formats
      if (result.error) {
        response += `❌ **Error with ${toolName}**: ${result.error}\n\n`;
      } else {
        // Handle both old format (result.result.content[0].text) and new direct format
        let data;
        if (result.result?.content?.[0]?.text) {
          // Old format - parse JSON from text
          try {
            data = JSON.parse(result.result.content[0].text);
          } catch {
            data = result.result.content[0].text;
          }
        } else if (result.result) {
          // New format - data is already parsed
          data = result.result;
        }
        
        if (data) {
          try {
            // Handle the response structure - check if data is nested under result.data
            let actualData = data;
            if (data.success && data.result && data.result.data) {
              actualData = data.result.data;
            } else if (data.result && Array.isArray(data.result)) {
              actualData = data.result;
            } else if (data.data && Array.isArray(data.data)) {
              actualData = data.data;
            }
            
            if (Array.isArray(actualData) && actualData.length > 0) {
              response += `✅ **${toolName.replace('_', ' ').toUpperCase()}**\n\n`;
              response += `Found ${actualData.length} record(s):\n\n`;
              
              // Check if this is a list or search tool and format accordingly
              if (toolName.startsWith('list_') || toolName.startsWith('search_')) {
                actualData.forEach((item, index) => {
                  response += `**${index + 1}.** `;
                  
                  // Format based on tool type - Enhanced details for search operations
                  switch (toolName) {
                    case 'list_patients':
                      if (item.first_name && item.last_name) {
                        response += `${item.first_name} ${item.last_name}`;
                        if (item.patient_number) response += ` (${item.patient_number})`;
                      }
                      break;
                      
                    case 'search_patients':
                      if (item.first_name && item.last_name) {
                        response += `**${item.first_name} ${item.last_name}**`;
                        if (item.patient_number) response += ` (${item.patient_number})`;
                        response += `\n`;
                        if (item.email) response += `   📧 Email: ${item.email}\n`;
                        if (item.phone) response += `   📱 Phone: ${item.phone}\n`;
                        if (item.date_of_birth) response += `   🎂 DOB: ${item.date_of_birth}\n`;
                        if (item.gender) response += `   👤 Gender: ${item.gender}\n`;
                        if (item.blood_type) response += `   🩸 Blood Type: ${item.blood_type}\n`;
                        if (item.status) response += `   ✅ Status: ${item.status}\n`;
                        response = response.slice(0, -1); // Remove last newline
                      }
                      break;
                      
                    case 'list_staff':
                      if (item.first_name && item.last_name) {
                        response += `${item.first_name} ${item.last_name}`;
                        if (item.position) response += ` - ${item.position}`;
                      }
                      break;
                      
                    case 'search_staff':
                      if (item.first_name && item.last_name) {
                        response += `**${item.first_name} ${item.last_name}**`;
                        if (item.position) response += ` - ${item.position}`;
                        response += `\n`;
                        if (item.email) response += `   📧 Email: ${item.email}\n`;
                        if (item.phone) response += `   📱 Phone: ${item.phone}\n`;
                        if (item.department_name) response += `   🏥 Department: ${item.department_name}\n`;
                        if (item.status) response += `   ✅ Status: ${item.status}\n`;
                        response = response.slice(0, -1); // Remove last newline
                      }
                      break;
                      
                    case 'list_departments':
                      if (item.name) {
                        response += `${item.name}`;
                        if (item.floor) response += ` (Floor ${item.floor})`;
                      }
                      break;
                      
                    case 'search_departments':
                      if (item.name) {
                        response += `**${item.name}**`;
                        response += `\n`;
                        if (item.floor) response += `   🏢 Floor: ${item.floor}\n`;
                        if (item.description) response += `   📝 Description: ${item.description}\n`;
                        if (item.head_of_department) response += `   👨‍⚕️ Head: ${item.head_of_department}\n`;
                        response = response.slice(0, -1); // Remove last newline
                      }
                      break;
                      
                    case 'list_beds':
                      if (item.bed_number) {
                        response += `Bed ${item.bed_number}`;
                        if (item.room_number) response += ` - Room ${item.room_number}`;
                        if (item.status) response += ` (${item.status})`;
                      }
                      break;
                      
                    case 'search_beds':
                      if (item.bed_number) {
                        response += `**Bed ${item.bed_number}**`;
                        response += `\n`;
                        if (item.room_number) response += `   🏠 Room: ${item.room_number}\n`;
                        if (item.bed_type) response += `   🛏️ Type: ${item.bed_type}\n`;
                        if (item.status) {
                          const statusIcon = item.status === 'available' ? '✅' : item.status === 'occupied' ? '🔴' : '⚠️';
                          response += `   ${statusIcon} Status: ${item.status}\n`;
                        }
                        if (item.patient_id) response += `   👤 Patient ID: ${item.patient_id}\n`;
                        response = response.slice(0, -1); // Remove last newline
                      }
                      break;
                      
                    case 'get_bed_by_number':
                      if (item.bed_number) {
                        response += `🛏️ **Bed ${item.bed_number}** - Complete Details\n\n`;
                        if (item.id) response += `**Bed ID:** ${item.id}\n`;
                        if (item.room_id) response += `**Room ID:** ${item.room_id}\n`;
                        if (item.bed_type) response += `**Bed Type:** ${item.bed_type}\n`;
                        if (item.status) {
                          const statusIcon = item.status === 'available' ? '✅' : item.status === 'occupied' ? '🔴' : '⚠️';
                          response += `**Status:** ${statusIcon} ${item.status.toUpperCase()}\n`;
                        }
                        if (item.patient_id) {
                          response += `**Current Patient:** ${item.patient_id}\n`;
                        } else {
                          response += `**Current Patient:** None (Available)\n`;
                        }
                        if (item.admission_date) response += `**Admission Date:** ${item.admission_date}\n`;
                        if (item.notes) response += `**Notes:** ${item.notes}\n`;
                        response += `\n**Actions Available:**\n`;
                        if (item.status === 'available') {
                          response += `• Assign to patient: "Assign bed ${item.bed_number} to patient [name]"\n`;
                        } else if (item.status === 'occupied') {
                          response += `• Discharge patient: "Discharge bed ${item.bed_number}"\n`;
                        }
                        response += `• Update status: "Update bed ${item.bed_number} status to [status]"\n`;
                      }
                      break;
                      
                    case 'list_rooms':
                    case 'search_rooms':
                      if (item.room_number) {
                        response += `Room ${item.room_number}`;
                        if (item.room_type) response += ` - ${item.room_type}`;
                      }
                      break;
                      
                    case 'list_equipment':
                    case 'search_equipment':
                      if (item.name) {
                        response += `${item.name}`;
                        if (item.status) response += ` (${item.status})`;
                      }
                      break;
                      
                    case 'list_supplies':
                    case 'search_supplies':
                      if (item.name) {
                        response += `${item.name}`;
                        if (item.current_stock !== undefined) response += ` - Stock: ${item.current_stock}`;
                      }
                      break;
                      
                    case 'list_users':
                    case 'search_users':
                      if (item.username) {
                        response += `${item.username}`;
                        if (item.role) response += ` (${item.role})`;
                      }
                      break;
                      
                    case 'list_meetings':
                    case 'search_meetings':
                      if (item.topic) {
                        response += `${item.topic}`;
                        if (item.meeting_date) response += ` - ${item.meeting_date}`;
                      }
                      break;
                      
                    case 'list_discharge_reports':
                    case 'search_discharge_reports':
                      if (item.report_number) {
                        response += `Report ${item.report_number}`;
                        if (item.patient_name) response += ` - ${item.patient_name}`;
                        if (item.discharge_date) response += ` (${item.discharge_date})`;
                      }
                      break;
                      
                    case 'list_equipment_categories':
                    case 'search_equipment_categories':
                      if (item.name) {
                        response += `${item.name}`;
                        if (item.description) response += ` - ${item.description}`;
                      }
                      break;
                      
                    case 'list_supply_categories':
                    case 'search_supply_categories':
                      if (item.name) {
                        response += `${item.name}`;
                        if (item.description) response += ` - ${item.description}`;
                      }
                      break;
                      
                    case 'list_inventory_transactions':
                    case 'search_inventory_transactions':
                      if (item.transaction_type) {
                        response += `${item.transaction_type}`;
                        if (item.item_name) response += ` - ${item.item_name}`;
                        if (item.quantity) response += ` (Qty: ${item.quantity})`;
                        if (item.transaction_date) response += ` - ${item.transaction_date}`;
                      }
                      break;
                      
                    case 'list_legacy_users':
                    case 'search_legacy_users':
                      if (item.username) {
                        response += `${item.username}`;
                        if (item.role) response += ` (${item.role})`;
                        if (item.status) response += ` - ${item.status}`;
                      }
                      break;
                      
                    default:
                      // For other list tools, show name/title and key info
                      if (item.name) {
                        response += `${item.name}`;
                      } else if (item.title) {
                        response += `${item.title}`;
                      } else if (item.first_name && item.last_name) {
                        response += `${item.first_name} ${item.last_name}`;
                      } else {
                        response += `${Object.keys(item)[0]}: ${Object.values(item)[0]}`;
                      }
                      break;
                  }
                  response += "\n";
                });
              } else {
                // Non-list tools - show more details
                data.forEach((item, index) => {
                  response += `**${index + 1}.** `;
                  if (item.first_name && item.last_name) {
                    response += `${item.first_name} ${item.last_name}`;
                    if (item.patient_number) response += ` (${item.patient_number})`;
                    if (item.email) response += ` - ${item.email}`;
                    if (item.phone) response += ` - ${item.phone}`;
                  } else if (item.name) {
                    response += `${item.name}`;
                    if (item.description) response += ` - ${item.description}`;
                  } else {
                    response += JSON.stringify(item, null, 2);
                  }
                  response += "\n";
                });
              }
              response += "\n";
            } else if (Array.isArray(actualData) && actualData.length === 0) {
              response += `✅ **${toolName.replace('_', ' ').toUpperCase()}**: No records found\n\n`;
            } else if (!Array.isArray(actualData) && actualData && actualData.length === 0) {
              response += `✅ **${toolName.replace('_', ' ').toUpperCase()}**: No records found\n\n`;
            } else {
              // Handle single object results
              if (toolName === 'get_patient_by_id' || toolName === 'get_patient_by_number') {
                if (actualData) {
                  response += `✅ **PATIENT DETAILS**\n\n`;
                  if (actualData.first_name && actualData.last_name) {
                    response += `👤 **Name:** ${actualData.first_name} ${actualData.last_name}\n`;
                  }
                  if (actualData.patient_number) {
                    response += `🆔 **Patient Number:** ${actualData.patient_number}\n`;
                  }
                  if (actualData.date_of_birth) {
                    response += `📅 **Date of Birth:** ${actualData.date_of_birth}\n`;
                  }
                  if (actualData.gender) {
                    response += `⚧️ **Gender:** ${actualData.gender}\n`;
                  }
                  if (actualData.phone_number) {
                    response += `📞 **Phone:** ${actualData.phone_number}\n`;
                  }
                  if (actualData.email) {
                    response += `📧 **Email:** ${actualData.email}\n`;
                  }
                  if (actualData.emergency_contact_name && actualData.emergency_contact_phone) {
                    response += `🚨 **Emergency Contact:** ${actualData.emergency_contact_name} (${actualData.emergency_contact_phone})\n`;
                  }
                  if (actualData.medical_record_number) {
                    response += `📋 **Medical Record:** ${actualData.medical_record_number}\n`;
                  }
                  response += `\n`;
                } else {
                  response += `❌ Patient not found\n`;
                  response += `💡 Try checking the patient number or use "search patients" to find patients by name.\n\n`;
                }
              } else if (toolName === 'get_staff_by_id') {
                if (actualData) {
                  response += `✅ **STAFF DETAILS**\n\n`;
                  if (actualData.first_name && actualData.last_name) {
                    response += `👤 **Name:** ${actualData.first_name} ${actualData.last_name}\n`;
                  }
                  if (actualData.employee_id) {
                    response += `🆔 **Employee ID:** ${actualData.employee_id}\n`;
                  }
                  if (actualData.position) {
                    response += `💼 **Position:** ${actualData.position}\n`;
                  }
                  if (actualData.department) {
                    response += `🏥 **Department:** ${actualData.department}\n`;
                  }
                  if (actualData.shift) {
                    response += `⏰ **Shift:** ${actualData.shift}\n`;
                  }
                  if (actualData.phone_number) {
                    response += `📞 **Phone:** ${actualData.phone_number}\n`;
                  }
                  if (actualData.email) {
                    response += `📧 **Email:** ${actualData.email}\n`;
                  }
                  response += `\n`;
                } else {
                  response += `❌ Staff member not found\n`;
                  response += `💡 Try searching for staff by name or check the employee ID.\n\n`;
                }
              } else if (toolName === 'get_department_by_id') {
                if (actualData) {
                  response += `✅ **DEPARTMENT DETAILS**\n\n`;
                  if (actualData.name) {
                    response += `🏥 **Name:** ${actualData.name}\n`;
                  }
                  if (actualData.description) {
                    response += `📝 **Description:** ${actualData.description}\n`;
                  }
                  if (actualData.head_of_department) {
                    response += `👨‍⚕️ **Head:** ${actualData.head_of_department}\n`;
                  }
                  if (actualData.location) {
                    response += `📍 **Location:** ${actualData.location}\n`;
                  }
                  if (actualData.extension) {
                    response += `📞 **Extension:** ${actualData.extension}\n`;
                  }
                  response += `\n`;
                } else {
                  response += `❌ Department not found\n`;
                  response += `💡 Try listing all departments to see available options.\n\n`;
                }
              } else if (toolName === 'get_room_by_id' || toolName === 'get_room_by_number') {
                if (actualData) {
                  response += `✅ **ROOM DETAILS**\n\n`;
                  if (actualData.room_number) {
                    response += `🚪 **Room Number:** ${actualData.room_number}\n`;
                  }
                  if (actualData.room_type) {
                    response += `🏠 **Type:** ${actualData.room_type}\n`;
                  }
                  if (actualData.department) {
                    response += `🏥 **Department:** ${actualData.department}\n`;
                  }
                  if (actualData.capacity) {
                    response += `👥 **Capacity:** ${actualData.capacity} beds\n`;
                  }
                  if (actualData.current_occupancy !== undefined) {
                    response += `📊 **Current Occupancy:** ${actualData.current_occupancy}/${actualData.capacity || 'N/A'}\n`;
                  }
                  if (actualData.status) {
                    response += `🔄 **Status:** ${actualData.status}\n`;
                  }
                  response += `\n`;
                } else {
                  response += `❌ Room not found\n`;
                  response += `💡 Try checking the room number or list available rooms.\n\n`;
                }
              } else if (toolName === 'get_appointment_by_id') {
                if (actualData) {
                  response += `✅ **APPOINTMENT DETAILS**\n\n`;
                  if (actualData.patient_name) {
                    response += `👤 **Patient:** ${actualData.patient_name}\n`;
                  }
                  if (actualData.doctor_name) {
                    response += `👨‍⚕️ **Doctor:** ${actualData.doctor_name}\n`;
                  }
                  if (actualData.appointment_date) {
                    response += `📅 **Date:** ${actualData.appointment_date}\n`;
                  }
                  if (actualData.appointment_time) {
                    response += `⏰ **Time:** ${actualData.appointment_time}\n`;
                  }
                  if (actualData.department) {
                    response += `🏥 **Department:** ${actualData.department}\n`;
                  }
                  if (actualData.reason) {
                    response += `📝 **Reason:** ${actualData.reason}\n`;
                  }
                  if (actualData.status) {
                    response += `🔄 **Status:** ${actualData.status}\n`;
                  }
                  response += `\n`;
                } else {
                  response += `❌ Appointment not found\n`;
                  response += `💡 Try listing appointments or checking the appointment ID.\n\n`;
                }
              } else if (toolName === 'get_equipment_by_id') {
                if (actualData) {
                  response += `✅ **EQUIPMENT DETAILS**\n\n`;
                  if (actualData.name) {
                    response += `🔧 **Name:** ${actualData.name}\n`;
                  }
                  if (actualData.category) {
                    response += `📂 **Category:** ${actualData.category}\n`;
                  }
                  if (actualData.serial_number) {
                    response += `🔢 **Serial Number:** ${actualData.serial_number}\n`;
                  }
                  if (actualData.location) {
                    response += `📍 **Location:** ${actualData.location}\n`;
                  }
                  if (actualData.status) {
                    response += `🔄 **Status:** ${actualData.status}\n`;
                  }
                  if (actualData.last_maintenance) {
                    response += `🔧 **Last Maintenance:** ${actualData.last_maintenance}\n`;
                  }
                  if (actualData.next_maintenance) {
                    response += `📅 **Next Maintenance:** ${actualData.next_maintenance}\n`;
                  }
                  response += `\n`;
                } else {
                  response += `❌ Equipment not found\n`;
                  response += `💡 Try listing equipment or checking the equipment ID.\n\n`;
                }
              } else if (toolName === 'get_medication_by_id') {
                if (actualData) {
                  response += `✅ **MEDICATION DETAILS**\n\n`;
                  if (actualData.name) {
                    response += `💊 **Name:** ${actualData.name}\n`;
                  }
                  if (actualData.category) {
                    response += `📂 **Category:** ${actualData.category}\n`;
                  }
                  if (actualData.dosage) {
                    response += `💉 **Dosage:** ${actualData.dosage}\n`;
                  }
                  if (actualData.description) {
                    response += `📝 **Description:** ${actualData.description}\n`;
                  }
                  if (actualData.side_effects) {
                    response += `⚠️ **Side Effects:** ${actualData.side_effects}\n`;
                  }
                  if (actualData.contraindications) {
                    response += `🚫 **Contraindications:** ${actualData.contraindications}\n`;
                  }
                  response += `\n`;
                } else {
                  response += `❌ Medication not found\n`;
                  response += `💡 Try listing medications or checking the medication ID.\n\n`;
                }
              } else if (toolName === 'get_bed_by_number') {
                // Special formatting for bed details
                response += `🛏️ **BED DETAILS**\n\n`;
                if (data.success && data.result && !data.result.error) {
                  const bedData = data.result;
                  response += `🛏️ **Bed Number:** ${bedData.bed_number || 'Unknown'}\n`;
                  if (bedData.room_number) response += `📍 **Room:** ${bedData.room_number}\n`;
                  if (bedData.bed_type) response += `🏷️ **Type:** ${bedData.bed_type}\n`;
                  if (bedData.status) {
                    const statusIcon = bedData.status === 'available' ? '✅' : bedData.status === 'occupied' ? '🔴' : '⚠️';
                    response += `${statusIcon} **Status:** ${bedData.status.toUpperCase()}\n`;
                  }
                  if (bedData.patient_id) {
                    response += `👤 **Current Patient:** ${bedData.patient_id}\n`;
                  } else {
                    response += `👤 **Current Patient:** None (Available)\n`;
                  }
                  if (bedData.admission_date) response += `📅 **Admission Date:** ${bedData.admission_date}\n`;
                  if (bedData.notes) response += `📝 **Notes:** ${bedData.notes}\n`;
                  
                  response += `\n**Available Actions:**\n`;
                  if (bedData.status === 'available') {
                    response += `• Assign to patient: "Assign bed ${bedData.bed_number} to patient [name]"\n`;
                  } else if (bedData.status === 'occupied') {
                    response += `• Discharge patient: "Discharge bed ${bedData.bed_number}"\n`;
                  }
                  response += `• Update status: "Update bed ${bedData.bed_number} status to [status]"\n`;
                } else {
                  const errorMsg = data.result?.error || data.message || 'Bed not found';
                  response += `❌ ${errorMsg}\n`;
                  response += `\n💡 Please check the bed number and try again. Use "list beds" to see all available beds.\n`;
                }
                response += `\n`;
              } else if (toolName === 'get_bed_status_with_time_remaining') {
                // Special formatting for bed status
                response += `🏥 **BED CLEANING STATUS**\n\n`;
                if (data.success) {
                  const bedData = data.result || data;
                  response += `🛏️ **Bed:** ${bedData.bed_number || 'Unknown'}\n`;
                  response += `📍 **Room:** ${bedData.room_number || 'Unknown'}\n`;
                  response += `📊 **Current Status:** ${bedData.current_status || 'Unknown'}\n`;
                  
                  const processStatus = bedData.process_status || 'none';
                  const timeRemaining = bedData.time_remaining_minutes || 0;
                  const progress = bedData.progress_percentage || 0;
                  
                  if (processStatus === 'cleaning') {
                    response += `🧽 **Process:** CLEANING IN PROGRESS\n`;
                    response += `⏱️ **Time Remaining:** ${timeRemaining} minutes\n`;
                    response += `📈 **Progress:** ${progress.toFixed(1)}%\n`;
                    response += `\n💡 The bed is currently being cleaned and will be ready in ${timeRemaining} minutes.\n`;
                  } else if (processStatus === 'initiated') {
                    response += `🚀 **Process:** CLEANING INITIATED\n`;
                    response += `⏱️ **Estimated Duration:** ${timeRemaining} minutes\n`;
                    response += `📈 **Progress:** ${progress.toFixed(1)}%\n`;
                    response += `\n💡 Cleaning process has been started and will begin shortly.\n`;
                  } else if (processStatus === 'none') {
                    response += `✅ **Process:** READY FOR USE\n`;
                    response += `⏱️ **Wait Time:** 0 minutes\n`;
                    response += `📈 **Status:** 100% Ready\n`;
                    response += `\n💡 The bed is clean and available for immediate use.\n`;
                  } else {
                    response += `🔄 **Process:** ${processStatus.toUpperCase()}\n`;
                    response += `⏱️ **Time Remaining:** ${timeRemaining} minutes\n`;
                    response += `📈 **Progress:** ${progress.toFixed(1)}%\n`;
                  }
                } else {
                  response += `❌ ${data.message || 'Unable to retrieve bed status'}\n`;
                }
                response += `\n`;
              } else {
                // For other single object results, try to extract meaningful data first
                const dataToShow = actualData || data;
                
                // Check if this might be a failed list/search operation that returned single object instead of array
                if (toolName.startsWith('list_') || toolName.startsWith('search_')) {
                  console.log(`🔍 Debug: ${toolName} returned single object instead of array:`, dataToShow);
                  // Try to extract array data from various possible structures
                  let arrayData = null;
                  if (dataToShow && dataToShow.data && Array.isArray(dataToShow.data)) {
                    arrayData = dataToShow.data;
                  } else if (dataToShow && dataToShow.result && Array.isArray(dataToShow.result)) {
                    arrayData = dataToShow.result;
                  } else if (Array.isArray(dataToShow)) {
                    arrayData = dataToShow;
                  }
                  
                  if (arrayData && arrayData.length > 0) {
                    response += `✅ **${toolName.replace('_', ' ').toUpperCase()}**\n\n`;
                    response += `Found ${arrayData.length} record(s):\n\n`;
                    
                    arrayData.forEach((item, index) => {
                      response += `**${index + 1}.** `;
                      
                      // Format based on tool type
                      if (toolName === 'search_patients' || toolName === 'list_patients') {
                        if (item.first_name && item.last_name) {
                          response += `${item.first_name} ${item.last_name}`;
                          if (item.patient_number) response += ` (${item.patient_number})`;
                        }
                      } else if (toolName === 'search_staff' || toolName === 'list_staff') {
                        if (item.first_name && item.last_name) {
                          response += `${item.first_name} ${item.last_name}`;
                          if (item.position) response += ` - ${item.position}`;
                        }
                      } else {
                        // Generic formatting
                        if (item.name) {
                          response += `${item.name}`;
                        } else if (item.first_name && item.last_name) {
                          response += `${item.first_name} ${item.last_name}`;
                        } else {
                          response += `${Object.keys(item)[0]}: ${Object.values(item)[0]}`;
                        }
                      }
                      response += "\n";
                    });
                    response += "\n";
                  } else {
                    response += `✅ **${toolName.replace('_', ' ').toUpperCase()}**: No records found\n\n`;
                  }
                } else {
                  response += `✅ **${toolName.replace('_', ' ').toUpperCase()}**: ${JSON.stringify(dataToShow, null, 2)}\n\n`;
                }
              }
            }
          } catch (error) {
            console.log(`🔍 Debug: Error formatting ${toolName}:`, error);
            console.log(`🔍 Debug: Original data structure:`, data);
            response += `✅ **${toolName.replace('_', ' ').toUpperCase()}**: ${typeof data === 'string' ? data : JSON.stringify(data)}\n\n`;
          }
        } else {
          response += `✅ **${toolName.replace('_', ' ').toUpperCase()}**: Operation completed successfully\n\n`;
        }
      }
    });

    return response.trim();
  }

  /**
   * Check if the message contains structured data (field: value format)
   */
  containsStructuredData(message) {
    // Look for patterns like "Field Name: Value" or "Required" or "Optional" sections
    const structuredPatterns = [
      /required/i,
      /optional/i,
      /\w+\s*:\s*\w+/,
      /bed\s+number\s*:/i,
      /room\s+id\s*:/i,
      /patient\s+number\s*:/i,
      /first\s+name\s*:/i,
      /last\s+name\s*:/i,
      /date\s+of\s+birth\s*:/i,
      /employee\s+id\s*:/i,
      /department\s*:/i
    ];
    
    return structuredPatterns.some(pattern => pattern.test(message));
  }

  /**
   * Parse structured input to determine the appropriate tool and parameters
   */
  parseStructuredInput(message) {
    const lines = message.split('\n').map(line => line.trim()).filter(line => line);
    const params = {};
    let operationType = null;
    
    // Extract field-value pairs
    for (const line of lines) {
      const colonMatch = line.match(/^([^:]+):\s*(.+)$/);
      if (colonMatch) {
        const field = colonMatch[1].trim().toLowerCase().replace(/\s+/g, '_');
        const value = colonMatch[2].trim();
        
        // Map common field names to parameter names
        const fieldMappings = {
          'bed_number': 'bed_number',
          'room_id': 'room_id',
          'bed_type': 'bed_type',
          'status': 'status',
          'first_name': 'first_name',
          'last_name': 'last_name',
          'date_of_birth': 'date_of_birth',
          'gender': 'gender',
          'phone': 'phone',
          'email': 'email',
          'address': 'address',
          'patient_number': 'patient_number',
          'employee_id': 'employee_id',
          'department_id': 'department_id',
          'department': 'department_id',
          'position': 'position',
          'name': 'name',
          'room_number': 'room_number',
          'doctor_id': 'doctor_id',
          'patient_id': 'patient_id',
          'username': 'username',
          'role': 'role',
          'password': 'password_hash',
          'equipment_id': 'equipment_id',
          'category_id': 'category_id',
          'item_code': 'item_code',
          'unit_of_measure': 'unit_of_measure'
        };
        
        const mappedField = fieldMappings[field] || field;
        params[mappedField] = value;
      }
    }
    
    // Determine operation type based on provided fields
    if (params.bed_number && params.room_id) {
      operationType = 'create_bed';
    } else if (params.username && params.email && params.role && params.first_name && params.last_name) {
      operationType = 'create_user';
      // Generate password hash if not provided (using a simple default)
      if (!params.password_hash) {
        params.password_hash = 'temp_password_hash'; // This should be handled properly in production
      }
    } else if (params.first_name && params.last_name && params.date_of_birth) {
      operationType = 'create_patient';
      // Generate patient number if not provided
      if (!params.patient_number) {
        params.patient_number = `PAT${String(Math.floor(Math.random() * 9000) + 1000)}`;
      }
    } else if (params.employee_id && params.department_id && params.position) {
      operationType = 'create_staff';
    } else if (params.name && !params.bed_number && !params.first_name && !params.username) {
      operationType = 'create_department';
    } else if (params.room_number && params.department_id) {
      operationType = 'create_room';
    } else if (params.equipment_id && params.name && params.category_id) {
      operationType = 'create_equipment';
    } else if (params.item_code && params.name && params.category_id && params.unit_of_measure) {
      operationType = 'create_supply';
    }
    
    if (operationType && Object.keys(params).length > 0) {
      console.log(`🎯 Detected structured input for: ${operationType}`, params);
      return { name: operationType, arguments: params };
    }
    
    return null;
  }

  /**
   * Extract patient parameters from natural language input
   */
  extractPatientParameters(message) {
    const params = {};
    const text = message.toLowerCase();
    
    // Extract names (look for "patient [first] [last]" or "[first] [last]")
    const namePatterns = [
      /patient\s+([a-zA-Z]+)\s+([a-zA-Z]+)/,
      /create\s+patient\s+([a-zA-Z]+)\s+([a-zA-Z]+)/,
      /add\s+patient\s+([a-zA-Z]+)\s+([a-zA-Z]+)/,
      /([a-zA-Z]+)\s+([a-zA-Z]+)/
    ];
    
    for (const pattern of namePatterns) {
      const match = message.match(pattern);
      if (match) {
        params.first_name = match[1];
        params.last_name = match[2];
        break;
      }
    }
    
    // Extract date of birth (YYYY-MM-DD format)
    const dobMatch = message.match(/(\d{4}-\d{2}-\d{2})/);
    if (dobMatch) {
      params.date_of_birth = dobMatch[1];
    } else {
      // Try alternative date formats
      const dobMatch2 = message.match(/born\s+(\d{4}-\d{2}-\d{2})/);
      if (dobMatch2) {
        params.date_of_birth = dobMatch2[1];
      }
    }
    
    // Extract gender
    if (text.includes('male') && !text.includes('female')) {
      params.gender = 'Male';
    } else if (text.includes('female')) {
      params.gender = 'Female';
    }
    
    // Extract phone (various formats)
    const phoneMatch = message.match(/(\(\d{3}\)\s*\d{3}-\d{4}|\d{3}-\d{3}-\d{4}|\+?\d{10,})/);
    if (phoneMatch) {
      params.phone = phoneMatch[1];
    }
    
    // Extract email
    const emailMatch = message.match(/([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})/);
    if (emailMatch) {
      params.email = emailMatch[1];
    }
    
    // Extract address (look for "address" keyword followed by text)
    const addressMatch = message.match(/address[:\s]+([^,]+(?:,\s*[^,]+)*)/i);
    if (addressMatch) {
      params.address = addressMatch[1].trim();
    }
    
    return params;
  }

  /**
   * Extract staff parameters from natural language input
   */
  extractStaffParameters(message) {
    const params = {};
    
    // Extract employee ID
    const empIdMatch = message.match(/emp(\d+)|employee\s+(\w+)|id\s+(\w+)/i);
    if (empIdMatch) {
      params.employee_id = empIdMatch[1] || empIdMatch[2] || empIdMatch[3];
    }
    
    // Extract department
    const deptMatch = message.match(/in\s+(\w+)|department\s+(\w+)/i);
    if (deptMatch) {
      params.department_id = deptMatch[1] || deptMatch[2];
    }
    
    // Extract position
    const positionMatch = message.match(/as\s+(\w+)|position\s+(\w+)/i);
    if (positionMatch) {
      params.position = positionMatch[1] || positionMatch[2];
    }
    
    return params;
  }

  /**
   * Extract department parameters from natural language input
   */
  extractDepartmentParameters(message) {
    const params = {};
    
    // Extract department name
    const nameMatch = message.match(/department\s+([a-zA-Z\s]+)/i);
    if (nameMatch) {
      params.name = nameMatch[1].trim();
    } else {
      const createMatch = message.match(/create\s+([a-zA-Z\s]+)\s+department/i);
      if (createMatch) {
        params.name = createMatch[1].trim();
      }
    }
    
    // Extract floor number
    const floorMatch = message.match(/floor\s+(\d+)/i);
    if (floorMatch) {
      params.floor_number = parseInt(floorMatch[1]);
    }
    
    return params;
  }

  /**
   * Extract meeting parameters from natural language input
   */
  extractMeetingParameters(message) {
    const params = {};
    
    // Normalize common time formats like "10.30pm" → "10:30 pm"
    const preNormalized = message.replace(/\b(\d{1,2})\.(\d{2})\s*([ap]m)\b/gi, (_m, h, mm, ap) => `${h}:${mm} ${ap}`);
    
    // Prefer an explicitly quoted title anywhere in the message
    const quoted = preNormalized.match(/["“”']([^"“”']+)["“”']/);
    if (quoted && quoted[1]) {
      params.purpose = quoted[1].trim();
    }
    
    // Extract meeting topic/purpose
    const topicPatterns = [
      /meeting\s+about\s+([^,\n]+)/i,
      /discuss\s+([^,\n]+)/i,
      /regarding\s+([^,\n]+)/i,
      /concerning\s+([^,\n]+)/i,
      /for\s+([^,\n]+)\s+meeting/i
    ];
    
    for (const pattern of topicPatterns) {
      const match = preNormalized.match(pattern);
      if (match) {
        if (!params.purpose) {
          params.purpose = match[1].trim();
        }
        break;
      }
    }
    
    // Extract participants
    const participantPatterns = [
      /between\s+([^,\n]+)\s+and\s+([^,\n]+)/i,
      /with\s+([^,\n]+)/i,
      /participants?\s*:?\s*([^,\n]+)/i
    ];
    
    for (const pattern of participantPatterns) {
      const match = preNormalized.match(pattern);
      if (match) {
        if (match[2]) {
          // "between X and Y" pattern
          params.participants = [match[1].trim(), match[2].trim()];
        } else {
          // Single participant or list
          params.participants = match[1].split(/\s+and\s+|\s*,\s*/).map(p => p.trim());
        }
        break;
      }
    }
    
    // Detect "all staff" / "all staffs" intent
    if (/\ball\s+staffs?\b/i.test(preNormalized)) {
      params.participants_scope = 'all_hospital_staff';
    }
    
    // Extract date
    const datePatterns = [
      /(\d{4}-\d{2}-\d{2})/,
      /tomorrow/i,
      /today/i,
      /next\s+(\w+)/i,
      /on\s+(\w+)/i
    ];
    
    for (const pattern of datePatterns) {
      const match = preNormalized.match(pattern);
      if (match) {
        if (match[0].toLowerCase() === 'tomorrow') {
          const tomorrow = new Date();
          tomorrow.setDate(tomorrow.getDate() + 1);
          params.date = tomorrow.toISOString().split('T')[0];
        } else if (match[0].toLowerCase() === 'today') {
          params.date = new Date().toISOString().split('T')[0];
        } else if (match[1] && pattern.toString().includes('next')) {
          // Handle "next Monday", etc. - simplified for now
          params.date_description = match[0];
        } else {
          params.date = match[1] || match[0];
        }
        break;
      }
    }
    
    // Extract time
    const timePatterns = [
      /at\s+(\d{1,2}:\d{2}(?:\s*[ap]m)?)/i,
      /(\d{1,2}:\d{2})/,
      /at\s+(\d{1,2})\s*([ap]m)/i,
      /(\d{1,2})\.(\d{2})\s*([ap]m)/i
    ];
    
    for (const pattern of timePatterns) {
      const match = preNormalized.match(pattern);
      if (match) {
        if (match.length === 4 && /[ap]m/i.test(match[3])) {
          // dot format captured
          params.time = `${match[1]}:${match[2]} ${match[3].toUpperCase()}`;
        } else if (match[2] && (match[2].toLowerCase() === 'am' || match[2].toLowerCase() === 'pm')) {
          params.time = `${match[1]} ${match[2].toUpperCase()}`;
        } else {
          params.time = match[1];
        }
        break;
      }
    }
    
    // Extract duration
    const durationPatterns = [
      /for\s+(\d+)\s*minutes?/i,
      /(\d+)\s*minutes?/i,
      /for\s+(\d+)\s*hours?/i,
      /(\d+)\s*hours?/i
    ];
    
    for (const pattern of durationPatterns) {
      const match = message.match(pattern);
      if (match) {
        const value = parseInt(match[1]);
        if (pattern.toString().includes('hour')) {
          params.duration_minutes = value * 60;
        } else {
          params.duration_minutes = value;
        }
        break;
      }
    }
    
    return params;
  }

  /**
   * Build a precise schedule_meeting query using extracted params
   */
  buildMeetingQuery(userMessage, params) {
    const title = params.purpose ? params.purpose : 'Meeting';
    const dateStr = params.date ? params.date : (userMessage.toLowerCase().includes('today') ? new Date().toISOString().split('T')[0] : undefined);
    let timeStr = params.time || '';
    if (timeStr && /am|pm/i.test(timeStr) && !/:/.test(timeStr)) {
      timeStr = timeStr.replace(/\b(\d{1,2})\s*([ap]m)\b/i, (_m, h, ap) => `${h}:00 ${ap.toUpperCase()}`);
    }
    if (timeStr && /\b([ap]m)\b/i.test(timeStr)) {
      timeStr = timeStr.replace(/\b([ap]m)\b/i, s => s.toUpperCase());
    }
    const durationStr = params.duration_minutes ? `${params.duration_minutes} minutes` : undefined;
    let participantPhrase = '';
    if (params.participants_scope === 'all_hospital_staff') {
      participantPhrase = 'with all hospital staff';
    } else if (Array.isArray(params.participants) && params.participants.length > 0) {
      participantPhrase = `with ${params.participants.join(' and ')}`;
    }
    const parts = [];
    // Multiple title cues to maximize backend extraction reliability
    parts.push(`Subject: "${title}"`);
    parts.push(`Exact Title: "${title}"`);
    parts.push(`Schedule "${title}" meeting`);
    parts.push(`Title: "${title}"`);
    parts.push(`Topic: "${title}"`);
    if (participantPhrase) parts.push(participantPhrase);
    if (dateStr) parts.push(`on ${dateStr}`);
    if (timeStr) parts.push(`at ${timeStr}`);
    if (durationStr) parts.push(`for ${durationStr}`);
    return parts.join(' ');
  }

  /**
   * Extract bed parameters from natural language input
   */
  extractBedParameters(message) {
    const params = {};
    
    // Extract bed number
    const bedMatch = message.match(/bed\s+(\w+)/i);
    if (bedMatch) {
      params.bed_number = bedMatch[1];
    }
    
    // Extract room ID
    const roomMatch = message.match(/room\s+(\w+)|in\s+(\w+)/i);
    if (roomMatch) {
      params.room_id = roomMatch[1] || roomMatch[2];
    }
    
    return params;
  }

  /**
   * Extract patient search parameters from natural language input
   */
  extractPatientSearchParameters(message) {
    const params = {};
    
    // Enhanced name extraction for voice input
    let nameFound = false;
    
    // Pattern 1: "find [FirstName] [LastName]"
    const findMatch = message.match(/find\s+([a-zA-Z]+)(?:\s+([a-zA-Z]+))?/i);
    if (findMatch) {
      params.first_name = findMatch[1];
      if (findMatch[2]) {
        params.last_name = findMatch[2];
      }
      nameFound = true;
    }
    
    // Pattern 2: "patient named [FirstName] [LastName]" or "patient called [FirstName] [LastName]"
    const namedMatch = message.match(/patient\s+(?:named|called)\s+([a-zA-Z]+)(?:\s+([a-zA-Z]+))?/i);
    if (!nameFound && namedMatch) {
      params.first_name = namedMatch[1];
      if (namedMatch[2]) {
        params.last_name = namedMatch[2];
      }
      nameFound = true;
    }
    
    // Pattern 3: "looking for [FirstName] [LastName]" or "show me [FirstName] [LastName]"
    const lookingMatch = message.match(/(?:looking for|show me)\s+([a-zA-Z]+)(?:\s+([a-zA-Z]+))?/i);
    if (!nameFound && lookingMatch) {
      params.first_name = lookingMatch[1];
      if (lookingMatch[2]) {
        params.last_name = lookingMatch[2];
      }
      nameFound = true;
    }
    
    // Pattern 4: Direct name patterns (for voice input like "Mohamed Nazif" or "Nazif")
    const directNameMatch = message.match(/\b(mohamed|mohammed|ahmad|ahmed|hassan|ali|omar|nazif|nasif|khalid|saeed|abdullah)\s+([a-zA-Z]+)\b/i);
    if (!nameFound && directNameMatch) {
      params.first_name = directNameMatch[1];
      params.last_name = directNameMatch[2];
      nameFound = true;
    }
    
    // Pattern 5: Single name (could be first or last name)
    const singleNameMatch = message.match(/\b(nazif|nasif|mohammed|mohamed|ahmed|hassan|ali|omar|khalid|saeed|abdullah)\b/i);
    if (!nameFound && singleNameMatch) {
      // Use the name as a general search term
      params.patient_name = singleNameMatch[1];
      nameFound = true;
    }
    
    // Extract patient number
    const patientNumMatch = message.match(/patient\s+(\w+)/i);
    if (patientNumMatch && !nameFound) {
      params.patient_number = patientNumMatch[1];
    }
    
    return params;
  }

  /**
   * Extract staff search parameters from natural language input
   */
  extractStaffSearchParameters(message) {
    const params = {};
    
    // Enhanced name extraction for voice input
    let nameFound = false;
    
    // Pattern 1: "find doctor [FirstName] [LastName]" or "find staff [FirstName] [LastName]"
    const findMatch = message.match(/find\s+(?:doctor|staff|dr\.?)\s+([a-zA-Z]+)(?:\s+([a-zA-Z]+))?/i);
    if (findMatch) {
      params.first_name = findMatch[1];
      if (findMatch[2]) {
        params.last_name = findMatch[2];
      }
      nameFound = true;
    }
    
    // Pattern 2: "doctor named [FirstName] [LastName]" or "staff named [FirstName] [LastName]"
    const namedMatch = message.match(/(?:doctor|staff|dr\.?)\s+(?:named|called)\s+([a-zA-Z]+)(?:\s+([a-zA-Z]+))?/i);
    if (!nameFound && namedMatch) {
      params.first_name = namedMatch[1];
      if (namedMatch[2]) {
        params.last_name = namedMatch[2];
      }
      nameFound = true;
    }
    
    // Pattern 3: "looking for doctor [FirstName] [LastName]"
    const lookingMatch = message.match(/(?:looking for|show me)\s+(?:doctor|staff|dr\.?)\s+([a-zA-Z]+)(?:\s+([a-zA-Z]+))?/i);
    if (!nameFound && lookingMatch) {
      params.first_name = lookingMatch[1];
      if (lookingMatch[2]) {
        params.last_name = lookingMatch[2];
      }
      nameFound = true;
    }
    
    // Pattern 4: Direct name patterns with doctor prefix
    const directNameMatch = message.match(/\b(?:doctor|dr\.?)\s+(mohamed|mohammed|ahmad|ahmed|hassan|ali|omar|nazif|nasif|khalid|saeed|abdullah)\s+([a-zA-Z]+)\b/i);
    if (!nameFound && directNameMatch) {
      params.first_name = directNameMatch[1];
      params.last_name = directNameMatch[2];
      nameFound = true;
    }
    
    // If we found names, combine them for fuzzy matching
    if (params.first_name && params.last_name) {
      params.staff_name = `${params.first_name} ${params.last_name}`;
    } else if (params.first_name) {
      params.staff_name = params.first_name;
    }
    
    return params;
  }

  /**
   * Extract department search parameters from natural language input
   */
  extractDepartmentSearchParameters(message) {
    const params = {};
    
    // Pattern 1: "find department [Name]"
    const findMatch = message.match(/find\s+department\s+([a-zA-Z\s]+)/i);
    if (findMatch) {
      params.department_name = findMatch[1].trim();
    }
    
    // Pattern 2: "department named [Name]" or "department called [Name]"
    const namedMatch = message.match(/department\s+(?:named|called)\s+([a-zA-Z\s]+)/i);
    if (!params.department_name && namedMatch) {
      params.department_name = namedMatch[1].trim();
    }
    
    // Pattern 3: "looking for department [Name]"
    const lookingMatch = message.match(/(?:looking for|show me)\s+department\s+([a-zA-Z\s]+)/i);
    if (!params.department_name && lookingMatch) {
      params.department_name = lookingMatch[1].trim();
    }
    
    // Pattern 4: Direct department name patterns (common voice variations)
    const directMatch = message.match(/\b(cardiology|cardio|emergency|er|surgery|orthopedic|pediatric|neurology|radiology|pharmacy|laboratory|lab)\b/i);
    if (!params.department_name && directMatch) {
      // Map common voice variations to full names
      const departmentMap = {
        'cardio': 'Cardiology',
        'er': 'Emergency',
        'lab': 'Laboratory'
      };
      params.department_name = departmentMap[directMatch[1].toLowerCase()] || directMatch[1];
    }
    
    return params;
  }

  /**
   * Extract equipment parameters from natural language input
   */
  extractEquipmentParameters(message) {
    const params = {};
    
    // Extract equipment ID
    const equipIdMatch = message.match(/equipment\s+(\w+)|eq(\d+)/i);
    if (equipIdMatch) {
      params.equipment_id = equipIdMatch[1] || `EQ${equipIdMatch[2]}`;
    }
    
    // Extract equipment name
    const nameMatch = message.match(/equipment\s+\w+\s+([a-zA-Z\s]+)/i);
    if (nameMatch) {
      params.name = nameMatch[1].trim();
    }
    
    // Extract category (basic mapping)
    if (message.toLowerCase().includes('mri') || message.toLowerCase().includes('scanner')) {
      params.category_id = 'radiology';
    } else if (message.toLowerCase().includes('monitor') || message.toLowerCase().includes('ventilator')) {
      params.category_id = 'medical';
    }
    
    return params;
  }

  /**
   * Extract supply parameters from natural language input
   */
  extractSupplyParameters(message) {
    const params = {};
    
    // Extract item code
    const itemMatch = message.match(/supply\s+(\w+)|sup(\d+)/i);
    if (itemMatch) {
      params.item_code = itemMatch[1] || `SUP${itemMatch[2]}`;
    }
    
    // Extract supply name
    const nameMatch = message.match(/supply\s+\w+\s+([a-zA-Z\s]+)/i);
    if (nameMatch) {
      params.name = nameMatch[1].trim();
    }
    
    // Basic unit mapping
    if (message.toLowerCase().includes('bandage') || message.toLowerCase().includes('syringe')) {
      params.unit_of_measure = 'piece';
      params.category_id = 'medical';
    }
    
    return params;
  }

  /**
   * Extract room parameters from natural language input
   */
  extractRoomParameters(message) {
    const params = {};
    
    // Extract room number
    const roomMatch = message.match(/room\s+(\w+)/i);
    if (roomMatch) {
      params.room_number = roomMatch[1];
    }
    
    // Extract department
    const deptMatch = message.match(/in\s+(\w+)|department\s+(\w+)/i);
    if (deptMatch) {
      params.department_id = deptMatch[1] || deptMatch[2];
    }
    
    return params;
  }

  /**
   * Extract user parameters from natural language input
   */
  extractUserParameters(message) {
    const params = {};
    
    // Extract username
    const userMatch = message.match(/user\s+(\w+)/i);
    if (userMatch) {
      params.username = userMatch[1];
    }
    
    // Extract email
    const emailMatch = message.match(/([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})/);
    if (emailMatch) {
      params.email = emailMatch[1];
    }
    
    // Extract role
    const roleMatch = message.match(/role\s+(\w+)|as\s+(\w+)/i);
    if (roleMatch) {
      params.role = roleMatch[1] || roleMatch[2];
    }
    
    // Extract names
    const nameMatch = message.match(/(\w+)\s+(\w+)(?:\s|$)/);
    if (nameMatch) {
      params.first_name = nameMatch[1];
      params.last_name = nameMatch[2];
    }
    
    return params;
  }

  /**
   * Extract ID from message for various entity types
   */
  extractId(message, entityType) {
    // Handle array input (for multiple entity types)
    if (Array.isArray(entityType)) {
      for (const type of entityType) {
        const result = this.extractId(message, type);
        if (result) return result;
      }
      return null;
    }
    
    const patterns = {
      'patient': [/patient\s+([A-Z0-9]+)/i, /pat([0-9]+)/i],
      'staff': [/staff\s+([A-Z0-9]+)/i, /emp([0-9]+)/i],
      'user': [/user\s+([A-Z0-9-]+)/i],
      'department': [/department\s+([A-Z0-9]+)/i, /dept\s+([A-Z0-9]+)/i],
      'doctor': [/doctor\s+([A-Z0-9]+)/i, /dr\s+([A-Z0-9]+)/i],
      'equipment': [/equipment\s+([A-Z0-9]+)/i, /eq([0-9]+)/i],
      'bed': [/bed\s+([A-Z0-9]+)/i, /bed\s+([0-9]+)/i],
      'supply': [/supply\s+([A-Z0-9]+)/i, /sup([0-9]+)/i]
    };
    
    const entityPatterns = patterns[entityType] || [];
    for (const pattern of entityPatterns) {
      const match = message.match(pattern);
      if (match) {
        return match[1];
      }
    }
    return null;
  }

  /**
   * Extract status from message
   */
  extractStatus(message) {
    const statusKeywords = ['available', 'occupied', 'maintenance', 'active', 'inactive', 'operational', 'broken'];
    for (const status of statusKeywords) {
      if (message.toLowerCase().includes(status)) {
        return status;
      }
    }
    return null;
  }

  /**
   * Extract date from message
   */
  extractDate(message) {
    const dateMatch = message.match(/(\d{4}-\d{2}-\d{2})/);
    return dateMatch ? dateMatch[1] : null;
  }

  /**
   * Validate if a string is a valid UUID
   */
  isValidUUID(str) {
    const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
    return uuidRegex.test(str);
  }

  /**
   * Parse full name into first_name and last_name for search_patients
   */
  parsePatientNameForSearch(fullName) {
    if (!fullName || typeof fullName !== 'string') {
      return {};
    }
    
    const nameParts = fullName.trim().split(/\s+/);
    
    if (nameParts.length === 1) {
      // Single name - could be first or last name, search both
      return {
        first_name: nameParts[0],
        last_name: nameParts[0]
      };
    } else if (nameParts.length === 2) {
      // "First Last"
      return {
        first_name: nameParts[0],
        last_name: nameParts[1]
      };
    } else if (nameParts.length > 2) {
      // "First Middle Last" - use first and last
      return {
        first_name: nameParts[0],
        last_name: nameParts[nameParts.length - 1]
      };
    }
    
    return {};
  }

  /**
   * Extract bed assignment parameters
   */
  extractBedAssignmentParameters(message) {
    const params = {};
    
    // Extract bed number (like "101A") - we'll convert to UUID later
    const bedNumber = this.extractId(message, 'bed') || message.match(/bed\s+([A-Z0-9]+)/i)?.[1];
    if (bedNumber) {
      // Store as bed_number for lookup, not bed_id (which needs to be UUID)
      params.bed_number = bedNumber;
    }
    
    // Extract patient ID or name
    params.patient_id = this.extractId(message, 'patient') || message.match(/patient\s+([A-Z0-9]+)/i)?.[1];
    
    // Extract patient name if no ID provided
    if (!params.patient_id) {
      const nameMatch = message.match(/(?:patient\s+|assign\s+bed\s+[A-Z0-9]+\s+to\s+(?:patient\s+)?)([A-Za-z]+\s+[A-Za-z]+)(?:\s+(?:to|on|in|any|date)|$)/i) || 
                       message.match(/assign\s+([A-Za-z]+\s+[A-Za-z]+)\s+to\s+(?:bed|any)/i) ||
                       message.match(/patient\s+([A-Za-z]+\s+[A-Za-z]+)(?:\s+(?:to|on|in)|$)/i);
      if (nameMatch) {
        params.patient_name = nameMatch[1].trim();
      }
    }
    
    params.admission_date = this.extractDate(message);
    return params;
  }

  /**
   * Extract discharge parameters
   */
  extractDischargeParameters(message) {
    const params = {};
    
    // Extract patient identifier - prioritize patient number (P1025) over UUID
    const patientNumberMatch = message.match(/patient\s+(P[A-Z0-9]+)/i) || 
                              message.match(/(P[A-Z0-9]+)/i);
    if (patientNumberMatch) {
      params.patient_id = patientNumberMatch[1];
    } else {
      // Fallback to UUID extraction
      params.patient_id = this.extractId(message, 'patient');
    }
    
    // Extract bed number (not bed_id which is UUID)
    const bedMatch = message.match(/bed\s+([A-Z0-9]+)/i);
    if (bedMatch) {
      params.bed_number = bedMatch[1];
    }
    
    // Extract patient name if no ID provided
    if (!params.patient_id && !params.bed_number) {
      const nameMatch = message.match(/patient\s+([a-zA-Z\s]+)/i) || 
                       message.match(/([a-zA-Z\s]+)\s+patient/i) ||
                       message.match(/discharge\s+([a-zA-Z\s]+)/i);
      if (nameMatch) {
        params.patient_name = nameMatch[1].trim();
      }
    }
    
    // Note: patient_id that starts with 'P' (like P1025) will be used directly as patient_number
    // No need to set patient_name since we're using patient_number parameter
    
    // Extract discharge condition
    const conditionMatch = message.match(/condition\s*:?\s*(stable|improved|critical|deceased)/i) ||
                          message.match(/(stable|improved|critical|deceased)/i);
    if (conditionMatch) {
      params.discharge_condition = conditionMatch[1].toLowerCase();
    }
    
    // Extract discharge destination
    const destinationMatch = message.match(/destination\s*:?\s*(home|transfer|rehabilitation|nursing_home)/i) ||
                            message.match(/(home|transfer|rehabilitation|nursing_home)/i);
    if (destinationMatch) {
      params.discharge_destination = destinationMatch[1].toLowerCase();
    }
    
    return params;
  }

  /**
   * Extract staff assignment parameters
   */
  extractStaffAssignmentParameters(message) {
    const params = {};
    
    // Extract staff identifier - could be employee ID (EMP002) or UUID
    const staffMatch = message.match(/staff\s+([A-Z0-9]+)/i) || message.match(/EMP([A-Z0-9]+)/i);
    if (staffMatch) {
      params.staff_id = staffMatch[1].toUpperCase();
    } else {
      params.staff_id = this.extractId(message, 'staff');
    }
    
    // Extract patient identifier - could be name or UUID
    params.patient_id = this.extractId(message, 'patient');
    
    // Extract patient name if no ID provided
    if (!params.patient_id) {
      const nameMatch = message.match(/patient\s+([a-zA-Z\s]+)/i) || 
                       message.match(/([a-zA-Z\s]+)\s+patient/i) ||
                       message.match(/to\s+([a-zA-Z\s]+)/i) ||
                       message.match(/assign.*to\s+([a-zA-Z\s]+)/i);
      if (nameMatch) {
        params.patient_name = nameMatch[1].trim();
      }
    }
    
    return params;
  }

  /**
   * Extract equipment assignment parameters
   */
  extractEquipmentAssignmentParameters(message) {
    const params = {};
    
    // Extract equipment identifier - could be equipment ID (EQ001) or UUID
    const equipMatch = message.match(/equipment\s+([A-Z0-9]+)/i) || message.match(/EQ([A-Z0-9]+)/i);
    if (equipMatch) {
      params.equipment_id = equipMatch[1].toUpperCase();
    } else {
      params.equipment_id = this.extractId(message, 'equipment');
    }
    
    // Extract patient identifier - could be name or UUID
    params.patient_id = this.extractId(message, 'patient');
    
    // Extract equipment name if no ID provided
    if (!params.equipment_id) {
      const nameMatch = message.match(/equipment\s+([a-zA-Z\s]+)/i) || 
                       message.match(/([a-zA-Z\s]+)\s+equipment/i) ||
                       message.match(/assign.*to\s+([a-zA-Z\s]+)/i);
      if (nameMatch) {
        params.equipment_name = nameMatch[1].trim();
      }
    }
    
    // Extract patient name if no ID provided
    if (!params.patient_id) {
      const nameMatch = message.match(/patient\s+([a-zA-Z\s]+)/i) || 
                       message.match(/([a-zA-Z\s]+)\s+patient/i) ||
                       message.match(/to\s+([a-zA-Z\s]+)/i) ||
                       message.match(/assign.*to\s+([a-zA-Z\s]+)/i);
      if (nameMatch) {
        params.patient_name = nameMatch[1].trim();
      }
    }
    
    return params;
  }

  /**
   * Extract supply assignment parameters
   */
  extractSupplyAssignmentParameters(message) {
    const params = {};
    
    // Extract supply identifier - could be item code (MED001) or UUID
    const supplyMatch = message.match(/supply\s+([A-Z0-9]+)/i) || message.match(/MED([A-Z0-9]+)/i);
    if (supplyMatch) {
      params.supply_id = supplyMatch[1].toUpperCase();
    } else {
      params.supply_id = this.extractId(message, 'supply');
    }
    
    // Extract patient identifier - could be name or UUID
    params.patient_id = this.extractId(message, 'patient');
    
    // Extract supply name if no ID provided
    if (!params.supply_id) {
      const nameMatch = message.match(/supply\s+([a-zA-Z\s]+)/i) || 
                       message.match(/supplies\s+([a-zA-Z\s]+)/i) ||
                       message.match(/([a-zA-Z\s]+)\s+supply/i) ||
                       message.match(/assign.*to\s+([a-zA-Z\s]+)/i);
      if (nameMatch) {
        params.supply_name = nameMatch[1].trim();
      }
    }
    
    // Extract patient name if no ID provided
    if (!params.patient_id) {
      const nameMatch = message.match(/patient\s+([a-zA-Z\s]+)/i) || 
                       message.match(/([a-zA-Z\s]+)\s+patient/i) ||
                       message.match(/to\s+([a-zA-Z\s]+)/i) ||
                       message.match(/assign.*to\s+([a-zA-Z\s]+)/i);
      if (nameMatch) {
        params.patient_name = nameMatch[1].trim();
      }
    }
    
    return params;
  }

  /**
   * Extract discharge status parameters
   */
  extractDischargeStatusParameters(message) {
    const params = {};
    
    // Extract patient identifier
    params.patient_id = this.extractId(message, 'patient');
    
    // Extract patient name if no ID provided
    if (!params.patient_id) {
      const nameMatch = message.match(/patient\s+([a-zA-Z\s]+)/i) || 
                       message.match(/([a-zA-Z\s]+)\s+patient/i) ||
                       message.match(/status\s+of\s+([a-zA-Z\s]+)/i);
      if (nameMatch) {
        params.patient_name = nameMatch[1].trim();
      }
    }
    
    return params;
  }

  /**
   * Extract bed discharge parameters
   */
  extractBedDischargeParameters(message) {
    const params = {};
    
    // Extract bed number (not bed_id which is UUID)
    const bedMatch = message.match(/bed\s+([A-Z0-9]+)/i);
    if (bedMatch) {
      params.bed_number = bedMatch[1];
    }
    
    // Extract discharge date if provided
    const dateMatch = message.match(/date\s*:?\s*(\d{4}-\d{2}-\d{2})/i) ||
                     message.match(/(\d{4}-\d{2}-\d{2})/);
    if (dateMatch) {
      params.discharge_date = dateMatch[1];
    }
    
    return params;
  }

  /**
   * Extract bed status parameters
   */
  extractBedStatusParameters(message) {
    const params = {};
    
    // Extract bed identifier (could be bed_id UUID or bed_number like "401A")
    // First try to get from "bed" pattern
    const bedMatch = message.match(/bed\s+([A-Z0-9-]+)/i);
    if (bedMatch) {
      params.bed_id = bedMatch[1];
    } else {
      // Try other patterns for bed identification
      params.bed_id = this.extractId(message, 'bed');
    }
    
    // Extract room number if mentioned
    const roomMatch = message.match(/room\s+([A-Z0-9]+)/i);
    if (roomMatch) {
      params.room_number = roomMatch[1];
    }
    
    console.log('🔍 Extracted bed status parameters:', params);
    return params;
  }

  /**
   * Extract equipment status update parameters
   */
  extractEquipmentStatusUpdateParameters(message) {
    const params = {};
    params.equipment_id = this.extractId(message, 'equipment');
    params.status = this.extractStatus(message);
    const notesMatch = message.match(/notes?\s*:?\s*([^,.\n]+)/i);
    if (notesMatch) {
      params.notes = notesMatch[1].trim();
    }
    return params;
  }

  /**
   * Extract category parameters (for equipment/supply categories)
   */
  extractCategoryParameters(message, type) {
    const params = {};
    const categoryMatch = message.match(new RegExp(`${type}\\s+category\\s+([a-zA-Z\\s]+)`, 'i'));
    if (categoryMatch) {
      params.name = categoryMatch[1].trim();
    }
    const descMatch = message.match(/description\s*:?\s*([^,.\n]+)/i);
    if (descMatch) {
      params.description = descMatch[1].trim();
    }
    return params;
  }

  /**
   * Extract supply stock update parameters
   */
  extractSupplyStockUpdateParameters(message) {
    const params = {};
    params.supply_id = this.extractId(message, 'supply') || message.match(/supply\s+([A-Z0-9]+)/i)?.[1];
    
    const quantityMatch = message.match(/quantity\s*:?\s*([+-]?\d+)/i) || message.match(/([+-]?\d+)\s*units?/i);
    if (quantityMatch) {
      params.quantity_change = parseInt(quantityMatch[1]);
    }
    
    const typeMatch = message.match(/type\s*:?\s*(purchase|usage|adjustment|return)/i);
    if (typeMatch) {
      params.transaction_type = typeMatch[1].toLowerCase();
    }
    
    const performedByMatch = message.match(/by\s+([A-Z0-9]+)/i);
    if (performedByMatch) {
      params.performed_by = performedByMatch[1];
    }
    
    return params;
  }

  /**
   * Extract user update parameters
   */
  extractUserUpdateParameters(message) {
    const params = {};
    params.user_id = this.extractId(message, 'user');
    
    const usernameMatch = message.match(/username\s*:?\s*([a-zA-Z0-9_]+)/i);
    if (usernameMatch) {
      params.username = usernameMatch[1];
    }
    
    const emailMatch = message.match(/email\s*:?\s*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})/i);
    if (emailMatch) {
      params.email = emailMatch[1];
    }
    
    const roleMatch = message.match(/role\s*:?\s*([a-zA-Z]+)/i);
    if (roleMatch) {
      params.role = roleMatch[1];
    }
    
    const activeMatch = message.match(/(activate|deactivate|active|inactive)/i);
    if (activeMatch) {
      params.is_active = activeMatch[1].toLowerCase().includes('activ') && !activeMatch[1].toLowerCase().includes('deactiv');
    }
    
    return params;
  }

  /**
   * Extract legacy user parameters
   */
  extractLegacyUserParameters(message) {
    const params = {};
    
    const nameMatch = message.match(/name\s*:?\s*([a-zA-Z\s]+)/i);
    if (nameMatch) {
      params.name = nameMatch[1].trim();
    }
    
    const emailMatch = message.match(/email\s*:?\s*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})/i);
    if (emailMatch) {
      params.email = emailMatch[1];
    }
    
    const addressMatch = message.match(/address\s*:?\s*([^,\n]+)/i);
    if (addressMatch) {
      params.address = addressMatch[1].trim();
    }
    
    const phoneMatch = message.match(/phone\s*:?\s*([\d\s\-()]+)/i);
    if (phoneMatch) {
      params.phone = phoneMatch[1].trim();
    }
    
    return params;
  }

  /**
   * Extract log interaction parameters
   */
  extractLogParameters(message) {
    const params = {};
    
    const agentMatch = message.match(/agent[_\s]type\s*:?\s*([a-zA-Z]+)/i);
    if (agentMatch) {
      params.agent_type = agentMatch[1];
    }
    
    const queryMatch = message.match(/query\s*:?\s*([^,\n]+)/i);
    if (queryMatch) {
      params.query = queryMatch[1].trim();
    }
    
    const responseMatch = message.match(/response\s*:?\s*([^,\n]+)/i);
    if (responseMatch) {
      params.response = responseMatch[1].trim();
    }
    
    return params;
  }

  /**
   * Extract parameters for user updates
   */
  extractUpdateUserParameters(message) {
    const params = {};
    
    // Extract user ID
    const userId = this.extractId(message, 'user');
    if (userId) {
      params.user_id = userId;
    }
    
    // Extract updateable fields
    const emailMatch = message.match(/email[:\s]+([^\s,]+)/i);
    if (emailMatch) {
      params.email = emailMatch[1];
    }
    
    const phoneMatch = message.match(/phone[:\s]+([^\s,]+)/i);
    if (phoneMatch) {
      params.phone = phoneMatch[1];
    }
    
    const roleMatch = message.match(/role[:\s]+(\w+)/i);
    if (roleMatch) {
      params.role = roleMatch[1];
    }
    
    if (message.toLowerCase().includes('active')) {
      params.is_active = true;
    } else if (message.toLowerCase().includes('inactive')) {
      params.is_active = false;
    }
    
    return params;
  }

  /**
   * Extract equipment status parameters
   */
  extractEquipmentStatusParameters(message) {
    const params = {};
    
    const equipId = this.extractId(message, 'equipment');
    if (equipId) {
      params.equipment_id = equipId;
    }
    
    if (message.toLowerCase().includes('operational')) {
      params.status = 'operational';
    } else if (message.toLowerCase().includes('maintenance')) {
      params.status = 'maintenance';
    } else if (message.toLowerCase().includes('broken') || message.toLowerCase().includes('out of order')) {
      params.status = 'broken';
    }
    
    const notesMatch = message.match(/notes?[:\s]+([^,]+)/i);
    if (notesMatch) {
      params.notes = notesMatch[1].trim();
    }
    
    return params;
  }

  /**
   * Extract supply stock update parameters
   */
  extractSupplyStockParameters(message) {
    const params = {};
    
    const supplyId = this.extractId(message, 'supply');
    if (supplyId) {
      params.supply_id = supplyId;
    }
    
    const quantityMatch = message.match(/(\+?-?\d+)\s*(?:units?|pieces?|items?)?/i);
    if (quantityMatch) {
      params.quantity_change = parseInt(quantityMatch[1]);
    }
    
    if (message.toLowerCase().includes('add') || message.toLowerCase().includes('restock')) {
      params.transaction_type = 'restock';
    } else if (message.toLowerCase().includes('use') || message.toLowerCase().includes('consume')) {
      params.transaction_type = 'usage';
    } else if (message.toLowerCase().includes('adjust')) {
      params.transaction_type = 'adjustment';
    }
    
    const performedByMatch = message.match(/by[:\s]+(\w+)/i);
    if (performedByMatch) {
      params.performed_by = performedByMatch[1];
    }
    
    return params;
  }

  /**
   * Add message to conversation history with memory management
   */
  addToConversationHistory(role, content, tool_calls = null, functionName = null, tool_call_id = null) {
    // Validate inputs to prevent null/undefined content
    if (!role || typeof role !== 'string') {
      console.warn('⚠️ Invalid role in addToConversationHistory:', role);
      return;
    }
    
    // Ensure content is never null/undefined
    const safeContent = content !== null && content !== undefined ? content : '';
    
    const message = { role, content: safeContent };
    
    if (tool_calls) {
      message.tool_calls = tool_calls;
    }
    
    if (functionName) {
      message.name = functionName;
    }

    if (tool_call_id) {
      message.tool_call_id = tool_call_id;
    }
    
    // Truncate very large content to prevent token overflow
    if (typeof safeContent === 'string' && safeContent.length > 2000) {
      message.content = safeContent.substring(0, 2000) + '... [truncated]';
    }
    
    this.conversationHistory.push(message);
    
    // Advanced conversation memory management that preserves tool call/response pairs
    if (this.conversationHistory.length > this.maxHistoryLength) {
      this.trimConversationHistory();
    }
  }

  /**
   * Trim conversation history while preserving tool call/response integrity
   */
  trimConversationHistory() {
    const systemMessages = this.conversationHistory.filter(msg => msg.role === 'system');
    const nonSystemMessages = this.conversationHistory.filter(msg => msg.role !== 'system');
    
    // Find complete tool call sequences (assistant with tool_calls + all tool responses)
    const completeSequences = [];
    let currentSequence = [];
    
    for (let i = 0; i < nonSystemMessages.length; i++) {
      const msg = nonSystemMessages[i];
      
      if (msg.role === 'assistant' && msg.tool_calls) {
        // Start new sequence
        if (currentSequence.length > 0) {
          completeSequences.push([...currentSequence]);
        }
        currentSequence = [msg];
      } else if (msg.role === 'tool' && currentSequence.length > 0) {
        // Add tool response to current sequence
        currentSequence.push(msg);
      } else if (msg.role === 'assistant' && !msg.tool_calls) {
        // Complete current sequence with final assistant response
        if (currentSequence.length > 0) {
          currentSequence.push(msg);
          completeSequences.push([...currentSequence]);
          currentSequence = [];
        } else {
          // Standalone assistant message
          completeSequences.push([msg]);
        }
      } else if (msg.role === 'user') {
        // Complete current sequence and start fresh
        if (currentSequence.length > 0) {
          completeSequences.push([...currentSequence]);
          currentSequence = [];
        }
        completeSequences.push([msg]);
      }
    }
    
    // Add any remaining sequence
    if (currentSequence.length > 0) {
      completeSequences.push([...currentSequence]);
    }
    
    // Keep the most recent complete sequences that fit within our limit
    const keptSequences = [];
    let messageCount = 0;
    
    for (let i = completeSequences.length - 1; i >= 0; i--) {
      const sequence = completeSequences[i];
      if (messageCount + sequence.length <= this.maxHistoryLength) {
        keptSequences.unshift(sequence);
        messageCount += sequence.length;
      } else {
        break;
      }
    }
    
    // Flatten sequences back to message list
    const keptMessages = keptSequences.flat();
    
    // Rebuild conversation history
    this.conversationHistory = [...systemMessages, ...keptMessages];
    
    console.log(`🧹 Trimmed conversation history: ${nonSystemMessages.length} -> ${keptMessages.length} messages`);
  }

  /**
   * Call OpenAI with function calling and conversation history (Claude Desktop Style) - FIXED VERSION
   */
  async callOpenAI(userMessage, functions, serverInfo = null) {
    // Add safety checks
    if (!functions || !Array.isArray(functions)) {
      console.warn('⚠️ Functions parameter is invalid:', functions);
      functions = [];
    }
    
    // Get agent information
    const availableAgents = this.getAgents();
    
    // Debug logging
    console.log('🔍 callOpenAI called with:', { 
      userMessage: userMessage?.substring(0, 50) + '...', 
      functionsCount: functions?.length,
      agentsCount: availableAgents?.length,
      hasServerInfo: !!serverInfo 
    });
    
    // Get today's date with comprehensive error handling
    const getCurrentDate = () => {
      try {
        if (typeof this.getTodayDate === 'function') {
          return this.getTodayDate();
        }
      } catch (error) {
        console.warn('❌ Error calling getTodayDate:', error);
      }
      // Always fall back to current date
      return new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' });
    };
    
    const todayDate = getCurrentDate();
    console.log('✅ Using date for system prompt:', todayDate);
    
          // Create system prompt without complex template literals - COMPLETE VERSION WITH ALL PROMPTS
      const systemPrompt = [
        "🛏️ **CRITICAL BED STATUS TOOL SELECTION OVERRIDE:**",
        "For ANY bed status queries (check bed X status, bed X status, is bed X ready, etc.), ALWAYS use 'get_bed_status_with_time_remaining' - NEVER use list_beds!",
        "**EXCEPTION: Patient discharge messages (discharge patient X, discharge patient from bed Y) should use discharge workflow tools, NOT bed status tools.**",
        "This tool shows cleaning time remaining, occupancy status, and patient assignments.",
        "Examples:",
        "- 'check bed 302A status' → use get_bed_status_with_time_remaining with bed_id: '302A'",
        "- 'bed 101 ready?' → use get_bed_status_with_time_remaining with bed_id: '101'", 
        "- 'status of bed 205B' → use get_bed_status_with_time_remaining with bed_id: '205B'",
                "- 'discharge patient P1025' → use discharge workflow tools (NOT bed status tools)",
        "",
        "🚨 **DISCHARGE WORKFLOW PRIORITY:**",
        "When a user message contains 'discharge' and 'patient', ALWAYS prioritize discharge workflow tools over bed status tools.",
        "Discharge messages should use: discharge_bed, generate_discharge_report, or discharge_patient_complete tools.",
        "",
        "📊 **LIST vs STATUS TOOLS - CRITICAL DIFFERENCE:**",
      "- list_beds = Shows ALL beds overview (use for 'show all beds', 'list beds', 'bed inventory')",
      "- get_bed_status_with_time_remaining = Shows SPECIFIC bed detail with cleaning timers (use for 'check bed X', 'bed X status')",
      "",
      "� IMPORTANT: For equipment usage, always use 'add_equipment_usage_with_codes' (prevents UUID errors)",
      "",
      "You are Hospital AI, an advanced AI assistant specialized in comprehensive hospital management.",
      "You're connected to a real hospital management system through MCP (Model Context Protocol).",
      "",
      "Today is: " + todayDate + ".",
      "",
      "🏥 **Hospital System Context:**",
      "- Server: Direct HTTP FastMCP Server with Advanced AI Systems", 
      "- Available Tools: " + (functions ? functions.length : 0) + " medical management tools",
      "- Active Agents: " + (availableAgents ? availableAgents.length : 0) + " specialized agents",
      "- Connection: Direct HTTP communication via MCP protocol",
      "",
      "🚀 **ADVANCED AI CAPABILITIES AVAILABLE:**",
      "The system includes 6 enterprise-level AI systems that you can access:",
      "1. **Master AI System (ai_master_request)**: For complex analysis, insights, and comprehensive responses",
      "2. **Predictive Analytics (run_predictive_forecast)**: Bed demand, staff requirements, supply consumption forecasts",
      "3. **Real-time Monitoring (get_ai_system_dashboard)**: Live system status and comprehensive metrics",
      "4. **Multi-language Support (translate_text)**: Patient communication in multiple languages",
      "5. **Equipment Lifecycle Management (manage_equipment_lifecycle)**: Advanced asset tracking and maintenance",
      "6. **Emergency Response (get_emergency_phrases)**: Multi-language emergency communication",
      "",
      "🔧 **WHEN TO USE ADVANCED AI TOOLS:**",
      "- Complex queries requiring analysis → ai_master_request",
      "- Predictions or forecasts → run_predictive_forecast", 
      "- System overview or dashboard → get_ai_system_dashboard",
      "- Translation needs → translate_text",
      "- Equipment maintenance → manage_equipment_lifecycle",
      "- Emergency situations → get_emergency_phrases",
      "",
      "**Specialized Agents:**",
      availableAgents && availableAgents.length > 0 ? 
        availableAgents.map(agent => 
          `- ${agent.name}: ${agent.description} (${agent.tools_count} tools)`
        ).join('\n') : 
        "- No agents information available",
      "",
      "**CRITICAL: Form-Based CREATE Operations:**",
      "The system uses a DUAL APPROACH for operations:",
      "1. **POPUP FORMS for CREATE operations:** The 9 main CREATE tools (create_patient, create_user, create_staff, create_department, create_room, create_bed, create_equipment, create_supply, create_legacy_user) are handled by POPUP FORMS",
      "2. **DIRECT TOOL CALLS for everything else:** All other operations (list, search, update, delete, assign, discharge, schedule_meeting, etc.) use direct tool calling",
      "",
      "**FORM HANDLING WORKFLOW:**",
      "- When user requests CREATE operations for the 10 main entities, a popup form will appear",
      "- **FORM SUBMISSIONS:** When user submits form data (indicated by structured data like 'Create patient: first_name=\"John\"'), IMMEDIATELY call the appropriate CREATE tool with the provided data",
      "- **CHAT REQUESTS:** For conversational CREATE requests, acknowledge that the form has been opened and guide the user to fill it out",
      "- For FOREIGN KEY fields in forms, guide users to:",
      "  * Use dropdown menus when available (Department, User, Room selections)",
      "  * Search by name/number rather than typing UUIDs",
      "  * Look up entities first if dropdowns aren't populated",
      "- For all OTHER operations (list_patients, search_patients, assign_bed_to_patient, discharge_bed, schedule_meeting, etc.), use direct tool calling",
      "",
      "**FORM SUBMISSIONS vs CHAT REQUESTS:**",
      "- **FORM SUBMISSION** (call CREATE tool immediately): Messages containing structured data like 'Create patient: first_name=\"John\", last_name=\"Doe\"' - these come from popup form submissions",
      "- **CHAT REQUEST** (show form): Conversational requests like 'create a new patient' or 'register patient John Doe' - these should trigger popup forms",
      "",
      "**NEVER call functions without required parameters. If a user requests an action but doesn't provide the necessary information:**",
      "1. Ask for the missing required information FIRST",
      "2. Only call functions after you have ALL required parameters",
      "3. For create_patient, you MUST have: first_name, last_name, date_of_birth",
      "4. For create_user, you MUST have: username, email, password_hash, role, first_name, last_name",
      "",
      "**CRITICAL: Foreign Key Resolution (Claude Desktop Style):**",
      "When users provide human-readable names instead of IDs, always resolve them first:",
      "1. For room_id: Ask 'Which room?' → User says 'Room 101' → Use search_rooms or list_rooms to find room_id",
      "2. For department_id: Ask 'Which department?' → User says 'Emergency' → Use list_departments to find department_id",
      "3. For doctor_id: Ask 'Which doctor?' → User says 'Dr. Smith' → Use list_staff to find staff member who is a doctor",
      "4. For patient_id: Ask 'Which patient?' → User says 'John Doe' → Use search_patients to find patient_id",
      "5. For category_id: Ask 'Which category?' → User says 'Medical Equipment' → Use list categories to find category_id",
      "",
      "**WORKFLOW: Always resolve foreign keys before create operations:**",
      "- If user says 'create bed in room 101' → FIRST find room_id for 'room 101', THEN create bed",
      "- If user says 'schedule meeting with Dr. Smith' → FIRST find staff_id for 'Dr. Smith', THEN create meeting",
      "- If user says 'assign bed to John Doe' → FIRST find patient_id for 'John Doe', THEN assign bed",
      "",
      "**NEVER ask users for UUIDs directly - always use human names and resolve automatically**",
      "",
      "**CRITICAL: Emergency Scenario Handling:**",
      "When users mention 'emergency patient' scenarios:",
      "1. FIRST guide user through patient creation form with provided details",
      "2. THEN check available beds with list_beds(status='available')",
      "3. If no beds are available, guide user through bed creation form - help them select room from dropdown or search rooms",
      "4. THEN assign the first truly available bed to the patient using direct tool call",
      "5. THEN list available doctors/staff with list_staff()",
      "6. THEN guide user through bed assignment - help them select available bed",
      "7. Use simple date formats like '2025-08-10 10:00' instead of '2025-08-10T10:00:00Z'",
      "8. Provide comprehensive response with next steps for bed assignment and doctor allocation",
      "",
      "**Enhanced Capabilities:**",
      "1. **Smart Parameter Collection**: Ask for missing details conversationally, one at a time",
      "2. **Multi-Tool Operations**: Automatically resolve names to IDs when needed",
      "3. **Conversation Memory**: Build upon previous exchanges",
      "4. **Contextual Responses**: Tailor responses based on conversation flow",
      "5. **Fuzzy Name Matching**: Handle voice-to-text transcription errors and similar-sounding names",
      "",
      "**INCOMPLETE REQUESTS:**",
      "- For 'create new department' → Ask: 'What should I call this department?'",
      "- Never create with placeholder names",
      "- Collect required information conversationally",
      "",
      "**FOREIGN KEY RESOLUTION:**",
      "- When users mention names instead of IDs, automatically search for matches",
      "- Explain what you're doing: 'Let me find John Doe in our patient records...'",
      "- If multiple matches found, ask for clarification",
      "",
      "**FUZZY NAME MATCHING:**",
      "- The system automatically handles similar-sounding names for all entities:",
      "  * Patients: 'Nazif' vs 'Nasif', 'Mohammed' vs 'Mohamed'",
      "  * Doctors: 'Ahmad' vs 'Ahmed', 'Hassan' vs 'Hasan'",
      "  * Staff: 'Ali' vs 'Aly', 'Omar' vs 'Umar'",
      "  * Departments: 'Cardiology' vs 'Cardio', 'Emergency' vs 'ER'",
      "- When fuzzy matching is used, inform the user: 'I found a similar name: Mohamed Nazif. Is this the patient you're looking for?'",
      "- Check tool results for '_fuzzy_match_info' to see if fuzzy matching was used",
      "- Always confirm fuzzy matches with the user before proceeding",
      "",
      "**VOICE-TO-TEXT CORRECTIONS:**",
      "- Common transcription errors for all entity types:",
      "  * Names: 'Nazif' → 'Nasif', 'Mohammed' → 'Mohamed', 'Ahmad' → 'Ahmed'",
      "  * Departments: 'Cardiology' → 'Cardio', 'Emergency' → 'ER'",
      "- When exact search fails, the system automatically tries fuzzy matching (70% similarity threshold)",
      "- Explain when corrections are made: 'I couldn't find 'Nasif' but found 'Nazif' which sounds similar'",
      "",
      "**CONVERSATION FLOW:**",
      "- Remember what the user is trying to accomplish",
      "- Build upon previous responses",
      "- Don't ask for information already provided",
      "- Confirm actions before executing",
      "",
      "**CRITICAL: Meeting Scheduling & Communication Workflow:**",
      "For meeting scheduling, always collect COMPLETE details before proceeding:",
      "",
      "1. **Meeting Information Collection - REQUIRED BEFORE SCHEDULING:**",
      "   When user requests a meeting, ALWAYS ask for missing details:",
      "   - **Purpose/Topic**: What is the purpose of this meeting?",
      "   - **Date**: What date would you like to schedule this meeting? (format: YYYY-MM-DD)",
      "   - **Time**: What time should the meeting start? (format: HH:MM, e.g., 14:30)",
      "   - **Duration**: How long should the meeting be? (e.g., 30 minutes, 1 hour)",
      "   - **Participants**: Who should attend this meeting? (specific names, departments, or roles)",
      "",
      "2. **WORKING Meeting Creation Process - Use schedule_meeting Tool:**",
      "   After collecting all details, create a SPECIFIC and DETAILED query for schedule_meeting.",
      "   Use EXACT user-provided details in the query.",
      "",
      "   **CRITICAL: Duration and Topic Handling:**",
      "   - ALWAYS include the EXACT duration as specified by user (e.g., '15 minutes', '30 minutes', '1 hour')",
      "   - ALWAYS include the SPECIFIC topic/purpose as the meeting title",
      "   - NEVER use generic titles like 'Hospital Meeting' or 'Staff Meeting'",
      "   - Duration must be extracted precisely: '15min' → '15 minutes', '1hr' → '1 hour', '30m' → '30 minutes'",
      "",
      "   **Example Usage:**",
      "   User says: 'Schedule meeting about daily improvement between shamil and nazif tomorrow at 9am for 15 minutes'",
      "   AI calls: schedule_meeting(query='Schedule Daily Improvement Meeting between Shamil and Nazif specifically on 2025-08-14 at 9:00 AM for 15 minutes to discuss daily workflow improvements and optimization strategies')",
      "   Expected Email Result:",
      "   - Subject: 'Daily Improvement Meeting - 2025-08-14'",
      "   - Topic: 'Daily Improvement Meeting'", 
      "   - Duration: '15 minutes'",
      "   - Participants: Only Shamil and Nazif (not all staff)",
      "",
      "   **Query Format Requirements:**",
      "   - Include EXACT purpose/topic in the title (NOT 'Hospital Meeting')",
      "   - Include SPECIFIC participants by name (between X and Y, with A and B, etc.)",
      "   - Include EXACT date and time as provided",
      "   - Include EXACT duration as specified (15 minutes, 30 minutes, 1 hour, etc.)",
      "   - Use descriptive meeting title that reflects the actual purpose",
      "   - When specific participants are mentioned (between A and B), only those people should receive emails",
      "",
      "   **DURATION PARSING - BE PRECISE:**",
      "   - '15min' or '15 minutes' → '15 minutes'",
      "   - '30min' or '30 minutes' → '30 minutes'", 
      "   - '1hr' or '1 hour' → '1 hour'",
      "   - '45min' or '45 minutes' → '45 minutes'",
      "   - '2hrs' or '2 hours' → '2 hours'",
      "",
      "   **DO NOT use generic titles like 'Hospital Meeting' or 'Staff Meeting'**",
      "   **DO use specific titles like 'Quarterly Review Meeting', 'Emergency Protocol Training', 'Budget Planning Session'**",
      "",
      "3. **Participant Targeting - IMPROVED PRECISION:**",
      "   **CRITICAL: Be very specific about participants in the query:**",
      "   - If user says 'Mohamed Shamil' → Use 'Schedule [TOPIC] meeting with Mohamed Shamil specifically'",
      "   - If user says 'Dr. Smith and Nurse Johnson' → Use 'Schedule [TOPIC] meeting with Dr. Smith and Nurse Johnson only'",
      "   - If user says 'Emergency Department staff' → Use 'Schedule [TOPIC] meeting with Emergency Department staff only'",
      "   - If user says 'All staff' → Use 'Schedule [TOPIC] meeting with all hospital staff'",
      "",
      "   **Example Specific Queries:**",
      "   'Schedule Monthly Operations Review meeting with Mohamed Shamil on 2025-08-17 at 4:00 PM for 1 hour'",
      "   'Schedule Emergency Protocol Training with Dr. Smith and Nurse Johnson on 2025-08-18 at 2:30 PM for 45 minutes'",
      "   'Schedule Department Meeting with Emergency Department staff only on 2025-08-19 at 10:00 AM for 2 hours'",
      "",
      "   **The more specific the query, the more targeted the invitations will be!**",
      "",
      "4. **Meeting Email Template - Handled Automatically:**",
      "   The schedule_meeting tool automatically creates professional meeting invitations with:",
      "   - Meeting purpose and agenda",
      "   - Date, time, and duration",
      "   - Google Meet link",
      "   - Participant list",
      "   - Professional formatting",
      "",
      "5. **Key Integration Points - USE WORKING TOOLS:**",
      "   - schedule_meeting = COMPLETE solution (Google Meet + Email + Database)",
      "   - list_users/list_staff = For information only",
      "   - NO separate email sending needed - schedule_meeting handles everything",
      "   - ALWAYS use schedule_meeting for meeting creation",
      "",
      "**SUCCESS WORKFLOW:**",
      "1. ✅ Ask for: Purpose, Date, Time, Duration, Participants",
      "2. ✅ Use schedule_meeting with detailed query including all information",
      "3. ✅ Confirm meeting created with Google Meet link",
      "4. ✅ Confirm participants will receive email invitations",
      "",
      "**EXAMPLE IMPROVED MEETING CREATION:**",
      "User: 'Schedule a meeting with Mohamed Shamil about monthly operations review for tomorrow at 4 PM'",
      "AI Response: 'I'll schedule that meeting for you. I have:",
      "- Purpose: Monthly operations review",
      "- Participant: Mohamed Shamil",
      "- Date: Tomorrow (2025-08-14)",
      "- Time: 4 PM",
      "How long should this meeting be?'",
      "User: '1 hour'",
      "AI calls: schedule_meeting(query='Schedule Monthly Operations Review meeting with Mohamed Shamil specifically on 2025-08-14 at 4:00 PM for 1 hour to discuss hospital operations and monthly performance')",
      "Expected Result:",
      "- ✅ Email subject: 'Monthly Operations Review - 2025-08-14'",
      "- ✅ Meeting time: 4:00 PM (as specified)",
      "- ✅ Email sent to: mrmshamil1786@gmail.com only",
      "- ✅ Google Meet link included",
      "",
      "**NEVER say you cannot send emails - schedule_meeting handles all email sending automatically!**",
      "",
      "**CRITICAL: Patient Discharge & Report Workflow:**",
      "For patient discharge and discharge reporting, use the INTEGRATED discharge tools:",
      "",
      "1. **discharge_bed Tool - Primary Discharge Action:**",
      "   - Use: discharge_bed(bed_id='bed-uuid', discharge_date='optional-iso-date')",
      "   - This discharges the patient from the bed and makes it available",
      "   - bed_id: Use UUID from list_beds or search by room/patient",
      "   - discharge_date: Optional ISO format date, defaults to current time",
      "",
      "2. **generate_discharge_report Tool - Comprehensive Report:**",
      "   - Use: generate_discharge_report(bed_id='bed-uuid', discharge_condition='stable', discharge_destination='home')",
      "   - Creates comprehensive medical discharge documentation",
      "   - discharge_condition: stable, improved, critical, etc.",
      "   - discharge_destination: home, transfer, nursing_facility, etc.",
      "",
      "3. **Discharge Workflow - Standard Process:**",
      "   - User: 'Discharge patient John Doe from Room 101'",
      "   - Step 1: Use search_patients or list_beds to find the patient's bed",
      "   - Step 2: Call discharge_bed(bed_id=found_bed_id)",
      "   - Step 3: Call generate_discharge_report(bed_id=found_bed_id, discharge_condition='stable')",
      "   - Provide confirmation with discharge details and report summary",
      "",
      "4. **ID Resolution for Discharge:**",
      "   - Patient Name → search_patients → find current bed assignment → get bed_id",
      "   - Room Number → list_beds(room_filter) → find occupied bed → get bed_id",
      "   - Bed Assignment → list_beds → match patient to bed → get bed_id",
      "",
      "**Always provide discharge summary and confirm bed is now available!**",
      "",
      "**CRITICAL: Bed Assignment Workflow:**",
      "For ANY bed assignment request (\"assign bed to patient\", \"assign bed X to patient Y\"), ALWAYS follow this 3-step process:",
      "",
      "1. **Step 1 - List Available Patients:**",
      "   - ALWAYS call list_patients first to show available patients",
      "   - This helps user identify the correct patient and patient ID",
      "",
      "2. **Step 2 - List Available Beds:**", 
      "   - ALWAYS call list_beds to show current bed availability",
      "   - This shows which beds are free and ready for assignment",
      "",
      "3. **Step 3 - Perform Assignment:**",
      "   - ONLY after both lists are available, call assign_bed_to_patient",
      "   - Use the IDs found from the previous steps",
      "",
      "**Bed Assignment Examples:**",
      "User: 'Assign bed 101B to patient John Abraham'",
      "Response sequence:",
      "- Call list_patients → Show available patients including John Abraham",
      "- Call list_beds → Show bed availability including 101B status",
      "- Call assign_bed_to_patient(bed_id=found_bed_id, patient_id=found_patient_id)",
      "",
      "User: 'I need to assign a bed to a patient'",
      "Response sequence:",
      "- Call list_patients → Show all patients for user to choose from",
      "- Call list_beds → Show available beds for user to choose from", 
      "- Wait for user to specify which patient and bed, then assign",
      "",
      "**NEVER skip the list_patients and list_beds steps for bed assignments!**",
      "",
      "📋 **Your Identity & Capabilities:**",
      "You are Hospital AI - NOT Claude. Always introduce yourself as 'Hospital AI'.",
      "You have access to a complete hospital management system with tools for:",
      "- 👥 Patient management (create, search, update patient records)",
      "- 🏢 Department operations (manage hospital departments)",
      "- 👨‍⚕️ Staff management (doctors, nurses, administrators)",
      "- 🛏️ Bed management (room assignments, occupancy)",
      "- 🏥 Equipment tracking (medical devices, maintenance)",
      "- 📦 Supply inventory (medications, consumables)",
      "-  Reporting and analytics",
      "",
      "🔧 **Function Calling Instructions:**",
      "- POPUP FORMS: DO NOT call create_patient, create_user, create_staff, create_department, create_room, create_bed, create_equipment, create_supply, or create_legacy_user directly",
      "- DIRECT TOOLS: Use all other function names exactly as provided",
      "- For form-based operations, acknowledge the form has opened and guide user to fill it",
      "- For direct tool operations, extract all provided parameters and call functions normally",
      "- CRITICAL: Always use exact parameter names as defined in schemas:",
      "  * For patients: use 'patient_number' only if provided, otherwise let it auto-generate",
      "  * For equipment: use 'equipment_id' as specified",
      "  * For search_patients: use specific field names (first_name, last_name, phone, email) NOT 'query'",
      "- For emergency scenarios, guide user through forms first, then use direct tools for bed assignment",
      "- Provide clear, helpful responses based on actual tool results",
      "- If a parameter name doesn't exist in the schema, don't use it",
      "",
      "",
      "**ALWAYS resolve human names to IDs before create operations - this is how Claude Desktop works!**",
      "",
      "**LIST TOOLS RESPONSE FORMAT:**",
      "When using any LIST tools (list_patients, list_staff, list_departments, list_beds, list_rooms, list_equipment, list_supplies, list_users, list_meetings, list_discharge_reports, list_equipment_categories, list_supply_categories, list_inventory_transactions, list_legacy_users), provide ONLY essential information:",
      "",
      "- **list_patients**: Only show patient names (first_name + last_name) and patient numbers",
      "- **list_staff**: Only show staff names (first_name + last_name) and positions",
      "- **list_departments**: Only show department names",
      "- **list_beds**: Only show bed numbers and room assignments",
      "- **list_rooms**: Only show room numbers and types",
      "- **list_equipment**: Only show equipment names and status",
      "- **list_supplies**: Only show supply names and current stock levels",
      "- **list_users**: Only show usernames and roles",
      "- **list_meetings**: Only show meeting topics and dates",
      "- **All other list tools**: Only show names/titles and key status information",
      "",
      "DO NOT show full details, IDs, or technical information unless specifically requested. This prevents '(Further details are truncated for brevity)' messages and keeps responses clean and readable.",
      "",
      "**Response Guidelines:**",
      "- Be conversational and professional",
      "- For CREATE operations (10 main entities): Acknowledge form opening and guide user to fill it out",
      "- For other operations: Process directly using appropriate tools",
      "- If user says 'Add new patient' without details, ask for patient information first",
      "- Explain what actions you're taking",
      "- Provide clear success/failure feedback",
      "- Hide technical UUIDs from users",
      "- Focus on user-friendly information",
      "- For emergency scenarios: Guide through forms first, then handle bed assignment",
      "- Remember the conversation context",
      "",
      "**IMPORTANT EXAMPLES:**",
      "User: 'Create new patient John Doe' → 'I've opened the patient admission form for you. Please fill in John's details including his date of birth, contact information, and any medical history.'",
      "User: 'Create new staff member' → 'I've opened the staff registration form. Please fill in the staff details. For the User ID, select from the dropdown of available users, and for Department ID, choose from the department dropdown.'",
      "User: 'List all patients' → Call list_patients tool directly and display results",
      "User: 'Assign bed 101 to patient John Doe' → First search for patient, then call assign_bed_to_patient tool",
      "",
      "**Equipment Usage Tool Selection:**",
      "✅ ALWAYS use 'add_equipment_usage_with_codes' for equipment usage operations",
      "- This tool automatically converts codes like P002, EQ001, EMP001 to internal UUIDs",
      "- It prevents UUID formatting errors and works with both codes and UUIDs",
      "- This is the preferred method for all equipment usage recording",
      "",
      "**Equipment Usage Examples:**",
      "✅ User: 'Record equipment usage: EQ001 used by EMP001 for patient P002'",
      "   → Use add_equipment_usage_with_codes with patient_id='P002', equipment_id='EQ001', staff_id='EMP001'",
      "",
      "✅ For ANY equipment usage request, use add_equipment_usage_with_codes",
      "   → This tool handles code-to-UUID conversion automatically",
      "",
      "� Note: The system will automatically redirect to the correct tool if needed",
      "",
      "Use the available functions to help users with hospital management tasks."
    ].join('\n');

    const messages = [{ role: 'system', content: systemPrompt }];
    
    // Validate conversation structure before adding to messages
    if (!this.validateConversationStructure()) {
      console.warn('⚠️ Invalid conversation structure detected, clearing history');
      this.clearConversationHistory();
    }
    
    // Add conversation history
    messages.push(...this.conversationHistory);
    
    // Add current user message if provided
    if (userMessage) {
      messages.push({ role: 'user', content: userMessage });
    }

    try {
      const response = await fetch('https://api.openai.com/v1/chat/completions', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${this.openaiApiKey}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          model: 'gpt-4-turbo-preview',
          messages: messages,
          tools: functions,
          tool_choice: 'auto',
          temperature: 0.7,
          max_tokens: 4000
        })
      });

      if (!response.ok) {
        const errorText = await response.text();
        console.error('OpenAI API Error Details:', errorText);
        
        if (response.status === 400) {
          if (errorText.includes('context_length_exceeded')) {
            console.warn('⚠️ Context length exceeded, clearing conversation history');
            this.clearConversationHistory();
            return this.callOpenAI(userMessage, functions);
          } else if (errorText.includes('tool_call_id')) {
            console.warn('⚠️ Broken tool call structure detected, clearing conversation history');
            this.clearConversationHistory();
            return this.callOpenAI(userMessage, functions);
          }
        }
        
        throw new Error(`OpenAI API error: ${response.status} - ${errorText}`);
      }

      const data = await response.json();
      console.log('🎯 OpenAI Response:', data.choices[0].message);
      
      return data;

    } catch (error) {
      console.error('❌ OpenAI API call failed:', error);
      
      if (error.message.includes('context_length') || 
          error.message.includes('token') || 
          error.message.includes('tool_call_id')) {
        console.warn('⚠️ Conversation structure issue detected, clearing history and retrying');
        this.clearConversationHistory();
        
        try {
          const retryMessages = [{ role: 'system', content: systemPrompt }];
          if (userMessage) {
            retryMessages.push({ role: 'user', content: userMessage });
          }
          
          const retryResponse = await fetch('https://api.openai.com/v1/chat/completions', {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${this.openaiApiKey}`,
              'Content-Type': 'application/json'
            },
            body: JSON.stringify({
              model: 'gpt-4-turbo-preview',
              messages: retryMessages,
              tools: functions,
              tool_choice: 'auto',
              temperature: 0.7,
              max_tokens: 4000
            })
          });
          
          if (retryResponse.ok) {
            const retryData = await retryResponse.json();
            console.log('✅ Retry successful:', retryData.choices[0].message);
            return retryData;
          }
        } catch (retryError) {
          console.error('❌ Retry also failed:', retryError);
        }
      }
      
      throw error;
    }
  }

  /**
   * Execute function calls from OpenAI response (Claude Desktop Style)
   */
  async executeFunctionCalls(gptResponse) {
    const results = [];
    const toolCalls = gptResponse.choices[0].message.tool_calls || [];
    let bedStatusUpdateNeeded = false;

    for (const toolCall of toolCalls) {
      let functionName = toolCall.function.name;
      const functionArgs = JSON.parse(toolCall.function.arguments);

      // 🚨 CRITICAL REDIRECT: Prevent UUID errors by redirecting problematic tool
      if (functionName === 'add_equipment_usage_simple') {
        console.warn('🚨 REDIRECTING: add_equipment_usage_simple → add_equipment_usage_with_codes (prevents UUID errors)');
        functionName = 'add_equipment_usage_with_codes';
      }

      console.log(`🔧 Executing function: ${functionName}`, functionArgs);

      try {
        // Call the actual MCP tool
        const result = await this.mcpClient.callTool(functionName, functionArgs);

        console.log(`✅ Function ${functionName} completed:`, result);

        // Try to parse the MCP return (many tools return a JSON string in result.content[0].text)
        let parsed = null;
        if (result && result.result && result.result.content && Array.isArray(result.result.content) && result.result.content[0]?.text) {
          try {
            parsed = JSON.parse(result.result.content[0].text);
            console.log(`✅ Parsed tool result for ${functionName}:`, parsed);
          } catch (parseErr) {
            console.warn(`⚠️ Could not parse tool result for ${functionName}, returning raw result`, parseErr);
            parsed = null;
          }
        }

        results.push({
          function: functionName, // Use the (possibly redirected) function name
          arguments: functionArgs,
          result: result,
          parsedResult: parsed,
          // Comes from the backend envelope, not from the HTTP status. Only a
          // true here means the action actually happened.
          executed: result?.executed === true,
          outcome: result?.outcome,
          runId: result?.runId,
          tool_call_id: toolCall.id
        });

        // 🛏️ Track if bed status update is needed
        const bedRelatedTools = [
          'discharge_bed', 'assign_bed_to_patient', 'update_bed_status',
          'create_bed_turnover', 'update_bed_turnover_status', 'auto_update_expired_cleaning_beds'
        ];
        
        if (bedRelatedTools.includes(functionName)) {
          bedStatusUpdateNeeded = true;
          console.log(`🛏️ Bed status auto-refresh triggered by: ${functionName}`);
        }

      } catch (error) {
        // A tool that was denied, or is awaiting a human, is NOT a failure —
        // and must not be reported to the user or the model as one. It also
        // must never be reported as completed.
        const notExecuted = error?.name === 'ToolNotExecutedError';

        if (notExecuted) {
          console.warn(`⛔ Function ${functionName} not executed (${error.outcome}):`, error.reason || error.message);
        } else {
          console.error(`❌ Function ${functionName} failed:`, error);
        }

        results.push({
          function: functionName,
          arguments: functionArgs,
          error: notExecuted ? error.userMessage : error.message,
          executed: false,
          outcome: notExecuted ? error.outcome : 'FAILED',
          awaitingHuman: notExecuted ? error.awaitingHuman : false,
          violations: notExecuted ? error.violations : undefined,
          runId: notExecuted ? error.runId : undefined,
          tool_call_id: toolCall.id
        });
      }
    }

    // 🔄 Auto-refresh bed statuses after bed operations
    if (bedStatusUpdateNeeded) {
      console.log('🔄 Auto-updating expired cleaning beds...');
      try {
        const autoUpdateResult = await this.mcpClient.callTool('auto_update_expired_cleaning_beds', {});
        console.log('✅ Auto-update completed:', autoUpdateResult);
        
        // Add this as a "hidden" result for internal tracking
        results.push({
          function: 'auto_update_expired_cleaning_beds',
          arguments: {},
          result: autoUpdateResult,
          tool_call_id: 'auto-' + Date.now(),
          hidden: true // Mark as hidden so it doesn't show to user
        });
      } catch (error) {
        console.warn('⚠️ Auto-update failed (non-critical):', error);
      }
    }

    return results;
  }

  /**
   * Disconnect from services
   */
  disconnect() {
    this.mcpClient.disconnect();
    this.isInitialized = false;
    
    // Clear any periodic updates
    if (this.bedStatusUpdateInterval) {
      clearInterval(this.bedStatusUpdateInterval);
      this.bedStatusUpdateInterval = null;
    }
  }

  /**
   * 🔄 Setup periodic bed status updates (every 2 minutes)
   * This ensures bed statuses stay current in real-time
   */
  setupPeriodicBedStatusUpdates() {
    // Avoid multiple intervals
    if (this.bedStatusUpdateInterval) {
      clearInterval(this.bedStatusUpdateInterval);
    }

    console.log('⏰ Setting up periodic bed status updates (every 2 minutes)');
    
    this.bedStatusUpdateInterval = setInterval(async () => {
      try {
        console.log('🔄 Periodic bed status update...');
        await this.mcpClient.callTool('auto_update_expired_cleaning_beds', {});
        console.log('✅ Periodic bed status update completed');
      } catch (error) {
        console.warn('⚠️ Periodic bed status update failed:', error);
      }
    }, 2 * 60 * 1000); // 2 minutes

    // Also run once immediately
    setTimeout(async () => {
      try {
        console.log('🔄 Initial bed status update...');
        await this.mcpClient.callTool('auto_update_expired_cleaning_beds', {});
        console.log('✅ Initial bed status update completed');
      } catch (error) {
        console.warn('⚠️ Initial bed status update failed:', error);
      }
    }, 5000); // 5 seconds after setup
  }

  /**
   * 🔄 Manual bed status refresh - call this whenever you need to update bed statuses immediately
   * Returns updated bed information
   */
  async refreshBedStatuses() {
    try {
      console.log('🔄 Manual bed status refresh triggered...');
      
      // Update expired cleaning beds
      const updateResult = await this.mcpClient.callTool('auto_update_expired_cleaning_beds', {});
      console.log('✅ Manual bed status refresh completed:', updateResult);
      
      // Also get current bed list for return
      const bedsResult = await this.mcpClient.callTool('list_beds', {});
      
      return {
        success: true,
        updateResult: updateResult,
        currentBeds: bedsResult,
        message: 'Bed statuses refreshed successfully'
      };
      
    } catch (error) {
      console.error('❌ Manual bed status refresh failed:', error);
      return {
        success: false,
        error: error.message,
        message: 'Failed to refresh bed statuses'
      };
    }
  }
}

export default DirectHttpAIMCPService;
