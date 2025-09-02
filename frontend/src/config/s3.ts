/**
 * Audio Upload Configuration - Uses Backend API for Security
 * No AWS credentials stored in frontend!
 */

import { API_ENDPOINTS } from './api';

export interface S3UploadResult {
  success: boolean;
  url?: string;
  key?: string;
  error?: string;
}

/**
 * Upload audio file via backend API (secure)
 * Backend handles all S3 credentials and uploads
 * @param audioBlob The audio blob to upload
 * @param fileName The filename for the upload
 * @param appointmentId Optional appointment ID for organization
 * @returns Promise<S3UploadResult>
 */
export const uploadAudioToS3 = async (
  audioBlob: Blob,
  fileName: string,
  appointmentId?: string,
  petId?: string
): Promise<S3UploadResult & { visitId?: string }> => {
  try {
    // Create FormData for the upload
    const formData = new FormData();
    formData.append('audio', audioBlob, fileName);
    
    if (appointmentId) {
      formData.append('appointment_id', appointmentId);
    }
    
    if (petId) {
      formData.append('pet_id', petId);
    }

    // Upload to backend endpoint that handles S3 upload securely
    const response = await fetch(API_ENDPOINTS.UPLOAD.AUDIO, {
      method: 'POST',
      body: formData,
      headers: {
        // Don't set Content-Type - let browser set it for FormData
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      }
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(`Upload failed: ${response.statusText} - ${errorData.message || ''}`);
    }

    const result = await response.json();
    
    return {
      success: true,
      url: result.url,
      key: result.key,
      visitId: result.visit_created?.visit_id
    };

  } catch (error) {
    console.error('Audio upload error:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Upload failed'
    };
  }
};

/**
 * Generate a unique filename for the audio recording
 * @param appointmentId Optional appointment ID
 * @param userId User ID
 * @returns Unique filename
 */
export const generateAudioFileName = (appointmentId?: string, userId?: string): string => {
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
  const prefix = appointmentId ? `appointment-${appointmentId}` : 'visit';
  const userSuffix = userId ? `-${userId.slice(0, 8)}` : '';
  
  return `${prefix}${userSuffix}-${timestamp}.webm`;
};

/**
 * Check if backend upload is available
 * @returns boolean indicating if upload service is configured
 */
export const isS3Configured = (): boolean => {
  // Always return true since backend handles S3 configuration
  // The backend will return appropriate errors if not configured
  return true;
};