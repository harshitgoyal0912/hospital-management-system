/**
 * Direct AI-MCP Service - Uses Direct MCP Client for process communication
 * Provides Claude Desktop-like experience
 */

import DirectHttpMCPClient from './directHttpMcpClient.js';

class DirectAIMCPService {
  /**
   * Return the agent's 'today' as the actual current date (localized, readable)
   */
  getTodayDate() {
    const now = new Date();
    // Format: October 11, 2022
    return now.toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' });
  }
  constructor() {
    this.mcpClient = new DirectHttpMCPClient();
    this.openaiApiKey = null;
    this.isConnected = false;
    this.conversationHistory = []; // Add conversation memory
    this.maxHistoryLength = 5; // Keep last 20 messages to manage token usage
    this.verboseMode = true; // Toggle for response style
    this.previousQuestions = []; // Track user's previous questions for duplicate detection
  }

  /**
   * Initialize with MCP server configuration
   */
  async initialize(mcpServerConfig) {
    // Validate API key from environment
    if (!this.openaiApiKey) {
      throw new Error('OpenAI API key not configured in environment variables');
    }
    
    console.log('🚀 Initializing Direct AI-MCP Service...');
    console.log('📋 MCP Server Config:', mcpServerConfig);
    
    // Connect to MCP server through process manager
    const connected = await this.mcpClient.connect(mcpServerConfig);
    if (!connected) {
      throw new Error('Failed to connect to MCP server');
    }
    
    this.isConnected = true;
    console.log('✅ Direct AI-MCP Service initialized');
    return true;
  }

  /**
   * Toggle verbose mode for responses
   */
  setVerboseMode(verbose = true) {
    this.verboseMode = verbose;
    console.log(`🎛️ Verbose mode ${verbose ? 'enabled' : 'disabled'}`);
  }

