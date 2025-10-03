import React, { useState, useEffect } from 'react';
import { X, Edit, Calendar, Clock, User, FileText, PawPrint, AlertCircle } from 'lucide-react';
import { API_ENDPOINTS, API_BASE_URL } from '../../config/api';
import { Appointment, AppointmentType, AppointmentStatus } from '../../types/appointment';

interface AppointmentDetailModalProps {
  isOpen: boolean;
  onClose: () => void;
  appointmentId: string;
  onEdit?: (appointmentId: string) => void;
}

const AppointmentDetailModal: React.FC<AppointmentDetailModalProps> = ({
  isOpen,
  onClose,
  appointmentId,
  onEdit
}) => {
  const [appointment, setAppointment] = useState<Appointment | null>(null);
  const [petOwner, setPetOwner] = useState<any>(null);
  const [assignedVet, setAssignedVet] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen && appointmentId) {
      fetchAppointmentDetails();
    }
  }, [isOpen, appointmentId]);

  const fetchAppointmentDetails = async () => {
    setLoading(true);
    setError(null);
    try {
      const token = localStorage.getItem('access_token');
      const baseURL = API_BASE_URL;

      // Fetch appointment details
      const appointmentResponse = await fetch(`${baseURL}/api/v1/appointments/${appointmentId}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (!appointmentResponse.ok) throw new Error('Failed to fetch appointment');
      const appointmentData = await appointmentResponse.json();
      setAppointment(appointmentData);

      // Fetch pet owner details
      if (appointmentData.pet_owner_id) {
        try {
          const ownerResponse = await fetch(API_ENDPOINTS.PET_OWNERS.GET(appointmentData.pet_owner_id));
          if (ownerResponse.ok) {
            const ownerData = await ownerResponse.json();
            setPetOwner(ownerData);
          }
        } catch (err) {
          console.error('Failed to fetch pet owner:', err);
        }
      }

      // Fetch assigned vet details
      if (appointmentData.assigned_vet_user_id) {
        try {
          const vetResponse = await fetch(`${baseURL}/api/v1/users/${appointmentData.assigned_vet_user_id}`, {
            headers: { 'Authorization': `Bearer ${token}` }
          });
          if (vetResponse.ok) {
            const vetData = await vetResponse.json();
            setAssignedVet(vetData);
          }
        } catch (err) {
          console.error('Failed to fetch vet:', err);
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load appointment details');
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  const formatDateTime = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString('en-US', {
      weekday: 'short',
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
      hour12: true
    });
  };

  const getStatusColor = (status: AppointmentStatus) => {
    switch (status) {
      case AppointmentStatus.SCHEDULED:
      case AppointmentStatus.CONFIRMED:
        return 'bg-blue-100 text-blue-800';
      case AppointmentStatus.IN_PROGRESS:
        return 'bg-yellow-100 text-yellow-800';
      case AppointmentStatus.COMPLETE:
      case AppointmentStatus.COMPLETED:
        return 'bg-green-100 text-green-800';
      case AppointmentStatus.CANCELLED:
        return 'bg-red-100 text-red-800';
      case AppointmentStatus.NO_SHOW:
        return 'bg-gray-100 text-gray-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getTypeLabel = (type: AppointmentType) => {
    return type.charAt(0).toUpperCase() + type.slice(1);
  };

  return (
    <div className="fixed inset-0 z-50 overflow-hidden">
      {/* Backdrop */}
      <div 
        className="absolute inset-0 bg-black bg-opacity-30 transition-opacity"
        onClick={onClose}
      />
      
      {/* Modal Panel */}
      <div className="absolute inset-y-0 right-0 flex max-w-2xl w-full">
        <div className="bg-white w-full shadow-2xl flex flex-col">
          {/* Header */}
          <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center">
                <Calendar className="w-4 h-4 text-blue-600" />
              </div>
              <div>
                <h2 className="text-base font-semibold text-gray-900">
                  {loading ? 'Loading...' : appointment?.title}
                </h2>
                <p className="text-sm text-gray-500">Appointment Details</p>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              {appointment && onEdit && (
                <button
                  onClick={() => onEdit(appointment.id)}
                  className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded transition-colors"
                  title="Edit appointment"
                >
                  <Edit className="w-4 h-4" />
                </button>
              )}
              <button
                onClick={onClose}
                className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
          </div>

          {/* Content */}
          <div className="flex-1 overflow-y-auto p-6">
            {loading && (
              <div className="flex items-center justify-center py-12">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              </div>
            )}

            {error && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start space-x-3">
                <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
                <div>
                  <h3 className="text-sm font-medium text-red-800">Error</h3>
                  <p className="text-sm text-red-700 mt-1">{error}</p>
                </div>
              </div>
            )}

            {!loading && !error && appointment && (
              <div className="space-y-6">
                {/* Status */}
                <div>
                  <span className={`px-2.5 py-1 inline-flex text-sm leading-5 font-semibold rounded-full ${getStatusColor(appointment.status)}`}>
                    {appointment.status.charAt(0).toUpperCase() + appointment.status.slice(1)}
                  </span>
                </div>

                {/* Appointment Details Table */}
                <div className="border border-gray-200 rounded-lg overflow-hidden">
                  <table className="min-w-full divide-y divide-gray-200">
                    <tbody className="bg-white divide-y divide-gray-200">
                      <tr>
                        <td className="px-4 py-3 text-sm font-medium text-gray-500 bg-gray-50 w-1/3">
                          <div className="flex items-center space-x-2">
                            <Calendar className="w-4 h-4 text-gray-400" />
                            <span>Date & Time</span>
                          </div>
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-900">
                          {formatDateTime(appointment.appointment_date)}
                        </td>
                      </tr>
                      <tr>
                        <td className="px-4 py-3 text-sm font-medium text-gray-500 bg-gray-50">
                          <div className="flex items-center space-x-2">
                            <Clock className="w-4 h-4 text-gray-400" />
                            <span>Duration</span>
                          </div>
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-900">
                          {appointment.duration_minutes} minutes
                        </td>
                      </tr>
                      <tr>
                        <td className="px-4 py-3 text-sm font-medium text-gray-500 bg-gray-50">
                          <div className="flex items-center space-x-2">
                            <FileText className="w-4 h-4 text-gray-400" />
                            <span>Type</span>
                          </div>
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-900">
                          {getTypeLabel(appointment.appointment_type)}
                        </td>
                      </tr>
                      {petOwner && (
                        <tr>
                          <td className="px-4 py-3 text-sm font-medium text-gray-500 bg-gray-50">
                            <div className="flex items-center space-x-2">
                              <User className="w-4 h-4 text-gray-400" />
                              <span>Pet Owner</span>
                            </div>
                          </td>
                          <td className="px-4 py-3 text-sm text-gray-900">
                            <div>
                              <p className="font-medium">{petOwner.full_name}</p>
                              {petOwner.email && <p className="text-gray-500">{petOwner.email}</p>}
                              {petOwner.phone && <p className="text-gray-500">{petOwner.phone}</p>}
                            </div>
                          </td>
                        </tr>
                      )}
                      {assignedVet && (
                        <tr>
                          <td className="px-4 py-3 text-sm font-medium text-gray-500 bg-gray-50">
                            <div className="flex items-center space-x-2">
                              <User className="w-4 h-4 text-gray-400" />
                              <span>Assigned Vet</span>
                            </div>
                          </td>
                          <td className="px-4 py-3 text-sm text-gray-900">
                            <div>
                              <p className="font-medium">{assignedVet.full_name || assignedVet.email}</p>
                              {assignedVet.email && assignedVet.full_name && <p className="text-gray-500">{assignedVet.email}</p>}
                            </div>
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>

                {/* Pets */}
                {appointment.pets && appointment.pets.length > 0 && (
                  <div className="space-y-4">
                    <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wider">
                      Pets ({appointment.pets.length})
                    </h3>
                    <div className="space-y-2">
                      {appointment.pets.map((pet) => (
                        <div
                          key={pet.id}
                          className="p-3 border border-gray-200 rounded-lg hover:border-blue-300 hover:bg-blue-50 transition-colors"
                        >
                          <div className="flex items-start space-x-3">
                            <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center flex-shrink-0">
                              <PawPrint className="w-4 h-4 text-green-600" />
                            </div>
                            <div className="flex-1">
                              <p className="text-base font-medium text-gray-900">{pet.name}</p>
                              <p className="text-sm text-gray-500">
                                {pet.species}
                                {pet.breed && ` • ${pet.breed}`}
                              </p>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Description */}
                {appointment.description && (
                  <div className="space-y-4">
                    <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wider">
                      Description
                    </h3>
                    <p className="text-base text-gray-900 whitespace-pre-wrap">{appointment.description}</p>
                  </div>
                )}

                {/* Notes */}
                {appointment.notes && (
                  <div className="space-y-4">
                    <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wider">
                      Notes
                    </h3>
                    <p className="text-base text-gray-900 whitespace-pre-wrap">{appointment.notes}</p>
                  </div>
                )}

                {/* Metadata */}
                <div className="pt-6 border-t border-gray-200 text-sm text-gray-500">
                  <div className="flex items-center space-x-4">
                    <span>Created {new Date(appointment.created_at).toLocaleDateString()}</span>
                    {appointment.updated_at !== appointment.created_at && (
                      <>
                        <span>•</span>
                        <span>Updated {new Date(appointment.updated_at).toLocaleDateString()}</span>
                      </>
                    )}
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default AppointmentDetailModal;

