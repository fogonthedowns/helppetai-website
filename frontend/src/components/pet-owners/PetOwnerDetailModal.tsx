import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { X, Mail, Phone, MapPin, Calendar, Edit, PawPrint, Plus } from 'lucide-react';
import { API_ENDPOINTS } from '../../config/api';
import PetCreateModal from '../pets/PetCreateModal';
import PetDetailModal from '../pets/PetDetailModal';
import PetEditModal from '../pets/PetEditModal';
import PetOwnerEditModal from './PetOwnerEditModal';
import ConfirmDialog from '../common/ConfirmDialog';

interface PetOwnerDetailModalProps {
  isOpen: boolean;
  onClose: () => void;
  ownerId: string;
}

interface PetOwner {
  uuid: string;
  full_name: string;
  email: string | null;
  phone: string | null;
  emergency_contact: string | null;
  secondary_phone: string | null;
  address: string | null;
  preferred_communication: string;
  notifications_enabled: boolean;
  created_at: string;
  updated_at: string;
}

interface Pet {
  id: string;
  name: string;
  species: string;
  breed?: string;
  age?: number;
  age_years?: number;
}

const PetOwnerDetailModal: React.FC<PetOwnerDetailModalProps> = ({
  isOpen,
  onClose,
  ownerId
}) => {
  const navigate = useNavigate();
  const [owner, setOwner] = useState<PetOwner | null>(null);
  const [pets, setPets] = useState<Pet[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isPetModalOpen, setIsPetModalOpen] = useState(false);
  const [selectedPetId, setSelectedPetId] = useState<string | null>(null);
  const [isPetDetailModalOpen, setIsPetDetailModalOpen] = useState(false);
  const [isPetEditModalOpen, setIsPetEditModalOpen] = useState(false);
  const [isOwnerEditModalOpen, setIsOwnerEditModalOpen] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [petToDelete, setPetToDelete] = useState<{ id: string; name: string } | null>(null);

  useEffect(() => {
    if (isOpen && ownerId) {
      fetchOwnerDetails();
    }
  }, [isOpen, ownerId]);

  const fetchOwnerDetails = async () => {
    setLoading(true);
    setError(null);
    try {
      // Fetch owner details
      const ownerResponse = await fetch(API_ENDPOINTS.PET_OWNERS.GET(ownerId));
      if (!ownerResponse.ok) throw new Error('Failed to fetch owner');
      const ownerData = await ownerResponse.json();
      setOwner(ownerData);

      // Fetch pets for this owner
      try {
        const endpoint = `${API_ENDPOINTS.PETS.LIST}?owner_id=${ownerId}`;
        const petsResponse = await fetch(endpoint);
        if (petsResponse.ok) {
          const petsData = await petsResponse.json();
          // The API returns {pets: [...], total: ..., page: ..., per_page: ...}
          setPets(petsData.pets || []);
        }
      } catch (err) {
        console.error('Failed to fetch pets:', err);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load owner details');
    } finally {
      setLoading(false);
    }
  };

  const handleDeletePet = async () => {
    if (!petToDelete) return;

    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(API_ENDPOINTS.PETS.DELETE(petToDelete.id), {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        throw new Error('Failed to delete pet');
      }

      // Close any open modals and refresh
      setIsPetDetailModalOpen(false);
      setSelectedPetId(null);
      fetchOwnerDetails();
    } catch (err) {
      console.error('Error deleting pet:', err);
      // Could show an error toast here
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-hidden">
      {/* Backdrop */}
      <div 
        className="absolute inset-0 bg-black bg-opacity-30 transition-opacity"
        onClick={onClose}
      />
      
      {/* Modal Panel */}
      <div className="absolute inset-y-0 right-0 flex max-w-xl w-full">
        <div className="bg-white w-full shadow-2xl flex flex-col">
          {/* Header */}
          <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200">
            <div className="flex items-center gap-2">
              <div className="w-10 h-10 bg-blue-100 rounded flex items-center justify-center">
                <span className="text-blue-600 font-medium text-base">
                  {owner?.full_name?.charAt(0) || '?'}
                </span>
              </div>
              <div>
                <h2 className="text-base font-semibold text-gray-900">
                  {loading ? 'Loading...' : owner?.full_name}
                </h2>
                <p className="text-base text-gray-500">Pet Owner</p>
              </div>
            </div>
                      <div className="flex items-center gap-1">
                        {owner && (
                          <button
                            onClick={() => setIsOwnerEditModalOpen(true)}
                            className="p-1.5 text-gray-600 hover:bg-gray-100 rounded transition-colors"
                            title="Edit"
                          >
                            <Edit className="w-4 h-4" />
                          </button>
                        )}
              <button
                onClick={onClose}
                className="p-1.5 text-gray-600 hover:bg-gray-100 rounded transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Content */}
          <div className="flex-1 overflow-y-auto">
            {loading ? (
              <div className="flex items-center justify-center h-32">
                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-500"></div>
              </div>
            ) : error ? (
              <div className="p-4">
                <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-red-800 text-md">
                  {error}
                </div>
              </div>
            ) : owner ? (
              <div className="p-4 space-y-4">
                {/* Contact Information */}
                <section>
                  <h3 className="text-base font-semibold text-gray-500 uppercase tracking-wider mb-3">
                    Contact Information
                  </h3>
                  <div className="space-y-2.5">
                    {owner.email && (
                      <div className="flex items-center gap-2 text-base text-gray-700">
                        <Mail className="w-4 h-4 text-gray-400" />
                        <a href={`mailto:${owner.email}`} className="hover:text-blue-600">
                          {owner.email}
                        </a>
                      </div>
                    )}
                    {owner.phone && (
                      <div className="flex items-center gap-2 text-base text-gray-700">
                        <Phone className="w-4 h-4 text-gray-400" />
                        <a href={`tel:${owner.phone}`} className="hover:text-blue-600">
                          {owner.phone}
                        </a>
                      </div>
                    )}
                    {owner.secondary_phone && (
                      <div className="flex items-center gap-2 text-base text-gray-700">
                        <Phone className="w-4 h-4 text-gray-400" />
                        <span className="text-gray-500 mr-1">Secondary:</span>
                        <a href={`tel:${owner.secondary_phone}`} className="hover:text-blue-600">
                          {owner.secondary_phone}
                        </a>
                      </div>
                    )}
                    {owner.emergency_contact && (
                      <div className="flex items-center gap-2 text-base text-gray-700">
                        <Phone className="w-4 h-4 text-red-400" />
                        <span className="text-gray-500 mr-1">Emergency:</span>
                        <a href={`tel:${owner.emergency_contact}`} className="hover:text-blue-600">
                          {owner.emergency_contact}
                        </a>
                      </div>
                    )}
                    {owner.address && (
                      <div className="flex items-start gap-2 text-base text-gray-700">
                        <MapPin className="w-4 h-4 text-gray-400 mt-0.5" />
                        <span>{owner.address}</span>
                      </div>
                    )}
                  </div>
                </section>

                {/* Preferences */}
                <section>
                  <h3 className="text-base font-semibold text-gray-500 uppercase tracking-wider mb-2">
                    Preferences
                  </h3>
                  <div className="space-y-1.5">
                    <div className="flex items-center justify-between text-base">
                      <span className="text-gray-600">Preferred Communication</span>
                      <span className="font-medium text-gray-900 capitalize">
                        {owner.preferred_communication}
                      </span>
                    </div>
                    <div className="flex items-center justify-between text-base">
                      <span className="text-gray-600">Notifications</span>
                      <span className={`font-medium ${owner.notifications_enabled ? 'text-green-600' : 'text-gray-400'}`}>
                        {owner.notifications_enabled ? 'Enabled' : 'Disabled'}
                      </span>
                    </div>
                  </div>
                </section>

                {/* Pets */}
                <section>
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="text-base font-semibold text-gray-500 uppercase tracking-wider">
                      Pets ({pets.length})
                    </h3>
                    <button 
                      onClick={() => setIsPetModalOpen(true)}
                      className="flex items-center gap-1 text-base text-blue-600 hover:text-blue-700 font-medium transition-colors"
                    >
                      <Plus className="w-4 h-4" />
                      Add Pet
                    </button>
                  </div>
                  {pets.length > 0 ? (
                    <div className="space-y-1.5">
                      {pets.map((pet) => (
                        <div
                          key={pet.id}
                          onClick={() => {
                            navigate(`/dashboard/pet_owners/${ownerId}/pets/${pet.id}`);
                          }}
                          className="p-2 border border-gray-200 rounded hover:border-blue-300 hover:bg-blue-50 transition-colors cursor-pointer"
                        >
                          <div className="flex items-center gap-2">
                            <div className="w-8 h-8 bg-green-100 rounded flex items-center justify-center">
                              <PawPrint className="w-4 h-4 text-green-600" />
                            </div>
                            <div>
                              <div className="text-base font-medium text-gray-900">{pet.name}</div>
                              <div className="text-base text-gray-500">
                                {pet.breed || pet.species}
                                {(pet.age || pet.age_years) && ` • ${pet.age || pet.age_years} years old`}
                              </div>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-6 text-gray-500">
                      <PawPrint className="w-8 h-8 mx-auto mb-1.5 text-gray-300" />
                      <p className="text-base">No pets registered yet</p>
                    </div>
                  )}
                </section>

                {/* Metadata */}
                <section className="pt-4 border-t border-gray-200">
                  <div className="flex items-center gap-2 text-base text-gray-500">
                    <Calendar className="w-4 h-4" />
                    <span>Created {new Date(owner.created_at).toLocaleDateString()}</span>
                    {owner.updated_at !== owner.created_at && (
                      <span>• Updated {new Date(owner.updated_at).toLocaleDateString()}</span>
                    )}
                  </div>
                </section>
              </div>
            ) : null}
          </div>
        </div>
      </div>

      {/* Pet Create Modal */}
      <PetCreateModal
        isOpen={isPetModalOpen}
        onClose={() => setIsPetModalOpen(false)}
        onSuccess={() => {
          setIsPetModalOpen(false);
          fetchOwnerDetails(); // Refresh the pet list
        }}
        ownerUuid={ownerId}
      />

        {/* Pet Detail Modal */}
        {selectedPetId && (
          <PetDetailModal
            isOpen={isPetDetailModalOpen}
            onClose={() => {
              setIsPetDetailModalOpen(false);
              setSelectedPetId(null);
            }}
            petId={selectedPetId}
            onEdit={(petId) => {
              setIsPetDetailModalOpen(false);
              setIsPetEditModalOpen(true);
            }}
            onDelete={(petId) => {
              // Find the pet name for the confirmation dialog
              const pet = pets.find(p => p.id === petId);
              setPetToDelete({ id: petId, name: pet?.name || 'this pet' });
              setShowDeleteConfirm(true);
            }}
          />
        )}

        {/* Pet Edit Modal */}
        {selectedPetId && (
          <PetEditModal
            isOpen={isPetEditModalOpen}
            onClose={() => {
              setIsPetEditModalOpen(false);
              setSelectedPetId(null);
            }}
            onSuccess={() => {
              setIsPetEditModalOpen(false);
              fetchOwnerDetails(); // Refresh the pet list
            }}
            petId={selectedPetId}
          />
        )}

        {/* Pet Owner Edit Modal */}
        <PetOwnerEditModal
          isOpen={isOwnerEditModalOpen}
          onClose={() => {
            setIsOwnerEditModalOpen(false);
          }}
          onSuccess={() => {
            setIsOwnerEditModalOpen(false);
            fetchOwnerDetails(); // Refresh the owner details
          }}
          ownerUuid={ownerId}
        />

        {/* Delete Confirmation Dialog */}
        <ConfirmDialog
          isOpen={showDeleteConfirm}
          onClose={() => {
            setShowDeleteConfirm(false);
            setPetToDelete(null);
          }}
          onConfirm={handleDeletePet}
          title="Delete this pet?"
          message={`Are you sure you want to delete ${petToDelete?.name}? This action cannot be undone.`}
          confirmText="Delete"
          cancelText="Cancel"
          isDangerous={true}
        />
      </div>
    );
  };

  export default PetOwnerDetailModal;

