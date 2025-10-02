import React, { useState, useEffect } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { API_ENDPOINTS, API_BASE_URL } from '../../config/api';

interface Practice {
  uuid: string;
  name: string;
  address_line1?: string;
  city?: string;
  state?: string;
}

interface InvitationDetails {
  id: string;
  practice_id: string;
  practice_name: string;
  email: string;
  status: string;
}

const VetSignup: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const searchParams = new URLSearchParams(location.search);
  const inviteId = searchParams.get('invite');
  const inviteCode = searchParams.get('code');
  
  const [formData, setFormData] = useState({
    username: '',
    password: '',
    confirmPassword: '',
    email: '',
    full_name: '',
    practice_id: ''
  });
  const [practices, setPractices] = useState<Practice[]>([]);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [practicesLoading, setPracticesLoading] = useState(true);
  const [invitationDetails, setInvitationDetails] = useState<InvitationDetails | null>(null);
  const [invitationLoading, setInvitationLoading] = useState(false);

  useEffect(() => {
    if (inviteId && inviteCode) {
      fetchInvitationDetails();
    } else {
      fetchPractices();
    }
  }, [inviteId, inviteCode]);

  const fetchInvitationDetails = async () => {
    if (!inviteId || !inviteCode) return;
    
    setInvitationLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/invites/${inviteId}?code=${inviteCode}`);
      if (response.ok) {
        const data = await response.json();
        setInvitationDetails(data);
        // Pre-populate email, username (same as email), and practice_id
        setFormData(prev => ({
          ...prev,
          email: data.email,
          username: data.email, // Set username to email
          practice_id: data.practice_id
        }));
      } else {
        setError('Invalid invitation link. Please check the link and try again.');
      }
    } catch (error) {
      console.error('Failed to fetch invitation:', error);
      setError('Failed to load invitation details.');
    } finally {
      setInvitationLoading(false);
      setPracticesLoading(false);
    }
  };

  const fetchPractices = async () => {
    try {
      const response = await fetch(API_ENDPOINTS.PRACTICES.LIST);
      if (response.ok) {
        const data = await response.json();
        setPractices(data);
      }
    } catch (error) {
      console.error('Failed to fetch practices:', error);
    } finally {
      setPracticesLoading(false);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSignup = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match');
      setLoading(false);
      return;
    }

    if (formData.password.length < 6) {
      setError('Password must be at least 6 characters long');
      setLoading(false);
      return;
    }

    if (!formData.email.includes('@')) {
      setError('Please enter a valid email address');
      setLoading(false);
      return;
    }

    try {
      const signupData = {
        username: formData.username,
        password: formData.password,
        email: formData.email,
        full_name: formData.full_name,
        role: invitationDetails ? 'PENDING_INVITE' : 'VET_STAFF',
        practice_id: formData.practice_id || undefined
      };

      const response = await fetch(API_ENDPOINTS.AUTH.SIGNUP, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(signupData),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Signup failed');
      }

      // If coming from invitation, auto-login and redirect to accept-invite page
      if (invitationDetails && inviteId && inviteCode) {
        try {
          // Auto-login after signup
          const loginResponse = await fetch(API_ENDPOINTS.AUTH.LOGIN, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: new URLSearchParams({
              username: formData.username,
              password: formData.password,
            }),
          });

          if (loginResponse.ok) {
            const loginData = await loginResponse.json();
            localStorage.setItem('access_token', loginData.access_token);
            
            // Redirect to accept-invite page
            setSuccess(true);
            setTimeout(() => {
              navigate(`/accept-invite/${inviteId}?code=${inviteCode}`);
            }, 1000);
          } else {
            // Fall back to manual login
            setSuccess(true);
            setTimeout(() => {
              navigate(`/login?redirect=/accept-invite/${inviteId}?code=${inviteCode}`, { 
                state: { 
                  message: 'Account created successfully! Please log in to join the practice.'
                }
              });
            }, 2000);
          }
        } catch (loginError) {
          console.error('Auto-login failed:', loginError);
          // Fall back to manual login
          setSuccess(true);
          setTimeout(() => {
            navigate(`/login?redirect=/accept-invite/${inviteId}?code=${inviteCode}`, { 
              state: { 
                message: 'Account created successfully! Please log in to join the practice.'
              }
            });
          }, 2000);
        }
      } else {
        setSuccess(true);
        setTimeout(() => {
          navigate('/login', { 
            state: { 
              message: 'Veterinary account created successfully! Please log in.',
              practiceId: formData.practice_id 
            }
          });
        }, 2000);
      }
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Signup failed');
    } finally {
      setLoading(false);
    }
  };

  if (success) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-emerald-50 via-white to-teal-50 flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-md w-full">
          <div className="bg-white rounded-2xl shadow-xl p-8 text-center">
            <div className="mx-auto flex items-center justify-center h-20 w-20 rounded-full bg-gradient-to-r from-emerald-400 to-teal-500 mb-6">
              <svg className="h-10 w-10 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <h2 className="text-3xl font-bold text-gray-900 mb-4">Welcome to HelpPetAI! 🩺</h2>
            <p className="text-gray-600 mb-2">
              Your veterinary account has been created successfully.
            </p>
            {formData.practice_id && (
              <p className="text-sm text-emerald-600 mb-4">
                You can complete your practice association after logging in.
              </p>
            )}
            <div className="flex items-center justify-center text-sm text-gray-500">
              <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-emerald-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Redirecting to login...
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-emerald-50 via-white to-teal-50 flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-lg w-full">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="flex justify-center mb-6">
            <div className="relative">
              <img 
                src="/logo_clear_back.png" 
                alt="HelpPetAI Logo" 
                width="64" 
                height="64" 
                className="rounded-2xl shadow-lg"
              />
              <div className="absolute -top-1 -right-1 h-6 w-6 bg-gradient-to-r from-emerald-500 to-teal-600 rounded-full flex items-center justify-center">
                <svg className="h-3 w-3 text-white" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
                </svg>
              </div>
            </div>
          </div>
          <h1 className="text-4xl font-bold bg-gradient-to-r from-emerald-700 to-teal-700 bg-clip-text text-transparent mb-3">
            Join as a Veterinarian
          </h1>
          <p className="text-lg text-gray-600 max-w-md mx-auto">
            Access advanced AI tools and connect with pet owners in your practice
          </p>
        </div>

        {/* Form */}
        <div className="bg-white rounded-2xl shadow-xl p-8">
          <form onSubmit={handleSignup} className="space-y-6">
            {error && (
              <div className="bg-red-50 border-l-4 border-red-400 rounded-lg p-4">
                <div className="flex">
                  <div className="flex-shrink-0">
                    <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                    </svg>
                  </div>
                  <div className="ml-3">
                    <p className="text-sm text-red-800 font-medium">{error}</p>
                  </div>
                </div>
              </div>
            )}

            {/* Professional Information */}
            <div className="space-y-4">
              <div className="flex items-center space-x-2 mb-4">
                <div className="h-8 w-8 bg-gradient-to-r from-emerald-500 to-teal-600 rounded-lg flex items-center justify-center">
                  <svg className="h-4 w-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                  </svg>
                </div>
                <h3 className="text-lg font-semibold text-gray-900">Professional Information</h3>
              </div>

              <div className="grid grid-cols-1 gap-4">
                <div>
                  <label htmlFor="full_name" className="block text-sm font-medium text-gray-700 mb-2">
                    Full Name
                  </label>
                  <input
                    id="full_name"
                    name="full_name"
                    type="text"
                    required
                    value={formData.full_name}
                    onChange={handleInputChange}
                    className="w-full px-4 py-3 border border-gray-300 rounded-xl shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition-all duration-200"
                    placeholder="Dr. Sarah Johnson"
                    disabled={loading}
                  />
                </div>

                <div>
                  <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-2">
                    {invitationDetails ? 'Username' : 'Professional Email'}
                    {invitationDetails && (
                      <span className="ml-2 text-xs text-green-600">(from invitation)</span>
                    )}
                  </label>
                  <input
                    id="email"
                    name="email"
                    type="email"
                    required
                    value={formData.email}
                    onChange={handleInputChange}
                    className="w-full px-4 py-3 border border-gray-300 rounded-xl shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition-all duration-200 disabled:bg-gray-50 disabled:text-gray-600"
                    placeholder="dr.johnson@vetclinic.com"
                    disabled={loading || !!invitationDetails}
                  />
                </div>
              </div>
            </div>

            {/* Account Information */}
            <div className="space-y-4">
              <div className="flex items-center space-x-2 mb-4">
                <div className="h-8 w-8 bg-gradient-to-r from-teal-500 to-cyan-600 rounded-lg flex items-center justify-center">
                  <svg className="h-4 w-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 7a2 2 0 012 2m0 0a2 2 0 012 2m-2-2a2 2 0 00-2 2m0 0a2 2 0 01-2 2m2-2a2 2 0 012 2M9 5a2 2 0 012 2v0a2 2 0 01-2 2H7a2 2 0 01-2-2V7a2 2 0 012-2h2z" />
                  </svg>
                </div>
                <h3 className="text-lg font-semibold text-gray-900">Account Setup</h3>
              </div>

              <div className="grid grid-cols-1 gap-4">
                {/* Only show username field if NOT coming from invitation */}
                {!invitationDetails && (
                  <div>
                    <label htmlFor="username" className="block text-sm font-medium text-gray-700 mb-2">
                      Username
                    </label>
                    <input
                      id="username"
                      name="username"
                      type="text"
                      required
                      value={formData.username}
                      onChange={handleInputChange}
                      className="w-full px-4 py-3 border border-gray-300 rounded-xl shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition-all duration-200"
                      placeholder="Choose a unique username"
                      disabled={loading}
                    />
                  </div>
                )}
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-2">
                      Password
                    </label>
                    <input
                      id="password"
                      name="password"
                      type="password"
                      required
                      value={formData.password}
                      onChange={handleInputChange}
                      className="w-full px-4 py-3 border border-gray-300 rounded-xl shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition-all duration-200"
                      placeholder="Min 6 characters"
                      disabled={loading}
                    />
                  </div>

                  <div>
                    <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-700 mb-2">
                      Confirm Password
                    </label>
                    <input
                      id="confirmPassword"
                      name="confirmPassword"
                      type="password"
                      required
                      value={formData.confirmPassword}
                      onChange={handleInputChange}
                      className="w-full px-4 py-3 border border-gray-300 rounded-xl shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition-all duration-200"
                      placeholder="Confirm password"
                      disabled={loading}
                    />
                  </div>
                </div>
              </div>
            </div>

            {/* Practice Association */}
            <div className="space-y-4">
              <div className="flex items-center space-x-2 mb-4">
                <div className="h-8 w-8 bg-gradient-to-r from-cyan-500 to-blue-600 rounded-lg flex items-center justify-center">
                  <svg className="h-4 w-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-4m-5 0H9m0 0H5m0 0h2M7 7h10M7 11h10M7 15h10" />
                  </svg>
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">
                    {invitationDetails ? 'Joining Practice' : 'Practice Association'}
                  </h3>
                  <p className="text-sm text-gray-500">
                    {invitationDetails ? 'You are being invited to join this practice' : 'Associate with your veterinary practice (optional)'}
                  </p>
                </div>
              </div>

              <div>
                {invitationLoading || practicesLoading ? (
                  <div className="w-full px-4 py-3 border border-gray-300 rounded-xl bg-gray-50 flex items-center">
                    <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-gray-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    <span className="text-gray-500">Loading practice details...</span>
                  </div>
                ) : invitationDetails ? (
                  <div className="w-full px-4 py-4 border-2 border-green-200 bg-green-50 rounded-xl">
                    <div className="flex items-center">
                      <div className="flex-shrink-0">
                        <svg className="h-6 w-6 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                      </div>
                      <div className="ml-3">
                        <p className="text-sm font-medium text-green-900">
                          🏥 {invitationDetails.practice_name}
                        </p>
                        <p className="text-xs text-green-700 mt-1">
                          You'll join this practice after completing registration
                        </p>
                      </div>
                    </div>
                  </div>
                ) : (
                  <>
                    <select
                      id="practice_id"
                      name="practice_id"
                      value={formData.practice_id}
                      onChange={handleInputChange}
                      className="w-full px-4 py-3 border border-gray-300 rounded-xl shadow-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition-all duration-200"
                      disabled={loading}
                    >
                      <option value="">🏥 Select your practice (optional)</option>
                      {practices.map((practice) => (
                        <option key={practice.uuid} value={practice.uuid}>
                          {practice.name}
                          {practice.city && practice.state && ` - ${practice.city}, ${practice.state}`}
                        </option>
                      ))}
                    </select>
                    <p className="mt-2 text-xs text-gray-500 flex items-center">
                      <svg className="h-4 w-4 mr-1 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      Don't see your practice? You can add it later or contact support to add your practice.
                    </p>
                  </>
                )}
              </div>
            </div>

            {/* Submit Button */}
            <div className="pt-4">
              <button
                type="submit"
                disabled={loading}
                className="w-full flex justify-center items-center py-4 px-6 border border-transparent rounded-xl text-base font-medium text-white bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-700 hover:to-teal-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-emerald-500 disabled:opacity-50 disabled:cursor-not-allowed transform transition-all duration-200 hover:scale-[1.02] active:scale-[0.98] shadow-lg"
              >
                {loading ? (
                  <>
                    <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Creating your veterinary account...
                  </>
                ) : (
                  <>
                    <svg className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    Create Veterinary Account
                  </>
                )}
              </button>
            </div>
          </form>

          {/* Footer Links */}
          <div className="mt-8 text-center space-y-3">
            <p className="text-sm text-gray-600">
              Already have an account?{' '}
              <Link to="/login" className="font-medium text-emerald-600 hover:text-emerald-500 transition-colors">
                Sign in here
              </Link>
            </p>
            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-gray-200" />
              </div>
              <div className="relative flex justify-center text-sm">
                <span className="px-4 bg-white text-gray-500">or</span>
              </div>
            </div>
            <p className="text-sm text-gray-600">
              Are you a pet owner?{' '}
              <Link to="/signup" className="font-medium bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent hover:from-blue-700 hover:to-indigo-700 transition-all">
                Create pet owner account →
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default VetSignup;