import React, { useState, useEffect } from 'react';
import HospitalManagementSystem from './components/HospitalManagementSystem';
import AuthSetup from './components/AuthSetup';
import './App.css';

function App() {
  const [user, setUser] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  // Check for existing user session on app load
  useEffect(() => {
    const savedUser = localStorage.getItem('hospitalUser');
    if (savedUser) {
      try {
        const userData = JSON.parse(savedUser);
        setUser(userData);
      } catch (error) {
        console.error('Error parsing saved user data:', error);
        localStorage.removeItem('hospitalUser');
      }
    }
    setIsLoading(false);
  }, []);

  const handleAuthComplete = (userData) => {
    // Save user data to localStorage
    localStorage.setItem('hospitalUser', JSON.stringify(userData));
    setUser(userData);
  };

  const handleLogout = () => {
    localStorage.removeItem('hospitalUser');
    sessionStorage.removeItem('hms_auth_token');
    sessionStorage.removeItem('hms_auth_user');
    setUser(null);
  };

  // Show loading state
  if (isLoading) {
    return (
      <div className="h-screen bg-slate-950 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 bg-blue-600 rounded-2xl flex items-center justify-center mx-auto mb-4 shadow-xl shadow-blue-500/20">
            <div className="w-8 h-8 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
          </div>
          <p className="text-white text-sm font-medium">Loading Hospital Management System...</p>
        </div>
      </div>
    );
  }

  // Show auth setup if no user is logged in
  if (!user) {
    return <AuthSetup onComplete={handleAuthComplete} />;
  }

  // Show main Hospital Management System for authenticated users
  return (
    <div className="App">
      <HospitalManagementSystem user={user} onLogout={handleLogout} />
    </div>
  );
}

export default App;
