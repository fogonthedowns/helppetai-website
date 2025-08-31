import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import VetDashboard from '../components/dashboard/VetDashboard';

/**
 * Vet Dashboard Page - Auto-routes to logged-in vet's UUID
 * Route: /dashboard/vet (auto-routes to logged-in vet's UUID)
 */
const VetDashboardPage: React.FC = () => {
  const { user, isAuthenticated, isLoading } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (!isLoading) {
      if (!isAuthenticated) {
        navigate('/login');
        return;
      }

      if (user && (user.role !== 'VET' && user.role !== 'VET_STAFF')) {
        navigate('/');
        return;
      }
    }
  }, [user, isAuthenticated, isLoading, navigate]);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return <VetDashboard />;
};

export default VetDashboardPage;
