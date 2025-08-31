import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { 
  Calendar, 
  Clock, 
  User, 
  Stethoscope, 
  AlertCircle,
  CheckCircle,
  XCircle,
  Plus
} from 'lucide-react';
import { Appointment, AppointmentStatus, AppointmentType } from '../../types/appointment';
import { API_ENDPOINTS } from '../../config/api';
import { getAuthHeaders } from '../../utils/authUtils';

interface AppointmentsListProps {
  petOwnerId?: string;
  petId?: string;
  showHeader?: boolean;
  maxItems?: number;
  showCreateButton?: boolean;
  title?: string;
}

const AppointmentsList: React.FC<AppointmentsListProps> = ({ 
  petOwnerId, 
  petId,
  showHeader = true,
  maxItems,
  showCreateButton = false,
  title = "Scheduled Appointments"
}) => {
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (petOwnerId) {
      fetchAppointmentsByOwner();
    }
  }, [petOwnerId]);

  const fetchAppointmentsByOwner = async () => {
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
      
      // Filter for scheduled/confirmed appointments and optionally by pet
      let filteredAppointments = data.filter((apt: Appointment) => 
        apt.status === AppointmentStatus.SCHEDULED || apt.status === AppointmentStatus.CONFIRMED
      );

      // If petId is provided, filter appointments that include this pet
      if (petId) {
        filteredAppointments = filteredAppointments.filter((apt: Appointment) =>
          apt.pets.some(pet => pet.id === petId)
        );
      }

      // Sort by appointment date
      filteredAppointments.sort((a: Appointment, b: Appointment) => 
        new Date(a.appointment_date).getTime() - new Date(b.appointment_date).getTime()
      );

      // Limit results if maxItems is specified
      if (maxItems) {
        filteredAppointments = filteredAppointments.slice(0, maxItems);
      }

      setAppointments(filteredAppointments);
    } catch (err) {
      console.error('Error fetching appointments:', err);
      setError(err instanceof Error ? err.message : 'Failed to load appointments');
    } finally {
      setLoading(false);
    }
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
      case AppointmentStatus.SCHEDULED:
        return <Clock className="w-4 h-4 text-blue-500" />;
      case AppointmentStatus.CONFIRMED:
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case AppointmentStatus.CANCELLED:
        return <XCircle className="w-4 h-4 text-red-500" />;
      default:
        return <Calendar className="w-4 h-4 text-gray-500" />;
    }
  };

  const getStatusColor = (status: AppointmentStatus) => {
    switch (status) {
      case AppointmentStatus.SCHEDULED:
        return 'bg-blue-100 text-blue-800';
      case AppointmentStatus.CONFIRMED:
        return 'bg-green-100 text-green-800';
      case AppointmentStatus.CANCELLED:
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getTypeIcon = (type: AppointmentType) => {
    switch (type) {
      case AppointmentType.EMERGENCY:
        return <AlertCircle className="w-4 h-4 text-red-500" />;
      case AppointmentType.SURGERY:
        return <Stethoscope className="w-4 h-4 text-purple-500" />;
      default:
        return <Calendar className="w-4 h-4 text-blue-500" />;
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-8">
        <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
        <span className="ml-2 text-gray-600">Loading appointments...</span>
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
          {showCreateButton && (
            <Link
              to="/appointments/new"
              className="inline-flex items-center px-3 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-md transition-colors duration-200"
            >
              <Plus className="w-4 h-4 mr-2" />
              Schedule Appointment
            </Link>
          )}
        </div>
      )}

      {appointments.length === 0 ? (
        <div className="text-center py-8">
          <Calendar className="w-12 h-12 mx-auto text-gray-300 mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No Scheduled Appointments</h3>
          <p className="text-gray-600">
            {petId ? 'This pet has no upcoming appointments.' : 'No upcoming appointments found.'}
          </p>
          {showCreateButton && (
            <Link
              to="/appointments/new"
              className="inline-flex items-center px-4 py-2 mt-4 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-md transition-colors duration-200"
            >
              <Plus className="w-4 h-4 mr-2" />
              Schedule First Appointment
            </Link>
          )}
        </div>
      ) : (
        <div className="space-y-3">
          {appointments.map((appointment) => (
            <div
              key={appointment.id}
              className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow duration-200"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center mb-2">
                    {getTypeIcon(appointment.appointment_type)}
                    <h4 className="ml-2 text-lg font-medium text-gray-900">
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
                  </div>
                </div>

                <div className="flex items-center ml-4">
                  {getStatusIcon(appointment.status)}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default AppointmentsList;
