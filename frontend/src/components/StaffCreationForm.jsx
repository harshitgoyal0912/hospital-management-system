import React, { useState, useEffect } from 'react';
import { CheckCircle, X } from 'lucide-react';

const StaffCreationForm = ({ 
  isOpen, 
  onClose, 
  onSubmit, 
  isSubmitting = false,
  aiMcpServiceRef,
  userOptions = [],
  departmentOptions = [],
  loadingDropdowns = false
}) => {
  const [formData, setFormData] = useState({
    user_id: '',
    employee_id: '',
    department_id: '',
    position: '',
    specialization: '',
    license_number: '',
    hire_date: '',
    salary: '',
    shift_pattern: '',
    status: 'active'
  });

  // Reset form when modal opens
  useEffect(() => {
    if (isOpen) {
      setFormData({
        user_id: '',
        employee_id: '',
        department_id: '',
        position: '',
        specialization: '',
        license_number: '',
        hire_date: '',
        salary: '',
        shift_pattern: '',
        status: 'active'
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
    const requiredFields = ['user_id', 'employee_id', 'position', 'department_id'];
    const missingFields = requiredFields.filter(field => !formData[field].trim());

    if (missingFields.length > 0) {
      alert(`Please fill in the following required fields: ${missingFields.join(', ')}`);
      return;
    }

    try {
      // Call the MCP tool directly to create the staff
      const response = await aiMcpServiceRef.current.callToolDirectly('create_staff', {
        user_id: formData.user_id,
        employee_id: formData.employee_id,
        department_id: formData.department_id,
        position: formData.position,
        specialization: formData.specialization,
        license_number: formData.license_number,
        hire_date: formData.hire_date,
        salary: formData.salary ? parseFloat(formData.salary) : undefined,
        shift_pattern: formData.shift_pattern,
        status: formData.status
      });

      // Debug logging
      console.log('Staff creation response:', JSON.stringify(response, null, 2));

      if (response && response.success) {
        // Call the parent's onSubmit callback with the response
        onSubmit(response);
        
        // Reset form
        setFormData({
          user_id: '',
          employee_id: '',
          department_id: '',
          position: '',
          specialization: '',
          license_number: '',
          hire_date: '',
          salary: '',
          shift_pattern: '',
          status: 'active'
        });
      } else {
        // Handle error
        const errorMessage = response?.message || 'Failed to create staff member';
        alert(`Error creating staff member: ${errorMessage}`);
      }
    } catch (error) {
      console.error('Error creating staff:', error);
      alert(`Error creating staff member: ${error.message}`);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-2 sm:p-4">
      <div className="bg-gray-900 rounded-lg w-full max-w-4xl max-h-[95vh] sm:max-h-[90vh] overflow-y-auto mx-2 sm:mx-0">
        {/* Header */}
        <div className="border-b border-gray-700 px-4 sm:px-6 py-3 sm:py-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg sm:text-xl font-semibold text-white">Staff Creation Form</h2>
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
            {/* Left Column */}
            <div className="space-y-4">
              <div>
                <h3 className="text-lg font-medium text-white mb-4">Basic Information</h3>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  Select User <span className="text-red-400">*</span>
                </label>
                <select
                  value={formData.user_id}
                  onChange={(e) => handleFormChange('user_id', e.target.value)}
                  className="w-full px-3 py-3 sm:py-2 bg-gray-800 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-base sm:text-sm"
                  disabled={loadingDropdowns}
                >
                  <option value="">
                    {loadingDropdowns ? 'Loading users...' : 'Select a user'}
                  </option>
                  {Array.isArray(userOptions) ? userOptions.map(user => (
                    <option key={user.id} value={user.id}>
                      {user.first_name} {user.last_name} ({user.username}) - {user.role}
                    </option>
                  )) : []}
                </select>
                <p className="text-xs text-gray-400 mt-1">Choose which user this staff record belongs to</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  Employee ID <span className="text-red-400">*</span>
                </label>
                <input
                  type="text"
                  value={formData.employee_id}
                  onChange={(e) => handleFormChange('employee_id', e.target.value)}
                  className="w-full px-3 py-2 bg-gray-800 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Employee ID (e.g., EMP001)"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  Select Department <span className="text-red-400">*</span>
                </label>
                <select
                  value={formData.department_id}
                  onChange={(e) => handleFormChange('department_id', e.target.value)}
                  className="w-full px-3 py-3 sm:py-2 bg-gray-800 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-base sm:text-sm"
                >
                  <option value="">Select a department</option>
                  {Array.isArray(departmentOptions) ? departmentOptions.map(dept => (
                    <option key={dept.id} value={dept.id}>
                      {dept.name} (Floor {dept.floor_number || 'N/A'})
                    </option>
                  )) : []}
                </select>
                <p className="text-xs text-gray-400 mt-1">Choose which department this staff member works in</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  Position <span className="text-red-400">*</span>
                </label>
                <select
                  value={formData.position}
                  onChange={(e) => handleFormChange('position', e.target.value)}
                  className="w-full px-3 py-2 bg-gray-800 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="">Select position</option>
                  <option value="Doctor">Doctor</option>
                  <option value="Nurse">Nurse</option>
                  <option value="Physician Assistant">Physician Assistant</option>
                  <option value="Medical Technician">Medical Technician</option>
                  <option value="Radiologist">Radiologist</option>
                  <option value="Pharmacist">Pharmacist</option>
                  <option value="Lab Technician">Lab Technician</option>
                  <option value="Receptionist">Receptionist</option>
                  <option value="Administrator">Administrator</option>
                  <option value="Other">Other</option>
                </select>
              </div>
            </div>

            {/* Right Column */}
            <div className="space-y-4">
              <div>
                <h3 className="text-lg font-medium text-white mb-4">Professional Details</h3>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">Specialization</label>
                <input
                  type="text"
                  value={formData.specialization}
                  onChange={(e) => handleFormChange('specialization', e.target.value)}
                  className="w-full px-3 py-2 bg-gray-800 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="e.g., Cardiology, Emergency Medicine"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">License Number</label>
                <input
                  type="text"
                  value={formData.license_number}
                  onChange={(e) => handleFormChange('license_number', e.target.value)}
                  className="w-full px-3 py-2 bg-gray-800 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Professional license number"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">Hire Date</label>
                <input
                  type="date"
                  value={formData.hire_date}
                  onChange={(e) => handleFormChange('hire_date', e.target.value)}
                  className="w-full px-3 py-2 bg-gray-800 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">Salary</label>
                <input
                  type="number"
                  value={formData.salary}
                  onChange={(e) => handleFormChange('salary', e.target.value)}
                  className="w-full px-3 py-2 bg-gray-800 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Annual salary"
                  min="0"
                  step="1000"
                />
              </div>
            </div>
          </div>

          {/* Work Schedule Section */}
          <div className="mt-6">
            <h3 className="text-lg font-medium text-white mb-4">Work Schedule & Status</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">Shift Pattern</label>
                <select
                  value={formData.shift_pattern}
                  onChange={(e) => handleFormChange('shift_pattern', e.target.value)}
                  className="w-full px-3 py-2 bg-gray-800 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="">Select shift pattern</option>
                  <option value="day">Day Shift</option>
                  <option value="night">Night Shift</option>
                  <option value="rotating">Rotating Shifts</option>
                  <option value="on_call">On Call</option>
                  <option value="flexible">Flexible</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">Status</label>
                <select
                  value={formData.status}
                  onChange={(e) => handleFormChange('status', e.target.value)}
                  className="w-full px-3 py-2 bg-gray-800 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="active">Active</option>
                  <option value="inactive">Inactive</option>
                  <option value="on_leave">On Leave</option>
                  <option value="suspended">Suspended</option>
                </select>
              </div>
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
                <span>Creating Staff...</span>
              </>
            ) : (
              <>
                <CheckCircle className="w-4 h-4" />
                <span>Create Staff Member</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default StaffCreationForm;
