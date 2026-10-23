import React, { useState } from 'react';
import { CheckCircle, X, Package, Tag, Lightbulb, BookOpen, ChevronRight, AlertCircle } from 'lucide-react';

const SupplyCategoryCreationForm = ({ 
  isOpen, 
  onClose, 
  onCategoryCreated,
  aiMcpServiceRef 
}) => {
  const [formData, setFormData] = useState({
    name: '',
    description: ''
  });
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleInputChange = (field, value) => {
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

    setIsSubmitting(true);

    try {
      const response = await aiMcpServiceRef.current.callToolDirectly(
        'create_supply_category',
        formData
      );

      if (response && response.success) {
        // Reset form
        setFormData({ name: '', description: '' });
        
        // Call the callback to handle success and close form
        if (onCategoryCreated) {
          onCategoryCreated(formData.name);
        }
      } else {
        alert(`Failed to create supply category: ${response.message || 'Unknown error'}`);
      }
    } catch (error) {
      alert(`Error creating supply category: ${error.message}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleClose = () => {
    setFormData({ name: '', description: '' });
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-[#2a2a2a] rounded-lg w-full max-w-5xl max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="border-b border-gray-700 px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <Package className="w-6 h-6 text-purple-400" />
              <h2 className="text-xl font-semibold text-white">Supply Category Creation</h2>
            </div>
            <button 
              onClick={handleClose} 
              className="text-gray-400 hover:text-white transition-colors"
              disabled={isSubmitting}
            >
              <X className="w-6 h-6" />
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="p-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            
            {/* Left Column - Category Information */}
            <div className="space-y-6">
              <div className="flex items-center space-x-2 mb-4">
                <Tag className="w-5 h-5 text-purple-400" />
                <h3 className="text-lg font-semibold text-white">Category Information</h3>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Category Name *
                  </label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => handleInputChange('name', e.target.value)}
                    className="w-full px-4 py-3 bg-[#1a1a1a] border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-purple-500 focus:ring-1 focus:ring-purple-500"
                    placeholder="e.g., Medications, Surgical Supplies, Cleaning Supplies"
                    disabled={isSubmitting}
                  />
                  <p className="text-xs text-gray-400 mt-1">
                    Use clear, descriptive names that are easy to understand
                  </p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Description (Optional)
                  </label>
                  <textarea
                    value={formData.description}
                    onChange={(e) => handleInputChange('description', e.target.value)}
                    className="w-full px-4 py-3 bg-[#1a1a1a] border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-purple-500 focus:ring-1 focus:ring-purple-500"
                    placeholder="Brief description of this supply category and what types of supplies it includes..."
                    rows="4"
                    disabled={isSubmitting}
                  />
                  <p className="text-xs text-gray-400 mt-1">
                    Provide context about what supplies belong in this category
                  </p>
                </div>
              </div>
            </div>

            {/* Right Column - Guidelines & Examples */}
            <div className="space-y-6">
              <div className="flex items-center space-x-2 mb-4">
                <BookOpen className="w-5 h-5 text-purple-400" />
                <h3 className="text-lg font-semibold text-white">Guidelines & Examples</h3>
              </div>

              <div className="space-y-6">
                {/* Common Supply Categories */}
                <div className="bg-[#1a1a1a] rounded-lg p-4">
                  <div className="flex items-center space-x-2 mb-3">
                    <Package className="w-4 h-4 text-purple-400" />
                    <h4 className="font-medium text-white">Common Supply Categories</h4>
                  </div>
                  <div className="space-y-2 text-sm text-gray-300">
                    <div className="flex items-center space-x-2">
                      <ChevronRight className="w-3 h-3 text-purple-400" />
                      <span><strong>Medications:</strong> Prescription drugs, over-the-counter medicines</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <ChevronRight className="w-3 h-3 text-purple-400" />
                      <span><strong>Surgical Supplies:</strong> Scalpels, sutures, surgical instruments</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <ChevronRight className="w-3 h-3 text-purple-400" />
                      <span><strong>Disposables:</strong> Gloves, masks, syringes, gauze</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <ChevronRight className="w-3 h-3 text-purple-400" />
                      <span><strong>Cleaning Supplies:</strong> Disinfectants, wipes, sanitizers</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <ChevronRight className="w-3 h-3 text-purple-400" />
                      <span><strong>Office Supplies:</strong> Forms, paperwork, administrative materials</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <ChevronRight className="w-3 h-3 text-purple-400" />
                      <span><strong>PPE:</strong> Personal protective equipment, safety gear</span>
                    </div>
                  </div>
                </div>

                {/* Category Naming Best Practices */}
                <div className="bg-[#1a1a1a] rounded-lg p-4">
                  <div className="flex items-center space-x-2 mb-3">
                    <Lightbulb className="w-4 h-4 text-yellow-400" />
                    <h4 className="font-medium text-white">Naming Best Practices</h4>
                  </div>
                  <div className="space-y-2 text-sm text-gray-300">
                    <div className="flex items-center space-x-2">
                      <ChevronRight className="w-3 h-3 text-yellow-400" />
                      <span>Use specific, descriptive names</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <ChevronRight className="w-3 h-3 text-yellow-400" />
                      <span>Avoid overly broad categories</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <ChevronRight className="w-3 h-3 text-yellow-400" />
                      <span>Consider departmental needs</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <ChevronRight className="w-3 h-3 text-yellow-400" />
                      <span>Think about inventory organization</span>
                    </div>
                  </div>
                </div>

                {/* Organization Tips */}
                <div className="bg-[#1a1a1a] rounded-lg p-4">
                  <div className="flex items-center space-x-2 mb-3">
                    <AlertCircle className="w-4 h-4 text-blue-400" />
                    <h4 className="font-medium text-white">Organization Tips</h4>
                  </div>
                  <div className="space-y-2 text-sm text-gray-300">
                    <div className="flex items-center space-x-2">
                      <ChevronRight className="w-3 h-3 text-blue-400" />
                      <span>Group similar supplies together</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <ChevronRight className="w-3 h-3 text-blue-400" />
                      <span>Consider usage frequency</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <ChevronRight className="w-3 h-3 text-blue-400" />
                      <span>Plan for future scalability</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <ChevronRight className="w-3 h-3 text-blue-400" />
                      <span>Align with hospital departments</span>
                    </div>
                  </div>
                </div>

                {/* Category Benefits */}
                <div className="bg-gradient-to-r from-purple-900/20 to-blue-900/20 rounded-lg p-4 border border-purple-500/20">
                  <h4 className="font-medium text-white mb-2">Why Supply Categories Matter</h4>
                  <p className="text-sm text-gray-300">
                    Well-organized supply categories improve inventory management, 
                    reduce waste, streamline ordering processes, and help staff 
                    quickly locate needed supplies during critical situations.
                  </p>
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
            disabled={isSubmitting || !formData.name.trim()}
            className="px-6 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
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

export default SupplyCategoryCreationForm;
