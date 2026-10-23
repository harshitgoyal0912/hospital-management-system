import React, { useState } from 'react';
import { X, CheckCircle, Tag } from 'lucide-react';

const EquipmentCategoryCreationForm = ({
  isOpen,
  onClose,
  onSubmit,
  isSubmitting,
  aiMcpServiceRef,
  onCategoryCreated
}) => {
  const [formData, setFormData] = useState({
    name: '',
    description: ''
  });

  const handleFormChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleSubmit = async () => {
    const requiredFields = ['name'];
    const missingFields = requiredFields.filter(field => !formData[field].trim());
    
    if (missingFields.length > 0) {
      alert(`Please fill in the following required fields: ${missingFields.join(', ')}`);
      return;
    }

    try {
      const response = await aiMcpServiceRef.current.callToolDirectly(
        'create_equipment_category',
        formData
      );

      // Reset form
      setFormData({
        name: '',
        description: ''
      });

      // Call parent submit handler
      if (onSubmit) {
        onSubmit(response);
      }

      // Notify parent to reload equipment categories if provided
      if (onCategoryCreated) {
        onCategoryCreated();
      }
    } catch (error) {
      console.error('Error creating equipment category:', error);
      alert('Failed to create equipment category. Please try again.');
    }
  };

  const handleClose = () => {
    // Reset form when closing
    setFormData({
      name: '',
      description: ''
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
              <Tag className="w-6 h-6 text-blue-400" />
              <h2 className="text-xl font-semibold text-white">Equipment Category Creation</h2>
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
                  <Tag className="w-5 h-5 mr-2 text-blue-400" />
                  Category Information
                </h3>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  Category Name *
                  <span className="text-xs text-gray-400 ml-1">(descriptive and clear)</span>
                </label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => handleFormChange('name', e.target.value)}
                  className="w-full px-3 py-2 bg-[#1a1a1a] border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-blue-500"
                  placeholder="e.g., Diagnostic Equipment, Surgical Instruments"
                />
                <p className="text-xs text-gray-400 mt-1">Choose a clear, descriptive name for this equipment category</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">Description (Optional)</label>
                <textarea
                  value={formData.description}
                  onChange={(e) => handleFormChange('description', e.target.value)}
                  className="w-full px-3 py-2 bg-[#1a1a1a] border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-blue-500"
                  placeholder="Brief description of this category"
                  rows="4"
                />
                <p className="text-xs text-gray-400 mt-1">Provide additional details about what equipment belongs in this category</p>
              </div>
            </div>

            {/* Guidelines & Examples */}
            <div className="space-y-4">
              <div className="border-b border-gray-600 pb-2 mb-4">
                <h3 className="text-lg font-medium text-white flex items-center">
                  💡 Guidelines & Examples
                </h3>
              </div>

              {/* Common Equipment Categories */}
              <div className="bg-[#1a1a1a] rounded-lg p-4 border border-gray-600">
                <h4 className="text-sm font-medium text-blue-400 mb-2">🏥 Common Equipment Categories</h4>
                <div className="text-xs text-gray-400 space-y-1">
                  <div><strong>Diagnostic:</strong> X-Ray, CT Scanner, MRI, Ultrasound</div>
                  <div><strong>Surgical:</strong> Operating Tables, Surgical Lights, Instruments</div>
                  <div><strong>Monitoring:</strong> Patient Monitors, ECG Machines, Pulse Oximeters</div>
                  <div><strong>Laboratory:</strong> Microscopes, Analyzers, Centrifuges</div>
                  <div><strong>Life Support:</strong> Ventilators, Defibrillators, Oxygen Equipment</div>
                  <div><strong>Mobility:</strong> Wheelchairs, Stretchers, Hospital Beds</div>
                  <div><strong>Rehabilitation:</strong> Physical Therapy Equipment, Exercise Tools</div>
                  <div><strong>Sterilization:</strong> Autoclaves, UV Sterilizers, Washers</div>
                </div>
              </div>

              {/* Category Naming Best Practices */}
              <div className="bg-[#1a1a1a] rounded-lg p-4 border border-gray-600">
                <h4 className="text-sm font-medium text-green-400 mb-2">✅ Naming Best Practices</h4>
                <ul className="text-xs text-gray-400 space-y-1">
                  <li>• Use descriptive, professional terminology</li>
                  <li>• Avoid abbreviations or acronyms when possible</li>
                  <li>• Be specific enough to avoid confusion</li>
                  <li>• Use consistent naming conventions</li>
                  <li>• Consider future equipment additions</li>
                  <li>• Keep names concise but informative</li>
                </ul>
              </div>

              {/* Organization Tips */}
              <div className="bg-[#1a1a1a] rounded-lg p-4 border border-gray-600">
                <h4 className="text-sm font-medium text-yellow-400 mb-2">📋 Organization Tips</h4>
                <div className="text-xs text-gray-400 space-y-1">
                  <div><strong>By Function:</strong> Group by primary medical purpose</div>
                  <div><strong>By Department:</strong> Organize by hospital department usage</div>
                  <div><strong>By Mobility:</strong> Fixed vs Portable equipment</div>
                  <div><strong>By Complexity:</strong> Simple tools vs Complex systems</div>
                  <div><strong>By Maintenance:</strong> Similar service requirements</div>
                </div>
              </div>

              {/* Impact of Categories */}
              <div className="bg-[#1a1a1a] rounded-lg p-4 border border-gray-600">
                <h4 className="text-sm font-medium text-purple-400 mb-2">🎯 Category Benefits</h4>
                <div className="text-xs text-gray-400 space-y-1">
                  <div>• <strong>Organization:</strong> Easier equipment management</div>
                  <div>• <strong>Reporting:</strong> Better inventory tracking</div>
                  <div>• <strong>Maintenance:</strong> Streamlined service scheduling</div>
                  <div>• <strong>Budgeting:</strong> Cost analysis by category</div>
                  <div>• <strong>Training:</strong> Staff specialization areas</div>
                  <div>• <strong>Compliance:</strong> Regulatory requirements</div>
                </div>
              </div>

              {/* Example Descriptions */}
              <div className="bg-[#1a1a1a] rounded-lg p-4 border border-gray-600">
                <h4 className="text-sm font-medium text-orange-400 mb-2">📝 Description Examples</h4>
                <div className="text-xs text-gray-400 space-y-1">
                  <div><strong>Diagnostic Equipment:</strong> "Medical devices used for patient examination, diagnosis, and health monitoring"</div>
                  <div><strong>Surgical Instruments:</strong> "Specialized tools and devices used during surgical procedures"</div>
                  <div><strong>Patient Monitoring:</strong> "Equipment for continuous observation of patient vital signs and health parameters"</div>
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
                <span>Creating Category...</span>
              </>
            ) : (
              <>
                <CheckCircle className="w-4 h-4" />
                <span>Create Category</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default EquipmentCategoryCreationForm;
