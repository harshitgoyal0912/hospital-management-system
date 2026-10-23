import React, { useState, useEffect, useRef } from 'react';
import { LogOut, User, Settings, Upload, FileText, History, CheckCircle, Plus, X, Mic, MicOff, VolumeX, Brain, Stethoscope, Activity, Pill } from 'lucide-react';
import DirectHttpAIMCPService from '../services/directHttpAiMcpService.js';
//import MedicalDocumentUpload from './MedicalDocumentUpload.jsx';
//import EnhancedMedicalDocumentUpload from './EnhancedMedicalDocumentUpload.jsx';
//import MedicalHistoryViewer from './MedicalHistoryViewer.jsx';
import PatientAdmissionForm from './PatientAdmissionForm.jsx';
import UserCreationForm from './UserCreationForm.jsx';
import StaffCreationForm from './StaffCreationForm.jsx';
import DepartmentCreationForm from './DepartmentCreationForm.jsx';
import RoomCreationForm from './RoomCreationForm.jsx';
import EquipmentCreationForm from './EquipmentCreationForm.jsx';
import SupplyCreationForm from './SupplyCreationForm.jsx';
import BedCreationForm from './BedCreationForm.jsx';
import LegacyUserCreationForm from './LegacyUserCreationForm.jsx';
import EquipmentCategoryCreationForm from './EquipmentCategoryCreationForm.jsx';
import SupplyCategoryCreationForm from './SupplyCategoryCreationForm.jsx';
import HospitalChatInterface from './HospitalChatInterface.jsx';
import RealTimeDashboard, { DashboardProvider } from './RealTimeDashboard.jsx';
import AIClinicalChatbot from './AIClinicalChatbot.jsx';

