import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Mic, Square, Play, Pause, Upload, CheckCircle } from 'lucide-react';
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
        
        // Initialize recording states for each pet
        const initialRecordings: Record<string, RecordingState> = {};
        data.pets.forEach((pet: Pet) => {
          initialRecordings[pet.id] = {
            isRecording: false,
            isPaused: false,
            duration: 0,
            audioBlob: null,
            isUploading: false,
            uploadSuccess: false
          };
        });
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
          <button
            onClick={() => navigate('/dashboard/vet')}
            className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700"
          >
            Back to Dashboard
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto py-8 px-4">
        {/* Header */}
        <div className="mb-8">
          <button
            onClick={() => navigate('/dashboard/vet')}
            className="flex items-center text-gray-600 hover:text-gray-900 mb-4"
          >
            <ArrowLeft className="w-5 h-5 mr-2" />
            Back to Dashboard
          </button>
          
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

        {/* Summary */}
        {appointment?.pets && (
          <div className="mt-8 bg-blue-50 border border-blue-200 rounded-lg p-4">
            <h4 className="font-medium text-blue-900 mb-2">Recording Progress</h4>
            <p className="text-blue-800 text-sm">
              {Object.values(recordings).filter(r => r.uploadSuccess).length} of {appointment.pets.length} pets recorded
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default AppointmentPetRecorder;
