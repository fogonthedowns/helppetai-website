import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, useLocation, Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { API_BASE_URL, API_ENDPOINTS } from '../config/api';

interface InvitationDetails {
  id: string;
  practice_id: string;
  practice_name: string;
  email: string;
  status: string;
  created_at: string;
  expires_at: string;
}

const AcceptInvitation: React.FC = () => {
  const { inviteId } = useParams<{ inviteId: string }>();
  const location = useLocation();
  const navigate = useNavigate();
  const { isAuthenticated, user } = useAuth();
  
  const searchParams = new URLSearchParams(location.search);
  const code = searchParams.get('code');
  
  const [inviteDetails, setInviteDetails] = useState<InvitationDetails | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [acceptStatus, setAcceptStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle');
  
  // Fetch invitation details
  useEffect(() => {
    const fetchInviteDetails = async () => {
      if (!inviteId || !code) {
        setError('Invalid invitation link. Both invite ID and code are required.');
        setLoading(false);
        return;
      }
      
      try {
        const response = await fetch(`${API_BASE_URL}/api/v1/invites/${inviteId}?code=${code}`, {
          headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
          }
        });
        
        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.detail || 'Failed to load invitation details');
        }
        
        const data = await response.json();
        setInviteDetails(data);
        setLoading(false);
      } catch (error: any) {
        console.error('Error fetching invitation:', error);
        setError(error.message || 'Failed to load invitation details. The invitation may have expired or been revoked.');
        setLoading(false);
      }
    };
    
    fetchInviteDetails();
  }, [inviteId, code]);
  
  // Handle accepting invitation for authenticated users
  const handleAcceptInvitation = async () => {
    if (acceptStatus === 'loading' || !inviteId || !code) return;
    
    setAcceptStatus('loading');
    setError('');
    
    try {
      const token = localStorage.getItem('access_token');
      
      const response = await fetch(`${API_BASE_URL}/api/v1/invites/${inviteId}/accept`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ invite_code: code })
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to accept invitation');
      }
      
      const data = await response.json();
      setAcceptStatus('success');
      
      // Refresh user data to update the role in AuthContext
      try {
        const token = localStorage.getItem('access_token') || localStorage.getItem('token');
        const userResponse = await fetch(API_ENDPOINTS.AUTH.ME, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
        
        if (userResponse.ok) {
          // Force a page reload to refresh the auth context
          setTimeout(() => {
            window.location.href = '/dashboard';
          }, 1500);
          return;
        }
      } catch (refreshError) {
        console.error('Failed to refresh user data:', refreshError);
      }
      
      // Fallback: navigate normally
      setTimeout(() => {
        navigate('/dashboard');
      }, 1500);
    } catch (error: any) {
      console.error('Error accepting invitation:', error);
      setAcceptStatus('error');
      setError(error.message || 'Unexpected error occurred while accepting invitation');
    }
  };
  
  const renderContent = () => {
    if (loading) {
      return (
        <div className="flex flex-col items-center justify-center p-8">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
          <p className="mt-4 text-gray-600">Loading invitation details...</p>
        </div>
      );
    }
    
    if (error) {
      return (
        <div className="bg-white rounded-lg shadow-md p-8 max-w-md mx-auto">
          <div className="flex items-center justify-center text-red-600 mb-4">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-12 w-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <h2 className="text-xl font-bold text-center text-gray-800 mb-2">Invitation Error</h2>
          <p className="text-gray-600 text-center mb-6">{error}</p>
          <div className="flex justify-center">
            <Link
              to="/"
              className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition duration-200"
            >
              Go to Home
            </Link>
          </div>
        </div>
      );
    }
    
    if (!isAuthenticated) {
      return (
        <div className="bg-white rounded-lg shadow-md p-8 max-w-md mx-auto">
          <h1 className="text-2xl font-bold text-center text-gray-800 mb-4">Practice Invitation</h1>
          
          {inviteDetails ? (
            <div className="mb-6 p-4 bg-gray-50 rounded-md">
              <div className="mb-2">
                <span className="font-medium">Invited to:</span> {inviteDetails.practice_name || 'Unknown practice'}
              </div>
              <div>
                <span className="font-medium">Expires:</span>{' '}
                {new Date(inviteDetails.expires_at).toLocaleDateString()}
              </div>
            </div>
          ) : (
            <div className="mb-6 p-4 bg-gray-50 rounded-md text-center text-gray-500">
              Loading invitation details...
            </div>
          )}
          
          <div className="mb-6">
            <h2 className="text-lg font-semibold mb-3 text-center">Sign in to join this practice</h2>
            <p className="text-sm text-center text-gray-600 mb-4">
              You need to be signed in to accept this invitation. Please log in or create an account.
            </p>
          </div>
          
          <div className="flex flex-col gap-3">
            <Link
              to={`/login?redirect=/accept-invite/${inviteId}?code=${code}`}
              className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition duration-200 text-center"
            >
              Sign In
            </Link>
            <Link
              to={`/vet-signup?invite=${inviteId}&code=${code}`}
              className="px-6 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 transition duration-200 text-center"
            >
              Create Account
            </Link>
          </div>
        </div>
      );
    }
    
    if (inviteDetails) {
      return (
        <div className="bg-white rounded-lg shadow-md p-8 max-w-md mx-auto">
          <div className="flex items-center justify-center text-green-600 mb-4">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-12 w-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </div>
          
          <h1 className="text-2xl font-bold text-center text-gray-800 mb-4">Practice Invitation</h1>
          
          <div className="mb-6 p-4 bg-gray-50 rounded-md">
            <div className="mb-2">
              <span className="font-medium">Invited to:</span> {inviteDetails.practice_name || 'Unknown practice'}
            </div>
          </div>
          
          <div className="text-center mb-6">
            {acceptStatus === 'idle' ? (
              <p className="text-gray-600">
                You're signed in as <span className="font-medium">{user?.email}</span>. Click below to join this practice.
              </p>
            ) : acceptStatus === 'loading' ? (
              <p className="text-blue-600">Joining practice...</p>
            ) : acceptStatus === 'success' ? (
              <p className="text-green-600">Successfully joined the practice! Redirecting...</p>
            ) : (
              <p className="text-red-600">Failed to join practice. Please try again.</p>
            )}
          </div>
          
          <div className="flex justify-center">
            {acceptStatus === 'idle' && (
              <button
                onClick={handleAcceptInvitation}
                className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition duration-200"
              >
                Join Practice
              </button>
            )}
            
            {acceptStatus === 'loading' && (
              <div className="flex items-center px-6 py-2 bg-blue-100 text-blue-800 rounded-md">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-800 mr-2"></div>
                <span>Joining...</span>
              </div>
            )}
            
            {acceptStatus === 'success' && (
              <div className="px-6 py-2 bg-green-100 text-green-800 rounded-md">
                <span>Success! Redirecting...</span>
              </div>
            )}
            
            {acceptStatus === 'error' && (
              <button
                onClick={handleAcceptInvitation}
                className="px-6 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition duration-200"
              >
                Try Again
              </button>
            )}
          </div>
        </div>
      );
    }
    
    return null;
  };
  
  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8 flex flex-col justify-center">
      {renderContent()}
    </div>
  );
};

export default AcceptInvitation;
