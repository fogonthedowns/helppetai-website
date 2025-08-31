import React from 'react';
import { Link } from 'react-router-dom';
import { Appointment, AppointmentStatus } from '../../types/appointment';
import { Calendar, Clock, User, RefreshCw } from 'lucide-react';

interface TodaysScheduleCardProps {
  appointments: Appointment[];
  nextAppointment?: Appointment;
  currentAppointment?: Appointment;
  completedCount: number;
  remainingCount: number;
  onRefresh: () => void;
  selectedDate?: Date;
}

export const TodaysScheduleCard: React.FC<TodaysScheduleCardProps> = ({
  appointments,
  nextAppointment,
  currentAppointment,
  completedCount,
  remainingCount,
  onRefresh,
  selectedDate
}) => {
  const formatSelectedDate = () => {
    if (!selectedDate) return "Today's Schedule";
    
    const today = new Date();
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);
    const tomorrow = new Date(today);
    tomorrow.setDate(tomorrow.getDate() + 1);

    if (selectedDate.toDateString() === today.toDateString()) {
      return "Today's Schedule";
    } else if (selectedDate.toDateString() === yesterday.toDateString()) {
      return "Yesterday's Schedule";
    } else if (selectedDate.toDateString() === tomorrow.toDateString()) {
      return "Tomorrow's Schedule";
    } else {
      return `Schedule for ${selectedDate.toLocaleDateString('en-US', { 
        weekday: 'short', 
        month: 'short', 
        day: 'numeric' 
      })}`;
    }
  };
  const getStatusColor = (status: AppointmentStatus) => {
    switch (status) {
      case AppointmentStatus.SCHEDULED:
        return 'bg-blue-100 text-blue-800';
      case AppointmentStatus.CONFIRMED:
        return 'bg-green-100 text-green-800';
      case AppointmentStatus.COMPLETED:
        return 'bg-gray-100 text-gray-800';
      case AppointmentStatus.CANCELLED:
        return 'bg-red-100 text-red-800';
      case AppointmentStatus.NO_SHOW:
        return 'bg-orange-100 text-orange-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const formatTime = (dateString: string) => {
    return new Date(dateString).toLocaleTimeString('en-US', {
      hour: 'numeric',
      minute: '2-digit',
      hour12: true
    });
  };

  const isCurrentTime = (appointment: Appointment) => {
    const now = new Date();
    const appointmentTime = new Date(appointment.appointment_date);
    const endTime = new Date(appointmentTime.getTime() + appointment.duration_minutes * 60000);
    return now >= appointmentTime && now <= endTime;
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200">
      {/* Card Header */}
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <Calendar className="w-5 h-5 text-blue-600 mr-2" />
            <h2 className="text-xl font-semibold text-gray-900">{formatSelectedDate()}</h2>
          </div>
          <div className="flex items-center space-x-4">
            <div className="text-sm text-gray-600">
              {completedCount} of {appointments.length} completed
            </div>
            <button
              onClick={onRefresh}
              className="p-2 text-gray-400 hover:text-gray-600 transition-colors"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
          </div>
        </div>
        
        {/* Progress Bar */}
        {appointments.length > 0 && (
          <div className="mt-3">
            <div className="flex justify-between text-sm text-gray-600 mb-1">
              <span>Progress</span>
              <span>{Math.round((completedCount / appointments.length) * 100)}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div 
                className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${(completedCount / appointments.length) * 100}%` }}
              />
            </div>
          </div>
        )}
      </div>

      {/* Next Up Section */}
      {nextAppointment && (
        <div className="px-6 py-4 bg-blue-50 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-medium text-blue-900 mb-1">Next Up</h3>
              <div className="flex items-center text-blue-800">
                <Clock className="w-4 h-4 mr-1" />
                <span className="font-medium">{formatTime(nextAppointment.appointment_date)}</span>
                <span className="mx-2">•</span>
                <span>{nextAppointment.title}</span>
              </div>
            </div>
            <Link
              to={`/visit-transcripts/record/${nextAppointment.id}`}
              className="bg-blue-600 text-white px-3 py-1 rounded-md text-sm hover:bg-blue-700 transition-colors"
            >
              Start Visit
            </Link>
          </div>
        </div>
      )}

      {/* Current Appointment */}
      {currentAppointment && (
        <div className="px-6 py-4 bg-green-50 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-medium text-green-900 mb-1">In Progress</h3>
              <div className="flex items-center text-green-800">
                <div className="w-2 h-2 bg-green-500 rounded-full mr-2 animate-pulse" />
                <span className="font-medium">{currentAppointment.title}</span>
              </div>
            </div>
            <Link
              to={`/visit-transcripts/record/${currentAppointment.id}`}
              className="bg-green-600 text-white px-3 py-1 rounded-md text-sm hover:bg-green-700 transition-colors"
            >
              Continue
            </Link>
          </div>
        </div>
      )}

      {/* Appointments List */}
      <div className="px-6 py-4">
        {appointments.length === 0 ? (
          <div className="text-center py-8">
            <Calendar className="w-12 h-12 text-gray-300 mx-auto mb-3" />
            <p className="text-gray-500">
              No appointments scheduled for {selectedDate?.toDateString() === new Date().toDateString() ? 'today' : 'this date'}
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {appointments.map((appointment) => (
              <div
                key={appointment.id}
                className={`p-4 rounded-lg border transition-all duration-200 hover:shadow-md ${
                  isCurrentTime(appointment) 
                    ? 'border-green-200 bg-green-50' 
                    : 'border-gray-200 bg-gray-50'
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center mb-2">
                      <span className="font-medium text-gray-900 mr-3">
                        {formatTime(appointment.appointment_date)}
                      </span>
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(appointment.status)}`}>
                        {appointment.status}
                      </span>
                      {isCurrentTime(appointment) && (
                        <span className="ml-2 px-2 py-1 bg-green-100 text-green-800 rounded-full text-xs font-medium">
                          Now
                        </span>
                      )}
                    </div>
                    
                    <h4 className="font-medium text-gray-900 mb-1">{appointment.title}</h4>
                    
                    <div className="flex items-center text-sm text-gray-600 space-x-4">
                      <div className="flex items-center">
                        <User className="w-4 h-4 mr-1" />
                        <span>{appointment.pets.map(pet => pet.name).join(', ')}</span>
                      </div>
                      <div className="flex items-center">
                        <Clock className="w-4 h-4 mr-1" />
                        <span>{appointment.duration_minutes} min</span>
                      </div>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-2">
                    {appointment.pets[0] && (
                      <Link
                        to={`/pets/${appointment.pets[0].id}`}
                        className="text-blue-600 hover:text-blue-800 text-sm font-medium"
                      >
                        View Pet
                      </Link>
                    )}
                    <Link
                      to={`/visit-transcripts/record/${appointment.id}`}
                      className="bg-blue-600 text-white px-3 py-1 rounded-md text-sm hover:bg-blue-700 transition-colors"
                    >
                      {appointment.status === AppointmentStatus.COMPLETED ? 'Review' : 'Start'}
                    </Link>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
