import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import UserProfileDropdown from './auth/UserProfileDropdown';
import ProfileEditModal from './auth/ProfileEditModal';

const Header = () => {
  const { isAuthenticated, username, user } = useAuth();
  const [isProfileModalOpen, setIsProfileModalOpen] = useState(false);
  const isAdmin = user?.role === 'ADMIN';
  const isVet = user?.role === 'VET' || user?.role === 'VET_STAFF';

  return (
    <>
      <header className="bg-white border-b border-gray-100">
        <div className="w-full px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <img 
                src="/helppetai.png" 
                alt="HelpPetAI Logo" 
                width="40" 
                height="40" 
                className="rounded-lg"
              />
              <Link to="/" className="text-2xl font-semibold text-gray-900 hover:text-gray-700 transition-colors" style={{
                fontFamily: 'Calibre, ui-sans-serif, system-ui, -apple-system, "system-ui", "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans", sans-serif',
                letterSpacing: '-0.02em',
                fontWeight: '600',
                fontSize: '24px',
                lineHeight: '1.2'
              }}>
                HelpPetAI
              </Link>
            </div>
            <div className="hidden md:flex items-center space-x-6">
              <Link to="/" className="text-gray-600 hover:text-gray-900 font-medium transition-colors">Home</Link>
              {!isAuthenticated && (
                <Link to="/vets" className="text-gray-600 hover:text-gray-900 font-medium transition-colors">Vets</Link>
              )}
              {!isAuthenticated && (
                <>
                  <Link to="/practices" className="text-gray-600 hover:text-gray-900 font-medium transition-colors">Practices</Link>
                  <Link to="/about" className="text-gray-600 hover:text-gray-900 font-medium transition-colors">About Us</Link>
                </>
              )}
              
              {isAuthenticated ? (
                <>
                  {isVet && (
                    <Link to="/dashboard/vet" className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 font-medium transition-colors">Dashboard</Link>
                  )}
                  {isAdmin && (
                    <Link to="/practices" className="text-gray-600 hover:text-gray-900 font-medium transition-colors">Practices</Link>
                  )}
                  <Link to="/pet_owners" className="text-gray-600 hover:text-gray-900 font-medium transition-colors">Pet Owners</Link>
                  <Link to="/rag/search" className="text-gray-600 hover:text-gray-900 font-medium transition-colors">Search</Link>
                  
                  {/* User Profile Dropdown */}
                  <UserProfileDropdown onEditProfile={() => setIsProfileModalOpen(true)} />
                </>
              ) : (
                <>
                  <Link to="/login" className="text-gray-600 hover:text-gray-900 font-medium transition-colors">Login</Link>
                </>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Profile Edit Modal */}
      <ProfileEditModal 
        isOpen={isProfileModalOpen} 
        onClose={() => setIsProfileModalOpen(false)} 
      />
    </>
  );
};

export default Header;