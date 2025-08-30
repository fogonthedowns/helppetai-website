/**
 * API configuration for different environments
 */

const getApiBaseUrl = (): string => {
  // In development, use explicit backend URL
  if (process.env.NODE_ENV === 'development') {
    return process.env.REACT_APP_API_URL || 'http://localhost:8000';
  }
  
  // In production, assume same domain with different port or path
  // You can customize this based on your deployment setup
  return process.env.REACT_APP_API_URL || '';
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
  }
} as const;
