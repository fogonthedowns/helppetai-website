import React from 'react';
import { BrowserRouter as Router, Routes, Route, useLocation } from 'react-router-dom';
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
import GeneralSignup from './components/auth/GeneralSignup';
import ProtectedRoute from './components/auth/ProtectedRoute';
import RoleBasedRoute from './components/auth/RoleBasedRoute';
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
import Dashboard from './pages/Dashboard';
import PrivacyPolicy from './pages/PrivacyPolicy';
import TermsOfService from './pages/TermsOfService';
import Pricing from './pages/Pricing';
import AIFrontDesk from './pages/AIFrontDesk';
import VisitTranscriptions from './pages/VisitTranscriptions';
import WebsiteHosting from './pages/WebsiteHosting';
import AcceptInvitation from './pages/AcceptInvitation';
import PracticeTeam from './pages/PracticeTeam';
import PendingInvitations from './pages/PendingInvitations';
import PracticeSelection from './pages/PracticeSelection';
import CreatePractice from './pages/CreatePractice';

// Import auth utilities to set up fetch interceptor
import './utils/authUtils';

const ConditionalHeader = () => {
  const location = useLocation();
  // Don't show header on dashboard routes
  if (location.pathname.startsWith('/dashboard')) {
    return null;
  }
  return <Header />;
};

