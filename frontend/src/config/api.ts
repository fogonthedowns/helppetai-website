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
    LIST: `${API_BASE_URL}/api/v1/practices`,
    CREATE: `${API_BASE_URL}/api/v1/practices`,
    GET: (id: string) => `${API_BASE_URL}/api/v1/practices/${id}`,
    UPDATE: (id: string) => `${API_BASE_URL}/api/v1/practices/${id}`,
    DELETE: (id: string) => `${API_BASE_URL}/api/v1/practices/${id}`,
  }
} as const;
