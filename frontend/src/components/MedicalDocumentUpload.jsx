import React, { useState, useRef } from 'react';
import { Upload, FileText, Image, AlertCircle, CheckCircle, Clock } from 'lucide-react';

const MedicalDocumentUpload = ({ patientId, onUploadComplete }) => {
  const [isDragging, setIsDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [uploadStatus, setUploadStatus] = useState(null);
  const [selectedFile, setSelectedFile] = useState(null);
  const [documentType, setDocumentType] = useState('prescription');
  const fileInputRef = useRef(null);

  const documentTypes = [
    { value: 'prescription', label: 'Prescription' },
    { value: 'lab_result', label: 'Lab Result' },
    { value: 'imaging', label: 'Medical Imaging' },
    { value: 'discharge_summary', label: 'Discharge Summary' },
    { value: 'consultation_note', label: 'Consultation Note' },
    { value: 'insurance_document', label: 'Insurance Document' },
    { value: 'other', label: 'Other' }
  ];

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      handleFileSelection(files[0]);
    }
  };

  const handleFileSelection = (file) => {
    // Validate file type
    const allowedTypes = [
      'image/jpeg', 'image/png', 'image/jpg', 'image/gif',
      'application/pdf', 'text/plain'
    ];
    
    if (!allowedTypes.includes(file.type)) {
      setUploadStatus({
        type: 'error',
        message: 'Please upload images (JPG, PNG, GIF) or PDF files only.'
      });
      return;
    }

    // Validate file size (10MB max)
    if (file.size > 10 * 1024 * 1024) {
      setUploadStatus({
        type: 'error',
        message: 'File size must be less than 10MB.'
      });
      return;
    }

    setSelectedFile(file);
    setUploadStatus(null);
  };

  const convertFileToBase64 = (file) => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.readAsDataURL(file);
      reader.onload = () => {
        // Remove the data URL prefix to get just the base64 content
        const base64 = reader.result.split(',')[1];
        resolve(base64);
      };
      reader.onerror = error => reject(error);
    });
  };

  const uploadDocument = async () => {
    if (!selectedFile || !patientId) {
      setUploadStatus({
        type: 'error',
        message: 'Please select a file and ensure patient ID is available.'
      });
      return;
    }

    setUploading(true);
    setUploadStatus(null);

    try {
      // Convert file to base64
      const base64Content = await convertFileToBase64(selectedFile);

      // Call the MCP upload tool
      const uploadResponse = await fetch(`http://${window.location.hostname}:8000/tools/call`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          jsonrpc: '2.0',
          id: 1,
          method: 'tools/call',
          params: {
            name: 'upload_medical_document',
            arguments: {
              patient_id: patientId,
              file_content: base64Content,
              file_name: selectedFile.name,
              document_type: documentType,
              mime_type: selectedFile.type
            }
          }
        })
      });

      const uploadResult = await uploadResponse.json();

      if (uploadResult.result?.content?.[0]?.text) {
        const result = JSON.parse(uploadResult.result.content[0].text);
        
        if (result.success) {
          setUploadStatus({
            type: 'success',
            message: 'Document uploaded successfully!',
            documentId: result.document_id
          });

          // Start processing the document
          setProcessing(true);
          await processDocument(result.document_id);
        } else {
          throw new Error(result.message || 'Upload failed');
        }
      } else {
        throw new Error('Invalid response from server');
      }

    } catch (error) {
      console.error('Upload error:', error);
      setUploadStatus({
        type: 'error',
        message: `Upload failed: ${error.message}`
      });
    } finally {
      setUploading(false);
    }
  };

  const processDocument = async (documentId) => {
    try {
      const processResponse = await fetch(`http://${window.location.hostname}:8000/tools/call`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          jsonrpc: '2.0',
          id: 2,
          method: 'tools/call',
          params: {
            name: 'process_medical_document',
            arguments: {
              document_id: documentId
            }
          }
        })
      });

      const processResult = await processResponse.json();

      if (processResult.result?.content?.[0]?.text) {
        const result = JSON.parse(processResult.result.content[0].text);
        
        if (result.success) {
          setUploadStatus({
            type: 'success',
            message: `Document processed successfully! Extracted ${result.entities_count} medical entities.`,
            documentId: documentId,
            processed: true,
            entitiesCount: result.entities_count,
            confidence: result.confidence_score
          });

          // Call parent callback if provided
          if (onUploadComplete) {
            onUploadComplete({
              documentId,
              fileName: selectedFile.name,
              documentType,
              entitiesCount: result.entities_count,
              confidence: result.confidence_score
            });
          }
        } else {
          throw new Error(result.message || 'Processing failed');
        }
      }
    } catch (error) {
      console.error('Processing error:', error);
      setUploadStatus({
        type: 'warning',
        message: `Document uploaded but processing failed: ${error.message}`
      });
    } finally {
      setProcessing(false);
    }
  };

  const resetUpload = () => {
    setSelectedFile(null);
    setUploadStatus(null);
    setUploading(false);
    setProcessing(false);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const getFileIcon = (file) => {
    if (file.type.startsWith('image/')) {
      return <Image className="w-8 h-8 text-blue-500" />;
    } else if (file.type === 'application/pdf') {
      return <FileText className="w-8 h-8 text-red-500" />;
    }
    return <FileText className="w-8 h-8 text-gray-500" />;
  };

  const getStatusIcon = () => {
    if (uploading || processing) {
      return <Clock className="w-5 h-5 text-blue-500 animate-spin" />;
    }
    if (uploadStatus?.type === 'success') {
      return <CheckCircle className="w-5 h-5 text-green-500" />;
    }
    if (uploadStatus?.type === 'error') {
      return <AlertCircle className="w-5 h-5 text-red-500" />;
    }
    return null;
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h3 className="text-lg font-semibold mb-4 flex items-center">
        <Upload className="w-5 h-5 mr-2" />
        Upload Medical Document
      </h3>

      {/* Document Type Selection */}
      <div className="mb-4">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Document Type
        </label>
        <select
          value={documentType}
          onChange={(e) => setDocumentType(e.target.value)}
          className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        >
          {documentTypes.map((type) => (
            <option key={type.value} value={type.value}>
              {type.label}
            </option>
          ))}
        </select>
      </div>

      {/* File Upload Area */}
      <div
        className={`border-2 border-dashed rounded-lg p-6 text-center transition-colors ${
          isDragging
            ? 'border-blue-500 bg-blue-50'
            : 'border-gray-300 hover:border-gray-400'
        }`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        {selectedFile ? (
          <div className="space-y-4">
            <div className="flex items-center justify-center space-x-3">
              {getFileIcon(selectedFile)}
              <div>
                <p className="font-medium">{selectedFile.name}</p>
                <p className="text-sm text-gray-500">
                  {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                </p>
              </div>
            </div>
            
            <div className="flex space-x-3 justify-center">
              <button
                onClick={uploadDocument}
                disabled={uploading || processing}
                className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
              >
                {uploading ? (
                  <>
                    <Clock className="w-4 h-4 animate-spin" />
                    <span>Uploading...</span>
                  </>
                ) : processing ? (
                  <>
                    <Clock className="w-4 h-4 animate-spin" />
                    <span>Processing...</span>
                  </>
                ) : (
                  <>
                    <Upload className="w-4 h-4" />
                    <span>Upload & Process</span>
                  </>
                )}
              </button>
              
              <button
                onClick={resetUpload}
                disabled={uploading || processing}
                className="bg-gray-600 text-white px-4 py-2 rounded-md hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Cancel
              </button>
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            <Upload className="w-12 h-12 text-gray-400 mx-auto" />
            <div>
              <p className="text-lg font-medium text-gray-900">
                Drop your medical document here
              </p>
              <p className="text-sm text-gray-500">
                or click to browse files
              </p>
            </div>
            
            <input
              ref={fileInputRef}
              type="file"
              onChange={(e) => {
                if (e.target.files && e.target.files[0]) {
                  handleFileSelection(e.target.files[0]);
                }
              }}
              accept="image/*,application/pdf,.txt"
              className="hidden"
            />
            
            <button
              onClick={() => fileInputRef.current?.click()}
              className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700"
            >
              Choose File
            </button>
            
            <p className="text-xs text-gray-400">
              Supported formats: JPG, PNG, GIF, PDF, TXT (Max 10MB)
            </p>
          </div>
        )}
      </div>

      {/* Status Messages */}
      {uploadStatus && (
        <div className={`mt-4 p-4 rounded-md flex items-start space-x-3 ${
          uploadStatus.type === 'success' ? 'bg-green-50 border border-green-200' :
          uploadStatus.type === 'error' ? 'bg-red-50 border border-red-200' :
          'bg-yellow-50 border border-yellow-200'
        }`}>
          {getStatusIcon()}
          <div className="flex-1">
            <p className={`text-sm font-medium ${
              uploadStatus.type === 'success' ? 'text-green-800' :
              uploadStatus.type === 'error' ? 'text-red-800' :
              'text-yellow-800'
            }`}>
              {uploadStatus.message}
            </p>
            
            {uploadStatus.processed && (
              <div className="mt-2 text-xs text-gray-600">
                <p>Document ID: {uploadStatus.documentId}</p>
                <p>Entities Extracted: {uploadStatus.entitiesCount}</p>
                <p>Confidence Score: {(uploadStatus.confidence * 100).toFixed(1)}%</p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default MedicalDocumentUpload;
