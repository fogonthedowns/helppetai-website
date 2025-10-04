import React from 'react';
import { Link, Routes, Route, useNavigate, useLocation } from 'react-router-dom';
import { ArrowLeft, CreditCard, User } from 'lucide-react';
import BillingSettings from '../components/settings/BillingSettings';
import ProfileSettings from '../components/settings/ProfileSettings';
import { useAuth } from '../contexts/AuthContext';

const Settings: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { user } = useAuth();

  const settingsSections = [
    { key: 'billing', label: 'Billing', icon: <CreditCard className="w-4 h-4" />, path: '/settings/billing' },
    { key: 'profile', label: 'Profile', icon: <User className="w-4 h-4" />, path: '/settings/profile' },
  ];

  const handleBack = () => {
    navigate('/dashboard/appointments');
  };

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Settings Sidebar */}
      <div className="w-64 bg-white border-r border-gray-200 flex flex-col">
        {/* Logo/Brand Section */}
        <div className="p-4 border-b border-gray-200">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-10 h-10 rounded-full overflow-hidden flex items-center justify-center bg-white border border-gray-200">
              <img 
                src="/logo_clear_back.png" 
                alt="HelpPetAI" 
                className="w-full h-full object-contain p-1"
              />
            </div>
            <div className="flex-1 min-w-0">
              <div className="text-sm font-medium text-gray-900">HelpPetAI</div>
              <div className="text-xs text-gray-500">{user?.full_name || 'Settings'}</div>
            </div>
          </div>
          <button
            onClick={handleBack}
            className="w-full flex items-center gap-2 px-3 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded-md transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Back to app</span>
          </button>
        </div>

        {/* Settings Navigation */}
        <nav className="flex-1 px-3 py-4">
          <div className="space-y-1">
            {settingsSections.map((section) => {
              const isActive = location.pathname === section.path;
              return (
                <Link
                  key={section.key}
                  to={section.path}
                  className={`flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-colors ${
                    isActive
                      ? 'bg-gray-100 text-gray-900 font-medium'
                      : 'text-gray-700 hover:bg-gray-50'
                  }`}
                >
                  {section.icon}
                  <span>{section.label}</span>
                </Link>
              );
            })}
          </div>
        </nav>
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-auto">
        <Routes>
          <Route path="billing" element={<BillingSettings />} />
          <Route path="profile" element={<ProfileSettings />} />
          <Route index element={<div className="p-8"><h2 className="text-2xl font-semibold">Settings</h2><p className="text-gray-600 mt-2">Select a section from the sidebar</p></div>} />
        </Routes>
      </div>
    </div>
  );
};

export default Settings;

