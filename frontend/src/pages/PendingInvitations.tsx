import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { API_BASE_URL } from '../config/api';
import { Mail, Clock, CheckCircle, ArrowRight } from 'lucide-react';

interface Invitation {
  id: string;
  practice_id: string;
  practice_name: string;
  email: string;
  status: string;
  invite_code: string;
  created_at: string;
  expires_at: string;
  inviter_name: string;
}

const PendingInvitations: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [invitations, setInvitations] = useState<Invitation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchPendingInvitations();
  }, []);

  const fetchPendingInvitations = async () => {
    try {
      const token = localStorage.getItem('access_token') || localStorage.getItem('token');
      const response = await fetch(`${API_BASE_URL}/api/v1/invites/my-invitations`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        }
      });

      if (response.ok) {
        const data = await response.json();
        // Filter to only show pending invitations
        const pending = data.filter((inv: Invitation) => inv.status === 'pending');
        setInvitations(pending);
      } else {
        throw new Error('Failed to fetch invitations');
      }
    } catch (error) {
      console.error('Error fetching invitations:', error);
      setError('Failed to load your invitations. Please try again later.');
    } finally {
      setLoading(false);
    }
  };

  const handleAcceptInvitation = (invitation: Invitation) => {
    navigate(`/accept-invite/${invitation.id}?code=${invitation.invite_code}`);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  const isExpired = (expiresAt: string) => {
    return new Date(expiresAt) < new Date();
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="text-center mb-12">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-blue-100 rounded-full mb-4">
            <Mail className="h-8 w-8 text-blue-600" />
          </div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Your Practice Invitations</h1>
          <p className="text-gray-600">
            You have {invitations.length} pending invitation{invitations.length !== 1 ? 's' : ''} to join veterinary practices
          </p>
        </div>

        {error && (
          <div className="mb-6 bg-red-50 border border-red-200 rounded-lg p-4">
            <p className="text-red-800">{error}</p>
          </div>
        )}

        {invitations.length === 0 ? (
          <div className="bg-white rounded-lg shadow-sm p-12 text-center">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-gray-100 rounded-full mb-4">
              <Mail className="h-8 w-8 text-gray-400" />
            </div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">No Pending Invitations</h3>
            <p className="text-gray-600 mb-6">
              You don't have any pending practice invitations at the moment.
            </p>
            <button
              onClick={() => navigate('/dashboard/vet')}
              className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
            >
              Go to Dashboard
            </button>
          </div>
        ) : (
          <div className="space-y-4">
            {invitations.map((invitation) => (
              <div
                key={invitation.id}
                className="bg-white rounded-lg shadow-sm border border-gray-200 hover:border-blue-300 hover:shadow-md transition-all duration-200 cursor-pointer"
                onClick={() => handleAcceptInvitation(invitation)}
              >
                <div className="p-6">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center mb-2">
                        <h3 className="text-xl font-bold text-gray-900 mr-3">
                          {invitation.practice_name}
                        </h3>
                        {!isExpired(invitation.expires_at) ? (
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                            <CheckCircle className="h-3 w-3 mr-1" />
                            Active
                          </span>
                        ) : (
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                            Expired
                          </span>
                        )}
                      </div>
                      
                      <div className="space-y-2 text-sm text-gray-600">
                        <div className="flex items-center">
                          <Mail className="h-4 w-4 mr-2 text-gray-400" />
                          <span>Invited to: {invitation.email}</span>
                        </div>
                        <div className="flex items-center">
                          <Clock className="h-4 w-4 mr-2 text-gray-400" />
                          <span>Invited on {formatDate(invitation.created_at)}</span>
                        </div>
                        {invitation.inviter_name && (
                          <div className="flex items-center">
                            <span className="text-gray-500">by {invitation.inviter_name}</span>
                          </div>
                        )}
                        <div className="text-xs text-gray-500 mt-2">
                          Expires: {formatDate(invitation.expires_at)}
                        </div>
                      </div>
                    </div>

                    <div className="ml-6 flex items-center">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleAcceptInvitation(invitation);
                        }}
                        disabled={isExpired(invitation.expires_at)}
                        className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        Accept Invitation
                        <ArrowRight className="ml-2 h-4 w-4" />
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Help Text */}
        <div className="mt-8 bg-blue-50 border border-blue-200 rounded-lg p-4">
          <p className="text-sm text-blue-800">
            <strong>Need help?</strong> Click on any invitation to view details and accept it to join the practice.
            Once you accept, you'll have access to that practice's data and appointments.
          </p>
        </div>
      </div>
    </div>
  );
};

export default PendingInvitations;

