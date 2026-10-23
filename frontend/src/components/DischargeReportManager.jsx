import React, { useState, useEffect } from 'react';
import PDFDownloadManager from '../utils/pdfDownloadManager.js';

const DischargeReportManager = ({ aiMcpService }) => {
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [storageStats, setStorageStats] = useState(null);
  const [selectedBed, setSelectedBed] = useState('');
  const [dischargeData, setDischargeData] = useState({
    condition: 'stable',
    destination: 'home',
    instructions: '',
    followUp: ''
  });

  const pdfManager = new PDFDownloadManager();

  useEffect(() => {
    loadStorageStats();
    loadAvailableReports();
  }, []);

  const loadStorageStats = () => {
    const stats = pdfManager.getStorageStats();
    setStorageStats(stats);
  };

  const loadAvailableReports = async () => {
    try {
      setLoading(true);
      
      if (!aiMcpService?.isConnected) {
        setError('MCP service not connected');
        return;
      }

      // Get list of discharge reports from server
      const result = await aiMcpService.mcpClient.callTool(
        'list_available_discharge_reports',
        {
          status: 'all',
          limit: 50
        }
      );

      if (result.success && result.data) {
        setReports(result.data);
      }

    } catch (err) {
      console.error('Failed to load reports:', err);
      setError('Failed to load reports');
    } finally {
      setLoading(false);
    }
  };

  const generateAndDownloadReport = async () => {
    if (!selectedBed) {
      setError('Please select a bed ID');
      return;
    }

    try {
      setLoading(true);
      setError('');

      console.log('🏥 Generating discharge report for bed:', selectedBed);
      
      // Call the generate_discharge_report tool directly through MCP service
      const result = await aiMcpService.callToolDirectly('generate_discharge_report', {
        bed_id: selectedBed,
        discharge_date: new Date().toISOString(),
        discharge_condition: dischargeData.discharge_condition || 'stable',
        discharge_destination: dischargeData.discharge_destination || 'home',
        discharge_instructions: dischargeData.discharge_instructions || 'Continue medications as prescribed. Follow up with primary care in 2 weeks.',
        follow_up_required: dischargeData.follow_up_required || 'Primary care follow-up in 2 weeks'
      });

      if (result.success) {
        console.log('✅ Report generated:', result.reportNumber);
        
        // Download the PDF and save to local storage
        const downloadResult = await pdfManager.downloadDischargeReportPDF(
          result.reportNumber,
          result.patientName
        );

        if (downloadResult.success) {
          alert(`✅ Success!\n\nReport ${result.reportNumber} has been:\n• Generated successfully\n• Downloaded as PDF\n• Saved to local storage\n\nFile: ${downloadResult.filename}\nSize: ${pdfManager.formatBytes(downloadResult.fileSize)}`);
          
          // Refresh the reports list and storage stats
          loadAvailableReports();
          loadStorageStats();
        } else {
          setError(`Report generated but download failed: ${downloadResult.error}`);
        }
      } else {
        setError(result.message || 'Failed to generate report');
      }

    } catch (err) {
      console.error('❌ Report generation error:', err);
      setError(`Error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const downloadExistingReport = async (reportNumber, patientName) => {
    try {
      setLoading(true);
      
      const result = await pdfManager.downloadDischargeReportPDF(reportNumber, patientName);
      
      if (result.success) {
        alert(`✅ Downloaded: ${result.filename}\nSize: ${pdfManager.formatBytes(result.fileSize)}\nSaved to local storage!`);
        loadStorageStats();
      } else {
        setError(`Download failed: ${result.error}`);
      }
    } catch (err) {
      setError(`Error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const downloadFromLocalStorage = (reportNumber) => {
    const success = pdfManager.downloadStoredReport(reportNumber);
    if (!success) {
      setError('Failed to download from local storage');
    }
  };

  const deleteFromLocalStorage = (reportNumber) => {
    if (confirm(`Delete report ${reportNumber} from local storage?`)) {
      const success = pdfManager.deleteStoredReport(reportNumber);
      if (success) {
        loadStorageStats();
        alert('Report deleted from local storage');
      } else {
        setError('Failed to delete report');
      }
    }
  };

  const clearAllStorage = () => {
    if (confirm('Clear all stored reports from local storage?')) {
      pdfManager.clearStorage();
      loadStorageStats();
      alert('All reports cleared from local storage');
    }
  };

  const getStoredReports = () => {
    return pdfManager.getStoredReports();
  };

  return (
    <div className="discharge-report-manager bg-white rounded-lg shadow-md p-6">
      <h2 className="text-2xl font-bold text-gray-800 mb-6">📋 Discharge Report Manager</h2>

      {/* Error Display */}
      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          <span className="block sm:inline">{error}</span>
          <button
            onClick={() => setError('')}
            className="float-right text-red-700 hover:text-red-900"
          >
            ×
          </button>
        </div>
      )}

      {/* Storage Statistics */}
      {storageStats && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
          <h3 className="font-semibold text-blue-800 mb-2">💾 Local Storage Statistics</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <span className="text-gray-600">Reports Stored:</span>
              <div className="font-semibold">{storageStats.reportCount}</div>
            </div>
            <div>
              <span className="text-gray-600">Storage Used:</span>
              <div className="font-semibold">{storageStats.formattedTotalSize}</div>
            </div>
            <div>
              <span className="text-gray-600">Usage:</span>
              <div className="font-semibold">{storageStats.usagePercentage.toFixed(1)}%</div>
            </div>
            <div>
              <span className="text-gray-600">Max Size:</span>
              <div className="font-semibold">{storageStats.formattedMaxSize}</div>
            </div>
          </div>
          
          {/* Storage Usage Bar */}
          <div className="mt-3">
            <div className="bg-gray-200 rounded-full h-2">
              <div
                className={`h-2 rounded-full ${
                  storageStats.usagePercentage > 80 ? 'bg-red-500' :
                  storageStats.usagePercentage > 60 ? 'bg-yellow-500' : 'bg-green-500'
                }`}
                style={{ width: `${Math.min(storageStats.usagePercentage, 100)}%` }}
              ></div>
            </div>
          </div>

          <button
            onClick={clearAllStorage}
            className="mt-3 px-3 py-1 bg-red-500 text-white text-sm rounded hover:bg-red-600"
            disabled={storageStats.reportCount === 0}
          >
            🗑️ Clear All Storage
          </button>
        </div>
      )}

      {/* Generate New Report */}
      <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-6">
        <h3 className="font-semibold text-green-800 mb-3">📄 Generate New Discharge Report</h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Bed ID (UUID):
            </label>
            <input
              type="text"
              value={selectedBed}
              onChange={(e) => setSelectedBed(e.target.value)}
              placeholder="e.g., 64b05767-1b82-46e4-87e1-00f3615f1c00"
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
            />
            <div className="text-xs text-gray-500 mt-1">
              💡 Use bed ID from occupied beds or test with: 64b05767-1b82-46e4-87e1-00f3615f1c00
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Discharge Condition:
            </label>
            <select
              value={dischargeData.condition}
              onChange={(e) => setDischargeData({...dischargeData, condition: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
            >
              <option value="stable">Stable</option>
              <option value="improving">Improving</option>
              <option value="critical">Critical</option>
              <option value="fair">Fair</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Discharge Destination:
            </label>
            <select
              value={dischargeData.destination}
              onChange={(e) => setDischargeData({...dischargeData, destination: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
            >
              <option value="home">Home</option>
              <option value="nursing_home">Nursing Home</option>
              <option value="rehab_facility">Rehabilitation Facility</option>
              <option value="another_hospital">Another Hospital</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Follow-up Required:
            </label>
            <input
              type="text"
              value={dischargeData.followUp}
              onChange={(e) => setDischargeData({...dischargeData, followUp: e.target.value})}
              placeholder="e.g., Primary care in 1 week"
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
            />
          </div>
        </div>

        <div className="mt-4">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Discharge Instructions:
          </label>
          <textarea
            value={dischargeData.instructions}
            onChange={(e) => setDischargeData({...dischargeData, instructions: e.target.value})}
            placeholder="Enter discharge instructions..."
            rows={3}
            className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
          />
        </div>

        <button
          onClick={generateAndDownloadReport}
          disabled={loading || !selectedBed}
          className="mt-4 px-6 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? '⏳ Generating...' : '📥 Generate & Download PDF'}
        </button>
      </div>

      {/* Server Reports List */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
        <h3 className="font-semibold text-blue-800 mb-3">☁️ Available Server Reports</h3>
        
        <button
          onClick={loadAvailableReports}
          className="mb-4 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 text-sm"
          disabled={loading}
        >
          {loading ? '⏳ Loading...' : '🔄 Refresh Reports'}
        </button>

        {reports.length === 0 ? (
          <p className="text-gray-600 text-sm">No discharge reports found on server.</p>
        ) : (
          <div className="space-y-2">
            {reports.map((report) => (
              <div key={report.report_number} className="bg-white rounded-lg p-3 border border-blue-200">
                <div className="flex justify-between items-center">
                  <div className="flex-1">
                    <div className="font-medium text-sm">{report.report_number}</div>
                    <div className="text-xs text-gray-600">
                      Patient: {report.patient_name} | Generated: {new Date(report.generated_date).toLocaleString()}
                    </div>
                  </div>
                  <button
                    onClick={() => downloadExistingReport(report.report_number, report.patient_name)}
                    disabled={loading}
                    className="px-3 py-1 bg-blue-600 text-white text-xs rounded hover:bg-blue-700 disabled:opacity-50"
                  >
                    📥 Download PDF
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Local Storage Reports */}
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
        <h3 className="font-semibold text-gray-800 mb-3">💾 Locally Stored Reports</h3>
        
        {(() => {
          const storedReports = getStoredReports();
          const reportEntries = Object.entries(storedReports);

          if (reportEntries.length === 0) {
            return <p className="text-gray-600 text-sm">No reports stored locally.</p>;
          }

          return (
            <div className="space-y-2">
              {reportEntries.map(([reportNumber, report]) => (
                <div key={reportNumber} className="bg-white rounded-lg p-3 border border-gray-200">
                  <div className="flex justify-between items-center">
                    <div className="flex-1">
                      <div className="font-medium text-sm">{reportNumber}</div>
                      <div className="text-xs text-gray-600">
                        Patient: {report.patientName} | 
                        Downloaded: {new Date(report.downloadDate).toLocaleString()} | 
                        Size: {pdfManager.formatBytes(report.fileSize)}
                      </div>
                      <div className="text-xs text-gray-500">
                        File: {report.filename}
                      </div>
                    </div>
                    <div className="flex space-x-2">
                      <button
                        onClick={() => downloadFromLocalStorage(reportNumber)}
                        className="px-3 py-1 bg-gray-600 text-white text-xs rounded hover:bg-gray-700"
                      >
                        📂 Download
                      </button>
                      <button
                        onClick={() => deleteFromLocalStorage(reportNumber)}
                        className="px-3 py-1 bg-red-600 text-white text-xs rounded hover:bg-red-700"
                      >
                        🗑️ Delete
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          );
        })()}
      </div>
    </div>
  );
};

export default DischargeReportManager;
