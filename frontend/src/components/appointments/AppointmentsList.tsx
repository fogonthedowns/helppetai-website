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
  title = "Recent Appointments"
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
      
      // Filter for relevant appointments (scheduled, confirmed, in_progress, complete) and optionally by pet
      let filteredAppointments = data.filter((apt: Appointment) => 
        apt.status === AppointmentStatus.SCHEDULED || 
        apt.status === AppointmentStatus.CONFIRMED ||
        apt.status === AppointmentStatus.IN_PROGRESS ||
        apt.status === AppointmentStatus.COMPLETE ||
        apt.status === AppointmentStatus.COMPLETED // Legacy
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



  const getStatusColor = (status: AppointmentStatus) => {
    switch (status) {
      case AppointmentStatus.SCHEDULED:
        return 'bg-blue-100 text-blue-800';
      case AppointmentStatus.IN_PROGRESS:
        return 'bg-yellow-100 text-yellow-800';
      case AppointmentStatus.COMPLETE:
      case AppointmentStatus.COMPLETED: // Legacy
        return 'bg-green-100 text-green-800';
      case AppointmentStatus.ERROR:
        return 'bg-red-100 text-red-800';
      case AppointmentStatus.CONFIRMED:
        return 'bg-emerald-100 text-emerald-800';
      case AppointmentStatus.CANCELLED:
        return 'bg-gray-100 text-gray-800';
      case AppointmentStatus.NO_SHOW:
        return 'bg-orange-100 text-orange-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusIcon = (status: AppointmentStatus) => {
    switch (status) {
      case AppointmentStatus.SCHEDULED:
        return <Calendar className="w-3 h-3 mr-1" />;
      case AppointmentStatus.IN_PROGRESS:
        return <Clock className="w-3 h-3 mr-1" />;
      case AppointmentStatus.COMPLETE:
      case AppointmentStatus.COMPLETED: // Legacy
        return <CheckCircle className="w-3 h-3 mr-1" />;
      case AppointmentStatus.ERROR:
        return <XCircle className="w-3 h-3 mr-1" />;
      case AppointmentStatus.CONFIRMED:
        return <CheckCircle className="w-3 h-3 mr-1" />;
      default:
        return null;
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
        <div className="mb-4">
          <div className="flex items-center justify-between mb-3">
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
          {showCreateButton && (
            <Link
              to="/appointments/new"
              className="inline-flex items-center px-3 py-1.5 text-sm font-medium text-gray-700 bg-gray-50 hover:bg-gray-100 border border-gray-300 rounded-md transition-colors duration-200 w-full justify-center"
            >
              <Plus className="w-4 h-4 mr-1.5" />
              Schedule Appointment
            </Link>
          )}
        </div>
      )}

      {appointments.length === 0 ? (
        <div className="text-center py-8">
          <Calendar className="w-12 h-12 mx-auto text-gray-300 mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No Recent Appointments</h3>
          <p className="text-gray-600">
            {petId ? 'This pet has no recent appointments.' : 'No recent appointments found.'}
          </p>
          {showCreateButton && (
            <Link
              to="/appointments/new"
              className="inline-flex items-center px-3 py-1.5 mt-4 text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 border border-gray-300 rounded-md transition-colors duration-200"
            >
              <Plus className="w-4 h-4 mr-1.5" />
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
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="font-medium text-gray-900">
                    {appointment.title}
                  </h4>
                  <p className="text-sm text-gray-600">
                    {formatDateTime(appointment.appointment_date)}
                  </p>
                </div>
                <span className={`inline-flex items-center px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(appointment.status)}`}>
                  {getStatusIcon(appointment.status)}
                  {appointment.status.replace('_', ' ').toUpperCase()}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default AppointmentsList;
