import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { 
  FileText, 
  Plus, 
  Clock, 
  CheckCircle, 
  AlertCircle, 
  XCircle,
  Calendar
} from 'lucide-react';
import { 
  VisitTranscript, 
  TranscriptState,
  TRANSCRIPT_STATE_LABELS,
  TRANSCRIPT_STATE_COLORS
} from '../../types/visitTranscript';
import { API_ENDPOINTS } from '../../config/api';
import { useAuth } from '../../contexts/AuthContext';
import { getAuthHeaders } from '../../utils/authUtils';

interface VisitTranscriptsListProps {
  petId: string;
  petOwnerId?: string;
  showHeader?: boolean;
  maxItems?: number;
}

const VisitTranscriptsList: React.FC<VisitTranscriptsListProps> = ({ 
  petId,
  petOwnerId, 
  showHeader = true, 
  maxItems 
}) => {
  const [transcripts, setTranscripts] = useState<VisitTranscript[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { user } = useAuth();

  useEffect(() => {
    fetchTranscripts();
  }, [petId]);

  const fetchTranscripts = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch(API_ENDPOINTS.VISIT_TRANSCRIPTS.BY_PET(petId), {
        headers: getAuthHeaders()
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch visit transcripts: ${response.statusText}`);
      }

      const data = await response.json();
      let transcriptList = Array.isArray(data) ? data : [];
      
      // Apply maxItems limit if specified
      if (maxItems && transcriptList.length > maxItems) {
        transcriptList = transcriptList.slice(0, maxItems);
      }
      
      setTranscripts(transcriptList);
    } catch (err) {
      console.error('Error fetching visit transcripts:', err);
      setError(err instanceof Error ? err.message : 'Failed to load visit transcripts');
    } finally {
      setLoading(false);
    }
  };

  const canCreateTranscripts = () => {
    return user?.role === 'VET' || user?.role === 'ADMIN';
  };

  const formatDate = (timestamp: number) => {
    return new Date(timestamp * 1000).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getStateIcon = (state: TranscriptState) => {
    switch (state) {
      case TranscriptState.NEW:
        return <Clock className="w-4 h-4" />;
      case TranscriptState.PROCESSING:
        return <Clock className="w-4 h-4 animate-spin" />;
      case TranscriptState.PROCESSED:
        return <CheckCircle className="w-4 h-4" />;
      case TranscriptState.FAILED:
        return <XCircle className="w-4 h-4" />;
      default:
        return <Clock className="w-4 h-4" />;
    }
  };

  if (loading) {
    return (
      <div className="space-y-4">
        {showHeader && (
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-gray-900 flex items-center">
              <FileText className="w-5 h-5 mr-2 text-blue-600" />
              Visit Transcripts
            </h3>
          </div>
        )}
        <div className="animate-pulse space-y-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="bg-gray-200 h-24 rounded-lg"></div>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-4">
        {showHeader && (
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-gray-900 flex items-center">
              <FileText className="w-5 h-5 mr-2 text-blue-600" />
              Visit Transcripts
            </h3>
          </div>
        )}
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center">
            <AlertCircle className="w-5 h-5 text-red-400 mr-2" />
            <p className="text-red-700">{error}</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {showHeader && (
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-900 flex items-center">
            <FileText className="w-5 h-5 mr-2 text-blue-600" />
            Visit Transcripts
            {transcripts.length > 0 && (
              <span className="ml-2 text-sm text-gray-500">
                ({transcripts.length} transcript{transcripts.length !== 1 ? 's' : ''})
              </span>
            )}
          </h3>
          {canCreateTranscripts() && (
            <Link
              to={`/pets/${petId}/visit-transcripts/create`}
              className="inline-flex items-center px-3 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-md transition-colors duration-200"
            >
              <Plus className="w-4 h-4 mr-2" />
              Add Transcript
            </Link>
          )}
        </div>
      )}

      {transcripts.length === 0 ? (
        <div className="text-center py-8 bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
          <FileText className="w-12 h-12 mx-auto text-gray-400 mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No visit transcripts</h3>
          <p className="text-gray-600 mb-4">
            This pet doesn't have any visit transcripts yet.
          </p>
          {canCreateTranscripts() && (
            <Link
              to={`/pets/${petId}/visit-transcripts/create`}
              className="inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-md transition-colors duration-200"
            >
              <Plus className="w-4 h-4 mr-2" />
              Add First Transcript
            </Link>
          )}
        </div>
      ) : (
        <div className="space-y-4">
          {transcripts.map((transcript) => (
            <div
              key={transcript.uuid}
              className="bg-white border border-gray-200 rounded-lg p-6 hover:shadow-md transition-shadow duration-200"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-3 mb-3">
                    <div className="flex items-center space-x-2">
                      <Calendar className="w-4 h-4 text-gray-500" />
                      <span className="text-sm font-medium text-gray-900">
                        {formatDate(transcript.visit_date)}
                      </span>
                    </div>
                    <div className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${TRANSCRIPT_STATE_COLORS[transcript.state]}`}>
                      {getStateIcon(transcript.state)}
                      <span className="ml-1">{TRANSCRIPT_STATE_LABELS[transcript.state]}</span>
                    </div>
                  </div>

                  {transcript.summary && (
                    <p className="text-gray-700 mb-3 line-clamp-2">
                      {transcript.summary}
                    </p>
                  )}


                </div>

                <div className="flex items-center space-x-2 ml-4">
                  <Link
                    to={`/pets/${petId}/visit-transcripts/${transcript.uuid}`}
                    className="inline-flex items-center px-3 py-2 text-sm font-medium text-blue-600 bg-blue-50 hover:bg-blue-100 rounded-md transition-colors duration-200"
                  >
                    <FileText className="w-4 h-4 mr-1" />
                    View
                  </Link>
                  {canCreateTranscripts() && transcript.state !== TranscriptState.PROCESSING && (
                    <Link
                      to={`/pets/${petId}/visit-transcripts/${transcript.uuid}/edit`}
                      className="inline-flex items-center px-3 py-2 text-sm font-medium text-gray-600 bg-gray-50 hover:bg-gray-100 rounded-md transition-colors duration-200"
                    >
                      Edit
                    </Link>
                  )}
                </div>
              </div>
            </div>
          ))}

          {maxItems && transcripts.length === maxItems && (
            <div className="text-center py-4">
              <Link
                to={`/pets/${petId}/visit-transcripts`}
                className="text-blue-600 hover:text-blue-500 font-medium text-sm"
              >
                View all visit transcripts →
              </Link>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default VisitTranscriptsList;