const DirectMCPChatbot = ({ user, onLogout }) => {
  // Mobile-responsive CSS classes for consistent mobile experience (reduced height)
  // Reduced vertical padding and font size to make the chat input area shorter
  const mobileInputClass = "w-full px-3 py-2 sm:py-1 text-sm sm:text-xs";
  const mobileSelectClass = "w-full px-3 py-2 sm:py-1 text-sm sm:text-xs";
  
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [showSetup, setShowSetup] = useState(false); // Start with false since auth is handled by parent
  const [showActionButtons, setShowActionButtons] = useState(true); // Track whether to show action buttons
  
  // Configuration state - get API key from environment variables
  const [openaiApiKey] = useState(import.meta.env.VITE_OPENAI_API_KEY || '');
  
  const [serverInfo, setServerInfo] = useState(null);
  const [connectionError, setConnectionError] = useState('');
  const [expandedThinking, setExpandedThinking] = useState({}); // Track which thinking messages are expanded
  const [isInputFocused, setIsInputFocused] = useState(false); // Track input focus state
  const [showPlusMenu, setShowPlusMenu] = useState(false); // Track plus icon dropdown menu
  
  // Voice functionality state
  const [isListening, setIsListening] = useState(false); // Track voice recording state
  const [isProcessingVoice, setIsProcessingVoice] = useState(false); // Track voice processing state
  const [isSpeaking, setIsSpeaking] = useState(false); // Track if AI is currently speaking
  const [lastVoiceInputId, setLastVoiceInputId] = useState(null); // Track the last voice input message ID
  const [isRecording, setIsRecording] = useState(false); // Track audio recording state
  const [mediaRecorder, setMediaRecorder] = useState(null); // Audio recorder instance
  const [audioChunks, setAudioChunks] = useState([]); // Recorded audio chunks
  const [currentAudio, setCurrentAudio] = useState(null); // Current playing audio
  const [microphoneAvailable, setMicrophoneAvailable] = useState(null); // Track microphone availability
  
  // Medical document features
  const [activeTab, setActiveTab] = useState('chat'); // chat, upload, history, dashboard, ai-clinical
  const [selectedPatientId, setSelectedPatientId] = useState(null); // This will store the UUID
  const [selectedPatientNumber, setSelectedPatientNumber] = useState(''); // This will store the patient number (P123456)
  const [searchingPatient, setSearchingPatient] = useState(false);
  const [patientSearchResult, setPatientSearchResult] = useState(null);
  const [patients, setPatients] = useState([]);
  
  // Patient admission popup form
  const [showPatientAdmissionForm, setShowPatientAdmissionForm] = useState(false);
  const [isSubmittingAdmission, setIsSubmittingAdmission] = useState(false);
  
  // Department creation popup form
  const [showDepartmentForm, setShowDepartmentForm] = useState(false);
  const [isSubmittingDepartment, setIsSubmittingDepartment] = useState(false);
  
  // Staff creation popup form
  const [showStaffForm, setShowStaffForm] = useState(false);
  const [isSubmittingStaff, setIsSubmittingStaff] = useState(false);
  
  // User creation popup form
  const [showUserForm, setShowUserForm] = useState(false);
  const [isSubmittingUser, setIsSubmittingUser] = useState(false);
  
  // Room creation popup form
  // Room creation popup form
  const [showRoomForm, setShowRoomForm] = useState(false);
  const [isSubmittingRoom, setIsSubmittingRoom] = useState(false);
  
  // Bed creation popup form
  const [showBedForm, setShowBedForm] = useState(false);
  const [isSubmittingBed, setIsSubmittingBed] = useState(false);
  
  // Equipment creation popup form
  const [showEquipmentForm, setShowEquipmentForm] = useState(false);
  const [isSubmittingEquipment, setIsSubmittingEquipment] = useState(false);
  
  // Supply creation popup form
  const [showSupplyForm, setShowSupplyForm] = useState(false);
  const [isSubmittingSupply, setIsSubmittingSupply] = useState(false);
  
  // Legacy User creation popup form
  const [showLegacyUserForm, setShowLegacyUserForm] = useState(false);
  const [isSubmittingLegacyUser, setIsSubmittingLegacyUser] = useState(false);
  
  // Equipment Category creation popup form
  const [showEquipmentCategoryForm, setShowEquipmentCategoryForm] = useState(false);
  const [isSubmittingEquipmentCategory, setIsSubmittingEquipmentCategory] = useState(false);
  
  // Supply Category creation popup form
  const [showSupplyCategoryForm, setShowSupplyCategoryForm] = useState(false);
  const [isSubmittingSupplyCategory, setIsSubmittingSupplyCategory] = useState(false);
  
  // Discharge workflow popup form
  const [showDischargeForm, setShowDischargeForm] = useState(false);
  const [dischargeFormData, setDischargeFormData] = useState({
    patient_id: '',
    bed_id: '',
    patient_name: '',
    discharge_condition: 'stable',
    discharge_destination: 'home'
  });
  const [isSubmittingDischarge, setIsSubmittingDischarge] = useState(false);
  
  // Dropdown options state for foreign keys
  const [departmentOptions, setDepartmentOptions] = useState([]);
  const [userOptions, setUserOptions] = useState([]);
  const [roomOptions, setRoomOptions] = useState([]);
  const [patientOptions, setPatientOptions] = useState([]);
  const [equipmentCategoryOptions, setEquipmentCategoryOptions] = useState([]);
  const [supplyCategoryOptions, setSupplyCategoryOptions] = useState([]);
  const [loadingDropdowns, setLoadingDropdowns] = useState(false);
  
  // Auto-scroll to bottom only when new messages are added, not on timer updates
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages.length]); // Only trigger on message count change, not message content changes

  // Auto-connect when component mounts if user is authenticated
  useEffect(() => {
    if (user && openaiApiKey && !isConnected && !showSetup) {
      console.log('🔄 Auto-connecting for authenticated user...');
      initializeService();
    }
  }, [user, isConnected, showSetup]); // Dependencies that should trigger auto-connection

  // Component to display thinking duration
  const ThinkingDuration = React.memo(({ startTime }) => {
    const [duration, setDuration] = React.useState(1);
    
    React.useEffect(() => {
      if (!startTime) return;
      
      // Update every 500ms instead of 100ms for better performance
      const interval = setInterval(() => {
        setDuration(Math.ceil((Date.now() - startTime) / 1000));
      }, 500);
      
      return () => clearInterval(interval);
    }, [startTime]);
    
    return <span>{duration}s</span>;
  });
  
  const aiMcpServiceRef = useRef(null);
  const messagesEndRef = useRef(null);
  const messagesContainerRef = useRef(null);
  const lastMessageCountRef = useRef(0);
  const inputFieldRef = useRef(null); // Add ref for input field
  const plusMenuRef = useRef(null); // Add ref for plus menu dropdown
  // Touch / swipe refs for mobile swipe navigation (upload/history -> chat)
  const touchStartXRef = useRef(null);
  const touchStartYRef = useRef(null);
  const touchStartTimeRef = useRef(null);
  const swipeTriggeredRef = useRef(false);

  // Handle touch start (record position/time)
  const handleTouchStart = (e) => {
    try {
      // Ignore if interacting with inputs
      const tag = e.target && e.target.tagName ? e.target.tagName.toUpperCase() : '';
      if (['INPUT', 'TEXTAREA', 'SELECT', 'BUTTON'].includes(tag)) return;
      const t = (e.touches && e.touches[0]) || null;
      if (!t) return;
      touchStartXRef.current = t.clientX;
      touchStartYRef.current = t.clientY;
      touchStartTimeRef.current = Date.now();
    } catch (err) {
      // swallow errors
    }
  };

  // Handle touch end (compute delta and detect swipe-right)
  const handleTouchEnd = (e) => {
    try {
      const t = (e.changedTouches && e.changedTouches[0]) || null;
      if (!t || touchStartXRef.current == null) return;
      const dx = t.clientX - touchStartXRef.current;
      const dy = t.clientY - touchStartYRef.current;
      const dt = Date.now() - (touchStartTimeRef.current || 0);

      const HORIZONTAL_SWIPE_THRESHOLD = 60; // pixels
      const VERTICAL_TOLERANCE = 75; // pixels
      const MAX_SWIPE_TIME = 800; // ms

      // Right swipe with limited vertical movement and reasonable speed
      if (dx > HORIZONTAL_SWIPE_THRESHOLD && Math.abs(dy) < VERTICAL_TOLERANCE && dt < MAX_SWIPE_TIME) {
        // Only switch when not already on chat
        setActiveTab((prev) => (prev === 'chat' ? prev : 'chat'));
      }

      // reset
      touchStartXRef.current = null;
      touchStartYRef.current = null;
      touchStartTimeRef.current = null;
      swipeTriggeredRef.current = false;
    } catch (err) {
      // swallow
    }
  };

  // Handle touch move for earlier detection (helps on scrollable containers)
  const handleTouchMove = (e) => {
    try {
      if (swipeTriggeredRef.current) return;
      const t = (e.touches && e.touches[0]) || null;
      if (!t || touchStartXRef.current == null) return;
      const dx = t.clientX - touchStartXRef.current;
      const dy = t.clientY - touchStartYRef.current;

      const HORIZONTAL_SWIPE_THRESHOLD = 60; // pixels
      const VERTICAL_TOLERANCE = 75; // pixels

      if (dx > HORIZONTAL_SWIPE_THRESHOLD && Math.abs(dy) < VERTICAL_TOLERANCE) {
        swipeTriggeredRef.current = true;
        setActiveTab((prev) => (prev === 'chat' ? prev : 'chat'));
      }
    } catch (err) {
      // swallow
    }
  };

  // Controlled scroll function
  const scrollToBottom = React.useCallback(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, []);

  // Auto-scroll only when new messages are added, with smart scrolling
  useEffect(() => {
    const currentMessageCount = messages.length;
    if (currentMessageCount > lastMessageCountRef.current) {
      // Only scroll if user is near the bottom (within 100px) or if it's the first message
      if (messagesContainerRef.current) {
        const container = messagesContainerRef.current;
        const isNearBottom = container.scrollTop + container.clientHeight >= container.scrollHeight - 100;
        
        if (isNearBottom || currentMessageCount === 1) {
          setTimeout(scrollToBottom, 50); // Small delay to ensure DOM is updated
        }
      } else {
        setTimeout(scrollToBottom, 50);
      }
    }
    lastMessageCountRef.current = currentMessageCount;
  }, [messages.length, scrollToBottom]);

  // Add keyboard shortcut to focus input (Ctrl/Cmd + /)
  useEffect(() => {
    const handleKeyDown = (event) => {
      if ((event.ctrlKey || event.metaKey) && event.key === '/') {
        event.preventDefault();
        if (inputFieldRef.current && isConnected) {
          inputFieldRef.current.focus();
        }
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isConnected]);

  // Handle outside clicks for plus menu
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (plusMenuRef.current && !plusMenuRef.current.contains(event.target)) {
        setShowPlusMenu(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Check microphone availability on component mount
  useEffect(() => {
    const checkMicrophoneAvailability = async () => {
      try {
        // Check if microphone APIs are available
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
          setMicrophoneAvailable(false);
          console.warn('Microphone API not available - likely due to non-HTTPS connection or browser restrictions');
          return;
        }

        // Check if we're in a secure context
        if (!window.isSecureContext && location.hostname !== 'localhost') {
          setMicrophoneAvailable(false);
          console.warn('Microphone requires HTTPS connection');
          return;
        }

        // Test microphone permissions (this won't trigger permission prompt if denied)
        const permissions = await navigator.permissions.query({ name: 'microphone' });
        
        if (permissions.state === 'denied') {
          setMicrophoneAvailable(false);
          console.warn('Microphone permission denied');
        } else {
          setMicrophoneAvailable(true);
          console.log('Microphone available');
        }
      } catch (error) {
        console.warn('Error checking microphone availability:', error);
        setMicrophoneAvailable(false);
      }
    };

    checkMicrophoneAvailability();
  }, []);

  // Mobile viewport handling to prevent keyboard issues
  useEffect(() => {
    const handleMobileViewport = () => {
      if (isMobileDevice()) {
        // Set CSS custom property for real viewport height
        const vh = window.innerHeight * 0.01;
        document.documentElement.style.setProperty('--vh', `${vh}px`);
        
        // Prevent viewport zoom on input focus
        const viewport = document.querySelector('meta[name=viewport]');
        if (!viewport) {
          const newViewport = document.createElement('meta');
          newViewport.name = 'viewport';
          newViewport.content = 'width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover';
          document.head.appendChild(newViewport);
        }
      }
    };

    // Initial setup
    handleMobileViewport();

    // Handle orientation changes and resize
    const handleResize = () => {
      if (isMobileDevice()) {
        setTimeout(handleMobileViewport, 100); // Delay to account for keyboard animation
      }
    };

    window.addEventListener('resize', handleResize);
    window.addEventListener('orientationchange', handleResize);

    // Cleanup
    return () => {
      window.removeEventListener('resize', handleResize);
      window.removeEventListener('orientationchange', handleResize);
    };
  }, []);

  // Mobile detection utility function
  const isMobileDevice = () => {
    return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) ||
           (window.innerWidth <= 768) || // Also check for small screen width
           ('ontouchstart' in window); // Check for touch capability
  };

  // iOS detection utility function
  const isIOSDevice = () => {
    return /iPad|iPhone|iPod/.test(navigator.userAgent);
  };

  // Smart focus function - focuses input but prevents keyboard popup on mobile
  const smartFocusInput = (delay = 100) => {
    setTimeout(() => {
      if (inputFieldRef.current) {
        if (isMobileDevice()) {
          // On mobile: Don't focus automatically to prevent keyboard popup
          // Just ensure input is visually focused (via state) without actual DOM focus
          setIsInputFocused(true);
          setTimeout(() => setIsInputFocused(false), 1000);
        } else {
          // On desktop: normal focus behavior
          inputFieldRef.current.focus();
        }
      }
    }, delay);
  };

  // OpenAI Text-to-Speech function for voice output
  const speakTextWithOpenAI = async (text, isResponseToVoiceInput = false) => {
    // Only speak if this is a response to voice input and we have an API key
    if (!isResponseToVoiceInput || !openaiApiKey.trim()) {
      return;
    }

    // Stop any current audio
    stopCurrentAudio();

    // Clean up text for speech (remove markdown and formatting)
    let cleanText = text
      .replace(/\*\*([^*]+)\*\*/g, '$1') // Remove bold markdown
      .replace(/\*([^*]+)\*/g, '$1') // Remove italic markdown
      .replace(/`([^`]+)`/g, '$1') // Remove code backticks
      .replace(/#{1,6}\s?/g, '') // Remove heading hashtags
      .replace(/---/g, '') // Remove horizontal rules
      .replace(/\n{2,}/g, '\n') // Reduce multiple newlines
      .replace(/🧠|🤔|🔍|🛠️|📊|💡|ℹ️|✅|❌|💥/g, '') // Remove emojis
      .replace(/\[(.*?)\]\(.*?\)/g, '$1') // Convert links to just text
      .replace(/\*\*([^*]+)\*\*/g, '$1') // Additional cleanup
      .replace(/\n/g, ' ') // Replace newlines with spaces
      .replace(/\s+/g, ' ') // Replace multiple spaces with single space
      .trim();

    // Skip speaking if text is too short or just symbols
    if (cleanText.length < 3 || /^[^\w\s]*$/.test(cleanText)) {
      return;
    }

    // Limit text length for TTS (OpenAI has a 4096 character limit)
    if (cleanText.length > 4000) {
      cleanText = cleanText.substring(0, 4000) + '...';
    }

    try {
      setIsSpeaking(true);

      const response = await fetch('https://api.openai.com/v1/audio/speech', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${openaiApiKey}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          model: 'tts-1', // Use tts-1 for faster generation, tts-1-hd for higher quality
          input: cleanText,
          voice: 'alloy', // Options: alloy, echo, fable, onyx, nova, shimmer
          response_format: 'mp3',
          speed: 1.0,
        }),
      });

      if (!response.ok) {
        throw new Error(`TTS API error: ${response.status}`);
      }

      const audioBlob = await response.blob();
      const audioUrl = URL.createObjectURL(audioBlob);
      const audio = new Audio(audioUrl);

      audio.onloadeddata = () => {
        setCurrentAudio(audio);
        audio.play().catch((error) => {
          console.error('Audio playback failed:', error);
          setIsSpeaking(false);
        });
      };

      audio.onended = () => {
        setIsSpeaking(false);
        setCurrentAudio(null);
        URL.revokeObjectURL(audioUrl);
      };

      audio.onerror = (error) => {
        console.error('Audio playback error:', error);
        setIsSpeaking(false);
        setCurrentAudio(null);
        URL.revokeObjectURL(audioUrl);
      };
    } catch (error) {
      console.error('OpenAI TTS error:', error);
      setIsSpeaking(false);

      // Fallback to browser speech synthesis if OpenAI fails
      if ('speechSynthesis' in window) {
        const utterance = new SpeechSynthesisUtterance(cleanText);
        utterance.rate = 1.0;
        utterance.pitch = 1.0;
        utterance.volume = 0.8;

        utterance.onend = () => setIsSpeaking(false);
        utterance.onerror = () => setIsSpeaking(false);

        speechSynthesis.speak(utterance);
      }
    }
  };

  // Function to stop current audio playback
  const stopCurrentAudio = () => {
    if (currentAudio) {
      currentAudio.pause();
      currentAudio.currentTime = 0;
      setCurrentAudio(null);
    }
    if ('speechSynthesis' in window && speechSynthesis.speaking) {
      speechSynthesis.cancel();
    }
    setIsSpeaking(false);
  };

  // OpenAI Speech-to-Text (Whisper) function
  const transcribeWithOpenAI = async (audioBlob) => {
    if (!openaiApiKey.trim()) {
      throw new Error('OpenAI API key is required for speech recognition');
    }

    const formData = new FormData();
    formData.append('file', audioBlob, 'audio.webm');
    formData.append('model', 'whisper-1');
    formData.append('language', 'en'); // Optional: specify language
    formData.append('response_format', 'json');

    try {
      const response = await fetch('https://api.openai.com/v1/audio/transcriptions', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${openaiApiKey}`,
        },
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`Whisper API error: ${response.status}`);
      }

      const result = await response.json();
      return result.text;
    } catch (error) {
      console.error('OpenAI Whisper error:', error);
      throw error;
    }
  };

  // Start recording audio for speech-to-text
  const startRecording = async () => {
    try {
      // Stop any current audio playback
      stopCurrentAudio();

      // Check if microphone APIs are available
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        throw new Error('Microphone access is not available. This may be due to: 1) Non-HTTPS connection (required for microphone access), 2) Browser security restrictions, or 3) Missing microphone permissions.');
      }

      // Check if we're in a secure context (HTTPS or localhost)
      if (!window.isSecureContext && location.hostname !== 'localhost') {
        throw new Error('Microphone access requires HTTPS connection. Please access the site via HTTPS.');
      }

      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      });

      const recorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus',
      });

      const chunks = [];

      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunks.push(event.data);
        }
      };

      recorder.onstop = async () => {
        const audioBlob = new Blob(chunks, { type: 'audio/webm' });
        setIsProcessingVoice(true);

        try {
          const transcript = await transcribeWithOpenAI(audioBlob);

          if (transcript && transcript.trim()) {
            setInputMessage(transcript);

            // Show user's voice input message in chat
            const voiceInputId = Date.now();
            const userMsg = {
              id: voiceInputId,
              text: transcript.trim(),
              sender: 'user',
              timestamp: new Date().toLocaleTimeString(),
              isVoiceInput: true,
            };
            setMessages((prev) => [...prev, userMsg]);
            setLastVoiceInputId(voiceInputId);

            // Auto-send the voice input after a short delay
            setTimeout(() => {
              if (transcript.trim() && isConnected && !isLoading) {
                setInputMessage('');
                sendMessageClaudeStyle(transcript.trim(), true);
                setIsProcessingVoice(false);
              } else {
                setIsProcessingVoice(false);
              }
            }, 800);
          } else {
            setIsProcessingVoice(false);
            console.log('No speech detected');
          }
        } catch (error) {
          console.error('Speech transcription failed:', error);
          setIsProcessingVoice(false);

          // Show error message
          const errorMsg = {
            id: Date.now(),
            text: `🎤 **Speech Recognition Error:** ${error.message}. Please try again.`,
            sender: 'ai',
            timestamp: new Date().toLocaleTimeString(),
            isError: true,
          };
          setMessages((prev) => [...prev, errorMsg]);
        }

        // Clean up media stream
        stream.getTracks().forEach((track) => track.stop());
        setAudioChunks([]);
      };

      setMediaRecorder(recorder);
      setAudioChunks(chunks);
      setIsRecording(true);
      setIsListening(true);

      recorder.start();
    } catch (error) {
      console.error('Failed to start recording:', error);
      setIsRecording(false);
      setIsListening(false);

      // Show error message
      const errorMsg = {
        id: Date.now(),
        text: `🎤 **Microphone Error:** ${error.message}. Please check your microphone permissions.`,
        sender: 'ai',
        timestamp: new Date().toLocaleTimeString(),
        isError: true,
      };
      setMessages((prev) => [...prev, errorMsg]);
    }
  };

  // Stop recording audio
  const stopRecording = () => {
    if (mediaRecorder && mediaRecorder.state === 'recording') {
      mediaRecorder.stop();
    }
    setIsRecording(false);
    setIsListening(false);
  };

  // Voice input toggle function
  const toggleVoiceInput = () => {
    if (!openaiApiKey.trim()) {
      const errorMsg = {
        id: Date.now(),
        text: '🔑 **API Key Required:** Please configure your OpenAI API key to use voice features.',
        sender: 'ai',
        timestamp: new Date().toLocaleTimeString(),
        isError: true,
      };
      setMessages((prev) => [...prev, errorMsg]);
      return;
    }

    // If AI is speaking, stop the speech
    if (isSpeaking) {
      stopCurrentAudio();
      return;
    }

    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  };

  /**
   * Initialize the AI-MCP service
   */
  const initializeService = async () => {
    if (!openaiApiKey.trim()) {
      setConnectionError('OpenAI API key not configured in environment variables. Please contact administrator.');
      return;
    }

    setIsLoading(true);
    setConnectionError('');
    
    try {
      aiMcpServiceRef.current = new DirectHttpAIMCPService();
      
      console.log('🚀 Initializing Direct HTTP MCP Service...');
      
      const initialized = await aiMcpServiceRef.current.initialize();
      
      if (initialized) {
        setIsConnected(true);
        setShowSetup(false);
        
        const info = aiMcpServiceRef.current.getServerInfo();
        setServerInfo(info);
        
        setMessages([{
          id: Date.now(),
          text: `👋 Welcome to Hospital Agent! How can I help you today? 🏥`,
          sender: 'ai',
          timestamp: new Date().toLocaleTimeString()
        }]);
        
        // Auto-focus the input field after successful connection (smart focus)
        smartFocusInput(100);
        
      } else {
        throw new Error('Failed to initialize service');
      }
      
    } catch (error) {
      console.error('❌ Initialization failed:', error);
      setConnectionError(`Connection failed: ${error.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Load dropdown options for foreign key fields
   */
  const loadDropdownOptions = async () => {
    if (!aiMcpServiceRef.current || loadingDropdowns) return;
    
    setLoadingDropdowns(true);
    try {
      // Load departments
      const departmentsResponse = await aiMcpServiceRef.current.mcpClient.callTool('list_departments', {});
      console.log('🏥 Departments response:', departmentsResponse);
      const departments = departmentsResponse?.result?.content?.[0]?.text 
        ? JSON.parse(departmentsResponse.result.content[0].text)?.result?.data || []
        : departmentsResponse?.result?.data || departmentsResponse || [];
      console.log('🏥 Departments parsed:', departments);
      setDepartmentOptions(Array.isArray(departments) ? departments : []);
      
      // Load users
      const usersResponse = await aiMcpServiceRef.current.mcpClient.callTool('list_users', {});
      console.log('👥 Users response:', usersResponse);
      const users = usersResponse?.result?.content?.[0]?.text 
        ? JSON.parse(usersResponse.result.content[0].text)?.result?.data || []
        : usersResponse?.result?.data || usersResponse || [];
      console.log('👥 Users parsed:', users);
      setUserOptions(Array.isArray(users) ? users : []);
      
      // Load rooms
      const roomsResponse = await aiMcpServiceRef.current.mcpClient.callTool('list_rooms', {});
      console.log('🚪 Rooms response:', roomsResponse);
      const rooms = roomsResponse?.result?.content?.[0]?.text 
        ? JSON.parse(roomsResponse.result.content[0].text)?.result?.data || []
        : roomsResponse?.result?.data || roomsResponse || [];
      console.log('🚪 Rooms parsed:', rooms);
      setRoomOptions(Array.isArray(rooms) ? rooms : []);
      
      // Load patients
      const patientsResponse = await aiMcpServiceRef.current.mcpClient.callTool('list_patients', {});
      const patients = patientsResponse?.result?.content?.[0]?.text 
        ? JSON.parse(patientsResponse.result.content[0].text)?.result?.data || []
        : patientsResponse?.result?.data || patientsResponse || [];
      console.log('🤒 Patients parsed:', patients);
      setPatientOptions(Array.isArray(patients) ? patients : []);
      
      // Load equipment categories
      try {
        const equipmentCategoriesResponse = await aiMcpServiceRef.current.mcpClient.callTool('list_equipment_categories', {});
        const equipmentCategories = equipmentCategoriesResponse?.result?.content?.[0]?.text 
          ? JSON.parse(equipmentCategoriesResponse.result.content[0].text)?.result?.data || []
          : equipmentCategoriesResponse?.result?.data || equipmentCategoriesResponse || [];
        setEquipmentCategoryOptions(Array.isArray(equipmentCategories) ? equipmentCategories : []);
      } catch (e) {
        console.warn('Equipment categories not available:', e);
        setEquipmentCategoryOptions([]);
      }
      
      // Load supply categories
      try {
        const supplyCategoriesResponse = await aiMcpServiceRef.current.mcpClient.callTool('list_supply_categories', {});
        const supplyCategories = supplyCategoriesResponse?.result?.content?.[0]?.text 
          ? JSON.parse(supplyCategoriesResponse.result.content[0].text)?.result?.data || []
          : supplyCategoriesResponse?.result?.data || supplyCategoriesResponse || [];
        setSupplyCategoryOptions(Array.isArray(supplyCategories) ? supplyCategories : []);
      } catch (e) {
        console.warn('Supply categories not available:', e);
        setSupplyCategoryOptions([]);
      }
      
      console.log('✅ Dropdown options loaded successfully');
    } catch (error) {
      console.error('❌ Failed to load dropdown options:', error);
    } finally {
      setLoadingDropdowns(false);
    }
  };

  /**
   * Use OpenAI to intelligently detect user intent for showing popup forms
   * Only specific CREATE tools trigger popup forms, all other tools use AI processing
   */
  const detectIntentWithAI = async (userMessage) => {
    console.log('🤖 detectIntentWithAI called with message:', userMessage);
    console.log('🤖 OpenAI API key available:', !!openaiApiKey.trim());
    
    if (!openaiApiKey.trim()) {
      console.log('⚠️ No OpenAI API key found, using fallback keyword detection for popup forms');
      
      // Fallback keyword detection when no API key is available
      const message = userMessage.toLowerCase();
      console.log('🔍 Checking message for keywords:', message);
      
      // CREATE operations that should trigger popup forms
      if ((message.includes('create') || message.includes('add') || message.includes('register') || message.includes('new')) && message.includes('patient')) {
        console.log('✅ Fallback detected: create_patient');
        return 'create_patient';
      }
      if ((message.includes('create') || message.includes('add') || message.includes('new')) && (message.includes('user') && !message.includes('legacy'))) {
        console.log('✅ Fallback detected: create_user');
        return 'create_user';
      }
      if ((message.includes('create') || message.includes('add') || message.includes('new')) && message.includes('legacy') && message.includes('user')) {
        console.log('✅ Fallback detected: create_legacy_user');
        return 'create_legacy_user';
      }
      if ((message.includes('create') || message.includes('add') || message.includes('new')) && message.includes('department')) {
        console.log('✅ Fallback detected: create_department');
        return 'create_department';
      }
      if ((message.includes('create') || message.includes('add') || message.includes('new')) && message.includes('room')) {
        console.log('✅ Fallback detected: create_room');
        return 'create_room';
      }
      if ((message.includes('create') || message.includes('add') || message.includes('new')) && message.includes('bed')) {
        console.log('✅ Fallback detected: create_bed');
        return 'create_bed';
      }
      if ((message.includes('create') || message.includes('add') || message.includes('new')) && (message.includes('staff') || message.includes('employee')) && !message.includes('usage') && !message.includes('assign')) {
        console.log('✅ Fallback detected: create_staff');
        return 'create_staff';
      }
      
      // DISCHARGE operations that should trigger popup forms
      if (message.includes('discharge') && (message.includes('patient') || message.includes('discharge'))) {
        console.log('✅ Fallback detected: discharge_patient');
        return 'discharge_patient';
      }
      
      // Check for equipment usage first (before equipment creation)
      if (message.includes('equipment') && (message.includes('usage') || message.includes('assign') || message.includes('used by') || message.includes('patient id') || message.includes('inventory') || message.includes('tracking'))) {
        console.log('🤖 Equipment usage/inventory detected - using AI processing');
        return 'ai_processing';
      }
      if ((message.includes('create') || message.includes('add') || message.includes('new')) && message.includes('equipment') && !message.includes('category') && !message.includes('usage') && !message.includes('assign')) {
        console.log('✅ Fallback detected: create_equipment');
        return 'create_equipment';
      }
      // Check for supply usage first (before supply creation)
      if (message.includes('supply') && (message.includes('usage') || message.includes('assign') || message.includes('used by') || message.includes('patient id') || message.includes('inventory') || message.includes('tracking') || message.includes('consumption'))) {
        console.log('🤖 Supply usage/inventory detected - using AI processing');
        return 'ai_processing';
      }
      if ((message.includes('create') || message.includes('add') || message.includes('new')) && message.includes('supply') && !message.includes('category') && !message.includes('usage') && !message.includes('assign')) {
        console.log('✅ Fallback detected: create_supply');
        return 'create_supply';
      }
      if ((message.includes('create') || message.includes('add') || message.includes('new')) && message.includes('equipment') && message.includes('category')) {
        console.log('✅ Fallback detected: create_equipment_category');
        return 'create_equipment_category';
      }
      if ((message.includes('create') || message.includes('add') || message.includes('new')) && message.includes('supply') && message.includes('category')) {
        console.log('✅ Fallback detected: create_supply_category');
        return 'create_supply_category';
      }
      
      // Default to AI processing for all other cases
      console.log('🤖 Fallback defaulting to: ai_processing');
      return 'ai_processing';
    }

    try {
      const response = await fetch('https://api.openai.com/v1/chat/completions', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${openaiApiKey}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          model: 'gpt-4-turbo-preview',
          messages: [
            {
              role: 'system',
              content: `You are an intelligent intent detection system for a hospital management application with multi-agent backend tools. 

POPUP FORM TRIGGERS (Only these EXACT 12 tools should show popup forms):
1. create_user: User creation popup form
2. create_patient: Patient admission popup form  
3. create_legacy_user: Legacy user creation popup form
4. create_department: Department creation popup form
5. create_room: Room creation popup form
6. create_bed: Bed creation popup form
7. create_staff: Staff creation popup form
8. create_equipment: Equipment creation popup form (ONLY for NEW equipment registration)
9. create_supply: Supply creation popup form (ONLY for NEW supply registration)
10. create_equipment_category: Equipment category creation popup form
11. create_supply_category: Supply category creation popup form
12. discharge_patient: Patient discharge workflow form

CRITICAL USAGE vs CREATION DISTINCTION:
- "add equipment usage" or "equipment usage" → ai_processing (add_equipment_usage tool)
- "add supply usage" or "supply usage" → ai_processing (add_supply_usage tool)
- "equipment assignment" or "assign equipment" → ai_processing (assignment tools)
- "supply assignment" or "assign supply" → ai_processing (assignment tools)
- "create equipment" or "register equipment" → create_equipment popup form
- "create supply" or "register supply" → create_supply popup form

IMPORTANT KEYWORDS FOR AI PROCESSING (NOT popup forms):
- Any message containing "usage", "assign", "assignment", "used by", "patient id", "inventory", "tracking", "consumption" should use ai_processing
- Equipment/supply USAGE, INVENTORY, TRACKING = ai_processing
- Equipment/supply CREATION = popup forms
- Patient DISCHARGE = discharge_patient popup form

RULES:
1. Only the exact 12 tools above trigger popup forms
2. All USAGE, ASSIGNMENT, TRACKING, INVENTORY operations use AI processing
3. All listing, searching, updating, deleting operations use AI processing
4. Staff meetings = AI processing (schedule_meeting tool)
5. Patient discharge = discharge_patient popup form

Return ONLY one of these values:
- "create_user" for system user creation
- "create_patient" for patient registration/admission  
- "create_legacy_user" for legacy user creation
- "create_department" for department creation
- "create_room" for room creation
- "create_bed" for bed creation
- "create_staff" for staff hiring/registration
- "create_equipment" for NEW equipment registration (not usage/inventory)
- "create_supply" for NEW supply registration (not usage/inventory)
- "create_equipment_category" for equipment category creation
- "create_supply_category" for supply category creation
- "discharge_patient" for patient discharge workflow
- "ai_processing" for everything else (including equipment/supply usage, inventory, assignments, updates, searches, etc.)

Examples:
- "Register a new patient" → create_patient
- "Add new staff member" → create_staff  
- "Create cardiology department" → create_department
- "Add new equipment" → create_equipment (only for NEW equipment registration)
- "Register equipment" → create_equipment
- "Create equipment category" → create_equipment_category
- "Add equipment usage for patient" → ai_processing
- "Add equipment usage Equipment ID: EQ001" → ai_processing
- "Record equipment usage" → ai_processing
- "Equipment usage tracking" → ai_processing
- "Equipment inventory" → ai_processing
- "Assign equipment to patient" → ai_processing
- "Add new supply" → create_supply (only for NEW supply registration)
- "Create supply category" → create_supply_category
- "Add supply usage" → ai_processing
- "Supply usage tracking" → ai_processing
- "Supply inventory usage" → ai_processing
- "Supply inventory tracking" → ai_processing
- "Supply consumption" → ai_processing
- "Schedule staff meeting" → ai_processing
- "List all patients" → ai_processing
- "Update bed status" → ai_processing`
            },
            {
              role: 'user',
              content: userMessage
            }
          ],
          max_tokens: 50,
          temperature: 0.1
        })
      });

      if (!response.ok) {
        console.warn('Intent detection API call failed:', response.status);
        return null;
      }

      const result = await response.json();
      const intent = result.choices[0].message.content.trim().toLowerCase();
      
      console.log('🤖 AI Intent Detection Result:', userMessage, '->', intent);
      
      // STRICT VALIDATION: Only these exact 12 create tools should show popup forms
      // All other tools use AI processing
      const POPUP_FORM_TOOLS = [
        'create_user',                  // System user creation
        'create_patient',               // Patient registration/admission  
        'create_legacy_user',           // Legacy user creation
        'create_department',            // Department creation
        'create_room',                  // Room creation
        'create_bed',                   // Bed creation
        'create_staff',                 // Staff hiring/registration
        'create_equipment',             // Equipment registration
        'create_supply',                // Supply registration
        'create_equipment_category',    // Equipment category creation
        'create_supply_category'        // Supply category creation
      ];
      
      if (POPUP_FORM_TOOLS.includes(intent)) {
        console.log('✅ POPUP FORM TRIGGERED for:', intent);
        return intent;
      }
      
      console.log('🤖 AI PROCESSING MODE for:', intent || 'unrecognized intent');
      return 'ai_processing'; // Default to AI processing for everything else
    } catch (error) {
      console.warn('Intent detection error:', error);
      return 'ai_processing'; // Default to AI processing on error
    }
  };

  /**
   * Smart conversation flow: 
   * - CREATE tools (create_user, create_patient, etc.) → Show popup forms
   * - ALL OTHER tools (list, search, update, delete, etc.) → Intelligent AI processing
   */
  const sendMessageClaudeStyle = async (customMessage = null, isFromVoiceInput = false) => {
    const messageToSend = customMessage || inputMessage.trim();
    if (!messageToSend || !isConnected || isLoading) return;

    const userMessage = messageToSend;
    if (!customMessage) {
      setInputMessage('');
    }
    setIsLoading(true);
    
    // Hide action buttons after first query
    if (showActionButtons) {
      setShowActionButtons(false);
      
      // Correct viewport after action buttons transition on mobile
      if (isMobileDevice()) {
        setTimeout(() => {
          const vh = window.innerHeight * 0.01;
          document.documentElement.style.setProperty('--vh', `${vh}px`);
          window.scrollTo(0, 0);
          document.body.style.height = '100%';
        }, 600); // Wait for transition to complete (500ms + buffer)
      }
    }

    // Add user message only if it's not from voice input (voice input already adds the message)
    if (!isFromVoiceInput) {
      const userMsg = {
        id: Date.now(),
        text: userMessage,
        sender: 'user',
        timestamp: new Date().toLocaleTimeString()
      };
      setMessages(prev => [...prev, userMsg]);
    }

    // Quick pattern: intercept 'record patient supply usage' messages and call the backend directly
    // try {
    //   const textLower = userMessage.toLowerCase();
    //   if (textLower.includes('record patient supply usage') || textLower.includes('record patient supply') || textLower.includes('administered')) {
    //     // Simple field extraction using regexes for common fields
    //     const getField = (regex) => {
    //       const m = userMessage.match(regex);
    //       return m ? m[1].trim() : null;
    //     };

    //     const patient_number = getField(/patient\s*(?:id|number)[:\s]+(P[0-9A-Za-z\-]+)/i) || getField(/patient[:\s]+(P[0-9A-Za-z\-]+)/i);
    //     const supply_item_code = getField(/supply\s*(?:item\s*)?code[:\s]+([A-Z0-9_\-]+)/i);
    //     const quantity_used = parseInt(getField(/quantity\s*used[:\s]+(\d+)/i) || '1', 10) || 1;
    //     const date_of_usage = getField(/date\s*of\s*usage[:\s]+([0-9\-\/]+)/i);
    //     const employee_id = getField(/staff\s*id[:\s]+([A-Z0-9_\-]+)/i) || getField(/employee\s*id[:\s]+([A-Z0-9_\-]+)/i);
    //     const notes = getField(/notes[:\s]+(.+)/i) || null;

    //     // If required fields present, call backend tool directly to persist
    //     if (patient_number && supply_item_code) {
    //       setIsLoading(true);
    //       const args = {
    //         patient_number,
    //         supply_item_code,
    //         quantity_used,
    //         employee_id,
    //         date_of_usage,
    //         notes
    //       };

    //       try {
    //         const resp = await aiMcpServiceRef.current.callToolDirectly('record_patient_supply_usage_by_code', args);
    //         // resp may be the raw tool return; format for display
    //         const success = resp && (resp.success === true || (resp.result && resp.result.success === true));
    //         const messageText = success ? `✅ Supply usage recorded for ${supply_item_code} (patient ${patient_number})` : `⚠️ Failed to record supply usage: ${JSON.stringify(resp)}`;

    //         const botMsg = { id: Date.now() + 1, text: messageText, sender: 'system', timestamp: new Date().toLocaleTimeString() };
    //         setMessages(prev => [...prev, botMsg]);
    //         setIsLoading(false);
    //         setInputMessage('');
    //         return; // stop further AI processing
    //       } catch (err) {
    //         const botMsg = { id: Date.now() + 1, text: `⚠️ Error recording supply usage: ${err.message || err}`, sender: 'system', timestamp: new Date().toLocaleTimeString() };
    //         setMessages(prev => [...prev, botMsg]);
    //         setIsLoading(false);
    //         return;
    //       }
    //     }
    //   }
    // } catch (err) {
    //   // Fall back to normal AI processing on parser errors
    //   console.warn('Supply usage parse error:', err);
    // }

    // 🤖 INTELLIGENT AI INTENT DETECTION FIRST
    try {
      console.log('🔍 Starting intent detection for:', userMessage);
      const detectedIntent = await detectIntentWithAI(userMessage);
      console.log('🎯 Detected intent:', detectedIntent);
      
      if (detectedIntent && detectedIntent !== 'ai_processing') {
        setIsLoading(false);
        
        console.log('🎯 POPUP FORM HANDLER - Processing intent:', detectedIntent);
        console.log('🎯 Current state - showPatientAdmissionForm:', showPatientAdmissionForm);
        
        // Show appropriate popup form based on AI detection
        switch (detectedIntent) {
          case 'create_patient':
            console.log('📝 Opening Patient Admission Form');
            console.log('📝 About to set showPatientAdmissionForm to true');
            setShowPatientAdmissionForm(true);
            console.log('📝 After setting showPatientAdmissionForm to true');
            const patientMsg = {
              id: Date.now() + 1,
              text: "I detected you want to register a new patient! I've opened the patient admission form for you.",
              sender: 'ai',
              timestamp: new Date().toLocaleTimeString()
            };
            setMessages(prev => [...prev, patientMsg]);
            return;
            
          case 'create_department':
            console.log('🏥 Opening Department Creation Form');
            await loadDropdownOptions(); // Load users for head_doctor_id
            setShowDepartmentForm(true);
            const deptMsg = {
              id: Date.now() + 1,
              text: "I detected you want to create a new department! I've opened the department creation form for you. The dropdown menus are being populated with available users for the head doctor selection.",
              sender: 'ai',
              timestamp: new Date().toLocaleTimeString()
            };
            setMessages(prev => [...prev, deptMsg]);
            return;
            
          case 'create_staff':
            console.log('👥 Opening Staff Creation Form');
            await loadDropdownOptions(); // Load users and departments
            setShowStaffForm(true);
            const staffMsg = {
              id: Date.now() + 1,
              text: "I detected you want to add a new staff member! I've opened the staff creation form for you. Please select a user and department from the dropdown menus.",
              sender: 'ai',
              timestamp: new Date().toLocaleTimeString()
            };
            setMessages(prev => [...prev, staffMsg]);
            return;
            
          case 'create_user':
            console.log('👤 Opening User Creation Form');
            setShowUserForm(true);
            const userMsg = {
              id: Date.now() + 1,
              text: "I detected you want to create a new user! I've opened the user creation form for you. This form doesn't require foreign key selections.",
              sender: 'ai',
              timestamp: new Date().toLocaleTimeString()
            };
            setMessages(prev => [...prev, userMsg]);
            return;
            
          case 'create_room':
            console.log('🏠 Opening Room Creation Form');
            await loadDropdownOptions(); // Load departments
            setShowRoomForm(true);
            const roomMsg = {
              id: Date.now() + 1,
              text: "I detected you want to create a new room! I've opened the room creation form for you. Please select a department from the dropdown menu.",
              sender: 'ai',
              timestamp: new Date().toLocaleTimeString()
            };
            setMessages(prev => [...prev, roomMsg]);
            return;
            
          case 'create_bed':
            console.log('🛏️ Opening Bed Creation Form');
            await loadDropdownOptions(); // Load rooms
            setShowBedForm(true);
            const bedMsg = {
              id: Date.now() + 1,
              text: "I detected you want to add a new bed! I've opened the bed creation form for you. Please select a room from the dropdown menu.",
              sender: 'ai',
              timestamp: new Date().toLocaleTimeString()
            };
            setMessages(prev => [...prev, bedMsg]);
            return;
            
          case 'create_equipment':
            console.log('⚙️ Opening Equipment Creation Form');
            await loadDropdownOptions(); // Load departments and categories
            setShowEquipmentForm(true);
            const equipMsg = {
              id: Date.now() + 1,
              text: "I detected you want to add new equipment! I've opened the equipment creation form for you. Please select a department and category from the dropdown menus.",
              sender: 'ai',
              timestamp: new Date().toLocaleTimeString()
            };
            setMessages(prev => [...prev, equipMsg]);
            return;
            
          case 'create_supply':
            console.log('📦 Opening Supply Creation Form');
            await loadDropdownOptions(); // Load categories
            setShowSupplyForm(true);
            const supplyMsg = {
              id: Date.now() + 1,
              text: "I detected you want to add new supplies! I've opened the supply creation form for you. Please select a category from the dropdown menu.",
              sender: 'ai',
              timestamp: new Date().toLocaleTimeString()
            };
            setMessages(prev => [...prev, supplyMsg]);
            return;
            
          case 'create_equipment_category':
            console.log('🏷️ Opening Equipment Category Creation Form');
            setShowEquipmentCategoryForm(true);
            const equipCatMsg = {
              id: Date.now() + 1,
              text: "I detected you want to create an equipment category! I've opened the equipment category creation form for you. Please provide a name and optional description.",
              sender: 'ai',
              timestamp: new Date().toLocaleTimeString()
            };
            setMessages(prev => [...prev, equipCatMsg]);
            return;
            
          case 'create_supply_category':
            console.log('🏷️ Opening Supply Category Creation Form');
            setShowSupplyCategoryForm(true);
            const supplyCatMsg = {
              id: Date.now() + 1,
              text: "I detected you want to create a supply category! I've opened the supply category creation form for you. Please provide a name and optional description.",
              sender: 'ai',
              timestamp: new Date().toLocaleTimeString()
            };
            setMessages(prev => [...prev, supplyCatMsg]);
            return;
            
          case 'discharge_patient':
            console.log('🏥 Opening Patient Discharge Workflow Form');
            setShowDischargeForm(true);
            const dischargeMsg = {
              id: Date.now() + 1,
              text: "I detected you want to discharge a patient! I've opened the comprehensive discharge workflow form for you. This will handle the complete discharge process including bed turnover and cleaning.",
              sender: 'ai',
              timestamp: new Date().toLocaleTimeString()
            };
            setMessages(prev => [...prev, dischargeMsg]);
            return;
            
          case 'create_legacy_user':
            console.log('👤 Opening Legacy User Creation Form');
            setShowLegacyUserForm(true);
            const legacyMsg = {
              id: Date.now() + 1,
              text: "I detected you want to create a legacy user! I've opened the legacy user creation form for you.",
              sender: 'ai',
              timestamp: new Date().toLocaleTimeString()
            };
            setMessages(prev => [...prev, legacyMsg]);
            return;
            
          default:
            console.warn('⚠️ Unknown popup intent detected:', detectedIntent, '- Falling back to AI processing');
            // Fall through to AI processing
        }
      }
      
      // If AI detected 'ai_processing' or no specific form intent, proceed with intelligent AI processing
      if (detectedIntent === 'ai_processing' || !detectedIntent) {
        console.log('🤖 AI PROCESSING MODE: Using intelligent backend agent tools for:', userMessage);
        // Skip fallback keyword detection and go directly to AI processing
      }
      
    } catch (error) {
      console.warn('AI intent detection failed, proceeding with AI processing:', error);
    }

    // For all other requests, use intelligent AI processing with the backend agents
    // The AI will analyze the request and call the appropriate backend tools automatically
    console.log('🤖 Proceeding with Intelligent AI Processing');

    let thinkingMessageId = null;
    let thinkingStartTime = null;

    try {
      // Show contextual thinking for all requests (since AI will determine the right tools)
      thinkingStartTime = Date.now();
      thinkingMessageId = Date.now() + Math.random();
      
      // Generate contextual thinking message based on user input
      let thinkingText = 'Processing ';
      if (userMessage.toLowerCase().includes('list') || userMessage.toLowerCase().includes('show')) {
        thinkingText = 'Retrieving ';
      } else if (userMessage.toLowerCase().includes('find') || userMessage.toLowerCase().includes('search')) {
        thinkingText = 'Searching for ';
      } else if (userMessage.toLowerCase().includes('update') || userMessage.toLowerCase().includes('assign')) {
        thinkingText = 'Updating ';
      } else if (userMessage.toLowerCase().includes('meeting') || userMessage.toLowerCase().includes('schedule')) {
        thinkingText = 'Scheduling ';
      }

      // Add the subject based on keywords
      if (userMessage.toLowerCase().includes('patient')) {
        thinkingText += 'patient information';
      } else if (userMessage.toLowerCase().includes('staff')) {
        thinkingText += 'staff records';
      } else if (userMessage.toLowerCase().includes('bed')) {
        thinkingText += 'bed information';
      } else if (userMessage.toLowerCase().includes('department')) {
        thinkingText += 'department data';
      } else if (userMessage.toLowerCase().includes('equipment')) {
        thinkingText += 'equipment status';
      } else if (userMessage.toLowerCase().includes('supply')) {
        thinkingText += 'supply inventory';
      } else if (userMessage.toLowerCase().includes('meeting')) {
        thinkingText += 'meeting details';
      } else {
        thinkingText += 'your request';
      }

      const thinkingMessage = {
        id: thinkingMessageId,
        text: thinkingText,
        sender: 'ai',
        timestamp: new Date().toLocaleTimeString(),
        isThinking: true,
        startTime: thinkingStartTime
      };
      setMessages(prev => [...prev, thinkingMessage]);

      // Process the request
      const response = await aiMcpServiceRef.current.processRequest(userMessage);
      
      // Remove thinking message if present
      if (thinkingMessageId) {
        setMessages(prev => prev.filter(msg => msg.id !== thinkingMessageId));
        
        // Remove artificial delay for faster response
        // await new Promise(resolve => setTimeout(resolve, 200));
      }
      
      // 🎯 HANDLE POPUP FORM INTENTS FROM SERVICE
      if (response.success && response.showPopupForm && response.popupIntent) {
        console.log('🎯 SERVICE POPUP INTENT DETECTED:', response.popupIntent);
        
        // Load dropdown options if needed for certain forms
        const formsNeedingDropdowns = ['create_staff', 'create_department', 'create_room', 'create_bed', 'create_equipment', 'create_supply'];
        if (formsNeedingDropdowns.includes(response.popupIntent)) {
          await loadDropdownOptions();
        }
        
        // Show the appropriate popup form
        switch (response.popupIntent) {
          case 'create_patient':
            setShowPatientAdmissionForm(true);
            break;
          case 'create_user':
            setShowUserForm(true);
            break;
          case 'create_staff':
            setShowStaffForm(true);
            break;
          case 'create_department':
            setShowDepartmentForm(true);
            break;
          case 'create_room':
            setShowRoomForm(true);
            break;
          case 'create_bed':
            setShowBedForm(true);
            break;
          case 'create_equipment':
            setShowEquipmentForm(true);
            break;
          case 'create_supply':
            setShowSupplyForm(true);
            break;
          case 'create_legacy_user':
            setShowLegacyUserForm(true);
            break;
          case 'create_equipment_category':
            setShowEquipmentCategoryForm(true);
            break;
          case 'create_supply_category':
            setShowSupplyCategoryForm(true);
            break;
          default:
            console.warn('Unknown popup intent:', response.popupIntent);
        }
        
        // Add the service response message
        const serviceMessage = {
          id: Date.now() + 1,
          text: response.message,
          sender: 'ai',
          timestamp: new Date().toLocaleTimeString()
        };
        setMessages(prev => [...prev, serviceMessage]);
        
        setIsLoading(false);
        return; // Exit early for popup forms
      }
      
  /**
   * Get agent information for a specific tool
   */
  const getAgentForTool = (toolName) => {
    if (!aiMcpServiceRef.current?.mcpClient?.getAgents) return null;
    
    const agents = aiMcpServiceRef.current.mcpClient.getAgents();
    
    // Tool to agent mapping based on the backend multi-agent system
    const toolToAgentMap = {
      // User Management Agent tools
      'create_user': 'User Management Agent',
      'get_user_by_id': 'User Management Agent',
      'update_user': 'User Management Agent',
      'delete_user': 'User Management Agent',
      'list_users': 'User Management Agent',
      'search_users': 'User Management Agent',
      'create_legacy_user': 'User Management Agent',
      
      // Department Management Agent tools
      'create_department': 'Department Management Agent',
      'get_department_by_id': 'Department Management Agent',
      'update_department': 'Department Management Agent',
      'delete_department': 'Department Management Agent',
      'list_departments': 'Department Management Agent',
      
      // Patient Management Agent tools
      'create_patient': 'Patient Management Agent',
      'get_patient_by_id': 'Patient Management Agent',
      'update_patient': 'Patient Management Agent',
      'delete_patient': 'Patient Management Agent',
      'list_patients': 'Patient Management Agent',
      'search_patients': 'Patient Management Agent',
      'get_patient_by_number': 'Patient Management Agent',
      
      // Room & Bed Management Agent tools
      'create_room': 'Room & Bed Management Agent',
      'get_room_by_id': 'Room & Bed Management Agent',
      'update_room': 'Room & Bed Management Agent',
      'delete_room': 'Room & Bed Management Agent',
      'list_rooms': 'Room & Bed Management Agent',
      'create_bed': 'Room & Bed Management Agent',
      'get_bed_by_id': 'Room & Bed Management Agent',
      'update_bed': 'Room & Bed Management Agent',
      'list_beds': 'Room & Bed Management Agent',
      'assign_bed_to_patient': 'Room & Bed Management Agent',
      'get_bed_status_with_time_remaining': 'Room & Bed Management Agent',
      'discharge_patient_complete': 'Room & Bed Management Agent',
      
      // Staff Management Agent tools
      'create_staff': 'Staff Management Agent',
      'get_staff_by_id': 'Staff Management Agent',
      'update_staff': 'Staff Management Agent',
      'delete_staff': 'Staff Management Agent',
      'list_staff': 'Staff Management Agent',
      'search_staff': 'Staff Management Agent',
      'assign_staff_to_patient': 'Staff Management Agent',
      
      // Equipment Management Agent tools
      'create_equipment': 'Equipment Management Agent',
      'get_equipment_by_id': 'Equipment Management Agent',
      'update_equipment': 'Equipment Management Agent',
      'delete_equipment': 'Equipment Management Agent',
      'list_equipment': 'Equipment Management Agent',
      'search_equipment': 'Equipment Management Agent',
      'create_equipment_category': 'Equipment Management Agent',
      'list_equipment_categories': 'Equipment Management Agent',
      'add_equipment_usage_by_codes': 'Equipment Management Agent',
      'list_equipment_usage': 'Equipment Management Agent',
      
      // Inventory Management Agent tools
      'create_supply': 'Inventory Management Agent',
      'get_supply_by_id': 'Inventory Management Agent',
      'update_supply': 'Inventory Management Agent',
      'delete_supply': 'Inventory Management Agent',
      'list_supplies': 'Inventory Management Agent',
      'search_supplies': 'Inventory Management Agent',
      'create_supply_category': 'Inventory Management Agent',
      'list_supply_categories': 'Inventory Management Agent',
      'add_supply_usage_by_codes': 'Inventory Management Agent',
      'list_supply_usage': 'Inventory Management Agent',
      'update_supply_stock': 'Inventory Management Agent',
      
      // Meeting Scheduling Agent tools
      'schedule_meeting': 'Meeting Scheduling Agent',
      'list_meetings': 'Meeting Scheduling Agent',
      'update_meeting': 'Meeting Scheduling Agent',
      'cancel_meeting': 'Meeting Scheduling Agent',
      'get_meeting_by_id': 'Meeting Scheduling Agent',
      'search_meetings': 'Meeting Scheduling Agent',
      
      // Medical Document Agent tools
      'upload_document': 'Medical Document Agent',
      'get_document_by_id': 'Medical Document Agent',
      'list_documents': 'Medical Document Agent',
      'search_documents': 'Medical Document Agent',
      'update_document': 'Medical Document Agent',
      'delete_document': 'Medical Document Agent',
      'extract_medical_entities': 'Medical Document Agent',
      'summarize_document': 'Medical Document Agent',
      'get_patient_documents': 'Medical Document Agent',
      
      // Discharge Report Agent tools
      'generate_discharge_report': 'Discharge Report Agent',
      'get_discharge_report': 'Discharge Report Agent',
      'list_discharge_reports': 'Discharge Report Agent',
      'update_discharge_report': 'Discharge Report Agent',
      'search_discharge_reports': 'Discharge Report Agent',
      
      // Patient Supply Usage Agent tools
      'assign_supplies_to_patient': 'Patient Supply Usage Agent',
      'get_patient_supply_usage': 'Patient Supply Usage Agent',
      'list_patient_assignments': 'Patient Supply Usage Agent',
      'update_patient_assignment': 'Patient Supply Usage Agent'
    };
    
    const agentName = toolToAgentMap[toolName];
    return agentName ? agents.find(agent => agent.name === agentName) : null;
  };

      if (response.success) {
        // Show tool execution if tools were called
        if (response.functionCalls && response.functionCalls.length > 0) {
          response.functionCalls.forEach((call, index) => {
            // Get agent information for this tool
            const agent = getAgentForTool(call.function);
            const agentPrefix = agent ? `👤 ${agent.name} ➤ ` : '🔧 ';
            
            // Create contextual thinking message for each tool
            let thinkingText = '';
            switch (call.function) {
              case 'search_patients':
                thinkingText = `${agentPrefix}Found a patient named ${call.arguments?.first_name || 'the patient'}.`;
                break;
              case 'list_patients':
                thinkingText = `${agentPrefix}Retrieved patient registry with all available patients.`;
                break;
              case 'list_beds':
                thinkingText = `${agentPrefix}Checked bed assignments and availability status.`;
                break;
              case 'list_departments':
                thinkingText = `${agentPrefix}Retrieved all hospital departments and their information.`;
                break;
              case 'list_staff':
                thinkingText = `${agentPrefix}Retrieved hospital staff directory.`;
                break;
              case 'get_patient_by_id':
                thinkingText = `${agentPrefix}Found detailed information for patient ${call.arguments?.patient_id || 'ID'}.`;
                break;
              case 'get_staff_by_id':
                thinkingText = `${agentPrefix}Located staff member ${call.arguments?.staff_id || 'information'}.`;
                break;
              case 'create_patient':
                thinkingText = `${agentPrefix}Successfully created new patient record.`;
                break;
              case 'assign_bed_to_patient':
                thinkingText = `${agentPrefix}Assigned bed to patient successfully.`;
                break;
              case 'list_equipment':
                thinkingText = `${agentPrefix}Retrieved medical equipment inventory.`;
                break;
              case 'list_supplies':
                thinkingText = `${agentPrefix}Retrieved medical supplies inventory.`;
                break;
              case 'schedule_meeting':
                thinkingText = `${agentPrefix}Scheduled meeting successfully.`;
                break;
              case 'discharge_patient_complete':
                thinkingText = `${agentPrefix}Processing complete patient discharge workflow.`;
                break;
              default:
                thinkingText = `${agentPrefix}Executed ${call.function.replace(/_/g, ' ')} successfully.`;
            }

            const toolMessage = {
              id: Date.now() + index + 100,
              text: thinkingText,
              sender: 'ai',
              timestamp: new Date().toLocaleTimeString(),
              isThinking: true,
              toolFunction: call.function,
              startTime: Date.now() // No artificial delay
            };
            setMessages(prev => [...prev, toolMessage]);
          });
        }

        // Final response with the processed data
        const finalResponse = {
          id: Date.now() + 1000,
          text: response.response || response.message || 'Here\'s what I found based on your request.',
          sender: 'ai',
          timestamp: new Date().toLocaleTimeString(),
          isFinalAnswer: true
        };
        setMessages(prev => [...prev, finalResponse]);

        // If this is a response to voice input, speak the response
        if (isFromVoiceInput) {
          setTimeout(() => {
            speakTextWithOpenAI(response.response || response.message || 'Here\'s what I found based on your request.', true);
          }, 500);
        }
        
      } else {
        // Direct error response without thinking for simple errors
        const errorResponse = {
          id: Date.now() + 1000,
          text: `I apologize, but I encountered an error: ${response.error || 'Unknown error occurred'}\n\nPlease try rephrasing your request or let me know if you need help with something specific.`,
          sender: 'ai',
          timestamp: new Date().toLocaleTimeString(),
          isError: true
        };
        setMessages(prev => [...prev, errorResponse]);

        // If this is a response to voice input, speak the error message
        if (isFromVoiceInput) {
          setTimeout(() => {
            speakTextWithOpenAI(`I apologize, but I encountered an error: ${response.error || 'Unknown error occurred'}. Please try rephrasing your request.`, true);
          }, 500);
        }
      }
      
    } catch (error) {
      console.error('❌ Send message failed:', error);
      
      // Remove thinking message if present
      if (thinkingMessageId) {
        setMessages(prev => prev.filter(msg => msg.id !== thinkingMessageId));
      }

      // Direct error message
      const errorMsg = {
        id: Date.now() + 1000,
        text: `I'm having trouble processing your request: ${error.message}\n\nThis might be a temporary connection issue. Please try again in a moment.`,
        sender: 'ai',
        timestamp: new Date().toLocaleTimeString(),
        isError: true
      };
      setMessages(prev => [...prev, errorMsg]);

      // If this is a response to voice input, speak the error message
      if (isFromVoiceInput) {
        setTimeout(() => {
          speakTextWithOpenAI(`I'm having trouble processing your request. This might be a temporary connection issue. Could you please try again?`, true);
        }, 500);
      }
    } finally {
      setIsLoading(false);
      
      // Auto-focus the input field after AI response (smart focus prevents mobile keyboard popup)
      smartFocusInput(100);
    }
  };

  /**
   * Format message text to render markdown formatting and detect discharge reports
   */
  const formatMessageText = (text) => {
    if (!text) return '';
    
    // Check if this message contains a discharge report (but exclude download success messages)
    const isDischargeReport = (text.includes('### Patient Discharge Report') || 
                              text.includes('**Report Number:**') || 
                              text.match(/DR-\d{8}-[A-F0-9]{8}/)) &&
                              !text.includes('PDF Download Complete') &&
                              !text.includes('downloaded to your Downloads folder');
    
    let formattedText = text
      // Bold formatting: **text** -> <strong>text</strong>
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      // Italic formatting: *text* -> <em>text</em>
      .replace(/(?<!\*)\*([^*]+)\*(?!\*)/g, '<em>$1</em>')
      // Convert line breaks to <br> tags
      .replace(/\n/g, '<br>')
      // Handle bullet points with proper spacing
      .replace(/^• (.*$)/gm, '<div class="ml-4">• $1</div>')
      // Handle double spaces
      .replace(/\s{2}/g, '&nbsp;&nbsp;');
    
    // If this is a discharge report, extract the report number and add download button
    if (isDischargeReport) {
      const reportNumberMatch = text.match(/DR-\d{8}-[A-F0-9]{8}/);
      if (reportNumberMatch && !formattedText.includes('downloadDischargeReportPDF')) {
        const reportNumber = reportNumberMatch[0];
        
        // Add download button HTML after the formatted text
        formattedText += `
          <div class="mt-1 px-3 py-1.5 bg-gray-800 border border-gray-600 rounded-lg">
            <div class="flex items-center justify-between">
              <div class="text-xs text-gray-300 flex items-center space-x-1.5">
                <span class="w-1.5 h-1.5 bg-green-400 rounded-full"></span>
                <span><strong>Report Generated: ${reportNumber}</strong></span>
              </div>
              <button 
                onclick="downloadDischargeReportPDF('${reportNumber}')"
                class="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-xs rounded-lg font-medium transition-all duration-200 flex items-center space-x-1.5 shadow-md hover:shadow-lg"
                title="Download this discharge report as PDF"
              >
                <span class="text-xs">📥</span>
                <span>Download as PDF</span>
              </button>
            </div>
          </div>
        `;
      }
    }
    
    return formattedText;
  };

  /**
   * Download discharge report as PDF - called from dynamically generated buttons
   */
  const downloadDischargeReportPDF = async (reportNumber) => {
    try {
      console.log('📥 Downloading discharge report PDF:', reportNumber);
      
      // Show loading message in chat
      const loadingMessage = {
        id: Date.now() + Math.random(),
        text: `⏳ Downloading discharge report ${reportNumber} as PDF...`,
        sender: 'assistant',
        timestamp: new Date(),
        isLoading: true
      };
      setMessages(prev => [...prev, loadingMessage]);
      
      // Import PDFDownloadManager
      const PDFDownloadManager = (await import('../utils/pdfDownloadManager.js')).default;
      const pdfManager = new PDFDownloadManager();
      
      // Extract patient name from the last few messages if available
      let patientName = 'Patient';
      const recentMessages = messages.slice(-5);
      for (const msg of recentMessages) {
        const nameMatch = msg.text.match(/Patient:\s*([^,\n]+)/i) || 
                         msg.text.match(/Name:\s*([^,\n]+)/i) ||
                         msg.text.match(/\*\*Name:\*\*\s*([^,\n]+)/i);
        if (nameMatch) {
          patientName = nameMatch[1].trim();
          break;
        }
      }
      
      // Download the PDF
      const result = await pdfManager.downloadDischargeReportPDF(reportNumber, patientName);
      
      // Remove loading message
      setMessages(prev => prev.filter(msg => msg.id !== loadingMessage.id));
      
      if (result.success) {
        // Add success message
        const successMessage = {
          id: Date.now() + Math.random(),
          text: `✅ **PDF Download Complete**\n\n📁 **File:** ${result.filename}\n📊 **Size:** ${pdfManager.formatBytes(result.fileSize)}\n💾 **Saved to:** Local browser storage\n\n🎯 The PDF has been automatically downloaded to your Downloads folder and saved in local storage for future access.`,
          sender: 'assistant',
          timestamp: new Date(),
          isFinalAnswer: true
        };
        setMessages(prev => [...prev, successMessage]);
      } else {
        // Add error message
        const errorMessage = {
          id: Date.now() + Math.random(),
          text: `❌ **Download Failed**\n\nError: ${result.error}\n\nPlease try again or contact support if the issue persists.`,
          sender: 'assistant',
          timestamp: new Date(),
          isError: true
        };
        setMessages(prev => [...prev, errorMessage]);
      }
      
    } catch (error) {
      console.error('❌ PDF download error:', error);
      
      // Remove any loading messages
      setMessages(prev => prev.filter(msg => !msg.isLoading));
      
      // Add error message
      const errorMessage = {
        id: Date.now() + Math.random(),
        text: `❌ **Download Error**\n\nFailed to download PDF: ${error.message}\n\nPlease try again later.`,
        sender: 'assistant',
        timestamp: new Date(),
        isError: true
      };
      setMessages(prev => [...prev, errorMessage]);
    }
  };

  // Make the download function globally accessible for the dynamically generated buttons
  useEffect(() => {
    window.downloadDischargeReportPDF = downloadDischargeReportPDF;
    
    // Cleanup when component unmounts
    return () => {
      delete window.downloadDischargeReportPDF;
    };
  }, [messages]); // Re-register when messages change to capture current state

  // Handle mobile viewport and keyboard behavior
  useEffect(() => {
    if (typeof window !== 'undefined' && isMobileDevice()) {
      // Set viewport height custom property for mobile
      const setVH = () => {
        const vh = window.innerHeight * 0.01;
        document.documentElement.style.setProperty('--vh', `${vh}px`);
        
        // Force height to fill entire viewport
        document.documentElement.style.height = '100%';
        document.body.style.height = '100%';
        document.body.style.minHeight = '100vh';
        document.body.style.minHeight = '100dvh';
      };
      
      // Set initial viewport height MULTIPLE TIMES to ensure it takes effect
      setVH();
      setTimeout(setVH, 100);  // Retry after 100ms
      setTimeout(setVH, 300);  // Retry after 300ms
      setTimeout(setVH, 1000); // Final retry after 1 second
      
      // Prevent body scroll on mobile, but allow input to move with keyboard
      document.body.style.overflow = 'hidden';
      document.body.style.backgroundColor = '#1a1a1a';
      document.documentElement.style.backgroundColor = '#1a1a1a';
      document.body.style.margin = '0';
      document.body.style.padding = '0';
      
      // Force immediate layout correction
      window.scrollTo(0, 0);
      
      // Throttled resize handler
      let timeoutId;
      const handleResize = () => {
        clearTimeout(timeoutId);
        timeoutId = setTimeout(setVH, 150);
      };
      
      // Listen for viewport changes
      window.addEventListener('resize', handleResize);
      window.addEventListener('orientationchange', () => {
        setTimeout(setVH, 500); // Delay for orientation change
      });
      
      // Force layout correction on load complete
      window.addEventListener('load', () => {
        setTimeout(setVH, 100);
        window.scrollTo(0, 0);
      });
      
      // Also trigger on DOM content loaded
      if (document.readyState === 'complete') {
        setTimeout(setVH, 100);
      } else {
        window.addEventListener('DOMContentLoaded', () => {
          setTimeout(setVH, 100);
        });
      }
      
      // Prevent page scroll when focusing input on mobile
      const preventScroll = (e) => {
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
          setTimeout(() => {
            window.scrollTo(0, 0);
            document.body.scrollTop = 0;
            document.documentElement.scrollTop = 0;
            // Ensure background color is maintained during keyboard transitions
            document.body.style.backgroundColor = '#1a1a1a';
            document.documentElement.style.backgroundColor = '#1a1a1a';
            document.body.style.height = '100%';
            document.body.style.minHeight = '100vh';
          }, 100);
        }
      };
      
      // Handle keyboard hide event to prevent white flash
      const handleFocusOut = () => {
        setTimeout(() => {
          setVH();
          document.body.style.backgroundColor = '#1a1a1a';
          document.documentElement.style.backgroundColor = '#1a1a1a';
          document.body.style.height = '100%';
          document.body.style.minHeight = '100vh';
          window.scrollTo(0, 0);
        }, 150);
      };
      
      document.addEventListener('focusin', preventScroll);
      document.addEventListener('focusout', handleFocusOut);
      
      // Cleanup
      return () => {
        window.removeEventListener('resize', handleResize);
        window.removeEventListener('orientationchange', handleResize);
        window.removeEventListener('load', setVH);
        window.removeEventListener('DOMContentLoaded', setVH);
        document.removeEventListener('focusin', preventScroll);
        document.removeEventListener('focusout', handleFocusOut);
        clearTimeout(timeoutId);
        
        // Reset body styles
        document.body.style.overflow = '';
        document.body.style.backgroundColor = '';
        document.documentElement.style.backgroundColor = '';
        document.body.style.height = '';
        document.body.style.minHeight = '';
        document.body.style.margin = '';
        document.body.style.padding = '';
        document.documentElement.style.height = '';
      };
    }
  }, []);

  // Force layout correction after component mount - fixes initial blank space
  useEffect(() => {
    if (typeof window !== 'undefined' && isMobileDevice()) {
      const forceLayoutCorrection = () => {
        const vh = window.innerHeight * 0.01;
        document.documentElement.style.setProperty('--vh', `${vh}px`);
        document.body.style.height = '100%';
        document.body.style.minHeight = '100vh';
        document.documentElement.style.height = '100%';
        window.scrollTo(0, 0);
      };
      
      // Multiple attempts to ensure the layout corrects
      const timeouts = [
        setTimeout(forceLayoutCorrection, 50),
        setTimeout(forceLayoutCorrection, 200),
        setTimeout(forceLayoutCorrection, 500),
        setTimeout(forceLayoutCorrection, 1500)
      ];
      
      return () => {
        timeouts.forEach(timeout => clearTimeout(timeout));
      };
    }
  }, [isConnected]); // Run when connection state changes

  // Fix viewport when action buttons visibility changes
  useEffect(() => {
    if (!showActionButtons && isMobileDevice()) {
      // Delay to allow transition to complete
      const timer = setTimeout(() => {
        const vh = window.innerHeight * 0.01;
        document.documentElement.style.setProperty('--vh', `${vh}px`);
        document.body.style.height = '100%';
        document.body.style.minHeight = '100vh';
        window.scrollTo(0, 0);
      }, 600); // Wait for CSS transition
      
      return () => clearTimeout(timer);
    }
  }, [showActionButtons]);

  /**
   * Handle sending messages with Claude-style conversation flow
   */
  const handleSendMessage = () => {
    sendMessageClaudeStyle();
  };

  /**
   * Format MCP data responses for clean display
   */
  // eslint-disable-next-line no-unused-vars
  const formatMCPData = (data) => {
    if (!data) return '❌ No data available\n';
    
    console.log('🔍 formatMCPData received:', data); // Debug log
    
    // Handle MCP response array format
    if (Array.isArray(data)) {
      // Check if it's an array of MCP response objects with type and text
      if (data.length > 0 && data[0].type === 'text' && data[0].text) {
        try {
          const parsedData = JSON.parse(data[0].text);
          console.log('🔍 Parsed JSON from MCP array:', parsedData); // Debug log
          return formatMCPData(parsedData); // Recursive call with parsed data
        } catch (e) {
          console.log('🔍 Failed to parse JSON from MCP array:', e); // Debug log
          return `${data[0].text}\n`;
        }
      }
      
      // Handle regular array
      let result = `📋 **DATA RESULTS**\n📊 **Found ${data.length} Item(s)**\n\n`;
      data.forEach((item, i) => {
        result += `${i + 1}. ${formatResultItem(item)}\n`;
      });
      return result;
    }
    
    // Handle nested structure like { "patients": [...], "count": N }
    if (data.patients && Array.isArray(data.patients)) {
      const patients = data.patients;
      let result = `👥 **PATIENT REGISTRY**\n📊 **Found ${patients.length} Patient(s)**\n\n`;
      
      patients.forEach((patient, i) => {
        result += `🏥 **${i + 1}. ${patient.first_name} ${patient.last_name}**\n`;
        result += `   📋 **Patient ID:** ${patient.patient_number}\n`;
        if (patient.date_of_birth) result += `   📅 **Date of Birth:** ${patient.date_of_birth}\n`;
        if (patient.gender) result += `   👤 **Gender:** ${patient.gender}\n`;
        if (patient.phone) result += `   📞 **Phone:** ${patient.phone}\n`;
        if (patient.email) result += `   📧 **Email:** ${patient.email}\n`;
        if (patient.address) result += `   🏠 **Address:** ${patient.address}\n`;
        if (patient.blood_type) result += `   🩸 **Blood Type:** ${patient.blood_type}\n`;
        if (patient.allergies && patient.allergies !== 'null' && patient.allergies !== null) {
          result += `   ⚠️ **Allergies:** ${patient.allergies}\n`;
        }
        if (patient.medical_history && patient.medical_history !== 'null' && patient.medical_history !== null) {
          result += `   📝 **Medical History:** ${patient.medical_history}\n`;
        }
        if (patient.emergency_contact_name) {
          result += `   🆘 **Emergency Contact:** ${patient.emergency_contact_name}`;
          if (patient.emergency_contact_phone) result += ` (${patient.emergency_contact_phone})`;
          result += '\n';
        }
        result += '\n';
      });
      
      if (data.count && data.count !== patients.length) {
        result += `📈 *Total in database: ${data.count} patients*\n`;
      }
      
      result += `\n💡 **Quick Actions:**\n`;
      result += `• Create new patient: "Add new patient [Name]"\n`;
      result += `• Search patient: "Find patient [Name/ID]"\n`;
      result += `• Update records: "Update patient [ID]"\n`;
      
      return result;
    }
    
    // Handle departments
    if (data.departments && Array.isArray(data.departments)) {
      const departments = data.departments;
      let result = `🏢 **HOSPITAL DEPARTMENTS**\n📊 **Found ${departments.length} Department(s)**\n\n`;
      
      departments.forEach((dept, i) => {
        result += `🏥 **${i + 1}. ${dept.name}**\n`;
        result += `   🆔 **Department ID:** ${dept.department_id}\n`;
        if (dept.floor_number) result += `   🏗️ **Floor:** ${dept.floor_number}\n`;
        if (dept.phone) result += `   📞 **Phone:** ${dept.phone}\n`;
        if (dept.email) result += `   📧 **Email:** ${dept.email}\n`;
        if (dept.description) result += `   📝 **Description:** ${dept.description}\n`;
        if (dept.head_doctor_id) result += `   👨‍⚕️ **Head Doctor ID:** ${dept.head_doctor_id}\n`;
        result += '\n';
      });
      
      result += `\n💡 **Department Actions:**\n`;
      result += `• Create department: "Add new department [Name]"\n`;
      result += `• Assign staff: "Assign staff to [Department]"\n`;
      result += `• Update info: "Update department [ID]"\n`;
      
      return result;
    }
    
    // Handle staff
    if (data.staff && Array.isArray(data.staff)) {
      const staff = data.staff;
      let result = `👨‍⚕️ **HOSPITAL STAFF**\n📊 **Found ${staff.length} Staff Member(s)**\n\n`;
      
      staff.forEach((member, i) => {
        result += `👤 **${i + 1}. ${member.position}**\n`;
        result += `   🆔 **Employee ID:** ${member.employee_id}\n`;
        if (member.department_id) result += `   🏢 **Department:** ${member.department_id}\n`;
        if (member.specialization) result += `   🎯 **Specialization:** ${member.specialization}\n`;
        if (member.status) result += `   📊 **Status:** ${member.status === 'active' ? '✅ Active' : '⏸️ Inactive'}\n`;
        if (member.hire_date) result += `   📅 **Hire Date:** ${member.hire_date}\n`;
        if (member.shift_pattern) result += `   ⏰ **Shift Pattern:** ${member.shift_pattern}\n`;
        result += '\n';
      });
      
      result += `\n💡 **Staff Actions:**\n`;
      result += `• Add staff: "Add new staff member"\n`;
      result += `• Schedule shifts: "Update staff schedule"\n`;
      result += `• Assign department: "Transfer staff to [Department]"\n`;
      
      return result;
    }
    
    // Handle beds
    if (data.beds && Array.isArray(data.beds)) {
      const beds = data.beds;
      const availableBeds = beds.filter(bed => bed.status === 'available').length;
      const occupiedBeds = beds.filter(bed => bed.status === 'occupied').length;
      
      let result = `🛏️ **BED MANAGEMENT**\n📊 **Found ${beds.length} Bed(s)** | ✅ ${availableBeds} Available | 🔴 ${occupiedBeds} Occupied\n\n`;
      
      beds.forEach((bed, i) => {
        const statusIcon = bed.status === 'available' ? '✅' : bed.status === 'occupied' ? '🔴' : '⚠️';
        result += `${statusIcon} **${i + 1}. Bed ${bed.bed_number}**\n`;
        if (bed.room_id) result += `   🏠 **Room:** ${bed.room_id}\n`;
        if (bed.status) result += `   📊 **Status:** ${bed.status.toUpperCase()}\n`;
        if (bed.bed_type) result += `   🛏️ **Type:** ${bed.bed_type}\n`;
        if (bed.patient_id) result += `   👤 **Current Patient:** ${bed.patient_id}\n`;
        result += '\n';
      });
      
      if (availableBeds === 0) {
        result += `\n🚨 **ALERT: NO AVAILABLE BEDS**\n`;
        result += `⚡ **Emergency Actions:**\n`;
        result += `• Check room capacity for emergency beds\n`;
        result += `• Review discharge schedule\n`;
        result += `• Contact bed management team\n`;
      } else {
        result += `\n💡 **Bed Actions:**\n`;
        result += `• Assign patient: "Assign bed [Number] to patient [ID]"\n`;
        result += `• Discharge patient: "Discharge patient [Name/ID]" or "Discharge bed [Number]"\n`;
        result += `• Check bed cleaning status: "Bed [Number] status" or "Is bed [Number] ready?"\n`;
        result += `• Create emergency bed: "Add emergency bed"\n`;
      }
      
      return result;
    }
    
    // Handle equipment
    if (data.equipment && Array.isArray(data.equipment)) {
      const equipment = data.equipment;
      let result = `🏥 **MEDICAL EQUIPMENT**\n📊 **Found ${equipment.length} Equipment Item(s)**\n\n`;
      
      equipment.forEach((item, i) => {
        result += `⚕️ **${i + 1}. ${item.name}**\n`;
        if (item.equipment_id) result += `   🆔 **Equipment ID:** ${item.equipment_id}\n`;
        if (item.category_id) result += `   📂 **Category:** ${item.category_id}\n`;
        if (item.manufacturer) result += `   🏭 **Manufacturer:** ${item.manufacturer}\n`;
        if (item.model) result += `   📱 **Model:** ${item.model}\n`;
        if (item.location) result += `   📍 **Location:** ${item.location}\n`;
        if (item.status) {
          const statusIcon = item.status === 'operational' ? '✅' : item.status === 'maintenance' ? '🔧' : '❌';
          result += `   ${statusIcon} **Status:** ${item.status.toUpperCase()}\n`;
        }
        result += '\n';
      });
      
      result += `\n💡 **Equipment Actions:**\n`;
      result += `• Schedule maintenance: "Maintain equipment [ID]"\n`;
      result += `• Update status: "Update equipment [ID] status"\n`;
      result += `• Add equipment: "Add new equipment"\n`;
      
      return result;
    }
    
    // Handle supplies
    if (data.supplies && Array.isArray(data.supplies)) {
      const supplies = data.supplies;
      const lowStock = supplies.filter(item => item.current_stock <= item.minimum_stock_level).length;
      
      let result = `📦 **MEDICAL SUPPLIES**\n📊 **Found ${supplies.length} Supply Item(s)**`;
      if (lowStock > 0) result += ` | ⚠️ ${lowStock} Low Stock`;
      result += `\n\n`;
      
      supplies.forEach((item, i) => {
        const stockIcon = item.current_stock <= item.minimum_stock_level ? '⚠️' : '✅';
        result += `${stockIcon} **${i + 1}. ${item.name}**\n`;
        if (item.item_code) result += `   🆔 **Item Code:** ${item.item_code}\n`;
        if (item.current_stock !== undefined) result += `   📊 **Current Stock:** ${item.current_stock}\n`;
        if (item.unit_of_measure) result += `   📏 **Unit:** ${item.unit_of_measure}\n`;
        if (item.supplier) result += `   🏢 **Supplier:** ${item.supplier}\n`;
        if (item.location) result += `   📍 **Location:** ${item.location}\n`;
        if (item.expiry_date) result += `   ⏰ **Expiry Date:** ${item.expiry_date}\n`;
        result += '\n';
      });
      
      result += `\n💡 **Supply Actions:**\n`;
      result += `• Restock: "Update stock for [Item Code]"\n`;
      result += `• Add supply: "Add new supply item"\n`;
      result += `• Check expiry: "Show expiring supplies"\n`;
      
      return result;
    }
    
    // Handle single objects
    if (typeof data === 'object') {
      return `✅ **RESULT:**\n${formatResultItem(data)}\n`;
    }
    
    // Handle simple values
    return `ℹ️ **INFO:** ${String(data)}\n`;
  };

  /**
   * Format individual result items for display
   */
  const formatResultItem = (item) => {
    if (!item) return 'No data';
    
    if (typeof item === 'string') {
      return item;
    }
    
    if (typeof item === 'object') {
      // For patient objects
      if (item.first_name && item.last_name) {
        let patientInfo = `${item.first_name} ${item.last_name}`;
        if (item.patient_number) patientInfo += ` (#${item.patient_number})`;
        if (item.date_of_birth) patientInfo += ` • Born: ${item.date_of_birth}`;
        if (item.phone) patientInfo += ` • Phone: ${item.phone}`;
        if (item.blood_type) patientInfo += ` • Blood Type: ${item.blood_type}`;
        return patientInfo;
      }
      // For department objects
      if (item.name && item.department_id) {
        let deptInfo = `${item.name} (ID: ${item.department_id})`;
        if (item.floor_number) deptInfo += ` • Floor ${item.floor_number}`;
        if (item.phone) deptInfo += ` • Phone: ${item.phone}`;
        return deptInfo;
      }
      // For staff objects
      if (item.user_id && item.position) {
        let staffInfo = `${item.position}`;
        if (item.employee_id) staffInfo += ` (#${item.employee_id})`;
        if (item.specialization) staffInfo += ` • ${item.specialization}`;
        if (item.department_id) staffInfo += ` • Dept: ${item.department_id}`;
        return staffInfo;
      }
      // For bed objects
      if (item.bed_number) {
        let bedInfo = `Bed ${item.bed_number}`;
        if (item.room_id) bedInfo += ` (Room ${item.room_id})`;
        if (item.status) bedInfo += ` • Status: ${item.status}`;
        if (item.bed_type) bedInfo += ` • Type: ${item.bed_type}`;
        return bedInfo;
      }
      // Generic object formatting
      const keys = Object.keys(item);
      if (keys.length > 0) {
        // Try to find a meaningful display field
        const nameField = keys.find(k => k.includes('name') || k.includes('title'));
        const idField = keys.find(k => k.includes('id') || k.includes('number'));
        
        if (nameField) {
          let result = `${item[nameField]}`;
          if (idField && item[idField]) result += ` (${item[idField]})`;
          return result;
        } else if (idField) {
          return `ID: ${item[idField]}`;
        } else {
          // Show first few key-value pairs
          return keys.slice(0, 2).map(k => `${k}: ${item[k]}`).join(', ');
        }
      }
    }
    
    return String(item);
  };

  /**
   * Disconnect from MCP server
   */
  const disconnect = async () => {
    if (aiMcpServiceRef.current) {
      await aiMcpServiceRef.current.disconnect();
    }
    setIsConnected(false);
    setShowSetup(true);
    setServerInfo(null);
    setMessages([]);
  };

  /**
   * Check server status
   */
  const checkStatus = async () => {
    if (aiMcpServiceRef.current) {
      try {
        const status = await aiMcpServiceRef.current.checkStatus();
        setServerInfo(status);
        
        if (status && !status.isConnected) {
          setIsConnected(false);
          setMessages(prev => [...prev, {
            id: Date.now(),
            text: '🔌 MCP server connection lost. Please reconnect.',
            sender: 'ai',
            timestamp: new Date().toLocaleTimeString()
          }]);
        }
      } catch (error) {
        console.error('Status check failed:', error);
      }
    }
  };

  /**
   * Search for patient by patient number and get UUID
   */
  const searchPatientByNumber = async (patientNumber) => {
    if (!patientNumber.trim()) {
      return null;
    }

    setSearchingPatient(true);
    try {
      const token = sessionStorage.getItem('hms_auth_token') || user?.token;
      const headers = {
        'Content-Type': 'application/json',
      };
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      const response = await fetch(`http://${window.location.hostname}:8000/tools/call`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          params: {
            name: 'search_patients',
            arguments: {
              patient_number: patientNumber.trim()
            }
          }
        })
      });

      const result = await response.json();
      
      if (result.result?.content?.[0]?.text) {
        const data = JSON.parse(result.result.content[0].text);
        
        if (data.success && data.result?.data?.length > 0) {
          const patient = data.result.data[0]; // Get first matching patient
          return {
            id: patient.id,
            patient_number: patient.patient_number,
            name: `${patient.first_name} ${patient.last_name}`,
            patient: patient
          };
        }
      }
      return null;
    } catch (error) {
      console.error('Patient search error:', error);
      return null;
    } finally {
      setSearchingPatient(false);
    }
  };

  /**
   * Handle patient number verification
   */
  const verifyPatient = async () => {
    if (!selectedPatientNumber.trim()) return;

    const patient = await searchPatientByNumber(selectedPatientNumber);
    
    if (patient) {
      setSelectedPatientId(patient.id);
      setPatientSearchResult(patient);
    } else {
      setPatientSearchResult(null);
      setSelectedPatientId(null);
      // Show error message
      setMessages(prev => [...prev, {
        id: Date.now(),
        text: `❌ No patient found with number: ${selectedPatientNumber}. Please check the patient number or create a new patient.`,
        sender: 'ai',
        timestamp: new Date().toLocaleTimeString()
      }]);
    }
  };

  /**
   * Handle successful patient admission from the component
   */
  const handlePatientAdmissionSuccess = (response) => {
    // Close the form
    setShowPatientAdmissionForm(false);

    // Add success message to chat
    let responseText = '';
    
    if (response.success || response.enhanced) {
      // Handle enhanced LangGraph response (Option 1)
      if (response.enhanced && response.workflow) {
        const patientData = response.patient?.result?.data || response.patient?.data || {};
        const workflowResult = response.workflow?.result || response.workflow;
        
        responseText = `✅ **Enhanced Patient Admission Completed Successfully!**

🏥 **LangGraph Intelligent Workflow Executed:**

📊 **Patient Registration:**
- Name: ${patientData.first_name || 'Unknown'} ${patientData.last_name || 'Unknown'}
- Patient Number: ${patientData.patient_number || patientData.id || 'Auto-generated'}
- Date of Birth: ${patientData.date_of_birth || 'Not provided'}
- Gender: ${patientData.gender || 'Not specified'}
- Phone: ${patientData.phone || 'Not provided'}
- Email: ${patientData.email || 'Not provided'}

🧠 **AI Workflow Results:**`;

        if (workflowResult?.success) {
          if (workflowResult.bed_id) {
            // Extract bed info from workflow messages if available
            const bedMessage = workflowResult.messages?.find(msg => msg.includes('Selected bed:') || msg.includes('Bed'));
            let bedDisplay = 'Assigned';
            if (bedMessage) {
              const bedMatch = bedMessage.match(/bed:?\s*([A-Z0-9]+)/i) || bedMessage.match(/Bed\s+([A-Z0-9]+)/i);
              if (bedMatch) {
                bedDisplay = `Bed ${bedMatch[1]}`;
              }
            }
            responseText += `\n🛏️ **Bed Assignment:** ✅ ${bedDisplay}`;
          }
          
          if (workflowResult.staff_assignments && workflowResult.staff_assignments.length > 0) {
            responseText += `\n👥 **Staff Assignment:** ✅ ${workflowResult.staff_assignments.length} medical staff assigned`;
            workflowResult.staff_assignments.forEach(assignment => {
              const displayName = assignment.name || `Staff ID: ${assignment.staff_id}`;
              const role = assignment.role ? assignment.role.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase()) : 'Medical Staff';
              responseText += `\n   • ${role}: ${displayName}`;
            });
          }
          
          if (workflowResult.equipment_assignments && workflowResult.equipment_assignments.length > 0) {
            responseText += `\n⚙️ **Equipment Setup:** ✅ ${workflowResult.equipment_assignments.length} items assigned`;
            workflowResult.equipment_assignments.forEach(equipment => {
              responseText += `\n   • ${equipment.equipment_type || 'Equipment'}: ${equipment.status || 'ready'}`;
            });
          }
          
          if (workflowResult.steps_completed && workflowResult.steps_completed.length > 0) {
            responseText += `\n📋 **Workflow Steps Completed:** ✅ ${workflowResult.steps_completed.length} steps`;
            workflowResult.steps_completed.forEach(step => {
              responseText += `\n   • ${step}`;
            });
          }
          
          responseText += `\n\n🎯 **Status:** Patient admission workflow complete - ready for care!`;
          
          if (workflowResult.messages && workflowResult.messages.length > 0) {
            responseText += `\n\n📝 **Workflow Summary:**`;
            // Filter out JSON messages and show only user-friendly ones
            const cleanMessages = workflowResult.messages.filter(msg => {
              return !msg.includes('{') && !msg.includes('Admission reports generated');
            }).slice(-3);
            
            if (cleanMessages.length > 0) {
              cleanMessages.forEach(msg => {
                responseText += `\n   • ${msg}`;
              });
            } else {
              responseText += `\n   • Patient successfully admitted with complete resource allocation`;
              responseText += `\n   • All medical staff and equipment prepared for immediate care`;
              responseText += `\n   • Hospital workflow orchestration completed successfully`;
            }
          }
        } else {
          responseText += `\n⚠️ **Workflow Status:** Planned (Resources identified and ready)`;
          
          // Show what was planned/identified
          if (workflowResult?.bed_id) {
            responseText += `\n🛏️ **Bed Identified:** ✅ Ready for assignment`;
          }
          
          if (workflowResult?.staff_assignments && workflowResult.staff_assignments.length > 0) {
            responseText += `\n👥 **Staff Identified:** ✅ ${workflowResult.staff_assignments.length} medical staff ready`;
            workflowResult.staff_assignments.forEach(assignment => {
              responseText += `\n   • ${assignment.name || assignment.role || 'Staff'}: Ready to assign`;
            });
          }
          
          if (workflowResult?.equipment_assignments && workflowResult.equipment_assignments.length > 0) {
            responseText += `\n⚙️ **Equipment Identified:** ✅ ${workflowResult.equipment_assignments.length} items ready`;
            workflowResult.equipment_assignments.forEach(equipment => {
              responseText += `\n   • ${equipment.equipment_type || 'Equipment'}: ${equipment.status || 'available'}`;
            });
          }
          
          if (workflowResult?.steps_completed && workflowResult.steps_completed.length > 0) {
            responseText += `\n📋 **Workflow Planning:** ✅ ${workflowResult.steps_completed.length} steps completed`;
          }
          
          responseText += `\n\n🎯 **Status:** All resources identified and ready for automatic assignment!`;
          responseText += `\n\n**The AI workflow has successfully:**
• 🔍 Found available bed
• 👥 Identified qualified medical staff  
• ⚙️ Located necessary equipment
• 📋 Prepared admission workflow

**Everything is ready for immediate patient care!**`;

          if (workflowResult?.error) {
            responseText += `\n\n📝 **Technical Note:** ${workflowResult.error}`;
          }
        }
        
      } else {
        // Standard response (original functionality)
        const patientData = response.result?.data || response.data || {};
        responseText = `✅ Patient created successfully in the database!
      
**Patient Details:**
- Name: ${patientData.first_name || 'Unknown'} ${patientData.last_name || 'Unknown'}
- Patient Number: ${patientData.patient_number || patientData.id || 'Not generated'}
- Date of Birth: ${patientData.date_of_birth || 'Not provided'}
- Gender: ${patientData.gender || 'Not specified'}
- Phone: ${patientData.phone || 'Not provided'}
- Email: ${patientData.email || 'Not provided'}

**Next Steps Required:**
After admitting a patient, you need to:
1. 🛏️ Assign a bed to the patient
2. 👥 Assign staff (doctors/nurses) to the patient
3. ⚙️ Assign equipment for patient care
4. 📦 Assign supplies from inventory

You can use these commands:
• "Assign bed [bed_number] to patient [patient_name]"
• "Assign staff [staff_name] to patient [patient_name]"
• "Assign equipment [equipment_name] to patient [patient_name]"
• "Assign supplies [supply_name] to patient [patient_name]"`;
      }
    } else {
      // Error case
      responseText = `❌ Failed to create patient: ${response.message || 'Unknown error'}`;
    }

    const successMsg = {
      id: Date.now(),
      text: `✅ Patient admission completed successfully!\n\n${responseText}`,
      sender: 'ai',
      timestamp: new Date().toLocaleTimeString()
    };
    setMessages(prev => [...prev, successMsg]);
  };

  /**
   * Close patient admission form
   */
  const closePatientAdmissionForm = () => {
    setShowPatientAdmissionForm(false);
    
    // Add message indicating form was closed
    const cancelMsg = {
      id: Date.now(),
      text: "Patient admission form was closed. You can say 'admit patient' anytime to open it again.",
      sender: 'ai',
      timestamp: new Date().toLocaleTimeString()
    };
    setMessages(prev => [...prev, cancelMsg]);
  };

  // Department Form Handlers
  const handleDepartmentSubmit = (response) => {
    setShowDepartmentForm(false);
    
    let responseText = '';
    if (response.success) {
      const deptData = response.result?.data || response.data || {};
      responseText = `✅ Department created successfully!
      
**Department Details:**
- Name: ${deptData.name || 'Unknown'}
- Description: ${deptData.description || 'Not provided'}
- Floor: ${deptData.floor_number || 'Not specified'}
- Phone: ${deptData.phone || 'Not provided'}
- Email: ${deptData.email || 'Not provided'}`;
    } else {
      responseText = `❌ Failed to create department: ${response.message || 'Unknown error'}`;
    }

    const successMsg = {
      id: Date.now(),
      text: responseText,
      sender: 'ai',
      timestamp: new Date().toLocaleTimeString()
    };
    setMessages(prev => [...prev, successMsg]);
  };

  const closeDepartmentForm = () => {
    setShowDepartmentForm(false);
    const cancelMsg = {
      id: Date.now(),
      text: "Department creation form was closed. You can say 'create department' anytime to open it again.",
      sender: 'ai',
      timestamp: new Date().toLocaleTimeString()
    };
    setMessages(prev => [...prev, cancelMsg]);
  };

  // Staff Form Handlers
  const handleStaffSubmit = (response) => {
    setShowStaffForm(false);
    
    let responseText = '';
    if (response.success) {
      const staffData = response.result?.data || response.data || {};
      responseText = `✅ Staff member created successfully!
      
**Staff Details:**
- Employee ID: ${staffData.employee_id || 'Not provided'}
- Position: ${staffData.position || 'Not provided'}
- Department ID: ${staffData.department_id || 'Not provided'}
- Status: ${staffData.status || 'Active'}`;
    } else {
      responseText = `❌ Failed to create staff member: ${response.message || 'Unknown error'}`;
    }

    const successMsg = {
      id: Date.now(),
      text: responseText,
      sender: 'ai',
      timestamp: new Date().toLocaleTimeString()
    };
    setMessages(prev => [...prev, successMsg]);
  };

  const closeStaffForm = () => {
    setShowStaffForm(false);
    const cancelMsg = {
      id: Date.now(),
      text: "Staff creation form was closed. You can say 'create staff' anytime to open it again.",
      sender: 'ai',
      timestamp: new Date().toLocaleTimeString()
    };
    setMessages(prev => [...prev, cancelMsg]);
  };

  // User Form Handlers
  /**
   * Handle successful user creation from the component
   */
  const handleUserCreationSuccess = (response) => {
    // Close the form
    setShowUserForm(false);

    // Add success message to chat
    let responseText = '';
    if (response.success) {
      const userData = response.result?.data || response.data || {};
      responseText = `✅ User created successfully!
      
**User Details:**
- Username: ${userData.username || 'Unknown'}
- Email: ${userData.email || 'Unknown'}
- Role: ${userData.role || 'Unknown'}
- Name: ${userData.first_name || 'Unknown'} ${userData.last_name || 'Unknown'}
- Active: ${userData.is_active ? 'Yes' : 'No'}`;
    } else {
      responseText = `❌ Failed to create user: ${response.message || 'Unknown error'}`;
    }

    const successMsg = {
      id: Date.now(),
      text: `✅ User created successfully!\n\n${responseText}`,
      sender: 'ai',
      timestamp: new Date().toLocaleTimeString()
    };
    setMessages(prev => [...prev, successMsg]);
  };

  const closeUserForm = () => {
    setShowUserForm(false);
    const cancelMsg = {
      id: Date.now(),
      text: "User creation form was closed. You can say 'create user' anytime to open it again.",
      sender: 'ai',
      timestamp: new Date().toLocaleTimeString()
    };
    setMessages(prev => [...prev, cancelMsg]);
  };

  // Room Form Handlers
  const handleRoomSubmit = (response) => {
    setShowRoomForm(false);
    
    let responseText = '';
    if (response.success) {
      const roomData = response.result?.data || response.data || {};
      responseText = `✅ Room created successfully!
      
**Room Details:**
- Room Number: ${roomData.room_number || 'Unknown'}
- Type: ${roomData.room_type || 'Standard'}
- Floor: ${roomData.floor_number || 'Not specified'}
- Capacity: ${roomData.capacity || 'Not specified'}
- Department ID: ${roomData.department_id || 'Not specified'}`;
    } else {
      responseText = `❌ Failed to create room: ${response.message || 'Unknown error'}`;
    }

    const successMsg = {
      id: Date.now(),
      text: responseText,
      sender: 'ai',
      timestamp: new Date().toLocaleTimeString()
    };
    setMessages(prev => [...prev, successMsg]);
  };

  const closeRoomForm = () => {
    setShowRoomForm(false);
    const cancelMsg = {
      id: Date.now(),
      text: "Room creation form was closed. You can say 'create room' anytime to open it again.",
      sender: 'ai',
      timestamp: new Date().toLocaleTimeString()
    };
    setMessages(prev => [...prev, cancelMsg]);
  };

  // Bed Form Handlers
  const handleBedSubmit = async (response) => {
    setIsSubmittingBed(false);
    setShowBedForm(false);

    let responseText = '';
    if (response.success) {
      const bedData = response.result?.data || response.data || {};
      responseText = `✅ Bed created successfully!
      
**Bed Details:**
- Bed Number: ${bedData.bed_number || 'Unknown'}
- Room ID: ${bedData.room_id || 'Unknown'}
- Type: ${bedData.bed_type || 'Standard'}
- Status: ${bedData.status || 'Available'}

The bed has been added to the hospital system and is ready for assignment.`;
    } else {
      responseText = `❌ Failed to create bed: ${response.message || 'Unknown error'}`;
    }

    const successMsg = {
      id: Date.now(),
      text: responseText,
      sender: 'ai',
      timestamp: new Date().toLocaleTimeString()
    };
    setMessages(prev => [...prev, successMsg]);
  };

  const closeBedForm = () => {
    setShowBedForm(false);
    const cancelMsg = {
      id: Date.now(),
      text: "Bed creation form was closed. You can say 'create bed' anytime to open it again.",
      sender: 'ai',
      timestamp: new Date().toLocaleTimeString()
    };
    setMessages(prev => [...prev, cancelMsg]);
  };

  // Equipment Form Handlers
  const handleEquipmentSubmit = (response) => {
    setShowEquipmentForm(false);
    
    let responseText = '';
    if (response.success) {
      const equipmentData = response.result?.data || response.data || {};
      responseText = `✅ Equipment created successfully!
      
**Equipment Details:**
- Equipment ID: ${equipmentData.equipment_id || 'Unknown'}
- Name: ${equipmentData.name || 'Unknown'}
- Model: ${equipmentData.model || 'Not specified'}
- Location: ${equipmentData.location || 'Not specified'}
- Status: ${equipmentData.status || 'Operational'}`;
    } else {
      responseText = `❌ Failed to create equipment: ${response.message || 'Unknown error'}`;
    }

    const successMsg = {
      id: Date.now(),
      text: responseText,
      sender: 'ai',
      timestamp: new Date().toLocaleTimeString()
    };
    setMessages(prev => [...prev, successMsg]);
  };

  const closeEquipmentForm = () => {
    setShowEquipmentForm(false);
    const cancelMsg = {
      id: Date.now(),
      text: "Equipment creation form was closed. You can say 'create equipment' anytime to open it again.",
      sender: 'ai',
      timestamp: new Date().toLocaleTimeString()
    };
    setMessages(prev => [...prev, cancelMsg]);
  };

  // Supply Form Handlers
  const handleSupplySubmit = async (response) => {
    setIsSubmittingSupply(false);
    setShowSupplyForm(false);

    let responseText = '';
    if (response.success) {
      const supplyData = response.result?.data || response.data || {};
      responseText = `✅ Supply created successfully!
      
**Supply Details:**
- Item Code: ${supplyData.item_code}
- Name: ${supplyData.name}
- Category: ${supplyData.category_name || 'N/A'}
- Unit of Measure: ${supplyData.unit_of_measure}
- Current Stock: ${supplyData.current_stock || 'N/A'}
- Location: ${supplyData.location || 'N/A'}

The supply has been added to the inventory system and is ready for use.`;
    } else {
      responseText = `❌ Failed to create supply: ${response.message || 'Unknown error'}`;
    }

    const successMsg = {
      id: Date.now(),
      text: responseText,
      sender: 'ai',
      timestamp: new Date().toLocaleTimeString()
    };
    setMessages(prev => [...prev, successMsg]);
  };

  const closeSupplyForm = () => {
    setShowSupplyForm(false);
    const cancelMsg = {
      id: Date.now(),
      text: "Supply creation form was closed. You can say 'create supply' anytime to open it again.",
      sender: 'ai',
      timestamp: new Date().toLocaleTimeString()
    };
    setMessages(prev => [...prev, cancelMsg]);
  };

  // Legacy User Form Handlers
  const handleLegacyUserSubmit = async (response) => {
    setIsSubmittingLegacyUser(false);
    setShowLegacyUserForm(false);

    let responseText = '';
    if (response.success) {
      const legacyUserData = response.result?.data || response.data || {};
      responseText = `✅ Legacy user created successfully!
      
**Legacy User Details:**
- Name: ${legacyUserData.name}
- Email: ${legacyUserData.email}
- Phone: ${legacyUserData.phone || 'Not provided'}
- Address: ${legacyUserData.address || 'Not provided'}

The legacy user has been added to the system for reference purposes.`;
    } else {
      responseText = `❌ Failed to create legacy user: ${response.message || 'Unknown error'}`;
    }

    const successMsg = {
      id: Date.now(),
      text: responseText,
      sender: 'ai',
      timestamp: new Date().toLocaleTimeString()
    };
    setMessages(prev => [...prev, successMsg]);
  };

  const closeLegacyUserForm = () => {
    setShowLegacyUserForm(false);
    const cancelMsg = {
      id: Date.now(),
      text: "Legacy user creation form was closed. You can say 'create legacy user' anytime to open it again.",
      sender: 'ai',
      timestamp: new Date().toLocaleTimeString()
    };
    setMessages(prev => [...prev, cancelMsg]);
  };

  // Equipment Category Form Handlers
  const handleEquipmentCategorySubmit = async (response) => {
    setIsSubmittingEquipmentCategory(false);
    setShowEquipmentCategoryForm(false);

    let responseText = '';
    if (response && response.success) {
      responseText = `✅ Equipment category created successfully!
      
The new equipment category has been added to the system and is now available for equipment assignment.`;
      // Reload equipment categories for dropdowns
      await loadDropdownOptions();
    } else {
      responseText = `❌ Failed to create equipment category: ${response.message || 'Unknown error'}`;
    }

    const responseMsg = {
      id: Date.now(),
      text: responseText,
      sender: 'ai',
      timestamp: new Date().toLocaleTimeString()
    };
    setMessages(prev => [...prev, responseMsg]);
  };

  const closeEquipmentCategoryForm = () => {
    setShowEquipmentCategoryForm(false);
    const cancelMsg = {
      id: Date.now(),
      text: "Equipment category creation form was closed. You can say 'create equipment category' anytime to open it again.",
      sender: 'ai',
      timestamp: new Date().toLocaleTimeString()
    };
    setMessages(prev => [...prev, cancelMsg]);
  };

  // Supply Category Form Handlers
  const handleSupplyCategorySubmit = async (categoryName) => {
    const responseText = `✅ Supply category "${categoryName}" created successfully!`;
    await loadDropdownOptions(); // Reload supply categories for dropdowns
    
    const responseMsg = {
      id: Date.now(),
      text: responseText,
      sender: 'ai',
      timestamp: new Date().toLocaleTimeString()
    };
    setMessages(prev => [...prev, responseMsg]);
    setShowSupplyCategoryForm(false);
  };

  const closeSupplyCategoryForm = () => {
    setShowSupplyCategoryForm(false);
    const cancelMsg = {
      id: Date.now(),
      text: "Supply category creation form was closed. You can say 'create supply category' anytime to open it again.",
      sender: 'ai',
      timestamp: new Date().toLocaleTimeString()
    };
    setMessages(prev => [...prev, cancelMsg]);
  };

  // Discharge Form Handlers
  const handleDischargeFormChange = (field, value) => {
    setDischargeFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const submitDischarge = async () => {
    // Validate required fields - need at least one identifier
    const hasIdentifier = dischargeFormData.patient_id || dischargeFormData.bed_id || dischargeFormData.patient_name;
    
    if (!hasIdentifier) {
      alert('Please provide at least one identifier: Patient ID, Bed ID, or Patient Name');
      return;
    }

    setIsSubmittingDischarge(true);

    try {
      // Call the comprehensive discharge workflow
      const response = await aiMcpServiceRef.current.callToolDirectly('discharge_patient_complete', {
        patient_id: dischargeFormData.patient_id || undefined,
        bed_id: dischargeFormData.bed_id || undefined,
        patient_name: dischargeFormData.patient_name || undefined,
        discharge_condition: dischargeFormData.discharge_condition,
        discharge_destination: dischargeFormData.discharge_destination
      });

      // Close the form and show success message
      setShowDischargeForm(false);
      
      // Reset form data
      setDischargeFormData({
        patient_id: '',
        bed_id: '',
        patient_name: '',
        discharge_condition: 'stable',
        discharge_destination: 'home'
      });

      // Add success message to chat
      let responseText = '';
      if (response.success) {
        const dischargeData = response.result || response;
        responseText = `✅ Patient discharged successfully!
        
**Discharge Summary:**
- Patient: ${dischargeData.patient_id || 'Unknown'}
- Bed: ${dischargeData.bed_id || 'Unknown'}
- Status: Discharged
- Bed Status: Cleaning (30 minutes)
- Discharge Report: Generated and available for download

**Next Steps:**
${dischargeData.next_steps ? dischargeData.next_steps.map(step => `• ${step}`).join('\n') : '• Bed cleaning in progress\n• Report available for download'}`;
      } else {
        responseText = `❌ Failed to discharge patient: ${response.message || 'Unknown error'}`;
      }

      const successMsg = {
        id: Date.now(),
        text: responseText,
        sender: 'ai',
        timestamp: new Date().toLocaleTimeString()
      };
      setMessages(prev => [...prev, successMsg]);

    } catch (error) {
      console.error('Error during discharge:', error);
      
      // Add error message to chat
      const errorMsg = {
        id: Date.now(),
        text: `❌ Error during discharge: ${error.message || 'Unknown error occurred'}`,
        sender: 'ai',
        timestamp: new Date().toLocaleTimeString()
      };
      setMessages(prev => [...prev, errorMsg]);
    } finally {
      setIsSubmittingDischarge(false);
    }
  };

  const closeDischargeForm = () => {
    setShowDischargeForm(false);
    
    // Add message indicating form was closed
    const cancelMsg = {
      id: Date.now(),
      text: "Discharge form was closed. You can say 'discharge patient' anytime to open it again.",
      sender: 'ai',
      timestamp: new Date().toLocaleTimeString()
    };
    setMessages(prev => [...prev, cancelMsg]);
  };

  /**
   * Check bed status with remaining cleaning time
   */
  const checkBedStatus = async (bedId) => {
    try {
      const response = await aiMcpServiceRef.current.callToolDirectly('get_bed_status_with_time_remaining', {
        bed_id: bedId
      });

      let statusText = '';
      if (response.success) {
        const bedData = response.result || response;
        if (bedData.process_status === 'cleaning') {
          const remaining = bedData.time_remaining_minutes || 0;
          const progress = bedData.progress_percentage || 0;
          statusText = `🛏️ **Bed ${bedData.bed_number} Status:**
          
**Current Status:** ${bedData.current_status}
**Process:** Cleaning in progress
**Time Remaining:** ${remaining} minutes
**Progress:** ${Math.round(progress)}%
**Room:** ${bedData.room_number}
**Estimated Completion:** ${bedData.estimated_completion ? new Date(bedData.estimated_completion).toLocaleTimeString() : 'Unknown'}

⏰ This bed will be automatically available in ${remaining} minutes when cleaning is complete.`;
        } else {
          statusText = `🛏️ **Bed ${bedData.bed_number} Status:**
          
**Current Status:** ${bedData.current_status}
**Room:** ${bedData.room_number}
**Process Status:** ${bedData.process_status || 'None'}

✅ This bed is ready for use.`;
        }
      } else {
        statusText = `❌ Failed to get bed status: ${response.message || 'Unknown error'}`;
      }

      const statusMsg = {
        id: Date.now(),
        text: statusText,
        sender: 'ai',
        timestamp: new Date().toLocaleTimeString()
      };
      setMessages(prev => [...prev, statusMsg]);

    } catch (error) {
      console.error('Error checking bed status:', error);
      const errorMsg = {
        id: Date.now(),
        text: `❌ Error checking bed status: ${error.message || 'Unknown error occurred'}`,
        sender: 'ai',
        timestamp: new Date().toLocaleTimeString()
      };
      setMessages(prev => [...prev, errorMsg]);
    }
  };

  // Setup Panel - Dark Chatbot Style
  if (showSetup) {
    return (
      <div className="h-screen bg-[#1a1a1a] flex flex-col text-white">
        {/* Header */}
        <div className="border-b border-gray-700 px-4 py-3 bg-[#1a1a1a]">
          <div className="flex items-center space-x-3">
            <div className="w-7 h-7 bg-blue-600 rounded-full flex items-center justify-center text-white text-sm font-medium shadow-lg">
              H
            </div>
            <div>
              <h1 className="text-sm font-medium text-white">Hospital Assistant</h1>
              <p className="text-xs text-gray-400">Setup & Configuration</p>
            </div>
          </div>
        </div>

        {/* Main Setup Content */}
        <div className="flex-1 overflow-y-auto bg-[#1a1a1a] flex items-center justify-center">
          <div className="max-w-lg w-full mx-4">
            {/* Welcome Section */}
            <div className="text-center mb-8">
              <div className="w-16 h-16 bg-blue-600 rounded-full flex items-center justify-center mx-auto mb-6 shadow-lg">
                <span className="text-2xl font-medium text-white">H</span>
              </div>
              <h1 className="text-2xl font-medium text-white mb-3">
                Welcome to Hospital Assistant
              </h1>
              <p className="text-gray-400 mb-6 text-sm">
                Connect to your hospital management system to get started with AI-powered healthcare administration.
              </p>
            </div>

            {/* Configuration Form */}
            <div className="space-y-6">
              {/* API Key Section */}
              <div className="bg-[#2a2a2a] rounded-lg p-6 border border-gray-700">
                <div className="flex items-center space-x-3 mb-4">
                  <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
                    <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" />
                    </svg>
                  </div>
                  <div>
                    <h3 className="text-white font-medium">OpenAI API Key</h3>
                    <p className="text-xs text-gray-400">Required for AI conversation processing</p>
                  </div>
                </div>
                <input
                  type="password"
                  value={openaiApiKey}
                  onChange={(e) => setOpenaiApiKey(e.target.value)}
                  placeholder="sk-..."
                  className="w-full px-4 py-3 bg-[#1a1a1a] border border-gray-600 rounded-lg focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500 text-white placeholder-gray-400 text-sm"
                />
              </div>

              {/* Server Status */}
              <div className="bg-[#2a2a2a] rounded-lg p-4 border border-gray-700">
                <h4 className="text-white font-medium mb-2 text-sm">📡 Server Connection</h4>
                <p className="text-xs text-gray-400">
                  Connecting directly to FastMCP server at: <br/>
                  <code className="text-green-400">http://127.0.0.1:8000</code>
                </p>
              </div>

              {/* Connection Status */}
              {connectionError && (
                <div className={`p-4 rounded-lg text-sm border ${
                  connectionError.includes('✅') 
                    ? 'bg-green-900/20 text-green-400 border-green-800' 
                    : 'bg-red-900/20 text-red-400 border-red-800'
                }`}>
                  {connectionError}
                </div>
              )}

              {/* Action Buttons */}
              <div className="space-y-3">
                <button
                  onClick={async () => {
                    setConnectionError('');
                    try {
                      const response = await fetch(`http://${window.location.hostname}:8000/`);
                      if (response.ok) {
                        setConnectionError('✅ FastMCP Server is running and ready');
                      } else {
                        setConnectionError(`❌ Server error: ${response.status}`);
                      }
                    } catch (error) {
                      setConnectionError(`❌ Cannot reach FastMCP Server: ${error.message}\nMake sure comprehensive_server.py is running on port 8000`);
                    }
                  }}
                  className="w-full py-3 px-4 bg-[#333] hover:bg-[#404040] text-white rounded-lg transition-colors text-sm font-medium border border-gray-600"
                >
                  <div className="flex items-center justify-center space-x-2">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <span>Test Server Connection</span>
                  </div>
                </button>
                
                <button
                  onClick={initializeService}
                  disabled={isLoading || !openaiApiKey.trim()}
                  className="w-full py-3 px-4 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white rounded-lg transition-all duration-200 font-medium"
                >
                  {isLoading ? (
                    <div className="flex items-center justify-center space-x-2">
                      <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                      <span>Connecting to Hospital System...</span>
                    </div>
                  ) : (
                    <div className="flex items-center justify-center space-x-2">
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                      </svg>
                      <span>Connect to Hospital System</span>
                    </div>
                  )}
                </button>
              </div>

              {/* Quick Tips */}
              <div className="bg-[#2a2a2a] rounded-lg p-4 border border-gray-700">
                <h4 className="text-white font-medium mb-2 text-sm">Quick Tips:</h4>
                <ul className="text-xs text-gray-400 space-y-1">
                  <li>• Make sure comprehensive_server.py is running on port 8000</li>
                  <li>• Your OpenAI API key needs GPT-4 access for best results</li>
                  <li>• No process manager needed - direct HTTP connection</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Main Chat Interface - Using HospitalChatInterface Component or Dashboard
  return (
    <>
      {/* Conditional rendering based on active tab */}
      {activeTab === 'dashboard' ? (
        // Dashboard View with Provider
        <DashboardProvider mcpClient={aiMcpServiceRef.current?.mcpClient}>
          <RealTimeDashboard setActiveTab={setActiveTab} />
        </DashboardProvider>
      ) : activeTab === 'ai-clinical' ? (
        // AI Clinical Assistant View
        <div className="h-screen">
          <AIClinicalChatbot 
            aiService={aiMcpServiceRef.current} 
            onBackToMainChat={() => setActiveTab('chat')}
          />
        </div>
      ) : (
        // Chat Interface View (existing)
        <HospitalChatInterface
          // User and server info
          user={user}
          serverInfo={serverInfo}
          onLogout={onLogout}
          
          // Chat state
          messages={messages}
          isLoading={isLoading}
          expandedThinking={expandedThinking}
          setExpandedThinking={setExpandedThinking}
          
          // Input handling
          inputMessage={inputMessage}
          setInputMessage={setInputMessage}
          handleSendMessage={handleSendMessage}
          isConnected={isConnected}
          
          // Action buttons
          showActionButtons={showActionButtons}
          smartFocusInput={smartFocusInput}
          
          // Plus menu
          showPlusMenu={showPlusMenu}
          setShowPlusMenu={setShowPlusMenu}
          plusMenuRef={plusMenuRef}
          setActiveTab={setActiveTab}
          
          // Medical document functionality
          activeTab={activeTab}
          selectedPatientId={selectedPatientId}
          setSelectedPatientId={setSelectedPatientId}
          selectedPatientNumber={selectedPatientNumber}
          setSelectedPatientNumber={setSelectedPatientNumber}
          searchingPatient={searchingPatient}
          patientSearchResult={patientSearchResult}
          verifyPatient={verifyPatient}
          searchPatientByNumber={searchPatientByNumber}
          
          // Voice functionality
          toggleVoiceInput={toggleVoiceInput}
          isListening={isListening}
          isRecording={isRecording}
          isProcessingVoice={isProcessingVoice}
          isSpeaking={isSpeaking}
          microphoneAvailable={microphoneAvailable}
          
          // Chat functionality
          aiMcpServiceRef={aiMcpServiceRef}
          setMessages={setMessages}
          setShowSetup={setShowSetup}
          
          // Formatting functions
          formatMessageText={formatMessageText}
          ThinkingDuration={ThinkingDuration}
          
          // Mobile responsiveness
          inputRef={inputFieldRef}
          isIOSDevice={isIOSDevice()}
        />
      )}

      {/* Patient Admission Form Component */}
      <PatientAdmissionForm 
        isOpen={showPatientAdmissionForm}
        onClose={closePatientAdmissionForm}
        onSubmit={handlePatientAdmissionSuccess}
        isSubmitting={isSubmittingAdmission}
        aiMcpServiceRef={aiMcpServiceRef}
      />

      {/* Department Creation Form Component */}
      <DepartmentCreationForm
        isOpen={showDepartmentForm}
        onClose={closeDepartmentForm}
        onSubmit={handleDepartmentSubmit}
        isSubmitting={isSubmittingDepartment}
        aiMcpServiceRef={aiMcpServiceRef}
        userOptions={userOptions}
        loadingDropdowns={loadingDropdowns}
      />

      {/* User Creation Form Component */}
      <UserCreationForm 
        isOpen={showUserForm}
        onClose={closeUserForm}
        onSubmit={handleUserCreationSuccess}
        isSubmitting={isSubmittingUser}
        aiMcpServiceRef={aiMcpServiceRef}
      />

      {/* Staff Creation Form Component */}
      <StaffCreationForm
        isOpen={showStaffForm}
        onClose={closeStaffForm}
        onSubmit={handleStaffSubmit}
        isSubmitting={isSubmittingStaff}
        aiMcpServiceRef={aiMcpServiceRef}
        userOptions={userOptions}
        departmentOptions={departmentOptions}
        loadingDropdowns={loadingDropdowns}
      />

      {/* Room Creation Form Component */}
      <RoomCreationForm
        isOpen={showRoomForm}
        onClose={closeRoomForm}
        onSubmit={handleRoomSubmit}
        isSubmitting={isSubmittingRoom}
        aiMcpServiceRef={aiMcpServiceRef}
        departmentOptions={departmentOptions}
        loadingDropdowns={loadingDropdowns}
      />

      {/* Bed Creation Form Component */}
      <BedCreationForm
        isOpen={showBedForm}
        onClose={closeBedForm}
        onSubmit={handleBedSubmit}
        isSubmitting={isSubmittingBed}
        aiMcpServiceRef={aiMcpServiceRef}
        roomOptions={roomOptions}
        loadingDropdowns={loadingDropdowns}
      />

      {/* Equipment Creation Form Component */}
      <EquipmentCreationForm
        isOpen={showEquipmentForm}
        onClose={closeEquipmentForm}
        onSubmit={handleEquipmentSubmit}
        isSubmitting={isSubmittingEquipment}
        aiMcpServiceRef={aiMcpServiceRef}
        departmentOptions={departmentOptions}
        equipmentCategoryOptions={equipmentCategoryOptions}
        loadingDropdowns={loadingDropdowns}
      />

      {/* Supply Creation Form Component */}
      <SupplyCreationForm
        isOpen={showSupplyForm}
        onClose={closeSupplyForm}
        onSubmit={handleSupplySubmit}
        isSubmitting={isSubmittingSupply}
        aiMcpServiceRef={aiMcpServiceRef}
        supplyCategoryOptions={supplyCategoryOptions}
        loadingDropdowns={loadingDropdowns}
      />

      {/* Legacy User Creation Form Component */}
      <LegacyUserCreationForm
        isOpen={showLegacyUserForm}
        onClose={closeLegacyUserForm}
        onSubmit={handleLegacyUserSubmit}
        isSubmitting={isSubmittingLegacyUser}
        aiMcpServiceRef={aiMcpServiceRef}
      />

      {/* Equipment Category Creation Form Component */}
      <EquipmentCategoryCreationForm
        isOpen={showEquipmentCategoryForm}
        onClose={closeEquipmentCategoryForm}
        onSubmit={handleEquipmentCategorySubmit}
        isSubmitting={isSubmittingEquipmentCategory}
        aiMcpServiceRef={aiMcpServiceRef}
        onCategoryCreated={loadDropdownOptions}
      />

      {/* Supply Category Creation Form Popup */}
      <SupplyCategoryCreationForm
        isOpen={showSupplyCategoryForm}
        onClose={closeSupplyCategoryForm}
        onCategoryCreated={handleSupplyCategorySubmit}
        aiMcpServiceRef={aiMcpServiceRef}
      />

      {/* Discharge Workflow Form Popup */}
      {showDischargeForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-[#2a2a2a] rounded-lg w-full max-w-xl max-h-[90vh] overflow-y-auto">
            <div className="border-b border-gray-700 px-6 py-4">
              <div className="flex items-center justify-between">
                <h2 className="text-xl font-semibold text-white">Patient Discharge Workflow</h2>
                <button onClick={closeDischargeForm} className="text-gray-400 hover:text-white">
                  <X className="w-6 h-6" />
                </button>
              </div>
            </div>
            <div className="px-6 py-4 space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">Patient ID (Optional)</label>
                  <input
                    type="text"
                    value={dischargeFormData.patient_id}
                    onChange={(e) => handleDischargeFormChange('patient_id', e.target.value)}
                    className="w-full px-3 py-2 bg-[#1a1a1a] border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-blue-500"
                    placeholder="Patient UUID"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">Bed ID (Optional)</label>
                  <input
                    type="text"
                    value={dischargeFormData.bed_id}
                    onChange={(e) => handleDischargeFormChange('bed_id', e.target.value)}
                    className="w-full px-3 py-2 bg-[#1a1a1a] border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-blue-500"
                    placeholder="Bed UUID"
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">Patient Name (Optional)</label>
                <input
                  type="text"
                  value={dischargeFormData.patient_name}
                  onChange={(e) => handleDischargeFormChange('patient_name', e.target.value)}
                  className="w-full px-3 py-2 bg-[#1a1a1a] border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-blue-500"
                  placeholder="First Name or Last Name (partial match)"
                />
                <p className="text-xs text-gray-400 mt-1">Provide at least one identifier above</p>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">Discharge Condition</label>
                  <select
                    value={dischargeFormData.discharge_condition}
                    onChange={(e) => handleDischargeFormChange('discharge_condition', e.target.value)}
                    className="w-full px-3 py-2 bg-[#1a1a1a] border border-gray-600 rounded-lg text-white focus:outline-none focus:border-blue-500"
                  >
                    <option value="stable">Stable</option>
                    <option value="improved">Improved</option>
                    <option value="critical">Critical</option>
                    <option value="deceased">Deceased</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">Discharge Destination</label>
                  <select
                    value={dischargeFormData.discharge_destination}
                    onChange={(e) => handleDischargeFormChange('discharge_destination', e.target.value)}
                    className="w-full px-3 py-2 bg-[#1a1a1a] border border-gray-600 rounded-lg text-white focus:outline-none focus:border-blue-500"
                  >
                    <option value="home">Home</option>
                    <option value="transfer">Transfer to Another Facility</option>
                    <option value="rehabilitation">Rehabilitation Center</option>
                    <option value="nursing_home">Nursing Home</option>
                  </select>
                </div>
              </div>
              <div className="bg-blue-900/20 border border-blue-800 rounded-lg p-3">
                <p className="text-sm text-blue-300">
                  <strong>Workflow:</strong> This will discharge the patient, generate a comprehensive report, 
                  start bed cleaning (30 minutes), and automatically update bed status when cleaning is complete.
                </p>
              </div>
            </div>
            <div className="border-t border-gray-700 px-6 py-4 flex justify-end space-x-3">
              <button onClick={closeDischargeForm} disabled={isSubmittingDischarge} className="px-4 py-2 text-gray-400 hover:text-white transition-colors disabled:opacity-50">Cancel</button>
              <button onClick={submitDischarge} disabled={isSubmittingDischarge} className="px-6 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2">
                {isSubmittingDischarge ? (<><div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" /><span>Processing Discharge...</span></>) : (<><CheckCircle className="w-4 h-4" /><span>Complete Discharge</span></>)}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default DirectMCPChatbot;
