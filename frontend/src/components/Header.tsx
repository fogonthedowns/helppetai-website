import React from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

const Header = () => {
  const { isAuthenticated, username, logout, user } = useAuth();
  const isAdmin = user?.role === 'ADMIN';
  const isVet = user?.role === 'VET' || user?.role === 'VET_STAFF';

  return (
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
                <div className="flex items-center space-x-4">
                  <span className="text-sm text-gray-600">Welcome, {username}</span>
                  <button 
                    onClick={logout}
                    className="bg-red-500 text-white px-4 py-2 rounded-lg hover:bg-red-600 transition-colors font-medium text-sm"
                  >
                    Logout
                  </button>
                </div>
              </>
            ) : (
              <>
                <Link to="/login" className="text-gray-600 hover:text-gray-900 font-medium transition-colors">Login</Link>
                <Link to="/signup" className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors font-medium">
                  Sign up
                </Link>
              </>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;
