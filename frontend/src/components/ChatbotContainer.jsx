/**
 * Example integration of AI Clinical Chatbot with main chatbot
 * This shows how to implement the back navigation functionality
 */

import React, { useState } from 'react';
import AIClinicalChatbot from './components/AIClinicalChatbot';
import YourMainChatbot from './components/YourMainChatbot'; // Replace with your actual main chatbot component

const ChatbotContainer = ({ aiService }) => {
  const [currentView, setCurrentView] = useState('main'); // 'main' or 'clinical'

  // Function to switch to AI Clinical Assistant
  const switchToAIClinical = () => {
    setCurrentView('clinical');
  };

  // Function to return to main chatbot
  const backToMainChat = () => {
    setCurrentView('main');
  };

  if (currentView === 'clinical') {
    return (
      <AIClinicalChatbot 
        aiService={aiService}
        onBackToMainChat={backToMainChat}
      />
    );
  }

  return (
    <YourMainChatbot 
      aiService={aiService}
      onSwitchToAIClinical={switchToAIClinical}
    />
  );
};

export default ChatbotContainer;
