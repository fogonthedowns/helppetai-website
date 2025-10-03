import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Menu, X, Phone, FileText, Globe } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import UserProfileDropdown from './auth/UserProfileDropdown';
import ProfileEditModal from './auth/ProfileEditModal';

const Header = () => {
  const { isAuthenticated, username, user, logout } = useAuth();
  const [isProfileModalOpen, setIsProfileModalOpen] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [isProductsOpen, setIsProductsOpen] = useState(false);
  const isSystemAdmin = user?.role === 'SYSTEM_ADMIN';
  const isAdmin = user?.role === 'ADMIN';
  const isVetStaff = user?.role === 'VET_STAFF' || user?.role === 'PRACTICE_ADMIN' || user?.role === 'SYSTEM_ADMIN';
  const isPendingInvite = user?.role === 'PENDING_INVITE';

  return (
    <>
      <header className="bg-white border-b border-gray-100 sticky top-0 z-50">
        <div className="w-full px-6 py-4">
          <div className="flex items-center justify-between">
            {/* Logo and Brand with Navigation */}
            <div className="flex items-center space-x-8">
              <div className="flex items-center space-x-3">
                <img 
                  src="/logo_clear_back.png" 
                  alt="HelpPetAI Logo" 
                  width="36" 
                  height="36" 
                  className="object-contain"
                />
                <Link to={isVetStaff ? "/dashboard/vet" : "/"} className="text-xl font-medium text-gray-900 hover:text-gray-700 transition-colors" style={{
                  fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, "Apple Color Emoji", Arial, sans-serif, "Segoe UI Emoji", "Segoe UI Symbol"',
                  letterSpacing: '-0.01em',
                  fontWeight: '500'
                }}>
                  HelpPetAI
                </Link>
              </div>

              {/* Desktop Navigation - Left Side */}
              <div className="hidden md:flex items-center space-x-6">
              {!isAuthenticated && (
                <>
                  {/* Products Dropdown */}
                  <div 
                    className="relative"
                    onMouseEnter={() => setIsProductsOpen(true)}
                    onMouseLeave={() => setIsProductsOpen(false)}
                  >
                    <button className="text-gray-600 hover:text-gray-900 font-medium transition-colors py-2">
                      Products
                    </button>
                    
                    {/* Products Dropdown Menu */}
                    {isProductsOpen && (
                      <div className="absolute top-full left-0 pt-2 z-50">
                        {/* Upward pointing caret */}
                        <div className="absolute top-1 left-6 w-3 h-3 bg-white border-l border-t border-gray-100 transform rotate-45"></div>
                        <div className="w-[450px] bg-white rounded-lg shadow-xl border border-gray-100 py-4 px-2">
                        {/* AI Front Desk */}
                        <Link 
                          to="/products/ai-front-desk" 
                          className="flex items-start gap-4 px-4 py-3 rounded-lg hover:bg-gray-50 transition-colors group"
                          onClick={() => setIsProductsOpen(false)}
                        >
                          <div className="flex-shrink-0 mt-1">
                            <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center group-hover:bg-blue-200 transition-colors">
                              <Phone className="w-5 h-5 text-blue-600" />
                            </div>
                          </div>
                          <div className="flex-1">
                            <h3 className="font-semibold text-gray-900 mb-1">AI Front Desk</h3>
                            <p className="text-sm text-gray-600">AI-powered phone agent that handles appointment scheduling and answers questions automatically.</p>
                          </div>
                        </Link>

                        {/* Visit Transcriptions */}
                        <Link 
                          to="/products/visit-transcriptions" 
                          className="flex items-start gap-4 px-4 py-3 rounded-lg hover:bg-gray-50 transition-colors group"
                          onClick={() => setIsProductsOpen(false)}
                        >
                          <div className="flex-shrink-0 mt-1">
                            <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center group-hover:bg-green-200 transition-colors">
                              <FileText className="w-5 h-5 text-green-600" />
                            </div>
                          </div>
                          <div className="flex-1">
                            <h3 className="font-semibold text-gray-900 mb-1">Visit Transcriptions</h3>
                            <p className="text-sm text-gray-600">Record and transcribe veterinary visits with AI-powered SOAP notes and complete end-to-end context.</p>
                          </div>
                        </Link>

                        {/* Website Hosting */}
                        <Link 
                          to="/products/website-hosting" 
                          className="flex items-start gap-4 px-6 py-4 rounded-lg hover:bg-gray-50 transition-colors group"
                          onClick={() => setIsProductsOpen(false)}
                        >
                          <div className="flex-shrink-0 mt-1">
                            <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center group-hover:bg-green-200 transition-colors">
                              <Globe className="w-5 h-5 text-green-600" />
                            </div>
                          </div>
                          <div className="flex-1">
                            <h3 className="font-semibold text-gray-900 mb-2">Website Hosting</h3>
                            <p className="text-sm text-gray-600 leading-relaxed">Fast, secure hosting for your practice website with 99.9% uptime guarantee.</p>
                          </div>
                        </Link>
                        </div>
                      </div>
                    )}
                  </div>
                  
                  <Link to="/contact" className="text-gray-600 hover:text-gray-900 font-medium transition-colors">Contact</Link>
                  <Link to="/about" className="text-gray-600 hover:text-gray-900 font-medium transition-colors">About Us</Link>
                  <Link to="/pricing" className="text-gray-600 hover:text-gray-900 font-medium transition-colors">Pricing</Link>
                </>
              )}
              {isAuthenticated && (
                <>
                  {isPendingInvite ? (
                    <>
                      {/* For PENDING_INVITE users, show link to invitations page */}
                      <Link to="/pending-invitations" className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 font-medium transition-colors">My Invitations</Link>
                    </>
                  ) : (
                    <>
                      {/* For active staff/admin users, show normal navigation */}
                      {isVetStaff && (
                        <Link to="/dashboard/vet" className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 font-medium transition-colors">Dashboard</Link>
                      )}
                      {isSystemAdmin && (
                        <Link to="/practices" className="text-gray-600 hover:text-gray-900 font-medium transition-colors">Practices</Link>
                      )}
                      {isVetStaff && (
                        <Link to="/practice/team" className="text-gray-600 hover:text-gray-900 font-medium transition-colors">Team</Link>
                      )}
                      <Link to="/pet_owners" className="text-gray-600 hover:text-gray-900 font-medium transition-colors">Pet Owners</Link>
                    </>
                  )}
                </>
              )}
              </div>
            </div>

            {/* Right Side - Auth Buttons */}
            <div className="hidden md:flex items-center space-x-4">
              {isAuthenticated ? (
                <UserProfileDropdown onEditProfile={() => setIsProfileModalOpen(true)} />
              ) : (
                <>
                  <Link to="/login" className="text-gray-600 hover:text-gray-900 font-medium transition-colors">Log in</Link>
                  <Link to="/signup" className="bg-gray-900 text-white px-4 py-2 rounded font-medium hover:bg-gray-800 transition-colors">Sign up</Link>
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

                
                {!isAuthenticated && (
                  <>
                    <Link 
                      to="/" 
                      className="text-gray-600 hover:text-gray-900 font-medium transition-colors"
                      onClick={() => setIsMobileMenuOpen(false)}
                    >
                      Home
                    </Link>
                    <Link 
                      to="/contact" 
                      className="text-gray-600 hover:text-gray-900 font-medium transition-colors"
                      onClick={() => setIsMobileMenuOpen(false)}
                    >
                      Contact
                    </Link>
                    <Link 
                      to="/about" 
                      className="text-gray-600 hover:text-gray-900 font-medium transition-colors"
                      onClick={() => setIsMobileMenuOpen(false)}
                    >
                      About Us
                    </Link>
                    <Link 
                      to="/pricing" 
                      className="text-gray-600 hover:text-gray-900 font-medium transition-colors"
                      onClick={() => setIsMobileMenuOpen(false)}
                    >
                      Pricing
                    </Link>
                    <Link 
                      to="/login" 
                      className="text-gray-600 hover:text-gray-900 font-medium transition-colors"
                      onClick={() => setIsMobileMenuOpen(false)}
                    >
                      Log in
                    </Link>
                    <Link 
                      to="/signup" 
                      className="bg-gray-900 text-white px-4 py-2 rounded hover:bg-gray-800 font-medium transition-colors text-center"
                      onClick={() => setIsMobileMenuOpen(false)}
                    >
                      Sign up
                    </Link>
                  </>
                )}

                {isAuthenticated && (
                  <>
                    {isPendingInvite ? (
                      <>
                        {/* For PENDING_INVITE users, show link to invitations page */}
                        <Link 
                          to="/pending-invitations" 
                          className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 font-medium transition-colors text-center"
                          onClick={() => setIsMobileMenuOpen(false)}
                        >
                          My Invitations
                        </Link>
                      </>
                    ) : (
                      <>
                        {/* For active staff/admin users, show normal navigation */}
                        {isVetStaff && (
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
                        {isVetStaff && (
                          <Link 
                            to="/practice/team" 
                            className="text-gray-600 hover:text-gray-900 font-medium transition-colors"
                            onClick={() => setIsMobileMenuOpen(false)}
                          >
                            Team
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
                      </>
                    )}
                    
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