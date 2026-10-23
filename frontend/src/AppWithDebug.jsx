import React, { useState, useEffect } from 'react';
import DirectMCPChatbot from './components/DirectMCPChatbot';
import AuthSetup from './components/AuthSetup';
import './App.css';

function App() {
  const [user, setUser] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  // Check for existing user session on app load
  useEffect(() => {
    const savedUser = localStorage.getItem('hospitalUser');
    console.log('Checking for saved user:', savedUser);
    if (savedUser) {
      try {
        const userData = JSON.parse(savedUser);
        console.log('Parsed user data:', userData);
        setUser(userData);
      } catch (error) {
        console.error('Error parsing saved user data:', error);
        localStorage.removeItem('hospitalUser');
      }
    }
    setIsLoading(false);
  }, []);

  const handleAuthComplete = (userData) => {
    console.log('Auth completed with user data:', userData);
    // Save user data to localStorage
    localStorage.setItem('hospitalUser', JSON.stringify(userData));
    setUser(userData);
  };

  const handleLogout = () => {
    console.log('Logging out user');
    localStorage.removeItem('hospitalUser');
    setUser(null);
  };

  console.log('App render state:', { isLoading, user: !!user });

  // Show loading state
  if (isLoading) {
    console.log('Showing loading state');
    return (
      <div className="h-screen bg-[#1a1a1a] flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 bg-blue-600 rounded-full flex items-center justify-center mx-auto mb-4 shadow-lg">
            <div className="w-8 h-8 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
          </div>
          <p className="text-white text-sm">Loading Hospital Management System...</p>
        </div>
      </div>
    );
  }

  // Show auth setup if no user is logged in
  if (!user) {
    console.log('Showing auth setup');
    return <AuthSetup onComplete={handleAuthComplete} />;
  }

  // Show main application for authenticated users
  console.log('Showing main application');
  return (
    <div className="App">
      <DirectMCPChatbot user={user} onLogout={handleLogout} />
    </div>
  );
}

export default App;
