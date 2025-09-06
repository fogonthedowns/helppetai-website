import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Menu, X } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import UserProfileDropdown from './auth/UserProfileDropdown';
import ProfileEditModal from './auth/ProfileEditModal';

const Header = () => {
  const { isAuthenticated, username, user, logout } = useAuth();
  const [isProfileModalOpen, setIsProfileModalOpen] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const isAdmin = user?.role === 'ADMIN';
  const isVet = user?.role === 'VET' || user?.role === 'VET_STAFF';

  return (
    <>
      <header className="bg-white border-b border-gray-100">
        <div className="w-full px-6 py-4">
          <div className="flex items-center justify-between">
            {/* Logo and Brand */}
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
            {/* Desktop Navigation */}
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

            {/* Mobile Menu Button */}
            <div className="md:hidden">
              <button
                onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
                className="p-2 rounded-md text-gray-600 hover:text-gray-900 hover:bg-gray-100 transition-colors"
                aria-label="Toggle mobile menu"
              >
                {isMobileMenuOpen ? (
                  <X className="h-6 w-6" />
                ) : (
                  <Menu className="h-6 w-6" />
                )}
              </button>
            </div>
          </div>

          {/* Mobile Navigation Menu */}
          {isMobileMenuOpen && (
            <div className="md:hidden mt-4 pb-4 border-t border-gray-100 pt-4">
              <div className="flex flex-col space-y-4">
                <Link 
                  to="/" 
                  className="text-gray-600 hover:text-gray-900 font-medium transition-colors"
                  onClick={() => setIsMobileMenuOpen(false)}
                >
                  Home
                </Link>
                
                {!isAuthenticated && (
                  <>
                    <Link 
                      to="/vets" 
                      className="text-gray-600 hover:text-gray-900 font-medium transition-colors"
                      onClick={() => setIsMobileMenuOpen(false)}
                    >
                      Vets
                    </Link>
                    <Link 
                      to="/practices" 
                      className="text-gray-600 hover:text-gray-900 font-medium transition-colors"
                      onClick={() => setIsMobileMenuOpen(false)}
                    >
                      Practices
                    </Link>
                    <Link 
                      to="/about" 
                      className="text-gray-600 hover:text-gray-900 font-medium transition-colors"
                      onClick={() => setIsMobileMenuOpen(false)}
                    >
                      About Us
                    </Link>
                    <Link 
                      to="/login" 
                      className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 font-medium transition-colors text-center"
                      onClick={() => setIsMobileMenuOpen(false)}
                    >
                      Login
                    </Link>
                  </>
                )}

                {isAuthenticated && (
                  <>
                    {isVet && (
                      <Link 
                        to="/dashboard/vet" 
                        className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 font-medium transition-colors text-center"
                        onClick={() => setIsMobileMenuOpen(false)}
                      >
                        Dashboard
                      </Link>
                    )}
                    {isAdmin && (
                      <Link 
                        to="/practices" 
                        className="text-gray-600 hover:text-gray-900 font-medium transition-colors"
                        onClick={() => setIsMobileMenuOpen(false)}
                      >
                        Practices
                      </Link>
                    )}
                    <Link 
                      to="/pet_owners" 
                      className="text-gray-600 hover:text-gray-900 font-medium transition-colors"
                      onClick={() => setIsMobileMenuOpen(false)}
                    >
                      Pet Owners
                    </Link>
                    <Link 
                      to="/rag/search" 
                      className="text-gray-600 hover:text-gray-900 font-medium transition-colors"
                      onClick={() => setIsMobileMenuOpen(false)}
                    >
                      Search
                    </Link>
                    
                    {/* Mobile User Profile Section */}
                    <div className="pt-4 border-t border-gray-100">
                      <div className="flex items-center space-x-3 mb-3">
                        <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center">
                          <span className="text-white text-sm font-medium">
                            {username?.charAt(0).toUpperCase()}
                          </span>
                        </div>
                        <span className="text-gray-900 font-medium">{username}</span>
                      </div>
                      <button
                        onClick={() => {
                          setIsProfileModalOpen(true);
                          setIsMobileMenuOpen(false);
                        }}
                        className="w-full text-left text-gray-600 hover:text-gray-900 font-medium transition-colors mb-2"
                      >
                        Edit Profile
                      </button>
                      <button
                        onClick={() => {
                          logout();
                          setIsMobileMenuOpen(false);
                        }}
                        className="w-full text-left text-red-600 hover:text-red-700 font-medium transition-colors"
                      >
                        Logout
                      </button>
                    </div>
                  </>
                )}
              </div>
            </div>
          )}
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