import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { ArrowLeft, Save, Upload, AlertCircle } from 'lucide-react';
import { 
  VisitTranscript, 
  VisitTranscriptCreate, 
  VisitTranscriptUpdate,
  TranscriptState
} from '../../types/visitTranscript';
import { API_ENDPOINTS } from '../../config/api';
import { useAuth } from '../../contexts/AuthContext';
import { getAuthHeaders } from '../../utils/authUtils';
import Breadcrumb, { BreadcrumbItem } from '../common/Breadcrumb';

interface VisitTranscriptFormProps {
  mode: 'create' | 'edit';
}

const VisitTranscriptForm: React.FC<VisitTranscriptFormProps> = ({ mode }) => {
  const { petId, transcriptId } = useParams<{ petId: string; transcriptId: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();
  
  const [loading, setLoading] = useState(mode === 'edit');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [petName, setPetName] = useState<string>('');
  
  const [formData, setFormData] = useState({
    visit_date: '',
    full_text: '',
    audio_transcript_url: '',
    summary: '',
    metadata: {} as Record<string, any>
  });

  useEffect(() => {
    // Fetch pet name for breadcrumbs
    fetchPetName();
    
    if (mode === 'edit' && transcriptId) {
      fetchTranscript();
    } else {
      // Set default visit date to now for create mode
      const now = new Date();
      setFormData(prev => ({
        ...prev,
        visit_date: now.toISOString().slice(0, 16) // Format for datetime-local input
      }));
      setLoading(false);
    }
  }, [mode, transcriptId]);

  const fetchPetName = async () => {
    try {
      const response = await fetch(API_ENDPOINTS.PETS.GET(petId!), {
        headers: getAuthHeaders()
      });
      if (response.ok) {
        const pet = await response.json();
        setPetName(pet.name);
      }
    } catch (err) {
      console.error('Error fetching pet name:', err);
    }
  };

  const fetchTranscript = async () => {
    if (!transcriptId) return;

    try {
      setLoading(true);
      setError(null);

      const response = await fetch(API_ENDPOINTS.VISIT_TRANSCRIPTS.GET(transcriptId), {
        headers: getAuthHeaders()
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch visit transcript: ${response.statusText}`);
      }

      const transcript: VisitTranscript = await response.json();
      
      // Convert unix timestamp to datetime-local format
      const visitDate = new Date(transcript.visit_date * 1000);
      const formattedDate = visitDate.toISOString().slice(0, 16);
      
      setFormData({
        visit_date: formattedDate,
        full_text: transcript.full_text,
        audio_transcript_url: transcript.audio_transcript_url || '',
        summary: transcript.summary || '',
        metadata: transcript.metadata || {}
      });
    } catch (err) {
      console.error('Error fetching visit transcript:', err);
      setError(err instanceof Error ? err.message : 'Failed to load visit transcript');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!petId) {
      setError('Pet ID is required');
      return;
    }

    if (!formData.visit_date || !formData.full_text.trim()) {
      setError('Visit date and transcript text are required');
      return;
    }

    try {
      setSaving(true);
      setError(null);

      // Convert datetime-local to unix timestamp
      const visitTimestamp = Math.floor(new Date(formData.visit_date).getTime() / 1000);

      let response: Response;
      
      if (mode === 'create') {
        const createData: VisitTranscriptCreate = {
          pet_id: petId,
          visit_date: visitTimestamp,
          full_text: formData.full_text.trim(),
          audio_transcript_url: formData.audio_transcript_url.trim() || undefined,
          summary: formData.summary.trim() || undefined,
          metadata: formData.metadata
        };

        response = await fetch(API_ENDPOINTS.VISIT_TRANSCRIPTS.CREATE, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            ...getAuthHeaders()
          },
          body: JSON.stringify(createData)
        });
      } else {
        if (!transcriptId) {
          throw new Error('Transcript ID is required for editing');
        }

        const updateData: VisitTranscriptUpdate = {
          visit_date: visitTimestamp,
          full_text: formData.full_text.trim(),
          audio_transcript_url: formData.audio_transcript_url.trim() || undefined,
          summary: formData.summary.trim() || undefined,
          metadata: formData.metadata
        };

        response = await fetch(API_ENDPOINTS.VISIT_TRANSCRIPTS.UPDATE(transcriptId), {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            ...getAuthHeaders()
          },
          body: JSON.stringify(updateData)
        });
      }

      if (!response.ok) {
        const errorData = await response.text();
        throw new Error(`Failed to ${mode} visit transcript: ${errorData}`);
      }

      const result = await response.json();
      navigate(`/pets/${petId}/visit-transcripts/${result.uuid}`);
    } catch (err) {
      console.error(`Error ${mode === 'create' ? 'creating' : 'updating'} visit transcript:`, err);
      setError(err instanceof Error ? err.message : `Failed to ${mode} visit transcript`);
    } finally {
      setSaving(false);
    }
  };

  const handleInputChange = (field: string, value: string) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const addMetadataField = () => {
    const key = prompt('Enter metadata key:');
    if (key && key.trim()) {
      const value = prompt('Enter metadata value:');
      if (value !== null) {
        setFormData(prev => ({
          ...prev,
          metadata: {
            ...prev.metadata,
            [key.trim()]: value.trim()
          }
        }));
      }
    }
  };

  const removeMetadataField = (key: string) => {
    setFormData(prev => {
      const newMetadata = { ...prev.metadata };
      delete newMetadata[key];
      return {
        ...prev,
        metadata: newMetadata
      };
    });
  };

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-1/4 mb-6"></div>
          <div className="space-y-6">
            <div className="h-10 bg-gray-200 rounded"></div>
            <div className="h-32 bg-gray-200 rounded"></div>
            <div className="h-10 bg-gray-200 rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto p-6">
      {/* Header */}
      <div className="mb-6">
        {/* Breadcrumbs */}
        <Breadcrumb 
          items={mode === 'edit' ? [
            { label: 'Pet Owners', href: '/pet_owners' },
            { label: petName || 'Pet', href: `/pets/${petId}` },
            { label: 'Visit Transcripts', href: `/pets/${petId}` },
            { label: 'Edit', isActive: true }
          ] : [
            { label: 'Pet Owners', href: '/pet_owners' },
            { label: petName || 'Pet', href: `/pets/${petId}` },
            { label: 'Visit Transcripts', href: `/pets/${petId}` },
            { label: 'Create', isActive: true }
          ]}
          className="mb-6"
        />
        
        <h1 className="text-2xl font-bold text-gray-900">
          {mode === 'create' ? 'Add Visit Transcript' : 'Edit Visit Transcript'}
        </h1>
      </div>

      {/* Error Message */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
          <div className="flex items-center">
            <AlertCircle className="w-5 h-5 text-red-400 mr-2" />
            <p className="text-red-700">{error}</p>
          </div>
        </div>
      )}

      {/* Form */}
      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Visit Date */}
        <div>
          <label htmlFor="visit_date" className="block text-sm font-medium text-gray-700 mb-2">
            Visit Date & Time *
          </label>
          <input
            type="datetime-local"
            id="visit_date"
            value={formData.visit_date}
            onChange={(e) => handleInputChange('visit_date', e.target.value)}
            className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            required
          />
        </div>

        {/* Audio URL */}
        <div>
          <label htmlFor="audio_url" className="block text-sm font-medium text-gray-700 mb-2">
            Audio Recording URL
          </label>
          <div className="flex">
            <input
              type="url"
              id="audio_url"
              value={formData.audio_transcript_url}
              onChange={(e) => handleInputChange('audio_transcript_url', e.target.value)}
              placeholder="https://example.com/audio.mp3"
              className="block w-full px-3 py-2 border border-gray-300 rounded-l-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            <button
              type="button"
              className="inline-flex items-center px-4 py-2 border border-l-0 border-gray-300 bg-gray-50 text-gray-700 rounded-r-md hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <Upload className="w-4 h-4" />
            </button>
          </div>
          <p className="text-sm text-gray-500 mt-1">
            Optional: URL to the audio recording of this visit
          </p>
        </div>

        {/* Summary */}
        <div>
          <label htmlFor="summary" className="block text-sm font-medium text-gray-700 mb-2">
            Visit Summary
          </label>
          <textarea
            id="summary"
            value={formData.summary}
            onChange={(e) => handleInputChange('summary', e.target.value)}
            rows={4}
            placeholder="Brief summary of the visit..."
            className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>

        {/* Full Transcript */}
        <div>
          <label htmlFor="full_text" className="block text-sm font-medium text-gray-700 mb-2">
            Full Transcript *
          </label>
          <textarea
            id="full_text"
            value={formData.full_text}
            onChange={(e) => handleInputChange('full_text', e.target.value)}
            rows={12}
            placeholder="Enter the complete visit transcript here..."
            className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent font-mono text-sm"
            required
          />
          <p className="text-sm text-gray-500 mt-1">
            {formData.full_text.length} characters
          </p>
        </div>

        {/* Metadata */}
        <div>
          <div className="flex items-center justify-between mb-3">
            <label className="block text-sm font-medium text-gray-700">
              Additional Information
            </label>
            <button
              type="button"
              onClick={addMetadataField}
              className="text-sm text-blue-600 hover:text-blue-500"
            >
              + Add Field
            </button>
          </div>
          
          {Object.keys(formData.metadata).length === 0 ? (
            <p className="text-sm text-gray-500 italic">No additional information</p>
          ) : (
            <div className="space-y-3">
              {Object.entries(formData.metadata).map(([key, value]) => (
                <div key={key} className="flex items-center space-x-3">
                  <div className="flex-1 grid grid-cols-2 gap-3">
                    <input
                      type="text"
                      value={key}
                      readOnly
                      className="px-3 py-2 border border-gray-300 rounded-md bg-gray-50 text-sm"
                    />
                    <input
                      type="text"
                      value={String(value)}
                      onChange={(e) => {
                        setFormData(prev => ({
                          ...prev,
                          metadata: {
                            ...prev.metadata,
                            [key]: e.target.value
                          }
                        }));
                      }}
                      className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                  </div>
                  <button
                    type="button"
                    onClick={() => removeMetadataField(key)}
                    className="text-red-600 hover:text-red-500 text-sm"
                  >
                    Remove
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Submit Buttons */}
        <div className="flex items-center justify-end space-x-3 pt-6 border-t border-gray-200">
          <Link
            to={mode === 'edit' && transcriptId ? `/pets/${petId}/visit-transcripts/${transcriptId}` : `/pets/${petId}`}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-md transition-colors"
          >
            Cancel
          </Link>
          <button
            type="submit"
            disabled={saving}
            className="inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed rounded-md transition-colors"
          >
            <Save className="w-4 h-4 mr-2" />
            {saving ? 'Saving...' : mode === 'create' ? 'Create Transcript' : 'Update Transcript'}
          </button>
        </div>
      </form>
    </div>
  );
};

export default VisitTranscriptForm;
