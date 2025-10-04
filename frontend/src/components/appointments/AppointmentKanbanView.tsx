import React, { useMemo, useState, useEffect } from 'react';
import { format, parseISO, startOfDay, isSameDay } from 'date-fns';
import { ChevronLeft, ChevronRight, Calendar, User } from 'lucide-react';
import { API_BASE_URL } from '../../config/api';
import { useAuth } from '../../contexts/AuthContext';

interface AppointmentKanbanViewProps {
  appointments: any[];
  onSelectAppointment: (appointmentId: string) => void;
  currentDate: Date;
  onNavigate: (date: Date) => void;
}

interface TeamMember {
  id: string;
  full_name: string;
  email: string;
  role: string;
}

const AppointmentKanbanView: React.FC<AppointmentKanbanViewProps> = ({
  appointments,
  onSelectAppointment,
  currentDate,
  onNavigate,
}) => {
  const { user } = useAuth();
  const [teamMembers, setTeamMembers] = useState<TeamMember[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchTeamMembers();
  }, [user?.practice_id]);

  const fetchTeamMembers = async () => {
    try {
      const token = localStorage.getItem('access_token');
      
      console.log('Fetching team members for practice:', user?.practice_id);
      console.log('User object:', user);
      
      if (!user?.practice_id) {
        console.log('No practice_id found, skipping team member fetch');
        setLoading(false);
        return;
      }

      const url = `${API_BASE_URL}/api/v1/practices/${user.practice_id}/members`;
      console.log('Team members API URL:', url);
      
      const response = await fetch(url, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      console.log('Team members response status:', response.status);
      
      if (response.ok) {
        const data = await response.json();
        console.log('Team members raw data:', data);
        const filteredMembers = data.filter((m: TeamMember) => 
          ['VET', 'VET_STAFF', 'PRACTICE_ADMIN'].includes(m.role)
        );
        console.log('Filtered team members:', filteredMembers);
        setTeamMembers(filteredMembers);
      } else {
        const errorText = await response.text();
        console.error('Team members fetch failed:', response.status, errorText);
      }
    } catch (error) {
      console.error('Failed to fetch team members:', error);
    } finally {
      setLoading(false);
    }
  };

  // Filter appointments for the current day
  const todayAppointments = useMemo(() => {
    console.log('All appointments:', appointments);
    console.log('Current date:', currentDate);
    
    const filtered = appointments.filter(apt => {
      try {
        const aptDate = parseISO(apt.appointment_date);
        const matches = isSameDay(aptDate, currentDate);
        console.log(`Appointment ${apt.id} date:`, aptDate, 'matches:', matches);
        return matches;
      } catch (error) {
        console.error('Error parsing appointment date:', error, apt);
        return false;
      }
    });
    
    console.log('Filtered appointments for today:', filtered);
    return filtered;
  }, [appointments, currentDate]);

  // Group appointments by assigned vet
  const appointmentsByVet = useMemo(() => {
    console.log('Team members:', teamMembers);
    
    const grouped: { [key: string]: any[] } = {
      unassigned: []
    };

    // Initialize columns for each team member
    teamMembers.forEach(member => {
      grouped[member.id] = [];
    });

    // Group appointments
    todayAppointments.forEach(apt => {
      console.log('Processing appointment:', apt.id, 'assigned_vet_user_id:', apt.assigned_vet_user_id);
      if (apt.assigned_vet_user_id) {
        if (!grouped[apt.assigned_vet_user_id]) {
          console.log('Creating new group for vet:', apt.assigned_vet_user_id);
          grouped[apt.assigned_vet_user_id] = [];
        }
        grouped[apt.assigned_vet_user_id].push(apt);
        console.log('Added to vet group:', apt.assigned_vet_user_id);
      } else {
        grouped.unassigned.push(apt);
        console.log('Added to unassigned');
      }
    });

    console.log('Final grouped appointments:', grouped);

    // Sort appointments by time within each group
    Object.keys(grouped).forEach(key => {
      grouped[key].sort((a, b) => {
        const timeA = parseISO(a.appointment_date).getTime();
        const timeB = parseISO(b.appointment_date).getTime();
        return timeA - timeB;
      });
    });

    return grouped;
  }, [todayAppointments, teamMembers]);

  const goToPreviousDay = () => {
    const newDate = new Date(currentDate);
    newDate.setDate(newDate.getDate() - 1);
    onNavigate(newDate);
  };

  const goToNextDay = () => {
    const newDate = new Date(currentDate);
    newDate.setDate(newDate.getDate() + 1);
    onNavigate(newDate);
  };

  const goToToday = () => {
    onNavigate(new Date());
  };

  const getStatusColor = (status: string) => {
    switch (status?.toLowerCase()) {
      case 'confirmed': return 'bg-green-100 border-green-300 text-green-800';
      case 'scheduled': return 'bg-blue-100 border-blue-300 text-blue-800';
      case 'completed': return 'bg-gray-100 border-gray-300 text-gray-600';
      case 'cancelled': return 'bg-red-100 border-red-300 text-red-800';
      case 'no_show': return 'bg-orange-100 border-orange-300 text-orange-800';
      default: return 'bg-gray-100 border-gray-300 text-gray-600';
    }
  };

  if (loading) {
    return (
      <div className="p-6 bg-white flex items-center justify-center h-96">
        <div className="text-gray-500">Loading schedule...</div>
      </div>
    );
  }

  return (
    <div className="bg-white h-full flex flex-col">
      {/* Date Navigation Header */}
      <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between bg-gray-50">
        <div className="flex items-center gap-4">
          <button
            onClick={goToPreviousDay}
            className="p-2 hover:bg-gray-200 rounded-md transition-colors"
          >
            <ChevronLeft className="w-5 h-5 text-gray-600" />
          </button>
          <h2 className="text-lg font-semibold text-gray-900">
            {format(currentDate, 'EEEE, MMMM d, yyyy')}
          </h2>
          <button
            onClick={goToNextDay}
            className="p-2 hover:bg-gray-200 rounded-md transition-colors"
          >
            <ChevronRight className="w-5 h-5 text-gray-600" />
          </button>
        </div>
        <button
          onClick={goToToday}
          className="px-4 py-2 text-sm font-medium text-blue-600 hover:bg-blue-50 rounded-md transition-colors flex items-center gap-2"
        >
          <Calendar className="w-4 h-4" />
          Today
        </button>
      </div>

      {/* Kanban Board */}
      <div className="flex-1 overflow-x-auto p-6">
        <div className="flex gap-4 h-full" style={{ minWidth: 'max-content' }}>
          {/* Unassigned Column */}
          {appointmentsByVet.unassigned && appointmentsByVet.unassigned.length > 0 && (
            <div className="flex-shrink-0 w-80">
              <div className="bg-gray-100 rounded-lg p-4 h-full flex flex-col">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-2">
                    <User className="w-5 h-5 text-gray-500" />
                    <h3 className="font-semibold text-gray-700">Unassigned</h3>
                  </div>
                  <span className="text-sm bg-gray-200 text-gray-600 px-2 py-1 rounded-full">
                    {appointmentsByVet.unassigned.length}
                  </span>
                </div>
                <div className="space-y-3 overflow-y-auto">
                  {appointmentsByVet.unassigned.map(apt => (
                    <AppointmentCard
                      key={apt.id}
                      appointment={apt}
                      onClick={() => onSelectAppointment(apt.id)}
                      getStatusColor={getStatusColor}
                    />
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Vet Columns */}
          {teamMembers.map(member => (
            <div key={member.id} className="flex-shrink-0 w-80">
              <div className="bg-gray-50 rounded-lg p-4 h-full flex flex-col border border-gray-200">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center text-white font-semibold">
                      {member.full_name ? member.full_name.charAt(0).toUpperCase() : member.email.charAt(0).toUpperCase()}
                    </div>
                    <div>
                      <h3 className="font-semibold text-gray-900">{member.full_name || member.email.split('@')[0]}</h3>
                      <p className="text-xs text-gray-500">{member.role.replace('_', ' ')}</p>
                    </div>
                  </div>
                  <span className="text-sm bg-blue-100 text-blue-600 px-2 py-1 rounded-full">
                    {appointmentsByVet[member.id]?.length || 0}
                  </span>
                </div>
                <div className="space-y-3 overflow-y-auto">
                  {appointmentsByVet[member.id]?.map(apt => (
                    <AppointmentCard
                      key={apt.id}
                      appointment={apt}
                      onClick={() => onSelectAppointment(apt.id)}
                      getStatusColor={getStatusColor}
                    />
                  )) || (
                    <div className="text-center text-gray-400 text-sm py-8">
                      No appointments
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

// Appointment Card Component
const AppointmentCard: React.FC<{
  appointment: any;
  onClick: () => void;
  getStatusColor: (status: string) => string;
}> = ({ appointment, onClick, getStatusColor }) => {
  const startTime = format(parseISO(appointment.appointment_date), 'h:mm a');
  const endTime = format(
    new Date(parseISO(appointment.appointment_date).getTime() + appointment.duration_minutes * 60000),
    'h:mm a'
  );

  return (
    <div
      onClick={onClick}
      className={`p-3 rounded-md border-2 cursor-pointer transition-all hover:shadow-md ${getStatusColor(appointment.status)}`}
    >
      <div className="flex items-start justify-between mb-2">
        <div className="flex-1">
          <div className="font-medium text-sm mb-1">{appointment.title}</div>
          <div className="text-xs opacity-75">
            {startTime} - {endTime}
          </div>
        </div>
        <span className="text-xs font-semibold px-2 py-1 rounded bg-white bg-opacity-50">
          {appointment.duration_minutes}m
        </span>
      </div>
      {appointment.pets && appointment.pets.length > 0 && (
        <div className="text-xs opacity-75 mt-2">
          🐾 {appointment.pets.map((p: any) => p.name).join(', ')}
        </div>
      )}
    </div>
  );
};

export default AppointmentKanbanView;

