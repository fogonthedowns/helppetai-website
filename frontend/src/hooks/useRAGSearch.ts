import { useState, useCallback, useRef } from 'react';
import { SearchState, RAGRequest, APIError } from '../types/rag';
import { searchRAG, generateSearchId, validateSearchQuery } from '../utils/searchUtils';

const initialState: SearchState = {
  query: '',
  isLoading: false,
  result: null,
  error: null,
  searchId: null,
  filters: {},
};

export const useRAGSearch = () => {
  const [state, setState] = useState<SearchState>(initialState);
  const abortControllerRef = useRef<AbortController | null>(null);

  const search = useCallback(async (query: string, filters: Partial<RAGRequest> = {}) => {
    // Validate query
    const validation = validateSearchQuery(query);
    if (!validation.isValid) {
      setState(prev => ({
        ...prev,
        error: validation.error || 'Invalid query',
        result: null,
      }));
      return;
    }

    // Cancel any existing request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    // Create new abort controller
    abortControllerRef.current = new AbortController();

    // Generate search ID
    const searchId = generateSearchId();

    // Set loading state
    setState(prev => ({
      ...prev,
      query: query.trim(),
      isLoading: true,
      error: null,
      result: null,
      searchId,
      filters,
    }));

    try {
      // Prepare request
      const request: RAGRequest = {
        question: query.trim(),
        max_results: 5,
        ...filters,
      };

      // Make API call
      const result = await searchRAG(request);

      // Check if request was aborted
      if (abortControllerRef.current?.signal.aborted) {
        return;
      }

      // Update state with results
      setState(prev => ({
        ...prev,
        isLoading: false,
        result,
        error: null,
      }));

    } catch (error) {
      // Check if request was aborted
      if (abortControllerRef.current?.signal.aborted) {
        return;
      }

      const apiError = error as APIError;
      setState(prev => ({
        ...prev,
        isLoading: false,
        result: null,
        error: apiError.message || 'An unexpected error occurred',
      }));
    }
  }, []);

  const clearResults = useCallback(() => {
    // Cancel any ongoing request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    setState(initialState);
  }, []);

  const updateQuery = useCallback((query: string) => {
    setState(prev => ({
      ...prev,
      query,
      error: null,
    }));
  }, []);

  const updateFilters = useCallback((filters: Partial<RAGRequest>) => {
    setState(prev => ({
      ...prev,
      filters: { ...prev.filters, ...filters },
    }));
  }, []);

  const clearError = useCallback(() => {
    setState(prev => ({
      ...prev,
      error: null,
    }));
  }, []);

  const cancelSearch = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    setState(prev => ({
      ...prev,
      isLoading: false,
    }));
  }, []);

  return {
    // State
    query: state.query,
    isLoading: state.isLoading,
    result: state.result,
    error: state.error,
    searchId: state.searchId,
    filters: state.filters,

    // Actions
    search,
    clearResults,
    updateQuery,
    updateFilters,
    clearError,
    cancelSearch,
  };
};
