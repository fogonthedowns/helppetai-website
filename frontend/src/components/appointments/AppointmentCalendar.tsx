import React, { useState, useMemo } from 'react';
import { Calendar, dateFnsLocalizer, View } from 'react-big-calendar';
import format from 'date-fns/format';
import parse from 'date-fns/parse';
import startOfWeek from 'date-fns/startOfWeek';
import getDay from 'date-fns/getDay';
import enUS from 'date-fns/locale/en-US';
import { parseISO } from 'date-fns';
import 'react-big-calendar/lib/css/react-big-calendar.css';

const locales = {
  'en-US': enUS,
};

const localizer = dateFnsLocalizer({
  format,
  parse,
  startOfWeek,
  getDay,
  locales,
});

interface AppointmentCalendarProps {
  appointments: any[];
  onSelectAppointment: (appointmentId: string) => void;
  onSelectSlot?: (slotInfo: { start: Date; end: Date }) => void;
  currentDate?: Date;
  onNavigate?: (date: Date) => void;
  currentView?: View;
  onViewChange?: (view: View) => void;
}

const AppointmentCalendar: React.FC<AppointmentCalendarProps> = ({
  appointments,
  onSelectAppointment,
  onSelectSlot,
  currentDate,
  onNavigate,
  currentView,
  onViewChange,
}) => {
  const [view, setView] = useState<View>(currentView || 'week');
  const [date, setDate] = useState(currentDate || new Date());

  // Use controlled props if provided, otherwise use local state
  const effectiveView = currentView || view;
  const effectiveDate = currentDate || date;

  const handleViewChange = (newView: View) => {
    if (onViewChange) {
      onViewChange(newView);
    } else {
      setView(newView);
    }
  };

  const handleNavigate = (newDate: Date) => {
    if (onNavigate) {
      onNavigate(newDate);
    } else {
      setDate(newDate);
    }
  };

  // Convert appointments to calendar events
  const events = useMemo(() => {
    return appointments.map((appointment) => {
      // Parse UTC date and convert to local time
      const start = parseISO(appointment.appointment_date);
      const end = new Date(start.getTime() + appointment.duration_minutes * 60000);

      // Get pet names
      const petNames = appointment.pets?.map((pet: any) => pet.name).join(', ') || 'No pets';
      
      // Get pet owner name
      const ownerName = appointment.pet_owner?.full_name || 'Unknown';

      return {
        id: appointment.id,
        title: `${petNames} - ${ownerName}`,
        start,
        end,
        resource: appointment,
        // Color coding by status
        status: appointment.status,
      };
    });
  }, [appointments]);

  // Event style getter for color coding
  const eventStyleGetter = (event: any) => {
    let backgroundColor = '#3182ce'; // default blue

    switch (event.status) {
      case 'scheduled':
        backgroundColor = '#3182ce'; // blue
        break;
      case 'confirmed':
        backgroundColor = '#38a169'; // green
        break;
      case 'completed':
        backgroundColor = '#718096'; // gray
        break;
      case 'cancelled':
        backgroundColor = '#e53e3e'; // red
        break;
      case 'no_show':
        backgroundColor = '#ed8936'; // orange
        break;
    }

    return {
      style: {
        backgroundColor,
        borderRadius: '5px',
        opacity: 0.9,
        color: 'white',
        border: '0px',
        display: 'block',
        fontSize: '13px',
        padding: '2px 5px',
      },
    };
  };

  const handleSelectEvent = (event: any) => {
    onSelectAppointment(event.id);
  };

  const handleSelectSlot = (slotInfo: any) => {
    if (onSelectSlot) {
      onSelectSlot({
        start: slotInfo.start,
        end: slotInfo.end,
      });
    }
  };

  return (
    <div className="h-full bg-white">
      <Calendar
        localizer={localizer}
        events={events}
        startAccessor="start"
        endAccessor="end"
        style={{ height: 'calc(100vh - 200px)', minHeight: '600px' }}
        view={effectiveView}
        onView={handleViewChange}
        date={effectiveDate}
        onNavigate={handleNavigate}
        onSelectEvent={handleSelectEvent}
        onSelectSlot={handleSelectSlot}
        selectable
        eventPropGetter={eventStyleGetter}
        popup
        step={15}
        timeslots={4}
        defaultView="week"
        views={['month', 'week', 'day', 'agenda']}
        toolbar={true}
      />
      
      {/* Legend */}
      <div className="flex items-center gap-4 p-4 border-t border-gray-200 text-xs">
        <span className="font-medium text-gray-700">Status:</span>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded bg-blue-600"></div>
          <span>Scheduled</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded bg-green-600"></div>
          <span>Confirmed</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded bg-gray-600"></div>
          <span>Completed</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded bg-red-600"></div>
          <span>Cancelled</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded bg-orange-600"></div>
          <span>No Show</span>
        </div>
      </div>
    </div>
  );
};

export default AppointmentCalendar;

