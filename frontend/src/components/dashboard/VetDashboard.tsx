import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { API_ENDPOINTS } from '../../config/api';
import { VetDashboard as VetDashboardType, TodayWorkSummary } from '../../types/dashboard';
import { TodaysScheduleCard } from './TodaysScheduleCard';
import { QuickActionsCard } from './QuickActionsCard';
import { Clock, AlertCircle, Calendar, FileText, CheckCircle, TrendingUp, ChevronLeft, ChevronRight } from 'lucide-react';

// Inline StatsOverview component to avoid module resolution issues
const StatsOverview: React.FC<{ stats: any }> = ({ stats }) => {
  const statCards = [
    {
      icon: <Calendar className="w-8 h-8 text-blue-600" />,
      title: 'Today\'s Appointments',
      value: stats.appointments_today,
      color: 'bg-blue-50 border-blue-200',
      textColor: 'text-blue-900'
    },

    {
      icon: <CheckCircle className="w-8 h-8 text-green-600" />,
      title: 'Completed Visits',
      value: stats.completed_visits,
      color: 'bg-green-50 border-green-200',
      textColor: 'text-green-900'
    },
    {
      icon: <TrendingUp className="w-8 h-8 text-purple-600" />,
      title: 'Completion Rate',
      value: stats.appointments_today > 0 
        ? `${Math.round((stats.completed_visits / stats.appointments_today) * 100)}%`
        : '0%',
      color: 'bg-purple-50 border-purple-200',
      textColor: 'text-purple-900'
    }
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {statCards.map((stat, index) => (
        <div
          key={index}
          className={`${stat.color} border rounded-xl p-6 transition-all duration-200 hover:shadow-md`}
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600 mb-1">{stat.title}</p>
              <p className={`text-3xl font-bold ${stat.textColor}`}>
                {stat.value}
              </p>
            </div>
            <div className="flex-shrink-0">
              {stat.icon}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};

const VetDashboard: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const { date: dateParam } = useParams<{ date?: string }>();
  const [dashboard, setDashboard] = useState<VetDashboardType | null>(null);
  const [todayWork, setTodayWork] = useState<TodayWorkSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Initialize selectedDate from URL parameter or default to today
  const [selectedDate, setSelectedDate] = useState<Date>(() => {
    if (dateParam) {
      try {
        // Parse YYYY-MM-DD format explicitly to avoid timezone issues
        const [year, month, day] = dateParam.split('-').map(Number);
        if (year && month && day) {
          const parsedDate = new Date(year, month - 1, day); // month is 0-indexed
          // Validate the date
          if (!isNaN(parsedDate.getTime())) {
            return parsedDate;
          }
        }
      } catch (e) {
        // Invalid date, fall back to today
      }
    }
    return new Date();
  });

  // Handle URL parameter changes (browser back/forward)
  useEffect(() => {
    if (dateParam) {
      try {
        // Parse YYYY-MM-DD format explicitly to avoid timezone issues
        const [year, month, day] = dateParam.split('-').map(Number);
        if (year && month && day) {
          const parsedDate = new Date(year, month - 1, day); // month is 0-indexed
          if (!isNaN(parsedDate.getTime()) && parsedDate.toDateString() !== selectedDate.toDateString()) {
            setSelectedDate(parsedDate);
          }
        } else {
          // Invalid date format in URL, redirect to today
          navigate('/dashboard/vet');
        }
      } catch (e) {
        // Invalid date in URL, redirect to today
        navigate('/dashboard/vet');
      }
    } else {
      // No date parameter, should be today
      const today = new Date();
      if (selectedDate.toDateString() !== today.toDateString()) {
        setSelectedDate(today);
      }
    }
  }, [dateParam, navigate, selectedDate]);

  useEffect(() => {
    if (user?.id) {
      fetchDashboardData();
      // Set up auto-refresh every 30 seconds only for today
      const isToday = selectedDate.toDateString() === new Date().toDateString();
      if (isToday) {
        const interval = setInterval(fetchDashboardData, 30000);
        return () => clearInterval(interval);
      }
    }
  }, [user?.id, selectedDate]);

  const fetchDashboardData = async () => {
    if (!user?.id) return;

    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      
      // Format selected date as YYYY-MM-DD
      const dateStr = selectedDate.toISOString().split('T')[0];
      
      // Fetch both dashboard and today's work summary for selected date
      const [dashboardResponse, todayResponse] = await Promise.all([
        fetch(`${API_ENDPOINTS.DASHBOARD.VET_DASHBOARD(user.id)}?date=${dateStr}`, {
          headers: { 'Authorization': `Bearer ${token}` }
        }),
        fetch(`${API_ENDPOINTS.DASHBOARD.VET_TODAY(user.id)}?date=${dateStr}`, {
          headers: { 'Authorization': `Bearer ${token}` }
        })
      ]);

      if (!dashboardResponse.ok || !todayResponse.ok) {
        throw new Error('Failed to fetch dashboard data');
      }

      const dashboardData = await dashboardResponse.json();
      const todayData = await todayResponse.json();
      
      setDashboard(dashboardData);
      setTodayWork(todayData);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load dashboard');
    } finally {
      setLoading(false);
    }
  };

  const updateDateAndURL = (newDate: Date) => {
    setSelectedDate(newDate);
    const dateStr = newDate.toISOString().split('T')[0];
    const isToday = newDate.toDateString() === new Date().toDateString();
    
    // Navigate to URL with date parameter, or base URL for today
    if (isToday) {
      navigate('/dashboard/vet');
    } else {
      navigate(`/dashboard/vet/${dateStr}`);
    }
  };

  const goToPreviousDay = () => {
    const previousDay = new Date(selectedDate);
    previousDay.setDate(previousDay.getDate() - 1);
    updateDateAndURL(previousDay);
  };

  const goToNextDay = () => {
    const nextDay = new Date(selectedDate);
    nextDay.setDate(nextDay.getDate() + 1);
    updateDateAndURL(nextDay);
  };

  const goToToday = () => {
    updateDateAndURL(new Date());
  };

  const formatSelectedDate = () => {
    const today = new Date();
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);
    const tomorrow = new Date(today);
    tomorrow.setDate(tomorrow.getDate() + 1);

    // Debug logging
    console.log('Date comparison debug:');
    console.log('selectedDate:', selectedDate.toDateString());
    console.log('today:', today.toDateString());
    console.log('yesterday:', yesterday.toDateString());
    console.log('tomorrow:', tomorrow.toDateString());

    if (selectedDate.toDateString() === today.toDateString()) {
      return 'Today';
    } else if (selectedDate.toDateString() === yesterday.toDateString()) {
      return 'Yesterday';
    } else if (selectedDate.toDateString() === tomorrow.toDateString()) {
      return 'Tomorrow';
    } else {
      return selectedDate.toLocaleDateString('en-US', { 
        weekday: 'long', 
        year: 'numeric', 
        month: 'long', 
        day: 'numeric' 
      });
    }
  };

  if (!user || (user.role !== 'VET' && user.role !== 'VET_STAFF')) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <AlertCircle className="w-16 h-16 text-red-500 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Access Denied</h2>
          <p className="text-gray-600">This dashboard is only available to veterinary staff.</p>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <AlertCircle className="w-16 h-16 text-red-500 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Error Loading Dashboard</h2>
          <p className="text-gray-600 mb-4">{error}</p>
          <button 
            onClick={fetchDashboardData}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-6 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900" style={{
                fontFamily: 'Calibre, ui-sans-serif, system-ui, -apple-system, "system-ui", "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans", sans-serif'
              }}>
                Welcome back, Dr. {user.full_name}
              </h1>
              
              {/* Date Navigation */}
              <div className="flex items-center mt-3 space-x-4">
                <div className="flex items-center bg-gray-100 rounded-lg p-1">
                  <button
                    onClick={goToPreviousDay}
                    className="p-2 hover:bg-white rounded-md transition-colors"
                    title="Previous day"
                  >
                    <ChevronLeft className="w-4 h-4 text-gray-600" />
                  </button>
                  
                  <div className="px-4 py-2 text-sm font-medium text-gray-900 min-w-[120px] text-center">
                    {formatSelectedDate()}
                  </div>
                  
                  <button
                    onClick={goToNextDay}
                    className="p-2 hover:bg-white rounded-md transition-colors"
                    title="Next day"
                  >
                    <ChevronRight className="w-4 h-4 text-gray-600" />
                  </button>
                </div>
                
                {selectedDate.toDateString() !== new Date().toDateString() && (
                  <button
                    onClick={goToToday}
                    className="px-3 py-1 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                  >
                    Today
                  </button>
                )}
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <div className="flex items-center text-sm text-gray-500">
                <Clock className="w-4 h-4 mr-1" />
                Last updated: {new Date().toLocaleTimeString()}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Dashboard Content */}
      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* Stats Overview */}
        {dashboard && <StatsOverview stats={dashboard.stats} />}

        {/* Main Dashboard - Just Today's Schedule */}
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 mt-8">
          {/* Schedule for Selected Date - Takes up 3/4 of the width */}
          <div className="lg:col-span-3">
            {todayWork && (
              <TodaysScheduleCard 
                appointments={todayWork.appointments_today}
                nextAppointment={todayWork.next_appointment}
                currentAppointment={todayWork.current_appointment}
                completedCount={todayWork.completed_count}
                remainingCount={todayWork.remaining_count}
                onRefresh={fetchDashboardData}
                selectedDate={selectedDate}
              />
            )}
          </div>

          {/* Quick Actions - Takes up 1/4 of the width */}
          <div>
            <QuickActionsCard />
          </div>
        </div>
      </div>
    </div>
  );
};

export default VetDashboard;
