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
    LOGIN: `${API_BASE_URL}/auth/token`,
    SIGNUP: `${API_BASE_URL}/auth/signup`,
    ME: `${API_BASE_URL}/auth/me`,
  },
  RAG: {
    QUERY: `${API_BASE_URL}/api/v1/rag/query`,
  }
} as const;
