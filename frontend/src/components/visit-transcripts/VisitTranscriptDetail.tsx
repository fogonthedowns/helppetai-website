import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { 
  FileText, 
  Calendar, 
  User, 
  Edit, 
  Trash2, 
  Play, 
  Pause,
  Volume2,
  Clock,
  CheckCircle,
  XCircle,
  AlertCircle,
  Download
} from 'lucide-react';
import { 
  VisitTranscript, 
  TranscriptState,
  TRANSCRIPT_STATE_LABELS,
  TRANSCRIPT_STATE_COLORS
} from '../../types/visitTranscript';
import { API_ENDPOINTS } from '../../config/api';
import { useAuth } from '../../contexts/AuthContext';
import { getAuthHeaders } from '../../utils/authUtils';
import Breadcrumb, { BreadcrumbItem } from '../common/Breadcrumb';

const VisitTranscriptDetail: React.FC = () => {
  const { petId, transcriptId } = useParams<{ petId: string; transcriptId: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();
  const [transcript, setTranscript] = useState<VisitTranscript | null>(null);
  const [pet, setPet] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [audioError, setAudioError] = useState<string | null>(null);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [audioElement, setAudioElement] = useState<HTMLAudioElement | null>(null);
  const [debugInfo, setDebugInfo] = useState<any>(null);
  const [showDebug, setShowDebug] = useState(false);
  const [audioLoading, setAudioLoading] = useState(false);

  useEffect(() => {
    if (transcriptId && petId) {
      fetchTranscript();
      fetchPet();
    }
  }, [transcriptId, petId]);

  useEffect(() => {
    // Cleanup audio when component unmounts
    return () => {
      if (audioElement) {
        audioElement.pause();
        audioElement.src = '';
        setAudioElement(null);
      }
    };
  }, [audioElement]);

  const fetchTranscript = async () => {
    if (!transcriptId) return;

    try {
      setLoading(true);
      setError(null);

      const response = await fetch(API_ENDPOINTS.VISIT_TRANSCRIPTS.GET(transcriptId), {
        headers: getAuthHeaders()
      });

      if (!response.ok) {
        if (response.status === 404) {
          throw new Error('Visit transcript not found');
        }
        throw new Error(`Failed to fetch visit transcript: ${response.statusText}`);
      }

      const data = await response.json();
      setTranscript(data);
    } catch (err) {
      console.error('Error fetching visit transcript:', err);
      setError(err instanceof Error ? err.message : 'Failed to load visit transcript');
    } finally {
      setLoading(false);
    }
  };

  const fetchPet = async () => {
    if (!petId) return;

    try {
      const response = await fetch(API_ENDPOINTS.PETS.GET(petId), {
        headers: getAuthHeaders()
      });

      if (response.ok) {
        const petData = await response.json();
        setPet(petData);
      }
    } catch (err) {
      console.error('Error fetching pet:', err);
      // Don't set error for pet fetch failure, just log it
    }
  };

  const canEdit = () => {
    if (!transcript || !user) return false;
    return user.role === 'ADMIN' || transcript.created_by === user.id;
  };

  const canDelete = () => {
    return user?.role === 'ADMIN';
  };

  const handleDelete = async () => {
    if (!transcriptId) return;

    try {
      const response = await fetch(API_ENDPOINTS.VISIT_TRANSCRIPTS.DELETE(transcriptId), {
        method: 'DELETE',
        headers: getAuthHeaders()
      });

      if (!response.ok) {
        throw new Error('Failed to delete visit transcript');
      }

      navigate(`/pets/${petId}`);
    } catch (err) {
      console.error('Error deleting visit transcript:', err);
      setError(err instanceof Error ? err.message : 'Failed to delete visit transcript');
    }
  };

  const getErrorMessage = (error: unknown): string => {
    if (error instanceof Error) {
      return error.message;
    }
    return String(error);
  };

  const toggleAudio = async () => {
    if (!transcript?.audio_transcript_url || !transcriptId) return;

    // Clear previous audio errors
    setAudioError(null);

    // If audio element exists, just toggle play/pause
    if (audioElement) {
      if (isPlaying) {
        audioElement.pause();
        setIsPlaying(false);
      } else {
        try {
          await audioElement.play();
          setIsPlaying(true);
        } catch (playError) {
          console.error('Resume play failed:', playError);
          setAudioError(`Playback failed: ${getErrorMessage(playError)}`);
          setIsPlaying(false);
        }
      }
      return;
    }

    // Create new audio element
    try {
      setAudioLoading(true);
      
      // Get presigned URL for secure audio access
      const response = await fetch(API_ENDPOINTS.VISIT_TRANSCRIPTS.AUDIO_PLAYBACK(transcriptId), {
        headers: getAuthHeaders()
      });

      if (!response.ok) {
        const errorText = await response.text();
        console.error('Audio access failed:', response.status, errorText);
        throw new Error(`Failed to get audio access: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();
      console.log('Audio playback response:', data);
      
      if (!data.presigned_url) {
        throw new Error('Invalid audio access response - no presigned URL');
      }

      // Create and configure audio element
      const audio = new Audio();
      
      // Set up event listeners
      audio.addEventListener('loadstart', () => {
        console.log('Audio loading started');
      });
      
      audio.addEventListener('loadedmetadata', () => {
        console.log('Audio metadata loaded');
      });
      
      audio.addEventListener('canplay', () => {
        console.log('Audio can start playing');
      });
      
      audio.addEventListener('ended', () => {
        console.log('Audio playback ended');
        setIsPlaying(false);
      });
      
      audio.addEventListener('error', (e) => {
        console.error('Audio error event:', e);
        console.error('Audio error details:', {
          error: audio.error,
          errorCode: audio.error?.code,
          errorMessage: audio.error?.message,
          networkState: audio.networkState,
          readyState: audio.readyState,
          src: audio.src
        });
        
        let errorMessage = 'Failed to load audio file';
        
        if (audio.error) {
          switch (audio.error.code) {
            case MediaError.MEDIA_ERR_ABORTED:
              errorMessage = 'Audio loading was aborted';
              break;
            case MediaError.MEDIA_ERR_NETWORK:
              errorMessage = 'Network error while loading audio. The URL may have expired. Click Play again to get a fresh URL.';
              // Clear the audio element so next play will get a fresh URL
              setAudioElement(null);
              break;
            case MediaError.MEDIA_ERR_DECODE:
              errorMessage = 'Audio file is corrupted or malformed. This recording may need to be re-uploaded.';
              break;
            case MediaError.MEDIA_ERR_SRC_NOT_SUPPORTED:
              errorMessage = 'Audio format not supported by this browser. Try downloading the file or use a different browser.';
              break;
            default:
              errorMessage = `Audio error: ${audio.error.message || 'Unknown error'}`;
          }
        }
        
        setAudioError(errorMessage);
        setIsPlaying(false);
        setAudioLoading(false);
      });

      // Check browser format support
      const canPlayM4A = audio.canPlayType('audio/mp4; codecs="mp4a.40.2"');
      const canPlayM4AAlt = audio.canPlayType('audio/m4a');
      
      console.log('Browser M4A support:', {
        'audio/mp4': canPlayM4A,
        'audio/m4a': canPlayM4AAlt,
        userAgent: navigator.userAgent
      });
      
      // If browser doesn't support M4A, show error immediately
      if (!canPlayM4A && !canPlayM4AAlt) {
        throw new Error('Your browser does not support M4A audio files. Please download the file or try a different browser.');
      }
      
      // Set the source and load
      audio.src = data.presigned_url;
      audio.load();
      
      setAudioElement(audio);
      
      // Try to play
      try {
        await audio.play();
        setIsPlaying(true);
        console.log('Audio started playing successfully');
      } catch (playError) {
        console.error('Play failed:', playError);
        
        // Handle different play errors with proper type checking
        let errorMessage = `Playback failed: ${getErrorMessage(playError)}`;
        
        if (playError instanceof Error) {
          if (playError.name === 'NotAllowedError') {
            errorMessage = 'Browser blocked autoplay. Click Play again to start audio.';
          } else if (playError.name === 'NotSupportedError') {
            errorMessage = 'Audio format not supported. Try downloading the file.';
          }
        }
        
        setAudioError(errorMessage);
        setIsPlaying(false);
      }
        
    } catch (err) {
      console.error('Error loading audio:', err);
      setAudioError(getErrorMessage(err));
      setIsPlaying(false);
    } finally {
      setAudioLoading(false);
    }
  };

  const downloadAudio = async () => {
    if (!transcriptId) return;

    try {
      const response = await fetch(API_ENDPOINTS.VISIT_TRANSCRIPTS.AUDIO_PLAYBACK(transcriptId), {
        headers: getAuthHeaders()
      });

      if (!response.ok) {
        throw new Error('Failed to get download URL');
      }

      const data = await response.json();
      
      if (data.presigned_url) {
        // Create a temporary link to trigger download
        const link = document.createElement('a');
        link.href = data.presigned_url;
        link.download = data.filename || 'recording.m4a';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
      }
    } catch (err) {
      console.error('Error downloading audio:', err);
      setAudioError('Failed to download audio file');
    }
  };

  const fetchDebugInfo = async () => {
    if (!transcriptId) return;
    
    try {
      const response = await fetch(API_ENDPOINTS.VISIT_TRANSCRIPTS.DEBUG(transcriptId), {
        headers: getAuthHeaders()
      });
      
      if (response.ok) {
        const data = await response.json();
        setDebugInfo(data);
        console.log('Debug info:', data);
      } else {
        console.error('Failed to fetch debug info:', response.status);
      }
    } catch (err) {
      console.error('Error fetching debug info:', err);
    }
  };

  const formatDate = (timestamp: number) => {
    return new Date(timestamp * 1000).toLocaleString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getStateIcon = (state: TranscriptState) => {
    switch (state) {
      case TranscriptState.NEW:
        return <Clock className="w-5 h-5" />;
      case TranscriptState.PROCESSING:
        return <Clock className="w-5 h-5 animate-spin" />;
      case TranscriptState.PROCESSED:
        return <CheckCircle className="w-5 h-5" />;
      case TranscriptState.FAILED:
        return <XCircle className="w-5 h-5" />;
      default:
        return <Clock className="w-5 h-5" />;
    }
  };

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-1/4 mb-6"></div>
          <div className="bg-gray-200 h-64 rounded-lg mb-6"></div>
          <div className="space-y-4">
            <div className="h-4 bg-gray-200 rounded w-3/4"></div>
            <div className="h-4 bg-gray-200 rounded w-1/2"></div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6">
          <div className="flex items-center">
            <AlertCircle className="w-6 h-6 text-red-400 mr-3" />
            <div>
              <h3 className="text-lg font-medium text-red-800">Error</h3>
              <p className="text-red-700 mt-1">{error}</p>
            </div>
          </div>
          <div className="mt-4">
            <p className="text-gray-600 text-sm">Use your browser's back button to return to the previous page.</p>
          </div>
        </div>
      </div>
    );
  }

  if (!transcript) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <div className="text-center py-12">
          <FileText className="w-12 h-12 mx-auto text-gray-400 mb-4" />
          <h3 className="text-lg font-medium text-gray-900">Visit transcript not found</h3>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto p-6">
      {/* Header */}
      <div className="mb-6">
        {/* Breadcrumb Navigation */}
        {pet && (
          <Breadcrumb
            items={[
              { label: 'Pet Owners', href: '/pet_owners' },
              { label: pet.owner?.full_name || 'Owner', href: `/pet_owners/${pet.owner_id}` },
              { label: pet.display_name || pet.name, href: `/pets/${petId}` },
              { label: `${new Date(transcript.visit_date).toLocaleDateString()} Visit`, isActive: true }
            ]}
            className="mb-6"
          />
        )}
        
        <div className="flex items-center justify-end mb-4">
          <div className="flex items-center space-x-3">
            {canEdit() && (
              <Link
                to={`/pets/${petId}/visit-transcripts/${transcript.uuid}/edit`}
                className="inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-md transition-colors duration-200"
              >
                <Edit className="w-4 h-4 mr-2" />
                Edit
              </Link>
            )}
            {canDelete() && (
              <button
                onClick={() => setShowDeleteConfirm(true)}
                className="inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-red-600 hover:bg-red-700 rounded-md transition-colors duration-200"
              >
                <Trash2 className="w-4 h-4 mr-2" />
                Delete
              </button>
            )}
          </div>
        </div>

        <div className="flex items-center space-x-4 mb-4">
          <h1 className="text-2xl font-bold text-gray-900">Visit Transcript</h1>
          <div className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${TRANSCRIPT_STATE_COLORS[transcript.state]}`}>
            {getStateIcon(transcript.state)}
            <span className="ml-2">{TRANSCRIPT_STATE_LABELS[transcript.state]}</span>
          </div>
        </div>

        <div className="flex items-center space-x-6 text-sm text-gray-600">
          <div className="flex items-center space-x-2">
            <Calendar className="w-4 h-4" />
            <span>{formatDate(transcript.visit_date)}</span>
          </div>
          {transcript.created_by && (
            <div className="flex items-center space-x-2">
              <User className="w-4 h-4" />
              <span>Created by veterinarian</span>
            </div>
          )}
        </div>
      </div>

      {/* Audio Player */}
      {transcript.audio_transcript_url && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <Volume2 className="w-5 h-5 text-blue-600" />
              <span className="font-medium text-blue-900">Audio Recording</span>
            </div>
            <div className="flex items-center space-x-2">
              <button
                onClick={toggleAudio}
                disabled={audioLoading}
                className="inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 rounded-md transition-colors duration-200"
              >
                {audioLoading ? (
                  <>
                    <Clock className="w-4 h-4 mr-2 animate-spin" />
                    Loading...
                  </>
                ) : isPlaying ? (
                  <>
                    <Pause className="w-4 h-4 mr-2" />
                    Pause
                  </>
                ) : (
                  <>
                    <Play className="w-4 h-4 mr-2" />
                    Play
                  </>
                )}
              </button>
              
              <button
                onClick={downloadAudio}
                className="inline-flex items-center px-3 py-2 text-sm font-medium text-blue-600 bg-blue-100 hover:bg-blue-200 rounded-md transition-colors duration-200"
                title="Download audio file"
              >
                <Download className="w-4 h-4 mr-2" />
                Download
              </button>
              
              <button
                onClick={() => {
                  fetchDebugInfo();
                  setShowDebug(!showDebug);
                }}
                className="inline-flex items-center px-3 py-2 text-sm font-medium text-gray-600 bg-gray-100 hover:bg-gray-200 rounded-md transition-colors duration-200"
              >
                Debug
              </button>
            </div>
          </div>
          
          {/* Audio Error Display */}
          {audioError && (
            <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded-md">
              <div className="flex items-start">
                <AlertCircle className="w-4 h-4 text-red-400 mr-2 mt-0.5 flex-shrink-0" />
                <p className="text-red-700 text-sm">{audioError}</p>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Debug Information */}
      {showDebug && debugInfo && (
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 mb-6">
          <h3 className="font-medium text-gray-900 mb-3">Debug Information</h3>
          <div className="space-y-2 text-sm">
            <div><strong>Visit ID:</strong> {debugInfo.visit_id}</div>
            <div><strong>Visit State:</strong> {debugInfo.visit_state}</div>
            <div><strong>S3 Key:</strong> {debugInfo.s3_key || debugInfo.audio_s3_key || 'Not found'}</div>
            <div><strong>S3 Bucket:</strong> {debugInfo.s3_bucket}</div>
            <div><strong>Filename:</strong> {debugInfo.filename || debugInfo.audio_filename || 'Not found'}</div>
            <div><strong>Content Type:</strong> {debugInfo.content_type || 'Not found'}</div>
            <div><strong>File Exists in S3:</strong> 
              <span className={debugInfo.s3_file_exists ? 'text-green-600' : 'text-red-600'}>
                {debugInfo.s3_file_exists ? ' Yes' : ' No'}
              </span>
            </div>
            {debugInfo.s3_error && (
              <div><strong>S3 Error:</strong> <span className="text-red-600">{debugInfo.s3_error}</span></div>
            )}
            {debugInfo.s3_file_size && (
              <div><strong>File Size:</strong> {(debugInfo.s3_file_size / 1024 / 1024).toFixed(2)} MB</div>
            )}
            {debugInfo.s3_content_type && (
              <div><strong>S3 Content Type:</strong> {debugInfo.s3_content_type}</div>
            )}
            {debugInfo.s3_last_modified && (
              <div><strong>Last Modified:</strong> {new Date(debugInfo.s3_last_modified).toLocaleString()}</div>
            )}
          </div>
          <details className="mt-4">
            <summary className="cursor-pointer font-medium text-gray-700">Raw Data</summary>
            <pre className="mt-2 p-3 bg-gray-100 rounded text-xs overflow-auto">
              {JSON.stringify(debugInfo, null, 2)}
            </pre>
          </details>
        </div>
      )}

      {/* Summary */}
      {transcript.summary && (
        <div className="bg-white border border-gray-200 rounded-lg p-6 mb-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-3">Summary</h2>
          <p className="text-gray-700 leading-relaxed">{transcript.summary}</p>
        </div>
      )}

      {/* Full Transcript */}
      <div className="bg-white border border-gray-200 rounded-lg p-6 mb-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-3">Full Transcript</h2>
        <div className="prose max-w-none">
          <div className="bg-gray-50 rounded-lg p-4 border">
            <pre className="whitespace-pre-wrap text-sm text-gray-800 font-mono leading-relaxed">
              {transcript.full_text}
            </pre>
          </div>
        </div>
      </div>

      {/* Metadata */}
      {Object.keys(transcript.metadata).length > 0 && (
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-3">Additional Information</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {Object.entries(transcript.metadata).map(([key, value]) => (
              <div key={key} className="border-b border-gray-100 pb-2">
                <dt className="text-sm font-medium text-gray-500 capitalize">
                  {key.replace(/_/g, ' ')}
                </dt>
                <dd className="text-sm text-gray-900 mt-1">
                  {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                </dd>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {showDeleteConfirm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Delete Visit Transcript</h3>
            <p className="text-gray-600 mb-6">
              Are you sure you want to delete this visit transcript? This action cannot be undone.
            </p>
            <div className="flex items-center justify-end space-x-3">
              <button
                onClick={() => setShowDeleteConfirm(false)}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-md transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleDelete}
                className="px-4 py-2 text-sm font-medium text-white bg-red-600 hover:bg-red-700 rounded-md transition-colors"
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default VisitTranscriptDetail;