import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { ArrowLeft, Save, Calendar, Stethoscope, DollarSign, Weight, Thermometer } from 'lucide-react';
import { 
  MedicalRecordFormData, 
  MedicalRecordCreateRequest,
  MedicalRecordUpdateRequest,
  MedicalRecord,
  MEDICAL_RECORD_TYPES,
  MEDICAL_RECORD_TYPE_LABELS,
  MEDICAL_DATA_TEMPLATES
} from '../../types/medicalRecord';
import { PetWithOwner } from '../../types/pet';
import { API_ENDPOINTS } from '../../config/api';
import { useAuth } from '../../contexts/AuthContext';
import { getAuthHeaders } from '../../utils/authUtils';

interface MedicalRecordFormProps {
  mode: 'create' | 'edit';
}

const MedicalRecordForm: React.FC<MedicalRecordFormProps> = ({ mode }) => {
  const navigate = useNavigate();
  const { petId, recordId } = useParams<{ petId: string; recordId?: string }>();
  const { user } = useAuth();

  const [pet, setPet] = useState<PetWithOwner | null>(null);
  const [existingRecord, setExistingRecord] = useState<MedicalRecord | null>(null);
  const [loading, setLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [formData, setFormData] = useState<MedicalRecordFormData>({
    record_type: 'checkup',
    title: '',
    description: '',
    medical_data: {},
    visit_date: new Date().toISOString().slice(0, 16), // YYYY-MM-DDTHH:MM format
    veterinarian_name: user?.full_name || '',
    clinic_name: '',
    diagnosis: '',
    treatment: '',
    medications: '',
    follow_up_required: false,
    follow_up_date: '',
    weight: undefined,
    temperature: undefined,
    cost: undefined
  });

  useEffect(() => {
    if (petId) {
      fetchPet();
    }
    if (mode === 'edit' && recordId) {
      fetchExistingRecord();
    } else {
      setLoading(false);
    }
  }, [petId, recordId, mode]);

  useEffect(() => {
    // Update medical data template when record type changes
    if (formData.record_type && MEDICAL_DATA_TEMPLATES[formData.record_type]) {
      setFormData(prev => ({
        ...prev,
        medical_data: { ...MEDICAL_DATA_TEMPLATES[formData.record_type] }
      }));
    }
  }, [formData.record_type]);

  const fetchPet = async () => {
    if (!petId) return;

    try {
             const response = await fetch(API_ENDPOINTS.PETS.GET(petId), {
         headers: getAuthHeaders()
       });
      
      if (!response.ok) {
        throw new Error('Failed to fetch pet information');
      }

      const petData = await response.json();
      setPet(petData);
    } catch (err) {
      console.error('Error fetching pet:', err);
      setError(err instanceof Error ? err.message : 'Failed to load pet information');
    }
  };

  const fetchExistingRecord = async () => {
    if (!recordId) return;

    try {
             const response = await fetch(API_ENDPOINTS.MEDICAL_RECORDS.GET(recordId), {
         headers: getAuthHeaders()
       });
      
      if (!response.ok) {
        throw new Error('Failed to fetch medical record');
      }

      const recordData = await response.json();
      setExistingRecord(recordData);
      
      // Populate form with existing data
      setFormData({
        record_type: recordData.record_type,
        title: recordData.title,
        description: recordData.description || '',
        medical_data: recordData.medical_data || {},
        visit_date: recordData.visit_date.slice(0, 16), // Convert to datetime-local format
        veterinarian_name: recordData.veterinarian_name || '',
        clinic_name: recordData.clinic_name || '',
        diagnosis: recordData.diagnosis || '',
        treatment: recordData.treatment || '',
        medications: recordData.medications || '',
        follow_up_required: recordData.follow_up_required,
        follow_up_date: recordData.follow_up_date ? recordData.follow_up_date.slice(0, 16) : '',
        weight: recordData.weight,
        temperature: recordData.temperature,
        cost: recordData.cost
      });
    } catch (err) {
      console.error('Error fetching medical record:', err);
      setError(err instanceof Error ? err.message : 'Failed to load medical record');
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target;
    
    if (type === 'checkbox') {
      const checked = (e.target as HTMLInputElement).checked;
      setFormData(prev => ({ ...prev, [name]: checked }));
    } else if (type === 'number') {
      const numValue = value === '' ? undefined : parseFloat(value);
      setFormData(prev => ({ ...prev, [name]: numValue }));
    } else {
      setFormData(prev => ({ ...prev, [name]: value }));
    }
  };

  const handleMedicalDataChange = (field: string, value: string) => {
    setFormData(prev => ({
      ...prev,
      medical_data: {
        ...prev.medical_data,
        [field]: value
      }
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (isSubmitting) return;

    // Validation
    if (!formData.title.trim()) {
      setError('Title is required');
      return;
    }

    if (!formData.visit_date) {
      setError('Visit date is required');
      return;
    }

    try {
      setIsSubmitting(true);
      setError(null);

      const submitData = {
        ...formData,
        visit_date: new Date(formData.visit_date).toISOString(),
        follow_up_date: formData.follow_up_date ? new Date(formData.follow_up_date).toISOString() : undefined
      };

      let response;
      
      if (mode === 'create') {
        const createData: MedicalRecordCreateRequest = {
          ...submitData,
          pet_id: petId!
        };
        
        response = await fetch(API_ENDPOINTS.MEDICAL_RECORDS.CREATE, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            ...getAuthHeaders()
          },
          body: JSON.stringify(createData)
        });
      } else {
        const updateData: MedicalRecordUpdateRequest = submitData;
        
        response = await fetch(API_ENDPOINTS.MEDICAL_RECORDS.UPDATE(recordId!), {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            ...getAuthHeaders()
          },
          body: JSON.stringify(updateData)
        });
      }

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Failed to ${mode} medical record`);
      }

      // Navigate back to pet detail page
      navigate(`/pets/${petId}`);
    } catch (err) {
      console.error(`Error ${mode === 'create' ? 'creating' : 'updating'} medical record:`, err);
      setError(err instanceof Error ? err.message : `Failed to ${mode} medical record`);
    } finally {
      setIsSubmitting(false);
    }
  };

  const canSubmit = () => {
    return user?.role === 'ADMIN' || user?.role === 'VET_STAFF';
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span className="ml-2 text-gray-600">Loading...</span>
      </div>
    );
  }

  if (!canSubmit()) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Access Denied</h2>
          <p className="text-gray-600">Only veterinarians and administrators can manage medical records.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <button
            onClick={() => navigate(`/pets/${petId}`)}
            className="inline-flex items-center text-gray-600 hover:text-gray-900 mb-4"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to {pet?.name || 'Pet'}
          </button>
          
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">
                {mode === 'create' ? 'Add Medical Record' : 'Edit Medical Record'}
              </h1>
              {pet && (
                <p className="text-gray-600 mt-1">
                  for {pet.name} ({pet.species})
                </p>
              )}
            </div>
          </div>
        </div>

        {error && (
          <div className="mb-6 bg-red-50 border border-red-200 rounded-lg p-4">
            <p className="text-sm text-red-700">{error}</p>
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="bg-white shadow-sm rounded-lg p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-6 flex items-center">
              <Stethoscope className="w-5 h-5 mr-2 text-blue-600" />
              Record Information
            </h2>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Record Type */}
              <div>
                <label htmlFor="record_type" className="block text-sm font-medium text-gray-700 mb-2">
                  Record Type *
                </label>
                <select
                  id="record_type"
                  name="record_type"
                  value={formData.record_type}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  required
                >
                  {MEDICAL_RECORD_TYPES.map(type => (
                    <option key={type} value={type}>
                      {MEDICAL_RECORD_TYPE_LABELS[type]}
                    </option>
                  ))}
                </select>
              </div>

              {/* Visit Date */}
              <div>
                <label htmlFor="visit_date" className="block text-sm font-medium text-gray-700 mb-2">
                  <Calendar className="w-4 h-4 inline mr-1" />
                  Visit Date & Time *
                </label>
                <input
                  type="datetime-local"
                  id="visit_date"
                  name="visit_date"
                  value={formData.visit_date}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  required
                />
              </div>

              {/* Title */}
              <div className="md:col-span-2">
                <label htmlFor="title" className="block text-sm font-medium text-gray-700 mb-2">
                  Title *
                </label>
                <input
                  type="text"
                  id="title"
                  name="title"
                  value={formData.title}
                  onChange={handleInputChange}
                  placeholder="e.g., Annual Checkup, Vaccination - Rabies, Emergency Visit"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  required
                />
              </div>

              {/* Veterinarian Name */}
              <div>
                <label htmlFor="veterinarian_name" className="block text-sm font-medium text-gray-700 mb-2">
                  Veterinarian
                </label>
                <input
                  type="text"
                  id="veterinarian_name"
                  name="veterinarian_name"
                  value={formData.veterinarian_name}
                  onChange={handleInputChange}
                  placeholder="Dr. Smith"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              {/* Clinic Name */}
              <div>
                <label htmlFor="clinic_name" className="block text-sm font-medium text-gray-700 mb-2">
                  Clinic/Hospital
                </label>
                <input
                  type="text"
                  id="clinic_name"
                  name="clinic_name"
                  value={formData.clinic_name}
                  onChange={handleInputChange}
                  placeholder="Animal Hospital Name"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
            </div>

            {/* Description */}
            <div className="mt-6">
              <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-2">
                Description
              </label>
              <textarea
                id="description"
                name="description"
                value={formData.description}
                onChange={handleInputChange}
                rows={3}
                placeholder="Brief description of the visit..."
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
          </div>

          {/* Medical Details */}
          <div className="bg-white shadow-sm rounded-lg p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-6">Medical Details</h2>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Weight */}
              <div>
                <label htmlFor="weight" className="block text-sm font-medium text-gray-700 mb-2">
                  <Weight className="w-4 h-4 inline mr-1" />
                  Weight (lbs)
                </label>
                <input
                  type="number"
                  id="weight"
                  name="weight"
                  value={formData.weight || ''}
                  onChange={handleInputChange}
                  step="0.1"
                  min="0"
                  placeholder="0.0"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              {/* Temperature */}
              <div>
                <label htmlFor="temperature" className="block text-sm font-medium text-gray-700 mb-2">
                  <Thermometer className="w-4 h-4 inline mr-1" />
                  Temperature (°F)
                </label>
                <input
                  type="number"
                  id="temperature"
                  name="temperature"
                  value={formData.temperature || ''}
                  onChange={handleInputChange}
                  step="0.1"
                  min="90"
                  max="110"
                  placeholder="101.5"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              {/* Cost */}
              <div>
                <label htmlFor="cost" className="block text-sm font-medium text-gray-700 mb-2">
                  <DollarSign className="w-4 h-4 inline mr-1" />
                  Cost ($)
                </label>
                <input
                  type="number"
                  id="cost"
                  name="cost"
                  value={formData.cost || ''}
                  onChange={handleInputChange}
                  step="0.01"
                  min="0"
                  placeholder="0.00"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
            </div>

            {/* Diagnosis */}
            <div className="mt-6">
              <label htmlFor="diagnosis" className="block text-sm font-medium text-gray-700 mb-2">
                Diagnosis
              </label>
              <textarea
                id="diagnosis"
                name="diagnosis"
                value={formData.diagnosis}
                onChange={handleInputChange}
                rows={3}
                placeholder="Clinical diagnosis and findings..."
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>

            {/* Treatment */}
            <div className="mt-6">
              <label htmlFor="treatment" className="block text-sm font-medium text-gray-700 mb-2">
                Treatment
              </label>
              <textarea
                id="treatment"
                name="treatment"
                value={formData.treatment}
                onChange={handleInputChange}
                rows={3}
                placeholder="Treatment provided and procedures performed..."
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>

            {/* Medications */}
            <div className="mt-6">
              <label htmlFor="medications" className="block text-sm font-medium text-gray-700 mb-2">
                Medications
              </label>
              <textarea
                id="medications"
                name="medications"
                value={formData.medications}
                onChange={handleInputChange}
                rows={2}
                placeholder="Medications prescribed with dosage and instructions..."
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
          </div>

          {/* Follow-up */}
          <div className="bg-white shadow-sm rounded-lg p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-6">Follow-up</h2>

            <div className="space-y-4">
              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="follow_up_required"
                  name="follow_up_required"
                  checked={formData.follow_up_required}
                  onChange={handleInputChange}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <label htmlFor="follow_up_required" className="ml-2 block text-sm text-gray-900">
                  Follow-up appointment required
                </label>
              </div>

              {formData.follow_up_required && (
                <div>
                  <label htmlFor="follow_up_date" className="block text-sm font-medium text-gray-700 mb-2">
                    Follow-up Date
                  </label>
                  <input
                    type="datetime-local"
                    id="follow_up_date"
                    name="follow_up_date"
                    value={formData.follow_up_date}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
              )}
            </div>
          </div>

          {/* Medical Data (Type-specific fields) */}
          {formData.medical_data && Object.keys(formData.medical_data).length > 0 && (
            <div className="bg-white shadow-sm rounded-lg p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-6">
                {MEDICAL_RECORD_TYPE_LABELS[formData.record_type as keyof typeof MEDICAL_RECORD_TYPE_LABELS]} Details
              </h2>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {Object.entries(formData.medical_data).map(([field, value]) => (
                  <div key={field}>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      {field.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                    </label>
                    <input
                      type="text"
                      value={value as string}
                      onChange={(e) => handleMedicalDataChange(field, e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Submit Button */}
          <div className="flex justify-end space-x-4">
            <button
              type="button"
              onClick={() => navigate(`/pets/${petId}`)}
              className="px-6 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="inline-flex items-center px-6 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-md disabled:opacity-50"
            >
              <Save className="w-4 h-4 mr-2" />
              {isSubmitting ? 'Saving...' : mode === 'create' ? 'Create Record' : 'Update Record'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default MedicalRecordForm;