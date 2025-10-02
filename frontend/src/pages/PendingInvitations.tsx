import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { API_BASE_URL, API_ENDPOINTS } from '../config/api';
import { Mail, Clock, CheckCircle, ArrowRight, Building2, Search, AlertCircle, X } from 'lucide-react';

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

interface Practice {
  uuid: string;
  name: string;
  address_line1?: string;
  city?: string;
  state?: string;
  zip_code?: string;
}

const PendingInvitations: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [invitations, setInvitations] = useState<Invitation[]>([]);
  const [currentPractice, setCurrentPractice] = useState<Practice | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [removeLoading, setRemoveLoading] = useState(false);
  const [showRemoveModal, setShowRemoveModal] = useState(false);

  useEffect(() => {
    fetchData();
  }, [user?.practice_id]);

  const fetchData = async () => {
    try {
      const token = localStorage.getItem('access_token') || localStorage.getItem('token');
      
      // Fetch invitations
      const invitesResponse = await fetch(`${API_BASE_URL}/api/v1/invites/my-invitations`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        }
      });

      if (invitesResponse.ok) {
        const data = await invitesResponse.json();
        const pending = data.filter((inv: Invitation) => inv.status === 'pending');
        setInvitations(pending);
      }

      // Fetch current practice if user has one
      if (user?.practice_id) {
        const practiceResponse = await fetch(API_ENDPOINTS.PRACTICES.GET(user.practice_id), {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          }
        });

        if (practiceResponse.ok) {
          const practiceData = await practiceResponse.json();
          setCurrentPractice(practiceData);
        }
      }
    } catch (error) {
      console.error('Error fetching data:', error);
      setError('Failed to load your information. Please try again later.');
    } finally {
      setLoading(false);
    }
  };

  const handleRemovePractice = async () => {
    setRemoveLoading(true);
    setError(null);
    setShowRemoveModal(false);

    try {
      const token = localStorage.getItem('access_token') || localStorage.getItem('token');
      const response = await fetch(`${API_ENDPOINTS.AUTH.ME}`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          practice_id: null,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to remove practice association');
      }

      // Reload to refresh user context
      window.location.reload();
    } catch (err: any) {
      console.error('Remove practice error:', err);
      setError(err.message || 'An error occurred. Please try again.');
      setRemoveLoading(false);
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
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Your Practice Status</h1>
          <p className="text-gray-600">
            {currentPractice 
              ? "You've requested to join a practice"
              : invitations.length > 0 
                ? `You have ${invitations.length} pending invitation${invitations.length !== 1 ? 's' : ''} to join veterinary practices`
                : "You don't have any pending invitations at the moment"
            }
          </p>
        </div>

        {error && (
          <div className="mb-6 bg-red-50 border border-red-200 rounded-lg p-4">
            <p className="text-red-800">{error}</p>
          </div>
        )}

        {/* Current Practice Association */}
        {currentPractice && (
          <div className="mb-8">
            <div className="bg-white rounded-lg shadow-sm border-2 border-gray-200 overflow-hidden">
              <div className="p-6">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <div className="flex-shrink-0">
                        <div className="w-10 h-10 bg-yellow-50 rounded-full flex items-center justify-center">
                          <AlertCircle className="h-5 w-5 text-yellow-600" />
                        </div>
                      </div>
                      <div>
                        <h3 className="text-sm font-medium text-gray-900">Pending Practice Access</h3>
                        <p className="text-xs text-gray-500 mt-0.5">Awaiting administrator approval</p>
                      </div>
                    </div>
                    <div className="mt-4 ml-13">
                      <div className="flex items-center gap-2 mb-2">
                        <Building2 className="h-5 w-5 text-gray-400" />
                        <h4 className="text-lg font-semibold text-gray-900">{currentPractice.name}</h4>
                      </div>
                      {(currentPractice.city || currentPractice.state || currentPractice.address_line1) && (
                        <p className="text-sm text-gray-600 ml-7">
                          {currentPractice.address_line1 && <>{currentPractice.address_line1}<br /></>}
                          {currentPractice.city}{currentPractice.city && currentPractice.state ? ', ' : ''}{currentPractice.state} {currentPractice.zip_code}
                        </p>
                      )}
                    </div>
                  </div>
                  <button
                    onClick={() => setShowRemoveModal(true)}
                    disabled={removeLoading}
                    className="ml-6 p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition disabled:opacity-50"
                    title="Remove practice association"
                  >
                    <X className="h-5 w-5" />
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Invitations List */}
        {invitations.length > 0 && (
          <div className="mb-8">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Pending Invitations</h2>
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
          </div>
        )}

        {/* No Invitations and No Practice - Show Search Option */}
        {!currentPractice && invitations.length === 0 && (
          <>
            <div className="bg-white rounded-lg shadow-sm p-12 text-center mb-8">
              <div className="inline-flex items-center justify-center w-16 h-16 bg-gray-100 rounded-full mb-4">
                <Mail className="h-8 w-8 text-gray-400" />
              </div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">No Pending Invitations</h3>
              <p className="text-gray-600 mb-4">
                You don't have any pending practice invitations at the moment.
              </p>
              <p className="text-sm text-gray-500">
                Search for your practice below to request access.
              </p>
            </div>

            {/* Divider */}
            <div className="relative my-8">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-gray-300"></div>
              </div>
              <div className="relative flex justify-center text-sm">
                <span className="px-4 bg-gray-50 text-gray-500">Don't have an invitation?</span>
              </div>
            </div>
          </>
        )}

        {/* Search for Practice Option - Show if no current practice */}
        {!currentPractice && (
          <div className="bg-white rounded-lg shadow-sm border-2 border-gray-200 overflow-hidden mb-8">
            <div className="p-8 text-center">
              <div className="inline-flex items-center justify-center w-16 h-16 bg-blue-50 rounded-full mb-4">
                <Search className="h-8 w-8 text-blue-600" />
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-2">Search for Your Practice</h3>
              <p className="text-gray-600 mb-6 max-w-md mx-auto">
                Can't find an invitation? Search for your veterinary practice to join your team.
              </p>
              <button
                onClick={() => navigate('/signup/select-practice')}
                className="inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition"
              >
                <Search className="h-5 w-5 mr-2" />
                Find My Practice
              </button>
            </div>
          </div>
        )}

        {/* Help Text */}
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
          <p className="text-sm text-gray-700">
            <strong>Need help?</strong> {currentPractice 
              ? "A practice administrator needs to send you an invitation or approve your access request. Please contact a member of your practice team to complete your onboarding."
              : invitations.length > 0 
                ? "If you've been invited to a practice, accept the invitation above. If not, use the search tool to find and join your practice."
                : "Use the search tool above to find your veterinary practice and request access."
            }
          </p>
        </div>
      </div>
    </div>
  );
};

export default PendingInvitations;
