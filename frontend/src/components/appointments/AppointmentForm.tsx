import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { API_ENDPOINTS } from '../../config/api';
import { AppointmentCreate, AppointmentType } from '../../types/appointment';

interface Practice {
  uuid: string;
  name: string;
  admin_user_id: string;
  phone?: string;
  email?: string;
  address?: string;
  license_number?: string;
  specialties: string[];
  created_at: string;
  updated_at: string;
  is_active: boolean;
}

interface PetOwner {
  uuid: string;
  full_name: string;
  email?: string;
  phone?: string;
  emergency_contact?: string;
  notifications_enabled: boolean;
  created_at: string;
  updated_at: string;
}

interface Pet {
  id: string;
  name: string;
  species: string;
  breed?: string;
}



export const AppointmentForm: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Form data
  const [formData, setFormData] = useState<AppointmentCreate>({
    practice_id: '',
    pet_owner_id: '',
    assigned_vet_user_id: user?.id || '',
    appointment_date: '',
    duration_minutes: 30,
    appointment_type: AppointmentType.CHECKUP,
    title: '',
    description: '',
    notes: '',
    pet_ids: []
  });

  // Dropdown data
  const [practices, setPractices] = useState<Practice[]>([]);
  const [petOwners, setPetOwners] = useState<PetOwner[]>([]);
  const [pets, setPets] = useState<Pet[]>([]);

  // Load initial data
  useEffect(() => {
    loadInitialData();
  }, []);

  // Load pets when pet owner changes
  useEffect(() => {
    if (formData.pet_owner_id) {
      loadPetsForOwner(formData.pet_owner_id);
    } else {
      setPets([]);
      setFormData(prev => ({ ...prev, pet_ids: [] }));
    }
  }, [formData.pet_owner_id]);

  const loadInitialData = async () => {
    try {
      const [practicesRes, petOwnersRes] = await Promise.all([
        fetch(API_ENDPOINTS.PRACTICES.LIST),
        fetch(API_ENDPOINTS.PET_OWNERS.LIST)
      ]);

      if (practicesRes.ok) {
        const practicesData = await practicesRes.json();
        setPractices(practicesData);
      }

      if (petOwnersRes.ok) {
        const petOwnersData = await petOwnersRes.json();
        console.log('Pet owners data received:', petOwnersData);
        setPetOwners(petOwnersData);
      } else {
        console.log('Pet owners API error:', await petOwnersRes.text());
      }
    } catch (err) {
      console.error('Error loading initial data:', err);
      setError('Failed to load form data');
    }
  };

  const loadPetsForOwner = async (ownerId: string) => {
    try {
      console.log('Loading pets for owner:', ownerId);
      console.log('API endpoint:', API_ENDPOINTS.PETS.BY_OWNER(ownerId));
      
      const response = await fetch(API_ENDPOINTS.PETS.BY_OWNER(ownerId));
      console.log('Pets API response status:', response.status);
      
      if (response.ok) {
        const petsData = await response.json();
        console.log('Pets data received:', petsData);
        setPets(petsData);
      } else {
        console.log('Pets API error:', await response.text());
        setPets([]); // Clear pets if API fails
      }
    } catch (err) {
      console.error('Error loading pets:', err);
      setPets([]); // Clear pets on error
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    
    if (name === 'pet_owner_id') {
      console.log('Pet owner selected:', value);
    }
    
    setFormData(prev => ({
      ...prev,
      [name]: name === 'duration_minutes' ? parseInt(value) || 0 : value
    }));
  };

  const handlePetSelection = (petId: string, checked: boolean) => {
    setFormData(prev => ({
      ...prev,
      pet_ids: checked 
        ? [...prev.pet_ids, petId]
        : prev.pet_ids.filter(id => id !== petId)
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(API_ENDPOINTS.APPOINTMENTS.CREATE, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData)
      });

      if (response.ok) {
        navigate('/dashboard/vet');
      } else {
        const errorData = await response.json();
        setError(errorData.message || 'Failed to create appointment');
      }
    } catch (err) {
      setError('Network error. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const formatDateTimeForInput = () => {
    const now = new Date();
    const year = now.getFullYear();
    const month = String(now.getMonth() + 1).padStart(2, '0');
    const day = String(now.getDate()).padStart(2, '0');
    const hours = String(now.getHours()).padStart(2, '0');
    const minutes = String(now.getMinutes()).padStart(2, '0');
    return `${year}-${month}-${day}T${hours}:${minutes}`;
  };

  return (
    <div className="max-w-4xl mx-auto px-6 py-8">
      <div className="bg-white rounded-xl shadow-sm border border-gray-200">
        <div className="px-6 py-4 border-b border-gray-200">
          <h1 className="text-2xl font-bold text-gray-900">Schedule New Appointment</h1>
          <p className="text-gray-600 mt-1">Create a new appointment for a pet owner</p>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <p className="text-red-800">{error}</p>
            </div>
          )}

          {/* Basic Information */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Practice *
              </label>
              <select
                name="practice_id"
                value={formData.practice_id}
                onChange={handleInputChange}
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="">
                  {practices.length === 0 ? 'No practices available - create one first' : 'Select a practice'}
                </option>
                {practices.map(practice => (
                  <option key={practice.uuid} value={practice.uuid}>
                    {practice.name}
                  </option>
                ))}
              </select>
              {practices.length === 0 && (
                <p className="text-sm text-red-600 mt-1">
                  No practices found. <a href="/practices/new" className="text-blue-600 hover:underline">Create a practice first</a>.
                </p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Pet Owner *
              </label>
              <select
                name="pet_owner_id"
                value={formData.pet_owner_id}
                onChange={handleInputChange}
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="">
                  {petOwners.length === 0 ? 'No pet owners available - create one first' : 'Select a pet owner'}
                </option>
                {petOwners.map(owner => (
                  <option key={owner.uuid} value={owner.uuid}>
                    {owner.full_name} {owner.email ? `(${owner.email})` : ''}
                  </option>
                ))}
              </select>
              {petOwners.length === 0 && (
                <p className="text-sm text-red-600 mt-1">
                  No pet owners found. <a href="/pet_owners/new" className="text-blue-600 hover:underline">Create a pet owner first</a>.
                </p>
              )}
            </div>
          </div>

          {/* Appointment Details */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Appointment Date & Time *
              </label>
              <input
                type="datetime-local"
                name="appointment_date"
                value={formData.appointment_date}
                onChange={handleInputChange}
                min={formatDateTimeForInput()}
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Duration (minutes)
              </label>
              <select
                name="duration_minutes"
                value={formData.duration_minutes}
                onChange={handleInputChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value={15}>15 minutes</option>
                <option value={30}>30 minutes</option>
                <option value={45}>45 minutes</option>
                <option value={60}>1 hour</option>
                <option value={90}>1.5 hours</option>
                <option value={120}>2 hours</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Appointment Type
              </label>
              <select
                name="appointment_type"
                value={formData.appointment_type}
                onChange={handleInputChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value={AppointmentType.CHECKUP}>Checkup</option>
                <option value={AppointmentType.EMERGENCY}>Emergency</option>
                <option value={AppointmentType.SURGERY}>Surgery</option>
                <option value={AppointmentType.CONSULTATION}>Consultation</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Assigned Veterinarian
              </label>
              <input
                type="text"
                value={`Dr. ${user?.full_name} (You)`}
                disabled
                className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-gray-50 text-gray-600"
              />
              <p className="text-sm text-gray-500 mt-1">Appointments are automatically assigned to you</p>
            </div>
          </div>

          {/* Title and Description */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Appointment Title *
            </label>
            <input
              type="text"
              name="title"
              value={formData.title}
              onChange={handleInputChange}
              required
              placeholder="e.g., Annual Checkup - Fluffy"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Description
            </label>
            <textarea
              name="description"
              value={formData.description}
              onChange={handleInputChange}
              rows={3}
              placeholder="Additional details about the appointment..."
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          {/* Pet Selection */}
          {formData.pet_owner_id && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Select Pets for Appointment *
              </label>
              {pets.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                  {pets.map(pet => (
                    <label key={pet.id} className="flex items-center p-3 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={formData.pet_ids.includes(pet.id)}
                        onChange={(e) => handlePetSelection(pet.id, e.target.checked)}
                        className="mr-3 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                      />
                      <div>
                        <div className="font-medium text-gray-900">{pet.name}</div>
                        <div className="text-sm text-gray-500">{pet.species} {pet.breed && `• ${pet.breed}`}</div>
                      </div>
                    </label>
                  ))}
                </div>
              ) : (
                <div className="p-4 border border-gray-200 rounded-lg bg-gray-50">
                  <p className="text-gray-600">No pets found for this pet owner.</p>
                  <p className="text-sm text-gray-500 mt-1">
                    The selected pet owner doesn't have any pets registered. 
                    <a href={`/pet_owners/${formData.pet_owner_id}`} className="text-blue-600 hover:underline ml-1">
                      Add pets to this owner first
                    </a>.
                  </p>
                </div>
              )}
            </div>
          )}

          {/* Notes */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Internal Notes
            </label>
            <textarea
              name="notes"
              value={formData.notes}
              onChange={handleInputChange}
              rows={3}
              placeholder="Internal notes for staff..."
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          {/* Submit Buttons */}
          <div className="flex justify-end space-x-4 pt-6 border-t border-gray-200">
            <button
              type="button"
              onClick={() => navigate('/dashboard/vet')}
              className="px-6 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading || formData.pet_ids.length === 0 || !formData.practice_id || !formData.pet_owner_id || !formData.title || !formData.appointment_date}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {loading ? 'Creating...' : 'Create Appointment'}
            </button>
          </div>
          
          {/* Helper text for disabled button */}
          {(formData.pet_ids.length === 0 || !formData.practice_id || !formData.pet_owner_id || !formData.title || !formData.appointment_date) && (
            <div className="mt-2 text-sm text-gray-500">
              {!formData.practice_id && <p>• Select a practice</p>}
              {!formData.pet_owner_id && <p>• Select a pet owner</p>}
              {formData.pet_owner_id && formData.pet_ids.length === 0 && <p>• Select at least one pet</p>}
              {!formData.title && <p>• Enter an appointment title</p>}
              {!formData.appointment_date && <p>• Choose appointment date and time</p>}
            </div>
          )}
        </form>
      </div>
    </div>
  );
};

export default AppointmentForm;
