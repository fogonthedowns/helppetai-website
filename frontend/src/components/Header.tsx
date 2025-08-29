import React from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

const Header = () => {
  const { isAuthenticated, username, logout } = useAuth();

  return (
    <header className="bg-white border-b border-gray-100">
      <div className="w-full px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <svg width="32" height="32" viewBox="0 0 32 32" className="text-blue-600">
              <defs>
                <linearGradient id="logo-gradient" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stopColor="#667eea" />
                  <stop offset="100%" stopColor="#764ba2" />
                </linearGradient>
              </defs>
              <rect width="32" height="32" rx="8" fill="url(#logo-gradient)" />
              <path d="M16 8c-4.4 0-8 3.6-8 8s3.6 8 8 8 8-3.6 8-8-3.6-8-8-8zm0 3c1.1 0 2 .9 2 2s-.9 2-2 2-2-.9-2-2 .9-2 2-2zm-3 8c0-1.7 1.3-3 3-3s3 1.3 3 3H13z" fill="white" opacity="0.9"/>
              <circle cx="16" cy="13" r="1.5" fill="white"/>
              <ellipse cx="16" cy="20" rx="2" ry="1" fill="white" opacity="0.7"/>
            </svg>
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
            <Link to="/vets" className="text-gray-600 hover:text-gray-900 font-medium transition-colors">Vets</Link>
            <Link to="/practices" className="text-gray-600 hover:text-gray-900 font-medium transition-colors">Practices</Link>
            <Link to="/about" className="text-gray-600 hover:text-gray-900 font-medium transition-colors">About Us</Link>
            
            {isAuthenticated ? (
              <>
                <Link to="/rag" className="text-gray-600 hover:text-gray-900 font-medium transition-colorss">AI Search</Link>
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
