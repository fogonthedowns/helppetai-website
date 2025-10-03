import React, { useState, useEffect } from 'react';
import { Phone, Loader, Clock, X } from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import { API_BASE_URL } from '../../config/api';

interface CallAnalysis {
  call_summary?: string;
  user_sentiment?: string;
  sentiment_color?: string;
  call_successful?: boolean;
  success_color?: string;
  appointment_type?: string;
  urgency_level?: string;
  pet_mentioned?: string;
  symptoms_mentioned?: string[];
  appointment_scheduled?: boolean;
}

interface Call {
  call_id: string;
  from_number?: string;
  to_number?: string;
  start_timestamp?: string;
  end_timestamp?: string;
  duration_ms?: number;
  call_status?: string;
  disconnect_reason?: string;
  recording_url?: string;
  agent_id?: string;
  call_analysis?: CallAnalysis;
}

const CallHistorySection: React.FC = () => {
  const { user } = useAuth();
  const [calls, setCalls] = useState<Call[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedCall, setSelectedCall] = useState<Call | null>(null);
  const [showCallDetail, setShowCallDetail] = useState(false);
  const [audioPlayer, setAudioPlayer] = useState<HTMLAudioElement | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);

  useEffect(() => {
    if (user?.practice_id) {
      loadCalls();
    }
  }, [user?.practice_id]);

  const loadCalls = async () => {
    if (!user?.practice_id) return;

    setLoading(true);
    setError(null);

    try {
      const token = localStorage.getItem('access_token');
      const baseURL = API_BASE_URL;

      const response = await fetch(
        `${baseURL}/api/v1/call-analysis/practice/${user.practice_id}/calls?limit=20&offset=0`,
        {
          headers: { 'Authorization': `Bearer ${token}` }
        }
      );

      if (!response.ok) {
        throw new Error('Failed to load call history');
      }

      const data = await response.json();
      // API might return { calls: [...] } or just [...]
      const callsArray = Array.isArray(data) ? data : (data.calls || []);
      setCalls(callsArray);
    } catch (err: any) {
      console.error('Error loading calls:', err);
      setError(err.message || 'Failed to load call history');
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (timestamp?: string) => {
    if (!timestamp) return 'Unknown';
    const date = new Date(timestamp);
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
      hour12: true
    });
  };

  const formatDuration = (startTimestamp?: string, endTimestamp?: string) => {
    if (!startTimestamp || !endTimestamp) return 'Unknown';
    
    const start = new Date(startTimestamp).getTime();
    const end = new Date(endTimestamp).getTime();
    const durationMs = end - start;
    const totalSeconds = Math.floor(durationMs / 1000);
    const minutes = Math.floor(totalSeconds / 60);
    const seconds = totalSeconds % 60;
    
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  };

  const getSentimentColor = (color?: string) => {
    switch (color?.toLowerCase()) {
      case 'green': return 'bg-green-100 text-green-800';
      case 'red': return 'bg-red-100 text-red-800';
      case 'orange': return 'bg-orange-100 text-orange-800';
      case 'yellow': return 'bg-yellow-100 text-yellow-800';
      case 'blue': return 'bg-blue-100 text-blue-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const playRecording = (url: string) => {
    // Stop current playback if any
    if (audioPlayer) {
      audioPlayer.pause();
      setAudioPlayer(null);
      setIsPlaying(false);
    }

    const audio = new Audio(url);
    audio.play();
    setAudioPlayer(audio);
    setIsPlaying(true);

    audio.onended = () => {
      setIsPlaying(false);
      setAudioPlayer(null);
    };
  };

  const stopRecording = () => {
    if (audioPlayer) {
      audioPlayer.pause();
      setAudioPlayer(null);
      setIsPlaying(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader className="w-8 h-8 text-blue-600 animate-spin" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6">
        <p className="text-red-800">{error}</p>
      </div>
    );
  }

  if (calls.length === 0) {
    return (
      <div className="bg-white rounded-lg border border-gray-200 p-12 text-center">
        <Phone className="w-12 h-12 text-gray-400 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">No Call History</h3>
        <p className="text-sm text-gray-500">
          Call history will appear here once your voice agent starts receiving calls.
        </p>
      </div>
    );
  }

  return (
    <>
      <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
        <table className="min-w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                From
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Time
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Duration
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Sentiment
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {calls.map((call) => (
              <tr
                key={call.call_id}
                onClick={() => {
                  setSelectedCall(call);
                  setShowCallDetail(true);
                }}
                className="hover:bg-gray-50 cursor-pointer transition-colors"
              >
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex flex-col">
                    <span className="text-sm font-medium text-gray-900">
                      {call.from_number || 'Unknown Number'}
                    </span>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center text-sm text-gray-600">
                    <Clock className="w-4 h-4 mr-1" />
                    {formatDate(call.start_timestamp)}
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                  {formatDuration(call.start_timestamp, call.end_timestamp)}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  {call.call_analysis?.user_sentiment && (
                    <span className={`px-3 py-1 inline-flex text-sm font-semibold rounded-full ${getSentimentColor(call.call_analysis.sentiment_color)}`}>
                      {call.call_analysis.user_sentiment}
                    </span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Call Detail Modal */}
      {showCallDetail && selectedCall && (
        <div className="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
              <h3 className="text-lg font-semibold text-gray-900">Call Details</h3>
              <button
                onClick={() => {
                  setShowCallDetail(false);
                  setSelectedCall(null);
                  stopRecording();
                }}
                className="text-gray-400 hover:text-gray-600"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="p-6 space-y-6">
              {/* Call Header Info */}
              <div className="bg-gray-50 rounded-lg p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <h4 className="text-base font-semibold text-gray-900">Call Information</h4>
                  <span className="text-sm font-medium text-gray-600">
                    {formatDuration(selectedCall.start_timestamp, selectedCall.end_timestamp)}
                  </span>
                </div>
                
                {selectedCall.start_timestamp && (
                  <p className="text-sm text-gray-600">
                    {new Date(selectedCall.start_timestamp).toLocaleString('en-US', {
                      dateStyle: 'full',
                      timeStyle: 'short'
                    })}
                  </p>
                )}

                {selectedCall.from_number && (
                  <div className="flex items-center text-sm text-gray-600">
                    <Phone className="w-4 h-4 mr-2" />
                    <span>From: {selectedCall.from_number}</span>
                  </div>
                )}

                {selectedCall.to_number && (
                  <div className="flex items-center text-sm text-gray-600">
                    <Phone className="w-4 h-4 mr-2" />
                    <span>To: {selectedCall.to_number}</span>
                  </div>
                )}

                {selectedCall.call_status && (
                  <div className="text-sm text-gray-600">
                    Status: <span className="capitalize">{selectedCall.call_status}</span>
                  </div>
                )}
              </div>

              {/* Call Analysis */}
              {selectedCall.call_analysis && (
                <div className="bg-gray-50 rounded-lg p-4 space-y-4">
                  <h4 className="text-base font-semibold text-gray-900">Call Analysis</h4>

                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      {selectedCall.call_analysis.call_successful !== undefined && (
                        <span className={`text-sm font-medium ${
                          selectedCall.call_analysis.call_successful ? 'text-green-600' : 'text-red-600'
                        }`}>
                          {selectedCall.call_analysis.call_successful ? '✓ Successful' : '✗ Unsuccessful'}
                        </span>
                      )}
                    </div>

                    {selectedCall.call_analysis.user_sentiment && (
                      <span className={`px-3 py-1 text-sm font-semibold rounded-full ${getSentimentColor(selectedCall.call_analysis.sentiment_color)}`}>
                        {selectedCall.call_analysis.user_sentiment}
                      </span>
                    )}
                  </div>

                  {selectedCall.call_analysis.call_summary && (
                    <div>
                      <p className="text-sm font-semibold text-gray-700 mb-1">Summary</p>
                      <p className="text-sm text-gray-900">{selectedCall.call_analysis.call_summary}</p>
                    </div>
                  )}

                  {selectedCall.call_analysis.appointment_type && (
                    <div className="text-sm">
                      <span className="font-semibold text-gray-700">Appointment Type:</span>{' '}
                      <span className="capitalize text-gray-900">{selectedCall.call_analysis.appointment_type}</span>
                    </div>
                  )}

                  {selectedCall.call_analysis.urgency_level && (
                    <div className="text-sm">
                      <span className="font-semibold text-gray-700">Urgency Level:</span>{' '}
                      <span className="capitalize text-gray-900">{selectedCall.call_analysis.urgency_level}</span>
                    </div>
                  )}

                  {selectedCall.call_analysis.pet_mentioned && (
                    <div className="text-sm">
                      <span className="font-semibold text-gray-700">Pet Mentioned:</span>{' '}
                      <span className="text-gray-900">{selectedCall.call_analysis.pet_mentioned}</span>
                    </div>
                  )}

                  {selectedCall.call_analysis.symptoms_mentioned && selectedCall.call_analysis.symptoms_mentioned.length > 0 && (
                    <div>
                      <p className="text-sm font-semibold text-gray-700 mb-1">Symptoms Mentioned</p>
                      <p className="text-sm text-gray-900">
                        {selectedCall.call_analysis.symptoms_mentioned.join(', ')}
                      </p>
                    </div>
                  )}

                  {selectedCall.call_analysis.appointment_scheduled !== undefined && (
                    <div className="text-sm">
                      <span className="font-semibold text-gray-700">Appointment Scheduled:</span>{' '}
                      <span className="text-gray-900">{selectedCall.call_analysis.appointment_scheduled ? 'Yes' : 'No'}</span>
                    </div>
                  )}
                </div>
              )}

              {/* Technical Details */}
              <div className="bg-gray-50 rounded-lg p-4 space-y-3">
                <h4 className="text-base font-semibold text-gray-900">Technical Details</h4>

                {selectedCall.call_id && (
                  <div className="text-sm">
                    <span className="font-semibold text-gray-700">Call ID:</span>{' '}
                    <span className="font-mono text-gray-900">{selectedCall.call_id}</span>
                  </div>
                )}

                {selectedCall.agent_id && (
                  <div className="text-sm">
                    <span className="font-semibold text-gray-700">Agent ID:</span>{' '}
                    <span className="font-mono text-gray-900">{selectedCall.agent_id}</span>
                  </div>
                )}

                {selectedCall.disconnect_reason && (
                  <div className="text-sm">
                    <span className="font-semibold text-gray-700">Disconnect Reason:</span>{' '}
                    <span className="capitalize text-gray-900">{selectedCall.disconnect_reason}</span>
                  </div>
                )}

                {selectedCall.recording_url && (
                  <div className="flex items-center justify-between pt-2">
                    <span className="text-sm font-semibold text-gray-700">Recording</span>
                    <button
                      onClick={() => {
                        if (isPlaying) {
                          stopRecording();
                        } else {
                          playRecording(selectedCall.recording_url!);
                        }
                      }}
                      className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                        isPlaying
                          ? 'bg-red-600 hover:bg-red-700 text-white'
                          : 'bg-blue-600 hover:bg-blue-700 text-white'
                      }`}
                    >
                      {isPlaying ? 'Stop' : 'Play'}
                    </button>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default CallHistorySection;

