import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Users, Save, ArrowLeft, AlertCircle, CheckCircle, Building2, Plus, X } from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import { API_ENDPOINTS } from '../../config/api';
import { formatPhoneNumber, unformatPhoneNumber, handlePhoneInput } from '../../utils/phoneUtils';
import '../../utils/authUtils'; // Import to ensure fetch interceptor is set up

interface Practice {
  uuid: string;
  name: string;
  address?: string;
  phone?: string;
  email?: string;
}

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

interface SelectedPractice {
  uuid: string;
  name: string;
  request_type: 'new_client' | 'transfer' | 'referral' | 'emergency';
  notes: string;
  primary_contact: boolean;
}

const PetOwnerCreate = () => {
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

  const [practices, setPractices] = useState<Practice[]>([]);
  const [selectedPractices, setSelectedPractices] = useState<SelectedPractice[]>([]);
  const [availablePractices, setAvailablePractices] = useState<Practice[]>([]);
  
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitStatus, setSubmitStatus] = useState<'idle' | 'success' | 'error'>('idle');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  // Check if user can access this page
  const canCreatePetOwners = user?.role === 'ADMIN' || user?.role === 'VET_STAFF';
  const isAdmin = user?.role === 'ADMIN';
  const isVetStaff = user?.role === 'VET_STAFF';

  useEffect(() => {
    if (!canCreatePetOwners) {
      navigate('/');
      return;
    }
    fetchPractices();
  }, [canCreatePetOwners, navigate]);

  // Auto-select practice for VET_STAFF users
  useEffect(() => {
    if (isVetStaff && user?.practice_id && practices.length > 0) {
      const userPractice = practices.find(p => p.uuid === user.practice_id);
      if (userPractice && selectedPractices.length === 0) {
        const autoAssociation: SelectedPractice = {
          uuid: userPractice.uuid,
          name: userPractice.name,
          request_type: 'new_client',
          notes: '',
          primary_contact: true
        };
        setSelectedPractices([autoAssociation]);
      }
    }
  }, [isVetStaff, user?.practice_id, practices, selectedPractices.length]);

  const fetchPractices = async () => {
    try {
      const response = await fetch(API_ENDPOINTS.PRACTICES.LIST);
      if (!response.ok) {
        throw new Error('Failed to fetch practices');
      }
      const data = await response.json();
      setPractices(data);
      setAvailablePractices(data);
    } catch (err) {
      setError('Failed to load practices');
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value, type } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? (e.target as HTMLInputElement).checked : value
    }));
  };

  const handlePhoneChange = (e: React.ChangeEvent<HTMLInputElement>, fieldName: string) => {
    handlePhoneInput(e, setFormData, fieldName);
  };

  const addPracticeAssociation = (practiceUuid: string) => {
    const practice = practices.find(p => p.uuid === practiceUuid);
    if (!practice) return;

    const newAssociation: SelectedPractice = {
      uuid: practice.uuid,
      name: practice.name,
      request_type: 'new_client',
      notes: '',
      primary_contact: selectedPractices.length === 0 // First one is primary by default
    };

    setSelectedPractices(prev => [...prev, newAssociation]);
    setAvailablePractices(prev => prev.filter(p => p.uuid !== practiceUuid));
  };

  const removePracticeAssociation = (practiceUuid: string) => {
    const practice = practices.find(p => p.uuid === practiceUuid);
    if (!practice) return;

    setSelectedPractices(prev => {
      const updated = prev.filter(p => p.uuid !== practiceUuid);
      // If we removed the primary contact, make the first remaining one primary
      if (updated.length > 0 && !updated.some(p => p.primary_contact)) {
        updated[0].primary_contact = true;
      }
      return updated;
    });
    setAvailablePractices(prev => [...prev, practice]);
  };

  const updatePracticeAssociation = (practiceUuid: string, field: keyof SelectedPractice, value: any) => {
    setSelectedPractices(prev => prev.map(p => {
      if (p.uuid === practiceUuid) {
        // If setting this as primary contact, unset others
        if (field === 'primary_contact' && value === true) {
          return { ...p, [field]: value };
        }
        return { ...p, [field]: value };
      } else if (field === 'primary_contact' && value === true) {
        // Unset primary contact for others
        return { ...p, primary_contact: false };
      }
      return p;
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Prevent double submission
    if (isSubmitting) {
      console.log('Form already submitting, ignoring duplicate submission');
      return;
    }
    
    console.log('Form submission started');
    setIsSubmitting(true);
    setSubmitStatus('idle');
    setError(null);

    // Validation
    if (!formData.full_name.trim()) {
      setError('Full name is required');
      setIsSubmitting(false);
      return;
    }

    // Only require practice selection for ADMIN users
    if (isAdmin && selectedPractices.length === 0) {
      setError('Please select at least one practice');
      setIsSubmitting(false);
      return;
    }

    try {
      // Step 1: Create the pet owner
      // Prepare form data with unformatted phone numbers for backend
      const submitData = {
        ...formData,
        phone: unformatPhoneNumber(formData.phone),
        emergency_contact: unformatPhoneNumber(formData.emergency_contact),
        secondary_phone: unformatPhoneNumber(formData.secondary_phone)
      };

      const petOwnerResponse = await fetch(API_ENDPOINTS.PET_OWNERS.CREATE, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(submitData)
      });

      if (!petOwnerResponse.ok) {
        const errorData = await petOwnerResponse.json();
        throw new Error(errorData.detail || 'Failed to create pet owner');
      }

      const petOwner = await petOwnerResponse.json();
      console.log('Pet owner created:', petOwner);

      // Step 2: Create practice associations
      const associationPromises = selectedPractices.map(async (practice) => {
        const associationData = {
          pet_owner_id: petOwner.uuid,
          practice_id: practice.uuid,
          request_type: practice.request_type,
          notes: practice.notes,
          primary_contact: practice.primary_contact
        };

        const response = await fetch(API_ENDPOINTS.ASSOCIATIONS.CREATE, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(associationData)
        });

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(`Failed to create association with ${practice.name}: ${errorData.detail}`);
        }

        return response.json();
      });

      await Promise.all(associationPromises);
      console.log('All associations created successfully');

      setSubmitStatus('success');
      setTimeout(() => {
        navigate('/pet_owners');
      }, 1500);

    } catch (err) {
      console.error('Form submission error:', err);
      setError(err instanceof Error ? err.message : 'Failed to create pet owner');
      setSubmitStatus('error');
    } finally {
      console.log('Form submission completed, setting isSubmitting to false');
      setIsSubmitting(false);
    }
  };

  if (!canCreatePetOwners) {
    return null; // Will redirect
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <Users className="w-8 h-8 text-blue-600 animate-pulse" />
          </div>
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Loading...</h2>
          <p className="text-gray-600">Fetching practice information</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <section className="bg-gradient-to-br from-blue-50 to-indigo-50 py-12">
        <div className="max-w-4xl mx-auto px-6">
          <div className="flex items-center mb-6">
            <button
              onClick={() => navigate('/pet_owners')}
              className="mr-4 p-2 text-gray-600 hover:text-gray-900 hover:bg-white rounded-lg transition-colors"
            >
              <ArrowLeft className="w-5 h-5" />
            </button>
            <div className="flex items-center">
              <div className="w-12 h-12 bg-blue-600 rounded-xl flex items-center justify-center mr-4">
                <Users className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-3xl font-bold text-gray-900">Create Pet Owner</h1>
                <p className="text-lg text-gray-600">
                  {isVetStaff 
                    ? "Add a new pet owner to your practice" 
                    : "Add a new pet owner and associate with practices"
                  }
                </p>
              </div>
            </div>
          </div>

          {/* Status Messages */}
          {submitStatus === 'success' && (
            <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg flex items-center">
              <CheckCircle className="w-5 h-5 text-green-600 mr-3" />
              <span className="text-green-800">Pet owner created successfully! Redirecting...</span>
            </div>
          )}

          {error && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-center">
              <AlertCircle className="w-5 h-5 text-red-600 mr-3" />
              <span className="text-red-800">{error}</span>
            </div>
          )}
        </div>
      </section>

      {/* Form */}
      <section className="py-12">
        <div className="max-w-4xl mx-auto px-6">
          <form onSubmit={handleSubmit} className="bg-white rounded-xl shadow-sm border border-gray-200 p-8">
            
            {/* Pet Owner Information */}
            <div className="mb-8">
              <h2 className="text-xl font-semibold text-gray-900 mb-6">Pet Owner Information</h2>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Full Name *
                  </label>
                  <input
                    type="text"
                    name="full_name"
                    value={formData.full_name}
                    onChange={handleInputChange}
                    required
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Enter full name"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Email
                  </label>
                  <input
                    type="email"
                    name="email"
                    value={formData.email}
                    onChange={handleInputChange}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Enter email address"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Phone
                  </label>
                  <input
                    type="tel"
                    name="phone"
                    value={formData.phone}
                    onChange={(e) => handlePhoneChange(e, 'phone')}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="(419) 283-1624"
                    maxLength={14} // (xxx) xxx-xxxx format
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Emergency Contact
                  </label>
                  <input
                    type="tel"
                    name="emergency_contact"
                    value={formData.emergency_contact}
                    onChange={(e) => handlePhoneChange(e, 'emergency_contact')}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="(419) 283-1624"
                    maxLength={14}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Secondary Phone
                  </label>
                  <input
                    type="tel"
                    name="secondary_phone"
                    value={formData.secondary_phone}
                    onChange={(e) => handlePhoneChange(e, 'secondary_phone')}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="(419) 283-1624"
                    maxLength={14}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Preferred Communication
                  </label>
                  <select
                    name="preferred_communication"
                    value={formData.preferred_communication}
                    onChange={handleInputChange}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="email">Email</option>
                    <option value="sms">SMS</option>
                    <option value="phone">Phone</option>
                  </select>
                </div>
              </div>

              <div className="mt-6">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Address
                </label>
                <textarea
                  name="address"
                  value={formData.address}
                  onChange={handleInputChange}
                  rows={3}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Enter full address"
                />
              </div>

              <div className="mt-6">
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    name="notifications_enabled"
                    checked={formData.notifications_enabled}
                    onChange={handleInputChange}
                    className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                  />
                  <span className="ml-2 text-sm text-gray-700">Enable notifications</span>
                </label>
              </div>
            </div>

            {/* Practice Associations - Only show for ADMIN or VET_STAFF with practice loaded */}
            {(isAdmin || (isVetStaff && selectedPractices.length > 0)) && (
              <div className="mb-8">
                <h2 className="text-xl font-semibold text-gray-900 mb-6">Practice Associations</h2>
                
                {/* VET_STAFF: Show read-only practice info */}
                {isVetStaff && selectedPractices.length > 0 && (
                  <div className="mb-6">
                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                      <div className="flex items-center">
                        <Building2 className="w-5 h-5 text-blue-600 mr-2" />
                        <div>
                          <h3 className="font-medium text-blue-900">
                            {selectedPractices[0].name}
                          </h3>
                          <p className="text-sm text-blue-700">
                            Pet owner will be automatically associated with your practice
                          </p>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
                
                {/* ADMIN: Add Practice Dropdown */}
                {isAdmin && availablePractices.length > 0 && (
                <div className="mb-6">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Add Practice Association
                  </label>
                  <div className="flex gap-3">
                    <select
                      onChange={(e) => {
                        if (e.target.value) {
                          addPracticeAssociation(e.target.value);
                          e.target.value = '';
                        }
                      }}
                      className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    >
                      <option value="">Select a practice to associate...</option>
                      {availablePractices.map(practice => (
                        <option key={practice.uuid} value={practice.uuid}>
                          {practice.name} {practice.address && `- ${practice.address}`}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>
              )}

              {/* ADMIN: Selected Practices with full controls */}
              {isAdmin && selectedPractices.length > 0 && (
                <div className="space-y-4">
                  {selectedPractices.map((practice) => (
                    <div key={practice.uuid} className="bg-gray-50 rounded-lg p-4 border border-gray-200">
                      <div className="flex items-start justify-between mb-4">
                        <div className="flex items-center">
                          <Building2 className="w-5 h-5 text-blue-600 mr-2" />
                          <h3 className="font-medium text-gray-900">{practice.name}</h3>
                          {practice.primary_contact && (
                            <span className="ml-2 px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full">
                              Primary
                            </span>
                          )}
                        </div>
                        <button
                          type="button"
                          onClick={() => removePracticeAssociation(practice.uuid)}
                          className="text-red-600 hover:text-red-800 p-1"
                        >
                          <X className="w-4 h-4" />
                        </button>
                      </div>

                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            Request Type
                          </label>
                          <select
                            value={practice.request_type}
                            onChange={(e) => updatePracticeAssociation(practice.uuid, 'request_type', e.target.value)}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                          >
                            <option value="new_client">New Client</option>
                            <option value="transfer">Transfer</option>
                            <option value="referral">Referral</option>
                            <option value="emergency">Emergency</option>
                          </select>
                        </div>

                        <div className="flex items-center">
                          <label className="flex items-center">
                            <input
                              type="checkbox"
                              checked={practice.primary_contact}
                              onChange={(e) => updatePracticeAssociation(practice.uuid, 'primary_contact', e.target.checked)}
                              className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                            />
                            <span className="ml-2 text-sm text-gray-700">Primary Contact</span>
                          </label>
                        </div>
                      </div>

                      <div className="mt-4">
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Notes
                        </label>
                        <textarea
                          value={practice.notes}
                          onChange={(e) => updatePracticeAssociation(practice.uuid, 'notes', e.target.value)}
                          rows={2}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                          placeholder="Optional notes about this association..."
                        />
                      </div>
                    </div>
                  ))}
                </div>
              )}

                {isAdmin && selectedPractices.length === 0 && (
                  <div className="text-center py-8 text-gray-500">
                    <Building2 className="w-12 h-12 mx-auto mb-3 text-gray-300" />
                    <p>No practice associations selected</p>
                    <p className="text-sm">Please select at least one practice above</p>
                  </div>
                )}
              </div>
            )}

            {/* Submit Button */}
            <div className="pt-6 border-t border-gray-200">
              <div className="flex space-x-4">
                <button
                  type="button"
                  onClick={() => navigate('/pet_owners')}
                  className="px-6 py-3 border border-gray-300 text-gray-700 rounded-lg font-medium hover:bg-gray-50 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting || (isAdmin && selectedPractices.length === 0)}
                  className="flex-1 bg-blue-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-blue-700 disabled:bg-blue-400 disabled:hover:bg-blue-400 disabled:cursor-not-allowed transition-colors flex items-center justify-center space-x-2"
                >
                  {isSubmitting ? (
                    <>
                      <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                      <span>Creating...</span>
                    </>
                  ) : (
                    <>
                      <Save className="w-5 h-5" />
                      <span>Create Pet Owner</span>
                    </>
                  )}
                </button>
              </div>
            </div>
          </form>
        </div>
      </section>
    </div>
  );
};

export default PetOwnerCreate;
