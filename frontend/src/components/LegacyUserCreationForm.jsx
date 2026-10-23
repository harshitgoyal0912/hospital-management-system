import React, { useState } from 'react';
import { X, CheckCircle, UserPlus } from 'lucide-react';

const LegacyUserCreationForm = ({
  isOpen,
  onClose,
  onSubmit,
  isSubmitting,
  aiMcpServiceRef
}) => {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    address: '',
    phone: ''
  });

  const handleFormChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleSubmit = async () => {
    const requiredFields = ['name', 'email'];
    const missingFields = requiredFields.filter(field => !formData[field].trim());
    
    if (missingFields.length > 0) {
      alert(`Please fill in the following required fields: ${missingFields.join(', ')}`);
      return;
    }

    try {
      const response = await aiMcpServiceRef.current.callToolDirectly('create_legacy_user', {
        name: formData.name,
        email: formData.email,
        address: formData.address,
        phone: formData.phone
      });

      // Reset form
      setFormData({
        name: '',
        email: '',
        address: '',
        phone: ''
      });

      // Call parent submit handler
      if (onSubmit) {
        onSubmit(response);
      }
    } catch (error) {
      console.error('Error creating legacy user:', error);
      alert('Failed to create legacy user. Please try again.');
    }
  };

  const handleClose = () => {
    // Reset form when closing
    setFormData({
      name: '',
      email: '',
      address: '',
      phone: ''
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
              <UserPlus className="w-6 h-6 text-blue-400" />
              <h2 className="text-xl font-semibold text-white">Legacy User Creation Form</h2>
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
                  <UserPlus className="w-5 h-5 mr-2 text-blue-400" />
                  Basic Information
                </h3>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  Full Name *
                  <span className="text-xs text-gray-400 ml-1">(as per official documents)</span>
                </label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => handleFormChange('name', e.target.value)}
                  className="w-full px-3 py-2 bg-[#1a1a1a] border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-blue-500"
                  placeholder="Enter full name"
                />
                <p className="text-xs text-gray-400 mt-1">Complete legal name for legacy records</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">Email Address *</label>
                <input
                  type="email"
                  value={formData.email}
                  onChange={(e) => handleFormChange('email', e.target.value)}
                  className="w-full px-3 py-2 bg-[#1a1a1a] border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-blue-500"
                  placeholder="Enter email address"
                />
                <p className="text-xs text-gray-400 mt-1">Primary contact email for legacy user</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">Phone Number</label>
                <input
                  type="tel"
                  value={formData.phone}
                  onChange={(e) => handleFormChange('phone', e.target.value)}
                  className="w-full px-3 py-2 bg-[#1a1a1a] border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-blue-500"
                  placeholder="Enter phone number"
                />
                <p className="text-xs text-gray-400 mt-1">Contact phone number with area code</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">Address</label>
                <textarea
                  value={formData.address}
                  onChange={(e) => handleFormChange('address', e.target.value)}
                  className="w-full px-3 py-2 bg-[#1a1a1a] border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-blue-500"
                  placeholder="Enter full address"
                  rows="3"
                />
                <p className="text-xs text-gray-400 mt-1">Complete address including city, state, and postal code</p>
              </div>
            </div>

            {/* Guidelines & Information */}
            <div className="space-y-4">
              <div className="border-b border-gray-600 pb-2 mb-4">
                <h3 className="text-lg font-medium text-white flex items-center">
                  💡 Legacy User Guidelines
                </h3>
              </div>

              {/* Legacy User Purpose */}
              <div className="bg-[#1a1a1a] rounded-lg p-4 border border-gray-600">
                <h4 className="text-sm font-medium text-blue-400 mb-2">📋 What is a Legacy User?</h4>
                <div className="text-xs text-gray-400 space-y-1">
                  <div>• Legacy users are simplified user records</div>
                  <div>• Used for historical data migration</div>
                  <div>• Basic contact information storage</div>
                  <div>• No authentication or role assignments</div>
                  <div>• Suitable for external contacts or references</div>
                </div>
              </div>

              {/* When to Use */}
              <div className="bg-[#1a1a1a] rounded-lg p-4 border border-gray-600">
                <h4 className="text-sm font-medium text-green-400 mb-2">✅ When to Use Legacy Users</h4>
                <div className="text-xs text-gray-400 space-y-1">
                  <div><strong>External Contacts:</strong> Non-staff contacts</div>
                  <div><strong>Data Migration:</strong> Importing old records</div>
                  <div><strong>Reference Only:</strong> Information storage</div>
                  <div><strong>Emergency Contacts:</strong> Patient references</div>
                  <div><strong>Vendors:</strong> Supplier contact information</div>
                </div>
              </div>

              {/* Best Practices */}
              <div className="bg-[#1a1a1a] rounded-lg p-4 border border-gray-600">
                <h4 className="text-sm font-medium text-yellow-400 mb-2">⭐ Best Practices</h4>
                <ul className="text-xs text-gray-400 space-y-1">
                  <li>• Use complete, accurate names</li>
                  <li>• Verify email addresses before entry</li>
                  <li>• Include country code for international phones</li>
                  <li>• Keep address format consistent</li>
                  <li>• Document purpose in notes if needed</li>
                </ul>
              </div>

              {/* Differences from Regular Users */}
              <div className="bg-[#1a1a1a] rounded-lg p-4 border border-gray-600">
                <h4 className="text-sm font-medium text-purple-400 mb-2">🔄 Legacy vs Regular Users</h4>
                <div className="text-xs text-gray-400 space-y-1">
                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <strong className="text-purple-300">Legacy Users:</strong>
                      <div>• No login access</div>
                      <div>• No roles/permissions</div>
                      <div>• Basic contact info only</div>
                      <div>• Simple data structure</div>
                    </div>
                    <div>
                      <strong className="text-blue-300">Regular Users:</strong>
                      <div>• System access</div>
                      <div>• Role-based permissions</div>
                      <div>• Full user profiles</div>
                      <div>• Authentication required</div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Data Usage */}
              <div className="bg-[#1a1a1a] rounded-lg p-4 border border-gray-600">
                <h4 className="text-sm font-medium text-orange-400 mb-2">🔒 Data Privacy</h4>
                <div className="text-xs text-gray-400 space-y-1">
                  <div>• Store only necessary information</div>
                  <div>• Ensure consent for data collection</div>
                  <div>• Follow privacy regulations</div>
                  <div>• Secure data transmission and storage</div>
                  <div>• Regular data audit and cleanup</div>
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
                <span>Creating Legacy User...</span>
              </>
            ) : (
              <>
                <CheckCircle className="w-4 h-4" />
                <span>Create Legacy User</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default LegacyUserCreationForm;
