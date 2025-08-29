/**
 * RAG API Type Definitions
 * These types match the backend API response structure exactly
 */

export interface SourceReference {
  id: string;
  title: string;
  url: string | null;
  chunk_info: string;
  relevance_score: number;
  audience: string | null;
  authority_level: string | null;
  publisher: string | null;
  publication_year: number | null;
  species: string[] | null;
  symptoms: string[] | null;
}

export interface QueryMetadata {
  processing_time_seconds: number;
  pinecone_results_count: number;
  sources_count: number;
  available_content_count?: number;
  question: string;
  timestamp: string;
  openai_model: string;
  openai_temperature?: number;
  embedding_model?: string;
  pinecone_index?: string;
  filters_applied?: boolean;
  filter_details?: Record<string, any>;
  status: string;
}

export interface RAGResponse {
  answer: string;
  sources: SourceReference[];
  query_metadata: QueryMetadata;
}

export interface RAGRequest {
  question: string;
  max_results?: number;
  // Filtering options
  doc_type?: string;
  species?: string[];
  symptoms?: string[];
  medical_system?: string;
  audience?: 'expert' | 'pet-owner';
  source_id?: string;
  chunk_index?: number;
  version?: string;
}

export interface SearchState {
  query: string;
  isLoading: boolean;
  result: RAGResponse | null;
  error: string | null;
  searchId: string | null;
  filters: Partial<RAGRequest>;
}

export interface SearchHistoryItem {
  id: string;
  query: string;
  timestamp: string;
  preview: string; // First 100 chars of answer
  filters?: Partial<RAGRequest>;
}

export interface LoadingPhase {
  id: string;
  message: string;
  duration: number; // seconds
  icon: string;
}

// Citation parsing types
export interface Citation {
  number: number;
  start: number;
  end: number;
  sourceIndex: number;
}

// Error types
export interface APIError {
  message: string;
  code?: string;
  details?: Record<string, any>;
}
