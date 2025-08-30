import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Heart, Calendar, Weight, Stethoscope } from 'lucide-react';
import { Pet } from '../../types/pet';
import { API_ENDPOINTS } from '../../config/api';
import { useAuth } from '../../contexts/AuthContext';
import '../../utils/authUtils';

interface PetOwnerInfo {
  id: string;
  user_id?: string;
  full_name: string;
}

interface PetsListProps {
  ownerUuid: string;
  showHeader?: boolean;
  maxItems?: number;
  petOwner?: PetOwnerInfo;
}

const PetsList: React.FC<PetsListProps> = ({ 
  ownerUuid, 
  showHeader = true, 
  maxItems,
  petOwner
}) => {
  const [pets, setPets] = useState<Pet[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { user } = useAuth();

  useEffect(() => {
    fetchPets();
  }, [ownerUuid]);

  const fetchPets = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch(API_ENDPOINTS.PETS.BY_OWNER(ownerUuid));
      
      if (!response.ok) {
        if (response.status === 403) {
          throw new Error('Access denied to view pets for this owner');
        }
        throw new Error('Failed to fetch pets');
      }

      const petsData = await response.json();
      setPets(petsData);
    } catch (err) {
      console.error('Error fetching pets:', err);
      setError(err instanceof Error ? err.message : 'Failed to load pets');
    } finally {
      setLoading(false);
    }
  };

  const canCreatePets = () => {
    return user?.role === 'ADMIN' || user?.role === 'VET_STAFF';
  };

  const canEditPets = () => {
    // Admin can edit all pets, VET_STAFF can edit pets from their practice, pet owners can edit their own pets
    return user?.role === 'ADMIN' || user?.role === 'VET_STAFF' || (petOwner && petOwner.user_id === user?.id);
  };

  const formatAge = (pet: Pet) => {
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

  const formatWeight = (weight?: number) => {
    if (!weight) return 'Weight not recorded';
    return `${weight} lbs`;
  };

  const displayedPets = maxItems ? pets.slice(0, maxItems) : pets;

  if (loading) {
    return (
      <div className="flex items-center justify-center py-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span className="ml-2 text-gray-600">Loading pets...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <div className="flex items-center">
          <div className="text-red-600">
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
            </svg>
          </div>
          <div className="ml-3">
            <p className="text-sm text-red-700">{error}</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {showHeader && (
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-900 flex items-center">
            <Heart className="w-5 h-5 mr-2 text-blue-600" />
            Pets {pets.length > 0 && `(${pets.length})`}
          </h3>
          {canCreatePets() && (
            <Link
              to={`/pets/create?owner_id=${ownerUuid}`}
              className="inline-flex items-center px-3 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-md transition-colors duration-200"
            >
              Add Pet
            </Link>
          )}
        </div>
      )}

      {pets.length === 0 ? (
        <div className="text-center py-8 bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
          <Heart className="w-12 h-12 mx-auto text-gray-400 mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No pets registered</h3>
          <p className="text-gray-600 mb-4">
            This pet owner doesn't have any pets registered yet.
          </p>
          {canCreatePets() && (
            <Link
              to={`/pets/create?owner_id=${ownerUuid}`}
              className="inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-md transition-colors duration-200"
            >
              Add First Pet
            </Link>
          )}
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {displayedPets.map((pet) => (
            <div
              key={pet.id}
              className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow duration-200"
            >
              <div className="flex items-start justify-between mb-3">
                <div>
                  <h4 className="text-lg font-semibold text-gray-900">{pet.name}</h4>
                  <p className="text-sm text-gray-600">{pet.species}</p>
                  {pet.breed && (
                    <p className="text-xs text-gray-500">{pet.breed}</p>
                  )}
                </div>
                <div className="flex space-x-2">
                  <Link
                    to={`/pets/${pet.id}`}
                    className="inline-flex items-center px-2 py-1 text-xs font-medium text-white bg-blue-600 hover:bg-blue-700 rounded transition-colors duration-200"
                  >
                    View
                  </Link>
                  {canEditPets() && (
                    <Link
                      to={`/pets/${pet.id}/edit`}
                      className="inline-flex items-center px-2 py-1 text-xs font-medium text-white bg-blue-600 hover:bg-blue-700 rounded transition-colors duration-200"
                    >
                      Edit
                    </Link>
                  )}
                </div>
              </div>

              <div className="space-y-2 text-sm text-gray-600">
                <div className="flex items-center">
                  <Calendar className="w-4 h-4 mr-2 text-gray-400" />
                  <span>{formatAge(pet)}</span>
                </div>
                
                {pet.weight && (
                  <div className="flex items-center">
                    <Weight className="w-4 h-4 mr-2 text-gray-400" />
                    <span>{formatWeight(pet.weight)}</span>
                  </div>
                )}

                {pet.gender && (
                  <div className="flex items-center">
                    <span className={`w-4 h-4 mr-2 text-center font-bold ${
                      pet.gender.toLowerCase() === 'male' ? 'text-blue-500' : 
                      pet.gender.toLowerCase() === 'female' ? 'text-pink-500' : 
                      'text-gray-400'
                    }`}>
                      {pet.gender.toLowerCase() === 'male' ? '♂' : 
                       pet.gender.toLowerCase() === 'female' ? '♀' : 
                       '♂♀'}
                    </span>
                    <span>{pet.gender}</span>
                  </div>
                )}

                {(pet.allergies || pet.medications) && (
                  <div className="flex items-center">
                    <Stethoscope className="w-4 h-4 mr-2 text-red-400" />
                    <span className="text-red-600">Medical notes</span>
                  </div>
                )}
              </div>

              {pet.microchip_id && (
                <div className="mt-3 pt-3 border-t border-gray-100">
                  <p className="text-xs text-gray-500">
                    Microchip: {pet.microchip_id}
                  </p>
                </div>
              )}

              {!pet.is_active && (
                <div className="mt-3 pt-3 border-t border-gray-100">
                  <span className="inline-flex items-center px-2 py-1 text-xs font-medium bg-red-100 text-red-800 rounded-full">
                    Inactive
                  </span>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {maxItems && pets.length > maxItems && (
        <div className="text-center pt-4">
          <Link
            to={`/pet_owners/${ownerUuid}/pets`}
            className="text-blue-600 hover:text-blue-700 font-medium"
          >
            View all {pets.length} pets →
          </Link>
        </div>
      )}
    </div>
  );
};

export default PetsList;
