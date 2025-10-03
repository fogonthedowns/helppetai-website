import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { X, Save, AlertCircle, CheckCircle } from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import { API_ENDPOINTS } from '../../config/api';
import { formatPhoneNumber, unformatPhoneNumber, handlePhoneInput } from '../../utils/phoneUtils';

interface PetOwnerFormData {
  full_name: string;
  email: string;
  phone: string;
  emergency_contact: string;
  secondary_phone: string;
  address: string;
  preferred_communication: 'email' | 'sms' | 'phone';
  notifications_enabled: boolean;
}

interface PetOwnerEditFormProps {
  onClose: () => void;
  onSuccess?: () => void;
  ownerUuid: string;
}

const PetOwnerEditForm: React.FC<PetOwnerEditFormProps> = ({ onClose, onSuccess, ownerUuid }) => {
  const navigate = useNavigate();
  const { user } = useAuth();

  const [formData, setFormData] = useState<PetOwnerFormData>({
    full_name: '',
    email: '',
    phone: '',
    emergency_contact: '',
    secondary_phone: '',
    address: '',
    preferred_communication: 'email',
    notifications_enabled: true
  });

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [submitStatus, setSubmitStatus] = useState<'idle' | 'success' | 'error'>('idle');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchOwner();
  }, [ownerUuid]);

  const fetchOwner = async () => {
    try {
      const response = await fetch(API_ENDPOINTS.PET_OWNERS.GET(ownerUuid));
      if (!response.ok) throw new Error('Failed to fetch pet owner');
      const owner = await response.json();
      setFormData({
        full_name: owner.full_name,
        email: owner.email || '',
        phone: formatPhoneNumber(owner.phone || ''),
        emergency_contact: formatPhoneNumber(owner.emergency_contact || ''),
        secondary_phone: formatPhoneNumber(owner.secondary_phone || ''),
        address: owner.address || '',
        preferred_communication: owner.preferred_communication || 'email',
        notifications_enabled: owner.notifications_enabled ?? true
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load pet owner');
    } finally {
      setIsLoading(false);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target;
    
    if (type === 'checkbox') {
      const checked = (e.target as HTMLInputElement).checked;
      setFormData(prev => ({ ...prev, [name]: checked }));
    } else {
      setFormData(prev => ({ ...prev, [name]: value }));
    }
  };

  const handlePhoneChange = (e: React.ChangeEvent<HTMLInputElement>, field: string) => {
    const formatted = formatPhoneNumber(e.target.value);
    setFormData(prev => ({ ...prev, [field]: formatted }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setError(null);

    try {
      // Create pet owner
      const petOwnerPayload = {
        ...formData,
        phone: unformatPhoneNumber(formData.phone),
        emergency_contact: unformatPhoneNumber(formData.emergency_contact),
        secondary_phone: unformatPhoneNumber(formData.secondary_phone),
        user_id: null
      };

        const response = await fetch(API_ENDPOINTS.PET_OWNERS.UPDATE(ownerUuid), {
          method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(petOwnerPayload)
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to update pet owner');
      }

      setSubmitStatus('success');
      onSuccess?.();
      onClose();

    } catch (err) {
      console.error('Form submission error:', err);
      setError(err instanceof Error ? err.message : 'Failed to update pet owner');
      setSubmitStatus('error');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200">
        <h2 className="text-base font-semibold text-gray-900">Edit Pet Owner</h2>
        <button
          onClick={onClose}
          className="p-1.5 text-gray-600 hover:bg-gray-100 rounded transition-colors"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Error Alert */}
      {error && (
        <div className="mx-4 mt-3 p-3 bg-red-50 border border-red-200 rounded-lg flex items-start gap-2">
          <AlertCircle className="w-4 h-4 text-red-600 mt-0.5 flex-shrink-0" />
          <p className="text-xs text-red-800">{error}</p>
        </div>
      )}

      {/* Form Content */}
      <form onSubmit={handleSubmit} className="flex-1 overflow-y-auto p-4 space-y-4">
        {/* Contact Information */}
        <section>
          <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
            Contact Information
          </h3>
          <div className="space-y-2">
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">
                Full Name *
              </label>
              <input
                type="text"
                name="full_name"
                value={formData.full_name}
                onChange={handleInputChange}
                required
                className="w-full px-2 py-1.5 text-xs border border-gray-300 rounded focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
                placeholder="Enter full name"
              />
            </div>

            <div className="grid grid-cols-2 gap-2">
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">Email</label>
                <input
                  type="email"
                  name="email"
                  value={formData.email}
                  onChange={handleInputChange}
                  className="w-full px-2 py-1.5 text-xs border border-gray-300 rounded focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Enter email"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">Phone</label>
                <input
                  type="tel"
                  name="phone"
                  value={formData.phone}
                  onChange={(e) => handlePhoneChange(e, 'phone')}
                  className="w-full px-2 py-1.5 text-xs border border-gray-300 rounded focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="(419) 283-1624"
                  maxLength={14}
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-2">
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">Emergency Contact</label>
                <input
                  type="tel"
                  name="emergency_contact"
                  value={formData.emergency_contact}
                  onChange={(e) => handlePhoneChange(e, 'emergency_contact')}
                  className="w-full px-2 py-1.5 text-xs border border-gray-300 rounded focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="(419) 283-1624"
                  maxLength={14}
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">Secondary Phone</label>
                <input
                  type="tel"
                  name="secondary_phone"
                  value={formData.secondary_phone}
                  onChange={(e) => handlePhoneChange(e, 'secondary_phone')}
                  className="w-full px-2 py-1.5 text-xs border border-gray-300 rounded focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="(419) 283-1624"
                  maxLength={14}
                />
              </div>
            </div>
          </div>
        </section>

        {/* Additional Information */}
        <section>
          <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
            Additional Information
          </h3>
          <div className="space-y-2">
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">Address</label>
              <textarea
                name="address"
                value={formData.address}
                onChange={handleInputChange}
                rows={2}
                className="w-full px-2 py-1.5 text-xs border border-gray-300 rounded focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
                placeholder="Enter full address"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">Preferred Communication</label>
              <select
                name="preferred_communication"
                value={formData.preferred_communication}
                onChange={handleInputChange}
                className="w-full px-2 py-1.5 text-xs border border-gray-300 rounded focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="email">Email</option>
                <option value="sms">SMS</option>
                <option value="phone">Phone</option>
              </select>
            </div>

            <div>
              <label className="flex items-center gap-2 text-xs font-medium text-gray-700">
                <input
                  type="checkbox"
                  name="notifications_enabled"
                  checked={formData.notifications_enabled}
                  onChange={handleInputChange}
                  className="rounded border-gray-300 text-blue-600 focus:ring-1 focus:ring-blue-500"
                />
                Enable notifications
              </label>
            </div>
          </div>
        </section>
      </form>

      {/* Footer */}
      <div className="px-4 py-3 border-t border-gray-200 flex justify-end gap-2">
        <button
          type="button"
          onClick={onClose}
          className="px-3 py-1.5 text-xs font-medium text-gray-700 bg-white border border-gray-300 rounded hover:bg-gray-50 transition-colors"
          disabled={isSubmitting}
        >
          Cancel
        </button>
        <button
          onClick={handleSubmit}
          disabled={isSubmitting}
          className="px-3 py-1.5 text-xs font-medium text-white bg-blue-600 rounded hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1"
        >
          <Save className="w-3.5 h-3.5" />
          {isSubmitting ? 'Saving...' : 'Save Changes'}
        </button>
      </div>
    </div>
  );
};

export default PetOwnerEditForm;

