import React, { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { API_ENDPOINTS } from '../../config/api';

interface Practice {
  uuid: string;
  name: string;
  address_line1?: string;
  city?: string;
  state?: string;
}

interface ProfileEditModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const ProfileEditModal: React.FC<ProfileEditModalProps> = ({ isOpen, onClose }) => {
  const { user, login } = useAuth();
  const [formData, setFormData] = useState({
    email: '',
    full_name: '',
    practice_id: ''
  });
  const [practices, setPractices] = useState<Practice[]>([]);
  const [loading, setLoading] = useState(false);
  const [practicesLoading, setPracticesLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => {
    if (isOpen && user) {
      setFormData({
        email: user.email || '',
        full_name: user.full_name || '',
        practice_id: user.practice_id || ''
      });
      fetchPractices();
    }
  }, [isOpen, user]);

  const fetchPractices = async () => {
    try {
      const response = await fetch(API_ENDPOINTS.PRACTICES.LIST);
      if (response.ok) {
        const data = await response.json();
        setPractices(data);
      }
    } catch (error) {
      console.error('Failed to fetch practices:', error);
    } finally {
      setPracticesLoading(false);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccess('');

    try {
      const token = localStorage.getItem('token');
      const response = await fetch(API_ENDPOINTS.AUTH.ME, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          email: formData.email,
          full_name: formData.full_name,
          practice_id: formData.practice_id || null
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Update failed');
      }

      const updatedUser = await response.json();
      
      // Update the auth context with new user data
      if (token) {
        await login(user?.username || '', token);
      }

      setSuccess('Profile updated successfully!');
      setTimeout(() => {
        onClose();
      }, 1500);
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Update failed');
    } finally {
      setLoading(false);
    }
  };

  const handleRemovePractice = async () => {
    setLoading(true);
    setError('');
    setSuccess('');

    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_ENDPOINTS.AUTH.ME}/practice`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to remove practice association');
      }

      // Update form data
      setFormData(prev => ({ ...prev, practice_id: '' }));
      
      // Update the auth context
      if (token) {
        await login(user?.username || '', token);
      }

      setSuccess('Practice association removed successfully!');
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Failed to remove practice association');
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900">Edit Profile</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {/* Success Message */}
          {success && (
            <div className="bg-green-50 border border-green-200 rounded-md p-4">
              <div className="flex">
                <div className="flex-shrink-0">
                  <svg className="h-5 w-5 text-green-400" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                </div>
                <div className="ml-3">
                  <div className="text-green-800 text-sm">{success}</div>
                </div>
              </div>
            </div>
          )}

          {/* Error Message */}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-md p-4">
              <div className="flex">
                <div className="flex-shrink-0">
                  <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                  </svg>
                </div>
                <div className="ml-3">
                  <div className="text-red-800 text-sm">{error}</div>
                </div>
              </div>
            </div>
          )}

          {/* Form Fields */}
          <div className="space-y-4">
            {/* Username (Read-only) */}
            <div>
              <label className="block text-sm font-medium text-gray-700">
                Username
              </label>
              <input
                type="text"
                value={user?.username || ''}
                disabled
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-50 text-gray-500 cursor-not-allowed"
              />
              <p className="mt-1 text-xs text-gray-500">Username cannot be changed</p>
            </div>

            {/* Full Name */}
            <div>
              <label htmlFor="full_name" className="block text-sm font-medium text-gray-700">
                Full Name *
              </label>
              <input
                id="full_name"
                name="full_name"
                type="text"
                required
                value={formData.full_name}
                onChange={handleInputChange}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                placeholder="Dr. Sarah Johnson"
                disabled={loading}
              />
            </div>

            {/* Email */}
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700">
                Email Address *
              </label>
              <input
                id="email"
                name="email"
                type="email"
                required
                value={formData.email}
                onChange={handleInputChange}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                placeholder="sarah.johnson@example.com"
                disabled={loading}
              />
            </div>

            {/* Practice Association */}
            <div>
              <label htmlFor="practice_id" className="block text-sm font-medium text-gray-700">
                Veterinary Practice
              </label>
              {practicesLoading ? (
                <div className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-50">
                  <span className="text-gray-500">Loading practices...</span>
                </div>
              ) : (
                <div className="space-y-2">
                  <select
                    id="practice_id"
                    name="practice_id"
                    value={formData.practice_id}
                    onChange={handleInputChange}
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    disabled={loading}
                  >
                    <option value="">No practice selected</option>
                    {practices.map((practice) => (
                      <option key={practice.uuid} value={practice.uuid}>
                        {practice.name}
                        {practice.city && practice.state && ` - ${practice.city}, ${practice.state}`}
                      </option>
                    ))}
                  </select>
                  
                  {formData.practice_id && (
                    <button
                      type="button"
                      onClick={handleRemovePractice}
                      disabled={loading}
                      className="text-sm text-red-600 hover:text-red-800 disabled:opacity-50"
                    >
                      Remove practice association
                    </button>
                  )}
                </div>
              )}
              <p className="mt-1 text-xs text-gray-500">
                Select the veterinary practice you work for
              </p>
            </div>

            {/* Role (Read-only) */}
            <div>
              <label className="block text-sm font-medium text-gray-700">
                Role
              </label>
              <input
                type="text"
                value={user?.role === 'VET_STAFF' ? 'Veterinary Staff' : user?.role === 'PRACTICE_ADMIN' ? 'Practice Administrator' : user?.role === 'SYSTEM_ADMIN' ? 'System Administrator' : user?.role || ''}
                disabled
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-50 text-gray-500 cursor-not-allowed"
              />
              <p className="mt-1 text-xs text-gray-500">Role is assigned by administrators</p>
            </div>
          </div>

          {/* Actions */}
          <div className="flex justify-end space-x-3 pt-6 border-t border-gray-200">
            <button
              type="button"
              onClick={onClose}
              disabled={loading}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
            >
              {loading ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default ProfileEditModal;
