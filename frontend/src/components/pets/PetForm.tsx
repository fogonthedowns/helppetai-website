import React, { useState, useEffect } from 'react';
import { useNavigate, useParams, useSearchParams } from 'react-router-dom';
import { ArrowLeft, Heart, Save, AlertCircle } from 'lucide-react';
import { Pet, PetFormData, PetCreateRequest, PetUpdateRequest, PET_SPECIES_OPTIONS, PET_GENDER_OPTIONS } from '../../types/pet';
import { API_ENDPOINTS } from '../../config/api';
import { useAuth } from '../../contexts/AuthContext';
import Breadcrumb, { BreadcrumbItem } from '../common/Breadcrumb';
import '../../utils/authUtils';

interface PetFormProps {
  mode: 'create' | 'edit';
}

const PetForm: React.FC<PetFormProps> = ({ mode }) => {
  const navigate = useNavigate();
  const { uuid } = useParams<{ uuid: string }>();
  const [searchParams] = useSearchParams();
  const { user } = useAuth();

  const [formData, setFormData] = useState<PetFormData>({
    name: '',
    species: '',
    breed: '',
    color: '',
    gender: '',
    weight: undefined,
    date_of_birth: '',
    microchip_id: '',
    spayed_neutered: undefined,
    allergies: '',
    medications: '',
    medical_notes: '',
    emergency_contact: '',
    emergency_phone: ''
  });

  const [ownerUuid, setOwnerUuid] = useState<string>('');
  const [pet, setPet] = useState<Pet | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitStatus, setSubmitStatus] = useState<'idle' | 'success' | 'error'>('idle');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (mode === 'create') {
      const ownerIdFromQuery = searchParams.get('owner_id');
      if (ownerIdFromQuery) {
        setOwnerUuid(ownerIdFromQuery);
      }
    } else if (mode === 'edit' && uuid) {
      fetchPet();
    }
  }, [mode, uuid, searchParams]);

  const fetchPet = async () => {
    if (!uuid) return;

    setLoading(true);
    try {
      const response = await fetch(API_ENDPOINTS.PETS.GET(uuid));
      
      if (!response.ok) {
        if (response.status === 403) {
          throw new Error('Access denied to this pet');
        }
        if (response.status === 404) {
          throw new Error('Pet not found');
        }
        throw new Error('Failed to fetch pet');
      }

      const petData: Pet = await response.json();
      setPet(petData);
      
      // Convert pet data to form data
      setFormData({
        name: petData.name,
        species: petData.species,
        breed: petData.breed || '',
        color: petData.color || '',
        gender: petData.gender || '',
        weight: petData.weight,
        date_of_birth: petData.date_of_birth || '',
        microchip_id: petData.microchip_id || '',
        spayed_neutered: petData.spayed_neutered,
        allergies: petData.allergies || '',
        medications: petData.medications || '',
        medical_notes: petData.medical_notes || '',
        emergency_contact: petData.emergency_contact || '',
        emergency_phone: petData.emergency_phone || ''
      });
      
      setOwnerUuid(petData.owner_id);
    } catch (err) {
      console.error('Error fetching pet:', err);
      setError(err instanceof Error ? err.message : 'Failed to load pet');
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value, type } = e.target;
    
    setFormData(prev => ({
      ...prev,
      [name]: type === 'number' ? (value ? parseFloat(value) : undefined) : value
    }));
  };

  const handleCheckboxChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: checked
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (isSubmitting) return;

    setIsSubmitting(true);
    setError(null);
    setSubmitStatus('idle');

    try {
      // Clean form data - convert empty strings to undefined for optional fields
      const cleanedData = {
        ...formData,
        breed: formData.breed?.trim() || undefined,
        color: formData.color?.trim() || undefined,
        gender: formData.gender?.trim() || undefined,
        microchip_id: formData.microchip_id?.trim() || undefined,
        allergies: formData.allergies?.trim() || undefined,
        medications: formData.medications?.trim() || undefined,
        medical_notes: formData.medical_notes?.trim() || undefined,
        emergency_contact: formData.emergency_contact?.trim() || undefined,
        emergency_phone: formData.emergency_phone?.trim() || undefined,
        date_of_birth: formData.date_of_birth || undefined
      };

      let response: Response;

      if (mode === 'create') {
        const createData: PetCreateRequest = {
          ...cleanedData,
          owner_id: ownerUuid
        };

        response = await fetch(API_ENDPOINTS.PETS.CREATE, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(createData)
        });
      } else {
        const updateData: PetUpdateRequest = cleanedData;

        response = await fetch(API_ENDPOINTS.PETS.UPDATE(uuid!), {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(updateData)
        });
      }

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `Failed to ${mode} pet`);
      }

      const result = await response.json();
      console.log(`Pet ${mode}d:`, result);

      setSubmitStatus('success');
      
      // Redirect after a brief delay to show success message
      setTimeout(() => {
        navigate(`/pet_owners/${ownerUuid}`);
      }, 1500);

    } catch (err) {
      console.error('Form submission error:', err);
      setError(err instanceof Error ? err.message : `Failed to ${mode} pet`);
      setSubmitStatus('error');
    } finally {
      setIsSubmitting(false);
    }
  };

  const canAccessForm = () => {
    return user?.role === 'ADMIN' || user?.role === 'VET_STAFF';
  };

  if (!canAccessForm()) {
    return (
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="bg-red-50 border border-red-200 rounded-lg p-6">
            <div className="flex items-center">
              <AlertCircle className="w-6 h-6 text-red-600 mr-3" />
              <div>
                <h3 className="text-lg font-medium text-red-800">Access Denied</h3>
                <p className="text-red-700 mt-1">You don't have permission to {mode} pets.</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <span className="ml-2 text-gray-600">Loading pet...</span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          {/* Breadcrumbs */}
          <Breadcrumb 
            items={mode === 'edit' ? [
              { label: 'Pet Owners', href: '/pet_owners' },
              { label: pet?.name || 'Pet', href: `/pets/${uuid}` },
              { label: 'Edit', isActive: true }
            ] : [
              { label: 'Pet Owners', href: '/pet_owners' },
              { label: 'Create Pet', isActive: true }
            ]}
            className="mb-6"
          />
          
          <div className="flex items-center">
            <div className="bg-blue-100 p-3 rounded-lg mr-4">
              <Heart className="w-6 h-6 text-blue-600" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                {mode === 'create' ? 'Add New Pet' : 'Edit Pet'}
              </h1>
              <p className="text-gray-600">
                {mode === 'create' 
                  ? 'Register a new pet for this owner' 
                  : 'Update pet information and medical details'
                }
              </p>
            </div>
          </div>
        </div>

        {/* Form */}
        <div className="bg-white shadow-sm rounded-lg">
          <form onSubmit={handleSubmit} className="p-6 space-y-6">
            {/* Basic Information */}
            <div>
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Basic Information</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-2">
                    Pet Name *
                  </label>
                  <input
                    type="text"
                    id="name"
                    name="name"
                    required
                    value={formData.name}
                    onChange={handleInputChange}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Enter pet's name"
                  />
                </div>

                <div>
                  <label htmlFor="species" className="block text-sm font-medium text-gray-700 mb-2">
                    Species *
                  </label>
                  <select
                    id="species"
                    name="species"
                    required
                    value={formData.species}
                    onChange={handleInputChange}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="">Select species</option>
                    {PET_SPECIES_OPTIONS.map(species => (
                      <option key={species} value={species}>{species}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label htmlFor="breed" className="block text-sm font-medium text-gray-700 mb-2">
                    Breed
                  </label>
                  <input
                    type="text"
                    id="breed"
                    name="breed"
                    value={formData.breed}
                    onChange={handleInputChange}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Enter breed"
                  />
                </div>

                <div>
                  <label htmlFor="color" className="block text-sm font-medium text-gray-700 mb-2">
                    Color
                  </label>
                  <input
                    type="text"
                    id="color"
                    name="color"
                    value={formData.color}
                    onChange={handleInputChange}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Enter color"
                  />
                </div>

                <div>
                  <label htmlFor="gender" className="block text-sm font-medium text-gray-700 mb-2">
                    <span className="flex items-center">
                      Gender
                      {formData.gender && (
                        <span className={`ml-2 font-bold ${
                          formData.gender.toLowerCase() === 'male' ? 'text-blue-500' : 
                          formData.gender.toLowerCase() === 'female' ? 'text-pink-500' : 
                          'text-gray-400'
                        }`}>
                          {formData.gender.toLowerCase() === 'male' ? '♂' : 
                           formData.gender.toLowerCase() === 'female' ? '♀' : 
                           '♂♀'}
                        </span>
                      )}
                    </span>
                  </label>
                  <select
                    id="gender"
                    name="gender"
                    value={formData.gender}
                    onChange={handleInputChange}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="">Select gender</option>
                    {PET_GENDER_OPTIONS.map(gender => (
                      <option key={gender} value={gender}>{gender}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label htmlFor="weight" className="block text-sm font-medium text-gray-700 mb-2">
                    Weight (lbs)
                  </label>
                  <input
                    type="number"
                    id="weight"
                    name="weight"
                    min="0"
                    step="0.1"
                    value={formData.weight || ''}
                    onChange={handleInputChange}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Enter weight"
                  />
                </div>

                <div>
                  <label htmlFor="date_of_birth" className="block text-sm font-medium text-gray-700 mb-2">
                    Date of Birth
                  </label>
                  <input
                    type="date"
                    id="date_of_birth"
                    name="date_of_birth"
                    value={formData.date_of_birth}
                    onChange={handleInputChange}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>

                <div>
                  <label htmlFor="microchip_id" className="block text-sm font-medium text-gray-700 mb-2">
                    Microchip ID
                  </label>
                  <input
                    type="text"
                    id="microchip_id"
                    name="microchip_id"
                    value={formData.microchip_id}
                    onChange={handleInputChange}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Enter microchip ID"
                  />
                </div>
              </div>

              <div className="mt-6">
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    name="spayed_neutered"
                    checked={formData.spayed_neutered || false}
                    onChange={handleCheckboxChange}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  <span className="ml-2 text-sm text-gray-700">Spayed/Neutered</span>
                </label>
              </div>
            </div>

            {/* Medical Information */}
            <div>
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Medical Information</h2>
              <div className="space-y-4">
                <div>
                  <label htmlFor="allergies" className="block text-sm font-medium text-gray-700 mb-2">
                    Allergies
                  </label>
                  <textarea
                    id="allergies"
                    name="allergies"
                    rows={3}
                    value={formData.allergies}
                    onChange={handleInputChange}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="List any known allergies"
                  />
                </div>

                <div>
                  <label htmlFor="medications" className="block text-sm font-medium text-gray-700 mb-2">
                    Current Medications
                  </label>
                  <textarea
                    id="medications"
                    name="medications"
                    rows={3}
                    value={formData.medications}
                    onChange={handleInputChange}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="List current medications and dosages"
                  />
                </div>

                <div>
                  <label htmlFor="medical_notes" className="block text-sm font-medium text-gray-700 mb-2">
                    Medical Notes
                  </label>
                  <textarea
                    id="medical_notes"
                    name="medical_notes"
                    rows={4}
                    value={formData.medical_notes}
                    onChange={handleInputChange}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Additional medical notes or conditions"
                  />
                </div>
              </div>
            </div>

            {/* Emergency Contact */}
            <div>
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Emergency Contact</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label htmlFor="emergency_contact" className="block text-sm font-medium text-gray-700 mb-2">
                    Emergency Contact Name
                  </label>
                  <input
                    type="text"
                    id="emergency_contact"
                    name="emergency_contact"
                    value={formData.emergency_contact}
                    onChange={handleInputChange}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Enter emergency contact name"
                  />
                </div>

                <div>
                  <label htmlFor="emergency_phone" className="block text-sm font-medium text-gray-700 mb-2">
                    Emergency Phone
                  </label>
                  <input
                    type="tel"
                    id="emergency_phone"
                    name="emergency_phone"
                    value={formData.emergency_phone}
                    onChange={handleInputChange}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Enter emergency phone number"
                  />
                </div>
              </div>
            </div>

            {/* Error Display */}
            {error && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                <div className="flex items-center">
                  <AlertCircle className="w-5 h-5 text-red-600 mr-2" />
                  <p className="text-sm text-red-700">{error}</p>
                </div>
              </div>
            )}

            {/* Success Display */}
            {submitStatus === 'success' && (
              <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                <div className="flex items-center">
                  <div className="text-green-600 mr-2">
                    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                    </svg>
                  </div>
                  <p className="text-sm text-green-700">
                    Pet {mode === 'create' ? 'created' : 'updated'} successfully! Redirecting...
                  </p>
                </div>
              </div>
            )}

            {/* Submit Button */}
            <div className="flex justify-end space-x-4 pt-6 border-t border-gray-200">
              <button
                type="button"
                onClick={() => navigate(-1)}
                className="px-6 py-3 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isSubmitting}
                className={`
                  inline-flex items-center px-6 py-3 text-sm font-medium text-white rounded-lg transition-colors duration-200
                  ${isSubmitting 
                    ? 'bg-gray-400 cursor-not-allowed' 
                    : 'bg-blue-600 hover:bg-blue-700 focus:ring-2 focus:ring-blue-500'
                  }
                `}
              >
                {isSubmitting ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    {mode === 'create' ? 'Creating...' : 'Updating...'}
                  </>
                ) : (
                  <>
                    <Save className="w-4 h-4 mr-2" />
                    {mode === 'create' ? 'Create Pet' : 'Update Pet'}
                  </>
                )}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default PetForm;
