import React, { useState } from 'react';
import { X, CheckCircle, Package } from 'lucide-react';

const SupplyCreationForm = ({
  isOpen,
  onClose,
  onSubmit,
  isSubmitting,
  aiMcpServiceRef,
  supplyCategoryOptions = [],
  loadingDropdowns
}) => {
  const [formData, setFormData] = useState({
    item_code: '',
    name: '',
    category_id: '',
    description: '',
    unit_of_measure: '',
    minimum_stock_level: '',
    maximum_stock_level: '',
    current_stock: '',
    unit_cost: '',
    supplier: '',
    expiry_date: '',
    location: ''
  });

  const handleFormChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleSubmit = async () => {
    const requiredFields = ['item_code', 'name', 'category_id', 'unit_of_measure'];
    const missingFields = requiredFields.filter(field => !formData[field].trim());
    
    if (missingFields.length > 0) {
      alert(`Please fill in the following required fields: ${missingFields.join(', ')}`);
      return;
    }

    try {
      const response = await aiMcpServiceRef.current.callToolDirectly('create_supply', {
        item_code: formData.item_code,
        name: formData.name,
        category_id: formData.category_id,
        description: formData.description,
        unit_of_measure: formData.unit_of_measure,
        minimum_stock_level: formData.minimum_stock_level ? parseInt(formData.minimum_stock_level) : undefined,
        maximum_stock_level: formData.maximum_stock_level ? parseInt(formData.maximum_stock_level) : undefined,
        current_stock: formData.current_stock ? parseInt(formData.current_stock) : undefined,
        unit_cost: formData.unit_cost ? parseFloat(formData.unit_cost) : undefined,
        supplier: formData.supplier,
        expiry_date: formData.expiry_date,
        location: formData.location
      });

      // Reset form
      setFormData({
        item_code: '',
        name: '',
        category_id: '',
        description: '',
        unit_of_measure: '',
        minimum_stock_level: '',
        maximum_stock_level: '',
        current_stock: '',
        unit_cost: '',
        supplier: '',
        expiry_date: '',
        location: ''
      });

      // Call parent submit handler
      if (onSubmit) {
        onSubmit(response);
      }
    } catch (error) {
      console.error('Error creating supply:', error);
      alert('Failed to create supply. Please try again.');
    }
  };

  const handleClose = () => {
    // Reset form when closing
    setFormData({
      item_code: '',
      name: '',
      category_id: '',
      description: '',
      unit_of_measure: '',
      minimum_stock_level: '',
      maximum_stock_level: '',
      current_stock: '',
      unit_cost: '',
      supplier: '',
      expiry_date: '',
      location: ''
    });
    
    if (onClose) {
      onClose();
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-[#2a2a2a] rounded-lg w-full max-w-5xl max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="border-b border-gray-700 px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <Package className="w-6 h-6 text-blue-400" />
              <h2 className="text-xl font-semibold text-white">Supply Creation Form</h2>
            </div>
            <button onClick={handleClose} className="text-gray-400 hover:text-white">
              <X className="w-6 h-6" />
            </button>
          </div>
        </div>

        {/* Form Content */}
        <div className="px-6 py-6">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            
            {/* Basic Information */}
            <div className="space-y-4">
              <div className="border-b border-gray-600 pb-2 mb-4">
                <h3 className="text-lg font-medium text-white flex items-center">
                  <Package className="w-5 h-5 mr-2 text-blue-400" />
                  Basic Information
                </h3>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  Item Code *
                  <span className="text-xs text-gray-400 ml-1">(e.g., SUP001, MED001)</span>
                </label>
                <input
                  type="text"
                  value={formData.item_code}
                  onChange={(e) => handleFormChange('item_code', e.target.value)}
                  className="w-full px-3 py-2 bg-[#1a1a1a] border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-blue-500"
                  placeholder="SUP001"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">Supply Name *</label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => handleFormChange('name', e.target.value)}
                  className="w-full px-3 py-2 bg-[#1a1a1a] border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-blue-500"
                  placeholder="e.g., Surgical Gloves"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">Supply Category *</label>
                <select
                  value={formData.category_id}
                  onChange={(e) => handleFormChange('category_id', e.target.value)}
                  className="w-full px-3 py-2 bg-[#1a1a1a] border border-gray-600 rounded-lg text-white focus:outline-none focus:border-blue-500"
                  disabled={loadingDropdowns}
                >
                  <option value="">Select a category</option>
                  {Array.isArray(supplyCategoryOptions) ? supplyCategoryOptions.map(category => (
                    <option key={category.id} value={category.id}>
                      {category.name}
                    </option>
                  )) : []}
                </select>
                <p className="text-xs text-gray-400 mt-1">Choose the supply category</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">Unit of Measure *</label>
                <input
                  type="text"
                  value={formData.unit_of_measure}
                  onChange={(e) => handleFormChange('unit_of_measure', e.target.value)}
                  className="w-full px-3 py-2 bg-[#1a1a1a] border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-blue-500"
                  placeholder="e.g., pieces, boxes, liters"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">Description</label>
                <textarea
                  value={formData.description}
                  onChange={(e) => handleFormChange('description', e.target.value)}
                  className="w-full px-3 py-2 bg-[#1a1a1a] border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-blue-500"
                  placeholder="Supply description"
                  rows="3"
                />
              </div>
            </div>

            {/* Stock Management */}
            <div className="space-y-4">
              <div className="border-b border-gray-600 pb-2 mb-4">
                <h3 className="text-lg font-medium text-white flex items-center">
                  📊 Stock Management
                </h3>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">Current Stock</label>
                <input
                  type="number"
                  value={formData.current_stock}
                  onChange={(e) => handleFormChange('current_stock', e.target.value)}
                  className="w-full px-3 py-2 bg-[#1a1a1a] border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-blue-500"
                  placeholder="Current stock quantity"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">Minimum Stock Level</label>
                <input
                  type="number"
                  value={formData.minimum_stock_level}
                  onChange={(e) => handleFormChange('minimum_stock_level', e.target.value)}
                  className="w-full px-3 py-2 bg-[#1a1a1a] border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-blue-500"
                  placeholder="Minimum stock level"
                />
                <p className="text-xs text-gray-400 mt-1">Alert when stock falls below this level</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">Maximum Stock Level</label>
                <input
                  type="number"
                  value={formData.maximum_stock_level}
                  onChange={(e) => handleFormChange('maximum_stock_level', e.target.value)}
                  className="w-full px-3 py-2 bg-[#1a1a1a] border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-blue-500"
                  placeholder="Maximum stock level"
                />
                <p className="text-xs text-gray-400 mt-1">Maximum inventory capacity</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">Unit Cost</label>
                <input
                  type="number"
                  step="0.01"
                  value={formData.unit_cost}
                  onChange={(e) => handleFormChange('unit_cost', e.target.value)}
                  className="w-full px-3 py-2 bg-[#1a1a1a] border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-blue-500"
                  placeholder="Cost per unit"
                />
                <p className="text-xs text-gray-400 mt-1">Cost for budgeting and inventory valuation</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">Expiry Date</label>
                <input
                  type="date"
                  value={formData.expiry_date}
                  onChange={(e) => handleFormChange('expiry_date', e.target.value)}
                  className="w-full px-3 py-2 bg-[#1a1a1a] border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-blue-500"
                />
                <p className="text-xs text-gray-400 mt-1">For perishable items</p>
              </div>
            </div>

            {/* Supplier & Location */}
            <div className="space-y-4">
              <div className="border-b border-gray-600 pb-2 mb-4">
                <h3 className="text-lg font-medium text-white flex items-center">
                  🏢 Supplier & Location
                </h3>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">Supplier</label>
                <input
                  type="text"
                  value={formData.supplier}
                  onChange={(e) => handleFormChange('supplier', e.target.value)}
                  className="w-full px-3 py-2 bg-[#1a1a1a] border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-blue-500"
                  placeholder="Supplier name"
                />
                <p className="text-xs text-gray-400 mt-1">Primary supplier for this item</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">Storage Location</label>
                <input
                  type="text"
                  value={formData.location}
                  onChange={(e) => handleFormChange('location', e.target.value)}
                  className="w-full px-3 py-2 bg-[#1a1a1a] border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-blue-500"
                  placeholder="Storage location"
                />
                <p className="text-xs text-gray-400 mt-1">Where this supply is stored</p>
              </div>

              {/* Guidelines Section */}
              <div className="bg-[#1a1a1a] rounded-lg p-4 border border-gray-600">
                <h4 className="text-sm font-medium text-blue-400 mb-2">💡 Supply Management Guidelines</h4>
                <ul className="text-xs text-gray-400 space-y-1">
                  <li>• Use unique item codes for tracking</li>
                  <li>• Set appropriate min/max stock levels</li>
                  <li>• Monitor expiry dates for perishables</li>
                  <li>• Keep supplier information updated</li>
                  <li>• Track unit costs for budgeting</li>
                  <li>• Specify clear storage locations</li>
                </ul>
              </div>

              {/* Common Supply Categories Info */}
              <div className="bg-[#1a1a1a] rounded-lg p-4 border border-gray-600">
                <h4 className="text-sm font-medium text-green-400 mb-2">📋 Common Supply Types</h4>
                <div className="text-xs text-gray-400 space-y-1">
                  <div><strong>Medical:</strong> Gloves, syringes, bandages</div>
                  <div><strong>Surgical:</strong> Instruments, sutures, drapes</div>
                  <div><strong>Pharmacy:</strong> Medications, vaccines</div>
                  <div><strong>Office:</strong> Paper, pens, forms</div>
                  <div><strong>Cleaning:</strong> Disinfectants, supplies</div>
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
                <span>Creating Supply...</span>
              </>
            ) : (
              <>
                <CheckCircle className="w-4 h-4" />
                <span>Create Supply</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default SupplyCreationForm;
