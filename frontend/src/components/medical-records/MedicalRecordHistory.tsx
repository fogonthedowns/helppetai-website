import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  ArrowLeft, 
  History, 
  Calendar, 
  User, 
  FileText,
  AlertTriangle
} from 'lucide-react';
import { 
  MedicalRecord,
  MedicalRecordListResponse,
  MEDICAL_RECORD_TYPE_LABELS,
  MEDICAL_RECORD_TYPE_COLORS
} from '../../types/medicalRecord';
import { API_ENDPOINTS } from '../../config/api';
import { useAuth } from '../../contexts/AuthContext';
import { getAuthHeaders } from '../../utils/authUtils';
import Breadcrumb, { BreadcrumbItem } from '../common/Breadcrumb';

const MedicalRecordHistory: React.FC = () => {
  const { petId } = useParams<{ petId: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();
  
  const [history, setHistory] = useState<MedicalRecordListResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [petName, setPetName] = useState<string>('');

  useEffect(() => {
    if (petId) {
      fetchHistory();
      fetchPetInfo();
    }
  }, [petId]);

  const fetchPetInfo = async () => {
    try {
      const response = await fetch(API_ENDPOINTS.PETS.GET(petId!), {
        headers: getAuthHeaders()
      });
      if (response.ok) {
        const pet = await response.json();
        setPetName(pet.name);
      }
    } catch (err) {
      console.error('Error fetching pet info:', err);
    }
  };

  const fetchHistory = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch(API_ENDPOINTS.MEDICAL_RECORDS.HISTORY(petId!), {
        headers: getAuthHeaders()
      });
      
      if (!response.ok) {
        if (response.status === 403) {
          throw new Error('Access denied to view medical record history');
        }
        throw new Error('Failed to fetch medical record history');
      }

      const historyData = await response.json();
      setHistory(historyData);
    } catch (err) {
      console.error('Error fetching medical record history:', err);
      setError(err instanceof Error ? err.message : 'Failed to load medical record history');
    } finally {
      setLoading(false);
    }
  };

  const formatDateTime = (dateString: string) => {
    return new Date(dateString).toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getRecordTypeColor = (recordType: string) => {
    return MEDICAL_RECORD_TYPE_COLORS[recordType as keyof typeof MEDICAL_RECORD_TYPE_COLORS] || 
           'bg-gray-100 text-gray-800';
  };

  const getRecordTypeLabel = (recordType: string) => {
    return MEDICAL_RECORD_TYPE_LABELS[recordType as keyof typeof MEDICAL_RECORD_TYPE_LABELS] || 
           recordType.charAt(0).toUpperCase() + recordType.slice(1);
  };

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <div className="flex items-center justify-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <span className="ml-2 text-gray-600">Loading medical record history...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center">
            <AlertTriangle className="w-5 h-5 text-red-600 mr-2" />
            <p className="text-sm text-red-700">{error}</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto p-6">
      <div className="mb-6">
        {/* Breadcrumbs */}
        <Breadcrumb 
          items={[
            { label: 'Pet Owners', href: '/pet_owners' },
            { label: petName || 'Pet', href: `/pets/${petId}` },
            { label: 'Medical Records', isActive: true }
          ]}
          className="mb-6"
        />
        
        <h1 className="text-2xl font-bold text-gray-900 flex items-center">
          <History className="w-6 h-6 mr-3 text-blue-600" />
          Medical Record History
          {petName && <span className="text-gray-600 ml-2">for {petName}</span>}
        </h1>
        
        {history && (
          <p className="text-gray-600 mt-2">
            {history.total} total version{history.total !== 1 ? 's' : ''} • 
            {history.current_records_count} current • 
            {history.historical_records_count} historical
          </p>
        )}
      </div>

      {!history || history.records.length === 0 ? (
        <div className="text-center py-8 bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
          <FileText className="w-12 h-12 mx-auto text-gray-400 mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No medical record history</h3>
          <p className="text-gray-600">
            This pet doesn't have any medical records yet.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {history.records.map((record, index) => (
            <div
              key={record.id}
              className={`bg-white border rounded-lg p-4 hover:shadow-md transition-shadow duration-200 ${
                record.is_current ? 'border-blue-200 bg-blue-50' : 'border-gray-200'
              }`}
            >
              <div className="flex items-start justify-between mb-3">
                <div className="flex-1">
                  <div className="flex items-center mb-2">
                    <span className={`inline-flex items-center px-2 py-1 text-xs font-medium rounded-full ${getRecordTypeColor(record.record_type)}`}>
                      {getRecordTypeLabel(record.record_type)}
                    </span>
                    <span className={`ml-2 inline-flex items-center px-2 py-1 text-xs font-medium rounded-full ${
                      record.is_current ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-600'
                    }`}>
                      {record.is_current ? 'Current' : `v${record.version}`}
                    </span>
                  </div>
                  
                  <h4 className="text-lg font-semibold text-gray-900 mb-1">
                    {record.title}
                  </h4>
                  
                  <div className="flex items-center text-sm text-gray-600 mb-2">
                    <Calendar className="w-4 h-4 mr-1" />
                    <span>Visit: {formatDateTime(record.visit_date)}</span>
                    {record.veterinarian_name && (
                      <>
                        <User className="w-4 h-4 ml-4 mr-1" />
                        <span>{record.veterinarian_name}</span>
                      </>
                    )}
                  </div>

                  {record.description && (
                    <p className="text-gray-700 text-sm mb-2 line-clamp-2">
                      {record.description}
                    </p>
                  )}

                  {record.diagnosis && (
                    <div className="text-sm">
                      <span className="font-medium text-gray-700">Diagnosis:</span>
                      <span className="ml-1 text-gray-600">{record.diagnosis}</span>
                    </div>
                  )}
                </div>

                <div className="flex items-center space-x-2 ml-4">
                  <button
                    onClick={() => navigate(`/pets/${petId}/medical-records/${record.id}`)}
                    className="inline-flex items-center px-2 py-1 text-xs font-medium text-white bg-blue-600 hover:bg-blue-700 rounded transition-colors duration-200"
                  >
                    <FileText className="w-3 h-3 mr-1" />
                    View
                  </button>
                </div>
              </div>

              {/* Metadata */}
              <div className="flex items-center justify-between text-xs text-gray-500 pt-2 border-t border-gray-100">
                <span>
                  Created: {formatDateTime(record.created_at)}
                </span>
                <span>
                  Version {record.version}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default MedicalRecordHistory;