const App = () => {
  return (
    <AuthProvider>
      <Router>
        <div className="min-h-screen bg-white">
          <ConditionalHeader />
          <Routes>
            {/* Original Routes - RESTORED */}
            <Route path="/" element={<Home />} />
            <Route path="/contact" element={<VetsContact />} />
            <Route path="/about" element={<AboutUs />} />
            <Route path="/pricing" element={<Pricing />} />
            <Route path="/products/ai-front-desk" element={<AIFrontDesk />} />
            <Route path="/products/visit-transcriptions" element={<VisitTranscriptions />} />
            <Route path="/products/website-hosting" element={<WebsiteHosting />} />
            <Route path="/privacy" element={<PrivacyPolicy />} />
            <Route path="/terms" element={<TermsOfService />} />
            
            {/* Invitation Routes - Accessible to PENDING_INVITE */}
            <Route path="/accept-invite/:inviteId" element={<AcceptInvitation />} />
            <Route path="/pending-invitations" element={
              <RoleBasedRoute allowedRoles={['PENDING_INVITE', 'VET_STAFF', 'PRACTICE_ADMIN', 'SYSTEM_ADMIN']}>
                <PendingInvitations />
              </RoleBasedRoute>
            } />
            
            {/* Auth Routes */}
            <Route path="/login" element={<Login />} />
            <Route path="/signup" element={<GeneralSignup />} />
            <Route path="/signup/select-practice" element={
              <RoleBasedRoute allowedRoles={['PENDING_INVITE', 'VET_STAFF', 'PRACTICE_ADMIN', 'SYSTEM_ADMIN']}>
                <PracticeSelection />
              </RoleBasedRoute>
            } />
            <Route path="/signup/create-practice" element={
              <RoleBasedRoute allowedRoles={['PENDING_INVITE', 'VET_STAFF', 'PRACTICE_ADMIN', 'SYSTEM_ADMIN']}>
                <CreatePractice />
              </RoleBasedRoute>
            } />
            <Route path="/pet-owner-signup" element={<Signup />} />
            <Route path="/vet-signup" element={<VetSignup />} />
            
            {/* Dashboard Routes - NOT accessible to PENDING_INVITE */}
            <Route path="/dashboard/*" element={
              <RoleBasedRoute allowedRoles={['VET_STAFF', 'PRACTICE_ADMIN', 'SYSTEM_ADMIN']}>
                <Dashboard />
              </RoleBasedRoute>
            } />
            <Route path="/dashboard/vet" element={
              <RoleBasedRoute allowedRoles={['VET_STAFF', 'PRACTICE_ADMIN', 'SYSTEM_ADMIN']}>
                <VetDashboardPage />
              </RoleBasedRoute>
            } />
            <Route path="/dashboard/vet/:date" element={
              <RoleBasedRoute allowedRoles={['VET_STAFF', 'PRACTICE_ADMIN', 'SYSTEM_ADMIN']}>
                <VetDashboardPage />
              </RoleBasedRoute>
            } />
            
            {/* Appointment Routes - NOT accessible to PENDING_INVITE */}
            <Route path="/appointments/new" element={
              <RoleBasedRoute allowedRoles={['VET_STAFF', 'PRACTICE_ADMIN', 'SYSTEM_ADMIN']}>
                <AppointmentForm />
              </RoleBasedRoute>
            } />
            
            {/* Visit Transcript Routes - NOT accessible to PENDING_INVITE */}
            <Route path="/visit-transcripts/record" element={
              <RoleBasedRoute allowedRoles={['VET_STAFF', 'PRACTICE_ADMIN', 'SYSTEM_ADMIN']}>
                <VisitTranscriptRecorder />
              </RoleBasedRoute>
            } />
            <Route path="/visit-transcripts/record/:appointmentId" element={
              <RoleBasedRoute allowedRoles={['VET_STAFF', 'PRACTICE_ADMIN', 'SYSTEM_ADMIN']}>
                <AppointmentPetRecorder />
              </RoleBasedRoute>
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
            
            {/* Practice Team Routes - NOT accessible to PENDING_INVITE */}
            <Route path="/practice/team" element={
              <RoleBasedRoute allowedRoles={['VET_STAFF', 'PRACTICE_ADMIN', 'SYSTEM_ADMIN']}>
                <PracticeTeam />
              </RoleBasedRoute>
            } />
            
            {/* Pet Owner Routes - NOT accessible to PENDING_INVITE */}
            <Route path="/pet_owners" element={
              <RoleBasedRoute allowedRoles={['VET_STAFF', 'PRACTICE_ADMIN', 'SYSTEM_ADMIN']}>
                <PetOwnersList />
              </RoleBasedRoute>
            } />
            <Route path="/pet_owners/new" element={
              <RoleBasedRoute allowedRoles={['VET_STAFF', 'PRACTICE_ADMIN', 'SYSTEM_ADMIN']}>
                <PetOwnerCreate />
              </RoleBasedRoute>
            } />
            <Route path="/pet_owners/:uuid" element={
              <RoleBasedRoute allowedRoles={['VET_STAFF', 'PRACTICE_ADMIN', 'SYSTEM_ADMIN']}>
                <PetOwnerDetail />
              </RoleBasedRoute>
            } />
            <Route path="/pet_owners/:uuid/edit" element={
              <RoleBasedRoute allowedRoles={['VET_STAFF', 'PRACTICE_ADMIN', 'SYSTEM_ADMIN']}>
                <PetOwnerForm mode="edit" />
              </RoleBasedRoute>
            } />
            
            {/* Pet Routes - NOT accessible to PENDING_INVITE */}
            <Route path="/pets/create" element={
              <RoleBasedRoute allowedRoles={['VET_STAFF', 'PRACTICE_ADMIN', 'SYSTEM_ADMIN']}>
                <PetForm mode="create" />
              </RoleBasedRoute>
            } />
            <Route path="/pets/:uuid" element={
              <RoleBasedRoute allowedRoles={['VET_STAFF', 'PRACTICE_ADMIN', 'SYSTEM_ADMIN', 'PET_OWNER']}>
                <PetDetail />
              </RoleBasedRoute>
            } />
            <Route path="/pets/:uuid/edit" element={
              <RoleBasedRoute allowedRoles={['VET_STAFF', 'PRACTICE_ADMIN', 'SYSTEM_ADMIN', 'PET_OWNER']}>
                <PetForm mode="edit" />
              </RoleBasedRoute>
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
