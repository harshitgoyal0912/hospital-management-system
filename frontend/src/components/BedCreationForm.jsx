import React, { useState } from 'react';
import { X, CheckCircle, Bed } from 'lucide-react';

const BedCreationForm = ({
  isOpen,
  onClose,
  onSubmit,
  isSubmitting,
  aiMcpServiceRef,
  roomOptions = [],
  loadingDropdowns
}) => {
  const [formData, setFormData] = useState({
    bed_number: '',
    room_id: '',
    bed_type: '',
    status: 'available'
  });

  const handleFormChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleSubmit = async () => {
    const requiredFields = ['bed_number'];
    const missingFields = requiredFields.filter(field => !formData[field].trim());
    
    if (missingFields.length > 0) {
      alert(`Please fill in the following required fields: ${missingFields.join(', ')}`);
      return;
    }

    try {
      const response = await aiMcpServiceRef.current.callToolDirectly('create_bed', {
        bed_number: formData.bed_number,
        room_id: formData.room_id,
        bed_type: formData.bed_type,
        status: formData.status
      });

      // Reset form
      setFormData({
        bed_number: '',
        room_id: '',
        bed_type: '',
        status: 'available'
      });

      // Call parent submit handler
      if (onSubmit) {
        onSubmit(response);
      }
    } catch (error) {
      console.error('Error creating bed:', error);
      alert('Failed to create bed. Please try again.');
    }
  };

  const handleClose = () => {
    // Reset form when closing
    setFormData({
      bed_number: '',
      room_id: '',
      bed_type: '',
      status: 'available'
    });
    
    if (onClose) {
      onClose();
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-[#2a2a2a] rounded-lg w-full max-w-4xl max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="border-b border-gray-700 px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <Bed className="w-6 h-6 text-blue-400" />
              <h2 className="text-xl font-semibold text-white">Bed Creation Form</h2>
            </div>
            <button onClick={handleClose} className="text-gray-400 hover:text-white">
              <X className="w-6 h-6" />
            </button>
          </div>
        </div>

        {/* Form Content */}
        <div className="px-6 py-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            
            {/* Basic Information */}
            <div className="space-y-4">
              <div className="border-b border-gray-600 pb-2 mb-4">
                <h3 className="text-lg font-medium text-white flex items-center">
                  <Bed className="w-5 h-5 mr-2 text-blue-400" />
                  Basic Information
                </h3>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  Bed Number *
                  <span className="text-xs text-gray-400 ml-1">(e.g., B101, ICU-01)</span>
                </label>
                <input
                  type="text"
                  value={formData.bed_number}
                  onChange={(e) => handleFormChange('bed_number', e.target.value)}
                  className="w-full px-3 py-2 bg-[#1a1a1a] border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-blue-500"
                  placeholder="B101"
                />
                <p className="text-xs text-gray-400 mt-1">Unique identifier for this bed</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">Select Room</label>
                <select
                  value={formData.room_id}
                  onChange={(e) => handleFormChange('room_id', e.target.value)}
                  className="w-full px-3 py-2 bg-[#1a1a1a] border border-gray-600 rounded-lg text-white focus:outline-none focus:border-blue-500"
                  disabled={loadingDropdowns}
                >
                  <option value="">Select a room ({roomOptions?.length || 0} available)</option>
                  {Array.isArray(roomOptions) ? roomOptions.map(room => (
                    <option key={room.id} value={room.id}>
                      Room {room.room_number} ({room.room_type}) - Floor {room.floor_number || 'N/A'}
                    </option>
                  )) : []}
                </select>
                <p className="text-xs text-gray-400 mt-1">Choose which room this bed will be placed in</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">Bed Type</label>
                <select
                  value={formData.bed_type}
                  onChange={(e) => handleFormChange('bed_type', e.target.value)}
                  className="w-full px-3 py-2 bg-[#1a1a1a] border border-gray-600 rounded-lg text-white focus:outline-none focus:border-blue-500"
                >
                  <option value="">Select bed type</option>
                  <option value="standard">Standard</option>
                  <option value="icu">ICU</option>
                  <option value="pediatric">Pediatric</option>
                  <option value="maternity">Maternity</option>
                  <option value="emergency">Emergency</option>
                  <option value="surgical">Surgical</option>
                  <option value="psychiatric">Psychiatric</option>
                  <option value="isolation">Isolation</option>
                </select>
                <p className="text-xs text-gray-400 mt-1">Type of bed based on medical requirements</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">Status</label>
                <select
                  value={formData.status}
                  onChange={(e) => handleFormChange('status', e.target.value)}
                  className="w-full px-3 py-2 bg-[#1a1a1a] border border-gray-600 rounded-lg text-white focus:outline-none focus:border-blue-500"
                >
                  <option value="available">Available</option>
                  <option value="occupied">Occupied</option>
                  <option value="maintenance">Maintenance</option>
                  <option value="reserved">Reserved</option>
                  <option value="cleaning">Cleaning</option>
                  <option value="out_of_service">Out of Service</option>
                </select>
                <p className="text-xs text-gray-400 mt-1">Current status of the bed</p>
              </div>
            </div>

            {/* Guidelines & Information */}
            <div className="space-y-4">
              <div className="border-b border-gray-600 pb-2 mb-4">
                <h3 className="text-lg font-medium text-white flex items-center">
                  💡 Guidelines & Information
                </h3>
              </div>

              {/* Bed Type Guidelines */}
              <div className="bg-[#1a1a1a] rounded-lg p-4 border border-gray-600">
                <h4 className="text-sm font-medium text-blue-400 mb-2">🛏️ Bed Type Guidelines</h4>
                <div className="text-xs text-gray-400 space-y-1">
                  <div><strong>Standard:</strong> Regular patient rooms</div>
                  <div><strong>ICU:</strong> Intensive care with monitoring equipment</div>
                  <div><strong>Pediatric:</strong> Child-sized beds with safety features</div>
                  <div><strong>Maternity:</strong> Specialized for childbirth and recovery</div>
                  <div><strong>Emergency:</strong> Quick access beds in ER</div>
                  <div><strong>Surgical:</strong> Pre/post-operative care</div>
                  <div><strong>Psychiatric:</strong> Mental health patient beds</div>
                  <div><strong>Isolation:</strong> Infection control beds</div>
                </div>
              </div>

              {/* Status Guidelines */}
              <div className="bg-[#1a1a1a] rounded-lg p-4 border border-gray-600">
                <h4 className="text-sm font-medium text-green-400 mb-2">📊 Status Management</h4>
                <div className="text-xs text-gray-400 space-y-1">
                  <div><strong>Available:</strong> Ready for patient assignment</div>
                  <div><strong>Occupied:</strong> Currently has a patient</div>
                  <div><strong>Reserved:</strong> Held for incoming patient</div>
                  <div><strong>Maintenance:</strong> Under repair or inspection</div>
                  <div><strong>Cleaning:</strong> Being sanitized between patients</div>
                  <div><strong>Out of Service:</strong> Temporarily unavailable</div>
                </div>
              </div>

              {/* Best Practices */}
              <div className="bg-[#1a1a1a] rounded-lg p-4 border border-gray-600">
                <h4 className="text-sm font-medium text-yellow-400 mb-2">⭐ Best Practices</h4>
                <ul className="text-xs text-gray-400 space-y-1">
                  <li>• Use clear, sequential bed numbering</li>
                  <li>• Match bed type to room type</li>
                  <li>• Consider department-specific needs</li>
                  <li>• Plan for emergency access</li>
                  <li>• Maintain proper bed-to-room ratios</li>
                  <li>• Track maintenance schedules</li>
                </ul>
              </div>

              {/* Room Integration Info */}
              <div className="bg-[#1a1a1a] rounded-lg p-4 border border-gray-600">
                <h4 className="text-sm font-medium text-purple-400 mb-2">🏥 Room Integration</h4>
                <div className="text-xs text-gray-400 space-y-1">
                  <div>• Beds are assigned to specific rooms</div>
                  <div>• Room capacity determines max beds</div>
                  <div>• Consider room type compatibility</div>
                  <div>• Floor location affects service delivery</div>
                  <div>• Department assignment impacts staffing</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="border-t border-gray-700 px-6 py-4 flex justify-end space-x-3">
          <button 
            onClick={handleClose} 
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
                <span>Creating Bed...</span>
              </>
            ) : (
              <>
                <CheckCircle className="w-4 h-4" />
                <span>Create Bed</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default BedCreationForm;
