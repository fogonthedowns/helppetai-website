import { RAGRequest, RAGResponse, APIError, Citation, SourceReference } from '../types/rag';

// API Configuration
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

/**
 * Search the RAG knowledge base
 */
export const searchRAG = async (request: RAGRequest): Promise<RAGResponse> => {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 30000); // 30 seconds

    const response = await fetch(`${API_BASE_URL}/api/v1/rag/query`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      let errorMessage = 'An unexpected error occurred';
      let errorDetails = null;

      try {
        const errorData = await response.json();
        errorMessage = errorData.detail || errorData.message || errorMessage;
        errorDetails = errorData;
      } catch {
        // If JSON parsing fails, use status text
        errorMessage = response.statusText || errorMessage;
      }

      const apiError: APIError = {
        message: errorMessage,
        code: response.status.toString(),
        details: errorDetails,
      };
      throw apiError;
    }

    const data = await response.json();
    return data;
  } catch (error: any) {
    if (error.name === 'AbortError') {
      throw {
        message: 'Request timeout - please try again',
        code: 'TIMEOUT',
      } as APIError;
    }

    if (error.message && error.code) {
      // Already an APIError
      throw error;
    }
    
    throw {
      message: error.message || 'Network error occurred',
      code: 'NETWORK_ERROR',
    } as APIError;
  }
};

/**
 * Parse citations from answer text
 * Finds [1], [2], [3] etc. and returns their positions
 * Deduplicates citations and limits to available sources
 */
export const parseCitations = (text: string, maxSources: number = 10): Citation[] => {
  const citations: Citation[] = [];
  const citationRegex = /\[(\d+)\]/g;
  const seenCitations = new Set<number>();
  let match;

  while ((match = citationRegex.exec(text)) !== null) {
    const citationNumber = parseInt(match[1], 10);
    const sourceIndex = citationNumber - 1; // Convert to 0-based index
    
    // Only include if:
    // 1. We haven't seen this citation number before
    // 2. The source index is within our available sources
    // 3. The citation number is reasonable (1-10)
    if (!seenCitations.has(citationNumber) && 
        sourceIndex >= 0 && 
        sourceIndex < maxSources &&
        citationNumber <= 10) {
      
      citations.push({
        number: citationNumber,
        start: match.index,
        end: match.index + match[0].length,
        sourceIndex: sourceIndex,
      });
      
      seenCitations.add(citationNumber);
    }
  }

  // Sort by position in text
  return citations.sort((a, b) => a.start - b.start);
};

/**
 * Replace citations in text with placeholder elements
 */
export const replaceCitationsWithPlaceholders = (text: string): string => {
  return text.replace(/\[(\d+)\]/g, '{{CITATION_$1}}');
};

/**
 * Clean up duplicate citations in text
 * Removes excessive duplicate citation numbers from text
 */
export const cleanupDuplicateCitations = (text: string, maxSources: number = 10): string => {
  // Split text into sentences/paragraphs for processing
  return text.replace(/(\[(\d+)\])\s*(\[\2\])+/g, '$1') // Remove immediate duplicates like [1] [1] [1]
             .replace(/(\[(\d+)\])\s*(?:\[\d+\]\s*)*(\[\2\])/g, '$1') // Remove duplicate citations separated by other citations
             .replace(/\[(\d+)\]/g, (match, num) => {
               const citationNum = parseInt(num, 10);
               return citationNum <= maxSources ? match : ''; // Remove citations beyond available sources
             });
};

/**
 * Generate a unique search ID
 */
export const generateSearchId = (): string => {
  return Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15);
};

/**
 * Format timestamp for display
 */
export const formatTimestamp = (timestamp: string): string => {
  const date = new Date(timestamp);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / (1000 * 60));
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

  if (diffMins < 1) {
    return 'Just now';
  } else if (diffMins < 60) {
    return `${diffMins}m ago`;
  } else if (diffHours < 24) {
    return `${diffHours}h ago`;
  } else if (diffDays < 7) {
    return `${diffDays}d ago`;
  } else {
    return date.toLocaleDateString();
  }
};

/**
 * Truncate text to specified length with ellipsis
 */
export const truncateText = (text: string, maxLength: number): string => {
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength).trim() + '...';
};

/**
 * Get animal emoji for species
 */
export const getSpeciesEmoji = (species: string): string => {
  const emojiMap: Record<string, string> = {
    dog: '🐕',
    cat: '🐱',
    horse: '🐴',
    cow: '🐄',
    sheep: '🐑',
    pig: '🐷',
    goat: '🐐',
    rabbit: '🐰',
    bird: '🐦',
    fish: '🐟',
    reptile: '🦎',
    rodent: '🐭',
  };
  
  return emojiMap[species.toLowerCase()] || '🐾';
};

/**
 * Get authority level badge info
 */
export const getAuthorityBadge = (authorityLevel: string | null): { emoji: string; label: string; color: string } => {
  switch (authorityLevel?.toLowerCase()) {
    case 'expert':
      return { emoji: '🏛️', label: 'Expert', color: 'bg-blue-100 text-blue-800' };
    case 'academic':
      return { emoji: '🎓', label: 'Academic', color: 'bg-purple-100 text-purple-800' };
    case 'clinical':
      return { emoji: '🩺', label: 'Clinical', color: 'bg-green-100 text-green-800' };
    case 'government':
      return { emoji: '🏛️', label: 'Government', color: 'bg-gray-100 text-gray-800' };
    default:
      return { emoji: '📄', label: 'Source', color: 'bg-gray-100 text-gray-600' };
  }
};

