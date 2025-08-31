import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { 
  Heart, Edit, Trash2, Calendar, Weight, 
  Stethoscope, Phone, AlertCircle, CheckCircle, RotateCcw 
} from 'lucide-react';
import { PetWithOwner } from '../../types/pet';
import { API_ENDPOINTS } from '../../config/api';
import { useAuth } from '../../contexts/AuthContext';
import Breadcrumb, { BreadcrumbItem } from '../common/Breadcrumb';
import '../../utils/authUtils';
import MedicalRecordsTimeline from '../medical-records/MedicalRecordsTimeline';
import VisitTranscriptsList from '../visit-transcripts/VisitTranscriptsList';
import AppointmentsList from '../appointments/AppointmentsList';

const PetDetail: React.FC = () => {
  const { uuid } = useParams<{ uuid: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();

  const [pet, setPet] = useState<PetWithOwner | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);

  useEffect(() => {
    if (uuid) {
      fetchPet();
    }
  }, [uuid]);

  const fetchPet = async () => {
    if (!uuid) return;

    try {
      setLoading(true);
      setError(null);

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

      const petData = await response.json();
      setPet(petData);
    } catch (err) {
      console.error('Error fetching pet:', err);
      setError(err instanceof Error ? err.message : 'Failed to load pet');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!uuid || !pet) return;

    setIsDeleting(true);
    try {
      const response = await fetch(API_ENDPOINTS.PETS.DELETE(uuid), {
        method: 'DELETE'
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to delete pet');
      }

      // Redirect to pet owner page
      navigate(`/pet_owners/${pet.owner_id}`);
    } catch (err) {
      console.error('Error deleting pet:', err);
      setError(err instanceof Error ? err.message : 'Failed to delete pet');
    } finally {
      setIsDeleting(false);
      setShowDeleteConfirm(false);
    }
  };

  const handleReactivate = async () => {
    if (!uuid) return;

    try {
      const response = await fetch(API_ENDPOINTS.PETS.REACTIVATE(uuid), {
        method: 'POST'
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to reactivate pet');
      }

      // Refresh pet data
      await fetchPet();
    } catch (err) {
      console.error('Error reactivating pet:', err);
      setError(err instanceof Error ? err.message : 'Failed to reactivate pet');
    }
  };

  const canEditPet = () => {
    // Admin can edit all pets, VET_STAFF can edit pets from their practice, pet owners can edit their own pets
    return user?.role === 'ADMIN' || user?.role === 'VET_STAFF' || (pet && pet.owner.user_id === user?.id);
  };

  const canDeletePet = () => {
    // Admin can delete all pets, VET_STAFF can delete pets from their practice, pet owners can delete their own pets
    return user?.role === 'ADMIN' || user?.role === 'VET_STAFF' || (pet && pet.owner.user_id === user?.id);
  };

  const formatAge = (pet: PetWithOwner) => {
    if (pet.age_years !== undefined && pet.age_years !== null) {
      return pet.age_years === 1 ? '1 year old' : `${pet.age_years} years old`;
    }
    if (pet.date_of_birth) {
      const birthDate = new Date(pet.date_of_birth);
      const today = new Date();
      const ageInMonths = (today.getFullYear() - birthDate.getFullYear()) * 12 + 
                         (today.getMonth() - birthDate.getMonth());
      
      if (ageInMonths < 12) {
        return ageInMonths === 1 ? '1 month old' : `${ageInMonths} months old`;
      }
    }
    return 'Age unknown';
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <span className="ml-2 text-gray-600">Loading pet...</span>
          </div>
        </div>
      </div>
    );
  }

  if (error || !pet) {
    return (
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="bg-red-50 border border-red-200 rounded-lg p-6">
            <div className="flex items-center">
              <AlertCircle className="w-6 h-6 text-red-600 mr-3" />
              <div>
                <h3 className="text-lg font-medium text-red-800">Error</h3>
                <p className="text-red-700 mt-1">{error || 'Pet not found'}</p>
              </div>
            </div>
            <div className="mt-4">
              <button
                onClick={() => navigate(-1)}
                className="text-red-600 hover:text-red-700 font-medium"
              >
                ← Go back
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          {/* Breadcrumb Navigation */}
          <Breadcrumb
            items={[
              { label: 'Pet Owners', href: '/pet_owners' },
              { label: pet.owner.full_name, href: `/pet_owners/${pet.owner_id}` },
              { label: pet.display_name, isActive: true }
            ]}
            className="mb-6"
          />
          
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <div className="bg-blue-100 p-3 rounded-lg mr-4">
                <Heart className="w-6 h-6 text-blue-600" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">{pet.display_name}</h1>
                <p className="text-gray-600">
                  {pet.species} {pet.breed && `• ${pet.breed}`}
                </p>
              </div>
            </div>

            <div className="flex items-center space-x-3">
              {!pet.is_active && canDeletePet() && (
                <button
                  onClick={handleReactivate}
                  className="inline-flex items-center px-3 py-2 text-sm font-medium text-white bg-green-600 hover:bg-green-700 rounded-md transition-colors duration-200"
                >
                  <RotateCcw className="w-4 h-4 mr-2" />
                  Reactivate
                </button>
              )}
              
              {canEditPet() && (
                <Link
                  to={`/pets/${pet.id}/edit`}
                  className="inline-flex items-center px-3 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-md transition-colors duration-200"
                >
                  <Edit className="w-4 h-4 mr-2" />
                  Edit
                </Link>
              )}
              
              {canDeletePet() && pet.is_active && (
                <button
                  onClick={() => setShowDeleteConfirm(true)}
                  className="inline-flex items-center px-3 py-2 text-sm font-medium text-white bg-red-600 hover:bg-red-700 rounded-md transition-colors duration-200"
                >
                  <Trash2 className="w-4 h-4 mr-2" />
                  Delete
                </button>
              )}
            </div>
          </div>

          {!pet.is_active && (
            <div className="mt-4 bg-red-50 border border-red-200 rounded-lg p-4">
              <div className="flex items-center">
                <AlertCircle className="w-5 h-5 text-red-600 mr-2" />
                <p className="text-sm text-red-700">This pet is inactive and won't appear in regular listings.</p>
              </div>
            </div>
          )}
        </div>

        {/* Pet Information */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Basic Information */}
          <div className="lg:col-span-2 space-y-6">
            <div className="bg-white shadow-sm rounded-lg p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Basic Information</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
                  <p className="text-gray-900">{pet.name}</p>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Species</label>
                  <p className="text-gray-900">{pet.species}</p>
                </div>

                {pet.breed && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Breed</label>
                    <p className="text-gray-900">{pet.breed}</p>
                  </div>
                )}

                {pet.color && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Color</label>
                    <p className="text-gray-900">{pet.color}</p>
                  </div>
                )}

                {pet.gender && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Gender</label>
                    <div className="flex items-center">
                      <span className={`mr-2 text-lg font-bold ${
                        pet.gender.toLowerCase() === 'male' ? 'text-blue-500' : 
                        pet.gender.toLowerCase() === 'female' ? 'text-pink-500' : 
                        'text-gray-400'
                      }`}>
                        {pet.gender.toLowerCase() === 'male' ? '♂' : 
                         pet.gender.toLowerCase() === 'female' ? '♀' : 
                         '♂♀'}
                      </span>
                      <p className="text-gray-900">{pet.gender}</p>
                    </div>
                  </div>
                )}

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Age</label>
                  <div className="flex items-center">
                    <Calendar className="w-4 h-4 text-gray-400 mr-2" />
                    <p className="text-gray-900">{formatAge(pet)}</p>
                  </div>
                </div>

                {pet.weight && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Weight</label>
                    <div className="flex items-center">
                      <Weight className="w-4 h-4 text-gray-400 mr-2" />
                      <p className="text-gray-900">{pet.weight} lbs</p>
                    </div>
                  </div>
                )}

                {pet.date_of_birth && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Date of Birth</label>
                    <p className="text-gray-900">{formatDate(pet.date_of_birth)}</p>
                  </div>
                )}

                {pet.microchip_id && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Microchip ID</label>
                    <p className="text-gray-900 font-mono text-sm">{pet.microchip_id}</p>
                  </div>
                )}

                {pet.spayed_neutered !== undefined && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Spayed/Neutered</label>
                    <div className="flex items-center">
                      {pet.spayed_neutered ? (
                        <CheckCircle className="w-4 h-4 text-green-500 mr-2" />
                      ) : (
                        <div className="w-4 h-4 border border-gray-300 rounded mr-2"></div>
                      )}
                      <p className="text-gray-900">{pet.spayed_neutered ? 'Yes' : 'No'}</p>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Medical Information */}
            {(pet.allergies || pet.medications || pet.medical_notes) && (
              <div className="bg-white shadow-sm rounded-lg p-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                  <Stethoscope className="w-5 h-5 mr-2 text-red-500" />
                  Medical Information
                </h2>
                <div className="space-y-4">
                  {pet.allergies && (
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">Allergies</label>
                      <div className="bg-red-50 border border-red-200 rounded-lg p-3">
                        <p className="text-gray-900 whitespace-pre-wrap">{pet.allergies}</p>
                      </div>
                    </div>
                  )}

                  {pet.medications && (
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">Current Medications</label>
                      <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                        <p className="text-gray-900 whitespace-pre-wrap">{pet.medications}</p>
                      </div>
                    </div>
                  )}

                  {pet.medical_notes && (
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">Medical Notes</label>
                      <div className="bg-gray-50 border border-gray-200 rounded-lg p-3">
                        <p className="text-gray-900 whitespace-pre-wrap">{pet.medical_notes}</p>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Medical Records */}
            <div className="bg-white shadow-sm rounded-lg p-6">
              <MedicalRecordsTimeline 
                petId={pet.id} 
                showHeader={true}
                maxItems={5}
              />
            </div>

            {/* Visit Transcripts */}
            <div className="bg-white shadow-sm rounded-lg p-6">
              <VisitTranscriptsList 
                petId={pet.id}
                petOwnerId={pet.owner_id}
                showHeader={true}
                maxItems={5}
              />
            </div>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Scheduled Appointments */}
            <div className="bg-white shadow-sm rounded-lg p-6">
              <AppointmentsList 
                petOwnerId={pet.owner_id}
                petId={pet.id}
                showHeader={true}
                maxItems={3}
                showCreateButton={true}
                title="Scheduled Appointments"
              />
            </div>

            {/* Owner Information */}
            <div className="bg-white shadow-sm rounded-lg p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Owner Information</h3>
              <div className="space-y-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
                  <Link 
                    to={`/pet_owners/${pet.owner_id}`}
                    className="text-blue-600 hover:text-blue-700 font-medium"
                  >
                    {pet.owner.full_name}
                  </Link>
                </div>
                
                {pet.owner.email && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
                    <a 
                      href={`mailto:${pet.owner.email}`}
                      className="text-blue-600 hover:text-blue-700"
                    >
                      {pet.owner.email}
                    </a>
                  </div>
                )}

                {pet.owner.phone && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Phone</label>
                    <a 
                      href={`tel:${pet.owner.phone}`}
                      className="text-blue-600 hover:text-blue-700 flex items-center"
                    >
                      <Phone className="w-4 h-4 mr-1" />
                      {pet.owner.phone}
                    </a>
                  </div>
                )}
              </div>
            </div>

            {/* Emergency Contact */}
            {(pet.emergency_contact || pet.emergency_phone) && (
              <div className="bg-white shadow-sm rounded-lg p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                  <AlertCircle className="w-5 h-5 mr-2 text-red-500" />
                  Emergency Contact
                </h3>
                <div className="space-y-3">
                  {pet.emergency_contact && (
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
                      <p className="text-gray-900">{pet.emergency_contact}</p>
                    </div>
                  )}

                  {pet.emergency_phone && (
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Phone</label>
                      <a 
                        href={`tel:${pet.emergency_phone}`}
                        className="text-red-600 hover:text-red-700 flex items-center font-medium"
                      >
                        <Phone className="w-4 h-4 mr-1" />
                        {pet.emergency_phone}
                      </a>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Record Information */}
            <div className="bg-white shadow-sm rounded-lg p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Record Information</h3>
              <div className="space-y-3 text-sm">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Created</label>
                  <p className="text-gray-600">{formatDate(pet.created_at)}</p>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Last Updated</label>
                  <p className="text-gray-600">{formatDate(pet.updated_at)}</p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
                  <span className={`inline-flex items-center px-2 py-1 text-xs font-medium rounded-full ${
                    pet.is_active 
                      ? 'bg-green-100 text-green-800' 
                      : 'bg-red-100 text-red-800'
                  }`}>
                    {pet.is_active ? 'Active' : 'Inactive'}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Delete Confirmation Modal */}
        {showDeleteConfirm && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
            <div className="bg-white rounded-lg p-6 max-w-md w-full">
              <div className="flex items-center mb-4">
                <AlertCircle className="w-6 h-6 text-red-600 mr-3" />
                <h3 className="text-lg font-medium text-gray-900">Delete Pet</h3>
              </div>
              
              <p className="text-gray-600 mb-6">
                Are you sure you want to delete <strong>{pet.name}</strong>? This action will deactivate the pet record but preserve the data for historical purposes.
              </p>
              
              <div className="flex justify-end space-x-3">
                <button
                  onClick={() => setShowDeleteConfirm(false)}
                  disabled={isDeleting}
                  className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  onClick={handleDelete}
                  disabled={isDeleting}
                  className="px-4 py-2 text-sm font-medium text-white bg-red-600 hover:bg-red-700 rounded-md disabled:opacity-50"
                >
                  {isDeleting ? 'Deleting...' : 'Delete Pet'}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default PetDetail;
