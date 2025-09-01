import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Mic, Square, Play, Pause, Upload, CheckCircle, Clock, XCircle, Eye } from 'lucide-react';
import { uploadAudioToS3, generateAudioFileName } from '../../config/s3';

interface Pet {
  id: string;
  name: string;
  species: string;
  breed?: string;
}

interface Appointment {
  id: string;
  title: string;
  appointment_date: string;
  pets: Pet[];
}

interface RecordingState {
  isRecording: boolean;
  isPaused: boolean;
  duration: number;
  audioBlob: Blob | null;
  isUploading: boolean;
  uploadSuccess: boolean;
  visitId?: string;
  existingVisit?: {
    id: string;
    state: string;
    created_at: string;
  };
}

const AppointmentPetRecorder: React.FC = () => {
  const { appointmentId } = useParams<{ appointmentId: string }>();
  const navigate = useNavigate();
  
  const [appointment, setAppointment] = useState<Appointment | null>(null);
  const [selectedPetId, setSelectedPetId] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>('');
  
  // Recording states for each pet
  const [recordings, setRecordings] = useState<Record<string, RecordingState>>({});
  const [mediaRecorder, setMediaRecorder] = useState<MediaRecorder | null>(null);
  const [currentRecordingPet, setCurrentRecordingPet] = useState<string>('');

  useEffect(() => {
    if (appointmentId) {
      fetchAppointmentDetails();
    }
  }, [appointmentId]);

  const fetchAppointmentDetails = async () => {
    try {
      const response = await fetch(`http://localhost:8000/api/v1/appointments/${appointmentId}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setAppointment(data);
        
        // Initialize recording states for each pet and check for existing visits
        const initialRecordings: Record<string, RecordingState> = {};
        
        for (const pet of data.pets) {
          // Check for existing visit for this pet and appointment
          const existingVisit = await checkExistingVisit(pet.id);
          
          initialRecordings[pet.id] = {
            isRecording: false,
            isPaused: false,
            duration: 0,
            audioBlob: null,
            isUploading: false,
            uploadSuccess: false,
            existingVisit: existingVisit || undefined
          };
        }
        
        setRecordings(initialRecordings);
        
        if (data.pets.length > 0) {
          setSelectedPetId(data.pets[0].id);
        }
      } else {
        setError('Failed to load appointment details');
      }
    } catch (err) {
      setError('Error loading appointment');
    } finally {
      setLoading(false);
    }
  };

  const checkExistingVisit = async (petId: string) => {
    try {
      // Get all visits for this pet and check if any match this appointment
      const response = await fetch(`http://localhost:8000/api/v1/visit-transcripts/pet/${petId}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (response.ok) {
        const visits = await response.json(); // This is directly an array
        console.log(`Checking visits for pet ${petId}:`, visits);
        
        // Find visit that matches this appointment
        const existingVisit = visits.find((visit: any) => 
          visit.metadata?.appointment_id === appointmentId
        );
        
        console.log(`Found existing visit for appointment ${appointmentId}:`, existingVisit);
        
        if (existingVisit) {
          return {
            id: existingVisit.uuid,
            state: existingVisit.state,
            created_at: existingVisit.created_at
          };
        }
      } else {
        console.log(`Failed to fetch visits for pet ${petId}:`, response.status, response.statusText);
      }
    } catch (err) {
      console.error('Error checking existing visit:', err);
    }
    return null;
  };

  const startRecording = async (petId: string) => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      const chunks: Blob[] = [];

      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunks.push(event.data);
        }
      };

      recorder.onstop = () => {
        const audioBlob = new Blob(chunks, { type: 'audio/webm' });
        setRecordings(prev => ({
          ...prev,
          [petId]: {
            ...prev[petId],
            audioBlob,
            isRecording: false,
            isPaused: false
          }
        }));
        
        // Stop all tracks to release microphone
        stream.getTracks().forEach(track => track.stop());
      };

      recorder.start();
      setMediaRecorder(recorder);
      setCurrentRecordingPet(petId);
      
      setRecordings(prev => ({
        ...prev,
        [petId]: {
          ...prev[petId],
          isRecording: true,
          isPaused: false,
          duration: 0
        }
      }));

      // Start duration timer
      const startTime = Date.now();
      const timer = setInterval(() => {
        setRecordings(prev => ({
          ...prev,
          [petId]: {
            ...prev[petId],
            duration: Math.floor((Date.now() - startTime) / 1000)
          }
        }));
      }, 1000);

      // Store timer reference
      (recorder as any).timer = timer;

    } catch (err) {
      console.error('Error starting recording:', err);
      setError('Failed to start recording. Please check microphone permissions.');
    }
  };

  const stopRecording = (petId: string) => {
    if (mediaRecorder && currentRecordingPet === petId) {
      mediaRecorder.stop();
      clearInterval((mediaRecorder as any).timer);
      setMediaRecorder(null);
      setCurrentRecordingPet('');
    }
  };

  const uploadRecording = async (petId: string) => {
    const recording = recordings[petId];
    if (!recording.audioBlob || !appointmentId) return;

    setRecordings(prev => ({
      ...prev,
      [petId]: { ...prev[petId], isUploading: true }
    }));

    try {
      const fileName = generateAudioFileName(appointmentId, petId);
      const result = await uploadAudioToS3(recording.audioBlob, fileName, appointmentId, petId);

      if (result.success) {
        setRecordings(prev => ({
          ...prev,
          [petId]: {
            ...prev[petId],
            isUploading: false,
            uploadSuccess: true,
            visitId: result.visitId
          }
        }));
      } else {
        throw new Error(result.error || 'Upload failed');
      }
    } catch (err) {
      console.error('Upload error:', err);
      setRecordings(prev => ({
        ...prev,
        [petId]: { ...prev[petId], isUploading: false }
      }));
      setError(`Upload failed: ${err instanceof Error ? err.message : 'Unknown error'}`);
    }
  };

  const formatDuration = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading appointment details...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-600 mb-4">{error}</p>
          <p className="text-gray-600">Use your browser's back button to return to the previous page.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto py-8 px-4">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Visit Recording</h1>
          <p className="text-gray-600 mt-2">
            {appointment?.title} - {new Date(appointment?.appointment_date || '').toLocaleString()}
          </p>
        </div>

        {/* Pet Recording Cards */}
        <div className="space-y-6">
          {appointment?.pets.map((pet) => {
            const recording = recordings[pet.id];
            return (
              <div key={pet.id} className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <h3 className="text-xl font-semibold text-gray-900">{pet.name}</h3>
                    <p className="text-gray-600">{pet.species} {pet.breed && `• ${pet.breed}`}</p>
                  </div>
                  
                  {recording.uploadSuccess && (
                    <div className="flex items-center text-green-600">
                      <CheckCircle className="w-5 h-5 mr-2" />
                      <span className="text-sm font-medium">Recording Complete</span>
                    </div>
                  )}
                </div>

                {/* Recording Controls */}
                <div className="flex items-center space-x-4">
                  {recording.existingVisit ? (
                    // Show existing recording status
                    <div className="w-full">
                      <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-4">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center space-x-3">
                            <div className={`inline-flex items-center px-3 py-1 text-sm font-medium rounded-full ${
                              recording.existingVisit.state === 'processed' ? 'bg-green-100 text-green-800' :
                              recording.existingVisit.state === 'processing' ? 'bg-blue-100 text-blue-800' :
                              recording.existingVisit.state === 'failed' ? 'bg-red-100 text-red-800' :
                              'bg-gray-100 text-gray-800'
                            }`}>
                              {recording.existingVisit.state === 'processed' && <CheckCircle className="w-4 h-4 mr-1" />}
                              {recording.existingVisit.state === 'processing' && <Clock className="w-4 h-4 mr-1 animate-spin" />}
                              {recording.existingVisit.state === 'failed' && <XCircle className="w-4 h-4 mr-1" />}
                              {recording.existingVisit.state === 'new' && <Clock className="w-4 h-4 mr-1" />}
                              Recording {recording.existingVisit.state.charAt(0).toUpperCase() + recording.existingVisit.state.slice(1)}
                            </div>
                            <span className="text-sm text-gray-600">
                              {new Date(recording.existingVisit.created_at).toLocaleString()}
                            </span>
                          </div>
                          
                          <button
                            onClick={() => navigate(`/pets/${pet.id}/visit-transcripts/${recording.existingVisit!.id}`)}
                            className="flex items-center bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition-colors"
                          >
                            <Eye className="w-5 h-5 mr-2" />
                            View Recording
                          </button>
                        </div>
                        <p className="text-sm text-green-700 mt-2">
                          ✅ This pet has already been recorded for this appointment.
                        </p>
                      </div>
                    </div>
                  ) : (
                    // Show recording controls for new recordings
                    <>
                      {!recording.isRecording && !recording.audioBlob && (
                        <button
                          onClick={() => startRecording(pet.id)}
                          className="flex items-center bg-red-600 text-white px-4 py-2 rounded-md hover:bg-red-700 transition-colors"
                        >
                          <Mic className="w-5 h-5 mr-2" />
                          Start Recording
                        </button>
                      )}

                      {recording.isRecording && (
                        <>
                          <button
                            onClick={() => stopRecording(pet.id)}
                            className="flex items-center bg-gray-600 text-white px-4 py-2 rounded-md hover:bg-gray-700 transition-colors"
                          >
                            <Square className="w-5 h-5 mr-2" />
                            Stop Recording
                          </button>
                          <div className="flex items-center text-red-600">
                            <div className="w-3 h-3 bg-red-600 rounded-full animate-pulse mr-2"></div>
                            <span className="font-mono text-lg">{formatDuration(recording.duration)}</span>
                          </div>
                        </>
                      )}

                      {recording.audioBlob && !recording.uploadSuccess && (
                        <button
                          onClick={() => uploadRecording(pet.id)}
                          disabled={recording.isUploading}
                          className="flex items-center bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 disabled:opacity-50 transition-colors"
                        >
                          <Upload className="w-5 h-5 mr-2" />
                          {recording.isUploading ? 'Uploading...' : 'Upload Recording'}
                        </button>
                      )}

                      {recording.audioBlob && (
                        <div className="text-sm text-gray-600">
                          Duration: {formatDuration(recording.duration)}
                        </div>
                      )}
                    </>
                  )}
                </div>

                {/* Status Messages */}
                {recording.isUploading && (
                  <div className="mt-4 text-blue-600 text-sm">
                    Uploading recording to secure storage...
                  </div>
                )}

                {recording.uploadSuccess && recording.visitId && (
                  <div className="mt-4 text-green-600 text-sm">
                    ✓ Visit record created successfully (ID: {recording.visitId})
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* Debug Info */}
        <div className="mt-8 bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <h4 className="font-medium text-yellow-900 mb-2">Debug Info</h4>
          <p className="text-yellow-800 text-sm mb-2">Appointment ID: {appointmentId}</p>
          <button
            onClick={() => {
              setLoading(true);
              fetchAppointmentDetails();
            }}
            className="bg-yellow-600 text-white px-3 py-1 rounded text-sm hover:bg-yellow-700"
          >
            Refresh & Check Again
          </button>
          <div className="mt-2 text-xs text-yellow-700">
            {Object.entries(recordings).map(([petId, recording]) => (
              <div key={petId}>
                Pet {petId}: {recording.existingVisit ? `Has existing visit ${recording.existingVisit.id}` : 'No existing visit'}
              </div>
            ))}
          </div>
        </div>

        {/* Summary */}
        {appointment?.pets && (
          <div className="mt-8 bg-blue-50 border border-blue-200 rounded-lg p-4">
            <h4 className="font-medium text-blue-900 mb-2">Recording Progress</h4>
            <p className="text-blue-800 text-sm">
              {Object.values(recordings).filter(r => r.uploadSuccess || r.existingVisit).length} of {appointment.pets.length} pets recorded
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default AppointmentPetRecorder;
