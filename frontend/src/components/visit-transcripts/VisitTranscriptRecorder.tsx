import React, { useState, useRef, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { uploadAudioToS3, isS3Configured } from '../../config/s3';
import { createOptimalMediaRecorder, prepareAudioForUpload } from '../../utils/audioConverter';
import { Mic, MicOff, Square, Play, Pause, Upload, Check, AlertCircle, ArrowLeft, Clock, CheckCircle, XCircle } from 'lucide-react';
import { VisitTranscript, TranscriptState, TRANSCRIPT_STATE_LABELS, TRANSCRIPT_STATE_COLORS } from '../../types/visitTranscript';
import { API_ENDPOINTS } from '../../config/api';

interface RecordingState {
  isRecording: boolean;
  isPaused: boolean;
  isFinished: boolean;
  duration: number;
  audioBlob: Blob | null;
  localStorageKey: string | null;
  uploadStatus: 'idle' | 'uploading' | 'success' | 'error';
  uploadError?: string;
}

export const VisitTranscriptRecorder: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const { appointmentId, visitId } = useParams<{ appointmentId?: string; visitId?: string }>();
  
  const [recordingState, setRecordingState] = useState<RecordingState>({
    isRecording: false,
    isPaused: false,
    isFinished: false,
    duration: 0,
    audioBlob: null,
    localStorageKey: null,
    uploadStatus: 'idle'
  });

  const [visitTranscript, setVisitTranscript] = useState<VisitTranscript | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<NodeJS.Timeout | null>(null);
  const streamRef = useRef<MediaStream | null>(null);

  useEffect(() => {
    if (visitId) {
      fetchVisitTranscript();
    }
    
    // Cleanup on unmount
    return () => {
      stopRecording();
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
      }
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    };
  }, [visitId]);

  const fetchVisitTranscript = async () => {
    if (!visitId) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(API_ENDPOINTS.VISIT_TRANSCRIPTS.GET(visitId));
      
      if (!response.ok) {
        throw new Error('Failed to fetch visit transcript');
      }
      
      const transcript: VisitTranscript = await response.json();
      setVisitTranscript(transcript);
    } catch (err) {
      console.error('Error fetching visit transcript:', err);
      setError(err instanceof Error ? err.message : 'Failed to fetch visit transcript');
    } finally {
      setLoading(false);
    }
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          sampleRate: 44100
        } 
      });
      
      streamRef.current = stream;
      
      const mediaRecorder = createOptimalMediaRecorder(stream);
      
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: mediaRecorder.mimeType });
        const localKey = saveToLocalStorage(audioBlob);
        
        setRecordingState(prev => ({
          ...prev,
          audioBlob,
          localStorageKey: localKey,
          isFinished: true,
          isRecording: false
        }));
      };

      mediaRecorder.start(1000); // Collect data every second
      
      setRecordingState(prev => ({
        ...prev,
        isRecording: true,
        isPaused: false,
        duration: 0
      }));

      // Start timer
      timerRef.current = setInterval(() => {
        setRecordingState(prev => ({
          ...prev,
          duration: prev.duration + 1
        }));
      }, 1000);

    } catch (error) {
      console.error('Error starting recording:', error);
      alert('Could not access microphone. Please check permissions.');
    }
  };

  const pauseRecording = () => {
    if (mediaRecorderRef.current && recordingState.isRecording) {
      mediaRecorderRef.current.pause();
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
      
      setRecordingState(prev => ({
        ...prev,
        isPaused: true
      }));
    }
  };

  const resumeRecording = () => {
    if (mediaRecorderRef.current && recordingState.isPaused) {
      mediaRecorderRef.current.resume();
      
      // Resume timer
      timerRef.current = setInterval(() => {
        setRecordingState(prev => ({
          ...prev,
          duration: prev.duration + 1
        }));
      }, 1000);
      
      setRecordingState(prev => ({
        ...prev,
        isPaused: false
      }));
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && recordingState.isRecording) {
      mediaRecorderRef.current.stop();
      
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
      
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
      }
    }
  };

  const saveToLocalStorage = (audioBlob: Blob): string => {
    const timestamp = new Date().toISOString();
    const key = `visit_recording_${appointmentId || 'new'}_${timestamp}`;
    
    // Convert blob to base64 for localStorage
    const reader = new FileReader();
    reader.onload = () => {
      const base64Data = reader.result as string;
      localStorage.setItem(key, JSON.stringify({
        data: base64Data,
        timestamp,
        appointmentId: appointmentId || null,
        userId: user?.id,
        uploaded: false
      }));
    };
    reader.readAsDataURL(audioBlob);
    
    return key;
  };

  const uploadToS3 = async () => {
    if (!recordingState.audioBlob || !recordingState.localStorageKey) return;

    setRecordingState(prev => ({ ...prev, uploadStatus: 'uploading' }));

    try {
      // Check if S3 is configured
      if (!isS3Configured()) {
        throw new Error('S3 not configured. Check environment variables.');
      }

      // Prepare audio with optimal format and filename
      const audioData = prepareAudioForUpload(recordingState.audioBlob, appointmentId, user?.id);
      
      // Upload to S3
      const uploadResult = await uploadAudioToS3(audioData.blob, audioData.filename);
      
      if (!uploadResult.success) {
        throw new Error(uploadResult.error || 'Upload failed');
      }

      // Mark as uploaded in localStorage
      const storedData = localStorage.getItem(recordingState.localStorageKey);
      if (storedData) {
        const data = JSON.parse(storedData);
        data.uploaded = true;
        data.s3Url = uploadResult.url;
        data.s3Key = uploadResult.key;
        localStorage.setItem(recordingState.localStorageKey, JSON.stringify(data));
      }

      setRecordingState(prev => ({ 
        ...prev, 
        uploadStatus: 'success' 
      }));

      // Auto-navigate back after successful upload
      setTimeout(() => {
        navigate('/dashboard/vet');
      }, 2000);

    } catch (error) {
      console.error('Upload failed:', error);
      setRecordingState(prev => ({ 
        ...prev, 
        uploadStatus: 'error',
        uploadError: error instanceof Error ? error.message : 'Upload failed. Recording saved locally.'
      }));
    }
  };

  const formatDuration = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const getStatusIcon = (state: TranscriptState) => {
    switch (state) {
      case TranscriptState.NEW:
        return <Clock className="w-4 h-4" />;
      case TranscriptState.PROCESSING:
        return <Clock className="w-4 h-4 animate-spin" />;
      case TranscriptState.PROCESSED:
        return <CheckCircle className="w-4 h-4" />;
      case TranscriptState.FAILED:
        return <XCircle className="w-4 h-4" />;
      default:
        return <Clock className="w-4 h-4" />;
    }
  };

  const getRecordingStatusColor = () => {
    if (recordingState.isRecording && !recordingState.isPaused) return 'text-red-600';
    if (recordingState.isPaused) return 'text-yellow-600';
    if (recordingState.isFinished) return 'text-green-600';
    return 'text-gray-600';
  };

  const getRecordingStatusText = () => {
    if (recordingState.isRecording && !recordingState.isPaused) return 'Recording...';
    if (recordingState.isPaused) return 'Paused';
    if (recordingState.isFinished) return 'Recording Complete';
    return 'Ready to Record';
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-4xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <button
                onClick={() => navigate('/dashboard/vet')}
                className="mr-4 p-2 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <ArrowLeft className="w-5 h-5 text-gray-600" />
              </button>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">Visit Recording</h1>
                <p className="text-gray-600">
                  {appointmentId ? `Appointment: ${appointmentId.slice(0, 8)}...` : 'New Visit Recording'}
                </p>
                {visitTranscript && (
                  <div className="flex items-center mt-2">
                    <span className={`inline-flex items-center px-2 py-1 text-xs font-medium rounded-full ${TRANSCRIPT_STATE_COLORS[visitTranscript.state]}`}>
                      {getStatusIcon(visitTranscript.state)}
                      <span className="ml-1">{TRANSCRIPT_STATE_LABELS[visitTranscript.state]}</span>
                    </span>
                  </div>
                )}
              </div>
            </div>
            <div className="text-right">
              <div className={`text-sm font-medium ${getRecordingStatusColor()}`}>
                {getRecordingStatusText()}
              </div>
              <div className="text-2xl font-mono font-bold text-gray-900">
                {formatDuration(recordingState.duration)}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-4xl mx-auto px-6 py-8">
        {/* Visit Status Card */}
        {visitTranscript && (
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 mb-6">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-lg font-semibold text-gray-900 mb-2">Recording Status</h2>
                <div className="flex items-center space-x-4">
                  <span className={`inline-flex items-center px-3 py-1 text-sm font-medium rounded-full ${TRANSCRIPT_STATE_COLORS[visitTranscript.state]}`}>
                    {getStatusIcon(visitTranscript.state)}
                    <span className="ml-2">{TRANSCRIPT_STATE_LABELS[visitTranscript.state]}</span>
                  </span>
                  <span className="text-sm text-gray-600">
                    Created: {new Date(visitTranscript.created_at).toLocaleString()}
                  </span>
                </div>
              </div>
              
              {visitTranscript.state === TranscriptState.PROCESSED && (
                <div className="text-right">
                  <div className="text-sm text-gray-600 mb-1">Recording Complete</div>
                  <button
                    onClick={() => navigate(`/visit-transcripts/${visitTranscript.uuid}`)}
                    className="inline-flex items-center px-4 py-2 bg-green-600 text-white text-sm font-medium rounded-lg hover:bg-green-700 transition-colors"
                  >
                    <CheckCircle className="w-4 h-4 mr-2" />
                    View Transcript
                  </button>
                </div>
              )}
              
              {visitTranscript.state === TranscriptState.PROCESSING && (
                <div className="text-right">
                  <div className="text-sm text-gray-600 mb-1">Processing...</div>
                  <button
                    onClick={fetchVisitTranscript}
                    className="inline-flex items-center px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors"
                  >
                    <Clock className="w-4 h-4 mr-2" />
                    Refresh Status
                  </button>
                </div>
              )}
              
              {visitTranscript.state === TranscriptState.FAILED && (
                <div className="text-right">
                  <div className="text-sm text-red-600 mb-1">Processing Failed</div>
                  <button
                    onClick={fetchVisitTranscript}
                    className="inline-flex items-center px-4 py-2 bg-red-600 text-white text-sm font-medium rounded-lg hover:bg-red-700 transition-colors"
                  >
                    <XCircle className="w-4 h-4 mr-2" />
                    Retry
                  </button>
                </div>
              )}
            </div>
          </div>
        )}

        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8">
          
          {/* Recording Visualization */}
          <div className="text-center mb-8">
            <div className={`inline-flex items-center justify-center w-32 h-32 rounded-full border-4 mb-4 ${
              recordingState.isRecording && !recordingState.isPaused 
                ? 'border-red-500 bg-red-50 animate-pulse' 
                : recordingState.isPaused
                ? 'border-yellow-500 bg-yellow-50'
                : recordingState.isFinished
                ? 'border-green-500 bg-green-50'
                : 'border-gray-300 bg-gray-50'
            }`}>
              {recordingState.isRecording && !recordingState.isPaused ? (
                <Mic className="w-16 h-16 text-red-600" />
              ) : recordingState.isPaused ? (
                <Pause className="w-16 h-16 text-yellow-600" />
              ) : recordingState.isFinished ? (
                <Check className="w-16 h-16 text-green-600" />
              ) : (
                <MicOff className="w-16 h-16 text-gray-400" />
              )}
            </div>
            
            <div className="text-4xl font-mono font-bold text-gray-900 mb-2">
              {formatDuration(recordingState.duration)}
            </div>
            <div className={`text-lg font-medium ${getRecordingStatusColor()}`}>
              {getRecordingStatusText()}
            </div>
          </div>

          {/* Recording Controls */}
          <div className="flex justify-center space-x-4 mb-8">
            {!recordingState.isRecording && !recordingState.isFinished && (
              <button
                onClick={startRecording}
                className="flex items-center px-6 py-3 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors font-medium"
              >
                <Mic className="w-5 h-5 mr-2" />
                Start Recording
              </button>
            )}

            {recordingState.isRecording && !recordingState.isPaused && (
              <>
                <button
                  onClick={pauseRecording}
                  className="flex items-center px-6 py-3 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700 transition-colors font-medium"
                >
                  <Pause className="w-5 h-5 mr-2" />
                  Pause
                </button>
                <button
                  onClick={stopRecording}
                  className="flex items-center px-6 py-3 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors font-medium"
                >
                  <Square className="w-5 h-5 mr-2" />
                  Finish
                </button>
              </>
            )}

            {recordingState.isPaused && (
              <>
                <button
                  onClick={resumeRecording}
                  className="flex items-center px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors font-medium"
                >
                  <Play className="w-5 h-5 mr-2" />
                  Resume
                </button>
                <button
                  onClick={stopRecording}
                  className="flex items-center px-6 py-3 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors font-medium"
                >
                  <Square className="w-5 h-5 mr-2" />
                  Finish
                </button>
              </>
            )}
          </div>

          {/* Upload Section */}
          {recordingState.isFinished && (
            <div className="border-t pt-6">
              <div className="text-center">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Recording Complete</h3>
                
                {recordingState.uploadStatus === 'idle' && (
                  <div>
                    <p className="text-gray-600 mb-4">
                      Recording saved locally. Click upload to sync to cloud storage.
                    </p>
                    <button
                      onClick={uploadToS3}
                      className="flex items-center px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium mx-auto"
                    >
                      <Upload className="w-5 h-5 mr-2" />
                      Upload Recording
                    </button>
                  </div>
                )}

                {recordingState.uploadStatus === 'uploading' && (
                  <div className="flex items-center justify-center">
                    <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600 mr-3"></div>
                    <span className="text-blue-600 font-medium">Uploading...</span>
                  </div>
                )}

                {recordingState.uploadStatus === 'success' && (
                  <div className="flex items-center justify-center text-green-600">
                    <Check className="w-6 h-6 mr-2" />
                    <span className="font-medium">Upload Complete! Redirecting...</span>
                  </div>
                )}

                {recordingState.uploadStatus === 'error' && (
                  <div>
                    <div className="flex items-center justify-center text-red-600 mb-4">
                      <AlertCircle className="w-6 h-6 mr-2" />
                      <span className="font-medium">{recordingState.uploadError}</span>
                    </div>
                    <button
                      onClick={uploadToS3}
                      className="flex items-center px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium mx-auto"
                    >
                      <Upload className="w-5 h-5 mr-2" />
                      Retry Upload
                    </button>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Instructions */}
          {!recordingState.isRecording && !recordingState.isFinished && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mt-6">
              <h4 className="font-medium text-blue-900 mb-2">Recording Instructions:</h4>
              <ul className="text-sm text-blue-800 space-y-1">
                <li>• Click "Start Recording" to begin capturing audio</li>
                <li>• Use "Pause" to temporarily stop recording</li>
                <li>• Click "Finish" when the visit is complete</li>
                <li>• Recordings are saved locally and uploaded to secure cloud storage</li>
                <li>• You can record offline - uploads will sync when internet is available</li>
              </ul>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default VisitTranscriptRecorder;
