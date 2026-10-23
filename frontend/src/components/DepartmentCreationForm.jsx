import React, { useState, useEffect } from 'react';
import { CheckCircle, X } from 'lucide-react';

const DepartmentCreationForm = ({ 
  isOpen, 
  onClose, 
  onSubmit, 
  isSubmitting = false,
  aiMcpServiceRef,
  userOptions = [],
  loadingDropdowns = false
}) => {
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    head_doctor_id: '',
    floor_number: '',
    phone: '',
    email: ''
  });

  // Reset form when modal opens
  useEffect(() => {
    if (isOpen) {
      setFormData({
        name: '',
        description: '',
        head_doctor_id: '',
        floor_number: '',
        phone: '',
        email: ''
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
    const requiredFields = ['name'];
    const missingFields = requiredFields.filter(field => !formData[field].trim());

    if (missingFields.length > 0) {
      alert(`Please fill in the following required fields: ${missingFields.join(', ')}`);
      return;
    }

    try {
      // Call the MCP tool directly to create the department
      const response = await aiMcpServiceRef.current.callToolDirectly('create_department', {
        name: formData.name,
        description: formData.description,
        head_doctor_id: formData.head_doctor_id,
        floor_number: formData.floor_number ? parseInt(formData.floor_number) : undefined,
        phone: formData.phone,
        email: formData.email
      });

      // Debug logging
      console.log('Department creation response:', JSON.stringify(response, null, 2));

      if (response && response.success) {
        // Call the parent's onSubmit callback with the response
        onSubmit(response);
        
        // Reset form
        setFormData({
          name: '',
          description: '',
          head_doctor_id: '',
          floor_number: '',
          phone: '',
          email: ''
        });
      } else {
        // Handle error
        const errorMessage = response?.message || 'Failed to create department';
        alert(`Error creating department: ${errorMessage}`);
      }
    } catch (error) {
      console.error('Error creating department:', error);
      alert(`Error creating department: ${error.message}`);
    }
  };

  if (!isOpen) return null;

  // Filter users to only show doctors and admins for head doctor selection
  const doctorOptions = Array.isArray(userOptions) 
    ? userOptions.filter(user => user.role === 'doctor' || user.role === 'admin')
    : [];

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-2 sm:p-4">
      <div className="bg-gray-900 rounded-lg w-full max-w-4xl max-h-[95vh] sm:max-h-[90vh] overflow-y-auto mx-2 sm:mx-0">
        {/* Header */}
        <div className="border-b border-gray-700 px-4 sm:px-6 py-3 sm:py-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg sm:text-xl font-semibold text-white">Department Creation Form</h2>
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
            {/* Left Column - Department Information */}
            <div className="space-y-4">
              <div>
                <h3 className="text-lg font-medium text-white mb-4">Department Information</h3>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  Department Name <span className="text-red-400">*</span>
                </label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => handleFormChange('name', e.target.value)}
                  className="w-full px-3 py-2 bg-gray-800 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="e.g., Cardiology, Emergency, Pediatrics"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">Description</label>
                <textarea
                  value={formData.description}
                  onChange={(e) => handleFormChange('description', e.target.value)}
                  className="w-full px-3 py-2 bg-gray-800 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  rows="4"
                  placeholder="Department description, services offered, and specializations"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">Floor Number</label>
                <input
                  type="number"
                  value={formData.floor_number}
                  onChange={(e) => handleFormChange('floor_number', e.target.value)}
                  className="w-full px-3 py-2 bg-gray-800 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="e.g., 3"
                  min="1"
                  max="50"
                />
                <p className="text-xs text-gray-400 mt-1">Which floor is this department located on?</p>
              </div>
            </div>

            {/* Right Column - Management & Contact */}
            <div className="space-y-4">
              <div>
                <h3 className="text-lg font-medium text-white mb-4">Management & Contact</h3>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">Head Doctor</label>
                <select
                  value={formData.head_doctor_id}
                  onChange={(e) => handleFormChange('head_doctor_id', e.target.value)}
                  className="w-full px-3 py-3 sm:py-2 bg-gray-800 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-base sm:text-sm"
                  disabled={loadingDropdowns}
                >
                  <option value="">
                    {loadingDropdowns ? 'Loading doctors...' : 'Select head doctor (optional)'}
                  </option>
                  {doctorOptions.map(user => (
                    <option key={user.id} value={user.id}>
                      {user.first_name} {user.last_name} ({user.username}) - {user.role}
                    </option>
                  ))}
                </select>
                <p className="text-xs text-gray-400 mt-1">Choose who will head this department</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">Phone Number</label>
                <input
                  type="tel"
                  value={formData.phone}
                  onChange={(e) => handleFormChange('phone', e.target.value)}
                  className="w-full px-3 py-2 bg-gray-800 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Department direct phone number"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">Email Address</label>
                <input
                  type="email"
                  value={formData.email}
                  onChange={(e) => handleFormChange('email', e.target.value)}
                  className="w-full px-3 py-2 bg-gray-800 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="department@hospital.com"
                />
              </div>
            </div>
          </div>

          {/* Information Panel */}
          <div className="mt-6 p-4 bg-gray-800 rounded-lg border border-gray-700">
            <h3 className="text-sm font-medium text-gray-300 mb-2">📝 Department Setup Guidelines</h3>
            <div className="text-xs text-gray-400 space-y-1">
              <p>• Department name should be unique and descriptive</p>
              <p>• Head doctor assignment helps with department management</p>
              <p>• Floor number aids in navigation and logistics</p>
              <p>• Contact information enables direct communication</p>
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
                <span>Creating Department...</span>
              </>
            ) : (
              <>
                <CheckCircle className="w-4 h-4" />
                <span>Create Department</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default DepartmentCreationForm;
