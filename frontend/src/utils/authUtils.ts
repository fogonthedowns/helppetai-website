/**
 * Authentication utilities for API requests
 */

// Setup fetch interceptor for automatic token inclusion
const originalFetch = window.fetch;

window.fetch = async (input: RequestInfo | URL, init?: RequestInit): Promise<Response> => {
  const token = localStorage.getItem('token');
  
  // Don't add auth header for S3 uploads (they use presigned URLs)
  const url = typeof input === 'string' ? input : input instanceof URL ? input.href : input.url;
  const isS3Upload = url.includes('.s3.amazonaws.com') || url.includes('s3.amazonaws.com');
  
  // Add authorization header if token exists and it's not an S3 upload
  if (token && !isS3Upload && init) {
    init.headers = {
      ...init.headers,
      'Authorization': `Bearer ${token}`,
    };
  } else if (token && !isS3Upload) {
    init = {
      ...init,
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    };
  }

  const response = await originalFetch(input, init);

  // Handle 401 responses (token expired)
  if (response.status === 401) {
    localStorage.removeItem('token');
    localStorage.removeItem('username');
    
    // Only redirect if we're not already on login/signup pages
    const currentPath = window.location.pathname;
    if (!currentPath.includes('/login') && !currentPath.includes('/signup')) {
      window.location.href = '/login';
    }
  }

  return response;
};

export const getAuthToken = (): string | null => {
  return localStorage.getItem('token');
};

export const isAuthenticated = (): boolean => {
  const token = getAuthToken();
  return !!token;
};

export const logout = (): void => {
  localStorage.removeItem('token');
  localStorage.removeItem('username');
  window.location.href = '/';
};

export const getAuthHeaders = (): Record<string, string> => {
  const token = getAuthToken();
  return token ? { 'Authorization': `Bearer ${token}` } : {};
};
