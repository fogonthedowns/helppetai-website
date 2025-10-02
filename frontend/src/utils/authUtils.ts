/**
 * Authentication utilities for API requests
 */

// Setup fetch interceptor for automatic token inclusion
const originalFetch = window.fetch;

window.fetch = async (input: RequestInfo | URL, init?: RequestInit): Promise<Response> => {
  const token = localStorage.getItem('token');
  
  // Add authorization header if token exists
  if (token && init) {
    init.headers = {
      ...init.headers,
      'Authorization': `Bearer ${token}`,
    };
  } else if (token) {
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
    localStorage.removeItem('access_token');
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
  localStorage.removeItem('access_token');
  localStorage.removeItem('username');
  window.location.href = '/';
};

export const getAuthHeaders = (): Record<string, string> => {
  const token = getAuthToken();
  return token ? { 'Authorization': `Bearer ${token}` } : {};
};
