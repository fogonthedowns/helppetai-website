import React, { useState, useEffect } from 'react';
import { X, Save, AlertCircle } from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import { API_ENDPOINTS } from '../../config/api';
import { AppointmentUpdate, AppointmentType, AppointmentStatus, Appointment } from '../../types/appointment';

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

interface AppointmentEditFormProps {
  appointmentId: string;
  onClose: () => void;
  onSuccess?: () => void;
}

const AppointmentEditForm: React.FC<AppointmentEditFormProps> = ({ appointmentId, onClose, onSuccess }) => {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const [appointment, setAppointment] = useState<Appointment | null>(null);
  const [formData, setFormData] = useState<AppointmentUpdate>({
    assigned_vet_user_id: '',
    appointment_date: '',
    duration_minutes: 30,
    appointment_type: AppointmentType.CHECKUP,
    status: AppointmentStatus.SCHEDULED,
    title: '',
    description: '',
    notes: '',
    pet_ids: []
  });

  const [petOwners, setPetOwners] = useState<PetOwner[]>([]);
  const [pets, setPets] = useState<Pet[]>([]);
  const [teamMembers, setTeamMembers] = useState<TeamMember[]>([]);
  const [selectedOwnerId, setSelectedOwnerId] = useState('');

  useEffect(() => {
    fetchAppointment();
  }, [appointmentId]);

  useEffect(() => {
    if (selectedOwnerId) {
      loadPetsForOwner(selectedOwnerId);
    } else {
      setPets([]);
    }
  }, [selectedOwnerId]);

  const fetchAppointment = async () => {
    setLoading(true);
    setError(null);
    try {
      const token = localStorage.getItem('access_token');
      const baseURL = 'http://127.0.0.1:8000';

      const response = await fetch(`${baseURL}/api/v1/appointments/${appointmentId}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (!response.ok) throw new Error('Failed to fetch appointment');
      
      const data: Appointment = await response.json();
      setAppointment(data);
      
      // Convert ISO date to datetime-local format
      const localDate = new Date(data.appointment_date);
      const localDateString = localDate.toISOString().slice(0, 16);

      setFormData({
        assigned_vet_user_id: data.assigned_vet_user_id || '',
        appointment_date: localDateString,
        duration_minutes: data.duration_minutes,
        appointment_type: data.appointment_type,
        status: data.status,
        title: data.title,
        description: data.description || '',
        notes: data.notes || '',
        pet_ids: data.pets.map(p => p.id)
      });

      setSelectedOwnerId(data.pet_owner_id);

      // Load pet owners
      const petOwnersRes = await fetch(API_ENDPOINTS.PET_OWNERS.LIST);
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

      // Load pets for the owner
      if (data.pet_owner_id) {
        await loadPetsForOwner(data.pet_owner_id);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load appointment');
    } finally {
      setLoading(false);
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
        ? [...(prev.pet_ids || []), petId]
        : (prev.pet_ids || []).filter(id => id !== petId)
    }));
  };

  // Generate dynamic title based on pet names, appointment type, and date/time
  const generateTitle = () => {
    const selectedPets = pets.filter(p => formData.pet_ids?.includes(p.id));
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
    setSaving(true);
    setError(null);

    try {
      // Generate dynamic title and convert appointment_date to ISO format
      const appointmentData: AppointmentUpdate = {
        ...formData,
        title: generateTitle(),
        appointment_date: new Date(formData.appointment_date!).toISOString()
      };

      const token = localStorage.getItem('access_token');
      const baseURL = 'http://127.0.0.1:8000';

      const response = await fetch(`${baseURL}/api/v1/appointments/${appointmentId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(appointmentData)
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Failed to update appointment');
      }

      if (onSuccess) {
        onSuccess();
      }
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update appointment');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full p-6">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
        <h2 className="text-base font-semibold text-gray-900">Edit Appointment</h2>
        <button
          onClick={onClose}
          className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded transition-colors"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Form */}
      <form onSubmit={handleSubmit} className="flex-1 overflow-y-auto p-6 space-y-5">
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-3 flex items-start space-x-2">
            <AlertCircle className="w-4 h-4 text-red-600 flex-shrink-0 mt-0.5" />
            <p className="text-sm text-red-700">{error}</p>
          </div>
        )}

        {/* Pet Owner - Display only, not editable */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Pet Owner
          </label>
          <div className="px-3 py-2 border border-gray-200 rounded-lg bg-gray-50 text-sm text-gray-700">
            {petOwners.find(o => o.uuid === selectedOwnerId)?.full_name || 'Loading...'}
          </div>
          <p className="text-xs text-gray-500 mt-1">Pet owner cannot be changed after creation</p>
        </div>

        {/* Pets Selection */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Pets <span className="text-red-500">*</span>
          </label>
          {pets.length > 0 ? (
            <div className="space-y-2">
              {pets.map((pet) => (
                <label
                  key={pet.id}
                  className="flex items-center space-x-2 p-2 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer"
                >
                  <input
                    type="checkbox"
                    checked={formData.pet_ids?.includes(pet.id) || false}
                    onChange={(e) => handlePetSelection(pet.id, e.target.checked)}
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                  <div className="flex-1">
                    <p className="text-sm font-medium text-gray-900">{pet.name}</p>
                    <p className="text-xs text-gray-500">
                      {pet.species}
                      {pet.breed && ` • ${pet.breed}`}
                    </p>
                  </div>
                </label>
              ))}
            </div>
          ) : (
            <p className="text-sm text-gray-500">No pets available for this owner</p>
          )}
        </div>

        {/* Date and Time */}
        <div>
          <label htmlFor="appointment_date" className="block text-sm font-medium text-gray-700 mb-1">
            Date & Time <span className="text-red-500">*</span>
          </label>
          <input
            type="datetime-local"
            id="appointment_date"
            name="appointment_date"
            value={formData.appointment_date}
            onChange={handleInputChange}
            required
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
          />
        </div>

        {/* Duration */}
        <div>
          <label htmlFor="duration_minutes" className="block text-sm font-medium text-gray-700 mb-1">
            Duration (minutes) <span className="text-red-500">*</span>
          </label>
          <select
            id="duration_minutes"
            name="duration_minutes"
            value={formData.duration_minutes}
            onChange={handleInputChange}
            required
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
          >
            <option value={15}>15 minutes</option>
            <option value={30}>30 minutes</option>
            <option value={45}>45 minutes</option>
            <option value={60}>60 minutes</option>
            <option value={90}>90 minutes</option>
          </select>
        </div>

        {/* Appointment Type */}
        <div>
          <label htmlFor="appointment_type" className="block text-sm font-medium text-gray-700 mb-1">
            Type <span className="text-red-500">*</span>
          </label>
          <select
            id="appointment_type"
            name="appointment_type"
            value={formData.appointment_type}
            onChange={handleInputChange}
            required
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
          >
            <option value={AppointmentType.CHECKUP}>Check-up</option>
            <option value={AppointmentType.SURGERY}>Surgery</option>
            <option value={AppointmentType.EMERGENCY}>Emergency</option>
            <option value={AppointmentType.CONSULTATION}>Consultation</option>
          </select>
        </div>

        {/* Status */}
        <div>
          <label htmlFor="status" className="block text-sm font-medium text-gray-700 mb-1">
            Status <span className="text-red-500">*</span>
          </label>
          <select
            id="status"
            name="status"
            value={formData.status}
            onChange={handleInputChange}
            required
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
          >
            <option value={AppointmentStatus.SCHEDULED}>Scheduled</option>
            <option value={AppointmentStatus.CONFIRMED}>Confirmed</option>
            <option value={AppointmentStatus.IN_PROGRESS}>In Progress</option>
            <option value={AppointmentStatus.COMPLETE}>Complete</option>
            <option value={AppointmentStatus.CANCELLED}>Cancelled</option>
            <option value={AppointmentStatus.NO_SHOW}>No Show</option>
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
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
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
          <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-1">
            Description
          </label>
          <textarea
            id="description"
            name="description"
            value={formData.description}
            onChange={handleInputChange}
            rows={3}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
            placeholder="Brief description of the appointment..."
          />
        </div>

        {/* Notes */}
        <div>
          <label htmlFor="notes" className="block text-sm font-medium text-gray-700 mb-1">
            Internal Notes
          </label>
          <textarea
            id="notes"
            name="notes"
            value={formData.notes}
            onChange={handleInputChange}
            rows={3}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
            placeholder="Internal notes (not visible to pet owner)..."
          />
        </div>
      </form>

      {/* Footer */}
      <div className="px-6 py-4 border-t border-gray-200 flex justify-end space-x-3">
        <button
          type="button"
          onClick={onClose}
          className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
        >
          Cancel
        </button>
        <button
          type="submit"
          onClick={handleSubmit}
          disabled={saving}
          className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
        >
          {saving ? (
            <>
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
              <span>Saving...</span>
            </>
          ) : (
            <>
              <Save className="w-4 h-4" />
              <span>Save Changes</span>
            </>
          )}
        </button>
      </div>
    </div>
  );
};

export default AppointmentEditForm;

