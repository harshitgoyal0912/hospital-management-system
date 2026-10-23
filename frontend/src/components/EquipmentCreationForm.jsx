import React, { useState, useEffect } from 'react';
import { CheckCircle, X } from 'lucide-react';

const EquipmentCreationForm = ({ 
  isOpen, 
  onClose, 
  onSubmit, 
  isSubmitting = false,
  aiMcpServiceRef,
  departmentOptions = [],
  equipmentCategoryOptions = [],
  loadingDropdowns = false
}) => {
  const [formData, setFormData] = useState({
    equipment_id: '',
    name: '',
    category_id: '',
    model: '',
    manufacturer: '',
    serial_number: '',
    purchase_date: '',
    warranty_expiry: '',
    location: '',
    department_id: '',
    status: 'operational',
    last_maintenance: '',
    next_maintenance: '',
    cost: '',
    notes: ''
  });

  // Reset form when modal opens
  useEffect(() => {
    if (isOpen) {
      setFormData({
        equipment_id: '',
        name: '',
        category_id: '',
        model: '',
        manufacturer: '',
        serial_number: '',
        purchase_date: '',
        warranty_expiry: '',
        location: '',
        department_id: '',
        status: 'operational',
        last_maintenance: '',
        next_maintenance: '',
        cost: '',
        notes: ''
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
    const requiredFields = ['equipment_id', 'name', 'category_id'];
    const missingFields = requiredFields.filter(field => !formData[field].trim());

    if (missingFields.length > 0) {
      alert(`Please fill in the following required fields: ${missingFields.join(', ')}`);
      return;
    }

    try {
      // Call the MCP tool directly to create the equipment
      const response = await aiMcpServiceRef.current.callToolDirectly('create_equipment', {
        equipment_id: formData.equipment_id,
        name: formData.name,
        category_id: formData.category_id,
        model: formData.model,
        manufacturer: formData.manufacturer,
        serial_number: formData.serial_number,
        purchase_date: formData.purchase_date,
        warranty_expiry: formData.warranty_expiry,
        location: formData.location,
        department_id: formData.department_id,
        status: formData.status,
        last_maintenance: formData.last_maintenance,
        next_maintenance: formData.next_maintenance,
        cost: formData.cost ? parseFloat(formData.cost) : undefined,
        notes: formData.notes
      });

      // Debug logging
      console.log('Equipment creation response:', JSON.stringify(response, null, 2));

      if (response && response.success) {
        // Call the parent's onSubmit callback with the response
        onSubmit(response);
        
        // Reset form
        setFormData({
          equipment_id: '',
          name: '',
          category_id: '',
          model: '',
          manufacturer: '',
          serial_number: '',
          purchase_date: '',
          warranty_expiry: '',
          location: '',
          department_id: '',
          status: 'operational',
          last_maintenance: '',
          next_maintenance: '',
          cost: '',
          notes: ''
        });
      } else {
        // Handle error
        const errorMessage = response?.message || 'Failed to create equipment';
        alert(`Error creating equipment: ${errorMessage}`);
      }
    } catch (error) {
      console.error('Error creating equipment:', error);
      alert(`Error creating equipment: ${error.message}`);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-2 sm:p-4">
      <div className="bg-gray-900 rounded-lg w-full max-w-5xl max-h-[95vh] sm:max-h-[90vh] overflow-y-auto mx-2 sm:mx-0">
        {/* Header */}
        <div className="border-b border-gray-700 px-4 sm:px-6 py-3 sm:py-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg sm:text-xl font-semibold text-white">Equipment Creation Form</h2>
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
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Column 1 - Basic Information */}
            <div className="space-y-4">
              <div>
                <h3 className="text-lg font-medium text-white mb-4">Basic Information</h3>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  Equipment ID <span className="text-red-400">*</span>
                </label>
                <input
                  type="text"
                  value={formData.equipment_id}
                  onChange={(e) => handleFormChange('equipment_id', e.target.value)}
                  className="w-full px-3 py-2 bg-gray-800 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="e.g., EQ001, XR-001"
                />
                <p className="text-xs text-gray-400 mt-1">Unique identifier for the equipment</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  Equipment Name <span className="text-red-400">*</span>
                </label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => handleFormChange('name', e.target.value)}
                  className="w-full px-3 py-2 bg-gray-800 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="e.g., X-Ray Machine, MRI Scanner"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  Equipment Category <span className="text-red-400">*</span>
                </label>
                <select
                  value={formData.category_id}
                  onChange={(e) => handleFormChange('category_id', e.target.value)}
                  className="w-full px-3 py-3 sm:py-2 bg-gray-800 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-base sm:text-sm"
                  disabled={loadingDropdowns}
                >
                  <option value="">
                    {loadingDropdowns ? 'Loading categories...' : 'Select a category'}
                  </option>
                  {Array.isArray(equipmentCategoryOptions) ? equipmentCategoryOptions.map(category => (
                    <option key={category.id} value={category.id}>
                      {category.name}
                    </option>
                  )) : []}
                </select>
                <p className="text-xs text-gray-400 mt-1">Choose the equipment category type</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">Model</label>
                <input
                  type="text"
                  value={formData.model}
                  onChange={(e) => handleFormChange('model', e.target.value)}
                  className="w-full px-3 py-2 bg-gray-800 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Equipment model number"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">Manufacturer</label>
                <input
                  type="text"
                  value={formData.manufacturer}
                  onChange={(e) => handleFormChange('manufacturer', e.target.value)}
                  className="w-full px-3 py-2 bg-gray-800 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Manufacturer name"
                />
              </div>
            </div>

            {/* Column 2 - Technical Details */}
            <div className="space-y-4">
              <div>
                <h3 className="text-lg font-medium text-white mb-4">Technical Details</h3>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">Serial Number</label>
                <input
                  type="text"
                  value={formData.serial_number}
                  onChange={(e) => handleFormChange('serial_number', e.target.value)}
                  className="w-full px-3 py-2 bg-gray-800 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Equipment serial number"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">Purchase Date</label>
                <input
                  type="date"
                  value={formData.purchase_date}
                  onChange={(e) => handleFormChange('purchase_date', e.target.value)}
                  className="w-full px-3 py-2 bg-gray-800 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">Warranty Expiry</label>
                <input
                  type="date"
                  value={formData.warranty_expiry}
                  onChange={(e) => handleFormChange('warranty_expiry', e.target.value)}
                  className="w-full px-3 py-2 bg-gray-800 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">Cost</label>
                <input
                  type="number"
                  value={formData.cost}
                  onChange={(e) => handleFormChange('cost', e.target.value)}
                  className="w-full px-3 py-2 bg-gray-800 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Purchase cost"
                  min="0"
                  step="0.01"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">Status</label>
                <select
                  value={formData.status}
                  onChange={(e) => handleFormChange('status', e.target.value)}
                  className="w-full px-3 py-2 bg-gray-800 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="operational">Operational</option>
                  <option value="maintenance">Under Maintenance</option>
                  <option value="out_of_order">Out of Order</option>
                  <option value="retired">Retired</option>
                </select>
              </div>
            </div>

            {/* Column 3 - Location & Maintenance */}
            <div className="space-y-4">
              <div>
                <h3 className="text-lg font-medium text-white mb-4">Location & Maintenance</h3>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">Location</label>
                <input
                  type="text"
                  value={formData.location}
                  onChange={(e) => handleFormChange('location', e.target.value)}
                  className="w-full px-3 py-2 bg-gray-800 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="e.g., Room 101, ICU Wing"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">Assigned Department</label>
                <select
                  value={formData.department_id}
                  onChange={(e) => handleFormChange('department_id', e.target.value)}
                  className="w-full px-3 py-3 sm:py-2 bg-gray-800 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-base sm:text-sm"
                  disabled={loadingDropdowns}
                >
                  <option value="">
                    {loadingDropdowns ? 'Loading departments...' : 'Select department (optional)'}
                  </option>
                  {Array.isArray(departmentOptions) ? departmentOptions.map(dept => (
                    <option key={dept.id} value={dept.id}>
                      {dept.name} (Floor {dept.floor_number || 'N/A'})
                    </option>
                  )) : []}
                </select>
                <p className="text-xs text-gray-400 mt-1">Department that will primarily use this equipment</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">Last Maintenance</label>
                <input
                  type="date"
                  value={formData.last_maintenance}
                  onChange={(e) => handleFormChange('last_maintenance', e.target.value)}
                  className="w-full px-3 py-2 bg-gray-800 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">Next Maintenance</label>
                <input
                  type="date"
                  value={formData.next_maintenance}
                  onChange={(e) => handleFormChange('next_maintenance', e.target.value)}
                  className="w-full px-3 py-2 bg-gray-800 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">Notes</label>
                <textarea
                  value={formData.notes}
                  onChange={(e) => handleFormChange('notes', e.target.value)}
                  className="w-full px-3 py-2 bg-gray-800 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  rows="3"
                  placeholder="Additional notes and specifications"
                />
              </div>
            </div>
          </div>

          {/* Information Panel */}
          <div className="mt-6 p-4 bg-green-900/20 rounded-lg border border-green-700/30">
            <h3 className="text-sm font-medium text-green-300 mb-2">🔧 Equipment Management Guidelines</h3>
            <div className="text-xs text-green-200/80 space-y-1">
              <p>• Equipment ID should follow hospital naming conventions (e.g., XR-001, MRI-02)</p>
              <p>• Regular maintenance scheduling helps ensure optimal performance and safety</p>
              <p>• Department assignment aids in resource allocation and usage tracking</p>
              <p>• Warranty tracking helps with service planning and cost management</p>
              <p>• Accurate status updates enable efficient equipment utilization</p>
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
                <span>Creating Equipment...</span>
              </>
            ) : (
              <>
                <CheckCircle className="w-4 h-4" />
                <span>Create Equipment</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default EquipmentCreationForm;
