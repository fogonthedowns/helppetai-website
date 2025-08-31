import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { 
  Calendar, 
  Clock, 
  User, 
  FileText, 
  CheckCircle,
  XCircle,
  AlertCircle,
  ExternalLink
} from 'lucide-react';
import { Appointment, AppointmentStatus } from '../../types/appointment';
import { VisitTranscript } from '../../types/visitTranscript';
import { API_ENDPOINTS } from '../../config/api';
import { getAuthHeaders } from '../../utils/authUtils';

interface PastAppointmentsListProps {
  petOwnerId?: string;
  petId?: string;
  showHeader?: boolean;
  maxItems?: number;
  title?: string;
}

const PastAppointmentsList: React.FC<PastAppointmentsListProps> = ({ 
  petOwnerId, 
  petId,
  showHeader = true,
  maxItems,
  title = "Past Appointments"
}) => {
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [transcripts, setTranscripts] = useState<VisitTranscript[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (petOwnerId) {
      fetchPastAppointments();
    }
    if (petId) {
      fetchTranscripts();
    }
  }, [petOwnerId, petId]);

  const fetchPastAppointments = async () => {
    if (!petOwnerId) return;

    try {
      setLoading(true);
      setError(null);

      const response = await fetch(API_ENDPOINTS.APPOINTMENTS.LIST_BY_PET_OWNER(petOwnerId), {
        headers: getAuthHeaders()
      });

      if (!response.ok) {
        throw new Error('Failed to fetch appointments');
      }

      const data = await response.json();
      
      // Filter for completed appointments and optionally by pet
      let filteredAppointments = data.filter((apt: Appointment) => 
        apt.status === AppointmentStatus.COMPLETED
      );

      // If petId is provided, filter appointments that include this pet
      if (petId) {
        filteredAppointments = filteredAppointments.filter((apt: Appointment) =>
          apt.pets.some(pet => pet.id === petId)
        );
      }

      // Sort by appointment date (most recent first)
      filteredAppointments.sort((a: Appointment, b: Appointment) => 
        new Date(b.appointment_date).getTime() - new Date(a.appointment_date).getTime()
      );

      // Limit results if maxItems is specified
      if (maxItems) {
        filteredAppointments = filteredAppointments.slice(0, maxItems);
      }

      setAppointments(filteredAppointments);
    } catch (err) {
      console.error('Error fetching past appointments:', err);
      setError(err instanceof Error ? err.message : 'Failed to load past appointments');
    } finally {
      setLoading(false);
    }
  };

  const fetchTranscripts = async () => {
    if (!petId) return;

    try {
      const response = await fetch(API_ENDPOINTS.VISIT_TRANSCRIPTS.BY_PET(petId), {
        headers: getAuthHeaders()
      });

      if (response.ok) {
        const data = await response.json();
        setTranscripts(Array.isArray(data) ? data : []);
      }
    } catch (err) {
      console.error('Error fetching transcripts:', err);
    }
  };

  const findTranscriptForAppointment = (appointment: Appointment): VisitTranscript | null => {
    if (!transcripts.length) return null;

    // Try to match transcript by date (within same day)
    const appointmentDate = new Date(appointment.appointment_date);
    const appointmentDay = appointmentDate.toDateString();

    return transcripts.find(transcript => {
      const transcriptDate = new Date(transcript.visit_date * 1000);
      const transcriptDay = transcriptDate.toDateString();
      return appointmentDay === transcriptDay;
    }) || null;
  };

  const formatDateTime = (dateString: string) => {
    return new Date(dateString).toLocaleString('en-US', {
      weekday: 'short',
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getStatusIcon = (status: AppointmentStatus) => {
    switch (status) {
      case AppointmentStatus.COMPLETED:
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case AppointmentStatus.CANCELLED:
        return <XCircle className="w-4 h-4 text-red-500" />;
      case AppointmentStatus.NO_SHOW:
        return <AlertCircle className="w-4 h-4 text-orange-500" />;
      default:
        return <Calendar className="w-4 h-4 text-gray-500" />;
    }
  };

  const getStatusColor = (status: AppointmentStatus) => {
    switch (status) {
      case AppointmentStatus.COMPLETED:
        return 'bg-green-100 text-green-800';
      case AppointmentStatus.CANCELLED:
        return 'bg-red-100 text-red-800';
      case AppointmentStatus.NO_SHOW:
        return 'bg-orange-100 text-orange-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-8">
        <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
        <span className="ml-2 text-gray-600">Loading past appointments...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <div className="flex items-center">
          <AlertCircle className="w-5 h-5 text-red-600 mr-2" />
          <p className="text-sm text-red-700">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {showHeader && (
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-900 flex items-center">
            <Calendar className="w-5 h-5 mr-2 text-blue-600" />
            {title}
            {appointments.length > 0 && (
              <span className="ml-2 text-sm text-gray-500">
                ({appointments.length} appointment{appointments.length !== 1 ? 's' : ''})
              </span>
            )}
          </h3>
        </div>
      )}

      {appointments.length === 0 ? (
        <div className="text-center py-8">
          <Calendar className="w-12 h-12 mx-auto text-gray-300 mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No Past Appointments</h3>
          <p className="text-gray-600">
            {petId ? 'This pet has no completed appointments.' : 'No completed appointments found.'}
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {appointments.map((appointment) => {
            const relatedTranscript = findTranscriptForAppointment(appointment);
            
            return (
              <div
                key={appointment.id}
                className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow duration-200"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center mb-2">
                      <h4 className="text-lg font-medium text-gray-900">
                        {appointment.title}
                      </h4>
                      <span className={`ml-3 inline-flex items-center px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(appointment.status)}`}>
                        {appointment.status.replace('_', ' ').toUpperCase()}
                      </span>
                    </div>
                    
                    <div className="space-y-2 text-sm text-gray-600">
                      <div className="flex items-center">
                        <Calendar className="w-4 h-4 mr-2" />
                        <span>{formatDateTime(appointment.appointment_date)}</span>
                      </div>
                      
                      <div className="flex items-center">
                        <Clock className="w-4 h-4 mr-2" />
                        <span>{appointment.duration_minutes} minutes</span>
                      </div>

                      {appointment.pets.length > 0 && (
                        <div className="flex items-center">
                          <User className="w-4 h-4 mr-2" />
                          <span>
                            Pets: {appointment.pets.map(pet => pet.name).join(', ')}
                          </span>
                        </div>
                      )}

                      {appointment.description && (
                        <p className="text-gray-700 mt-2">{appointment.description}</p>
                      )}

                      {/* Related Transcript Link */}
                      {relatedTranscript && (
                        <div className="mt-3 pt-3 border-t border-gray-100">
                          <Link
                            to={`/pets/${petId}/visit-transcripts/${relatedTranscript.uuid}`}
                            className="inline-flex items-center text-sm text-blue-600 hover:text-blue-700 font-medium"
                          >
                            <FileText className="w-4 h-4 mr-1" />
                            View Visit Transcript
                            <ExternalLink className="w-3 h-3 ml-1" />
                          </Link>
                        </div>
                      )}
                    </div>
                  </div>

                  <div className="flex items-center ml-4">
                    {getStatusIcon(appointment.status)}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default PastAppointmentsList;
