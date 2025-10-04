import React, { useState } from 'react';
import { Edit2, X, Loader, AlertTriangle } from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import { API_BASE_URL } from '../../config/api';
import md5 from 'md5';

// Generate Gravatar URL from email
const getGravatarUrl = (email: string, size: number = 200): string => {
  const trimmedEmail = email.trim().toLowerCase();
  const hash = md5(trimmedEmail);
  return `https://www.gravatar.com/avatar/${hash}?d=identicon&s=${size}`;
};

const ProfileSettings: React.FC = () => {
  const { user, refreshUser } = useAuth();
  const [showEditPanel, setShowEditPanel] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [practiceName, setPracticeName] = useState<string | null>(null);
  const [formData, setFormData] = useState({
    email: user?.email || '',
    full_name: user?.full_name || '',
  });
  const [showRemovePracticeConfirm, setShowRemovePracticeConfirm] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!user?.id) return;

    setLoading(true);
    setError(null);

    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`${API_BASE_URL}/api/v1/auth/me`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: formData.email || null,
          full_name: formData.full_name,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to update profile');
      }

      await refreshUser?.();
      setShowEditPanel(false);
    } catch (err: any) {
      setError(err.message || 'Failed to update profile');
    } finally {
      setLoading(false);
    }
  };

  const handleRemovePractice = async () => {
    if (!user?.id) return;

    setLoading(true);
    setError(null);

    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`${API_BASE_URL}/api/v1/auth/me`, {
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
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to remove practice association');
      }

      await refreshUser?.();
      setShowRemovePracticeConfirm(false);
      setShowEditPanel(false);
    } catch (err: any) {
      setError(err.message || 'Failed to remove practice association');
    } finally {
      setLoading(false);
    }
  };

  const getRoleDisplay = (role: string) => {
    const roleMap: { [key: string]: string } = {
      'VET_STAFF': 'Vet Staff',
      'PRACTICE_ADMIN': 'Practice Admin',
      'SYSTEM_ADMIN': 'Admin',
      'PET_OWNER': 'Pet Owner',
      'PENDING_INVITE': 'Pending Invite',
    };
    return roleMap[role] || role;
  };

  // Fetch practice name when component mounts
  React.useEffect(() => {
    const fetchPracticeName = async () => {
      if (!user?.practice_id) {
        setPracticeName(null);
        return;
      }

      try {
        const token = localStorage.getItem('access_token');
        const response = await fetch(`${API_BASE_URL}/api/v1/practices/${user.practice_id}`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });

        if (response.ok) {
          const practice = await response.json();
          setPracticeName(practice.name || practice.practice_name || 'Unknown Practice');
        }
      } catch (err) {
        console.error('Error fetching practice name:', err);
        setPracticeName('Unknown Practice');
      }
    };

    fetchPracticeName();
  }, [user?.practice_id]);

  if (!user) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader className="w-8 h-8 text-blue-600 animate-spin" />
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-8 py-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold text-gray-900">Profile</h1>
            <p className="text-sm text-gray-600 mt-1">Manage your account information</p>
          </div>
          <button
            onClick={() => {
              setFormData({
                email: user.email || '',
                full_name: user.full_name || '',
              });
              setShowEditPanel(true);
            }}
            className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-md text-sm font-medium hover:bg-blue-700"
          >
            <Edit2 className="w-4 h-4 mr-2" />
            Edit Profile
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto bg-gray-50">
        <div className="max-w-4xl mx-auto px-8 py-6">
          <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
            {/* Profile Info Section */}
            <div className="px-6 py-4 border-b border-gray-200">
              <div className="flex items-center gap-4">
                <img 
                  src={getGravatarUrl(user.email || user.username, 96)}
                  alt={user.full_name}
                  className="w-16 h-16 rounded-full"
                />
                <div>
                  <h2 className="text-lg font-semibold text-gray-900">{user.full_name}</h2>
                  <p className="text-sm text-gray-600">{user.username}</p>
                </div>
              </div>
            </div>

            {/* Details Table */}
            <table className="min-w-full">
              <tbody className="divide-y divide-gray-200">
                <tr>
                  <td className="px-6 py-4 text-sm font-medium text-gray-500 bg-gray-50 w-1/3">
                    Username
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-900">
                    {user.username}
                  </td>
                </tr>
                <tr>
                  <td className="px-6 py-4 text-sm font-medium text-gray-500 bg-gray-50">
                    Full Name
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-900">
                    {user.full_name}
                  </td>
                </tr>
                <tr>
                  <td className="px-6 py-4 text-sm font-medium text-gray-500 bg-gray-50">
                    Role
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-900">
                    <span className="inline-flex items-center px-2 py-1 text-xs font-medium bg-blue-100 text-blue-800 rounded-full">
                      {getRoleDisplay(user.role)}
                    </span>
                  </td>
                </tr>
                <tr>
                  <td className="px-6 py-4 text-sm font-medium text-gray-500 bg-gray-50">
                    Practice
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-900">
                    {user.practice_id ? (
                      <span>{practiceName || 'Loading...'}</span>
                    ) : (
                      <span className="text-gray-400">Not associated</span>
                    )}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Edit Panel */}
      {showEditPanel && (
        <>
          <div 
            className="fixed inset-0 bg-black/20 z-40 transition-opacity"
            onClick={() => setShowEditPanel(false)}
          />
          
          <div className="fixed inset-y-0 right-0 w-96 bg-white shadow-xl z-50 flex flex-col">
            <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900">Edit profile</h3>
              <button
                onClick={() => setShowEditPanel(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <form onSubmit={handleSubmit} className="flex flex-col h-full">
              <div className="flex-1 overflow-y-auto px-6 py-6 space-y-4">
                {error && (
                  <div className="p-3 bg-red-50 border border-red-200 rounded-md">
                    <p className="text-sm text-red-800">{error}</p>
                  </div>
                )}

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Full Name
                  </label>
                  <input
                    type="text"
                    value={formData.full_name}
                    onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                    className="block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Email
                  </label>
                  <input
                    type="email"
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    className="block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="your@email.com"
                  />
                </div>

                <div className="pt-4 border-t border-gray-200">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Practice Association
                  </label>
                  {user.practice_id ? (
                    <div className="space-y-2">
                      <div className="text-sm text-gray-600">
                        Currently associated with practice
                      </div>
                      <button
                        type="button"
                        onClick={() => setShowRemovePracticeConfirm(true)}
                        className="text-sm text-red-600 hover:text-red-700 font-medium"
                      >
                        Remove practice association
                      </button>
                    </div>
                  ) : (
                    <p className="text-sm text-gray-500">Not associated with any practice</p>
                  )}
                </div>
              </div>

              <div className="border-t border-gray-200 px-6 py-4 flex gap-3">
                <button
                  type="button"
                  onClick={() => setShowEditPanel(false)}
                  disabled={loading}
                  className="flex-1 px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-md text-sm font-medium hover:bg-blue-700 disabled:opacity-50 flex items-center justify-center gap-2"
                >
                  {loading ? (
                    <>
                      <Loader className="h-4 w-4 animate-spin" />
                      Saving...
                    </>
                  ) : (
                    'Save changes'
                  )}
                </button>
              </div>
            </form>
          </div>
        </>
      )}

      {/* Remove Practice Confirmation Modal */}
      {showRemovePracticeConfirm && (
        <>
          <div 
            className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4"
            onClick={() => setShowRemovePracticeConfirm(false)}
          />
          
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 pointer-events-none">
            <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6 pointer-events-auto" onClick={(e) => e.stopPropagation()}>
              <div className="flex items-start gap-3 mb-4">
                <div className="bg-red-100 rounded-full p-2">
                  <AlertTriangle className="h-5 w-5 text-red-600" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">Remove Practice Association</h3>
                  <p className="text-sm text-gray-600 mt-1">
                    Are you sure you want to remove your practice association? You may lose access to practice data.
                  </p>
                </div>
              </div>

              <div className="flex gap-3 justify-end">
                <button
                  onClick={() => setShowRemovePracticeConfirm(false)}
                  disabled={loading}
                  className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50"
                >
                  Cancel
                </button>
                <button
                  onClick={handleRemovePractice}
                  disabled={loading}
                  className="px-4 py-2 bg-red-600 text-white rounded-md text-sm font-medium hover:bg-red-700 disabled:opacity-50 flex items-center gap-2"
                >
                  {loading ? (
                    <>
                      <Loader className="h-4 w-4 animate-spin" />
                      Removing...
                    </>
                  ) : (
                    'Remove Association'
                  )}
                </button>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default ProfileSettings;

