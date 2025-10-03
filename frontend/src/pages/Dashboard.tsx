import React, { useState, useEffect } from 'react';
import { Link, useNavigate, Routes, Route, useLocation } from 'react-router-dom';
import { Phone, Users, Clock, Calendar, Plus, Search, Home, Settings, HelpCircle, UserCircle, LogOut, CalendarCheck, Bot, UserPlus, Trash2, Mail, X, CheckCircle } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { API_BASE_URL } from '../config/api';
import PetOwnerDetailModal from '../components/pet-owners/PetOwnerDetailModal';
import PetOwnerCreateModal from '../components/pet-owners/PetOwnerCreateModal';
import PetDetailModal from '../components/pets/PetDetailModal';
import AppointmentCreateModal from '../components/appointments/AppointmentCreateModal';
import AppointmentDetailModal from '../components/appointments/AppointmentDetailModal';
import AppointmentEditModal from '../components/appointments/AppointmentEditModal';
import AppointmentForm from '../components/appointments/AppointmentForm';
import ConfirmDialog from '../components/common/ConfirmDialog';
import VoiceAgentSection from '../components/voice-agents/VoiceAgentSection';
import PhoneConfigSection from '../components/voice-agents/PhoneConfigSection';
import CallHistorySection from '../components/calls/CallHistorySection';
import AppointmentCalendar from '../components/appointments/AppointmentCalendar';

