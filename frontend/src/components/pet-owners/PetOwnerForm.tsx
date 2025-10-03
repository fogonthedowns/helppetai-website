import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { Users, Save, ArrowLeft, AlertCircle, CheckCircle, Building2, Plus, X } from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import { API_ENDPOINTS } from '../../config/api';
import { formatPhoneNumber, unformatPhoneNumber, handlePhoneInput } from '../../utils/phoneUtils';
import PetsList from '../pets/PetsList';
import Breadcrumb, { BreadcrumbItem } from '../common/Breadcrumb';
import '../../utils/authUtils'; // Import to ensure fetch interceptor is set up

interface Practice {
  uuid: string;
  name: string;
  address?: string;
  phone?: string;
  email?: string;
}

interface PetOwnerFormData {
  user_id: string;  // Optional - can be empty for MVP
  full_name: string;
  email: string;
  phone: string;
  emergency_contact: string;
  secondary_phone: string;
  address: string;
  preferred_communication: string;
  notifications_enabled: boolean;
}

interface Association {
  id: string;
  practice_id: string;
  practice_name?: string;
  request_type: 'new_client' | 'transfer' | 'referral' | 'emergency';
  notes: string;
  primary_contact: boolean;
  status: string;
}

interface SelectedPractice {
  uuid: string;
  name: string;
  request_type: 'new_client' | 'transfer' | 'referral' | 'emergency';
  notes: string;
  primary_contact: boolean;
  isNew?: boolean;
  associationId?: string;
}

interface PetOwnerFormProps {
  mode: 'create' | 'edit';
}

