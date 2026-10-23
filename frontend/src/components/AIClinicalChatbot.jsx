/**
 * AI Clinical Chatbot - Enhanced chatbot with clinical decision support
 * Integrates the new AI Clinical Assistant agent with your existing chatbot architecture
 */

import React, { useState, useRef, useEffect } from 'react';
import { MessageCircle, Brain, Activity, Pill, FileText, AlertTriangle, Send, Bot, User, Stethoscope, ArrowLeft } from 'lucide-react';

const AIClinicalChatbot = ({ aiService, onBackToMainChat }) => {
  const [messages, setMessages] = useState([
    {
      id: 1,
      type: 'assistant',
      content: '🏥 Hello! I\'m your AI Clinical Assistant. I can help with:\n\n• 🧠 Clinical decision support\n• 💊 Drug interaction checking\n• 📊 Vital signs analysis\n• 🔍 Differential diagnosis\n• 📝 Clinical note processing\n\n' + (onBackToMainChat ? '← Use the back button to return to your main chatbot\n\n' : '') + 'How can I assist you today?',
      timestamp: new Date(),
      isAI: true,
      category: 'welcome'
    }
  ]);
  
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [selectedClinicalMode, setSelectedClinicalMode] = useState('general');
  const [showActionButtons, setShowActionButtons] = useState(true); // Hide after first input
  const [showMobileModeDropdown, setShowMobileModeDropdown] = useState(false); // Mobile mode selector
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);
  const modeDropdownRef = useRef(null);

  // Clinical AI modes
  const clinicalModes = {
    general: { icon: Brain, label: 'General AI Assistant', color: 'blue' },
    clinical: { icon: Stethoscope, label: 'Clinical Decision Support', color: 'green' },
    drugs: { icon: Pill, label: 'Drug Interactions', color: 'purple' },
    vitals: { icon: Activity, label: 'Vital Signs Analysis', color: 'red' },
    diagnosis: { icon: FileText, label: 'Differential Diagnosis', color: 'orange' },
    notes: { icon: FileText, label: 'Clinical Notes', color: 'indigo' }
  };

  // Quick action buttons for clinical scenarios
  const quickActions = [
    { 
      text: 'Warfarin + Aspirin interactions', 
      mode: 'drugs',
      icon: Pill 
    },
    { 
      text: 'BP 140/90, HR 95 analysis', 
      mode: 'vitals',
      icon: Activity 
    },
    { 
      text: 'Chest pain + dyspnea diagnosis', 
      mode: 'diagnosis',
      icon: AlertTriangle 
    },
    { 
      text: 'Hypertensive emergency support', 
      mode: 'clinical',
      icon: Stethoscope 
    }
  ];

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Auto-resize textarea based on content (matching original chatbot)
  useEffect(() => {
    if (inputRef.current) {
      const textarea = inputRef.current;
      textarea.style.height = 'auto';
      const newHeight = Math.min(Math.max(textarea.scrollHeight, 40), 120);
      textarea.style.height = newHeight + 'px';
    }
  }, [inputValue]);

  // Reset textarea height when input is cleared
  useEffect(() => {
    if (inputRef.current && inputValue === '') {
      inputRef.current.style.height = '40px';
    }
  }, [inputValue]);

  // Handle mobile viewport height issues with keyboard (matching original)
  useEffect(() => {
    const setVH = () => {
      const vh = window.innerHeight * 0.01;
      document.documentElement.style.setProperty('--vh', `${vh}px`);
    };

    setVH();
    window.addEventListener('resize', setVH);
    window.addEventListener('orientationchange', setVH);

    return () => {
      window.removeEventListener('resize', setVH);
      window.removeEventListener('orientationchange', setVH);
    };
  }, []);

  // Close mobile dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (modeDropdownRef.current && !modeDropdownRef.current.contains(event.target)) {
        setShowMobileModeDropdown(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  // Enhanced message processing with clinical AI integration
  const handleSendMessage = async () => {
    if (!inputValue.trim() || isLoading) return;

    const userMessage = {
      id: Date.now(),
      type: 'user',
      content: inputValue,
      timestamp: new Date(),
      isAI: false,
      clinicalMode: selectedClinicalMode
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);
    setShowActionButtons(false); // Hide action buttons after first input

    try {
      let response;
      
      // Route to appropriate AI Clinical Assistant tool based on mode
      if (selectedClinicalMode === 'clinical') {
        response = await aiService.callToolDirectly('ai_clinical_assistant', {
          query: inputValue,
          context: { mode: 'clinical_decision_support' }
        });
      } else if (selectedClinicalMode === 'drugs') {
        // Extract medications from the input for drug interaction check
        const medications = extractMedicationsFromText(inputValue);
        if (medications.length > 0) {
          response = await aiService.callToolDirectly('get_drug_interactions', {
            medications: medications,
            patient_context: { query: inputValue }
          });
        } else {
          response = await aiService.callToolDirectly('ai_clinical_assistant', {
            query: `Drug interaction analysis: ${inputValue}`,
            context: { mode: 'drug_interactions' }
          });
        }
      } else if (selectedClinicalMode === 'vitals') {
        // Extract vital signs from the input
        const vitalSigns = extractVitalSignsFromText(inputValue);
        if (Object.keys(vitalSigns).length > 0) {
          response = await aiService.callToolDirectly('analyze_vital_signs', {
            vital_signs: vitalSigns,
            patient_age: null // Could be extracted from context
          });
        } else {
          response = await aiService.callToolDirectly('ai_clinical_assistant', {
            query: `Vital signs analysis: ${inputValue}`,
            context: { mode: 'vital_signs' }
          });
        }
      } else if (selectedClinicalMode === 'diagnosis') {
        // Extract symptoms for differential diagnosis
        const symptoms = extractSymptomsFromText(inputValue);
        if (symptoms.length > 0) {
          response = await aiService.callToolDirectly('generate_differential_diagnosis', {
            symptoms: symptoms,
            patient_context: { query: inputValue }
          });
        } else {
          response = await aiService.callToolDirectly('ai_clinical_assistant', {
            query: `Differential diagnosis: ${inputValue}`,
            context: { mode: 'differential_diagnosis' }
          });
        }
      } else if (selectedClinicalMode === 'notes') {
        response = await aiService.callToolDirectly('process_clinical_notes', {
          document_text: inputValue,
          extract_type: 'comprehensive'
        });
      } else {
        // General mode - use your existing AI service
        response = await aiService.processRequest(inputValue);
      }

      // Parse the response - handle the MCP format that wraps the actual result
      let parsedResponse = response;
      
      // Handle orchestrator response format (success, agent, result)
      if (response && response.success && response.result) {
        parsedResponse = response.result;
      }
      // Check if response is in MCP format with content array
      else if (response && response.content && Array.isArray(response.content) && response.content[0] && response.content[0].text) {
        try {
          // Parse the JSON string inside the MCP response
          const innerResponse = JSON.parse(response.content[0].text);
          
          if (innerResponse.result) {
            parsedResponse = innerResponse.result;
          } else {
            parsedResponse = innerResponse;
          }
        } catch (parseError) {
          parsedResponse = response.content[0].text;
        }
      }
      // Handle direct response format
      else if (response && response.result) {
        parsedResponse = response.result;
      }
      // Handle string responses
      else if (typeof response === 'string') {
        try {
          parsedResponse = JSON.parse(response);
        } catch (parseError) {
          parsedResponse = response;
        }
      }

      // Format the response for clinical display
      const assistantMessage = {
        id: Date.now() + 1,
        type: 'assistant',
        content: formatClinicalResponse(parsedResponse, selectedClinicalMode),
        timestamp: new Date(),
        isAI: true,
        clinicalMode: selectedClinicalMode,
        rawResponse: parsedResponse
      };

      setMessages(prev => [...prev, assistantMessage]);

    } catch (error) {
      console.error('AI Clinical Assistant error:', error);
      
      const errorMessage = {
        id: Date.now() + 1,
        type: 'assistant',
        content: `❌ I encountered an error while processing your clinical request: ${error.message}. Please try again or contact support.`,
        timestamp: new Date(),
        isAI: true,
        isError: true
      };

      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  // Extract medications from natural language text
  const extractMedicationsFromText = (text) => {
    const commonMeds = [
      'warfarin', 'aspirin', 'ibuprofen', 'acetaminophen', 'paracetamol', 'metformin', 
      'lisinopril', 'amlodipine', 'atorvastatin', 'metoprolol', 'furosemide',
      'digoxin', 'phenytoin', 'lithium', 'amoxicillin', 'azithromycin', 'omeprazole',
      'hydrochlorothiazide', 'simvastatin', 'prednisone', 'albuterol', 'insulin',
      'losartan', 'clopidogrel', 'levothyroxine', 'gabapentin', 'sertraline',
      'tramadol', 'oxycodone', 'morphine', 'codeine', 'fentanyl', 'heparin',
      'enoxaparin', 'carvedilol', 'diltiazem', 'verapamil', 'amiodarone'
    ];
    
    const found = [];
    const lowerText = text.toLowerCase();
    
    // First try to find exact medication matches
    commonMeds.forEach(med => {
      const regex = new RegExp(`\\b${med}\\b`, 'i');
      if (regex.test(lowerText)) {
        found.push(med);
      }
    });
    
    // If no exact matches, try to extract from common patterns
    if (found.length === 0) {
      const patterns = [
        /(\w+)\s*\+\s*(\w+)/g, // "drug1 + drug2"
        /(\w+)\s*and\s*(\w+)/g, // "drug1 and drug2"
        /(\w+)\s*with\s*(\w+)/g, // "drug1 with drug2"
        /interactions?\s*(?:for|between)\s*([^,.]+)/gi // "interactions for drug1, drug2"
      ];
      
      patterns.forEach(pattern => {
        let match;
        while ((match = pattern.exec(lowerText)) !== null) {
          if (match[1]) found.push(match[1].trim());
          if (match[2]) found.push(match[2].trim());
        }
      });
    }
    
    return [...new Set(found)]; // Remove duplicates
  };

  // Extract vital signs from text
  const extractVitalSignsFromText = (text) => {
    const vitals = {};
    
    // Blood pressure pattern (e.g., "BP 120/80", "140/90")
    const bpMatch = text.match(/(?:bp|blood pressure)?[:\s]*(\d{2,3})\/(\d{2,3})/i);
    if (bpMatch) {
      vitals.blood_pressure = [parseInt(bpMatch[1]), parseInt(bpMatch[2])];
    }
    
    // Heart rate pattern (e.g., "HR 85", "heart rate 72")
    const hrMatch = text.match(/(?:hr|heart rate)[:\s]*(\d{2,3})/i);
    if (hrMatch) {
      vitals.heart_rate = parseInt(hrMatch[1]);
    }
    
    // Respiratory rate pattern (e.g., "RR 18", "respiratory rate 20")
    const rrMatch = text.match(/(?:rr|respiratory rate)[:\s]*(\d{1,2})/i);
    if (rrMatch) {
      vitals.respiratory_rate = parseInt(rrMatch[1]);
    }
    
    // Temperature pattern (e.g., "temp 98.6", "temperature 37.2")
    const tempMatch = text.match(/(?:temp|temperature)[:\s]*(\d{2,3}\.?\d?)/i);
    if (tempMatch) {
      vitals.temperature = parseFloat(tempMatch[1]);
    }
    
    // Oxygen saturation pattern (e.g., "O2 sat 98%", "oxygen 95")
    const o2Match = text.match(/(?:o2 sat|oxygen saturation|spo2)[:\s]*(\d{2,3})%?/i);
    if (o2Match) {
      vitals.oxygen_saturation = parseInt(o2Match[1]);
    }
    
    return vitals;
  };

  // Extract symptoms from text
  const extractSymptomsFromText = (text) => {
    const commonSymptoms = [
      'chest pain', 'shortness of breath', 'headache', 'fever', 'cough',
      'nausea', 'vomiting', 'dizziness', 'fatigue', 'abdominal pain',
      'back pain', 'joint pain', 'difficulty breathing', 'palpitations'
    ];
    
    const found = [];
    const lowerText = text.toLowerCase();
    
    commonSymptoms.forEach(symptom => {
      if (lowerText.includes(symptom)) {
        found.push(symptom);
      }
    });
    
    // If no common symptoms found, split by common delimiters
    if (found.length === 0) {
      const potential = text.split(/[,;+&]/).map(s => s.trim()).filter(s => s.length > 2);
      return potential.slice(0, 5); // Limit to 5 symptoms
    }
    
    return found;
  };

  // Format clinical AI response for display
  const formatClinicalResponse = (response, mode) => {
    if (!response) return '❌ No response received from AI Clinical Assistant.';
    
    if (typeof response === 'string') return response;
    
    if (response.success === false) {
      return `❌ **Clinical AI Error:** ${response.error || 'Unknown error occurred'}`;
    }
    
    let formatted = '';
    
    // Format based on clinical mode
    switch (mode) {
      case 'clinical':
        if (response.ai_response) {
          formatted += `🧠 **Clinical AI Analysis:**\n\n${response.ai_response}\n\n`;
        }
        if (response.structured_recommendations && response.structured_recommendations.recommendations) {
          formatted += `📋 **Recommendations:**\n${response.structured_recommendations.recommendations.map(rec => `• ${rec}`).join('\n')}\n\n`;
        }
        if (response.safety_checks && response.safety_checks.length > 0) {
          formatted += `⚠️ **Safety Alerts:**\n${response.safety_checks.map(check => `• ${check}`).join('\n')}\n\n`;
        }
        break;
        
      case 'drugs':
        formatted += `💊 **Drug Interaction Analysis**\n\n`;
        
        // Check for interactions
        if (response.interactions && response.interactions.length > 0) {
          formatted += `� **Drug Interactions Found:**\n\n`;
          response.interactions.forEach(interaction => {
            formatted += `⚠️ **${interaction.medication_1} + ${interaction.medication_2}**\n`;
            formatted += `   • **Severity:** ${interaction.severity || 'Moderate'}\n`;
            formatted += `   • **Type:** ${interaction.interaction_type || 'Drug-Drug Interaction'}\n`;
            formatted += `   • **Description:** ${interaction.description}\n\n`;
          });
        } else {
          formatted += `✅ **No Direct Drug-Drug Interactions Found**\n\n`;
        }
        
        // Check for contraindications
        if (response.contraindications && response.contraindications.length > 0) {
          formatted += `🚫 **Contraindications:**\n\n`;
          response.contraindications.forEach(contra => {
            formatted += `⚠️ **${contra.medication}**\n`;
            formatted += `   • **Contraindication:** ${contra.contraindication}\n`;
            formatted += `   • **Severity:** ${contra.severity}\n`;
            formatted += `   • **Description:** ${contra.description}\n\n`;
          });
        }
        
        // Always show AI insights if available - this is the detailed analysis
        if (response.ai_insights) {
          formatted += `🧠 **Detailed AI Clinical Analysis:**\n\n${response.ai_insights}\n\n`;
        }
        
        // Show medication list being analyzed
        if (response.medications && response.medications.length > 0) {
          formatted += `📋 **Medications Analyzed:** ${response.medications.join(', ')}\n\n`;
        }
        
        // Show clinical recommendation
        if (response.recommendation) {
          formatted += `📋 **Clinical Recommendation:**\n${response.recommendation}\n\n`;
        }
        break;
        
      case 'vitals':
        if (response.overall_status === 'critical') {
          formatted += `🚨 **CRITICAL VITAL SIGNS ALERT**\n\n`;
        } else {
          formatted += `📊 **Vital Signs Analysis**\n\n`;
        }
        
        if (response.alerts && response.alerts.length > 0) {
          formatted += `🚨 **Alerts:**\n${response.alerts.map(alert => `• ${alert}`).join('\n')}\n\n`;
        }
        
        if (response.analysis) {
          formatted += `� **Detailed Analysis:**\n`;
          Object.entries(response.analysis).forEach(([vital, data]) => {
            if (typeof data === 'object' && data.status) {
              const statusIcon = data.status === 'normal' ? '✅' : data.status === 'high' ? '🔴' : '🔵';
              formatted += `${statusIcon} **${vital.replace('_', ' ').toUpperCase()}:** ${data.value} (Normal: ${data.normal_range})\n`;
            }
          });
          formatted += '\n';
        }
        
        if (response.ai_insights) {
          formatted += `🧠 **AI Clinical Insights:**\n\n${response.ai_insights}\n\n`;
        }
        break;
        
      case 'diagnosis':
        formatted += `🔍 **Differential Diagnosis Analysis**\n\n`;
        
        if (response.differential_diagnosis) {
          if (typeof response.differential_diagnosis === 'object' && !response.differential_diagnosis.raw_response) {
            // Try to format structured diagnosis
            if (response.differential_diagnosis.diagnoses) {
              formatted += `**Top Differential Diagnoses:**\n`;
              response.differential_diagnosis.diagnoses.forEach((dx, index) => {
                formatted += `${index + 1}. ${dx.name || dx} (${dx.probability || 'Unknown probability'})\n`;
              });
              formatted += '\n';
            }
            
            if (response.differential_diagnosis.tests) {
              formatted += `**Recommended Tests:**\n${response.differential_diagnosis.tests.map(test => `• ${test}`).join('\n')}\n\n`;
            }
            
            if (response.differential_diagnosis.red_flags) {
              formatted += `🚩 **Red Flag Symptoms:**\n${response.differential_diagnosis.red_flags.map(flag => `• ${flag}`).join('\n')}\n\n`;
            }
          } else {
            // Fallback to raw response
            formatted += response.differential_diagnosis.raw_response || JSON.stringify(response.differential_diagnosis, null, 2);
            formatted += '\n\n';
          }
        }
        
        if (response.ai_raw_response && !response.differential_diagnosis.raw_response) {
          formatted += `**AI Analysis:**\n${response.ai_raw_response}\n\n`;
        }
        break;
        
      case 'notes':
        formatted += `📝 **Clinical Notes Analysis**\n\n`;
        
        if (response.extracted_data) {
          const data = response.extracted_data;
          
          if (data.patient_info) {
            formatted += `� **Patient Information:**\n`;
            if (data.patient_info.chief_complaint) {
              formatted += `• Chief Complaint: ${data.patient_info.chief_complaint}\n`;
            }
            if (data.patient_info.history_present_illness) {
              formatted += `• History: ${data.patient_info.history_present_illness}\n`;
            }
            formatted += '\n';
          }
          
          if (data.symptoms && data.symptoms.length > 0) {
            formatted += `🔍 **Symptoms:**\n${data.symptoms.map(symptom => `• ${symptom}`).join('\n')}\n\n`;
          }
          
          if (data.vital_signs && Object.keys(data.vital_signs).length > 0) {
            formatted += `📊 **Vital Signs:**\n`;
            Object.entries(data.vital_signs).forEach(([vital, value]) => {
              formatted += `• ${vital.replace('_', ' ')}: ${value}\n`;
            });
            formatted += '\n';
          }
          
          if (data.medications && data.medications.length > 0) {
            formatted += `💊 **Medications:**\n${data.medications.map(med => `• ${med}`).join('\n')}\n\n`;
          }
          
          if (data.diagnoses) {
            formatted += `🔬 **Diagnoses:**\n`;
            if (data.diagnoses.primary) {
              formatted += `• Primary: ${data.diagnoses.primary}\n`;
            }
            if (data.diagnoses.secondary && data.diagnoses.secondary.length > 0) {
              formatted += `• Secondary: ${data.diagnoses.secondary.join(', ')}\n`;
            }
            formatted += '\n';
          }
          
          if (data.plan) {
            formatted += `📋 **Treatment Plan:**\n${data.plan}\n\n`;
          }
        }
        
        if (response.confidence_score) {
          formatted += `📈 **Extraction Confidence:** ${Math.round(response.confidence_score * 100)}%\n\n`;
        }
        break;
        
      default:
        if (response.ai_response) {
          formatted = response.ai_response;
        } else {
          formatted = JSON.stringify(response, null, 2);
        }
    }
    
    // Add disclaimer for clinical content
    if (mode !== 'general' && formatted) {
      formatted += '\n⚕️ *This is AI-generated clinical assistance. Always verify with current medical guidelines and consult with qualified healthcare professionals.*';
    }
    
    return formatted || '✅ Request processed successfully.';
  };

  const handleQuickAction = (action) => {
    setSelectedClinicalMode(action.mode);
    setInputValue(action.text);
    setShowActionButtons(false); // Hide action buttons when quick action is used
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className="bg-[#1a1a1a] flex flex-col text-white relative" style={{ 
      height: 'calc(var(--vh, 1vh) * 100)',
      maxHeight: 'calc(var(--vh, 1vh) * 100)',
      overflow: 'hidden'
    }}>
      {/* Header - FIXED AT TOP (matching original chatbot exactly) */}
      <div className="fixed top-0 left-0 right-0 border-b border-gray-700 px-3 sm:px-4 py-3 bg-[#1a1a1a] z-30">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2 sm:space-x-3">
            {/* Back Button */}
            {onBackToMainChat && (
              <button
                onClick={onBackToMainChat}
                className="p-1.5 sm:p-2 rounded-md text-gray-400 hover:text-gray-300 hover:bg-gray-700 transition-colors"
                title="Back to Main Chatbot"
              >
                <ArrowLeft className="w-4 h-4 sm:w-5 sm:h-5" />
              </button>
            )}
            
            <div className="w-6 h-6 sm:w-7 sm:h-7 bg-green-600 rounded-full flex items-center justify-center text-white text-xs sm:text-sm font-medium shadow-lg">
              <Stethoscope className="w-3 h-3 sm:w-4 sm:h-4" />
            </div>
            <div className="min-w-0 flex-1">
              <h1 className="text-sm font-medium text-white truncate">AI Clinical Assistant</h1>
              <div className="text-xs text-gray-400">
                <div className="hidden sm:block">
                  <p className="mb-1">
                    Intelligent clinical decision support • OpenAI GPT-3.5 • RAG-enhanced medical knowledge
                  </p>
                </div>
                <div className="block sm:hidden">
                  <p>Clinical AI • Medical Knowledge Base</p>
                </div>
              </div>
            </div>
          </div>
          
          {/* Clinical Mode Selector - Mobile: Dropdown, Desktop: Show all */}
          <div className="flex space-x-1">
            {/* Mobile: Dropdown mode selector */}
            <div className="sm:hidden relative" ref={modeDropdownRef}>
              <button
                onClick={() => setShowMobileModeDropdown(!showMobileModeDropdown)}
                className="p-1.5 rounded-md bg-green-600 text-white shadow-lg flex items-center space-x-1"
                title={clinicalModes[selectedClinicalMode].label}
              >
                {React.createElement(clinicalModes[selectedClinicalMode].icon, { className: "w-3 h-3" })}
                <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>
              
              {/* Mobile Dropdown Menu */}
              {showMobileModeDropdown && (
                <div className="absolute top-full right-0 mt-1 bg-gray-800 border border-gray-600 rounded-md shadow-lg z-50 min-w-48">
                  {Object.entries(clinicalModes).map(([key, mode]) => {
                    const IconComponent = mode.icon;
                    return (
                      <button
                        key={key}
                        onClick={() => {
                          setSelectedClinicalMode(key);
                          setShowMobileModeDropdown(false);
                        }}
                        className={`w-full flex items-center space-x-2 px-3 py-2 text-left hover:bg-gray-700 transition-colors ${
                          selectedClinicalMode === key
                            ? 'bg-green-600 text-white'
                            : 'text-gray-300'
                        }`}
                      >
                        <IconComponent className="w-4 h-4" />
                        <span className="text-sm">{mode.label}</span>
                      </button>
                    );
                  })}
                </div>
              )}
            </div>
            
            {/* Desktop: Show all modes */}
            <div className="hidden sm:flex space-x-1">
              {Object.entries(clinicalModes).map(([key, mode]) => {
                const IconComponent = mode.icon;
                return (
                  <button
                    key={key}
                    onClick={() => setSelectedClinicalMode(key)}
                    className={`p-2 rounded-md transition-colors ${
                      selectedClinicalMode === key
                        ? 'bg-green-600 text-white shadow-lg'
                        : 'text-gray-400 hover:text-gray-300 hover:bg-gray-700'
                    }`}
                    title={mode.label}
                  >
                    <IconComponent className="w-4 h-4" />
                  </button>
                );
              })}
            </div>
          </div>
        </div>
        
        {/* Active Mode Indicator */}
        <div className="mt-2">
          <div className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-gray-700 text-gray-300">
            {React.createElement(clinicalModes[selectedClinicalMode].icon, { className: "w-3 h-3 mr-1" })}
            {clinicalModes[selectedClinicalMode].label}
          </div>
        </div>
      </div>

      {/* Chat Output Area - SCROLLABLE MIDDLE SECTION (matching original layout) */}
      <div 
        className="absolute left-0 right-0 bg-[#1a1a1a] transition-all duration-300 ease-in-out"
        style={{ 
          top: '100px', // Increased from 16 to account for header + mode indicator
          overflowY: 'auto',
          overflowX: 'hidden',
          WebkitOverflowScrolling: 'touch',
          bottom: showActionButtons ? '100px' : '70px', // Same as original
          height: 'auto'
        }}
      >
        <div className="max-w-4xl mx-auto">
          {/* Welcome Message */}
          {messages.length === 1 && ( // Only show when just the welcome message exists
            <div className="px-4 py-8 text-center">
              <div className="max-w-md mx-auto">
                <div className="w-12 h-12 bg-green-600 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Stethoscope className="w-6 h-6 text-white" />
                </div>
                <h2 className="text-lg font-medium text-white mb-2">AI Clinical Assistant</h2>
                <p className="text-sm text-gray-400 mb-4">
                  I'm your intelligent clinical decision support assistant. I can help with drug interactions, vital signs analysis, differential diagnosis, and clinical note processing.
                </p>
                {onBackToMainChat && (
                  <p className="text-xs text-gray-500 mb-4">
                    💡 Tip: Use the ← back button in the header to return to your main chatbot anytime
                  </p>
                )}
              </div>
            </div>
          )}

          {/* Chat Messages */}
          {messages.map((message) => (
            <div key={message.id} className="px-4 py-2 bg-[#1a1a1a]">
              <div className="flex space-x-3">
                <div className={`w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0 shadow-lg ${
                  message.isAI ? 'bg-green-600' : 'bg-blue-600'
                }`}>
                  {message.isAI ? (
                    <Stethoscope className="w-4 h-4 text-white" />
                  ) : (
                    <User className="w-4 h-4 text-white" />
                  )}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center space-x-2 mb-1">
                    <span className="text-sm font-medium text-white">
                      {message.isAI ? 'AI Clinical Assistant' : 'You'}
                    </span>
                    <span className="text-xs text-gray-500">
                      {message.timestamp.toLocaleTimeString()}
                    </span>
                    {message.clinicalMode && message.clinicalMode !== 'general' && (
                      <span className="px-2 py-0.5 rounded text-xs bg-gray-700 text-gray-300">
                        {clinicalModes[message.clinicalMode]?.label || message.clinicalMode}
                      </span>
                    )}
                  </div>
                  <div className={`text-sm leading-relaxed ${
                    message.isError ? 'text-red-400' : 'text-gray-300'
                  }`}>
                    <div 
                      className="whitespace-pre-wrap break-words"
                      dangerouslySetInnerHTML={{
                        __html: message.content.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>').replace(/\n/g, '<br/>')
                      }}
                    />
                  </div>
                </div>
              </div>
            </div>
          ))}
          
          {/* Loading indicator (matching original style) */}
          {isLoading && (
            <div className="px-4 py-2 bg-[#1a1a1a]">
              <div className="flex space-x-3">
                <div className="w-7 h-7 bg-green-600 rounded-full flex items-center justify-center flex-shrink-0 shadow-lg">
                  <div className="w-3 h-3 border border-gray-400 border-t-white rounded-full animate-spin"></div>
                </div>
                <div className="flex-1 min-w-0">
                  <div className="mb-1">
                    <span className="text-xs text-gray-500 italic">Processing clinical request...</span>
                  </div>
                  <div className="flex items-center space-x-2 text-gray-300 mb-1">
                    <span className="text-green-400">🧠</span>
                    <span className="text-xs text-gray-400">AI Clinical Analysis</span>
                  </div>
                </div>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Chat Input Area - FIXED AT BOTTOM (matching original layout exactly) */}
      <div 
        className={`fixed bottom-0 left-0 right-0 bg-[#1a1a1a] border-t border-gray-700 px-4 z-30 transition-all duration-300 ease-in-out ${
          showActionButtons ? 'py-2' : 'py-1'
        }`}
        style={{ 
          paddingBottom: 'max(8px, env(safe-area-inset-bottom, 0px))',
          position: 'fixed',
          bottom: '0',
          transform: 'translateZ(0)',
          willChange: 'transform'
        }}
      >
        <div className="max-w-4xl mx-auto">
          {/* Action Buttons - Inside Input Container (matching original) */}
          {showActionButtons && (
            <div className="mb-3 transition-all duration-300 ease-in-out">
              {/* Desktop: 1 row 4 columns, Mobile: 2 rows 2 columns */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-1.5 sm:gap-2">
                {quickActions.map((action, index) => (
                  <button
                    key={index}
                    onClick={() => handleQuickAction(action)}
                    className="flex items-center justify-center bg-[#2a2a2a] hover:bg-[#333] text-white rounded-md sm:rounded-lg px-1.5 sm:px-2 py-1.5 sm:py-2 transition-colors text-xs border border-gray-600 hover:border-gray-500 min-h-[40px] sm:min-h-[44px]"
                    title={action.text}
                  >
                    <action.icon className="w-3 h-3 mr-1 flex-shrink-0" />
                    <span className="font-medium truncate text-xs sm:text-sm">{action.text}</span>
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Input Section (matching original layout exactly) */}
          <div className="pb-2">
            <div className="bg-[#2a2a2a] rounded-lg border border-gray-600 focus-within:ring-2 focus-within:ring-green-500 focus-within:border-transparent flex items-end p-2 space-x-2">
              {/* Left Side - Textarea */}
              <textarea
                ref={inputRef}
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder={`Enter your ${clinicalModes[selectedClinicalMode].label.toLowerCase()} request...`}
                disabled={isLoading}
                className="flex-1 bg-transparent text-white placeholder-gray-400 focus:outline-none text-sm resize-none overflow-y-auto"
                style={{
                  WebkitAppearance: 'none',
                  fontSize: '14px',
                  maxHeight: '120px',
                  height: '40px',
                  WebkitTouchCallout: 'none',
                  WebkitUserSelect: 'text',
                  WebkitTapHighlightColor: 'transparent'
                }}
                autoComplete="off"
                autoCorrect="off"
                autoCapitalize="sentences"
                spellCheck="true"
                rows={1}
              />
              
              {/* Right Side - Send Button (circular like original) */}
              <div className="flex items-center">
                <button
                  onClick={() => {
                    handleSendMessage();
                  }}
                  disabled={!inputValue.trim() || isLoading}
                  className="w-7 h-7 sm:w-8 sm:h-8 bg-gray-600 hover:bg-gray-500 disabled:bg-gray-700 text-white rounded-full flex items-center justify-center transition-colors duration-200"
                  title="Send message"
                >
                  {isLoading ? (
                    <div className="w-2.5 h-2.5 sm:w-3 sm:h-3 border border-white border-t-transparent rounded-full animate-spin"></div>
                  ) : (
                    <svg className="w-3.5 h-3.5 sm:w-4 sm:h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 10l7-7m0 0l7 7m-7-7v18" />
                    </svg>
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AIClinicalChatbot;
