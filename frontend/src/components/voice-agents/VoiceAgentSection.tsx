import React, { useState, useEffect } from 'react';
import { Bot, Phone, CheckCircle, AlertCircle, Loader, Edit } from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import { API_BASE_URL } from '../../config/api';

interface VoiceAgent {
  id: string;
  practice_id: string;
  agent_id: string;
  timezone: string;
  metadata: Record<string, any>;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  phone_number?: string;
}

const VoiceAgentSection: React.FC = () => {
  const { user } = useAuth();
  const [agent, setAgent] = useState<VoiceAgent | null>(null);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [welcomeMessage, setWelcomeMessage] = useState('');
  const [isEditingMessage, setIsEditingMessage] = useState(false);
  const [editedMessage, setEditedMessage] = useState('');
  const [isUpdatingMessage, setIsUpdatingMessage] = useState(false);

  useEffect(() => {
    if (user?.practice_id) {
      loadVoiceAgent();
    }
  }, [user?.practice_id]);

  const loadVoiceAgent = async () => {
    if (!user?.practice_id) return;

    setLoading(true);
    setError(null);

    try {
      const token = localStorage.getItem('access_token');
      const baseURL = API_BASE_URL;

      const response = await fetch(`${baseURL}/api/v1/practices/${user.practice_id}/voice-agent`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.status === 404) {
        // No agent exists - this is expected
        setAgent(null);
      } else if (response.ok) {
        const data = await response.json();
        setAgent(data);
        
        // Load welcome message
        loadWelcomeMessage();
      } else {
        throw new Error('Failed to load voice agent');
      }
    } catch (err: any) {
      console.error('Error loading voice agent:', err);
      setError(err.message || 'Failed to load voice agent');
    } finally {
      setLoading(false);
    }
  };

  const createVoiceAgent = async () => {
    if (!user?.practice_id) return;

    setCreating(true);
    setError(null);

    try {
      const token = localStorage.getItem('access_token');
      const baseURL = API_BASE_URL;

      const response = await fetch(`${baseURL}/api/v1/practices/${user.practice_id}/voice-agent`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          timezone: 'US/Pacific',
          metadata: {}
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to create voice agent');
      }

      const data = await response.json();
      setAgent(data);
    } catch (err: any) {
      console.error('Error creating voice agent:', err);
      setError(err.message || 'Failed to create voice agent');
    } finally {
      setCreating(false);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: 'numeric',
      minute: '2-digit'
    });
  };

  const loadWelcomeMessage = async () => {
    if (!user?.practice_id) return;

    try {
      const token = localStorage.getItem('access_token');
      const baseURL = API_BASE_URL;
      
      // URL encode the node name
      const nodeName = encodeURIComponent('Welcome Node');
      const url = `${baseURL}/api/v1/practices/${user.practice_id}/voice-agent/node/${nodeName}/message`;
      
      console.log('🔍 Loading welcome message from:', url);

      const response = await fetch(url, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const data = await response.json();
        console.log('✅ Loaded welcome message:', data);
        setWelcomeMessage(data.message);
      } else {
        console.error('❌ Failed to load welcome message, status:', response.status);
        const errorText = await response.text();
        console.error('Error response:', errorText);
        setWelcomeMessage('Unable to load current message');
      }
    } catch (err) {
      console.error('❌ Error loading welcome message:', err);
      setWelcomeMessage('Unable to load current message');
    }
  };

  const updateWelcomeMessage = async () => {
    if (!user?.practice_id || !editedMessage.trim()) return;

    setIsUpdatingMessage(true);
    setError(null);

    try {
      const token = localStorage.getItem('access_token');
      const baseURL = API_BASE_URL;
      
      // URL encode the node name
      const nodeName = encodeURIComponent('Welcome Node');
      const url = `${baseURL}/api/v1/practices/${user.practice_id}/voice-agent/node/${nodeName}/message`;
      
      console.log('🎭 Updating welcome message to:', url);
      console.log('📝 New message preview:', editedMessage.substring(0, 100));

      const response = await fetch(url, {
        method: 'PATCH',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          personality_text: editedMessage
        })
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        console.error('❌ Failed to update message, status:', response.status);
        throw new Error(errorData.detail || 'Failed to update message');
      }

      const data = await response.json();
      console.log('✅ Updated welcome message successfully:', data);
      
      // Reload the message from the server to confirm the update
      await loadWelcomeMessage();
      setIsEditingMessage(false);
    } catch (err: any) {
      console.error('❌ Error updating welcome message:', err);
      setError(err.message || 'Failed to update welcome message');
    } finally {
      setIsUpdatingMessage(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader className="w-8 h-8 text-blue-600 animate-spin" />
      </div>
    );
  }

  if (error && !agent) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6">
        <div className="flex items-start space-x-3">
          <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
          <div>
            <h3 className="text-sm font-medium text-red-800">Error</h3>
            <p className="text-sm text-red-700 mt-1">{error}</p>
            <button
              onClick={loadVoiceAgent}
              className="mt-3 text-sm font-medium text-red-600 hover:text-red-700"
            >
              Try Again
            </button>
          </div>
        </div>
      </div>
    );
  }

  // No agent - show setup view
  if (!agent) {
    return (
      <div className="bg-white rounded-lg border border-gray-200 p-12">
        <div className="max-w-md mx-auto text-center space-y-6">
          <div className="flex justify-center">
            <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center">
              <Bot className="w-8 h-8 text-blue-600" />
            </div>
          </div>

          <div className="space-y-3">
            <h3 className="text-xl font-semibold text-gray-900">
              No Voice Agent Configured
            </h3>
            <p className="text-base text-gray-600">
              Set up a voice agent to handle phone calls for your practice. The voice agent will help customers book appointments and answer common questions.
            </p>
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-3">
              <p className="text-sm text-red-700">{error}</p>
            </div>
          )}

          <button
            onClick={createVoiceAgent}
            disabled={creating}
            className="inline-flex items-center space-x-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {creating ? (
              <>
                <Loader className="w-5 h-5 animate-spin" />
                <span>Setting up...</span>
              </>
            ) : (
              <>
                <Bot className="w-5 h-5" />
                <span>Set Up Voice Agent</span>
              </>
            )}
          </button>
        </div>
      </div>
    );
  }

  // Agent exists - show configured view
  return (
    <div className="space-y-6">
      {/* Status Card */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center space-x-3">
            <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
              <Bot className="w-6 h-6 text-blue-600" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-gray-900">Voice Agent</h3>
              <p className="text-sm text-gray-500">Agent ID: {agent.agent_id.substring(0, 8)}...</p>
            </div>
          </div>
          <div className={`px-3 py-1 rounded-full flex items-center space-x-2 ${
            agent.is_active ? 'bg-green-100' : 'bg-gray-100'
          }`}>
            <div className={`w-2 h-2 rounded-full ${agent.is_active ? 'bg-green-600' : 'bg-gray-600'}`}></div>
            <span className={`text-sm font-medium ${agent.is_active ? 'text-green-700' : 'text-gray-700'}`}>
              {agent.is_active ? 'Active' : 'Inactive'}
            </span>
          </div>
        </div>

        {/* Agent Details Table */}
        <div className="border border-gray-200 rounded-lg overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <tbody className="bg-white divide-y divide-gray-200">
              <tr>
                <td className="px-4 py-3 text-sm font-medium text-gray-500 bg-gray-50 w-1/3">
                  <div className="flex items-center space-x-2">
                    <Phone className="w-4 h-4 text-gray-400" />
                    <span>Phone Number</span>
                  </div>
                </td>
                <td className="px-4 py-3 text-sm text-gray-900">
                  {agent.phone_number || (
                    <span className="text-gray-400 italic">Not configured</span>
                  )}
                </td>
              </tr>
              <tr>
                <td className="px-4 py-3 text-sm font-medium text-gray-500 bg-gray-50">
                  <div className="flex items-center space-x-2">
                    <CheckCircle className="w-4 h-4 text-gray-400" />
                    <span>Timezone</span>
                  </div>
                </td>
                <td className="px-4 py-3 text-sm text-gray-900">
                  {agent.timezone}
                </td>
              </tr>
              <tr>
                <td className="px-4 py-3 text-sm font-medium text-gray-500 bg-gray-50">
                  <span>Created</span>
                </td>
                <td className="px-4 py-3 text-sm text-gray-900">
                  {formatDate(agent.created_at)}
                </td>
              </tr>
              <tr>
                <td className="px-4 py-3 text-sm font-medium text-gray-500 bg-gray-50">
                  <span>Last Updated</span>
                </td>
                <td className="px-4 py-3 text-sm text-gray-900">
                  {formatDate(agent.updated_at)}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      {/* Welcome Message Section */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Welcome Message</h3>
          {!isEditingMessage && (
            <button
              onClick={() => {
                setEditedMessage(welcomeMessage);
                setIsEditingMessage(true);
              }}
              className="text-blue-600 hover:text-blue-700 text-sm font-medium flex items-center space-x-1"
            >
              <Edit className="w-4 h-4" />
              <span>Edit</span>
            </button>
          )}
        </div>

        {isEditingMessage ? (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Current Message:
              </label>
              <textarea
                value={editedMessage}
                onChange={(e) => setEditedMessage(e.target.value)}
                rows={6}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                placeholder="Enter welcome message..."
              />
            </div>
            <div className="flex justify-end space-x-3">
              <button
                onClick={() => {
                  setIsEditingMessage(false);
                  setEditedMessage('');
                }}
                disabled={isUpdatingMessage}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                onClick={updateWelcomeMessage}
                disabled={isUpdatingMessage || !editedMessage.trim()}
                className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
              >
                {isUpdatingMessage ? (
                  <>
                    <Loader className="w-4 h-4 animate-spin" />
                    <span>Updating...</span>
                  </>
                ) : (
                  <span>Update</span>
                )}
              </button>
            </div>
          </div>
        ) : (
          <div>
            <p className="text-sm text-gray-500 mb-2">Current Message:</p>
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
              <p className="text-sm text-gray-900 whitespace-pre-wrap">
                {welcomeMessage || 'Loading...'}
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default VoiceAgentSection;

