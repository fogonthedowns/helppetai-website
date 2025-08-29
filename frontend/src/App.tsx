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
import PracticesList from './components/practices/PracticesList';
import PracticeDetail from './components/practices/PracticeDetail';
import PracticeForm from './components/practices/PracticeForm';
import PetOwnersList from './components/pet-owners/PetOwnersList';
import PetOwnerDetail from './components/pet-owners/PetOwnerDetail';
import PetOwnerForm from './components/pet-owners/PetOwnerForm';
import PetOwnerCreate from './components/pet-owners/PetOwnerCreate';

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
            
            {/* Practice Routes - Public */}
            <Route path="/practices" element={<PracticesList />} />
            <Route path="/practices/:id" element={<PracticeDetail />} />
            
            {/* Practice Routes - Admin Only */}
            <Route path="/practices/new" element={
              <ProtectedRoute>
                <PracticeForm mode="create" />
              </ProtectedRoute>
            } />
            <Route path="/practices/:id/edit" element={
              <ProtectedRoute>
                <PracticeForm mode="edit" />
              </ProtectedRoute>
            } />
            
            {/* Pet Owner Routes */}
            <Route path="/pet_owners" element={
              <ProtectedRoute>
                <PetOwnersList />
              </ProtectedRoute>
            } />
            <Route path="/pet_owners/new" element={
              <ProtectedRoute>
                <PetOwnerCreate />
              </ProtectedRoute>
            } />
            <Route path="/pet_owners/:uuid" element={
              <ProtectedRoute>
                <PetOwnerDetail />
              </ProtectedRoute>
            } />
            <Route path="/pet_owners/:uuid/edit" element={
              <ProtectedRoute>
                <PetOwnerForm mode="edit" />
              </ProtectedRoute>
            } />
            
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