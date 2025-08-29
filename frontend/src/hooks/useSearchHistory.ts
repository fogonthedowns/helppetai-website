import { useState, useEffect, useCallback } from 'react';
import { SearchHistoryItem, RAGRequest } from '../types/rag';
import { truncateText } from '../utils/searchUtils';

const STORAGE_KEY = 'helppetai_search_history';
const MAX_HISTORY_ITEMS = 20;

const loadHistoryFromStorage = (): SearchHistoryItem[] => {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      const parsed = JSON.parse(stored);
      if (Array.isArray(parsed)) {
        return parsed;
      }
    }
  } catch (error) {
    console.warn('Failed to load search history from localStorage:', error);
  }
  return [];
};

const saveHistoryToStorage = (history: SearchHistoryItem[]): void => {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(history));
  } catch (error) {
    console.warn('Failed to save search history to localStorage:', error);
  }
};

export const useSearchHistory = () => {
  const [history, setHistory] = useState<SearchHistoryItem[]>([]);
  const [isLoaded, setIsLoaded] = useState(false);

  // Load history on mount
  useEffect(() => {
    const loadedHistory = loadHistoryFromStorage();
    setHistory(loadedHistory);
    setIsLoaded(true);
  }, []);

  // Save to localStorage whenever history changes
  useEffect(() => {
    if (isLoaded) {
      saveHistoryToStorage(history);
    }
  }, [history, isLoaded]);

  const addSearch = useCallback((
    query: string,
    answer: string,
    filters?: Partial<RAGRequest>
  ) => {
    const newItem: SearchHistoryItem = {
      id: Date.now().toString() + Math.random().toString(36).substring(2),
      query: query.trim(),
      timestamp: new Date().toISOString(),
      preview: truncateText(answer, 100),
      filters,
    };

    setHistory(prev => {
      // Remove any existing item with the same query
      const filtered = prev.filter(item => item.query !== newItem.query);
      
      // Add new item at the beginning
      const updated = [newItem, ...filtered];
      
      // Limit to MAX_HISTORY_ITEMS
      return updated.slice(0, MAX_HISTORY_ITEMS);
    });
  }, []);

  const removeSearch = useCallback((id: string) => {
    setHistory(prev => prev.filter(item => item.id !== id));
  }, []);

  const clearHistory = useCallback(() => {
    setHistory([]);
  }, []);

  const getSearchById = useCallback((id: string): SearchHistoryItem | undefined => {
    return history.find(item => item.id === id);
  }, [history]);

  const searchHistory = useCallback((searchTerm: string): SearchHistoryItem[] => {
    if (!searchTerm.trim()) {
      return history;
    }

    const term = searchTerm.toLowerCase();
    return history.filter(item => 
      item.query.toLowerCase().includes(term) ||
      item.preview.toLowerCase().includes(term)
    );
  }, [history]);

  const getRecentSearches = useCallback((limit: number = 5): SearchHistoryItem[] => {
    return history.slice(0, limit);
  }, [history]);

  const updateSearch = useCallback((id: string, updates: Partial<SearchHistoryItem>) => {
    setHistory(prev => prev.map(item => 
      item.id === id ? { ...item, ...updates } : item
    ));
  }, []);

  const hasSearches = history.length > 0;

  return {
    // State
    history,
    isLoaded,
    hasSearches,

    // Actions
    addSearch,
    removeSearch,
    clearHistory,
    getSearchById,
    searchHistory,
    getRecentSearches,
    updateSearch,
  };
};
