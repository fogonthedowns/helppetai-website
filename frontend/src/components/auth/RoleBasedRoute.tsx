import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';

interface RoleBasedRouteProps {
  children: React.ReactNode;
  allowedRoles?: string[];
  redirectTo?: string;
}

/**
 * Route guard that checks if user has required role
 * PENDING_INVITE users are automatically redirected to /pending-invitations
 * unless the route explicitly allows PENDING_INVITE
 */
const RoleBasedRoute: React.FC<RoleBasedRouteProps> = ({ 
  children, 
  allowedRoles = [],
  redirectTo 
}) => {
  const { isAuthenticated, isLoading, user } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // If user is PENDING_INVITE and route doesn't explicitly allow it, redirect
  if (user?.role === 'PENDING_INVITE' && !allowedRoles.includes('PENDING_INVITE')) {
    return <Navigate to="/pending-invitations" replace />;
  }

  // If allowedRoles is specified and user doesn't have the role, redirect
  if (allowedRoles.length > 0 && user?.role && !allowedRoles.includes(user.role)) {
    return <Navigate to={redirectTo || '/pending-invitations'} replace />;
  }

  return <>{children}</>;
};

export default RoleBasedRoute;