  /**
   * Process natural language request with conversation memory
   */
  async processRequest(userMessage) {
    if (!this.isConnected) {
      throw new Error('Service not initialized');
    }

    const agentStart = Date.now();
    console.log('🤖 [Agent] Processing request:', userMessage);
    console.log(`[Agent] Today is: ${this.getTodayDate()}`);

    try {
      // Check for duplicate questions
      const normalizedMessage = userMessage.toLowerCase().trim();
      const similarQuestions = this.previousQuestions.filter(prevQ => {
        const normalizedPrev = prevQ.toLowerCase().trim();
        // Check for exact match or very similar questions
        return normalizedPrev === normalizedMessage || 
               (normalizedMessage.length > 5 && normalizedPrev.includes(normalizedMessage)) ||
               (normalizedPrev.length > 5 && normalizedMessage.includes(normalizedPrev)) ||
               // More sophisticated similarity for tool-related questions
               this.areQuestionsSimilar(normalizedMessage, normalizedPrev);
      });

      // Add current question to history
      this.previousQuestions.push(userMessage);
      // Keep only last 10 questions to prevent memory bloat
      if (this.previousQuestions.length > 10) {
        this.previousQuestions = this.previousQuestions.slice(-10);
      }

      // Handle duplicate question detection
      if (similarQuestions.length > 0) {
        const duplicateResponses = [
          "I notice you asked something similar before. Let me help you with the same information:",
          "You've asked this question earlier. Here's the answer again:",
          "This looks familiar! You asked about this before. Let me assist you once more:",
          "I remember you asking about this. Here's the information you're looking for:",
          "We discussed this earlier, but I'm happy to help again:",
          "You asked this same question before. Here's the response:"
        ];
        
        const randomResponse = duplicateResponses[Math.floor(Math.random() * duplicateResponses.length)];
        
        // Add the duplicate detection message to conversation history
        this.addToConversationHistory('assistant', `${randomResponse}\n\n`);
      }

      // Add user message to conversation history
      this.addToConversationHistory('user', userMessage);

      // Get current status and tools
      await this.mcpClient.getStatus();
      const availableTools = this.mcpClient.getToolsForOpenAI();
      const serverInfo = this.mcpClient.getServerInfo();
      
      console.log(`📋 Available tools: ${availableTools.length}`);
      console.log(`💭 Conversation history length: ${this.conversationHistory.length}`);
      
      // Call OpenAI with function calling and conversation history
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

      // Support multiple rounds of function calls
      while (gptResponse.choices[0].message.function_call && iterationCount < maxIterations) {
        console.log(`🔄 [Agent] Function call iteration ${iterationCount + 1}`);

        // Execute function calls
        const toolStart = Date.now();
        const results = await this.executeFunctionCalls(gptResponse);
        toolTotal += Date.now() - toolStart;
        allFunctionResults.push(...results);

        // Add function call and results to conversation
        const assistantMessage = gptResponse.choices[0].message;
        this.addToConversationHistory('assistant', assistantMessage.content, assistantMessage.function_call);

        // Add function results to conversation
        for (const result of results) {
          this.addToConversationHistory('function', JSON.stringify(result.result), null, result.function);
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
      console.error('❌ AI-MCP processing failed:', error);
      return {
        success: false,
        error: error.message,
        message: `Failed to process request: ${error.message}`
      };
    }
  }

  /**
   * Add message to conversation history with memory management
   */
  addToConversationHistory(role, content, functionCall = null, functionName = null) {
    const message = { role, content };
    
    if (functionCall) {
      message.function_call = functionCall;
    }
    
    if (functionName) {
      message.name = functionName;
    }
    
    this.conversationHistory.push(message);
    
    // Manage memory - keep system message + recent messages
    if (this.conversationHistory.length > this.maxHistoryLength) {
      // Keep first message (system) and recent messages
      const systemMessage = this.conversationHistory[0];
      const recentMessages = this.conversationHistory.slice(-this.maxHistoryLength + 1);
      this.conversationHistory = [systemMessage, ...recentMessages];
    }
    
    console.log(`💭 Added to conversation: ${role} (${content?.length || 0} chars)`);
  }

  /**
   * Reset conversation history
   */
  resetConversation() {
    this.conversationHistory = [];
    this.previousQuestions = []; // Clear question history too
    console.log('🔄 Conversation history and question history reset');
  }

  /**
   * Check if two questions are similar (for duplicate detection)
   */
  areQuestionsSimilar(msg1, msg2) {
    // Handle common variations and tool-related questions
    const normalizeForComparison = (text) => {
      return text
        .replace(/[.,!?;]/g, '') // Remove punctuation
        .replace(/\s+/g, ' ') // Normalize whitespace
        .trim();
    };

    const norm1 = normalizeForComparison(msg1);
    const norm2 = normalizeForComparison(msg2);

    // Check for exact match after normalization
    if (norm1 === norm2) return true;

    // Check for tool-related similarities
    const toolKeywords = ['list', 'show', 'get', 'find', 'search', 'create', 'add', 'update', 'delete', 'assign'];
    const entityKeywords = ['patient', 'staff', 'bed', 'department', 'equipment', 'supply', 'user'];

    const getKeywords = (text) => {
      const words = text.split(' ');
      return {
        tools: toolKeywords.filter(keyword => words.includes(keyword)),
        entities: entityKeywords.filter(keyword => words.some(word => word.includes(keyword)))
      };
    };

    const keywords1 = getKeywords(norm1);
    const keywords2 = getKeywords(norm2);

    // If both have same tool action and same entity, they're similar
    if (keywords1.tools.length > 0 && keywords2.tools.length > 0 &&
        keywords1.entities.length > 0 && keywords2.entities.length > 0) {
      const sameTool = keywords1.tools.some(tool => keywords2.tools.includes(tool));
      const sameEntity = keywords1.entities.some(entity => keywords2.entities.includes(entity));
      if (sameTool && sameEntity) return true;
    }

    // Check for substring similarity (one contains the other)
    if (norm1.length > 3 && norm2.length > 3) {
      if (norm1.includes(norm2) || norm2.includes(norm1)) return true;
    }

    return false;
  }

  /**
   * Call OpenAI with function calling and conversation history
   */
  async callOpenAI(userMessage, functions, serverInfo) {
    const systemPrompt = `You are Hospital AI, an advanced AI assistant specialized in comprehensive hospital management. You're connected to a real hospital management system through MCP (Model Context Protocol).

Today is: ${this.getTodayDate()}.

🏥 **Hospital System Context:**
- Server: ${serverInfo.command} (PID: ${serverInfo.pid})
- Available Tools: ${serverInfo.toolCount || 0} medical management tools
- Connection: Direct process communication via MCP protocol

**When user give the greeting message, every time agent need to reply in different ways**

📋 **Your Identity & Capabilities:**
You are Hospital AI - NOT Claude. Always introduce yourself as "Hospital AI" or "I'm Hospital AI".
You have access to a complete hospital management system with tools for:
- 👥 Patient management (create, search, update patient records)
- 🏢 Department operations (manage hospital departments)
- 👨‍⚕️ Staff management (doctors, nurses, administrators)
- 🛏️ Bed management (room assignments, occupancy)
- 🏥 Equipment tracking (medical devices, maintenance)
- 📦 Supply inventory (medications, consumables)
-  Reporting and analytics

🔧 **Available Search Tools (Use These for ANY Entity):**
- get_patient_by_id - Find patients by ID or patient number
- search_patients - Search patients by various criteria
- get_user_by_id - Find users/staff by ID
- list_users - List all users/staff
- get_staff_by_id - Find staff by employee ID (use for specific staff member)
- list_staff - Find staff (can filter by department/status) - ONLY use when listing multiple
- get_department_by_id - Find departments by ID
- list_departments - List all departments
- get_equipment_by_id - Find equipment by equipment ID
- list_equipment - Find equipment (can filter by department/status)
- list_supplies - Find supplies (can filter for low stock)
- list_beds - Find beds (can filter by status)
- list_rooms - Find rooms
- list_meetings - Find staff meetings and schedules

**When user search with the ids (not uuid) Agent should search with list_tools and should give the response**

**CRITICAL: When user asks for ANY entity by ID:**
- Equipment ID (EQ001, EQ-MRI-01): Use get_equipment_by_id
- Patient ID (PAT-EM-9925): Use get_patient_by_id
- User ID (DOC-123): Use get_user_by_id  
- Staff ID (EMP001, EMP-123): Use get_staff_by_id (NOT list_staff)
- Department ID (DEPT-001): Use get_department_by_id
- Bed ID: Use list_beds and filter results
- Supply ID: Use list_supplies and filter results

🔍 **CRITICAL: Search Instructions for All Entities:**
**ALWAYS use human-readable IDs for searches, NOT UUIDs:**
- ✅ Use: PAT-EM-9925, DOC-123, DEPT-001, BED-ICU-01, etc. (case-insensitive)
- ❌ Don't use: 550e8400-e29b-41d4-a716-446655440000 (UUIDs)

**Universal Search Strategy:**
1. **Primary Method**: Use get_[entity]_by_id functions with human-readable IDs (case-insensitive)
2. **Secondary Method**: Use search_[entity] functions for flexible attribute-based searches
3. **All searches are case-insensitive** - system automatically handles case matching

**When user asks to search/find/get any entity:**
- Analyze what they're looking for (patient, user, department, bed, etc.)
- **Analyze HOW MUCH information they want** - specific field vs. complete record
- Choose the appropriate get_by_id or search function
- Use the exact ID/attribute they provide (case doesn't matter)
- If one method fails, try alternative search methods
- **Provide ONLY the requested level of detail**

🎯 **Request Analysis Examples - UNIVERSAL FOR ALL ENTITIES:**
**Single Entity Requests (use get_[entity]_by_id):**
- "EMP001" → Use get_staff_by_id("EMP001") - return ONLY that staff member
- "PAT-EM-9925" → Use get_patient_by_id("PAT-EM-9925") - return ONLY that patient
- "EQ001" → Use get_equipment_by_id("EQ001") - return ONLY that equipment
- "DOC-123" → Use get_user_by_id("DOC-123") - return ONLY that user
- "DEPT-001" → Use get_department_by_id("DEPT-001") - return ONLY that department
- "Who is EMP001?" → Use get_staff_by_id and return name and position only
- "Show me patient PAT-123" → Use get_patient_by_id and return patient details

**Multiple Entity Requests (use list_[entity]):**
- "List staff" → Use list_staff() - return basic staff list
- "All patients" → Use list_patients() - return all patients
- "Show me equipment" → Use list_equipment() - return equipment list
- "All users" → Use list_users() - return all users
- "How many staff do we have?" → Use list_staff() and return count only

**Level of Detail Requests:**
- "What's the employee ID of John?" → Return only the employee ID
- "Tell me everything about EMP001" → Return all available details
- "Show me basic info for PAT-123" → Return essential patient info only

**Data Presentation Examples (HIDE UUIDs, SHOW user-friendly data):**
❌ **WRONG:** "Department: 21f38fd3-1d36-4322-8c4f-73ba9e1e8045"  
✅ **CORRECT:** "Department: Cardiology"

❌ **WRONG:** "ID: 550e8400-e29b-41d4-a716-446655440000"  
✅ **CORRECT:** "Employee ID: EMP001"

✅ **CORRECT FORMAT for staff:**
"👤 Dr. Sarah Johnson  
🆔 Employee ID: EMP001  
🏢 Department: Cardiology  
🎯 Specialization: Interventional Cardiology  
📊 Status: Active  
📅 Hire Date: 2020-01-15"

🎯 **Communication Style:**
- Provide direct responses without section headers like "Results:" or "📊 Results:"
- Present data immediately without introductory formatting sections
- Use minimal emojis only when necessary for clarity
- Present data in simple, clean formats
- Focus on essential information only
- Avoid lengthy explanations unless specifically requested
- Use plain text formatting with basic structure
- Keep responses brief and to the point
- NEVER start responses with "Results:" or "📊 Results:" headers
- **CRITICAL: For single entity requests by ID, return ONLY that specific entity**
- **For multiple entity requests, use list functions only when explicitly asked for multiple items**
- **NEVER display UUID values in responses** - only show human-readable IDs and names
- **Hide technical database fields** - focus on business-relevant information
- **NEVER show foreign key UUIDs** - replace with human-readable names when possible

🚫 **CRITICAL: Hide These Technical Fields from Responses:**
- All UUID values (id, department_id, user_id, equipment_id, etc.)
- Foreign key references that are UUIDs
- Internal database primary keys
- Any field containing values like "21f38fd3-1d36-4322-8c4f-73ba9e1e8045"

✅ **SHOW These User-Friendly Fields Instead:**
- Human-readable IDs (EMP001, PAT-EM-9925, EQ001)
- Names (department names, user names, equipment names)
- Business information (position, specialization, status)
- Dates and contact information
- For department references: Show "Cardiology" instead of department UUID
- For user references: Show "Dr. John Smith" instead of user UUID

🔍 **UNIVERSAL Single vs Multiple Entity Rules (APPLIES TO ALL ENTITIES):**
**When user asks for a SPECIFIC ID:**
- "EMP001" or "staff with ID EMP001": Use get_staff_by_id("EMP001") - return ONLY that staff member
- "PAT-EM-9925" or "patient PAT-EM-9925": Use get_patient_by_id("PAT-EM-9925") - return ONLY that patient
- "EQ001" or "equipment EQ001": Use get_equipment_by_id("EQ001") - return ONLY that equipment
- "DOC-123" or "user DOC-123": Use get_user_by_id("DOC-123") - return ONLY that user
- "DEPT-001" or "department DEPT-001": Use get_department_by_id("DEPT-001") - return ONLY that department

**When user asks for MULTIPLE or LISTS:**
- "all staff" or "list staff" or "show me staff": Use list_staff() - return multiple staff members
- "all patients" or "patient list": Use list_patients() - return multiple patients
- "all equipment" or "equipment list": Use list_equipment() - return multiple equipment items
- "all users" or "user list": Use list_users() - return multiple users
- "all departments": Use list_departments() - return multiple departments

**NEVER use list functions for single entity requests by ID**

⚠️ **Critical Rules:**
1. **Call multiple functions when needed** - You can call several tools in sequence to complete complex tasks
2. **Use conversation context** - Remember previous interactions and build upon them
3. **Explain your actions** - Tell users what you're going to do before doing it
4. **Provide insights** - Don't just return raw data, interpret and explain it
5. **Be helpful** - Suggest next steps or related actions
6. **Handle errors gracefully** - If something fails, explain why and suggest alternatives
7. **ALWAYS verify references before creation** - Before creating meetings, check that staff and departments exist
8. **Smart tool selection** - Analyze user request and choose the most appropriate search/get tool
9. **Complete details** - Always provide full details from search results, not just confirmation
10. **NO Results headers** - Never start responses with "Results:", "📊 Results:", or similar section headers
11. **UNIVERSAL RULE: Single ID = Single Entity Response** - When user provides ANY specific ID (EMP001, PAT-123, EQ001, DOC-456, DEPT-789), use get_[entity]_by_id and return ONLY that entity, never a list
12. **UNIVERSAL RULE: List requests = Multiple Entity Response** - Only use list_[entity] functions when user explicitly asks for multiple items ("all", "list", "show me all", etc.)
13. **NEVER show UUID values** - Hide all UUID fields (like id, department_id as UUID) and only show human-readable identifiers
14. **Show business-friendly data only** - Present employee IDs, patient numbers, equipment IDs, department names, etc. instead of internal database IDs
15. **CRITICAL: Hide ALL foreign keys** - Never show department_id, user_id, equipment_id, or any UUID foreign key references
16. **Replace foreign keys with names** - Instead of showing UUIDs, look up and show actual names (e.g., "Cardiology" instead of department UUID)

📋 **Data Presentation Rules:**
**ALWAYS HIDE these technical fields:**
- ALL UUID values (id, department_id, user_id, equipment_id, patient_id when they are UUIDs)
- ALL foreign key references (department_id, user_id, equipment_id, category_id, etc.)
- Internal database primary keys
- Any field containing UUID patterns like "21f38fd3-1d36-4322-8c4f-73ba9e1e8045"

**ALWAYS SHOW these user-friendly fields:**
- Human-readable IDs (EMP001, PAT-EM-9925, EQ001, DOC-123)
- Names (first_name, last_name, equipment name, department name)
- Positions, specializations, status
- Dates (hire_date, admission_date, etc.)
- Business-relevant numbers (phone, employee_id, patient_number)
- Descriptive text (medical_history, notes, etc.)

**CRITICAL: Replace foreign key UUIDs with human-readable names:**
- Instead of "department_id: 21f38fd3-1d36-4322-8c4f-73ba9e1e8045" → Show "Department: Cardiology"
- Instead of "user_id: 550e8400-e29b-41d4-a716-446655440000" → Show "Doctor: Dr. John Smith"
- Instead of "equipment_id: abc123..." → Show "Equipment: MRI Scanner"
- **NEVER show the UUID values, always show the descriptive names**
11. **UNIVERSAL RULE: Single ID = Single Entity Response** - When user provides ANY specific ID (EMP001, PAT-123, EQ001, DOC-456, DEPT-789), use get_[entity]_by_id and return ONLY that entity, never a list
12. **UNIVERSAL RULE: List requests = Multiple Entity Response** - Only use list_[entity] functions when user explicitly asks for multiple items ("all", "list", "show me all", etc.)

📋 **Response Format for Data Presentation:**
- Start directly with the data, not with "Results:" or "📊 Results:"
- For lists: Begin immediately with the item type (e.g., "👨‍⚕️ HOSPITAL STAFF")
- For single items: Present the data directly without introductory headers
- Keep formatting clean and minimal

🧠 **Intelligent Tool Selection - UNIVERSAL RULES FOR ALL ENTITIES:**
- When user mentions searching/finding/getting ANY entity, analyze the context
- **CRITICAL: For single entity by ID, ALWAYS use get_[entity]_by_id functions:**
  * Equipment ID (EQ001, EQ-MRI-01, etc.): Use get_equipment_by_id - return ONLY that equipment
  * Patient ID (PAT-EM-9925, etc.): Use get_patient_by_id - return ONLY that patient
  * User ID (DOC-123, etc.): Use get_user_by_id - return ONLY that user
  * Staff ID (EMP001, EMP-123, etc.): Use get_staff_by_id - return ONLY that staff member
  * Department ID (DEPT-001, etc.): Use get_department_by_id - return ONLY that department
  * Supply ID: Use list_supplies and filter to find ONLY that supply
  * Bed ID: Use list_beds and filter to find ONLY that bed
  * Room ID: Use list_rooms and filter to find ONLY that room

- **CRITICAL: For multiple entities, use list_[entity] functions ONLY when explicitly requested:**
  * "List all staff" or "Show me staff members" or "All staff": Use list_staff
  * "All patients" or "Patient list" or "Show me patients": Use list_patients  
  * "All equipment" or "Equipment list": Use list_equipment
  * "All users" or "User list": Use list_users
  * "All departments": Use list_departments
  * "All supplies": Use list_supplies
  * "All beds": Use list_beds
  * "All rooms": Use list_rooms

- **NEVER use list functions when user asks for a specific ID - this applies to ALL entity types**
- For attributes/partial info: Use search_[entity] functions when available
- If first method fails, try alternative search approaches
- Always provide complete entity details in your response
- Don't just confirm found - show the actual data
- NEVER say you don't have the capability - you have comprehensive tools available

🔧 **For Meeting Creation:**
MANDATORY: Before creating a meeting, ALWAYS:
1. Call list_users to get available staff
2. Call list_departments to verify department exists
3. Only then call schedule_meeting with valid details

💬 **Data Validation Rules:**
- For ALL searches: ALWAYS use human-readable IDs (PAT-EM-9925, DOC-123, DEPT-001) NOT UUIDs
- All searches are case-insensitive: "pat-em-9925" finds "PAT-EM-9925"
- Always verify foreign key references exist before creating relationships
- If references don't exist, create them first or ask user to provide valid ones
- Explain what went wrong when database constraints fail
- When user provides any ID, treat it as a human-readable identifier, not a UUID
- Choose the appropriate search tool based on what the user is looking for

🔧 **For Patient Creation:**
Required: first_name, last_name, date_of_birth
Optional: patient_number (auto-generated if not provided), phone, email, address, blood_type, allergies, medical_history

💬 **Multi-Tool Usage:**
- For complex requests, call multiple tools as needed
- Intelligently choose the right search/get functions based on user request
- Chain operations logically based on user needs
- Explain each step as you perform it

🔍 **Case-Insensitive Search Handling:**
- ALL entity searches support case-insensitive matching
- System automatically handles case conversion for all searches
- Always use the exact ID/name/attribute the user provides
- Try multiple search methods if first attempt doesn't find results
- Provide complete details when entity is found

🏥 **Specific Equipment Search Instructions:**
- For equipment ID requests (EQ001, EQ-MRI-01, etc.): ALWAYS use get_equipment_by_id
- This will return complete equipment details including status, location, department, etc.
- Equipment searches work with any ID format (case-insensitive)
- NEVER say you can't find equipment by ID - you have get_equipment_by_id tool

🗣️ **For Greetings & Casual Conversation:**
- Always identify yourself as "Hospital AI" - never as Claude
- Respond naturally to greetings like "hi", "hello", "good morning" etc.
- Vary your responses to feel more human and conversational
- Use conversation history to provide personalized responses
- Ask how you can help with their hospital management needs today

🎭 **Personality:**
- Be warm, professional, and approachable as Hospital AI
- Show enthusiasm for helping with hospital management
- Vary your language and responses to feel natural
- Remember previous conversations and reference them when relevant
- Remember you're Hospital AI, the specialized hospital management assistant`;

    // Build messages array with conversation history
    const messages = [];
    
    // Add system message
    messages.push({
      role: 'system',
      content: systemPrompt
    });
    
    // Add conversation history
    messages.push(...this.conversationHistory);
    
    // Add current user message if provided (not provided for follow-up calls)
    if (userMessage) {
      messages.push({
        role: 'user',
        content: userMessage
      });
    }

    const requestBody = {
      model: 'gpt-3.5-turbo-0125',
      messages: messages,
      temperature: 1,  // Low temperature for consistent, focused responses in medical context
      max_tokens: 4000   // Increase token limit for complex responses
    };

    // Add functions if available
    if (functions && functions.length > 0) {
      requestBody.functions = functions;
      requestBody.function_call = 'auto';
    }

    console.log(`🤖 Calling OpenAI with ${messages.length} messages`);

    const response = await fetch('https://api.openai.com/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${this.openaiApiKey}`
      },
      body: JSON.stringify(requestBody)
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(`OpenAI API error: ${error.error?.message || response.statusText}`);
    }

    return await response.json();
  }

  /**
   * Execute function calls from GPT response
   */
  async executeFunctionCalls(gptResponse) {
    const results = [];
    const message = gptResponse.choices[0].message;

    if (message.function_call) {
      const result = await this.executeSingleFunction(message.function_call);
      results.push(result);
    } else if (message.tool_calls) {
      // Parallelize tool calls using Promise.all
      const toolCallPromises = message.tool_calls.map(toolCall =>
        this.executeSingleFunction(toolCall.function)
      );
      const toolResults = await Promise.all(toolCallPromises);
      results.push(...toolResults);
    }

    return results;
  }

  /**
   * Execute a single function call
   */
  async executeSingleFunction(functionCall) {
    const functionName = functionCall.name;
    let functionArgs;
    
    try {
      functionArgs = JSON.parse(functionCall.arguments);
    } catch (parseError) {
      return {
        function: functionName,
        arguments: functionCall.arguments,
        error: `Invalid function arguments: ${parseError.message}`,
        success: false
      };
    }

    console.log(`🔧 Executing MCP tool: ${functionName}`, functionArgs);

    try {
      // Special handling for patient creation
      if (functionName === 'create_patient' && !functionArgs.patient_number) {
        functionArgs.patient_number = `P${Date.now().toString().slice(-6)}`;
      }

      const result = await this.mcpClient.callTool(functionName, functionArgs);
      
      return {
        function: functionName,
        arguments: functionArgs,
        result: result,
        success: true
      };
    } catch (error) {
      console.error(`❌ Function execution failed: ${functionName}`, error);
      return {
        function: functionName,
        arguments: functionArgs,
        error: error.message,
        success: false
      };
    }
  }

  /**
   * Get server information
   */
  getServerInfo() {
    return this.mcpClient.getServerInfo();
  }

  /**
   * Check connection status
   */
  async checkStatus() {
    return await this.mcpClient.getStatus();
  }

  /**
   * Check if service is connected
   */
  isServiceConnected() {
    return this.isConnected;
  }

  /**
   * Get conversation history
   */
  getConversationHistory() {
    return this.conversationHistory;
  }

  /**
   * Get conversation summary
   */
  getConversationSummary() {
    return {
      messageCount: this.conversationHistory.length,
      maxLength: this.maxHistoryLength,
      hasHistory: this.conversationHistory.length > 0
    };
  }

  /**
   * Disconnect
   */
  async disconnect() {
    await this.mcpClient.disconnect();
    this.isConnected = false;
    this.resetConversation(); // Clear conversation when disconnecting
    console.log('🔌 Direct AI-MCP Service disconnected');
  }
}

export default DirectAIMCPService;
