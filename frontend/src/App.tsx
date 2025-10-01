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
import VetSignup from './components/auth/VetSignup';
import ProtectedRoute from './components/auth/ProtectedRoute';
import PracticesList from './components/practices/PracticesList';
import PracticeDetail from './components/practices/PracticeDetail';
import PracticeForm from './components/practices/PracticeForm';
import PetOwnersList from './components/pet-owners/PetOwnersList';
import PetOwnerDetail from './components/pet-owners/PetOwnerDetail';
import PetOwnerForm from './components/pet-owners/PetOwnerForm';
import PetOwnerCreate from './components/pet-owners/PetOwnerCreate';
import PetDetail from './components/pets/PetDetail';
import PetForm from './components/pets/PetForm';
import MedicalRecordForm from './components/medical-records/MedicalRecordForm';
import MedicalRecordDetail from './components/medical-records/MedicalRecordDetail';
import MedicalRecordHistory from './components/medical-records/MedicalRecordHistory';
import VisitTranscriptDetail from './components/visit-transcripts/VisitTranscriptDetail';
import VisitTranscriptForm from './components/visit-transcripts/VisitTranscriptForm';
import VisitTranscriptRecorder from './components/visit-transcripts/VisitTranscriptRecorder';
import AppointmentPetRecorder from './components/visit-transcripts/AppointmentPetRecorder';
import AppointmentForm from './components/appointments/AppointmentForm';
import VetDashboardPage from './pages/VetDashboardPage';
import PrivacyPolicy from './pages/PrivacyPolicy';
import TermsOfService from './pages/TermsOfService';
import Comparison from './pages/Comparison';
import AcceptInvitation from './pages/AcceptInvitation';
import PracticeTeam from './pages/PracticeTeam';

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
            <Route path="/contact" element={<VetsContact />} />
            <Route path="/about" element={<AboutUs />} />
            <Route path="/comparison" element={<Comparison />} />
            <Route path="/privacy" element={<PrivacyPolicy />} />
            <Route path="/terms" element={<TermsOfService />} />
            
            {/* Invitation Routes */}
            <Route path="/accept-invite/:inviteId" element={<AcceptInvitation />} />
            
            {/* Auth Routes */}
            <Route path="/login" element={<Login />} />
            <Route path="/signup" element={<Signup />} />
            <Route path="/vet-signup" element={<VetSignup />} />
            
            {/* Dashboard Routes */}
            <Route path="/dashboard/vet" element={
              <ProtectedRoute>
                <VetDashboardPage />
              </ProtectedRoute>
            } />
            <Route path="/dashboard/vet/:date" element={
              <ProtectedRoute>
                <VetDashboardPage />
              </ProtectedRoute>
            } />
            
            {/* Appointment Routes */}
            <Route path="/appointments/new" element={
              <ProtectedRoute>
                <AppointmentForm />
              </ProtectedRoute>
            } />
            
            {/* Visit Transcript Routes */}
            <Route path="/visit-transcripts/record" element={
              <ProtectedRoute>
                <VisitTranscriptRecorder />
              </ProtectedRoute>
            } />
            <Route path="/visit-transcripts/record/:appointmentId" element={
              <ProtectedRoute>
                <AppointmentPetRecorder />
              </ProtectedRoute>
            } />
            
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
            
            {/* Practice Team Routes */}
            <Route path="/practice/team" element={
              <ProtectedRoute>
                <PracticeTeam />
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
            
            {/* Pet Routes */}
            <Route path="/pets/create" element={
              <ProtectedRoute>
                <PetForm mode="create" />
              </ProtectedRoute>
            } />
            <Route path="/pets/:uuid" element={
              <ProtectedRoute>
                <PetDetail />
              </ProtectedRoute>
            } />
            <Route path="/pets/:uuid/edit" element={
              <ProtectedRoute>
                <PetForm mode="edit" />
              </ProtectedRoute>
            } />
            
            {/* Medical Record Routes */}
            <Route path="/pets/:petId/medical-records/create" element={
              <ProtectedRoute>
                <MedicalRecordForm mode="create" />
              </ProtectedRoute>
            } />
            <Route path="/pets/:petId/medical-records/history" element={
              <ProtectedRoute>
                <MedicalRecordHistory />
              </ProtectedRoute>
            } />
            <Route path="/pets/:petId/medical-records/:recordId" element={
              <ProtectedRoute>
                <MedicalRecordDetail />
              </ProtectedRoute>
            } />
            <Route path="/pets/:petId/medical-records/:recordId/edit" element={
              <ProtectedRoute>
                <MedicalRecordForm mode="edit" />
              </ProtectedRoute>
            } />
            
            {/* Visit Transcript Routes */}
            <Route path="/pets/:petId/visit-transcripts/create" element={
              <ProtectedRoute>
                <VisitTranscriptForm mode="create" />
              </ProtectedRoute>
            } />
            <Route path="/pets/:petId/visit-transcripts/:transcriptId" element={
              <ProtectedRoute>
                <VisitTranscriptDetail />
              </ProtectedRoute>
            } />
            <Route path="/pets/:petId/visit-transcripts/:transcriptId/edit" element={
              <ProtectedRoute>
                <VisitTranscriptForm mode="edit" />
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