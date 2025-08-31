/**
 * Visit Transcript Types - Based on spec in docs/0009_VisitTranscript.md
 */

export enum TranscriptState {
  NEW = 'new',
  PROCESSING = 'processing', 
  PROCESSED = 'processed',
  FAILED = 'failed'
}

export interface VisitTranscript {
  uuid: string;
  pet_id: string;
  visit_date: number; // Unix timestamp (int32)
  full_text: string;
  audio_transcript_url?: string;
  metadata: Record<string, any>;
  summary?: string;
  state: TranscriptState;
  created_at: string;
  updated_at: string;
  created_by?: string; // User ID who created the transcript
}

export interface VisitTranscriptCreate {
  pet_id: string;
  visit_date: number;
  full_text: string;
  audio_transcript_url?: string;
  metadata?: Record<string, any>;
  summary?: string;
}

export interface VisitTranscriptUpdate {
  visit_date?: number;
  full_text?: string;
  audio_transcript_url?: string;
  metadata?: Record<string, any>;
  summary?: string;
  state?: TranscriptState;
}

export interface VisitTranscriptListResponse {
  transcripts: VisitTranscript[];
  total: number;
  page: number;
  per_page: number;
}

// State display configurations
export const TRANSCRIPT_STATE_LABELS: Record<TranscriptState, string> = {
  [TranscriptState.NEW]: 'New',
  [TranscriptState.PROCESSING]: 'Processing',
  [TranscriptState.PROCESSED]: 'Processed',
  [TranscriptState.FAILED]: 'Failed'
};

export const TRANSCRIPT_STATE_COLORS: Record<TranscriptState, string> = {
  [TranscriptState.NEW]: 'bg-gray-100 text-gray-800',
  [TranscriptState.PROCESSING]: 'bg-blue-100 text-blue-800',
  [TranscriptState.PROCESSED]: 'bg-green-100 text-green-800',
  [TranscriptState.FAILED]: 'bg-red-100 text-red-800'
};
