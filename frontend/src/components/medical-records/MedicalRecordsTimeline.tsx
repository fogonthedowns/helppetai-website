import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { 
  Calendar, 
  Stethoscope, 
  Plus, 
  Clock, 
  AlertTriangle, 
  TrendingUp,
  FileText,
  User,
  DollarSign,
  History
} from 'lucide-react';
import { 
  MedicalRecord, 
  MedicalRecordTimelineResponse,
  MEDICAL_RECORD_TYPE_LABELS,
  MEDICAL_RECORD_TYPE_COLORS
} from '../../types/medicalRecord';
import { API_ENDPOINTS } from '../../config/api';
import { useAuth } from '../../contexts/AuthContext';
import { getAuthHeaders } from '../../utils/authUtils';

interface MedicalRecordsTimelineProps {
  petId: string;
  showHeader?: boolean;
  maxItems?: number;
}

const MedicalRecordsTimeline: React.FC<MedicalRecordsTimelineProps> = ({ 
  petId, 
  showHeader = true, 
  maxItems 
}) => {
  const [timeline, setTimeline] = useState<MedicalRecordTimelineResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { user } = useAuth();

  useEffect(() => {
    fetchTimeline();
  }, [petId]);

  const fetchTimeline = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch(API_ENDPOINTS.MEDICAL_RECORDS.TIMELINE(petId), {
        headers: getAuthHeaders()
      });
      
      if (!response.ok) {
        if (response.status === 403) {
          throw new Error('Access denied to view medical records for this pet');
        }
        throw new Error('Failed to fetch medical records');
      }

      const timelineData = await response.json();
      setTimeline(timelineData);
    } catch (err) {
      console.error('Error fetching medical records timeline:', err);
      setError(err instanceof Error ? err.message : 'Failed to load medical records');
    } finally {
      setLoading(false);
    }
  };

  const canCreateRecords = () => {
    return user?.role === 'ADMIN' || user?.role === 'VET_STAFF';
  };

  const canEditRecords = () => {
    return user?.role === 'ADMIN' || user?.role === 'VET_STAFF';
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
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

  const displayedRecords = maxItems && timeline ? 
    timeline.records_by_date.slice(0, maxItems) : 
    timeline?.records_by_date || [];

  if (loading) {
    return (
      <div className="flex items-center justify-center py-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span className="ml-2 text-gray-600">Loading medical records...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <div className="flex items-center">
          <AlertTriangle className="w-5 h-5 text-red-600 mr-2" />
          <p className="text-sm text-red-700">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {showHeader && (
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-900 flex items-center">
            <Stethoscope className="w-5 h-5 mr-2 text-blue-600" />
            Medical Records
            {timeline && timeline.records_by_date.length > 0 && (
              <span className="ml-2 text-sm text-gray-500">
                ({timeline.records_by_date.length} record{timeline.records_by_date.length !== 1 ? 's' : ''})
              </span>
            )}
          </h3>
          {canCreateRecords() && (
            <Link
              to={`/pets/${petId}/medical-records/create`}
              className="inline-flex items-center px-3 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-md transition-colors duration-200"
            >
              <Plus className="w-4 h-4 mr-2" />
              Add Record
            </Link>
          )}
        </div>
      )}

      {/* Follow-ups Due Alert */}
      {timeline && timeline.follow_up_due.length > 0 && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <div className="flex items-start">
            <Clock className="w-5 h-5 text-yellow-600 mr-3 mt-0.5" />
            <div>
              <h4 className="text-sm font-medium text-yellow-800 mb-2">
                Follow-ups Due ({timeline.follow_up_due.length})
              </h4>
              <div className="space-y-1">
                {timeline.follow_up_due.map((record) => (
                  <div key={record.id} className="text-sm text-yellow-700">
                    <Link 
                      to={`/pets/${petId}/medical-records/${record.id}`}
                      className="hover:underline font-medium"
                    >
                      {record.title}
                    </Link>
                    {record.follow_up_date && (
                      <span className="ml-2">
                        (Due: {formatDate(record.follow_up_date)})
                      </span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Recent Weight */}
      {timeline && timeline.recent_weight && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-center">
            <TrendingUp className="w-5 h-5 text-blue-600 mr-3" />
            <div>
              <h4 className="text-sm font-medium text-blue-800">Latest Weight</h4>
              <p className="text-blue-700">
                {timeline.recent_weight} lbs
                {timeline.weight_trend && (
                  <span className="ml-2 text-xs">
                    ({timeline.weight_trend})
                  </span>
                )}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Medical Records Timeline */}
      {!timeline || timeline.records_by_date.length === 0 ? (
        <div className="text-center py-8 bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
          <Stethoscope className="w-12 h-12 mx-auto text-gray-400 mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No medical records</h3>
          <p className="text-gray-600 mb-4">
            This pet doesn't have any medical records yet.
          </p>
          {canCreateRecords() && (
            <Link
              to={`/pets/${petId}/medical-records/create`}
              className="inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-md transition-colors duration-200"
            >
              <Plus className="w-4 h-4 mr-2" />
              Add First Record
            </Link>
          )}
        </div>
      ) : (
        <div className="space-y-4">
          {displayedRecords.map((record, index) => (
            <div
              key={record.id}
              className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow duration-200"
            >
              <div className="flex items-start justify-between mb-3">
                <div className="flex-1">
                  <div className="flex items-center mb-2">
                    <span className={`inline-flex items-center px-2 py-1 text-xs font-medium rounded-full ${getRecordTypeColor(record.record_type)}`}>
                      {getRecordTypeLabel(record.record_type)}
                    </span>
                    {!record.is_current && (
                      <span className="ml-2 inline-flex items-center px-2 py-1 text-xs font-medium bg-gray-100 text-gray-600 rounded-full">
                        v{record.version}
                      </span>
                    )}
                    {record.follow_up_required && (
                      <Clock className="w-4 h-4 ml-2 text-yellow-500" />
                    )}
                  </div>
                  
                  <h4 className="text-lg font-semibold text-gray-900 mb-1">
                    <Link 
                      to={`/pets/${petId}/medical-records/${record.id}`}
                      className="hover:text-blue-600 transition-colors"
                    >
                      {record.title}
                    </Link>
                  </h4>
                  
                  <div className="flex items-center text-sm text-gray-600 mb-2">
                    <Calendar className="w-4 h-4 mr-1" />
                    <span>{formatDateTime(record.visit_date)}</span>
                    {record.veterinarian_name && (
                      <>
                        <User className="w-4 h-4 ml-4 mr-1" />
                        <span>{record.veterinarian_name}</span>
                      </>
                    )}
                    {record.cost && (
                      <>
                        <DollarSign className="w-4 h-4 ml-4 mr-1" />
                        <span>${record.cost}</span>
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
                  <Link
                    to={`/pets/${petId}/medical-records/${record.id}`}
                    className="inline-flex items-center px-2 py-1 text-xs font-medium text-white bg-blue-600 hover:bg-blue-700 rounded transition-colors duration-200"
                  >
                    <FileText className="w-3 h-3 mr-1" />
                    View
                  </Link>
                  <Link
                    to={`/pets/${petId}/medical-records/history`}
                    className="inline-flex items-center px-2 py-1 text-xs font-medium text-white bg-gray-600 hover:bg-gray-700 rounded transition-colors duration-200"
                  >
                    <History className="w-3 h-3 mr-1" />
                    History
                  </Link>
                  {canEditRecords() && record.is_current && (
                    <Link
                      to={`/pets/${petId}/medical-records/${record.id}/edit`}
                      className="inline-flex items-center px-2 py-1 text-xs font-medium text-white bg-blue-600 hover:bg-blue-700 rounded transition-colors duration-200"
                    >
                      Edit
                    </Link>
                  )}
                </div>
              </div>

              {/* Additional info row */}
              <div className="flex items-center justify-between text-xs text-gray-500 pt-2 border-t border-gray-100">
                <span>
                  {record.days_since_visit === 0 ? 'Today' : 
                   record.days_since_visit === 1 ? '1 day ago' : 
                   `${record.days_since_visit} days ago`}
                </span>
                {record.follow_up_date && (
                  <span>
                    Follow-up: {formatDate(record.follow_up_date)}
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {maxItems && timeline && timeline.records_by_date.length > maxItems && (
        <div className="text-center pt-4">
          <Link
            to={`/pets/${petId}/medical-records`}
            className="text-blue-600 hover:text-blue-700 font-medium"
          >
            View all {timeline.records_by_date.length} medical records →
          </Link>
        </div>
      )}
    </div>
  );
};

export default MedicalRecordsTimeline;
