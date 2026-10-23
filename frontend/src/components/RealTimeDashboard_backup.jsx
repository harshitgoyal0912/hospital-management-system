// RealTimeDashboard.jsx - Clean backup before fixing the current broken file
import React, { useState, useEffect } from 'react';
import { ArrowLeft, Activity, AlertTriangle, Users, Bed, Clock, Zap } from 'lucide-react';
import { useDashboard } from '../contexts/DashboardContext';

const RealTimeDashboard = ({ onBack, setActiveTab }) => {
  const { dashboardData, isLoading, refresh } = useDashboard();

  // Auto-refresh every 30 seconds
  useEffect(() => {
    const interval = setInterval(refresh, 30000);
    return () => clearInterval(interval);
  }, [refresh]);

  return (
    <div className="h-screen bg-[#1a1a1a] text-white flex flex-col overflow-hidden">
      {/* Header */}
      <div className="flex-shrink-0 flex items-center justify-between p-6 border-b border-gray-700">
        <div className="flex items-center space-x-4">
          {onBack && (
            <button
              onClick={onBack}
              className="p-2 text-gray-400 hover:text-gray-300 hover:bg-gray-700 rounded-md transition-colors"
              title="Back to Chat"
            >
              <ArrowLeft className="w-5 h-5" />
            </button>
          )}
          <h1 className="text-2xl font-bold text-white">📊 Hospital Dashboard</h1>
        </div>
        <div className="flex items-center space-x-4">
          <button 
            onClick={refresh}
            className="bg-blue-600 text-white px-4 py-2 rounded text-sm hover:bg-blue-700 flex items-center space-x-2"
          >
            <Activity className="w-4 h-4" />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {/* Stats Grid */}
        <div className="flex-shrink-0">
          <HospitalStatsGrid />
        </div>

        {/* Charts and Alerts Grid */}
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-6 flex-shrink-0">
          <BedOccupancyChart />
          <EmergencyAlertsPanel />
        </div>

        {/* Activity Feed */}
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-6 flex-shrink-0">
          <RecentActivityPanel />
          <HospitalStatusOverview />
        </div>
      </div>

      {/* Footer */}
      <div className="flex-shrink-0">
        <LastUpdated />
      </div>
    </div>
  );
};

// Hospital Status Overview Component
const HospitalStatusOverview = () => {
  const { dashboardData } = useDashboard();

  return (
    <div className="bg-[#2a2a2a] rounded-lg p-6 border border-gray-600">
      <h3 className="text-lg font-medium text-white mb-4">📈 Hospital Status Overview</h3>
      <div className="space-y-4">
        {/* Capacity Status */}
        <div className="bg-[#333] rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <h4 className="text-white font-medium flex items-center">
              <span className="text-lg mr-2">🏥</span>
              Overall Capacity
            </h4>
            <span className="text-sm text-gray-400">Real-time</span>
          </div>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <div className="text-gray-400">Bed Utilization</div>
              <div className="text-white font-medium">
                {dashboardData.stats?.beds ? `${dashboardData.stats.beds.occupancy_rate}%` : 'Loading...'}
              </div>
            </div>
            <div>
              <div className="text-gray-400">Available Beds</div>
              <div className="text-white font-medium">
                {dashboardData.stats?.beds ? `${dashboardData.stats.beds.available}` : 'Loading...'}
              </div>
            </div>
          </div>
        </div>

        {/* Patient Flow */}
        <div className="bg-[#333] rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <h4 className="text-white font-medium flex items-center">
              <span className="text-lg mr-2">🚶‍♂️</span>
              Patient Flow Today
            </h4>
            <span className="text-sm text-gray-400">24hr</span>
          </div>
          <div className="grid grid-cols-3 gap-2 text-sm">
            <div className="text-center">
              <div className="text-green-400 font-bold text-lg">
                {dashboardData.stats?.patients?.admissions_today || 0}
              </div>
              <div className="text-gray-400 text-xs">Admissions</div>
            </div>
            <div className="text-center">
              <div className="text-blue-400 font-bold text-lg">
                {dashboardData.stats?.patients?.total || 0}
              </div>
              <div className="text-gray-400 text-xs">In Hospital</div>
            </div>
            <div className="text-center">
              <div className="text-orange-400 font-bold text-lg">
                {dashboardData.stats?.patients?.discharges_today || 0}
              </div>
              <div className="text-gray-400 text-xs">Discharges</div>
            </div>
          </div>
        </div>

        {/* Critical Metrics */}
        <div className="bg-[#333] rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <h4 className="text-white font-medium flex items-center">
              <span className="text-lg mr-2">⚡</span>
              Critical Metrics
            </h4>
            <span className="text-sm text-gray-400">Live</span>
          </div>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div className="flex items-center justify-between">
              <span className="text-gray-400">Staff on Duty:</span>
              <span className="text-white font-medium">
                {dashboardData.stats?.staff?.on_duty || 0}/{dashboardData.stats?.staff?.total_active || 0}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-400">Active Alerts:</span>
              <span className={`font-medium ${
                dashboardData.alerts?.total_alerts > 0 ? 'text-orange-400' : 'text-green-400'
              }`}>
                {dashboardData.alerts?.total_alerts || 0}
              </span>
            </div>
          </div>
        </div>

        {/* Quick Stats */}
        <div className="grid grid-cols-2 gap-3">
          <div className="bg-blue-900/30 border border-blue-600/30 rounded-lg p-3 text-center">
            <div className="text-blue-400 text-lg font-bold">
              {dashboardData.beds?.departments?.length || 0}
            </div>
            <div className="text-gray-400 text-xs">Departments</div>
          </div>
          <div className="bg-green-900/30 border border-green-600/30 rounded-lg p-3 text-center">
            <div className="text-green-400 text-lg font-bold">
              {Math.round(((dashboardData.stats?.beds?.total || 0) - (dashboardData.stats?.beds?.occupied || 0)) / (dashboardData.stats?.beds?.total || 1) * 100) || 0}%
            </div>
            <div className="text-gray-400 text-xs">Available</div>
          </div>
        </div>
      </div>
    </div>
  );
};

// Other components would be defined here...
// (HospitalStatsGrid, BedOccupancyChart, EmergencyAlertsPanel, RecentActivityPanel, LastUpdated)

export default RealTimeDashboard;
