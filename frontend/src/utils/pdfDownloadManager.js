/**
 * PDF Download Utility for Hospital Management System
 * Handles PDF file downloads and local storage management
 */

class PDFDownloadManager {
  constructor() {
    this.STORAGE_KEY = 'hospital_downloaded_reports';
    this.MAX_STORAGE_SIZE = 50 * 1024 * 1024; // 50MB limit
  }

  /**
   * Download a discharge report as PDF and save to local storage
   * @param {string} reportNumber - The report number to download
   * @param {string} patientName - Patient name for filename
   * @returns {Promise<Object>} Download result
   */
  async downloadDischargeReportPDF(reportNumber, patientName = '') {
    try {
      console.log('📥 Downloading discharge report PDF:', reportNumber);
      
      const apiUrl = `http://${window.location.hostname}:8000/tools/call`;
      
      // Make API call to download PDF
      const response = await fetch(apiUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          jsonrpc: "2.0",
          id: 1,
          params: {
            name: 'download_discharge_report',
            arguments: {
              report_number: reportNumber,
              download_format: 'pdf'
            }
          }
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      
      // Parse MCP JSON-RPC response
      if (result.error) {
        throw new Error(result.error.message || 'MCP API error');
      }
      
      if (!result.result?.content?.[0]?.text) {
        throw new Error('Invalid MCP response format');
      }
      
      // Parse the text content which contains the actual result
      const pdfData = JSON.parse(result.result.content[0].text);
      
      if (!pdfData.success) {
        throw new Error(pdfData.error || pdfData.message || 'Failed to download PDF');
      }
      console.log('✅ PDF download response:', pdfData);

      // Get the actual PDF file
      const pdfResponse = await this.fetchPDFFile(pdfData.download_path);
      const blob = await pdfResponse.blob();
      
      // Create download filename
      const timestamp = new Date().toISOString().slice(0, 19).replace(/[:]/g, '-');
      const sanitizedPatientName = patientName.replace(/[^a-zA-Z0-9]/g, '_');
      const filename = `${reportNumber}_${sanitizedPatientName}_${timestamp}.pdf`;
      
      // Save to local storage
      await this.saveToLocalStorage(reportNumber, blob, filename, {
        patientName,
        reportNumber,
        downloadDate: new Date().toISOString(),
        fileSize: blob.size
      });

      // Trigger browser download
      this.triggerBrowserDownload(blob, filename);

      // Get current storage stats
      const storageStats = this.getStorageStats();

      return {
        success: true,
        filename,
        fileSize: blob.size,
        storageStats,
        storedLocally: true,
        message: 'PDF downloaded successfully and saved to local storage'
      };

    } catch (error) {
      console.error('❌ PDF download error:', error);
      return {
        success: false,
        error: error.message,
        message: 'Failed to download PDF'
      };
    }
  }

  /**
   * Fetch the actual PDF file from the server
   * @param {string} filePath - Server file path
   * @returns {Promise<Response>} PDF response
   */
  async fetchPDFFile(filePath) {
    // Convert Windows path to URL-friendly path
    // The server serves from 'reports' directory as root, so remove 'reports\' or 'reports/'
    const urlPath = filePath.replace(/\\/g, '/').replace(/^reports\//, '');
    
    const baseUrl = `http://${window.location.hostname}:8000`;
    
    const pdfUrl = `${baseUrl}/${urlPath}`;
    
    console.log('📡 Fetching PDF from:', pdfUrl);
    
    const response = await fetch(pdfUrl, {
      method: 'GET',
      headers: {
        'Accept': 'application/pdf',
      }
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch PDF file: ${response.status}`);
    }

    return response;
  }

  /**
   * Save PDF blob to browser's local storage
   * @param {string} reportNumber - Report identifier
   * @param {Blob} blob - PDF blob data
   * @param {string} filename - File name
   * @param {Object} metadata - File metadata
   */
  async saveToLocalStorage(reportNumber, blob, filename, metadata) {
    try {
      // Convert blob to base64 for storage
      const base64Data = await this.blobToBase64(blob);
      
      // Get existing storage
      const existingData = this.getStoredReports();
      
      // Check storage size limit
      const newSize = base64Data.length;
      if (this.calculateStorageSize(existingData) + newSize > this.MAX_STORAGE_SIZE) {
        // Remove oldest reports to make space
        this.cleanupOldReports(existingData, newSize);
      }

      // Store the new report
      existingData[reportNumber] = {
        ...metadata,
        filename,
        data: base64Data,
        storedAt: new Date().toISOString()
      };

      localStorage.setItem(this.STORAGE_KEY, JSON.stringify(existingData));
      console.log('💾 PDF saved to local storage:', filename);

    } catch (error) {
      console.error('❌ Failed to save to local storage:', error);
      throw error;
    }
  }

  /**
   * Convert blob to base64 string
   * @param {Blob} blob - The blob to convert
   * @returns {Promise<string>} Base64 string
   */
  blobToBase64(blob) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => resolve(reader.result.split(',')[1]); // Remove data:application/pdf;base64, prefix
      reader.onerror = reject;
      reader.readAsDataURL(blob);
    });
  }

  /**
   * Trigger browser download of the PDF
   * @param {Blob} blob - PDF blob
   * @param {string} filename - Download filename
   */
  triggerBrowserDownload(blob, filename) {
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.style.display = 'none';
    a.href = url;
    a.download = filename;
    
    document.body.appendChild(a);
    a.click();
    
    // Cleanup
    setTimeout(() => {
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    }, 100);
  }

  /**
   * Get all stored reports from local storage
   * @returns {Object} Stored reports data
   */
  getStoredReports() {
    try {
      const stored = localStorage.getItem(this.STORAGE_KEY);
      return stored ? JSON.parse(stored) : {};
    } catch (error) {
      console.error('❌ Failed to read from local storage:', error);
      return {};
    }
  }

  /**
   * Get a specific stored report
   * @param {string} reportNumber - Report identifier
   * @returns {Object|null} Report data or null
   */
  getStoredReport(reportNumber) {
    const stored = this.getStoredReports();
    return stored[reportNumber] || null;
  }

  /**
   * Calculate total storage size
   * @param {Object} reportsData - Reports data object
   * @returns {number} Total size in bytes
   */
  calculateStorageSize(reportsData) {
    return Object.values(reportsData).reduce((total, report) => {
      return total + (report.data ? report.data.length : 0);
    }, 0);
  }

  /**
   * Clean up old reports to make space
   * @param {Object} existingData - Current stored data
   * @param {number} requiredSpace - Space needed for new report
   */
  cleanupOldReports(existingData, requiredSpace) {
    // Sort by stored date (oldest first)
    const reports = Object.entries(existingData).sort((a, b) => 
      new Date(a[1].storedAt) - new Date(b[1].storedAt)
    );

    let freedSpace = 0;
    let currentSize = this.calculateStorageSize(existingData);

    // Remove reports until we have enough space
    for (const [reportNumber, reportData] of reports) {
      if (currentSize - freedSpace + requiredSpace <= this.MAX_STORAGE_SIZE) {
        break;
      }

      console.log('🗑️ Removing old report to make space:', reportNumber);
      delete existingData[reportNumber];
      freedSpace += reportData.data ? reportData.data.length : 0;
    }
  }

  /**
   * Download a stored report from local storage
   * @param {string} reportNumber - Report identifier
   * @returns {boolean} Success status
   */
  downloadStoredReport(reportNumber) {
    try {
      const report = this.getStoredReport(reportNumber);
      if (!report || !report.data) {
        console.error('❌ Report not found in local storage:', reportNumber);
        return false;
      }

      // Convert base64 back to blob
      const binaryString = atob(report.data);
      const bytes = new Uint8Array(binaryString.length);
      for (let i = 0; i < binaryString.length; i++) {
        bytes[i] = binaryString.charCodeAt(i);
      }
      const blob = new Blob([bytes], { type: 'application/pdf' });

      // Trigger download
      this.triggerBrowserDownload(blob, report.filename);
      return true;

    } catch (error) {
      console.error('❌ Failed to download stored report:', error);
      return false;
    }
  }

  /**
   * Get storage statistics
   * @returns {Object} Storage statistics
   */
  getStorageStats() {
    const stored = this.getStoredReports();
    const reportCount = Object.keys(stored).length;
    const totalSize = this.calculateStorageSize(stored);
    
    return {
      reportCount,
      totalSize,
      maxSize: this.MAX_STORAGE_SIZE,
      usagePercentage: (totalSize / this.MAX_STORAGE_SIZE) * 100,
      formattedTotalSize: this.formatBytes(totalSize),
      formattedMaxSize: this.formatBytes(this.MAX_STORAGE_SIZE)
    };
  }

  /**
   * Format bytes to human readable string
   * @param {number} bytes - Bytes to format
   * @returns {string} Formatted string
   */
  formatBytes(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }

  /**
   * Clear all stored reports
   */
  clearStorage() {
    localStorage.removeItem(this.STORAGE_KEY);
    console.log('🗑️ Cleared all stored reports');
  }

  /**
   * Delete a specific report from storage
   * @param {string} reportNumber - Report to delete
   * @returns {boolean} Success status
   */
  deleteStoredReport(reportNumber) {
    try {
      const stored = this.getStoredReports();
      if (stored[reportNumber]) {
        delete stored[reportNumber];
        localStorage.setItem(this.STORAGE_KEY, JSON.stringify(stored));
        console.log('🗑️ Deleted stored report:', reportNumber);
        return true;
      }
      return false;
    } catch (error) {
      console.error('❌ Failed to delete stored report:', error);
      return false;
    }
  }
}

export default PDFDownloadManager;
