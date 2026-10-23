import React, { useState, useRef } from 'react';
import { Upload, FileText, X, CheckCircle, AlertCircle, Bed, Package, Settings, Home } from 'lucide-react';
import Papa from 'papaparse';

const BulkDataUpload = ({ onClose, onUploadComplete }) => {
  const [activeCard, setActiveCard] = useState(null);
  const [uploadStatus, setUploadStatus] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [isDragOver, setIsDragOver] = useState(false);
  const fileInputRef = useRef(null);

  // Define CSV templates for each table
  const csvTemplates = {
    beds: {
      name: 'Beds',
      icon: Bed,
      color: 'blue',
      fields: [
        'bed_number',
        'room_number', // This will be converted to room_id
        'bed_type',
        'status',
        'notes'
      ],
      example: [
        {
          bed_number: 'B101A',
          room_number: 'R101',
          bed_type: 'standard',
          status: 'available',
          notes: 'Standard patient bed'
        },
        {
          bed_number: 'B201B',
          room_number: 'R201',
          bed_type: 'icu',
          status: 'maintenance',
          notes: 'ICU bed with monitoring equipment'
        }
      ],
      notes: [
        'bed_type: standard, icu, emergency, pediatric, maternity, surgical, psychiatric, isolation',
        'status: available, occupied, maintenance, reserved, cleaning, out_of_service',
        'room_number will be automatically mapped to room_id',
        'notes field is optional for additional information'
      ]
    },
    equipment: {
      name: 'Equipment',
      icon: Settings,
      color: 'green',
      fields: [
        'equipment_id',
        'name',
        'category_name', // This will be converted to category_id
        'model',
        'manufacturer',
        'serial_number',
        'purchase_date', // YYYY-MM-DD format
        'warranty_expiry', // YYYY-MM-DD format
        'department_name', // This will be converted to department_id
        'status',
        'location',
        'last_maintenance', // YYYY-MM-DD format
        'next_maintenance', // YYYY-MM-DD format
        'cost',
        'notes'
      ],
      example: [
        {
          equipment_id: 'EQ001',
          name: 'X-Ray Machine',
          category_name: 'Imaging',
          model: 'XR-2000',
          manufacturer: 'MedTech Corp',
          serial_number: 'SN123456',
          purchase_date: '2023-01-15',
          warranty_expiry: '2026-01-15',
          department_name: 'Radiology',
          status: 'operational',
          location: 'Room 201',
          last_maintenance: '2024-06-01',
          next_maintenance: '2024-12-01',
          cost: '50000.00',
          notes: 'Digital X-ray system with advanced imaging'
        }
      ],
      notes: [
        'status: operational, maintenance, out_of_order, retired',
        'category_name will be mapped to existing categories',
        'department_name will be mapped to existing departments',
        'Date format: YYYY-MM-DD (e.g., 2024-12-31)',
        'cost should be numeric (e.g., 15000.50)',
        'New categories/departments will be created if not found'
      ]
    },
    rooms: {
      name: 'Rooms',
      icon: Home,
      color: 'purple',
      fields: [
        'room_number',
        'floor_number',
        'room_type',
        'department_name', // This will be converted to department_id
        'capacity',
        'status'
      ],
      example: [
        {
          room_number: 'R101',
          floor_number: 1,
          room_type: 'patient',
          department_name: 'Internal Medicine',
          capacity: 2,
          status: 'available'
        },
        {
          room_number: 'ICU001',
          floor_number: 3,
          room_type: 'icu',
          department_name: 'Intensive Care',
          capacity: 1,
          status: 'occupied'
        }
      ],
      notes: [
        'room_type: patient, icu, operation, emergency, consultation, diagnostic, laboratory, pharmacy, storage, administrative',
        'status: available, occupied, maintenance, cleaning',
        'department_name will be mapped to existing departments',
        'capacity: maximum number of beds/occupants',
        'floor_number should be numeric'
      ]
    },
    supplies: {
      name: 'Supplies',
      icon: Package,
      color: 'orange',
      fields: [
        'item_code',
        'name',
        'category_name', // This will be converted to category_id
        'description',
        'unit_of_measure',
        'minimum_stock_level',
        'maximum_stock_level',
        'current_stock',
        'unit_cost',
        'supplier',
        'expiry_date', // YYYY-MM-DD format
        'location'
      ],
      example: [
        {
          item_code: 'SUP001',
          name: 'Surgical Gloves',
          category_name: 'Medical Supplies',
          description: 'Latex-free surgical gloves, size M',
          unit_of_measure: 'box',
          minimum_stock_level: 10,
          maximum_stock_level: 100,
          current_stock: 50,
          unit_cost: 15.99,
          supplier: 'MedSupply Inc',
          expiry_date: '2025-12-31',
          location: 'Storage Room A'
        }
      ],
      notes: [
        'unit_of_measure: box, unit, bottle, kg, ml, etc.',
        'category_name will be mapped to existing categories',
        'New categories will be created if not found',
        'Numeric fields: stock levels should be integers, unit_cost should be decimal',
        'Date format: YYYY-MM-DD (e.g., 2025-12-31)',
        'All stock and cost fields are optional but recommended'
      ]
    }
  };

  const handleCardClick = (cardType) => {
    setActiveCard(cardType);
    setUploadStatus(null);
  };

  const handleFileUpload = (event) => {
    const file = event.target.files[0];
    if (!file || !activeCard) return;

    processFile(file);
  };

  const handleDrop = (event) => {
    event.preventDefault();
    setIsDragOver(false);
    
    const files = event.dataTransfer.files;
    if (files.length > 0 && activeCard) {
      processFile(files[0]);
    }
  };

  const handleDragOver = (event) => {
    event.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = (event) => {
    event.preventDefault();
    setIsDragOver(false);
  };

  const processFile = (file) => {
    if (!file.name.toLowerCase().endsWith('.csv')) {
      setUploadStatus({
        type: 'error',
        message: 'Please upload a CSV file.'
      });
      return;
    }

    setIsUploading(true);
    setUploadStatus(null);

    Papa.parse(file, {
      header: true,
      skipEmptyLines: true,
      complete: async (results) => {
        try {
          await processUpload(results.data);
        } catch (error) {
          setUploadStatus({
            type: 'error',
            message: `Upload failed: ${error.message}`
          });
        } finally {
          setIsUploading(false);
        }
      },
      error: (error) => {
        setUploadStatus({
          type: 'error',
          message: `CSV parsing failed: ${error.message}`
        });
        setIsUploading(false);
      }
    });
  };

  const processUpload = async (data) => {
    if (!data.length) {
      throw new Error('No data found in CSV file');
    }

    const template = csvTemplates[activeCard];
    
    // Define required fields for each table type
    let requiredFields = [];
    switch (activeCard) {
      case 'beds':
        requiredFields = ['bed_number']; // room_number is also important but handled separately
        break;
      case 'equipment':
        requiredFields = ['equipment_id', 'name']; // category_name, department_name handled separately
        break;
      case 'rooms':
        requiredFields = ['room_number']; // department_name handled separately
        break;
      case 'supplies':
        requiredFields = ['item_code', 'name', 'unit_of_measure']; // category_name handled separately
        break;
      default:
        requiredFields = [];
    }

    // Validate required fields
    const firstRow = data[0];
    const missingFields = requiredFields.filter(field => !firstRow.hasOwnProperty(field) || !firstRow[field]?.toString().trim());
    
    if (missingFields.length > 0) {
      throw new Error(`Missing required fields: ${missingFields.join(', ')}`);
    }

    // Additional validation for foreign key reference fields
    if (activeCard === 'beds' && !firstRow.room_number?.toString().trim()) {
      throw new Error('room_number is required for bed creation');
    }
    if (activeCard === 'equipment' && !firstRow.category_name?.toString().trim()) {
      throw new Error('category_name is required for equipment creation');
    }
    if (activeCard === 'rooms' && !firstRow.department_name?.toString().trim()) {
      throw new Error('department_name is required for room creation');
    }
    if (activeCard === 'supplies' && !firstRow.category_name?.toString().trim()) {
      throw new Error('category_name is required for supply creation');
    }

    // Process the data based on table type
    let processedData;
    switch (activeCard) {
      case 'beds':
        processedData = await processBeds(data);
        break;
      case 'equipment':
        processedData = await processEquipment(data);
        break;
      case 'rooms':
        processedData = await processRooms(data);
        break;
      case 'supplies':
        processedData = await processSupplies(data);
        break;
      default:
        throw new Error('Invalid table type');
    }

    // Send to backend
    const response = await fetch(`http://${window.location.hostname}:8000/api/bulk-upload`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        table: activeCard,
        data: processedData
      })
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.message || 'Upload failed');
    }

    const result = await response.json();
    
    setUploadStatus({
      type: 'success',
      message: `Successfully uploaded ${result.inserted} records to ${template.name} table.`
    });

    if (onUploadComplete) {
      onUploadComplete(activeCard, result);
    }
  };

  const processBeds = async (data) => {
    // Convert room_number to room_id by querying rooms
    const roomNumbers = [...new Set(data.map(row => row.room_number))];
    const roomMappings = await getRoomMappings(roomNumbers);

    return data.map(row => ({
      bed_number: row.bed_number,
      room_id: roomMappings[row.room_number],
      bed_type: row.bed_type,
      status: row.status || 'available',
      notes: row.notes || ''
    }));
  };

  const processEquipment = async (data) => {
    const categoryNames = [...new Set(data.map(row => row.category_name))];
    const departmentNames = [...new Set(data.map(row => row.department_name))];
    
    const [categoryMappings, departmentMappings] = await Promise.all([
      getCategoryMappings(categoryNames, 'equipment'),
      getDepartmentMappings(departmentNames)
    ]);

    return data.map(row => ({
      equipment_id: row.equipment_id,
      name: row.name,
      category_id: categoryMappings[row.category_name],
      model: row.model,
      manufacturer: row.manufacturer,
      serial_number: row.serial_number,
      purchase_date: row.purchase_date || null,
      warranty_expiry: row.warranty_expiry || null,
      department_id: departmentMappings[row.department_name],
      status: row.status || 'operational',
      location: row.location,
      last_maintenance: row.last_maintenance || null,
      next_maintenance: row.next_maintenance || null,
      cost: parseFloat(row.cost) || 0,
      notes: row.notes || ''
    }));
  };

  const processRooms = async (data) => {
    const departmentNames = [...new Set(data.map(row => row.department_name))];
    const departmentMappings = await getDepartmentMappings(departmentNames);

    return data.map(row => ({
      room_number: row.room_number,
      floor_number: parseInt(row.floor_number),
      room_type: row.room_type,
      department_id: departmentMappings[row.department_name],
      capacity: parseInt(row.capacity) || 1,
      status: row.status || 'available'
    }));
  };

  const processSupplies = async (data) => {
    const categoryNames = [...new Set(data.map(row => row.category_name))];
    const categoryMappings = await getCategoryMappings(categoryNames, 'supply');

    return data.map(row => ({
      item_code: row.item_code,
      name: row.name,
      category_id: categoryMappings[row.category_name],
      description: row.description || '',
      unit_of_measure: row.unit_of_measure,
      minimum_stock_level: parseInt(row.minimum_stock_level) || 0,
      maximum_stock_level: parseInt(row.maximum_stock_level) || 0,
      current_stock: parseInt(row.current_stock) || 0,
      unit_cost: parseFloat(row.unit_cost) || 0,
      supplier: row.supplier || '',
      expiry_date: row.expiry_date || null,
      location: row.location || ''
    }));
  };

  // Helper functions to get ID mappings
  const getRoomMappings = async (roomNumbers) => {
    const response = await fetch(`http://${window.location.hostname}:8000/api/rooms/by-numbers`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ room_numbers: roomNumbers })
    });
    if (!response.ok) throw new Error('Failed to fetch room mappings');
    return await response.json();
  };

  const getDepartmentMappings = async (departmentNames) => {
    const response = await fetch(`http://${window.location.hostname}:8000/api/departments/by-names`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ department_names: departmentNames })
    });
    if (!response.ok) throw new Error('Failed to fetch department mappings');
    return await response.json();
  };

  const getCategoryMappings = async (categoryNames, type) => {
    const response = await fetch(`http://${window.location.hostname}:8000/api/categories/by-names`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ category_names: categoryNames, type })
    });
    if (!response.ok) throw new Error('Failed to fetch category mappings');
    return await response.json();
  };

  const downloadSampleCSV = (cardType) => {
    const template = csvTemplates[cardType];
    const csv = Papa.unparse(template.example);
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${cardType}_sample.csv`;
    link.click();
    window.URL.revokeObjectURL(url);
  };

  // Close on Escape key
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape' && onClose) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

  return (
    <div 
      className="fixed inset-0 bg-black/75 backdrop-blur-sm flex items-center justify-center z-50 p-2 sm:p-4 animate-fade-in"
      onClick={(e) => {
        if (e.target === e.currentTarget && onClose) {
          onClose();
        }
      }}
    >
      <div 
        className="bg-slate-900 rounded-2xl border border-slate-700 w-full max-w-4xl max-h-[95vh] sm:max-h-[90vh] overflow-y-auto shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="border-b border-slate-800 p-4 sm:p-5 flex items-center justify-between">
          <div className="flex-1 min-w-0">
            <h2 className="text-lg sm:text-xl font-bold text-white truncate">Bulk Data Upload</h2>
            <p className="text-slate-400 text-xs sm:text-sm hidden sm:block">Upload CSV files to populate database tables</p>
            <p className="text-slate-400 text-xs sm:hidden">Upload CSV files</p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="text-slate-400 hover:text-white p-2 rounded-xl hover:bg-slate-800 transition-colors cursor-pointer ml-2 flex-shrink-0"
            aria-label="Close"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-3 sm:p-6">
          {!activeCard ? (
            // Table selection cards
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4">
              {Object.entries(csvTemplates).map(([key, template]) => {
                const Icon = template.icon;
                const colorClasses = {
                  blue: 'border-blue-500 bg-blue-500/10 hover:bg-blue-500/20',
                  green: 'border-green-500 bg-green-500/10 hover:bg-green-500/20',
                  purple: 'border-purple-500 bg-purple-500/10 hover:bg-purple-500/20',
                  orange: 'border-orange-500 bg-orange-500/10 hover:bg-orange-500/20'
                };

                return (
                  <div
                    key={key}
                    onClick={() => handleCardClick(key)}
                    className={`p-4 sm:p-6 rounded-lg border cursor-pointer transition-all ${colorClasses[template.color]} active:scale-95`}
                  >
                    <div className="flex items-center space-x-2 sm:space-x-3 mb-2 sm:mb-3">
                      <Icon className={`w-6 h-6 sm:w-8 sm:h-8 text-${template.color}-400 flex-shrink-0`} />
                      <h3 className="text-base sm:text-lg font-semibold text-white">{template.name}</h3>
                    </div>
                    <p className="text-gray-300 text-xs sm:text-sm mb-3 sm:mb-4">
                      Upload CSV data for {template.name.toLowerCase()} management
                    </p>
                    <div className="text-xs text-gray-400">
                      <strong>Fields:</strong> 
                      <span className="hidden sm:inline"> {template.fields.join(', ')}</span>
                      <span className="sm:hidden"> {template.fields.length} fields</span>
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            // Upload interface for selected table
            <div>
              <div className="flex items-center justify-between mb-4 sm:mb-6">
                <div className="flex items-center space-x-2 sm:space-x-3 flex-1 min-w-0">
                  {React.createElement(csvTemplates[activeCard].icon, {
                    className: `w-5 h-5 sm:w-6 sm:h-6 text-${csvTemplates[activeCard].color}-400 flex-shrink-0`
                  })}
                  <h3 className="text-base sm:text-lg font-semibold text-white truncate">
                    Upload {csvTemplates[activeCard].name}
                  </h3>
                </div>
                <button
                  onClick={() => {
                    setActiveCard(null);
                    setUploadStatus(null);
                  }}
                  className="text-gray-400 hover:text-white text-xs sm:text-sm whitespace-nowrap ml-2"
                >
                  ← Back
                </button>
              </div>

              {/* CSV Format Guide */}
              <div className="bg-[#2a2a2a] rounded-lg p-3 sm:p-4 mb-4 sm:mb-6">
                <h4 className="text-white font-medium mb-2 sm:mb-3 text-sm sm:text-base">CSV Format Requirements</h4>
                
                <div className="grid grid-cols-1 gap-3 sm:gap-4">
                  <div>
                    <h5 className="text-xs sm:text-sm font-medium text-gray-300 mb-2">Required Fields:</h5>
                    <div className="text-xs text-gray-400 space-y-1">
                      <div className="flex flex-wrap gap-1 sm:gap-2">
                        {csvTemplates[activeCard].fields.map(field => (
                          <div key={field} className={`font-mono bg-gray-800 px-2 py-1 rounded text-xs ${
                            // Highlight required fields based on table type
                            ((activeCard === 'beds' && ['bed_number', 'room_number'].includes(field)) ||
                             (activeCard === 'equipment' && ['equipment_id', 'name', 'category_name'].includes(field)) ||
                             (activeCard === 'rooms' && ['room_number', 'department_name'].includes(field)) ||
                             (activeCard === 'supplies' && ['item_code', 'name', 'unit_of_measure', 'category_name'].includes(field)))
                            ? 'bg-blue-800 text-blue-200' : 'bg-gray-800 text-gray-300'
                          }`}>
                            {field}
                            {/* Mark required fields */}
                            {((activeCard === 'beds' && ['bed_number', 'room_number'].includes(field)) ||
                             (activeCard === 'equipment' && ['equipment_id', 'name', 'category_name'].includes(field)) ||
                             (activeCard === 'rooms' && ['room_number', 'department_name'].includes(field)) ||
                             (activeCard === 'supplies' && ['item_code', 'name', 'unit_of_measure', 'category_name'].includes(field))) && 
                             <span className="text-red-400 ml-1">*</span>
                            }
                          </div>
                        ))}
                      </div>
                      <div className="text-xs text-blue-300 mt-2">
                        <span className="text-red-400">*</span> Required fields
                      </div>
                    </div>
                  </div>
                  
                  <div>
                    <h5 className="text-xs sm:text-sm font-medium text-gray-300 mb-2">Important Notes:</h5>
                    <div className="text-xs text-gray-400 space-y-1">
                      {csvTemplates[activeCard].notes.map((note, index) => (
                        <div key={index} className="break-words">• {note}</div>
                      ))}
                    </div>
                  </div>
                </div>

                <div className="mt-3 sm:mt-4 flex flex-col sm:flex-row space-y-2 sm:space-y-0 sm:space-x-3">
                  <button
                    onClick={() => downloadSampleCSV(activeCard)}
                    className="bg-gray-600 hover:bg-gray-700 text-white px-3 py-1.5 rounded text-xs sm:text-sm flex items-center justify-center space-x-2"
                  >
                    <FileText className="w-3 h-3 sm:w-4 sm:h-4" />
                    <span>Download Sample CSV</span>
                  </button>
                </div>
              </div>

              {/* File Upload */}
              <div 
                className={`border-2 border-dashed rounded-lg p-4 sm:p-8 text-center transition-colors ${
                  isDragOver 
                    ? 'border-blue-500 bg-blue-500/10' 
                    : 'border-gray-600'
                }`}
                onDrop={handleDrop}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".csv"
                  onChange={handleFileUpload}
                  className="hidden"
                />
                
                {!isUploading ? (
                  <div>
                    <Upload className={`w-8 h-8 sm:w-12 sm:h-12 mx-auto mb-3 sm:mb-4 ${
                      isDragOver ? 'text-blue-400' : 'text-gray-400'
                    }`} />
                    <p className="text-white mb-2 text-sm sm:text-base">
                      <span className="hidden sm:inline">
                        {isDragOver ? 'Drop CSV file here' : 'Drop your CSV file here or click to browse'}
                      </span>
                      <span className="sm:hidden">Upload CSV file</span>
                    </p>
                    <p className="text-gray-400 text-xs sm:text-sm mb-3 sm:mb-4">Maximum file size: 10MB</p>
                    <button
                      onClick={() => fileInputRef.current?.click()}
                      className="bg-blue-600 hover:bg-blue-700 active:bg-blue-800 text-white px-4 py-2 rounded-md text-sm sm:text-base w-full sm:w-auto transition-colors"
                    >
                      Choose File
                    </button>
                  </div>
                ) : (
                  <div>
                    <div className="w-6 h-6 sm:w-8 sm:h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-3 sm:mb-4"></div>
                    <p className="text-white text-sm sm:text-base">Processing upload...</p>
                  </div>
                )}
              </div>

              {/* Upload Status */}
              {uploadStatus && (
                <div className={`mt-3 sm:mt-4 p-3 sm:p-4 rounded-lg flex items-start space-x-3 ${
                  uploadStatus.type === 'success' 
                    ? 'bg-green-500/10 border border-green-500' 
                    : 'bg-red-500/10 border border-red-500'
                }`}>
                  {uploadStatus.type === 'success' ? (
                    <CheckCircle className="w-4 h-4 sm:w-5 sm:h-5 text-green-400 flex-shrink-0 mt-0.5" />
                  ) : (
                    <AlertCircle className="w-4 h-4 sm:w-5 sm:h-5 text-red-400 flex-shrink-0 mt-0.5" />
                  )}
                  <p className={`text-xs sm:text-sm ${uploadStatus.type === 'success' ? 'text-green-300' : 'text-red-300'} break-words`}>
                    {uploadStatus.message}
                  </p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default BulkDataUpload;
