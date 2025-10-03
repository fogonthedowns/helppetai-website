import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Search, Building2, MapPin } from 'lucide-react';
import { API_ENDPOINTS } from '../config/api';
import { useAuth } from '../contexts/AuthContext';

interface Practice {
  uuid: string;
  name: string;
  address_line1?: string;
  city?: string;
  state?: string;
  zip_code?: string;
}

const PracticeSelection: React.FC = () => {
  const navigate = useNavigate();
  const { isAuthenticated, user } = useAuth();
  const [searchTerm, setSearchTerm] = useState('');
  const [practices, setPractices] = useState<Practice[]>([]);
  const [filteredPractices, setFilteredPractices] = useState<Practice[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [signupLoading, setSignupLoading] = useState(false);

  // Get signup data from localStorage (for new signups)
  const signupDataStr = localStorage.getItem('signup_data');
  const isNewSignup = !!signupDataStr;

  useEffect(() => {
    fetchPractices();
  }, []);

  useEffect(() => {
    // Only filter when user has typed at least 2 characters
    if (searchTerm.trim().length >= 2) {
      const filtered = practices.filter(practice => {
        const searchLower = searchTerm.toLowerCase();
        return (
          practice.name.toLowerCase().includes(searchLower) ||
          (practice.city && practice.city.toLowerCase().includes(searchLower)) ||
          (practice.state && practice.state.toLowerCase().includes(searchLower)) ||
          (practice.zip_code && practice.zip_code.includes(searchTerm))
        );
      });
      // Limit to 50 results for performance
      setFilteredPractices(filtered.slice(0, 50));
    } else {
      setFilteredPractices([]);
    }
  }, [searchTerm, practices]);

  const fetchPractices = async () => {
    setLoading(true);
    try {
      const response = await fetch(API_ENDPOINTS.PRACTICES.LIST);
      if (response.ok) {
        const data = await response.json();
        setPractices(data);
      }
    } catch (error) {
      console.error('Failed to fetch practices:', error);
      setError('Failed to load practices. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleSelectPracticeForNewSignup = async (practice: Practice) => {
    setSignupLoading(true);
    setError('');

    try {
      if (!signupDataStr) {
        throw new Error('Signup data not found. Please start over.');
      }

      const signupData = JSON.parse(signupDataStr);

      // Create user with selected practice
      const response = await fetch(API_ENDPOINTS.AUTH.SIGNUP, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          username: signupData.email,
          email: signupData.email,
          password: signupData.password,
          full_name: signupData.full_name,
          practice_id: practice.uuid,
          role: 'VET_STAFF' // Backend will override based on practice membership
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Signup failed');
      }

      // Clean up signup data
      localStorage.removeItem('signup_data');

      // Auto-login
      try {
        const loginResponse = await fetch(API_ENDPOINTS.AUTH.LOGIN, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
          },
          body: new URLSearchParams({
            username: signupData.email,
            password: signupData.password,
          }),
        });

        if (loginResponse.ok) {
          const loginData = await loginResponse.json();
          localStorage.setItem('token', loginData.access_token);
          localStorage.setItem('access_token', loginData.access_token);
          localStorage.setItem('username', signupData.email);
          
          // Redirect with full page reload
          setTimeout(() => {
            window.location.href = '/dashboard';
          }, 500);
        } else {
          // Fallback to manual login
          navigate('/login', { 
            state: { 
              message: 'Account created successfully! Please log in.'
            }
          });
        }
      } catch (loginError) {
        console.error('Auto-login failed:', loginError);
        navigate('/login', { 
          state: { 
            message: 'Account created successfully! Please log in.'
          }
        });
      }
    } catch (err: any) {
      console.error('Signup error:', err);
      setError(err.message || 'An error occurred during signup. Please try again.');
      setSignupLoading(false);
    }
  };

  const handleSelectPracticeForExistingUser = async (practice: Practice) => {
    setSignupLoading(true);
    setError('');

    try {
      const token = localStorage.getItem('access_token') || localStorage.getItem('token');
      if (!token || !user) {
        throw new Error('Not authenticated. Please log in.');
      }

      // Update user's practice using the /me/practice endpoint
      const response = await fetch(`${API_ENDPOINTS.AUTH.ME}/practice`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          practice_id: practice.uuid,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to join practice');
      }

      // Reload to refresh user context
      window.location.href = '/pending-invitations';
    } catch (err: any) {
      console.error('Join practice error:', err);
      setError(err.message || 'An error occurred. Please try again.');
      setSignupLoading(false);
    }
  };

  const handleSelectPractice = (practice: Practice) => {
    if (isNewSignup) {
      handleSelectPracticeForNewSignup(practice);
    } else {
      handleSelectPracticeForExistingUser(practice);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-4xl mx-auto px-4 py-6">
          <Link 
            to={isNewSignup ? "/signup" : "/pending-invitations"} 
            className="inline-flex items-center text-sm text-gray-600 hover:text-gray-900 mb-4"
          >
            ← Back
          </Link>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Find Your Practice</h1>
          <p className="text-gray-600">
            {isNewSignup 
              ? "Search for your veterinary practice to join" 
              : "Search for your veterinary practice and request to join"
            }
          </p>
        </div>
      </div>

      <div className="flex-1 flex flex-col items-center justify-start p-8">
        <div className="w-full max-w-3xl">
          {error && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-sm text-red-800">{error}</p>
            </div>
          )}

          {/* Search Box */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                <Search className="h-5 w-5 text-gray-400" />
              </div>
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Search by practice name, city, state, or zip code..."
                className="w-full pl-12 pr-4 py-4 text-lg border border-gray-300 rounded-lg focus:ring-2 focus:ring-gray-500 focus:border-transparent transition"
                disabled={loading || signupLoading}
              />
            </div>
            
            {searchTerm.length > 0 && searchTerm.length < 2 && (
              <p className="mt-2 text-sm text-gray-500">Type at least 2 characters to search</p>
            )}
          </div>

          {/* Loading State */}
          {loading && (
            <div className="flex justify-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-800"></div>
            </div>
          )}

          {/* Results */}
          {!loading && searchTerm.length >= 2 && (
            <div className="space-y-3">
              {filteredPractices.length === 0 ? (
                <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8 text-center">
                  <Building2 className="h-12 w-12 text-gray-400 mx-auto mb-3" />
                  <p className="text-gray-600 mb-2">No practices found</p>
                  <p className="text-sm text-gray-500">
                    Try a different search term or check the spelling
                  </p>
                </div>
              ) : (
                <>
                  <p className="text-sm text-gray-600 mb-3">
                    Showing {filteredPractices.length} result{filteredPractices.length !== 1 ? 's' : ''}
                    {filteredPractices.length === 50 && ' (limited to 50 results, refine your search for more)'}
                  </p>
                  {filteredPractices.map((practice) => (
                    <button
                      key={practice.uuid}
                      onClick={() => handleSelectPractice(practice)}
                      disabled={signupLoading}
                      className="w-full bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:border-gray-400 hover:shadow-md transition text-left disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-3 mb-2">
                            <Building2 className="h-5 w-5 text-gray-400 flex-shrink-0" />
                            <h3 className="text-lg font-semibold text-gray-900">{practice.name}</h3>
                          </div>
                          {(practice.city || practice.state || practice.address_line1) && (
                            <div className="flex items-start gap-2 text-sm text-gray-600 ml-8">
                              <MapPin className="h-4 w-4 text-gray-400 flex-shrink-0 mt-0.5" />
                              <div>
                                {practice.address_line1 && <div>{practice.address_line1}</div>}
                                {(practice.city || practice.state) && (
                                  <div>
                                    {practice.city}{practice.city && practice.state ? ', ' : ''}{practice.state} {practice.zip_code}
                                  </div>
                                )}
                              </div>
                            </div>
                          )}
                        </div>
                        <div className="text-sm text-gray-500 ml-4">
                          Click to join
                        </div>
                      </div>
                    </button>
                  ))}
                </>
              )}
            </div>
          )}

          {/* Initial State */}
          {!loading && searchTerm.length < 2 && (
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-12 text-center">
              <Search className="h-16 w-16 text-gray-300 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">Start searching for your practice</h3>
              <p className="text-gray-600 max-w-md mx-auto">
                Enter your practice name, city, state, or zip code to find your veterinary practice and join your team.
              </p>
            </div>
          )}
        </div>
      </div>

      {signupLoading && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-8 max-w-sm">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-800 mx-auto mb-4"></div>
            <p className="text-center text-gray-900 font-medium">
              {isNewSignup ? 'Creating your account...' : 'Joining practice...'}
            </p>
          </div>
        </div>
      )}
    </div>
  );
};

export default PracticeSelection;
