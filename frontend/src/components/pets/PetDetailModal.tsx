import React, { useState, useEffect } from 'react';
import { X, Edit, Trash2, PawPrint, Calendar, Weight, Syringe, FileText } from 'lucide-react';
import { API_ENDPOINTS } from '../../config/api';

interface PetDetailModalProps {
  isOpen: boolean;
  onClose: () => void;
  petId: string;
  onEdit?: (petId: string) => void;
  onDelete?: (petId: string) => void;
}

interface Pet {
  id: string;
  name: string;
  species: string;
  breed?: string;
  color?: string;
  gender?: string;
  weight?: number;
  date_of_birth?: string;
  microchip_id?: string;
  spayed_neutered?: boolean;
  allergies?: string;
  medications?: string;
  medical_notes?: string;
  emergency_contact?: string;
  emergency_phone?: string;
  owner_id: string;
}

const PetDetailModal: React.FC<PetDetailModalProps> = ({
  isOpen,
  onClose,
  petId,
  onEdit,
  onDelete
}) => {
  const [pet, setPet] = useState<Pet | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [medicalRecords, setMedicalRecords] = useState<any[]>([]);

  useEffect(() => {
    if (isOpen && petId) {
      fetchPetDetails();
    }
  }, [isOpen, petId]);

  const fetchPetDetails = async () => {
    setLoading(true);
    setError(null);
    try {
      // Fetch pet details
      const petResponse = await fetch(API_ENDPOINTS.PETS.GET(petId));
      if (!petResponse.ok) throw new Error('Failed to fetch pet');
      const petData = await petResponse.json();
      setPet(petData);

      // Fetch medical records for this pet
      try {
        const recordsResponse = await fetch(API_ENDPOINTS.MEDICAL_RECORDS.BY_PET(petId));
        if (recordsResponse.ok) {
          const recordsData = await recordsResponse.json();
          setMedicalRecords(recordsData);
        }
      } catch (err) {
        console.error('Failed to fetch medical records:', err);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load pet details');
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  const calculateAge = (dateOfBirth: string) => {
    const today = new Date();
    const birthDate = new Date(dateOfBirth);
    let age = today.getFullYear() - birthDate.getFullYear();
    const monthDiff = today.getMonth() - birthDate.getMonth();
    if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birthDate.getDate())) {
      age--;
    }
    return age;
  };

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
              <div className="w-8 h-8 bg-green-100 rounded flex items-center justify-center">
                <PawPrint className="w-5 h-5 text-green-600" />
              </div>
              <div>
                <h2 className="text-base font-semibold text-gray-900">
                  {loading ? 'Loading...' : pet?.name}
                </h2>
                <p className="text-sm text-gray-500">{pet?.species}</p>
              </div>
            </div>
            <div className="flex items-center gap-1">
              {onEdit && pet && (
                <button
                  onClick={() => onEdit(pet.id)}
                  className="p-1.5 text-gray-600 hover:bg-gray-100 rounded transition-colors"
                  title="Edit"
                >
                  <Edit className="w-4 h-4" />
                </button>
              )}
              {onDelete && pet && (
                <button
                  onClick={() => onDelete(pet.id)}
                  className="p-1.5 text-red-600 hover:bg-red-50 rounded transition-colors"
                  title="Delete"
                >
                  <Trash2 className="w-4 h-4" />
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
                <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-red-800 text-xs">
                  {error}
                </div>
              </div>
            ) : pet ? (
              <div className="p-4 space-y-4">
                {/* Basic Information */}
                <section>
                  <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-3">
                    Basic Information
                  </h3>
                  <div className="space-y-2">
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-gray-600">Species</span>
                      <span className="font-medium text-gray-900">{pet.species}</span>
                    </div>
                    {pet.breed && (
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-gray-600">Breed</span>
                        <span className="font-medium text-gray-900">{pet.breed}</span>
                      </div>
                    )}
                    {pet.color && (
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-gray-600">Color</span>
                        <span className="font-medium text-gray-900">{pet.color}</span>
                      </div>
                    )}
                    {pet.gender && (
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-gray-600">Gender</span>
                        <span className="font-medium text-gray-900">{pet.gender}</span>
                      </div>
                    )}
                    {pet.weight && (
                      <div className="flex items-center gap-2 text-sm text-gray-700">
                        <Weight className="w-4 h-4 text-gray-400" />
                        <span>{pet.weight} lbs</span>
                      </div>
                    )}
                    {pet.date_of_birth && (
                      <div className="flex items-center gap-2 text-sm text-gray-700">
                        <Calendar className="w-4 h-4 text-gray-400" />
                        <span>{new Date(pet.date_of_birth).toLocaleDateString()} ({calculateAge(pet.date_of_birth)} years old)</span>
                      </div>
                    )}
                    {pet.spayed_neutered !== undefined && (
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-gray-600">Spayed/Neutered</span>
                        <span className={`font-medium ${pet.spayed_neutered ? 'text-green-600' : 'text-gray-400'}`}>
                          {pet.spayed_neutered ? 'Yes' : 'No'}
                        </span>
                      </div>
                    )}
                    {pet.microchip_id && (
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-gray-600">Microchip ID</span>
                        <span className="font-mono text-gray-900 text-xs">{pet.microchip_id}</span>
                      </div>
                    )}
                  </div>
                </section>

                {/* Medical Information */}
                {(pet.allergies || pet.medications || pet.medical_notes) && (
                  <section>
                    <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
                      Medical Information
                    </h3>
                    <div className="space-y-2">
                      {pet.allergies && (
                        <div>
                          <div className="text-xs font-medium text-gray-700 mb-1">Allergies</div>
                          <div className="text-xs text-gray-600 bg-red-50 p-2 rounded">{pet.allergies}</div>
                        </div>
                      )}
                      {pet.medications && (
                        <div>
                          <div className="text-xs font-medium text-gray-700 mb-1">Current Medications</div>
                          <div className="text-xs text-gray-600 bg-blue-50 p-2 rounded">{pet.medications}</div>
                        </div>
                      )}
                      {pet.medical_notes && (
                        <div>
                          <div className="text-xs font-medium text-gray-700 mb-1">Medical Notes</div>
                          <div className="text-xs text-gray-600 bg-gray-50 p-2 rounded">{pet.medical_notes}</div>
                        </div>
                      )}
                    </div>
                  </section>
                )}

                {/* Medical Records */}
                <section>
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
                      Medical Records ({medicalRecords.length})
                    </h3>
                    <button 
                      className="flex items-center gap-1 text-xs text-blue-600 hover:text-blue-700 font-medium transition-colors"
                    >
                      <FileText className="w-3.5 h-3.5" />
                      View All
                    </button>
                  </div>
                  {medicalRecords.length > 0 ? (
                    <div className="space-y-1.5">
                      {medicalRecords.slice(0, 3).map((record: any) => (
                        <div
                          key={record.id}
                          className="p-2 border border-gray-200 rounded hover:border-blue-300 hover:bg-blue-50 transition-colors cursor-pointer"
                        >
                          <div className="flex items-center gap-2">
                            <Syringe className="w-3.5 h-3.5 text-blue-600" />
                            <div className="flex-1">
                              <div className="text-xs font-medium text-gray-900">{record.diagnosis || 'Visit'}</div>
                              <div className="text-xs text-gray-500">
                                {new Date(record.visit_date).toLocaleDateString()}
                              </div>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-6 text-gray-500">
                      <FileText className="w-8 h-8 mx-auto mb-1.5 text-gray-300" />
                      <p className="text-xs">No medical records yet</p>
                    </div>
                  )}
                </section>

                {/* Emergency Contact */}
                {(pet.emergency_contact || pet.emergency_phone) && (
                  <section className="pt-4 border-t border-gray-200">
                    <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
                      Emergency Contact
                    </h3>
                    <div className="space-y-1.5">
                      {pet.emergency_contact && (
                        <div className="text-xs text-gray-700">
                          <span className="text-gray-600">Name: </span>
                          <span className="font-medium">{pet.emergency_contact}</span>
                        </div>
                      )}
                      {pet.emergency_phone && (
                        <div className="text-xs text-gray-700">
                          <span className="text-gray-600">Phone: </span>
                          <span className="font-medium">{pet.emergency_phone}</span>
                        </div>
                      )}
                    </div>
                  </section>
                )}
              </div>
            ) : null}
          </div>
        </div>
      </div>
    </div>
  );
};

export default PetDetailModal;

