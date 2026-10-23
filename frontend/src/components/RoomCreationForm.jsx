import React, { useState, useEffect } from 'react';
import { CheckCircle, X } from 'lucide-react';

const RoomCreationForm = ({ 
  isOpen, 
  onClose, 
  onSubmit, 
  isSubmitting = false,
  aiMcpServiceRef,
  departmentOptions = [],
  loadingDropdowns = false
}) => {
  const [formData, setFormData] = useState({
    room_number: '',
    room_type: '',
    capacity: '',
    floor_number: '',
    department_id: ''
  });

  // Reset form when modal opens
  useEffect(() => {
    if (isOpen) {
      setFormData({
        room_number: '',
        room_type: '',
        capacity: '',
        floor_number: '',
        department_id: ''
      });
    }
  }, [isOpen]);

  const handleFormChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleSubmit = async () => {
    // Validate required fields
    const requiredFields = ['room_number', 'department_id'];
    const missingFields = requiredFields.filter(field => !formData[field].trim());

    if (missingFields.length > 0) {
      alert(`Please fill in the following required fields: ${missingFields.join(', ')}`);
      return;
    }

    try {
      // Call the MCP tool directly to create the room
      const response = await aiMcpServiceRef.current.callToolDirectly('create_room', {
        room_number: formData.room_number,
        department_id: formData.department_id,
        room_type: formData.room_type,
        floor_number: formData.floor_number ? parseInt(formData.floor_number) : undefined,
        capacity: formData.capacity ? parseInt(formData.capacity) : undefined
      });

      // Debug logging
      console.log('Room creation response:', JSON.stringify(response, null, 2));

      if (response && response.success) {
        // Call the parent's onSubmit callback with the response
        onSubmit(response);
        
        // Reset form
        setFormData({
          room_number: '',
          room_type: '',
          capacity: '',
          floor_number: '',
          department_id: ''
        });
      } else {
        // Handle error
        const errorMessage = response?.message || 'Failed to create room';
        alert(`Error creating room: ${errorMessage}`);
      }
    } catch (error) {
      console.error('Error creating room:', error);
      alert(`Error creating room: ${error.message}`);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-2 sm:p-4">
      <div className="bg-gray-900 rounded-lg w-full max-w-4xl max-h-[95vh] sm:max-h-[90vh] overflow-y-auto mx-2 sm:mx-0">
        {/* Header */}
        <div className="border-b border-gray-700 px-4 sm:px-6 py-3 sm:py-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg sm:text-xl font-semibold text-white">Room Creation Form</h2>
            <button 
              onClick={onClose} 
              className="text-gray-400 hover:text-white p-1 transition-colors"
            >
              <X className="w-5 h-5 sm:w-6 sm:h-6" />
            </button>
          </div>
        </div>

        {/* Form Content */}
        <div className="px-4 sm:px-6 py-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Left Column - Room Information */}
            <div className="space-y-4">
              <div>
                <h3 className="text-lg font-medium text-white mb-4">Room Information</h3>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  Room Number <span className="text-red-400">*</span>
                </label>
                <input
                  type="text"
                  value={formData.room_number}
                  onChange={(e) => handleFormChange('room_number', e.target.value)}
                  className="w-full px-3 py-2 bg-gray-800 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="e.g., R101, ICU-02, OT-01"
                />
                <p className="text-xs text-gray-400 mt-1">Unique identifier for the room</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  Room Type <span className="text-red-400">*</span>
                </label>
                <select
                  value={formData.room_type}
                  onChange={(e) => handleFormChange('room_type', e.target.value)}
                  className="w-full px-3 py-3 sm:py-2 bg-gray-800 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-base sm:text-sm"
                >
                  <option value="">Select room type</option>
                  <option value="patient">Patient Room</option>
                  <option value="icu">ICU (Intensive Care Unit)</option>
                  <option value="operation">Operation Theater</option>
                  <option value="emergency">Emergency Room</option>
                  <option value="consultation">Consultation Room</option>
                  <option value="diagnostic">Diagnostic Room</option>
                  <option value="laboratory">Laboratory</option>
                  <option value="pharmacy">Pharmacy</option>
                  <option value="storage">Storage Room</option>
                  <option value="administrative">Administrative Office</option>
                </select>
                <p className="text-xs text-gray-400 mt-1">Select the primary purpose of this room</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  Select Department <span className="text-red-400">*</span>
                </label>
                <select
                  value={formData.department_id}
                  onChange={(e) => handleFormChange('department_id', e.target.value)}
                  className="w-full px-3 py-3 sm:py-2 bg-gray-800 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-base sm:text-sm"
                  disabled={loadingDropdowns}
                >
                  <option value="">
                    {loadingDropdowns ? 'Loading departments...' : 'Select a department'}
                  </option>
                  {Array.isArray(departmentOptions) ? departmentOptions.map(dept => (
                    <option key={dept.id} value={dept.id}>
                      {dept.name} (Floor {dept.floor_number || 'N/A'})
                    </option>
                  )) : []}
                </select>
                <p className="text-xs text-gray-400 mt-1">Choose which department this room belongs to</p>
              </div>
            </div>

            {/* Right Column - Specifications */}
            <div className="space-y-4">
              <div>
                <h3 className="text-lg font-medium text-white mb-4">Room Specifications</h3>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">Capacity</label>
                <input
                  type="number"
                  value={formData.capacity}
                  onChange={(e) => handleFormChange('capacity', e.target.value)}
                  className="w-full px-3 py-2 bg-gray-800 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Number of beds/occupants"
                  min="1"
                  max="50"
                />
                <p className="text-xs text-gray-400 mt-1">Maximum number of beds or occupants</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">Floor Number</label>
                <input
                  type="number"
                  value={formData.floor_number}
                  onChange={(e) => handleFormChange('floor_number', e.target.value)}
                  className="w-full px-3 py-2 bg-gray-800 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="e.g., 1, 2, 3"
                  min="1"
                  max="50"
                />
                <p className="text-xs text-gray-400 mt-1">Which floor is this room located on?</p>
              </div>

              {/* Room Type Specific Guidelines */}
              <div className="mt-6 p-4 bg-gray-800 rounded-lg border border-gray-700">
                <h4 className="text-sm font-medium text-gray-300 mb-2">💡 Room Type Guidelines</h4>
                <div className="text-xs text-gray-400 space-y-1">
                  <p>• <strong>Patient Room:</strong> Standard accommodation, 1-4 beds</p>
                  <p>• <strong>ICU:</strong> Intensive care, specialized equipment</p>
                  <p>• <strong>Operation Theater:</strong> Surgical procedures, sterile environment</p>
                  <p>• <strong>Emergency Room:</strong> Immediate care, quick access</p>
                  <p>• <strong>Consultation:</strong> Doctor-patient meetings</p>
                  <p>• <strong>Diagnostic:</strong> Medical imaging, tests</p>
                </div>
              </div>
            </div>
          </div>

          {/* Information Panel */}
          <div className="mt-6 p-4 bg-blue-900/20 rounded-lg border border-blue-700/30">
            <h3 className="text-sm font-medium text-blue-300 mb-2">📋 Room Setup Guidelines</h3>
            <div className="text-xs text-blue-200/80 space-y-1">
              <p>• Room numbers should be unique and follow hospital naming conventions</p>
              <p>• Department assignment helps with resource allocation and staff management</p>
              <p>• Capacity planning aids in bed management and patient flow</p>
              <p>• Floor number enables efficient navigation and emergency responses</p>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="border-t border-gray-700 px-4 sm:px-6 py-4 flex justify-end space-x-3">
          <button 
            onClick={onClose} 
            disabled={isSubmitting} 
            className="px-4 py-2 text-gray-400 hover:text-white transition-colors disabled:opacity-50"
          >
            Cancel
          </button>
          <button 
            onClick={handleSubmit} 
            disabled={isSubmitting} 
            className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
          >
            {isSubmitting ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                <span>Creating Room...</span>
              </>
            ) : (
              <>
                <CheckCircle className="w-4 h-4" />
                <span>Create Room</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default RoomCreationForm;
