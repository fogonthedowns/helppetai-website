import React, { useState, useEffect } from 'react';
import { X, Save, AlertCircle } from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import { API_ENDPOINTS } from '../../config/api';
import { AppointmentCreate, AppointmentType } from '../../types/appointment';

interface Practice {
  uuid: string;
  name: string;
}

interface PetOwner {
  uuid: string;
  full_name: string;
  email?: string;
  phone?: string;
}

interface Pet {
  id: string;
  name: string;
  species: string;
  breed?: string;
}

interface TeamMember {
  id: string;
  email: string;
  full_name?: string;
  role: string;
}

interface AppointmentCreateFormProps {
  onClose: () => void;
  onSuccess?: () => void;
}

const AppointmentCreateForm: React.FC<AppointmentCreateFormProps> = ({ onClose, onSuccess }) => {
  const { user } = useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const [formData, setFormData] = useState<AppointmentCreate>({
    practice_id: user?.practice_id || '',
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

  const [practices, setPractices] = useState<Practice[]>([]);
  const [petOwners, setPetOwners] = useState<PetOwner[]>([]);
  const [pets, setPets] = useState<Pet[]>([]);
  const [teamMembers, setTeamMembers] = useState<TeamMember[]>([]);

  useEffect(() => {
    loadInitialData();
  }, []);

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
      const token = localStorage.getItem('access_token');
      const baseURL = 'http://127.0.0.1:8000';

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
        setPetOwners(petOwnersData);
      }

      // Load team members
      if (user?.practice_id) {
        const teamRes = await fetch(`${baseURL}/api/v1/practices/${user.practice_id}/members`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        if (teamRes.ok) {
          const teamData = await teamRes.json();
          setTeamMembers(teamData);
        }
      }
    } catch (err) {
      console.error('Error loading initial data:', err);
      setError('Failed to load form data');
    }
  };

  const loadPetsForOwner = async (ownerId: string) => {
    try {
      const response = await fetch(API_ENDPOINTS.PETS.BY_OWNER(ownerId));
      if (response.ok) {
        const petsData = await response.json();
        setPets(petsData);
      } else {
        setPets([]);
      }
    } catch (err) {
      console.error('Error loading pets:', err);
      setPets([]);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
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

  // Generate dynamic title based on pet names, appointment type, and date/time
  const generateTitle = () => {
    const selectedPets = pets.filter(p => formData.pet_ids.includes(p.id));
    const petNames = selectedPets.map(p => p.name).join(', ') || 'Pet';
    
    const appointmentTypeLabel = formData.appointment_type 
      ? formData.appointment_type.charAt(0).toUpperCase() + formData.appointment_type.slice(1)
      : 'Appointment';
    
    let dateTimeStr = '';
    if (formData.appointment_date) {
      const date = new Date(formData.appointment_date);
      const dateStr = date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
      const timeStr = date.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' });
      dateTimeStr = ` - ${dateStr} at ${timeStr}`;
    }
    
    return `${petNames} ${appointmentTypeLabel}${dateTimeStr}`;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      // Generate dynamic title and convert appointment_date to ISO format
      const appointmentData = {
        ...formData,
        title: generateTitle(),
        appointment_date: new Date(formData.appointment_date).toISOString()
      };

      const response = await fetch(API_ENDPOINTS.APPOINTMENTS.CREATE, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(appointmentData)
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to create appointment');
      }

      onSuccess?.();
      onClose();
    } catch (err) {
      console.error('Error creating appointment:', err);
      setError(err instanceof Error ? err.message : 'Failed to create appointment');
    } finally {
      setLoading(false);
    }
  };

  const formatDateTimeForInput = (date: Date) => {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    return `${year}-${month}-${day}T${hours}:${minutes}`;
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200">
        <h2 className="text-base font-semibold text-gray-900">Schedule New Appointment</h2>
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
          <p className="text-sm text-red-800">{error}</p>
        </div>
      )}

      {/* Form Content */}
      <form onSubmit={handleSubmit} className="flex-1 overflow-y-auto p-4 space-y-4">
        {/* Practice Selection */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Practice *
          </label>
          <select
            name="practice_id"
            value={formData.practice_id}
            onChange={handleInputChange}
            required
            className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="">Select a practice</option>
            {practices.map(practice => (
              <option key={practice.uuid} value={practice.uuid}>
                {practice.name}
              </option>
            ))}
          </select>
        </div>

        {/* Pet Owner Selection */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Pet Owner *
          </label>
          <select
            name="pet_owner_id"
            value={formData.pet_owner_id}
            onChange={handleInputChange}
            required
            className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="">Select pet owner</option>
            {petOwners.map(owner => (
              <option key={owner.uuid} value={owner.uuid}>
                {owner.full_name} {owner.email && `(${owner.email})`}
              </option>
            ))}
          </select>
        </div>

        {/* Pet Selection */}
        {pets.length > 0 && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Select Pets *
            </label>
            <div className="space-y-2">
              {pets.map(pet => (
                <label key={pet.id} className="flex items-center">
                  <input
                    type="checkbox"
                    checked={formData.pet_ids.includes(pet.id)}
                    onChange={(e) => handlePetSelection(pet.id, e.target.checked)}
                    className="rounded border-gray-300 text-blue-600 focus:ring-1 focus:ring-blue-500"
                  />
                  <span className="ml-2 text-sm text-gray-700">
                    {pet.name} ({pet.species}{pet.breed ? `, ${pet.breed}` : ''})
                  </span>
                </label>
              ))}
            </div>
          </div>
        )}

        {/* Date & Time */}
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Date & Time *
            </label>
            <input
              type="datetime-local"
              name="appointment_date"
              value={formData.appointment_date}
              onChange={handleInputChange}
              required
              className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Duration (minutes) *
            </label>
            <select
              name="duration_minutes"
              value={formData.duration_minutes}
              onChange={handleInputChange}
              required
              className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="15">15 minutes</option>
              <option value="30">30 minutes</option>
              <option value="45">45 minutes</option>
              <option value="60">60 minutes</option>
              <option value="90">90 minutes</option>
            </select>
          </div>
        </div>

        {/* Appointment Type */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Appointment Type *
          </label>
          <select
            name="appointment_type"
            value={formData.appointment_type}
            onChange={handleInputChange}
            required
            className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
          >
            <option value={AppointmentType.CHECKUP}>Checkup</option>
            <option value={AppointmentType.EMERGENCY}>Emergency</option>
            <option value={AppointmentType.SURGERY}>Surgery</option>
            <option value={AppointmentType.CONSULTATION}>Consultation</option>
          </select>
        </div>

        {/* Assigned Vet */}
        <div>
          <label htmlFor="assigned_vet_user_id" className="block text-sm font-medium text-gray-700 mb-1">
            Assigned Veterinarian
          </label>
          <select
            id="assigned_vet_user_id"
            name="assigned_vet_user_id"
            value={formData.assigned_vet_user_id}
            onChange={handleInputChange}
            className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="">Unassigned</option>
            {teamMembers.map((member) => (
              <option key={member.id} value={member.id}>
                {member.full_name || member.email} ({member.role})
              </option>
            ))}
          </select>
        </div>

        {/* Description */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Description
          </label>
          <textarea
            name="description"
            value={formData.description}
            onChange={handleInputChange}
            rows={2}
            placeholder="Appointment details..."
            className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
          />
        </div>

        {/* Notes */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Internal Notes
          </label>
          <textarea
            name="notes"
            value={formData.notes}
            onChange={handleInputChange}
            rows={2}
            placeholder="Private notes (not visible to pet owner)..."
            className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
          />
        </div>
      </form>

      {/* Footer */}
      <div className="px-4 py-3 border-t border-gray-200 flex justify-end gap-2">
        <button
          type="button"
          onClick={onClose}
          disabled={loading}
          className="px-3 py-1.5 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded hover:bg-gray-50 transition-colors disabled:opacity-50"
        >
          Cancel
        </button>
        <button
          onClick={handleSubmit}
          disabled={loading || !formData.practice_id || !formData.pet_owner_id || formData.pet_ids.length === 0}
          className="px-3 py-1.5 text-sm font-medium text-white bg-blue-600 rounded hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1"
        >
          <Save className="w-3.5 h-3.5" />
          {loading ? 'Creating...' : 'Create Appointment'}
        </button>
      </div>
    </div>
  );
};

export default AppointmentCreateForm;

