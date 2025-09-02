/**
 * PetRecordingsList - Example component showing how to filter recordings by pet
 * This demonstrates the fix for the iOS team's issue
 */

import React from 'react';
import { Play, Clock, CheckCircle, XCircle } from 'lucide-react';
import { Appointment, RecordingSummary } from '../../types/appointment';

interface PetRecordingsListProps {
  appointment: Appointment;
  selectedPetId: string;
}

export const PetRecordingsList: React.FC<PetRecordingsListProps> = ({
  appointment,
  selectedPetId
}) => {
  
  // ✅ THIS IS THE FIX! - Filter recordings by specific pet
  const petRecordings = appointment.recordings.filter(recording => 
    recording.pet_id === selectedPetId
  );

  const selectedPet = appointment.pets.find(pet => pet.id === selectedPetId);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'transcribed':
        return <CheckCircle className="w-4 h-4 text-green-600" />;
      case 'uploading':
        return <Clock className="w-4 h-4 text-yellow-600 animate-spin" />;
      case 'failed':
        return <XCircle className="w-4 h-4 text-red-600" />;
      default:
        return <Clock className="w-4 h-4 text-blue-600" />;
    }
  };

  const formatDuration = (seconds?: number): string => {
    if (!seconds) return '--:--';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const formatDate = (dateString: string): string => {
    return new Date(dateString).toLocaleString();
  };

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">
          Recordings for {selectedPet?.name}
        </h3>
        <span className="text-sm text-gray-500">
          {petRecordings.length} recording{petRecordings.length !== 1 ? 's' : ''}
        </span>
      </div>

      {petRecordings.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          <div className="text-gray-400 mb-2">
            <Play className="w-12 h-12 mx-auto" />
          </div>
          <p>No recordings found for {selectedPet?.name}</p>
          <p className="text-sm">Start a new recording above</p>
        </div>
      ) : (
        <div className="space-y-3">
          {petRecordings.map((recording) => (
            <div 
              key={recording.id}
              className="flex items-center justify-between p-3 bg-gray-50 rounded-lg border"
            >
              <div className="flex items-center space-x-3">
                {getStatusIcon(recording.status)}
                <div>
                  <div className="font-medium text-gray-900">
                    Recording #{recording.id.slice(-8)}
                  </div>
                  <div className="text-sm text-gray-500">
                    {formatDate(recording.created_at)}
                  </div>
                </div>
              </div>
              
              <div className="flex items-center space-x-4">
                <div className="text-right">
                  <div className="text-sm font-medium text-gray-900">
                    {formatDuration(recording.duration_seconds)}
                  </div>
                  <div className="text-xs text-gray-500 capitalize">
                    {recording.status}
                  </div>
                </div>
                
                {recording.status === 'transcribed' && (
                  <button className="p-2 text-blue-600 hover:bg-blue-50 rounded-full transition-colors">
                    <Play className="w-4 h-4" />
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Example of showing ALL recordings for debugging */}
      <details className="mt-4">
        <summary className="text-sm text-gray-500 cursor-pointer hover:text-gray-700">
          Debug: Show all appointment recordings ({appointment.recordings.length})
        </summary>
        <div className="mt-2 text-xs text-gray-600 bg-gray-100 p-2 rounded">
          {appointment.recordings.map(recording => (
            <div key={recording.id} className="mb-1">
              Recording {recording.id.slice(-8)} → Pet {recording.pet_id.slice(-8)} ({recording.status})
            </div>
          ))}
        </div>
      </details>
    </div>
  );
};

export default PetRecordingsList;
