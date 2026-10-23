import React, { useState, useEffect, useRef } from 'react';
import DirectAIMCPService from '../services/directAiMcpService.js';
import PDFDownloadManager from '../utils/pdfDownloadManager.js';

const HospitalAssistant = () => {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [showSetup, setShowSetup] = useState(true);
  const [generatedReports, setGeneratedReports] = useState([]);
  
  // Configuration state
  const [openaiApiKey, setOpenaiApiKey] = useState(import.meta.env.VITE_OPENAI_API_KEY || '');
  const [mcpServerConfig, setMcpServerConfig] = useState({
    command: 'python',
    args: ['comprehensive_server.py'],
    cwd: './backend-python',
    env: {}
  });
  
  const [connectionError, setConnectionError] = useState('');
  const [serverInfo, setServerInfo] = useState(null);

  // Refs for services
  const aiMcpServiceRef = useRef(null);
  const messagesEndRef = useRef(null);
  const pdfManagerRef = useRef(null);

  // Initialize PDF manager
  useEffect(() => {
    if (!pdfManagerRef.current) {
      pdfManagerRef.current = new PDFDownloadManager();
    }
  }, []);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const initializeService = async () => {
    if (!openaiApiKey.trim()) {
      setConnectionError('OpenAI API key is required');
      return;
    }

    setIsLoading(true);
    setConnectionError('');

    try {
      console.log('🚀 Initializing Hospital Assistant...');
      
      aiMcpServiceRef.current = new DirectAIMCPService();
      await aiMcpServiceRef.current.initialize(openaiApiKey, mcpServerConfig);
      
      const info = aiMcpServiceRef.current.mcpClient.getServerInfo();
      setServerInfo(info);
      setIsConnected(true);
      setShowSetup(false);
      
      setMessages([{
        id: Date.now(),
        text: `🎯 **Hospital Assistant Ready!**\n\n✅ Connected to ${info.name} v${info.version}\n🔧 Available Tools: ${info.toolCount}\n\nI can help you with:\n• 👥 **Patient Management** - Create, search, update patient records\n• 📅 **Appointments** - Schedule and manage appointments\n• 🏥 **Bed Management** - Assign and track bed occupancy\n• 👨‍⚕️ **Staff Operations** - Manage staff assignments and schedules\n• 📋 **Reports** - Generate discharge reports and documents\n• 💊 **Supplies & Equipment** - Track medical supplies and equipment\n• 📊 **Data & Analytics** - Hospital statistics and insights\n\nWhat would you like to do?`,
        sender: 'ai',
        timestamp: new Date().toLocaleTimeString()
      }]);
      
    } catch (error) {
      console.error('❌ Connection failed:', error);
      setConnectionError(error.message);
    } finally {
      setIsLoading(false);
    }
  };

  const sendMessage = async () => {
    if (!inputMessage.trim() || isLoading || !aiMcpServiceRef.current) return;

    const userMessage = {
      id: Date.now(),
      text: inputMessage,
      sender: 'user',
      timestamp: new Date().toLocaleTimeString()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);

    try {
      // DirectAIMCPService exposes processRequest(), not sendMessage()
      const serviceResp = await aiMcpServiceRef.current.processRequest(inputMessage);
      const responseText = serviceResp?.message || serviceResp?.error || '';

      // Improved file name & report number extraction
      let reportNumberFromFile = null;
      const fileNameLineMatch = responseText.match(/File Name:\*\*?[^\n]*?([A-Z0-9_-]+\.pdf)/i);
      if (fileNameLineMatch) {
        const fileName = fileNameLineMatch[1];
        const coreMatch = fileName.match(/(DR-\d{8}-[A-F0-9]{8})/i);
        if (coreMatch) reportNumberFromFile = coreMatch[1];
      }
      const reportNumberRegexMatch = responseText.match(/DR-\d{8}-[A-F0-9]{8}/i);
      const finalReportNumber = reportNumberFromFile || reportNumberRegexMatch?.[0] || null;

      const reportNumberMatch = finalReportNumber ? [null, finalReportNumber] : null;
      const hasDownloadButton = !!finalReportNumber;

      const aiMessage = {
        id: Date.now() + 1,
        text: responseText,
        sender: 'ai',
        timestamp: new Date().toLocaleTimeString(),
        hasDownload: hasDownloadButton,
        reportNumber: hasDownloadButton ? finalReportNumber : null
      };

      setMessages(prev => [...prev, aiMessage]);
      
      if (hasDownloadButton) {
        setGeneratedReports(prev => [...prev, reportNumberMatch[1]]);
        console.log(`📄 New report generated: ${reportNumberMatch[1]}`);
      }
      
    } catch (error) {
      console.error('❌ Message error:', error);
      
      const errorMessage = {
        id: Date.now() + 1,
        text: `❌ **Error:** ${error.message}\n\nPlease check:\n- Server connection\n- OpenAI API key\n- Backend server status`,
        sender: 'ai',
        timestamp: new Date().toLocaleTimeString(),
        isError: true
      };
      
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const handleDownloadPDF = async (reportNumber) => {
    if (!reportNumber) {
      console.error('❌ No report number provided for download');
      return;
    }

    console.log(`📥 Download request for report: ${reportNumber}`);
    setIsLoading(true);

    try {
      // Extract patient name from recent messages
      let patientName = 'Unknown Patient';
      const recentMessages = messages.slice(-5);
      for (const msg of recentMessages) {
        const nameMatch = msg.text.match(/(?:patient|name):\s*([A-Za-z\s]+)/i);
        if (nameMatch) {
          patientName = nameMatch[1].trim();
          break;
        }
      }

      // Always local now
      await handleLocalFileDownload(reportNumber, patientName);

    } catch (error) {
      console.error('❌ Download error:', error);
      setMessages(prev => [...prev, {
        id: Date.now(),
        text: `❌ **Download Failed:** ${error.message}` ,
        sender: 'ai',
        timestamp: new Date().toLocaleTimeString(),
        isError: true
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleLocalFileDownload = async (reportNumber, patientName) => {
    try {
      console.log('📥 Starting PDF download for report:', reportNumber);
      
      // Direct call to our Node.js backend endpoint that handles PDF generation
      const endpointUrl = `http://localhost:3001/reports/discharge/download/${reportNumber}.pdf`;
      console.log('📡 Fetching from:', endpointUrl);
      
      const response = await fetch(endpointUrl, {
        method: 'GET',
        headers: {
          'Accept': 'application/pdf'
        }
      });

      if (!response.ok) {
        let errorMsg = `Server responded ${response.status}`;
        try {
          const errorData = await response.json();
          errorMsg = errorData.error || errorMsg;
          console.error('Server error details:', errorData);
        } catch (e) {
          console.error('Failed to parse error response');
        }
        throw new Error(errorMsg);
      }

      const pdfBlob = await response.blob();
      console.log('✅ PDF blob received, size:', pdfBlob.size, 'bytes');
      
      if (!pdfBlob || pdfBlob.size === 0) {
        throw new Error('Empty PDF response');
      }

      // Create download filename
      const downloadFilename = `discharge-report-${reportNumber}.pdf`;
      
      // Trigger browser download
      const downloadUrl = window.URL.createObjectURL(pdfBlob);
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.download = downloadFilename;
      link.style.display = 'none';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(downloadUrl);

      console.log('✅ PDF download triggered successfully');

      // Save to localStorage
      try {
        await pdfManagerRef.current.saveToLocalStorage(reportNumber, pdfBlob, downloadFilename, {
          patientName,
          generatedAt: new Date().toISOString(),
          fileSize: pdfBlob.size,
          originalFilename: downloadFilename
        });
        const storageStats = pdfManagerRef.current.getStorageStats() || {};
        
        setMessages(prev => [...prev, {
          id: Date.now(),
          text: `✅ **PDF Downloaded Successfully!**\n\n📁 **File:** ${downloadFilename}\n👤 **Patient:** ${patientName}\n💾 **Size:** ${(pdfBlob.size / 1024).toFixed(2)} KB\n📂 **Local Storage:** ${storageStats.formattedTotalSize || '0 KB'} / ${storageStats.formattedMaxSize || '50 MB'}\n📱 **Total Reports:** ${storageStats.reportCount || 0}`,
          sender: 'ai',
          timestamp: new Date().toLocaleTimeString()
        }]);
      } catch (storageError) {
        console.warn('Local storage failed:', storageError);
        setMessages(prev => [...prev, {
          id: Date.now(),
          text: `✅ **PDF Downloaded Successfully!**\n\n📁 **File:** ${downloadFilename}\n👤 **Patient:** ${patientName}\n💾 **Size:** ${(pdfBlob.size / 1024).toFixed(2)} KB\n⚠️ **Note:** Local storage failed but file downloaded`,
          sender: 'ai',
          timestamp: new Date().toLocaleTimeString()
        }]);
      }
    } catch (error) {
      console.error('❌ PDF download error:', error);
      setMessages(prev => [...prev, {
        id: Date.now(),
        text: `❌ **PDF download failed:** ${error.message}\n\n**Troubleshooting:**\n• Ensure the report was generated successfully\n• Check if the backend server is running\n• Try generating the report again`,
        sender: 'ai',
        timestamp: new Date().toLocaleTimeString(),
        isError: true
      }]);
    }
  };

  const disconnect = async () => {
    if (aiMcpServiceRef.current) {
      await aiMcpServiceRef.current.disconnect();
      setIsConnected(false);
      setServerInfo(null);
      setMessages([]);
      setShowSetup(true);
      console.log('🔌 Disconnected from MCP Server');
    }
  };

  const checkStatus = async () => {
    if (aiMcpServiceRef.current) {
      try {
        await aiMcpServiceRef.current.mcpClient.getStatus();
        const info = aiMcpServiceRef.current.mcpClient.getServerInfo();
        setMessages(prev => [...prev, {
          id: Date.now(),
          text: `📊 **Status Check:**\n- Connection: ✅ Active\n- Tools: ${info.toolCount}\n- Server: ${info.name} v${info.version}`,
          sender: 'ai',
          timestamp: new Date().toLocaleTimeString()
        }]);
      } catch (error) {
        setMessages(prev => [...prev, {
          id: Date.now(),
          text: `❌ **Status Check Failed:** ${error.message}`,
          sender: 'ai',
          timestamp: new Date().toLocaleTimeString(),
          isError: true
        }]);
      }
    }
  };

  // Setup Screen
  if (showSetup) {
    return (
      <div className="h-screen bg-[#1a1a1a] flex items-center justify-center text-white">
        <div className="bg-[#2a2a2a] rounded-lg shadow-xl p-8 max-w-md w-full mx-4">
          <div className="text-center mb-6">
            <div className="w-16 h-16 bg-blue-600 rounded-full flex items-center justify-center mx-auto mb-4">
              <span className="text-2xl font-medium text-white">H</span>
            </div>
            <h1 className="text-xl font-bold text-white">Hospital Assistant</h1>
            <p className="text-gray-400 text-sm mt-2">Connect to Hospital Management System</p>
          </div>

          {connectionError && (
            <div className="bg-red-900 border border-red-700 text-red-200 px-3 py-2 rounded mb-4 text-sm">
              {connectionError}
            </div>
          )}

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                OpenAI API Key:
              </label>
              <input
                type="password"
                value={openaiApiKey}
                onChange={(e) => setOpenaiApiKey(e.target.value)}
                placeholder="sk-..."
                className="w-full px-3 py-2 bg-[#3a3a3a] border border-gray-600 rounded-md text-white placeholder-gray-400 focus:outline-none focus:ring-1 focus:ring-blue-500"
              />
            </div>

            <button
              onClick={initializeService}
              disabled={isLoading || !openaiApiKey.trim()}
              className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 text-white font-medium py-2 px-4 rounded-md transition-colors duration-200"
            >
              {isLoading ? 'Connecting...' : '🚀 Connect to Hospital System'}
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Main Interface
  return (
    <div className="h-screen bg-[#1a1a1a] flex flex-col text-white">
      {/* Header */}
      <div className="border-b border-gray-700 px-4 py-3 bg-[#1a1a1a]">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-7 h-7 bg-blue-600 rounded-full flex items-center justify-center text-white text-sm font-medium shadow-lg">
              H
            </div>
            <div>
              <h1 className="text-sm font-medium text-white">Hospital Assistant</h1>
              {serverInfo && (
                <p className="text-xs text-gray-400">
                  Connected • {serverInfo.toolCount} tools
                </p>
              )}
            </div>
          </div>
          <button
            onClick={disconnect}
            className="p-1.5 text-gray-400 hover:text-gray-300 hover:bg-gray-700 rounded-md transition-colors"
            title="Disconnect"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>

      {/* Chat Messages */}
      <div className="flex-1 overflow-y-auto bg-[#1a1a1a]">
        <div className="max-w-4xl mx-auto">
          <div className="px-4 py-6">
            {messages.length === 0 && (
              <div className="text-center">
                <div className="w-20 h-20 bg-blue-600 rounded-full flex items-center justify-center mx-auto mb-6">
                  <span className="text-3xl font-medium text-white">H</span>
                </div>
                <div className="max-w-lg mx-auto">
                  <h3 className="text-lg font-medium text-white mb-3">
                    Hospital Management Assistant
                  </h3>
                  <p className="text-gray-400 mb-6 text-sm">
                    I'm your AI assistant for hospital management tasks. Ask me anything!
                  </p>
                </div>
              </div>
            )}
            
            {messages.map((message) => (
              <div key={message.id} className="px-4 py-2 bg-[#1a1a1a]">
                <div className="flex space-x-3">
                  <div className="w-7 h-7 bg-blue-600 rounded-full flex items-center justify-center flex-shrink-0 text-sm font-medium text-white shadow-lg">
                    {message.sender === 'user' ? 'U' : 'H'}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="text-gray-300 text-sm whitespace-pre-wrap">
                      {message.text}
                    </div>
                    {message.hasDownload && message.reportNumber && (
                      <div className="mt-3 p-3 bg-[#2a2a2a] border border-gray-600 rounded-lg">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center space-x-2">
                            <svg className="w-5 h-5 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                            </svg>
                            <span className="text-sm text-blue-400 font-medium">
                              📄 Report Generated: {message.reportNumber}
                            </span>
                          </div>
                          <button
                            onClick={() => handleDownloadPDF(message.reportNumber)}
                            disabled={isLoading}
                            className="flex items-center space-x-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 text-white px-3 py-1.5 rounded-md text-sm font-medium transition-colors"
                          >
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                            </svg>
                            <span>Download PDF</span>
                          </button>
                        </div>
                      </div>
                    )}
                    <div className="text-xs text-gray-500 mt-1">
                      {message.timestamp}
                    </div>
                  </div>
                </div>
              </div>
            ))}
            
            {isLoading && (
              <div className="px-4 py-2 bg-[#1a1a1a]">
                <div className="flex space-x-3">
                  <div className="w-7 h-7 bg-blue-600 rounded-full flex items-center justify-center flex-shrink-0 shadow-lg">
                    <div className="w-3 h-3 border border-gray-400 border-t-white rounded-full animate-spin"></div>
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="text-gray-300 text-sm">
                      Processing your request...
                    </div>
                  </div>
                </div>
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* Chat Input */}
        <div className="border-t border-gray-700 bg-[#1a1a1a] px-4 py-4">
          <div className="max-w-4xl mx-auto">
            <div className="flex space-x-3">
              <div className="flex-1">
                <textarea
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Ask me about patients, appointments, reports, or anything hospital related..."
                  className="w-full px-3 py-2 bg-[#2a2a2a] border border-gray-600 rounded-md text-white placeholder-gray-400 focus:outline-none focus:ring-1 focus:ring-blue-500 resize-none"
                  rows={2}
                  disabled={isLoading}
                />
              </div>
              <button
                onClick={sendMessage}
                disabled={isLoading || !inputMessage.trim()}
                className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 text-white px-4 py-2 rounded-md font-medium transition-colors duration-200 flex items-center space-x-2"
              >
                <span>Send</span>
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default HospitalAssistant;