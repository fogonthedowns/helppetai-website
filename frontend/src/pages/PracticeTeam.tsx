import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { API_BASE_URL } from '../config/api';
import { UserPlus, Mail, Clock, CheckCircle, XCircle, Trash2, User, Shield } from 'lucide-react';

interface TeamMember {
  id: string;
  username: string;
  full_name: string;
  email: string;
  role: string;
  is_active: boolean;
  created_at: string;
}

interface PendingInvite {
  id: string;
  email: string;
  status: string;
  created_at: string;
  expires_at: string;
}

const PracticeTeam: React.FC = () => {
  const { user } = useAuth();
  const practiceId = user?.practice_id; // Ensure practiceId is defined here
  const [members, setMembers] = useState<TeamMember[]>([]);
  const [pendingInvites, setPendingInvites] = useState<PendingInvite[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Invite modal state
  const [showInviteModal, setShowInviteModal] = useState(false);
  const [inviteEmail, setInviteEmail] = useState('');
  const [isInviting, setIsInviting] = useState(false);
  const [inviteSuccess, setInviteSuccess] = useState<string | null>(null);
  const [inviteError, setInviteError] = useState<string | null>(null);
  
  // Revoke state
  const [revokeConfirm, setRevokeConfirm] = useState<string | null>(null);
  const [isRevoking, setIsRevoking] = useState(false);
  
  // Remove member state
  const [removeMemberConfirm, setRemoveMemberConfirm] = useState<string | null>(null);
  const [isRemovingMember, setIsRemovingMember] = useState(false);
  
  // Fetch team members and pending invites
  useEffect(() => {
    const fetchTeamData = async () => {
      if (!practiceId) {
        setError('No practice ID found');
        setIsLoading(false);
        return;
      }
      
      try {
        const token = localStorage.getItem('access_token');
        
        // Fetch team members
        const membersResponse = await fetch(
          `${API_BASE_URL}/api/v1/practices/${practiceId}/members`,
          {
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json',
            }
          }
        );
        
        if (membersResponse.ok) {
          const membersData = await membersResponse.json();
          setMembers(membersData);
        }
        
        // Fetch pending invites
        const invitesResponse = await fetch(
          `${API_BASE_URL}/api/v1/practices/${practiceId}/invites`,
          {
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json',
            }
          }
        );
        
        if (invitesResponse.ok) {
          const invitesData = await invitesResponse.json();
          // Filter to only show pending invites
          const pendingOnly = invitesData.filter((inv: PendingInvite) => inv.status === 'pending');
          setPendingInvites(pendingOnly);
        }
        
        setIsLoading(false);
      } catch (error: any) {
        console.error('Error fetching team data:', error);
        setError(error.message || 'Failed to load team data');
        setIsLoading(false);
      }
    };
    
    fetchTeamData();
  }, [practiceId]);
  
  // Handle sending an invitation
  const handleSendInvite = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inviteEmail.trim() || !practiceId) return;
    
    // Check if this email is already invited
    const emailLower = inviteEmail.trim().toLowerCase();
    const isAlreadyInvited = pendingInvites.some(
      i => i.email.toLowerCase() === emailLower && i.status === 'pending'
    );
    
    if (isAlreadyInvited) {
      setInviteError('This email has already been invited');
      return;
    }
    
    setIsInviting(true);
    setInviteSuccess(null);
    setInviteError(null);
    
    try {
      const token = localStorage.getItem('access_token');
      
      const response = await fetch(
        `${API_BASE_URL}/api/v1/practices/${practiceId}/invites`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ email: inviteEmail.trim() })
        }
      );
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to send invitation');
      }
      
      const data = await response.json();
      setInviteSuccess(`Invitation sent to ${inviteEmail} successfully`);
      setInviteEmail('');
      
      // Add the new invite to the list
      setPendingInvites([...pendingInvites, data]);
      
      setTimeout(() => {
        setShowInviteModal(false);
        setInviteSuccess(null);
      }, 2000);
    } catch (error: any) {
      console.error('Error sending invitation:', error);
      setInviteError(error.message || 'Failed to send invitation');
    } finally {
      setIsInviting(false);
    }
  };
  
  // Handle revoking an invitation
  const handleRevokeInvite = async (inviteId: string) => {
    if (!practiceId) {
      console.error('No practiceId found!');
      setError('No practice ID found');
      return;
    }
    
    console.log('Revoking invite:', inviteId, 'for practice:', practiceId);
    setIsRevoking(true);
    setError(null);
    
    try {
      const token = localStorage.getItem('access_token');
      const url = `${API_BASE_URL}/api/v1/practices/${practiceId}/invites/${inviteId}`;
      console.log('DELETE request to:', url);
      
      const response = await fetch(url, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        }
      });
      
      console.log('Response status:', response.status);
      
      if (!response.ok) {
        const errorData = await response.json();
        console.error('Error response:', errorData);
        throw new Error(errorData.detail || 'Failed to revoke invitation');
      }
      
      console.log('Invitation revoked successfully');
      // Remove the invitation from the list
      setPendingInvites(pendingInvites.filter(inv => inv.id !== inviteId));
      setRevokeConfirm(null);
      
      // Show success message briefly
      const successMsg = 'Invitation revoked successfully';
      setInviteSuccess(successMsg);
      setTimeout(() => setInviteSuccess(null), 3000);
    } catch (error: any) {
      console.error('Error revoking invitation:', error);
      setError(error.message || 'Failed to revoke invitation');
    } finally {
      setIsRevoking(false);
    }
  };
  
  // Handle removing a team member
  const handleRemoveMember = async (memberId: string) => {
    if (!practiceId) {
      console.error('No practiceId found!');
      setError('No practice ID found');
      return;
    }
    
    console.log('Removing member:', memberId, 'from practice:', practiceId);
    setIsRemovingMember(true);
    setError(null);
    
    try {
      const token = localStorage.getItem('access_token');
      const url = `${API_BASE_URL}/api/v1/practices/${practiceId}/members/${memberId}`;
      console.log('DELETE request to:', url);
      
      const response = await fetch(url, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        }
      });
      
      console.log('Response status:', response.status);
      
      if (!response.ok) {
        const errorData = await response.json();
        console.error('Error response:', errorData);
        throw new Error(errorData.detail || 'Failed to remove team member');
      }
      
      console.log('Team member removed successfully');
      // Remove the member from the list
      setMembers(members.filter(m => m.id !== memberId));
      setRemoveMemberConfirm(null);
      
      // Show success message briefly
      const successMsg = 'Team member removed successfully';
      setInviteSuccess(successMsg);
      setTimeout(() => setInviteSuccess(null), 3000);
    } catch (error: any) {
      console.error('Error removing team member:', error);
      setError(error.message || 'Failed to remove team member');
    } finally {
      setIsRemovingMember(false);
    }
  };
  
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };
  
  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    );
  }
  
  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Team Members</h1>
          <p className="mt-2 text-gray-600">Manage your practice team and send invitations</p>
        </div>
        
          {error && (
          <div className="mb-6 bg-red-50 border border-red-200 rounded-lg p-4">
            <p className="text-red-800">{error}</p>
          </div>
        )}
        
        {inviteSuccess && (
          <div className="mb-6 bg-green-50 border border-green-200 rounded-lg p-4">
            <p className="text-green-800">{inviteSuccess}</p>
          </div>
        )}
        
        {/* Invite Button */}
        <div className="mb-6">
          <button
            onClick={() => setShowInviteModal(true)}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            <UserPlus className="mr-2 h-5 w-5" />
            Invite Team Member
          </button>
        </div>
        
        {/* Active Team Members */}
        <div className="bg-white shadow rounded-lg overflow-hidden mb-6">
          <div className="px-6 py-4 border-b border-gray-200 flex justify-between">
            <h2 className="text-lg font-medium text-gray-900">Team Members</h2>
            <span className="text-sm font-medium text-gray-500">Role</span>
          </div>
          {members.length === 0 && pendingInvites.length === 0 ? (
            <div className="px-6 py-12 text-center">
              <User className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-2 text-sm font-medium text-gray-900">No team members</h3>
              <p className="mt-1 text-sm text-gray-500">Invite members to join your practice.</p>
            </div>
          ) : (
            <div className="divide-y divide-gray-200">
              {[...members, ...pendingInvites].map((member) => (
                <div key={member.id} className="px-4 py-2 hover:bg-gray-50 flex items-center justify-between">
                  <div className="flex items-center">
                    <img src={`https://www.gravatar.com/avatar/${member.email}?s=40&d=identicon`} alt="avatar" className="h-8 w-8 rounded-full" />
                    <div className="ml-3">
                      <div className={`text-sm font-medium text-gray-900 ${!('role' in member) ? 'italic' : ''}`}>
                        {'full_name' in member ? member.full_name : member.email}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center">
                    <div className="text-sm text-gray-500 mr-3">
                      {'role' in member ? member.role : 'Pending Invite'}
                    </div>
                    {('role' in member && member.role !== 'PRACTICE_ADMIN') || !('role' in member) ? (
                      <button 
                        className="text-red-600 hover:text-red-900" 
                        onClick={() => {
                          if ('role' in member) {
                            // Remove team member
                            setRemoveMemberConfirm(member.id);
                          } else {
                            // Revoke invite
                            setRevokeConfirm(member.id);
                          }
                        }}
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    ) : null}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
        
      </div>
      
      {/* Invite Modal */}
      {showInviteModal && (
        <div className="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Invite Team Member</h3>
            
            {inviteSuccess && (
              <div className="mb-4 bg-green-50 border border-green-200 rounded-md p-3">
                <p className="text-sm text-green-800">{inviteSuccess}</p>
              </div>
            )}
            
            {inviteError && (
              <div className="mb-4 bg-red-50 border border-red-200 rounded-md p-3">
                <p className="text-sm text-red-800">{inviteError}</p>
              </div>
            )}
            
            <form onSubmit={handleSendInvite}>
              <div className="mb-4">
                <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-2">
                  Email Address
                </label>
                <input
                  type="email"
                  id="email"
                  value={inviteEmail}
                  onChange={(e) => setInviteEmail(e.target.value)}
                  className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  placeholder="colleague@example.com"
                  required
                  disabled={isInviting}
                />
              </div>
              
              <div className="flex justify-end gap-3">
                <button
                  type="button"
                  onClick={() => {
                    setShowInviteModal(false);
                    setInviteEmail('');
                    setInviteError(null);
                  }}
                  className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                  disabled={isInviting}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
                  disabled={isInviting}
                >
                  {isInviting ? 'Sending...' : 'Send Invitation'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
      
      {/* Revoke Confirmation Modal */}
      {revokeConfirm && (
        <div className="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6">
            <div className="flex items-center mb-4">
              <div className="flex-shrink-0 w-10 h-10 rounded-full bg-red-100 flex items-center justify-center">
                <Trash2 className="h-5 w-5 text-red-600" />
              </div>
              <h3 className="ml-3 text-lg font-medium text-gray-900">Revoke Invitation</h3>
            </div>
            
            <p className="text-sm text-gray-600 mb-6">
              Are you sure you want to revoke this invitation? The recipient will no longer be able to accept it.
            </p>
            
            <div className="flex justify-end gap-3">
              <button
                type="button"
                onClick={() => setRevokeConfirm(null)}
                className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                disabled={isRevoking}
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={() => handleRevokeInvite(revokeConfirm)}
                className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 disabled:opacity-50 disabled:cursor-not-allowed"
                disabled={isRevoking}
              >
                {isRevoking ? 'Revoking...' : 'Revoke Invitation'}
              </button>
            </div>
          </div>
        </div>
      )}
      
      {/* Remove Member Confirmation Modal */}
      {removeMemberConfirm && (
        <div className="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6">
            <div className="flex items-center mb-4">
              <div className="flex-shrink-0 w-10 h-10 rounded-full bg-red-100 flex items-center justify-center">
                <Trash2 className="h-5 w-5 text-red-600" />
              </div>
              <h3 className="ml-3 text-lg font-medium text-gray-900">Remove Team Member</h3>
            </div>
            
            <p className="text-sm text-gray-600 mb-6">
              Are you sure you want to remove this team member from the practice? They will lose access to all practice data.
            </p>
            
            <div className="flex justify-end gap-3">
              <button
                type="button"
                onClick={() => setRemoveMemberConfirm(null)}
                className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                disabled={isRemovingMember}
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={() => handleRemoveMember(removeMemberConfirm)}
                className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 disabled:opacity-50 disabled:cursor-not-allowed"
                disabled={isRemovingMember}
              >
                {isRemovingMember ? 'Removing...' : 'Remove Member'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default PracticeTeam;