const PetOwnerForm: React.FC<PetOwnerFormProps> = ({ mode }) => {
  const navigate = useNavigate();
  const { uuid } = useParams<{ uuid: string }>();
  const { user } = useAuth();
  
  const [formData, setFormData] = useState<PetOwnerFormData>({
    user_id: '',
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
  const [existingAssociations, setExistingAssociations] = useState<Association[]>([]);
  
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitStatus, setSubmitStatus] = useState<'idle' | 'success' | 'error'>('idle');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const isAdmin = user?.role === 'ADMIN';
  const communicationOptions = [
    { value: 'email', label: 'Email' },
    { value: 'sms', label: 'SMS' },
    { value: 'phone', label: 'Phone' }
  ];

  useEffect(() => {
    if (mode === 'edit' && uuid) {
      fetchPetOwner();
      // Only fetch practices for ADMIN in edit mode
      if (isAdmin) {
        fetchPractices();
      }
    } else if (mode === 'create') {
      fetchPractices();
    }
  }, [mode, uuid, isAdmin]);

  // Fetch associations after practices are loaded (only for ADMIN)
  useEffect(() => {
    if (mode === 'edit' && uuid && practices.length > 0 && isAdmin) {
      fetchExistingAssociations();
    }
  }, [mode, uuid, practices, isAdmin]);

  const fetchPetOwner = async () => {
    if (!uuid) return;
    
    setLoading(true);
    try {
      const response = await fetch(API_ENDPOINTS.PET_OWNERS.GET(uuid));
      if (!response.ok) {
        throw new Error('Failed to fetch pet owner');
      }
      const petOwner = await response.json();
      setFormData({
        user_id: petOwner.user_id || '',
        full_name: petOwner.full_name || '',
        email: petOwner.email || '',
        phone: petOwner.phone || '',
        emergency_contact: petOwner.emergency_contact || '',
        secondary_phone: petOwner.secondary_phone || '',
        address: petOwner.address || '',
        preferred_communication: petOwner.preferred_communication,
        notifications_enabled: petOwner.notifications_enabled
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load pet owner');
    } finally {
      setLoading(false);
    }
  };

  const fetchPractices = async () => {
    try {
      const response = await fetch(API_ENDPOINTS.PRACTICES.LIST);
      if (!response.ok) {
        throw new Error('Failed to fetch practices');
      }
      const data = await response.json();
      setPractices(data);
    } catch (err) {
      console.error('Failed to load practices:', err);
    }
  };

  const fetchExistingAssociations = async () => {
    if (!uuid) return;
    
    try {
      const response = await fetch(API_ENDPOINTS.ASSOCIATIONS.BY_PET_OWNER(uuid));
      if (!response.ok) {
        throw new Error('Failed to fetch associations');
      }
      const associations = await response.json();
      setExistingAssociations(associations);
      
      // Convert existing associations to selected practices format
      const existingSelected = associations.map((assoc: Association) => {
        const practice = practices.find(p => p.uuid === assoc.practice_id);
        return {
          uuid: assoc.practice_id,
          name: practice?.name || 'Unknown Practice',
          request_type: assoc.request_type,
          notes: assoc.notes || '',
          primary_contact: assoc.primary_contact,
          isNew: false,
          associationId: assoc.id
        };
      });
      
      setSelectedPractices(existingSelected);
      
      // Update available practices (exclude already associated ones)
      const associatedPracticeIds = associations.map((assoc: Association) => assoc.practice_id);
      setAvailablePractices(practices.filter(p => !associatedPracticeIds.includes(p.uuid)));
    } catch (err) {
      console.error('Failed to load associations:', err);
    }
  };

  // Update available practices when practices or selected practices change
  useEffect(() => {
    if (practices.length > 0) {
      const selectedPracticeIds = selectedPractices.map(sp => sp.uuid);
      setAvailablePractices(practices.filter(p => !selectedPracticeIds.includes(p.uuid)));
    }
  }, [practices, selectedPractices]);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target;
    
    if (type === 'checkbox') {
      const checked = (e.target as HTMLInputElement).checked;
      setFormData(prev => ({ ...prev, [name]: checked }));
    } else {
      setFormData(prev => ({ ...prev, [name]: value }));
    }
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
      primary_contact: selectedPractices.length === 0, // First one is primary by default
      isNew: true
    };

    setSelectedPractices(prev => [...prev, newAssociation]);
  };

  const removePracticeAssociation = (practiceUuid: string) => {
    setSelectedPractices(prev => {
      const updated = prev.filter(p => p.uuid !== practiceUuid);
      // If we removed the primary contact, make the first remaining one primary
      if (updated.length > 0 && !updated.some(p => p.primary_contact)) {
        updated[0].primary_contact = true;
      }
      return updated;
    });
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
    setError(null);
    setSubmitStatus('idle');

    // Validation
    if (!formData.full_name.trim()) {
      setError('Full name is required');
      setIsSubmitting(false);
      return;
    }

    try {
      // Step 1: Update pet owner basic info
      const submitData = {
        ...formData,
        user_id: formData.user_id.trim() || null, // Convert empty string to null for UUID field
        phone: unformatPhoneNumber(formData.phone),
        emergency_contact: unformatPhoneNumber(formData.emergency_contact),
        secondary_phone: unformatPhoneNumber(formData.secondary_phone)
      };

      let response;
      if (mode === 'create') {
        response = await fetch(API_ENDPOINTS.PET_OWNERS.CREATE, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(submitData),
        });
      } else {
        response = await fetch(API_ENDPOINTS.PET_OWNERS.UPDATE(uuid!), {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(submitData),
        });
      }

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Failed to ${mode} pet owner`);
      }

      const result = await response.json();
      console.log('Pet owner updated:', result);

      // Step 2: Handle practice associations (only for ADMIN in edit mode)
      if (mode === 'edit' && uuid && isAdmin) {
        await handleAssociationUpdates(uuid);
      }

      setSubmitStatus('success');
      
      // Redirect after a brief delay to show success message
      setTimeout(() => {
        if (mode === 'edit') {
          navigate(`/pet_owners/${uuid}`);
        } else {
          navigate(`/pet_owners/${result.uuid}`);
        }
      }, 1500);

    } catch (err) {
      console.error('Form submission error:', err);
      setError(err instanceof Error ? err.message : `Failed to ${mode} pet owner`);
      setSubmitStatus('error');
    } finally {
      console.log('Form submission completed, setting isSubmitting to false');
      setIsSubmitting(false);
    }
  };

  const handleAssociationUpdates = async (petOwnerUuid: string) => {
    const promises: Promise<any>[] = [];

    // Handle new associations
    const newAssociations = selectedPractices.filter(sp => sp.isNew);
    for (const practice of newAssociations) {
      const associationData = {
        pet_owner_id: petOwnerUuid,
        practice_id: practice.uuid,
        request_type: practice.request_type,
        notes: practice.notes,
        primary_contact: practice.primary_contact
      };

      promises.push(
        fetch(API_ENDPOINTS.ASSOCIATIONS.CREATE, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(associationData)
        }).then(response => {
          if (!response.ok) {
            throw new Error(`Failed to create association with ${practice.name}`);
          }
          return response.json();
        })
      );
    }

    // Handle removed associations
    const currentPracticeIds = selectedPractices.map(sp => sp.uuid);
    const removedAssociations = existingAssociations.filter(
      assoc => !currentPracticeIds.includes(assoc.practice_id)
    );
    
    for (const assoc of removedAssociations) {
      promises.push(
        fetch(API_ENDPOINTS.ASSOCIATIONS.DELETE(assoc.id), {
          method: 'DELETE'
        }).then(response => {
          if (!response.ok) {
            throw new Error(`Failed to remove association`);
          }
        })
      );
    }

    // Handle updated existing associations
    const updatedAssociations = selectedPractices.filter(
      sp => !sp.isNew && sp.associationId
    );
    
    for (const practice of updatedAssociations) {
      const originalAssoc = existingAssociations.find(ea => ea.id === practice.associationId);
      if (originalAssoc && (
        originalAssoc.request_type !== practice.request_type ||
        originalAssoc.notes !== practice.notes ||
        originalAssoc.primary_contact !== practice.primary_contact
      )) {
        const updateData = {
          request_type: practice.request_type,
          notes: practice.notes,
          primary_contact: practice.primary_contact
        };

        promises.push(
          fetch(API_ENDPOINTS.ASSOCIATIONS.UPDATE(practice.associationId!), {
            method: 'PUT',
            headers: {
              'Content-Type': 'application/json'
            },
            body: JSON.stringify(updateData)
          }).then(response => {
            if (!response.ok) {
              throw new Error(`Failed to update association with ${practice.name}`);
            }
            return response.json();
          })
        );
      }
    }

    await Promise.all(promises);
    console.log('All association updates completed');
  };

  // Check authorization for editing
  const canEdit = user?.role === 'ADMIN' || user?.role === 'VET_STAFF' || user?.role === 'PRACTICE_ADMIN';
  if (mode === 'edit' && !canEdit) {
    // Only ADMIN, VET_STAFF, and PRACTICE_ADMIN can edit pet owners
    // VET_STAFF and PRACTICE_ADMIN can edit pet owners associated with their practice (backend will enforce this)
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <AlertCircle className="w-16 h-16 text-red-300 mx-auto mb-4" />
          <h1 className="text-2xl font-bold text-gray-900 mb-4">Access Denied</h1>
          <p className="text-gray-600 mb-6">Admin or Vet Staff access required to edit pet owners.</p>
          <button
            onClick={() => navigate(-1)}
            className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors"
          >
            Go Back
          </button>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading pet owner...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <section className="bg-white border-b border-gray-200">
        <div className="max-w-4xl mx-auto px-6 py-8">
          {/* Breadcrumbs */}
          <Breadcrumb 
            items={mode === 'edit' ? [
              { label: 'Pet Owners', href: '/pet_owners' },
              { label: formData.full_name || 'Pet Owner', href: `/pet_owners/${uuid}` },
              { label: 'Edit', isActive: true }
            ] : [
              { label: 'Pet Owners', href: '/pet_owners' },
              { label: 'Create', isActive: true }
            ]}
            className="mb-6"
          />

          <div className="flex items-center space-x-4">
            <div className="bg-blue-100 p-4 rounded-xl">
              <Users className="w-8 h-8 text-blue-600" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-gray-900">
                {mode === 'create' ? 'Create Pet Owner' : 'Edit Pet Owner'}
              </h1>
              <p className="text-gray-600 mt-1">
                {mode === 'create' 
                  ? 'Update pet owner information' 
                  : 'Update pet owner information'
                }
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Form */}
      <section className="py-8">
        <div className="max-w-4xl mx-auto px-6">
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8">
            {/* Status Messages */}
            {submitStatus === 'success' && (
              <div className="mb-6 bg-green-50 border border-green-200 rounded-md p-4">
                <div className="flex items-center">
                  <CheckCircle className="w-5 h-5 text-green-600 mr-2" />
                  <span className="text-green-800">
                    Pet owner {mode === 'create' ? 'created' : 'updated'} successfully! Redirecting...
                  </span>
                </div>
              </div>
            )}

            {error && (
              <div className="mb-6 bg-red-50 border border-red-200 rounded-md p-4">
                <div className="flex items-center">
                  <AlertCircle className="w-5 h-5 text-red-600 mr-2" />
                  <span className="text-red-800">{error}</span>
                </div>
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Basic Information */}
              <div>
                <label htmlFor="full_name" className="block text-sm font-medium text-gray-700 mb-2">
                  Full Name *
                </label>
                <input
                  type="text"
                  id="full_name"
                  name="full_name"
                  value={formData.full_name}
                  onChange={handleInputChange}
                  required
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Enter full name"
                />
              </div>

              {/* Primary Contact Information */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-2">
                    Email Address
                  </label>
                  <input
                    type="email"
                    id="email"
                    name="email"
                    value={formData.email}
                    onChange={handleInputChange}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="owner@example.com"
                  />
                </div>

                <div>
                  <label htmlFor="phone" className="block text-sm font-medium text-gray-700 mb-2">
                    Primary Phone
                  </label>
                  <input
                    type="tel"
                    id="phone"
                    name="phone"
                    value={formData.phone}
                    onChange={handleInputChange}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="(555) 123-4567"
                  />
                </div>
              </div>

              {/* Additional Contact Information */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label htmlFor="emergency_contact" className="block text-sm font-medium text-gray-700 mb-2">
                    Emergency Contact
                  </label>
                  <input
                    type="tel"
                    id="emergency_contact"
                    name="emergency_contact"
                    value={formData.emergency_contact}
                    onChange={handleInputChange}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="(555) 123-4567"
                  />
                </div>

                <div>
                  <label htmlFor="secondary_phone" className="block text-sm font-medium text-gray-700 mb-2">
                    Secondary Phone
                  </label>
                  <input
                    type="tel"
                    id="secondary_phone"
                    name="secondary_phone"
                    value={formData.secondary_phone}
                    onChange={handleInputChange}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="(555) 123-4567"
                  />
                </div>
              </div>

              {/* Address */}
              <div>
                <label htmlFor="address" className="block text-sm font-medium text-gray-700 mb-2">
                  Address
                </label>
                <textarea
                  id="address"
                  name="address"
                  value={formData.address}
                  onChange={handleInputChange}
                  rows={3}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="123 Main St, City, State 12345"
                />
              </div>

              {/* Preferences */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label htmlFor="preferred_communication" className="block text-sm font-medium text-gray-700 mb-2">
                    Preferred Communication *
                  </label>
                  <select
                    id="preferred_communication"
                    name="preferred_communication"
                    value={formData.preferred_communication}
                    onChange={handleInputChange}
                    required
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  >
                    {communicationOptions.map(option => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="flex items-center">
                  <input
                    type="checkbox"
                    id="notifications_enabled"
                    name="notifications_enabled"
                    checked={formData.notifications_enabled}
                    onChange={handleInputChange}
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                  <label htmlFor="notifications_enabled" className="ml-2 block text-sm font-medium text-gray-700">
                    Enable Notifications
                  </label>
                </div>
              </div>

              {/* Practice Associations - Only show for ADMIN in edit mode */}
              {mode === 'edit' && isAdmin && (
                <div className="mb-8">
                  <h2 className="text-xl font-semibold text-gray-900 mb-6">Practice Associations</h2>
                  
                  {/* Add Practice Dropdown */}
                  {availablePractices.length > 0 && (
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

                  {/* Selected Practices */}
                  {selectedPractices.length > 0 && (
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
                              {practice.isNew && (
                                <span className="ml-2 px-2 py-1 bg-green-100 text-green-800 text-xs rounded-full">
                                  New
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

                  {selectedPractices.length === 0 && (
                    <div className="text-center py-8 text-gray-500">
                      <Building2 className="w-12 h-12 mx-auto mb-3 text-gray-300" />
                      <p>No practice associations</p>
                      <p className="text-sm">Add practice associations above</p>
                    </div>
                  )}
                </div>
              )}

              {/* Submit Button */}
              <div className="flex items-center justify-end pt-6 border-t border-gray-200">
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="bg-blue-600 text-white px-8 py-3 rounded-lg hover:bg-blue-700 disabled:bg-blue-400 disabled:hover:bg-blue-400 transition-colors flex items-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <Save className="w-4 h-4" />
                  <span>
                    {isSubmitting 
                      ? (mode === 'create' ? 'Creating...' : 'Updating...') 
                      : (mode === 'create' ? 'Create Pet Owner' : 'Update Pet Owner')
                    }
                  </span>
                </button>
              </div>
            </form>
          </div>

          {/* Pets Section - Only show in edit mode */}
          {mode === 'edit' && uuid && (
            <div className="mt-8">
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <PetsList 
                  ownerUuid={uuid} 
                  petOwner={{
                    id: uuid,
                    user_id: formData.user_id,
                    full_name: formData.full_name
                  }}
                />
              </div>
            </div>
          )}
        </div>
      </section>
    </div>
  );
};

export default PetOwnerForm;
