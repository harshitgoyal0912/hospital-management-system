import React, { useRef, useEffect } from 'react';
import { LogOut, User, Settings, Upload, FileText, History, CheckCircle, Plus, X, Mic, MicOff, VolumeX, BarChart3, Brain, Stethoscope, Database } from 'lucide-react';
import EnhancedMedicalDocumentUpload from './EnhancedMedicalDocumentUpload.jsx';
import MedicalHistoryViewer from './MedicalHistoryViewer.jsx';
import BulkDataUpload from './BulkDataUpload.jsx';

const HospitalChatInterface = ({
  // User and server info
  user,
  serverInfo,
  onLogout,
  
  // Chat state
  messages,
  isLoading,
  expandedThinking,
  setExpandedThinking,
  
  // Input handling
  inputMessage,
  setInputMessage,
  handleSendMessage,
  isConnected,
  
  // Action buttons
  showActionButtons,
  setShowActionButtons,
  smartFocusInput,
  
  // Plus menu
  showPlusMenu,
  setShowPlusMenu,
  plusMenuRef,
  setActiveTab,
  
  // Medical document functionality
  activeTab,
  selectedPatientId,
  setSelectedPatientId,
  selectedPatientNumber,
  setSelectedPatientNumber,
  searchingPatient,
  patientSearchResult,
  verifyPatient,
  searchPatientByNumber,
  
  // Voice functionality
  toggleVoiceInput,
  isListening,
  isRecording,
  isProcessingVoice,
  isSpeaking,
  microphoneAvailable,
  
  // Chat functionality
  aiMcpServiceRef,
  setMessages,
  setShowSetup,
  
  // Formatting functions
  formatMessageText,
  ThinkingDuration,
  
  // Mobile responsiveness
  inputRef,
  isIOSDevice
}) => {
  const messagesEndRef = useRef(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Auto-resize textarea based on content
  useEffect(() => {
    if (inputRef.current) {
      const textarea = inputRef.current;
      // Reset height to auto to get the correct scrollHeight
      textarea.style.height = 'auto';
      // Set height based on scrollHeight, with min and max constraints
      const newHeight = Math.min(Math.max(textarea.scrollHeight, 40), 120);
      textarea.style.height = newHeight + 'px';
    }
  }, [inputMessage]);

  // Reset textarea height when input is cleared (after sending message)
  useEffect(() => {
    if (inputRef.current && inputMessage === '') {
      inputRef.current.style.height = '40px';
    }
  }, [inputMessage]);

  // Handle mobile viewport height issues with keyboard
  useEffect(() => {
    const setVH = () => {
      const vh = window.innerHeight * 0.01;
      document.documentElement.style.setProperty('--vh', `${vh}px`);
    };

    setVH();
    window.addEventListener('resize', setVH);
    window.addEventListener('orientationchange', setVH);

    // Prevent body scroll on mobile when keyboard appears
    const handleFocusIn = () => {
      document.body.classList.add('no-scroll');
    };

    const handleFocusOut = () => {
      document.body.classList.remove('no-scroll');
    };

    // Add event listeners for input focus/blur
    document.addEventListener('focusin', handleFocusIn);
    document.addEventListener('focusout', handleFocusOut);

    return () => {
      window.removeEventListener('resize', setVH);
      window.removeEventListener('orientationchange', setVH);
      document.removeEventListener('focusin', handleFocusIn);
      document.removeEventListener('focusout', handleFocusOut);
      document.body.classList.remove('no-scroll');
    };
  }, []);

  return (
    <div className="bg-[#1a1a1a] flex flex-col text-white relative" style={{ 
      height: 'calc(var(--vh, 1vh) * 100)',
      maxHeight: 'calc(var(--vh, 1vh) * 100)',
      overflow: 'hidden'
    }}>
      {/* Claude-style Header - FIXED AT TOP */}
      <div className="fixed top-0 left-0 right-0 border-b border-gray-700 px-3 sm:px-4 py-3 bg-[#1a1a1a] z-30">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2 sm:space-x-3">
            <div className="w-6 h-6 sm:w-7 sm:h-7 bg-blue-600 rounded-full flex items-center justify-center text-white text-xs sm:text-sm font-medium shadow-lg">
              H
            </div>
            <div className="min-w-0 flex-1">
              <h1 className="text-sm font-medium text-white truncate">Hospital Agent</h1>
              {serverInfo && (
                <div className="text-xs text-gray-400">
                  {/* Desktop version - detailed */}
                  <div className="hidden sm:block">
                    <p className="mb-1">
                      Connected • {serverInfo.toolCount || 0} tools • {serverInfo.agentCount || 0} agents • {aiMcpServiceRef.current?.getConversationSummary?.()?.messageCount || 0} messages in memory
                    </p>
                  </div>
                  {/* Mobile version - compact */}
                  <div className="block sm:hidden">
                    <p>
                      {serverInfo.toolCount || 0} tools • {serverInfo.agentCount || 0} agents
                    </p>
                  </div>
                </div>
              )}
            </div>
          </div>
          
          {/* User Info and Actions - Responsive */}
          <div className="flex items-center space-x-1 sm:space-x-3">
            {/* User Profile */}
            <div className="flex items-center space-x-1 sm:space-x-2">
              <div className="w-5 h-5 sm:w-6 sm:h-6 bg-blue-600 rounded-full flex items-center justify-center">
                <span className="text-white text-xs font-medium">
                  {user?.fullName ? user.fullName.charAt(0).toUpperCase() : user?.email?.charAt(0).toUpperCase() || 'U'}
                </span>
              </div>
              <div className="hidden md:block">
                <p className="text-xs text-white font-medium">{user?.fullName || 'User'}</p>
                <p className="text-xs text-gray-400">{user?.role || 'Staff'}</p>
              </div>
            </div>

            {/* Action Buttons - Responsive with Mobile Menu */}
            <div className="flex items-center space-x-1">
              {/* Mobile: Show only essential buttons */}
              <div className="flex items-center space-x-1 sm:hidden">
                <button
                  onClick={() => setActiveTab('dashboard')}
                  className={`p-1.5 hover:bg-gray-700 rounded-md transition-colors ${
                    activeTab === 'dashboard' ? 'text-blue-400' : 'text-gray-400 hover:text-gray-300'
                  }`}
                  title="Dashboard"
                >
                  <BarChart3 className="w-4 h-4" />
                </button>
                <button
                  onClick={() => setActiveTab('ai-clinical')}
                  className={`p-1.5 hover:bg-gray-700 rounded-md transition-colors ${
                    activeTab === 'ai-clinical' ? 'text-green-400' : 'text-gray-400 hover:text-gray-300'
                  }`}
                  title="AI Clinical Assistant"
                >
                  <Stethoscope className="w-4 h-4" />
                </button>
                <button
                  onClick={onLogout}
                  className="p-1.5 text-gray-400 hover:text-red-400 hover:bg-gray-700 rounded-md transition-colors"
                  title="Logout"
                >
                  <LogOut className="w-4 h-4" />
                </button>
              </div>
              
              {/* Desktop: Show all buttons */}
              <div className="hidden sm:flex items-center space-x-1">
                <button
                  onClick={() => {
                    if (aiMcpServiceRef.current) {
                      aiMcpServiceRef.current.resetConversation();
                      setMessages(prev => [...prev, {
                        id: Date.now(),
                        text: '🔄 **Conversation Reset** - Memory cleared. Starting fresh!',
                        sender: 'ai',
                        timestamp: new Date().toLocaleTimeString()
                      }]);
                    }
                  }}
                  className="p-2 text-gray-400 hover:text-gray-300 hover:bg-gray-700 rounded-md transition-colors"
                  title="Reset conversation"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                  </svg>
                </button>
                <button
                  onClick={() => setActiveTab('dashboard')}
                  className={`p-2 hover:bg-gray-700 rounded-md transition-colors ${
                    activeTab === 'dashboard' ? 'text-blue-400' : 'text-gray-400 hover:text-gray-300'
                  }`}
                  title="Dashboard"
                >
                  <BarChart3 className="w-4 h-4" />
                </button>
                <button
                  onClick={() => setActiveTab('ai-clinical')}
                  className={`p-2 hover:bg-gray-700 rounded-md transition-colors ${
                    activeTab === 'ai-clinical' ? 'text-green-400' : 'text-gray-400 hover:text-gray-300'
                  }`}
                  title="AI Clinical Assistant"
                >
                  <Stethoscope className="w-4 h-4" />
                </button>
                <button
                  onClick={() => setShowSetup(true)}
                  className="p-2 text-gray-400 hover:text-gray-300 hover:bg-gray-700 rounded-md transition-colors"
                  title="Settings"
                >
                  <Settings className="w-4 h-4" />
                </button>
                <button
                  onClick={onLogout}
                  className="p-2 text-gray-400 hover:text-red-400 hover:bg-gray-700 rounded-md transition-colors"
                  title="Logout"
                >
                  <LogOut className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Chat Output Area - SCROLLABLE MIDDLE SECTION */}
      <div 
        className="absolute top-16 left-0 right-0 bg-[#1a1a1a] transition-all duration-300 ease-in-out"
        style={{ 
          overflowY: 'auto',
          overflowX: 'hidden',
          WebkitOverflowScrolling: 'touch',
          bottom: showActionButtons ? '100px' : '70px', // Much closer to input area
          height: 'auto'
        }}
      >
        <div className="max-w-4xl mx-auto">
          {/* Welcome Message */}
          {messages.length === 0 && (
            <div className="px-4 py-8 text-center">
              <div className="max-w-md mx-auto">
                <div className="w-12 h-12 bg-blue-600 rounded-full flex items-center justify-center mx-auto mb-4">
                  <span className="text-xl font-medium text-white">H</span>
                </div>
                <h2 className="text-lg font-medium text-white mb-2">Welcome to Hospital Assistant</h2>
                <p className="text-sm text-gray-400 mb-4">
                  I'm here to help you manage patients, beds, equipment, staff, and more. You can ask me questions or use the action buttons below to get started.
                </p>
              </div>
            </div>
          )}
          
          {/* Chat Messages */}
          {(() => {
            let timerAlreadyShown = false;
            return messages.map((message, index) => {
              // Only show timer for the first thinking message encountered
              const shouldShowTimer = message.isThinking && message.startTime && !timerAlreadyShown;
              if (shouldShowTimer) {
                timerAlreadyShown = true;
              }
              
              return (
              <div key={message.id} className={`px-2 sm:px-4 py-2 ${
                message.isThinking ? 'bg-[#1a1a1a]' : 
                message.isFinalAnswer ? 'bg-[#1a1a1a]' : 
                message.isError ? 'bg-[#1a1a1a]' : 'bg-[#1a1a1a]'
              }`}>
              {message.sender === 'user' ? (
                // User message - aligned to the right - Responsive
                <div className="flex justify-end">
                  <div className="max-w-[85%] sm:max-w-[80%]">
                    <div className="prose prose-sm max-w-none">
                      <div className={`whitespace-pre-wrap leading-relaxed text-xs sm:text-sm text-white rounded-2xl px-3 sm:px-4 py-2 ${
                        message.isVoiceInput ? 'bg-blue-700 border border-blue-500' : 'bg-slate-700'
                      }`}>
                        {message.isVoiceInput && (
                          <div className="flex items-center space-x-1 mb-1 text-blue-200">
                            <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 24 24">
                              <path d="M12 2c1.1 0 2 .9 2 2v6c0 1.1-.9 2-2 2s-2-.9-2-2V4c0-1.1.9-2 2-2zm5.3 6c0 3-2.5 5.1-5.3 5.1S6.7 11 6.7 8H5c0 3.4 2.7 6.2 6 6.7v3.3h2v-3.3c3.3-.5 6-3.3 6-6.7h-1.7z" />
                            </svg>
                            <span className="text-xs">Voice Input</span>
                          </div>
                        )}
                        <div dangerouslySetInnerHTML={{ __html: formatMessageText(message.text) }} />
                      </div>
                    </div>
                  </div>
                </div>
              ) : (
                // AI message - aligned to the left - Responsive
                <div className="flex space-x-2 sm:space-x-3">
                  <div className="w-6 h-6 sm:w-7 sm:h-7 bg-blue-600 rounded-full flex items-center justify-center flex-shrink-0 text-xs sm:text-sm font-medium text-white shadow-lg">
                    {message.isThinking ? (
                      <div className="w-2 h-2 sm:w-3 sm:h-3 border border-gray-400 border-t-white rounded-full animate-spin"></div>
                    ) : (
                      'H'
                    )}
                  </div>
                
                <div className="flex-1 min-w-0">
                  {message.isThinking && (
                    <div className="mb-1">
                      <button
                        onClick={() => setExpandedThinking(prev => ({
                          ...prev,
                          [message.id]: !prev[message.id]
                        }))}
                        className="flex items-center space-x-1 sm:space-x-2 text-xs text-gray-500 italic hover:text-gray-400 transition-colors w-full justify-between"
                      >
                        <div className="flex items-center space-x-1 sm:space-x-2 min-w-0">
                          <span className="text-gray-400">🔧</span>
                          <span className="font-mono text-blue-400 truncate">
                            {message.toolFunction || 'thinking'} 
                            {expandedThinking[message.id]}
                          </span>
                        </div>
                        <span className="ml-auto flex items-center space-x-1 flex-shrink-0">
                          {/* Only show timer for the very first thinking message */}
                          {message.isThinking && message.startTime && shouldShowTimer && (
                            <ThinkingDuration startTime={message.startTime} />
                          )}
                          <svg 
                            className={`w-3 h-3 transform transition-transform ${expandedThinking[message.id] ? 'rotate-180' : ''}`} 
                            fill="none" 
                            stroke="currentColor" 
                            viewBox="0 0 24 24"
                          >
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                          </svg>
                        </span>
                      </button>
                      {expandedThinking[message.id] && (
                        <div className="mt-2 text-xs sm:text-sm text-gray-300 pl-4 sm:pl-6 bg-gray-800/30 rounded-lg p-3 border-l-2 border-blue-500">
                          <div className="text-blue-400 text-xs mb-2 font-medium">🔧 Tool Details:</div>
                          <div dangerouslySetInnerHTML={{ __html: formatMessageText(message.text) }} />
                        </div>
                      )}
                    </div>
                  )}
                  
                  {/* Tool Call Display */}
                  {message.isToolCall && (
                    <div className="mb-2">
                      <div className="flex items-center space-x-2 text-xs text-gray-400 mb-1">
                        <span className="text-blue-400">🔧</span>
                        <span>Tool Execution</span>
                      </div>
                    </div>
                  )}
                  
                  <div className="prose prose-sm max-w-none">
                    {!message.isThinking && (
                      <div 
                        className={`whitespace-pre-wrap leading-relaxed text-sm ${
                          message.isThinking ? 'text-gray-300' :
                          message.isFinalAnswer ? 'text-white' :
                          message.isError ? 'text-red-400' :
                          message.isToolCall ? 'text-blue-200 bg-gray-800 p-3 rounded-lg border-l-2 border-blue-500' :
                          'text-white'
                        }`}
                        dangerouslySetInnerHTML={{
                          __html: formatMessageText(message.text)
                        }}
                      />
                    )}
                  </div>
                </div>
              </div>
              )}
            </div>
            );
          });
          })()}
          
          {/* Loading indicator */}
          {isLoading && (
            <div className="px-4 py-2 bg-[#1a1a1a]">
              <div className="flex space-x-3">
                <div className="w-7 h-7 bg-blue-600 rounded-full flex items-center justify-center flex-shrink-0 shadow-lg">
                  <div className="w-3 h-3 border border-gray-400 border-t-white rounded-full animate-spin"></div>
                </div>
                <div className="flex-1 min-w-0">
                  <div className="mb-1">
                    <button
                      onClick={() => setExpandedThinking(prev => ({
                        ...prev,
                        ['loading']: !prev['loading']
                      }))}
                      className="flex items-center space-x-2 text-xs text-gray-500 italic hover:text-gray-400 transition-colors"
                    >
                      <span>Processing your request...</span>
                      <span className="ml-auto flex items-center space-x-1">
                        {/* Remove the timer from loading indicator - it's just for processing */}
                        <svg 
                          className={`w-3 h-3 transform transition-transform ${expandedThinking['loading'] ? 'rotate-180' : ''}`} 
                          fill="none" 
                          stroke="currentColor" 
                          viewBox="0 0 24 24"
                        >
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                        </svg>
                      </span>
                    </button>
                  </div>
                  <div className="flex items-center space-x-2 text-gray-300 mb-1">
                    <span className="text-blue-400">🔍</span>
                    <span className="text-xs text-gray-400">Request Analysis</span>
                  </div>
                  {expandedThinking['loading'] && (
                    <div className="text-sm text-gray-300">
                      Analyzing your request and determining the best approach...
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Chat Input Area - FIXED AT BOTTOM */}
      <div 
        className={`fixed bottom-0 left-0 right-0 bg-[#1a1a1a] border-t border-gray-700 px-4 z-30 transition-all duration-300 ease-in-out ${
          showActionButtons ? 'py-2' : 'py-1'
        }`}
        style={{ 
          paddingBottom: 'max(8px, env(safe-area-inset-bottom, 0px))',
          position: 'fixed',
          bottom: '0',
          transform: 'translateZ(0)', // Force hardware acceleration
          willChange: 'transform'
        }}
      >
        <div className="max-w-4xl mx-auto">
          {/* Action Buttons - Inside Input Container */}
          {showActionButtons && (
            <div className="mb-3 transition-all duration-300 ease-in-out">
              {/* Desktop: 1 row 4 columns, Mobile: 2 rows 2 columns */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                {/* View All Patients */}
                <button
                  onClick={() => {
                    setInputMessage("List all patients");
                    smartFocusInput(100);
                  }}
                  className="flex items-center justify-center bg-[#2a2a2a] hover:bg-[#333] text-white rounded-md sm:rounded-lg px-2 py-2 transition-colors text-xs border border-gray-600 hover:border-gray-500"
                  title="View all patients"
                >
                  <span className="font-medium whitespace-nowrap">View Patients</span>
                </button>

                {/* Check Bed Status */}
                <button
                  onClick={() => {
                    setInputMessage("Show bed availability");
                    smartFocusInput(100);
                  }}
                  className="flex items-center justify-center bg-[#2a2a2a] hover:bg-[#333] text-white rounded-md sm:rounded-lg px-2 py-2 transition-colors text-xs border border-gray-600 hover:border-gray-500"
                  title="Check bed availability"
                >
                  <span className="font-medium whitespace-nowrap">Bed Status</span>
                </button>

                {/* Emergency Alert */}
                <button
                  onClick={() => {
                    setInputMessage("Show emergency status and available emergency beds");
                    smartFocusInput(100);
                  }}
                  className="flex items-center justify-center bg-[#2a2a2a] hover:bg-[#333] text-white rounded-md sm:rounded-lg px-2 py-2 transition-colors text-xs border border-gray-600 hover:border-gray-500"
                  title="Emergency status"
                >
                  <span className="font-medium whitespace-nowrap">Emergency</span>
                </button>

                {/* Quick Stats */}
                <button
                  onClick={() => {
                    setInputMessage("Show hospital overview with current stats");
                    smartFocusInput(100);
                  }}
                  className="flex items-center justify-center bg-[#2a2a2a] hover:bg-[#333] text-white rounded-md sm:rounded-lg px-2 py-2 transition-colors text-xs border border-gray-600 hover:border-gray-500"
                  title="Hospital overview"
                >
                  <span className="font-medium whitespace-nowrap">Overview</span>
                </button>
              </div>
            </div>
          )}
          <div className="flex items-center space-x-2 bg-[#2a2a2a] rounded-lg px-3 py-2 border border-gray-600 focus-within:border-blue-500">
            {/* Left Side - Plus Menu */}
            <div className="flex items-center">
              <div className="relative" ref={plusMenuRef}>
                <button
                  onClick={() => setShowPlusMenu(!showPlusMenu)}
                  className="text-gray-400 hover:text-white transition-colors p-1"
                  title="Upload documents or view medical history"
                >
                  <Plus className="w-4 h-4" />
                </button>
                
                {showPlusMenu && (
                  <div className="absolute bottom-full left-0 mb-2 bg-[#2a2a2a] border border-gray-600 rounded-lg shadow-lg min-w-44 sm:min-w-48 z-50">
                    <button
                      onClick={() => {
                        setActiveTab('upload');
                        setShowPlusMenu(false);
                      }}
                      className="w-full text-left px-2 sm:px-3 py-2 text-xs sm:text-sm text-white hover:bg-gray-700 rounded-t-lg flex items-center space-x-2"
                    >
                      <Upload className="w-3 h-3 sm:w-4 sm:h-4" />
                      <span>Upload Documents</span>
                    </button>
                    <button
                      onClick={() => {
                        setActiveTab('history');
                        setShowPlusMenu(false);
                      }}
                      className="w-full text-left px-2 sm:px-3 py-2 text-xs sm:text-sm text-white hover:bg-gray-700 border-t border-gray-600 flex items-center space-x-2"
                    >
                      <History className="w-3 h-3 sm:w-4 sm:h-4" />
                      <span>Medical History</span>
                    </button>
                    <button
                      onClick={() => {
                        setActiveTab('bulk-data');
                        setShowPlusMenu(false);
                      }}
                      className="w-full text-left px-2 sm:px-3 py-2 text-xs sm:text-sm text-white hover:bg-gray-700 rounded-b-lg border-t border-gray-600 flex items-center space-x-2"
                    >
                      <Database className="w-3 h-3 sm:w-4 sm:h-4" />
                      <span>Add Data</span>
                    </button>
                  </div>
                )}
              </div>
            </div>
            
            {/* Middle - Multi-line Text Input */}
            <textarea
              ref={inputRef}
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyDown={(e) => {
                // Check if it's a mobile device
                const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) ||
                                (window.innerWidth <= 768) || 
                                ('ontouchstart' in window);
                
                if (e.key === 'Enter' && !e.shiftKey) {
                  if (isMobile) {
                    // On mobile: Enter key creates new line, don't send message
                    // Let the default behavior happen (new line)
                    return;
                  } else {
                    // On desktop: Enter sends message, Shift+Enter creates new line
                    e.preventDefault();
                    handleSendMessage();
                  }
                }
                // Shift+Enter always creates new line on both mobile and desktop
              }}
              onFocus={() => setShowActionButtons(true)}
              onBlur={() => {
                // Hide action buttons when keyboard is dismissed, with small delay
                setTimeout(() => setShowActionButtons(false), 150);
              }}
              placeholder={isConnected ? "Ask about patients, beds, staff, equipment..." : "Connecting..."}
              disabled={!isConnected || isLoading}
              className="flex-1 bg-transparent text-white placeholder-gray-400 focus:outline-none text-sm resize-none overflow-y-auto"
              style={{
                WebkitAppearance: 'none',
                fontSize: isIOSDevice ? '16px' : '14px',
                maxHeight: '120px',
                height: '40px', // Initial height
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
            
            {/* Right Side - Send Button */}
            <div className="flex items-center">
              {/* Microphone Button */}
              <button
                onClick={toggleVoiceInput}
                disabled={!isConnected || isLoading || isProcessingVoice || microphoneAvailable === false}
                className={`transition-colors duration-200 p-1 ${
                  microphoneAvailable === false
                    ? "text-gray-500 cursor-not-allowed opacity-50"
                    : isListening || isRecording
                    ? "text-red-400 hover:text-red-300 animate-pulse"
                    : isProcessingVoice
                    ? "text-yellow-400 hover:text-yellow-300 animate-pulse"
                    : isSpeaking
                    ? "text-blue-400 hover:text-blue-300 animate-pulse"
                    : "text-gray-400 hover:text-white disabled:text-gray-600"
                }`}
                title={
                  microphoneAvailable === false
                    ? "Microphone not available (requires HTTPS connection and permissions)"
                    : microphoneAvailable === null
                    ? "Checking microphone availability..."
                    : isListening || isRecording
                    ? "Recording... (Click to stop)"
                    : isProcessingVoice
                    ? "Processing voice input..."
                    : isSpeaking
                    ? "AI is speaking... (Click to stop)"
                    : "Start voice input (OpenAI Whisper)"
                }
              >
                {microphoneAvailable === false ? (
                  <svg className="w-4 h-4 sm:w-5 sm:h-5" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M19 11h-1.7c0 .74-.16 1.43-.43 2.05l1.23 1.23c.56-.98.9-2.09.9-3.28zm-4.02.17c0-.06.02-.11.02-.17V4c0-1.66-1.34-3-3-3S9 2.34 9 4v.18l5.98 5.99zM4.27 3L3 4.27l6.01 6.01V11c0 1.66 1.33 3 2.99 3 .22 0 .44-.03.65-.08l1.66 1.66c-.71.33-1.5.52-2.31.52-2.76 0-5.3-2.1-5.3-5.1H5c0 3.41 2.72 6.23 6 6.72V21h2v-3.28c.91-.13 1.77-.45 2.54-.9L19.73 21 21 19.73 4.27 3z"/>
                  </svg>
                ) : isListening || isRecording ? (
                  <svg className="w-4 h-4 sm:w-5 sm:h-5" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M6 6h12v12H6z" />
                  </svg>
                ) : isProcessingVoice ? (
                  <svg className="w-4 h-4 sm:w-5 sm:h-5 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                  </svg>
                ) : isSpeaking ? (
                  <svg className="w-4 h-4 sm:w-5 sm:h-5" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M3 9v6h4l5 5V4L7 9H3zm13.5 3c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02zM14 3.23v2.06c2.89.86 5 3.54 5 6.71s-2.11 5.85-5 6.71v2.06c4.01-.91 7-4.49 7-8.77s-2.99-7.86-7-8.77z" />
                  </svg>
                ) : (
                  <svg className="w-4 h-4 sm:w-5 sm:h-5" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M12 2c1.1 0 2 .9 2 2v6c0 1.1-.9 2-2 2s-2-.9-2-2V4c0-1.1.9-2 2-2zm5.3 6c0 3-2.5 5.1-5.3 5.1S6.7 11 6.7 8H5c0 3.4 2.7 6.2 6 6.7v3.3h2v-3.3c3.3-.5 6-3.3 6-6.7h-1.7z" />
                  </svg>
                )}
              </button>
              
              {/* Send Button - Circular */}
              <button
                onClick={() => {
                  handleSendMessage();
                  setShowActionButtons(false); // Hide action buttons after sending
                }}
                disabled={!isConnected || isLoading || !inputMessage.trim()}
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
      
      {/* Upload Documents Tab */}
      {activeTab === 'upload' && (
        <div className="fixed inset-0 bg-[#1a1a1a] z-40 flex flex-col overflow-y-auto">
          <div className="flex-1 p-3 sm:p-6">
            <div className="max-w-4xl mx-auto">
              <div className="mb-4 sm:mb-6">
                {/* Back to Chat Button */}
                <button
                  onClick={() => setActiveTab('chat')}
                  className="mb-4 flex items-center space-x-2 text-gray-400 hover:text-white transition-colors"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                  </svg>
                  <span>Back to Chat</span>
                </button>
                
                <h2 className="text-xl sm:text-2xl font-bold text-white mb-2">Upload Medical Documents</h2>
                <p className="text-sm sm:text-base text-gray-400">Upload patient medical documents for AI-powered analysis and history tracking.</p>
              </div>
              
              {/* Patient Selection */}
              <div className="mb-4 sm:mb-6">
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Select Patient by Patient Number
                </label>
                <div className="flex flex-col sm:flex-row space-y-3 sm:space-y-0 sm:space-x-4">
                  <input
                    type="text"
                    placeholder="Enter Patient Number (e.g., P123456)"
                    value={selectedPatientNumber}
                    onChange={(e) => setSelectedPatientNumber(e.target.value.toUpperCase())}
                    className="flex-1 p-3 bg-[#2a2a2a] border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm sm:text-base"
                    onKeyPress={(e) => e.key === 'Enter' && verifyPatient()}
                  />
                  <button
                    onClick={verifyPatient}
                    disabled={searchingPatient || !selectedPatientNumber.trim()}
                    className="bg-blue-600 text-white px-4 sm:px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center text-sm sm:text-base whitespace-nowrap"
                  >
                    {searchingPatient ? (
                      <>
                        <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>
                        Searching...
                      </>
                    ) : (
                      'Verify Patient'
                    )}
                  </button>
                </div>
                
                {/* Patient Search Result */}
                {patientSearchResult && (
                  <div className="mt-3 p-3 bg-green-900/20 border border-green-500/30 rounded-lg">
                    <div className="flex items-center text-green-400">
                      <CheckCircle className="w-4 h-4 sm:w-5 sm:h-5 mr-2" />
                      <span className="font-medium text-sm sm:text-base">Patient Found:</span>
                    </div>
                    <div className="mt-1 text-xs sm:text-sm text-gray-300 space-y-1">
                      <p><strong>Name:</strong> {patientSearchResult.name}</p>
                      <p><strong>Patient Number:</strong> {patientSearchResult.patient_number}</p>
                      <p><strong>Email:</strong> {patientSearchResult.patient.email || 'Not provided'}</p>
                      <p><strong>Phone:</strong> {patientSearchResult.patient.phone || 'Not provided'}</p>
                    </div>
                  </div>
                )}
                
                <p className="text-xs text-gray-500 mt-2">
                  Enter the patient number (like P123456) to verify the patient exists before uploading documents.
                </p>
              </div>

              {/* Enhanced Document Upload Component */}
              {selectedPatientId && (
                <EnhancedMedicalDocumentUpload 
                  patientId={selectedPatientId}
                  onUploadComplete={(results) => {
                    console.log('Documents uploaded:', results);
                    // Show success message and potentially switch to history tab
                    setMessages(prev => [...prev, {
                      id: Date.now(),
                      type: 'assistant',
                      content: `✅ Successfully uploaded ${results.length} medical document(s) for patient ${patientSearchResult?.name} (${patientSearchResult?.patient_number}). ${results.map(r => `\n• ${r.fileName}: ${r.entitiesCount} entities extracted`).join('')}`,
                      timestamp: new Date()
                    }]);
                  }}
                />
              )}

              {!selectedPatientId && (
                <div className="text-center text-gray-500 py-8 sm:py-12">
                  <Upload className="w-12 h-12 sm:w-16 sm:h-16 mx-auto mb-4" />
                  <p className="text-base sm:text-lg font-medium">Enter a Patient Number to start uploading documents</p>
                  <p className="text-xs sm:text-sm">Search for the patient by their patient number (like P123456) before uploading medical documents.</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Medical History Tab */}
      {activeTab === 'history' && (
        <div className="fixed inset-0 bg-[#1a1a1a] z-40 flex flex-col overflow-y-auto">
          <div className="flex-1 p-3 sm:p-6">
            <div className="max-w-4xl mx-auto">
              <div className="mb-4 sm:mb-6">
                {/* Back to Chat Button */}
                <button
                  onClick={() => setActiveTab('chat')}
                  className="mb-4 flex items-center space-x-2 text-gray-400 hover:text-white transition-colors"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                  </svg>
                  <span>Back to Chat</span>
                </button>
                
                <h2 className="text-xl sm:text-2xl font-bold text-white mb-2">Medical History</h2>
                <p className="text-sm sm:text-base text-gray-400">View comprehensive medical history extracted from uploaded documents.</p>
              </div>
              
              {/* Patient Selection for History */}
              <div className="mb-4 sm:mb-6">
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  View History for Patient
                </label>
                <div className="flex flex-col sm:flex-row space-y-3 sm:space-y-0 sm:space-x-4">
                  <input
                    type="text"
                    placeholder="Enter Patient Number (e.g., P123456)"
                    value={selectedPatientNumber}
                    onChange={(e) => setSelectedPatientNumber(e.target.value.toUpperCase())}
                    className="flex-1 p-3 bg-[#2a2a2a] border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm sm:text-base"
                    onKeyPress={(e) => e.key === 'Enter' && verifyPatient()}
                  />
                  <button
                    onClick={verifyPatient}
                    disabled={searchingPatient || !selectedPatientNumber.trim()}
                    className="bg-blue-600 text-white px-4 sm:px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center text-sm sm:text-base whitespace-nowrap"
                  >
                    {searchingPatient ? (
                      <>
                        <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>
                        Searching...
                      </>
                    ) : (
                      'Find Patient'
                    )}
                  </button>
                </div>
                
                {/* Patient Search Result */}
                {patientSearchResult && (
                  <div className="mt-3 p-3 bg-green-900/20 border border-green-500/30 rounded-lg">
                    <div className="flex items-center text-green-400">
                      <CheckCircle className="w-4 h-4 sm:w-5 sm:h-5 mr-2" />
                      <span className="font-medium text-sm sm:text-base">Viewing history for:</span>
                    </div>
                    <div className="mt-1 text-xs sm:text-sm text-gray-300">
                      <p><strong>{patientSearchResult.name}</strong> ({patientSearchResult.patient_number})</p>
                    </div>
                  </div>
                )}
              </div>

              {/* Medical History Component */}
              {selectedPatientId && (
                <MedicalHistoryViewer patientId={selectedPatientId} />
              )}

              {!selectedPatientId && (
                <div className="text-center text-gray-500 py-8 sm:py-12">
                  <FileText className="w-12 h-12 sm:w-16 sm:h-16 mx-auto mb-4" />
                  <p className="text-base sm:text-lg font-medium">Enter a Patient ID to view medical history</p>
                  <p className="text-xs sm:text-sm">Access comprehensive medical records and AI-extracted insights.</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Bulk Data Upload Modal */}
      {activeTab === 'bulk-data' && (
        <BulkDataUpload
          onClose={() => setActiveTab('chat')}
          onUploadComplete={(tableType, result) => {
            setActiveTab('chat');
            // Add a success message to chat
            if (setMessages) {
              const successMessage = {
                id: Date.now(),
                content: `✅ Successfully uploaded ${result.inserted} records to ${tableType} table via bulk CSV upload.`,
                sender: 'ai',
                timestamp: new Date().toLocaleTimeString()
              };
              setMessages(prev => [...prev, successMessage]);
            }
          }}
        />
      )}
    </div>
  );
};

export default HospitalChatInterface;