/**
 * Get relevance score stars (0-5 stars)
 */
export const getRelevanceStars = (score: number): number => {
  // Convert 0-1 score to 0-5 stars
  return Math.round(score * 5);
};

/**
 * Debounce function for search input
 */
export const debounce = <T extends (...args: any[]) => any>(
  func: T,
  wait: number
): ((...args: Parameters<T>) => void) => {
  let timeout: NodeJS.Timeout;
  
  return (...args: Parameters<T>) => {
    clearTimeout(timeout);
    timeout = setTimeout(() => func(...args), wait);
  };
};

/**
 * Copy text to clipboard
 */
export const copyToClipboard = async (text: string): Promise<boolean> => {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch (error) {
    // Fallback for older browsers
    const textArea = document.createElement('textarea');
    textArea.value = text;
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();
    
    try {
      document.execCommand('copy');
      document.body.removeChild(textArea);
      return true;
    } catch (fallbackError) {
      document.body.removeChild(textArea);
      return false;
    }
  }
};

/**
 * Generate shareable URL for search results
 */
export const generateShareableURL = (searchId: string, query: string): string => {
  const baseUrl = window.location.origin;
  const params = new URLSearchParams({
    q: query,
    id: searchId,
  });
  
  return `${baseUrl}/rag/search?${params.toString()}`;
};

/**
 * Validate search query
 */
export const validateSearchQuery = (query: string): { isValid: boolean; error?: string } => {
  if (!query.trim()) {
    return { isValid: false, error: 'Please enter a question' };
  }
  
  if (query.length < 3) {
    return { isValid: false, error: 'Question must be at least 3 characters long' };
  }
  
  if (query.length > 1000) {
    return { isValid: false, error: 'Question must be less than 1000 characters' };
  }
  
  return { isValid: true };
};

/**
 * Combine multiple chunks from the same source into a single display item
 */
export interface CombinedSource {
  id: string;
  title: string;
  url: string | null;
  chunks: Array<{
    chunk_info: string;
    relevance_score: number;
    originalIndex: number;
  }>;
  audience: string | null;
  authority_level: string | null;
  publisher: string | null;
  publication_year: number | null;
  species: string[] | null;
  symptoms: string[] | null;
  maxRelevanceScore: number;
  totalChunks: number;
}

export const combineSourceChunks = (sources: SourceReference[]): CombinedSource[] => {
  const sourceMap = new Map<string, CombinedSource>();
  
  sources.forEach((source, index) => {
    // Create a key based on title + url to group sources that are actually the same
    const sourceKey = `${source.title || 'Unknown'}|${source.url || 'no-url'}`;
    
    if (sourceMap.has(sourceKey)) {
      // Add chunk to existing source
      const combined = sourceMap.get(sourceKey)!;
      combined.chunks.push({
        chunk_info: source.chunk_info,
        relevance_score: source.relevance_score,
        originalIndex: index
      });
      combined.maxRelevanceScore = Math.max(combined.maxRelevanceScore, source.relevance_score);
      combined.totalChunks++;
    } else {
      // Create new combined source
      sourceMap.set(sourceKey, {
        id: source.id, // Use the first ID encountered
        title: source.title,
        url: source.url,
        chunks: [{
          chunk_info: source.chunk_info,
          relevance_score: source.relevance_score,
          originalIndex: index
        }],
        audience: source.audience,
        authority_level: source.authority_level,
        publisher: source.publisher,
        publication_year: source.publication_year,
        species: source.species,
        symptoms: source.symptoms,
        maxRelevanceScore: source.relevance_score,
        totalChunks: 1
      });
    }
  });
  
  // Sort by max relevance score
  return Array.from(sourceMap.values()).sort((a, b) => b.maxRelevanceScore - a.maxRelevanceScore);
};

/**
 * Create a mapping from original source indices to combined source indices
 */
export const createCitationMapping = (sources: SourceReference[], combinedSources: CombinedSource[]): Map<number, number> => {
  const mapping = new Map<number, number>();
  
  combinedSources.forEach((combinedSource, combinedIndex) => {
    combinedSource.chunks.forEach(chunk => {
      mapping.set(chunk.originalIndex, combinedIndex);
    });
  });
  
  return mapping;
};

/**
 * Remap citation numbers in answer text to match combined sources
 */
export const remapCitationsInAnswer = (answerText: string, citationMapping: Map<number, number>): string => {
  // Find all citations in the format [1], [2], etc.
  return answerText.replace(/\[(\d+)\]/g, (match, number) => {
    const originalIndex = parseInt(number, 10) - 1; // Convert to 0-based index
    const newIndex = citationMapping.get(originalIndex);
    
    if (newIndex !== undefined) {
      return `[${newIndex + 1}]`; // Convert back to 1-based index
    }
    
    // If no mapping found, remove the citation
    return '';
  });
};