const Dashboard: React.FC = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Determine active section from URL
  const getActiveSectionFromPath = (): 'agents' | 'phones' | 'calls' | 'schedule' | 'owners' | 'team' | 'appointments' => {
    const path = location.pathname;
    if (path.includes('/pet_owners')) return 'owners';
    if (path.includes('/appointments')) return 'appointments';
    if (path.includes('/calls')) return 'calls';
    if (path.includes('/schedule')) return 'schedule';
    if (path.includes('/phones')) return 'phones';
    if (path.includes('/team')) return 'team';
    if (path.includes('/agents')) return 'agents';
    return 'agents'; // default
  };

  const activeSection = getActiveSectionFromPath();

  // Real data from API
  const [voiceAgent, setVoiceAgent] = useState<any>(null);
  const [calls, setCalls] = useState<any[]>([]);
  const [schedule, setSchedule] = useState<any[]>([]);
  const [owners, setOwners] = useState<any[]>([]);
  const [teamMembers, setTeamMembers] = useState<any[]>([]);
  const [pendingInvites, setPendingInvites] = useState<any[]>([]);
  const [appointments, setAppointments] = useState<any[]>([]);
  
  // Modal state
  const [selectedOwnerId, setSelectedOwnerId] = useState<string | null>(null);
  const [isOwnerModalOpen, setIsOwnerModalOpen] = useState(false);
  const [isCreateOwnerOpen, setIsCreateOwnerOpen] = useState(false);
  const [isCreateAppointmentOpen, setIsCreateAppointmentOpen] = useState(false);
  const [selectedPetId, setSelectedPetId] = useState<string | null>(null);
  const [isPetDetailModalOpen, setIsPetDetailModalOpen] = useState(false);
  const [selectedAppointmentId, setSelectedAppointmentId] = useState<string | null>(null);
  const [isAppointmentModalOpen, setIsAppointmentModalOpen] = useState(false);
  const [isAppointmentEditModalOpen, setIsAppointmentEditModalOpen] = useState(false);
  const [ownerMenuOpen, setOwnerMenuOpen] = useState<string | null>(null);
  
  // Team invite state
  const [showInviteModal, setShowInviteModal] = useState(false);
  const [inviteEmail, setInviteEmail] = useState('');
  const [isInviting, setIsInviting] = useState(false);
  const [inviteSuccess, setInviteSuccess] = useState<string | null>(null);
  const [inviteError, setInviteError] = useState<string | null>(null);
  const [revokeInviteId, setRevokeInviteId] = useState<string | null>(null);
  const [removeMemberId, setRemoveMemberId] = useState<string | null>(null);

  // Calendar state
  const [calendarDate, setCalendarDate] = useState(new Date());
  const [calendarView, setCalendarView] = useState<any>('week');

  const navigationItems = [
    { key: 'agents' as const, label: 'Agents', icon: <Bot className="w-4 h-4" />, section: 'BUILD', path: '/dashboard/agents' },
    { key: 'phones' as const, label: 'Phone Numbers', icon: <Phone className="w-4 h-4" />, section: 'DEPLOY', path: '/dashboard/phones' },
    { key: 'appointments' as const, label: 'Appointments', icon: <CalendarCheck className="w-4 h-4" />, section: 'MONITOR', path: '/dashboard/appointments' },
    { key: 'calls' as const, label: 'Call History', icon: <Clock className="w-4 h-4" />, section: 'MONITOR', path: '/dashboard/calls' },
    { key: 'schedule' as const, label: 'Work Schedule', icon: <Calendar className="w-4 h-4" />, section: 'MONITOR', path: '/dashboard/schedule' },
    { key: 'owners' as const, label: 'Pet Owners', icon: <Users className="w-4 h-4" />, section: 'MONITOR', path: '/dashboard/pet_owners' },
    { key: 'team' as const, label: 'Team', icon: <UserCircle className="w-4 h-4" />, section: 'MONITOR', path: '/dashboard/team' },
  ];

  // Redirect to default tab if on base /dashboard
  useEffect(() => {
    if (location.pathname === '/dashboard' || location.pathname === '/dashboard/') {
      navigate('/dashboard/agents', { replace: true });
    }
  }, [location.pathname, navigate]);

  // Check URL for modal opens
  useEffect(() => {
    const path = location.pathname;
    
    // /dashboard/pet_owners/new
    if (path.includes('/pet_owners/new')) {
      setIsCreateOwnerOpen(true);
      return;
    }
    
    // /dashboard/pet_owners/{uuid}/pets/{petUuid}
    const petOwnerPetMatch = path.match(/\/dashboard\/pet_owners\/([a-f0-9-]+)\/pets\/([a-f0-9-]+)/);
    if (petOwnerPetMatch) {
      const [, ownerUuid, petUuid] = petOwnerPetMatch;
      setSelectedOwnerId(ownerUuid);
      setIsOwnerModalOpen(true);
      setSelectedPetId(petUuid);
      setIsPetDetailModalOpen(true);
      return;
    }
    
    // /dashboard/pet_owners/{uuid}
    const petOwnerMatch = path.match(/\/dashboard\/pet_owners\/([a-f0-9-]+)/);
    if (petOwnerMatch) {
      const [, ownerUuid] = petOwnerMatch;
      setSelectedOwnerId(ownerUuid);
      setIsOwnerModalOpen(true);
      return;
    }
    
    // /dashboard/appointments/{uuid}
    const appointmentMatch = path.match(/\/dashboard\/appointments\/([a-f0-9-]+)/);
    if (appointmentMatch) {
      const [, appointmentUuid] = appointmentMatch;
      setSelectedAppointmentId(appointmentUuid);
      setIsAppointmentModalOpen(true);
      return;
    }
    
    // Close all modals if no match
    setIsCreateOwnerOpen(false);
    setIsOwnerModalOpen(false);
    setIsPetDetailModalOpen(false);
    setIsAppointmentModalOpen(false);
  }, [location.pathname]);

  // Fetch data on mount and when active section changes
  useEffect(() => {
    if (user?.practice_id) {
      fetchData();
    }
  }, [location.pathname, user?.practice_id]);

  const fetchData = async () => {
    if (!user?.practice_id) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const token = localStorage.getItem('access_token');
      const baseURL = API_BASE_URL;

      switch (activeSection) {
        case 'agents':
          // GET /api/v1/practices/{practice_id}/voice-agent
          const agentRes = await fetch(`${baseURL}/api/v1/practices/${user.practice_id}/voice-agent`, {
            headers: { 'Authorization': `Bearer ${token}` }
          });
          if (agentRes.ok) {
            const data = await agentRes.json();
            setVoiceAgent(data);
          }
          break;

        case 'appointments':
          // GET /api/v1/appointments/practice/{practice_id}
          const appointmentsRes = await fetch(`${baseURL}/api/v1/appointments/practice/${user.practice_id}`, {
            headers: { 'Authorization': `Bearer ${token}` }
          });
          if (appointmentsRes.ok) {
            const data = await appointmentsRes.json();
            setAppointments(data);
          }
          break;

        case 'calls':
          // GET /api/v1/call-analysis/practice/{practice_id}/calls
          const callsRes = await fetch(`${baseURL}/api/v1/call-analysis/practice/${user.practice_id}/calls?limit=20&offset=0`, {
            headers: { 'Authorization': `Bearer ${token}` }
          });
          if (callsRes.ok) {
            const data = await callsRes.json();
            setCalls(data.calls || []);
          }
          break;

        case 'schedule':
          // GET /api/v1/scheduling-unix/vet-availability/{vet_id}
          if (user.id) {
            const today = new Date().toISOString().split('T')[0];
            const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
            const scheduleRes = await fetch(`${baseURL}/api/v1/scheduling-unix/vet-availability/${user.id}?date=${today}&timezone=${timezone}`, {
              headers: { 'Authorization': `Bearer ${token}` }
            });
            if (scheduleRes.ok) {
              const data = await scheduleRes.json();
              setSchedule(data);
            }
          }
          break;

        case 'owners':
          // GET /api/v1/pet_owners/
          const ownersRes = await fetch(`${baseURL}/api/v1/pet_owners/`, {
            headers: { 'Authorization': `Bearer ${token}` }
          });
          if (ownersRes.ok) {
            const data = await ownersRes.json();
            setOwners(data);
          }
          break;

        case 'team':
          // GET /api/v1/practices/{practice_id}/members
          const teamRes = await fetch(`${baseURL}/api/v1/practices/${user.practice_id}/members`, {
            headers: { 'Authorization': `Bearer ${token}` }
          });
          if (teamRes.ok) {
            const data = await teamRes.json();
            setTeamMembers(data);
          }
          
          // GET /api/v1/practices/{practice_id}/invites
          const invitesRes = await fetch(`${baseURL}/api/v1/practices/${user.practice_id}/invites`, {
            headers: { 'Authorization': `Bearer ${token}` }
          });
          if (invitesRes.ok) {
            const invitesData = await invitesRes.json();
            const pendingOnly = invitesData.filter((inv: any) => inv.status === 'pending');
            setPendingInvites(pendingOnly);
          }
          break;
      }
    } catch (err) {
      console.error('Error fetching data:', err);
      setError('Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const getButtonAction = () => {
    switch(activeSection) {
      case 'agents': return null;
      case 'phones': return null;
      case 'appointments': return { label: 'New Appointment', action: () => setIsCreateAppointmentOpen(true) };
      case 'calls': return { label: 'View All', action: () => console.log('View all') };
      case 'schedule': return { label: 'Edit Schedule', action: () => console.log('Edit schedule') };
      case 'owners': return { label: 'Add Owner', action: () => navigate('/dashboard/pet_owners/new') };
      case 'team': return { label: 'Invite Member', action: () => setShowInviteModal(true) };
      default: return { label: 'Create', action: () => {} };
    }
  };

  // Handle nested routes (e.g., /dashboard/appointments/new - full page forms only)
  const isFullPageRoute = location.pathname.includes('/appointments/new');

  // If it's a full-page route, don't render the dashboard chrome
  if (isFullPageRoute) {
    return (
      <Routes>
        <Route path="appointments/new" element={<AppointmentForm />} />
      </Routes>
    );
  }

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const formatDate = (dateString: string) => {
    if (!dateString) return '-';
    try {
      return new Date(dateString).toLocaleString();
    } catch {
      return dateString;
    }
  };

  // Handle sending an invitation
  const handleSendInvite = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsInviting(true);
    setInviteError(null);
    setInviteSuccess(null);
    
    try {
      const token = localStorage.getItem('access_token');
      const baseURL = API_BASE_URL;
      
      const response = await fetch(`${baseURL}/api/v1/practices/${user?.practice_id}/invites`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email: inviteEmail })
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to send invitation');
      }
      
      setInviteSuccess('Invitation sent successfully!');
      setInviteEmail('');
      setTimeout(() => {
        setShowInviteModal(false);
        setInviteSuccess(null);
        fetchData(); // Refresh team data
      }, 2000);
    } catch (error: any) {
      setInviteError(error.message || 'Failed to send invitation');
    } finally {
      setIsInviting(false);
    }
  };

  // Handle revoking an invitation
  const handleRevokeInvite = async () => {
    if (!revokeInviteId) return;
    
    try {
      const token = localStorage.getItem('access_token');
      const baseURL = API_BASE_URL;
      
      const response = await fetch(`${baseURL}/api/v1/practices/${user?.practice_id}/invites/${revokeInviteId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        }
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to revoke invitation');
      }
      
      setPendingInvites(pendingInvites.filter(inv => inv.id !== revokeInviteId));
      setRevokeInviteId(null);
    } catch (error: any) {
      console.error('Error revoking invitation:', error);
      setError(error.message || 'Failed to revoke invitation');
      setRevokeInviteId(null);
    }
  };

  // Handle removing a team member
  const handleRemoveMember = async () => {
    if (!removeMemberId) return;
    
    try {
      const token = localStorage.getItem('access_token');
      const baseURL = API_BASE_URL;
      
      const response = await fetch(`${baseURL}/api/v1/practices/${user?.practice_id}/members/${removeMemberId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        }
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to remove team member');
      }
      
      setTeamMembers(teamMembers.filter(m => m.id !== removeMemberId));
      setRemoveMemberId(null);
    } catch (error: any) {
      console.error('Error removing team member:', error);
      setError(error.message || 'Failed to remove team member');
      setRemoveMemberId(null);
    }
  };

  const formatDuration = (start: string, end: string) => {
    if (!start || !end) return '-';
    try {
      const duration = Math.abs(new Date(end).getTime() - new Date(start).getTime()) / 1000;
      const minutes = Math.floor(duration / 60);
      const seconds = Math.floor(duration % 60);
      return `${minutes}:${seconds.toString().padStart(2, '0')}`;
    } catch {
      return '-';
    }
  };

  // No longer need to check for nested routes - we'll render them as overlays

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Left Sidebar */}
      <div className="w-60 bg-white border-r border-gray-200 flex flex-col">
        {/* Logo/Workspace */}
        <div className="p-4 border-b border-gray-200">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
              <span className="text-white font-semibold text-sm">HP</span>
            </div>
            <div className="flex-1 min-w-0">
              <div className="text-sm font-medium text-gray-900">HelpPetAI</div>
              <div className="text-xs text-gray-500">{user?.full_name || 'User'}</div>
            </div>
          </div>
          <button
            onClick={handleLogout}
            className="w-full flex items-center gap-2 px-3 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded-md transition-colors"
          >
            <LogOut className="w-4 h-4" />
            <span>Log out</span>
          </button>
        </div>

        {/* Navigation */}
        <div className="flex-1 overflow-y-auto py-4">
          {/* BUILD Section */}
          <div className="px-3 mb-4">
            <div className="text-xs font-semibold text-gray-500 uppercase mb-2 px-2">Build</div>
            {navigationItems.filter(item => item.section === 'BUILD').map((item) => (
              <button
                key={item.key}
                onClick={() => navigate(item.path)}
                className={`w-full flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-colors ${
                  activeSection === item.key
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-700 hover:bg-gray-100'
                }`}
              >
                {item.icon}
                <span>{item.label}</span>
              </button>
            ))}
          </div>

          {/* DEPLOY Section */}
          <div className="px-3 mb-4">
            <div className="text-xs font-semibold text-gray-500 uppercase mb-2 px-2">Deploy</div>
            {navigationItems.filter(item => item.section === 'DEPLOY').map((item) => (
              <button
                key={item.key}
                onClick={() => navigate(item.path)}
                className={`w-full flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-colors ${
                  activeSection === item.key
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-700 hover:bg-gray-100'
                }`}
              >
                {item.icon}
                <span>{item.label}</span>
              </button>
            ))}
          </div>

          {/* MONITOR Section */}
          <div className="px-3 mb-4">
            <div className="text-xs font-semibold text-gray-500 uppercase mb-2 px-2">Monitor</div>
            {navigationItems.filter(item => item.section === 'MONITOR').map((item) => (
              <button
                key={item.key}
                onClick={() => navigate(item.path)}
                className={`w-full flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-colors ${
                  activeSection === item.key
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-700 hover:bg-gray-100'
                }`}
              >
                {item.icon}
                <span>{item.label}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Bottom Section */}
        <div className="p-3 border-t border-gray-200 space-y-3">
          {/* Pay As You Go Box */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
            <div className="flex items-center space-x-2 mb-2">
              <CheckCircle className="w-4 h-4 text-blue-600" />
              <span className="text-xs font-medium text-blue-900">Pay As You Go</span>
            </div>
            <div className="space-y-1.5">
              <div className="flex justify-between items-center">
                <span className="text-xs text-gray-700">Credits:</span>
                <span className="text-xs font-medium text-gray-900">$10.00 💰</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-xs text-gray-700">Phone Numbers:</span>
                <span className="text-xs font-medium text-gray-900">0/1</span>
              </div>
            </div>
          </div>

          <button className="w-full flex items-center gap-3 px-3 py-2 rounded-md text-sm text-gray-700 hover:bg-gray-100 transition-colors">
            <Settings className="w-4 h-4" />
            <span>Settings</span>
          </button>
          <button className="w-full flex items-center gap-3 px-3 py-2 rounded-md text-sm text-gray-700 hover:bg-gray-100 transition-colors">
            <HelpCircle className="w-4 h-4" />
            <span>Help</span>
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Top Bar */}
        <div className="bg-white border-b border-gray-200 px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-semibold text-gray-900">
                {navigationItems.find(item => item.key === activeSection)?.label || 'Dashboard'}
              </h1>
            </div>
            <div className="flex items-center gap-3">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input
                  type="text"
                  placeholder="Search..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10 pr-4 py-2 text-sm bg-white border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900 placeholder-gray-400 w-64"
                />
              </div>
              {getButtonAction() && (
                <button
                  onClick={getButtonAction()!.action}
                  className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors"
                >
                  {getButtonAction()!.label}
                </button>
              )}
            </div>
          </div>
        </div>

        {/* Content Area */}
        <div className="flex-1 overflow-auto bg-white">
          {loading && (
            <div className="flex items-center justify-center h-64">
              <div className="text-gray-500">Loading...</div>
            </div>
          )}

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-4">
              <p className="text-red-800 text-sm">{error}</p>
            </div>
          )}

          {/* AI Agents Table */}
          {activeSection === 'agents' && (
            <VoiceAgentSection />
          )}

          {/* Phone Numbers Configuration */}
          {activeSection === 'phones' && (
            <PhoneConfigSection />
          )}

          {/* Appointments Calendar */}
          {activeSection === 'appointments' && !loading && (
            <AppointmentCalendar
              appointments={appointments}
              currentDate={calendarDate}
              onNavigate={setCalendarDate}
              currentView={calendarView}
              onViewChange={setCalendarView}
              onSelectAppointment={(appointmentId) => {
                setSelectedAppointmentId(appointmentId);
                setIsAppointmentModalOpen(true);
                navigate(`/dashboard/appointments/${appointmentId}`);
              }}
              onSelectSlot={(slotInfo) => {
                // Open create appointment modal with pre-filled date/time
                setIsCreateAppointmentOpen(true);
                navigate('/dashboard/appointments/new');
              }}
            />
          )}

          {/* Call History */}
          {activeSection === 'calls' && (
            <CallHistorySection />
          )}

          {/* Work Schedule Table */}
          {activeSection === 'schedule' && !loading && (
            <div className="bg-white border-t border-gray-200 overflow-hidden">
              {schedule.length > 0 ? (
                <table className="min-w-full">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Start Time</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">End Time</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                      <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider"></th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200">
                    {schedule.map((slot: any) => (
                      <tr key={slot.id} className="hover:bg-gray-50 cursor-pointer transition-colors">
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {new Date(slot.start_at).toLocaleDateString()}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                          {new Date(slot.start_at).toLocaleTimeString()}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                          {new Date(slot.end_at).toLocaleTimeString()}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">
                            Available
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : (
                <div className="p-8 text-center text-gray-500">
                  No schedule configured yet
                </div>
              )}
            </div>
          )}

          {/* Pet Owners Table */}
          {activeSection === 'owners' && !loading && (
            <div className="bg-white border-t border-gray-200 overflow-x-auto">
              {loading ? (
                <div className="p-8 text-center text-gray-500">Loading...</div>
              ) : owners.length > 0 ? (
                <table className="min-w-full">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Name</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Email</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Phone</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Pets</th>
                      <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider"></th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200">
                    {owners.map((owner: any) => (
                      <tr 
                        key={owner.uuid} 
                        onClick={() => {
                          navigate(`/dashboard/pet_owners/${owner.uuid}`);
                        }}
                        className="hover:bg-gray-50 cursor-pointer transition-colors relative"
                      >
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                          {owner.full_name}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                          {owner.email || '-'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                          {owner.phone || '-'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                          {owner.pets?.length || 0}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : (
                <div className="p-8 text-center text-gray-500">
                  No pet owners yet
                </div>
              )}
            </div>
          )}

          {/* Team Members Table */}
          {activeSection === 'team' && !loading && (
            <div className="bg-white border-t border-gray-200 overflow-hidden">
              {(teamMembers.length > 0 || pendingInvites.length > 0) ? (
                <table className="min-w-full">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Name/Email</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Role/Status</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Joined</th>
                      <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200">
                    {teamMembers.map((member: any) => (
                      <tr key={member.id} className="hover:bg-gray-50 transition-colors">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex items-center">
                            <div className="flex-shrink-0 h-8 w-8">
                              <div className="h-8 w-8 rounded-full bg-blue-100 flex items-center justify-center">
                                <span className="text-sm font-medium text-blue-600">
                                  {member.full_name?.charAt(0) || member.email.charAt(0).toUpperCase()}
                                </span>
                              </div>
                            </div>
                            <div className="ml-3">
                              <div className="text-sm font-medium text-gray-900">{member.full_name || member.email}</div>
                              <div className="text-sm text-gray-500">{member.email}</div>
                            </div>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">
                            {member.role}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                          {formatDate(member.created_at)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-right text-sm">
                          {member.role !== 'PRACTICE_ADMIN' && (
                            <button
                              onClick={() => setRemoveMemberId(member.id)}
                              className="text-red-600 hover:text-red-900"
                              title="Remove team member"
                            >
                              <Trash2 className="h-4 w-4" />
                            </button>
                          )}
                        </td>
                      </tr>
                    ))}
                    {pendingInvites.map((invite: any) => (
                      <tr key={invite.id} className="hover:bg-gray-50 transition-colors bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex items-center">
                            <div className="flex-shrink-0 h-8 w-8">
                              <div className="h-8 w-8 rounded-full bg-gray-200 flex items-center justify-center">
                                <Mail className="h-4 w-4 text-gray-400" />
                              </div>
                            </div>
                            <div className="ml-3">
                              <div className="text-sm font-medium text-gray-900 italic">{invite.email}</div>
                              <div className="text-xs text-gray-500">Expires: {new Date(invite.expires_at).toLocaleDateString()}</div>
                            </div>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-yellow-100 text-yellow-800 italic">
                            Pending Invite
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                          {formatDate(invite.created_at)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-right text-sm">
                          <button
                            onClick={() => setRevokeInviteId(invite.id)}
                            className="text-red-600 hover:text-red-900"
                            title="Revoke invitation"
                          >
                            <Trash2 className="h-4 w-4" />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : (
                <div className="p-8 text-center text-gray-500">
                  <Users className="mx-auto h-12 w-12 text-gray-400 mb-4" />
                  <p>No team members yet</p>
                  <p className="text-sm mt-2">Click "Invite Member" to add your first team member</p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

        {/* Pet Owner Detail Modal */}
        {selectedOwnerId && (
          <PetOwnerDetailModal
            isOpen={isOwnerModalOpen}
            onClose={() => {
              setIsOwnerModalOpen(false);
              setSelectedOwnerId(null);
              navigate('/dashboard/pet_owners');
            }}
            ownerId={selectedOwnerId}
          />
        )}

        {/* Create Pet Owner Sliding Panel */}
        <PetOwnerCreateModal
          isOpen={isCreateOwnerOpen}
          onClose={() => navigate('/dashboard/pet_owners')}
          onSuccess={() => {
            fetchData(); // Refresh the list
            navigate('/dashboard/pet_owners');
          }}
        />

        {/* Create Appointment Modal */}
        <AppointmentCreateModal
          isOpen={isCreateAppointmentOpen}
          onClose={() => setIsCreateAppointmentOpen(false)}
          onSuccess={() => {
            setIsCreateAppointmentOpen(false);
            fetchData(); // Refresh the appointments list
          }}
        />

        {/* Pet Detail Modal (for /dashboard/pet_owners/{uuid}/pets/{petUuid}) */}
        {selectedPetId && (
          <PetDetailModal
            isOpen={isPetDetailModalOpen}
            onClose={() => {
              setIsPetDetailModalOpen(false);
              setSelectedPetId(null);
              // Navigate back to pet owner modal
              if (selectedOwnerId) {
                navigate(`/dashboard/pet_owners/${selectedOwnerId}`);
              } else {
                navigate('/dashboard/pet_owners');
              }
            }}
            petId={selectedPetId}
            onEdit={(petId) => {
              console.log('Edit pet:', petId);
            }}
            onDelete={async (petId) => {
              console.log('Delete pet:', petId);
            }}
          />
        )}

        {/* Appointment Detail Modal (placeholder - needs implementation) */}
        {selectedAppointmentId && (
          <AppointmentDetailModal
            isOpen={isAppointmentModalOpen}
            onClose={() => {
              setIsAppointmentModalOpen(false);
              setSelectedAppointmentId(null);
              navigate('/dashboard/appointments');
            }}
            appointmentId={selectedAppointmentId}
            onEdit={(id) => {
              setIsAppointmentEditModalOpen(true);
            }}
          />
        )}

        <AppointmentEditModal
          isOpen={isAppointmentEditModalOpen}
          onClose={() => {
            setIsAppointmentEditModalOpen(false);
          }}
          appointmentId={selectedAppointmentId || ''}
          onSuccess={() => {
            fetchData();
            setIsAppointmentEditModalOpen(false);
          }}
        />

        {/* Invite Team Member Modal */}
        {showInviteModal && (
          <div className="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center p-4 z-50">
            <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-medium text-gray-900">Invite Team Member</h3>
                <button
                  onClick={() => {
                    setShowInviteModal(false);
                    setInviteEmail('');
                    setInviteError(null);
                    setInviteSuccess(null);
                  }}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>
              
              {inviteSuccess && (
                <div className="mb-4 bg-green-50 border border-green-200 rounded-md p-3">
                  <p className="text-sm text-green-800">{inviteSuccess}</p>
                </div>
              )}
              
              {inviteError && (
                <div className="mb-4 bg-red-50 border border-red-200 rounded-md p-3">
                  <p className="text-sm text-red-800">{inviteError}</p>
                </div>
              )}
              
              <form onSubmit={handleSendInvite}>
                <div className="mb-4">
                  <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-2">
                    Email Address
                  </label>
                  <input
                    type="email"
                    id="email"
                    value={inviteEmail}
                    onChange={(e) => setInviteEmail(e.target.value)}
                    className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    placeholder="colleague@example.com"
                    required
                    disabled={isInviting}
                  />
                </div>
                
                <div className="flex justify-end gap-3">
                  <button
                    type="button"
                    onClick={() => {
                      setShowInviteModal(false);
                      setInviteEmail('');
                      setInviteError(null);
                      setInviteSuccess(null);
                    }}
                    className="px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                    disabled={isInviting}
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
                    disabled={isInviting}
                  >
                    {isInviting ? (
                      <>
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                        Sending...
                      </>
                    ) : (
                      <>
                        <UserPlus className="mr-2 h-4 w-4" />
                        Send Invitation
                      </>
                    )}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Revoke Invite Confirmation */}
        <ConfirmDialog
          isOpen={revokeInviteId !== null}
          onClose={() => setRevokeInviteId(null)}
          onConfirm={handleRevokeInvite}
          title="Revoke Invitation"
          message="Are you sure you want to revoke this invitation? This action cannot be undone."
          confirmText="Revoke"
          isDangerous={true}
        />

        {/* Remove Team Member Confirmation */}
        <ConfirmDialog
          isOpen={removeMemberId !== null}
          onClose={() => setRemoveMemberId(null)}
          onConfirm={handleRemoveMember}
          title="Remove Team Member"
          message="Are you sure you want to remove this team member from your practice? They will lose access immediately."
          confirmText="Remove"
          isDangerous={true}
        />
      </div>
    );
  };
  
  export default Dashboard;
