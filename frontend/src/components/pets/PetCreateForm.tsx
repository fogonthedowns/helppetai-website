import React, { useState } from 'react';
import { X, Save, AlertCircle } from 'lucide-react';
import { PetFormData, PetCreateRequest, PET_SPECIES_OPTIONS, PET_GENDER_OPTIONS } from '../../types/pet';
import { API_ENDPOINTS } from '../../config/api';

interface PetCreateFormProps {
  onClose: () => void;
  onSuccess?: () => void;
  ownerUuid: string;
}

const PetCreateForm: React.FC<PetCreateFormProps> = ({ onClose, onSuccess, ownerUuid }) => {
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

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.name || !formData.species) {
      setError('Pet name and species are required');
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      const token = localStorage.getItem('access_token');
      const createData: PetCreateRequest = {
        owner_id: ownerUuid,
        name: formData.name,
        species: formData.species,
        breed: formData.breed || undefined,
        color: formData.color || undefined,
        gender: formData.gender || undefined,
        weight: formData.weight,
        date_of_birth: formData.date_of_birth || undefined,
        microchip_id: formData.microchip_id || undefined,
        spayed_neutered: formData.spayed_neutered,
        allergies: formData.allergies || undefined,
        medications: formData.medications || undefined,
        medical_notes: formData.medical_notes || undefined,
        emergency_contact: formData.emergency_contact || undefined,
        emergency_phone: formData.emergency_phone || undefined
      };

      const response = await fetch(API_ENDPOINTS.PETS.CREATE, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(createData)
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => null);
        throw new Error(errorData?.detail || 'Failed to create pet');
      }

      if (onSuccess) onSuccess();
      onClose();
    } catch (err) {
      console.error('Error creating pet:', err);
      setError(err instanceof Error ? err.message : 'Failed to create pet');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleChange = (field: keyof PetFormData, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200">
        <h2 className="text-sm font-semibold text-gray-900">Add New Pet</h2>
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

      {/* Form */}
      <form onSubmit={handleSubmit} className="flex-1 overflow-y-auto p-4 space-y-4">
        {/* Basic Information */}
        <section>
          <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
            Basic Information
          </h3>
          <div className="space-y-2">
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">
                Pet Name *
              </label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => handleChange('name', e.target.value)}
                className="w-full px-2 py-1.5 text-xs border border-gray-300 rounded focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
                required
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">
                Species *
              </label>
              <select
                value={formData.species}
                onChange={(e) => handleChange('species', e.target.value)}
                className="w-full px-2 py-1.5 text-xs border border-gray-300 rounded focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
                required
              >
                <option value="">Select species</option>
                {PET_SPECIES_OPTIONS.map(option => (
                  <option key={option} value={option}>{option}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">
                Breed
              </label>
              <input
                type="text"
                value={formData.breed}
                onChange={(e) => handleChange('breed', e.target.value)}
                className="w-full px-2 py-1.5 text-xs border border-gray-300 rounded focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>

            <div className="grid grid-cols-2 gap-2">
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">
                  Color
                </label>
                <input
                  type="text"
                  value={formData.color}
                  onChange={(e) => handleChange('color', e.target.value)}
                  className="w-full px-2 py-1.5 text-xs border border-gray-300 rounded focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">
                  Gender
                </label>
                <select
                  value={formData.gender}
                  onChange={(e) => handleChange('gender', e.target.value)}
                  className="w-full px-2 py-1.5 text-xs border border-gray-300 rounded focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="">Select gender</option>
                  {PET_GENDER_OPTIONS.map(option => (
                    <option key={option} value={option}>{option}</option>
                  ))}
                </select>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-2">
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">
                  Weight (lbs)
                </label>
                <input
                  type="number"
                  step="0.1"
                  value={formData.weight || ''}
                  onChange={(e) => handleChange('weight', e.target.value ? parseFloat(e.target.value) : undefined)}
                  className="w-full px-2 py-1.5 text-xs border border-gray-300 rounded focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">
                  Date of Birth
                </label>
                <input
                  type="date"
                  value={formData.date_of_birth}
                  onChange={(e) => handleChange('date_of_birth', e.target.value)}
                  className="w-full px-2 py-1.5 text-xs border border-gray-300 rounded focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
            </div>
          </div>
        </section>

        {/* Medical Information */}
        <section>
          <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
            Medical Information
          </h3>
          <div className="space-y-2">
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">
                Microchip ID
              </label>
              <input
                type="text"
                value={formData.microchip_id}
                onChange={(e) => handleChange('microchip_id', e.target.value)}
                className="w-full px-2 py-1.5 text-xs border border-gray-300 rounded focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>

            <div>
              <label className="flex items-center gap-2 text-xs font-medium text-gray-700">
                <input
                  type="checkbox"
                  checked={formData.spayed_neutered || false}
                  onChange={(e) => handleChange('spayed_neutered', e.target.checked)}
                  className="rounded border-gray-300 text-blue-600 focus:ring-1 focus:ring-blue-500"
                />
                Spayed/Neutered
              </label>
            </div>

            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">
                Allergies
              </label>
              <textarea
                value={formData.allergies}
                onChange={(e) => handleChange('allergies', e.target.value)}
                rows={2}
                className="w-full px-2 py-1.5 text-xs border border-gray-300 rounded focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">
                Current Medications
              </label>
              <textarea
                value={formData.medications}
                onChange={(e) => handleChange('medications', e.target.value)}
                rows={2}
                className="w-full px-2 py-1.5 text-xs border border-gray-300 rounded focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">
                Medical Notes
              </label>
              <textarea
                value={formData.medical_notes}
                onChange={(e) => handleChange('medical_notes', e.target.value)}
                rows={2}
                className="w-full px-2 py-1.5 text-xs border border-gray-300 rounded focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
          </div>
        </section>

        {/* Emergency Contact */}
        <section>
          <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
            Emergency Contact
          </h3>
          <div className="space-y-2">
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">
                Emergency Contact Name
              </label>
              <input
                type="text"
                value={formData.emergency_contact}
                onChange={(e) => handleChange('emergency_contact', e.target.value)}
                className="w-full px-2 py-1.5 text-xs border border-gray-300 rounded focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">
                Emergency Phone
              </label>
              <input
                type="tel"
                value={formData.emergency_phone}
                onChange={(e) => handleChange('emergency_phone', e.target.value)}
                className="w-full px-2 py-1.5 text-xs border border-gray-300 rounded focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
              />
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
          {isSubmitting ? 'Creating...' : 'Create Pet'}
        </button>
      </div>
    </div>
  );
};

export default PetCreateForm;

