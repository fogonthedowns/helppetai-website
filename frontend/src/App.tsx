import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import { SearchPage } from './pages/SearchPage';
import { SearchResult } from './pages/SearchResult';
import Header from './components/Header';
import Home from './components/Home';
import VetsContact from './components/VetsContact';
import AboutUs from './components/AboutUs';
import Login from './components/auth/Login';
import Signup from './components/auth/Signup';
import ProtectedRoute from './components/auth/ProtectedRoute';

// Import auth utilities to set up fetch interceptor
import './utils/authUtils';

const App = () => {
  return (
    <AuthProvider>
      <Router>
        <div className="min-h-screen bg-white">
          <Header />
          <Routes>
            {/* Original Routes - RESTORED */}
            <Route path="/" element={<Home />} />
            <Route path="/vets" element={<VetsContact />} />
            <Route path="/about" element={<AboutUs />} />
            
            {/* Auth Routes */}
            <Route path="/login" element={<Login />} />
            <Route path="/signup" element={<Signup />} />
            
            {/* Protected RAG Search Routes */}
            <Route path="/rag" element={
              <ProtectedRoute>
                <SearchPage />
              </ProtectedRoute>
            } />
            <Route path="/rag/search" element={
              <ProtectedRoute>
                <SearchPage />
              </ProtectedRoute>
            } />
            <Route path="/rag/search/:searchId" element={
              <ProtectedRoute>
                <SearchResult />
              </ProtectedRoute>
            } />
          </Routes>
        </div>
      </Router>
    </AuthProvider>
  );
};

export default App;