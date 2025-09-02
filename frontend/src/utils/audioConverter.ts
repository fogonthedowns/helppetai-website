/**
 * Audio Format Converter Utility
 * Handles conversion between WebM and M4A formats for cross-platform compatibility
 */

// Option 1: Simple format detection and handling
export interface AudioConversionResult {
  blob: Blob;
  filename: string;
  format: 'webm' | 'm4a' | 'unknown';
  converted: boolean;
}

/**
 * Detect audio format from blob
 */
export const detectAudioFormat = (blob: Blob): 'webm' | 'm4a' | 'unknown' => {
  if (blob.type.includes('webm')) return 'webm';
  if (blob.type.includes('m4a') || blob.type.includes('mp4')) return 'm4a';
  return 'unknown';
};

/**
 * Convert WebM to M4A using MediaRecorder with different options
 * This is a fallback approach that tries different recording formats
 */
export const getOptimalRecordingOptions = (): MediaRecorderOptions[] => {
  const options: MediaRecorderOptions[] = [];
  
  // Try M4A first (if supported)
  if (MediaRecorder.isTypeSupported('audio/mp4')) {
    options.push({ mimeType: 'audio/mp4' });
  }
  
  // Try AAC in MP4 container
  if (MediaRecorder.isTypeSupported('audio/mp4;codecs=mp4a.40.2')) {
    options.push({ mimeType: 'audio/mp4;codecs=mp4a.40.2' });
  }
  
  // Fallback to WebM with Opus
  if (MediaRecorder.isTypeSupported('audio/webm;codecs=opus')) {
    options.push({ mimeType: 'audio/webm;codecs=opus' });
  }
  
  // Last resort - default WebM
  options.push({ mimeType: 'audio/webm' });
  
  return options;
};

/**
 * Create MediaRecorder with the best available format
 */
export const createOptimalMediaRecorder = (stream: MediaStream): MediaRecorder => {
  const options = getOptimalRecordingOptions();
  
  for (const option of options) {
    try {
      return new MediaRecorder(stream, option);
    } catch (error) {
      console.warn(`Failed to create MediaRecorder with ${option.mimeType}:`, error);
      continue;
    }
  }
  
  // Fallback without options
  return new MediaRecorder(stream);
};

/**
 * Generate appropriate filename based on format
 */
export const generateAudioFileName = (
  format: 'webm' | 'm4a' | 'unknown',
  appointmentId?: string,
  userId?: string
): string => {
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
  const prefix = appointmentId ? `appointment-${appointmentId}` : 'visit';
  const userSuffix = userId ? `-${userId.slice(0, 8)}` : '';
  
  const extension = format === 'm4a' ? 'm4a' : 'webm';
  return `${prefix}${userSuffix}-${timestamp}.${extension}`;
};

/**
 * Prepare audio for upload - handles format detection and naming
 */
export const prepareAudioForUpload = (
  audioBlob: Blob,
  appointmentId?: string,
  userId?: string
): AudioConversionResult => {
  const format = detectAudioFormat(audioBlob);
  const filename = generateAudioFileName(format, appointmentId, userId);
  
  return {
    blob: audioBlob,
    filename,
    format,
    converted: false
  };
};

// Advanced Option: FFmpeg.wasm conversion (for future implementation)
export const isFFmpegAvailable = (): boolean => {
  return typeof window !== 'undefined' && 'SharedArrayBuffer' in window;
};

/**
 * Convert WebM to M4A using FFmpeg.wasm (requires additional setup)
 * This is a placeholder for future implementation
 */
export const convertWebMToM4A = async (webmBlob: Blob): Promise<Blob> => {
  // TODO: Implement FFmpeg.wasm conversion
  // For now, return original blob
  console.warn('FFmpeg.wasm conversion not implemented yet');
  return webmBlob;
};
