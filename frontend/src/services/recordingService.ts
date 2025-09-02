/**
 * Recording Service - Uses the unified recording API (same as iPhone)
 * Maintains the same interface as the old S3 service for UI compatibility
 */

import { API_ENDPOINTS } from '../config/api';

export interface RecordingUploadRequest {
  appointment_id?: string;
  visit_id?: string;
  pet_id: string;  // CRITICAL: Now required by backend
  recording_type?: 'visit_audio';
  filename: string;
  content_type: string;
  estimated_duration_seconds?: number;
}

export interface RecordingUploadResponse {
  recording_id: string;
  upload_url: string;
  upload_fields: Record<string, string>;
  s3_key: string;
  bucket: string;
  expires_in: number;
  max_file_size: number;
}

export interface RecordingCompleteRequest {
  file_size_bytes: number;
  duration_seconds: number;
  metadata?: Record<string, any>;
}

export interface RecordingResult {
  success: boolean;
  url?: string;
  key?: string;
  error?: string;
  visitId?: string;
  recordingId?: string;
}

/**
 * Upload audio using the new unified recording API
 * Maintains same interface as old uploadAudioToS3 for UI compatibility
 */
export const uploadAudioToS3 = async (
  audioBlob: Blob,
  fileName: string,
  appointmentId?: string,
  petId?: string,
  visitId?: string
): Promise<RecordingResult> => {
  try {
    const token = localStorage.getItem('token');
    if (!token) {
      throw new Error('No authentication token found');
    }

    // Validate that petId is provided (now required by backend)
    if (!petId) {
      throw new Error('Pet ID is required for all recordings');
    }

    // Step 1: Initiate the recording upload
    const initiateRequest: RecordingUploadRequest = {
      appointment_id: appointmentId,
      visit_id: visitId,
      pet_id: petId, // CRITICAL: Include pet_id in request
      recording_type: 'visit_audio',
      filename: fileName, // This will be .mp3 filename
      content_type: audioBlob.type || 'audio/webm', // Send actual content type
      estimated_duration_seconds: undefined // We'll calculate this if needed
    };

    const initiateResponse = await fetch(API_ENDPOINTS.RECORDINGS.INITIATE, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify(initiateRequest)
    });

    if (!initiateResponse.ok) {
      const errorData = await initiateResponse.json().catch(() => ({}));
      
      // Handle the "recording already exists" case gracefully
      if (initiateResponse.status === 409) {
        throw new Error('A recording already exists for this visit. Only one recording per visit is allowed.');
      }
      
      throw new Error(`Failed to initiate upload: ${errorData.detail || initiateResponse.statusText}`);
    }

    const uploadData: RecordingUploadResponse = await initiateResponse.json();

    // Step 2: Upload directly to S3 using presigned URL
    const formData = new FormData();
    
    // Add all the required fields from the presigned URL
    Object.entries(uploadData.upload_fields).forEach(([key, value]) => {
      formData.append(key, value);
    });
    
    // Add the file last (this is important for S3)
    formData.append('file', audioBlob, fileName);

    const s3Response = await fetch(uploadData.upload_url, {
      method: 'POST',
      body: formData,
      headers: {
        // Explicitly don't send Authorization header to S3
      }
    });

    if (!s3Response.ok) {
      throw new Error(`S3 upload failed: ${s3Response.statusText}`);
    }

    // Step 3: Complete the recording upload
    const completeRequest: RecordingCompleteRequest = {
      file_size_bytes: audioBlob.size,
      duration_seconds: 0, // We don't have duration in the UI yet
      metadata: {
        browser: navigator.userAgent,
        upload_method: 'react_frontend'
      }
    };

    const completeResponse = await fetch(API_ENDPOINTS.RECORDINGS.COMPLETE(uploadData.recording_id), {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify(completeRequest)
    });

    if (!completeResponse.ok) {
      const errorData = await completeResponse.json().catch(() => ({}));
      throw new Error(`Failed to complete upload: ${errorData.detail || completeResponse.statusText}`);
    }

    const completeData = await completeResponse.json();

    // Return the same format as the old S3 service for UI compatibility
    return {
      success: true,
      url: `https://${uploadData.bucket}.s3.amazonaws.com/${uploadData.s3_key}`,
      key: uploadData.s3_key,
      recordingId: uploadData.recording_id,
      visitId: completeData.visit_id || visitId // Use the visit_id from the response if available
    };

  } catch (error) {
    console.error('Recording upload error:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Upload failed'
    };
  }
};

/**
 * Generate a unique filename for the audio recording
 * Use .mp3 extension as requested - backend will handle format conversion
 */
export const generateAudioFileName = (appointmentId?: string, userId?: string): string => {
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
  const prefix = appointmentId ? `appointment-${appointmentId}` : 'visit';
  const userSuffix = userId ? `-${userId.slice(0, 8)}` : '';
  
  return `${prefix}${userSuffix}-${timestamp}.mp3`;
};

/**
 * Check if recording service is available
 */
export const isS3Configured = (): boolean => {
  return true; // Backend handles all configuration
};

/**
 * Check if a visit already has a recording
 */
export const checkExistingRecording = async (visitId: string): Promise<boolean> => {
  try {
    const token = localStorage.getItem('token');
    if (!token) return false;

    const response = await fetch(`${API_ENDPOINTS.RECORDINGS.LIST}?visit_id=${visitId}`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });

    if (response.ok) {
      const recordings = await response.json();
      return Array.isArray(recordings) && recordings.length > 0;
    }
    
    return false;
  } catch (error) {
    console.error('Error checking existing recording:', error);
    return false;
  }
};
