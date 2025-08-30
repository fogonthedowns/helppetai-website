import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { Building2, Save, ArrowLeft, AlertCircle, CheckCircle } from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import { API_ENDPOINTS } from '../../config/api';
import '../../utils/authUtils'; // Import to ensure fetch interceptor is set up

interface PracticeFormData {
  name: string;
  admin_user_id: string;
  phone: string;
  email: string;
  address: string;
  license_number: string;
  specialties: string[];
}

interface PracticeFormProps {
  mode: 'create' | 'edit';
}

const PracticeForm: React.FC<PracticeFormProps> = ({ mode }) => {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const { user } = useAuth();
  
  const [formData, setFormData] = useState<PracticeFormData>({
    name: '',
    admin_user_id: user?.id || '',
    phone: '',
    email: '',
    address: '',
    license_number: '',
    specialties: []
  });

  const [specialtyInput, setSpecialtyInput] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitStatus, setSubmitStatus] = useState<'idle' | 'success' | 'error'>('idle');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  // Common specialties for quick selection
  const commonSpecialties = [
    'General Practice', 'Emergency Medicine', 'Surgery', 'Dermatology',
    'Cardiology', 'Oncology', 'Ophthalmology', 'Dentistry',
    'Exotic Animals', 'Internal Medicine', 'Neurology', 'Orthopedics'
  ];

  useEffect(() => {
    if (mode === 'edit' && id) {
      fetchPractice();
    }
  }, [mode, id]);

  const fetchPractice = async () => {
    if (!id) return;
    
    setLoading(true);
    try {
      const response = await fetch(API_ENDPOINTS.PRACTICES.GET(id));
      if (!response.ok) {
        throw new Error('Failed to fetch practice');
      }
      const practice = await response.json();
      setFormData({
        name: practice.name,
        admin_user_id: practice.admin_user_id,
        phone: practice.phone || '',
        email: practice.email || '',
        address: practice.address || '',
        license_number: practice.license_number || '',
        specialties: practice.specialties || []
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load practice');
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const addSpecialty = (specialty: string) => {
    if (specialty && !formData.specialties.includes(specialty)) {
      setFormData(prev => ({
        ...prev,
        specialties: [...prev.specialties, specialty]
      }));
    }
  };

  const removeSpecialty = (specialty: string) => {
    setFormData(prev => ({
      ...prev,
      specialties: prev.specialties.filter(s => s !== specialty)
    }));
  };

  const handleSpecialtyInput = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && specialtyInput.trim()) {
      e.preventDefault();
      addSpecialty(specialtyInput.trim());
      setSpecialtyInput('');
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setSubmitStatus('idle');
    setError(null);

    try {
      const url = mode === 'create' 
        ? API_ENDPOINTS.PRACTICES.CREATE
        : API_ENDPOINTS.PRACTICES.UPDATE(id!);
      
      const method = mode === 'create' ? 'POST' : 'PUT';

      // Clean up form data - convert empty strings to null for optional fields
      const cleanedFormData = {
        ...formData,
        license_number: formData.license_number.trim() || null,
        phone: formData.phone.trim() || null,
        email: formData.email.trim() || null,
        address: formData.address.trim() || null
      };

      console.log('Sending practice data:', cleanedFormData);

      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(cleanedFormData),
      });

      if (response.ok) {
        setSubmitStatus('success');
        setTimeout(() => {
          navigate('/practices');
        }, 1500);
      } else {
        const errorData = await response.json();
        throw new Error(errorData.detail || `Failed to ${mode} practice`);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : `Failed to ${mode} practice`);
      setSubmitStatus('error');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="w-8 h-8 border-2 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">Loading practice...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header Section */}
      <section className="bg-gradient-to-br from-blue-50 to-indigo-50 py-16">
        <div className="max-w-4xl mx-auto px-6">
          <div className="flex items-center mb-6">
            <button
              onClick={() => navigate('/practices')}
              className="mr-4 p-2 text-gray-600 hover:text-gray-900 transition-colors"
            >
              <ArrowLeft className="w-6 h-6" />
            </button>
            <div className="w-16 h-16 bg-blue-600 rounded-2xl flex items-center justify-center mr-4">
              <Building2 className="w-8 h-8 text-white" />
            </div>
            <div>
              <h1 className="text-5xl font-bold text-gray-900 mb-2" style={{
                fontFamily: 'Calibre, ui-sans-serif, system-ui, -apple-system, "system-ui", "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans", sans-serif'
              }}>
                {mode === 'create' ? 'Add New Practice' : 'Edit Practice'}
              </h1>
              <p className="text-xl text-gray-600">
                {mode === 'create' 
                  ? 'Create a new veterinary practice profile'
                  : 'Update practice information'
                }
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Form Section */}
      <section className="py-16">
        <div className="max-w-2xl mx-auto px-6">
          {/* Status Messages */}
          {submitStatus === 'success' && (
            <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg flex items-center space-x-3">
              <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0" />
              <div>
                <p className="text-green-800 font-medium">Success!</p>
                <p className="text-green-700 text-sm">
                  Practice {mode === 'create' ? 'created' : 'updated'} successfully. Redirecting...
                </p>
              </div>
            </div>
          )}

          {error && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-center space-x-3">
              <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0" />
              <div>
                <p className="text-red-800 font-medium">Error</p>
                <p className="text-red-700 text-sm">{error}</p>
              </div>
            </div>
          )}

          <form onSubmit={handleSubmit} className="bg-white rounded-xl shadow-sm border border-gray-200 p-8">
            <div className="space-y-6">
              {/* Practice Name */}
              <div>
                <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-2">
                  Practice Name *
                </label>
                <input
                  type="text"
                  id="name"
                  name="name"
                  required
                  value={formData.name}
                  onChange={handleInputChange}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
                  placeholder="Enter practice name"
                />
              </div>

              {/* Contact Information */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label htmlFor="phone" className="block text-sm font-medium text-gray-700 mb-2">
                    Phone Number
                  </label>
                  <input
                    type="tel"
                    id="phone"
                    name="phone"
                    value={formData.phone}
                    onChange={handleInputChange}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
                    placeholder="(555) 123-4567"
                  />
                </div>

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
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
                    placeholder="practice@example.com"
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
                  rows={3}
                  value={formData.address}
                  onChange={handleInputChange}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors resize-none"
                  placeholder="Enter practice address"
                />
              </div>

              {/* License Number */}
              <div>
                <label htmlFor="license_number" className="block text-sm font-medium text-gray-700 mb-2">
                  License Number
                </label>
                <input
                  type="text"
                  id="license_number"
                  name="license_number"
                  value={formData.license_number}
                  onChange={handleInputChange}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
                  placeholder="Enter license number"
                />
              </div>

              {/* Specialties */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Specialties
                </label>
                
                {/* Common Specialties */}
                <div className="mb-4">
                  <p className="text-sm text-gray-600 mb-2">Quick add:</p>
                  <div className="flex flex-wrap gap-2">
                    {commonSpecialties.map((specialty) => (
                      <button
                        key={specialty}
                        type="button"
                        onClick={() => addSpecialty(specialty)}
                        disabled={formData.specialties.includes(specialty)}
                        className="px-3 py-1 text-sm border border-gray-300 rounded-full hover:bg-gray-50 disabled:bg-gray-100 disabled:text-gray-400 transition-colors"
                      >
                        {specialty}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Custom Specialty Input */}
                <input
                  type="text"
                  value={specialtyInput}
                  onChange={(e) => setSpecialtyInput(e.target.value)}
                  onKeyDown={handleSpecialtyInput}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
                  placeholder="Add custom specialty (press Enter)"
                />

                {/* Selected Specialties */}
                {formData.specialties.length > 0 && (
                  <div className="mt-3">
                    <p className="text-sm text-gray-600 mb-2">Selected specialties:</p>
                    <div className="flex flex-wrap gap-2">
                      {formData.specialties.map((specialty) => (
                        <span
                          key={specialty}
                          className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm flex items-center space-x-1"
                        >
                          <span>{specialty}</span>
                          <button
                            type="button"
                            onClick={() => removeSpecialty(specialty)}
                            className="ml-1 text-blue-600 hover:text-blue-800"
                          >
                            ×
                          </button>
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Submit Button */}
            <div className="pt-8 border-t border-gray-200 mt-8">
              <div className="flex space-x-4">
                <button
                  type="button"
                  onClick={() => navigate('/practices')}
                  className="px-6 py-3 border border-gray-300 text-gray-700 rounded-lg font-medium hover:bg-gray-50 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="flex-1 bg-blue-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-blue-700 disabled:bg-blue-400 disabled:cursor-not-allowed transition-colors flex items-center justify-center space-x-2"
                >
                  {isSubmitting ? (
                    <>
                      <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                      <span>{mode === 'create' ? 'Creating...' : 'Updating...'}</span>
                    </>
                  ) : (
                    <>
                      <Save className="w-5 h-5" />
                      <span>{mode === 'create' ? 'Create Practice' : 'Update Practice'}</span>
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

export default PracticeForm;
