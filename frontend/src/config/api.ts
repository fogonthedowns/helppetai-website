/**
 * API configuration for different environments
 */

const getApiBaseUrl = (): string => {
  // Use environment variable if set
  if (process.env.REACT_APP_API_URL) {
    return process.env.REACT_APP_API_URL;
  }
  
  // In development, use localhost backend
  if (process.env.NODE_ENV === 'development') {
    return 'http://localhost:8000';
  }
  
  // In production, use api.helppet.ai
  return 'https://api.helppet.ai';
};

export const API_BASE_URL = getApiBaseUrl();

export const API_ENDPOINTS = {
  AUTH: {
    LOGIN: `${API_BASE_URL}/api/v1/auth/token`,
    SIGNUP: `${API_BASE_URL}/api/v1/auth/signup`,
    ME: `${API_BASE_URL}/api/v1/auth/me`,
  },
  RAG: {
    QUERY: `${API_BASE_URL}/api/v1/rag/query`,
  },
  PRACTICES: {
    LIST: `${API_BASE_URL}/api/v1/practices/`,
    CREATE: `${API_BASE_URL}/api/v1/practices/`,
    GET: (id: string) => `${API_BASE_URL}/api/v1/practices/${id}`,
    UPDATE: (id: string) => `${API_BASE_URL}/api/v1/practices/${id}`,
    DELETE: (id: string) => `${API_BASE_URL}/api/v1/practices/${id}`,
  },
  PET_OWNERS: {
    LIST: `${API_BASE_URL}/api/v1/pet_owners/`,
    CREATE: `${API_BASE_URL}/api/v1/pet_owners/`,
    GET: (uuid: string) => `${API_BASE_URL}/api/v1/pet_owners/${uuid}`,
    UPDATE: (uuid: string) => `${API_BASE_URL}/api/v1/pet_owners/${uuid}`,
    DELETE: (uuid: string) => `${API_BASE_URL}/api/v1/pet_owners/${uuid}`,
  },
  ASSOCIATIONS: {
    CREATE: `${API_BASE_URL}/api/v1/associations/`,
    UPDATE: (associationId: string) => `${API_BASE_URL}/api/v1/associations/${associationId}`,
    BY_PRACTICE: (practiceId: string) => `${API_BASE_URL}/api/v1/associations/practice/${practiceId}`,
    BY_PET_OWNER: (petOwnerId: string) => `${API_BASE_URL}/api/v1/associations/pet-owner/${petOwnerId}`,
    APPROVE: (associationId: string) => `${API_BASE_URL}/api/v1/associations/${associationId}/approve`,
    REJECT: (associationId: string) => `${API_BASE_URL}/api/v1/associations/${associationId}/reject`,
    DELETE: (associationId: string) => `${API_BASE_URL}/api/v1/associations/${associationId}`,
  },
  PETS: {
    LIST: `${API_BASE_URL}/api/v1/pets/`,
    CREATE: `${API_BASE_URL}/api/v1/pets/`,
    GET: (uuid: string) => `${API_BASE_URL}/api/v1/pets/${uuid}`,
    UPDATE: (uuid: string) => `${API_BASE_URL}/api/v1/pets/${uuid}`,
    DELETE: (uuid: string) => `${API_BASE_URL}/api/v1/pets/${uuid}`,
    BY_OWNER: (ownerUuid: string) => `${API_BASE_URL}/api/v1/pets/owner/${ownerUuid}`,
    REACTIVATE: (uuid: string) => `${API_BASE_URL}/api/v1/pets/${uuid}/reactivate`,
  },
  MEDICAL_RECORDS: {
    BY_PET: (petUuid: string) => `${API_BASE_URL}/api/v1/medical-records/pet/${petUuid}`,
    GET: (uuid: string) => `${API_BASE_URL}/api/v1/medical-records/${uuid}`,
    CREATE: `${API_BASE_URL}/api/v1/medical-records/`,
    UPDATE: (uuid: string) => `${API_BASE_URL}/api/v1/medical-records/${uuid}`,
    DELETE: (uuid: string) => `${API_BASE_URL}/api/v1/medical-records/${uuid}`,
    TIMELINE: (petUuid: string) => `${API_BASE_URL}/api/v1/medical-records/pet/${petUuid}/timeline`,
    HISTORY: (petUuid: string) => `${API_BASE_URL}/api/v1/medical-records/pet/${petUuid}/history`,
    FOLLOW_UPS_DUE: `${API_BASE_URL}/api/v1/medical-records/follow-ups/due`,
  },
  VISIT_TRANSCRIPTS: {
    BY_PET: (petUuid: string) => `${API_BASE_URL}/api/v1/visit-transcripts/pet/${petUuid}`,
    GET: (transcriptUuid: string) => `${API_BASE_URL}/api/v1/visit-transcripts/${transcriptUuid}`,
    CREATE: `${API_BASE_URL}/api/v1/visit-transcripts/`,
    UPDATE: (transcriptUuid: string) => `${API_BASE_URL}/api/v1/visit-transcripts/${transcriptUuid}`,
    DELETE: (transcriptUuid: string) => `${API_BASE_URL}/api/v1/visit-transcripts/${transcriptUuid}`,
  },
  APPOINTMENTS: {
    LIST_BY_PRACTICE: (practiceUuid: string) => `${API_BASE_URL}/api/v1/appointments/practice/${practiceUuid}`,
    LIST_BY_PET_OWNER: (ownerUuid: string) => `${API_BASE_URL}/api/v1/appointments/pet-owner/${ownerUuid}`,
    LIST_BY_VET: (vetUuid: string) => `${API_BASE_URL}/api/v1/appointments/vet/${vetUuid}`,
    GET: (appointmentUuid: string) => `${API_BASE_URL}/api/v1/appointments/${appointmentUuid}`,
    CREATE: `${API_BASE_URL}/api/v1/appointments`,
    UPDATE: (appointmentUuid: string) => `${API_BASE_URL}/api/v1/appointments/${appointmentUuid}`,
    CANCEL: (appointmentUuid: string) => `${API_BASE_URL}/api/v1/appointments/${appointmentUuid}`,
  },
  DASHBOARD: {
    VET_DASHBOARD: (vetUuid: string) => `${API_BASE_URL}/api/v1/dashboard/vet/${vetUuid}`,
    VET_TODAY: (vetUuid: string) => `${API_BASE_URL}/api/v1/dashboard/vet/${vetUuid}/today`,
    PENDING_VISITS: (vetUuid: string) => `${API_BASE_URL}/api/v1/visits/vet/${vetUuid}/pending`,
  },
  UPLOAD: {
    AUDIO: `${API_BASE_URL}/api/v1/upload/audio`,
    AUDIO_PRESIGNED_URL: (visitId: string) => `${API_BASE_URL}/api/v1/upload/audio/${visitId}/presigned-url`,
  }
} as const;
