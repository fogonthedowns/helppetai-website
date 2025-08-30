import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { 
  ArrowLeft, 
  Edit, 
  Trash2, 
  Calendar, 
  User, 
  Stethoscope, 
  DollarSign, 
  Weight, 
  Thermometer,
  Clock,
  AlertTriangle,
  FileText,
  Building
} from 'lucide-react';
import { 
  MedicalRecordWithRelations,
  MEDICAL_RECORD_TYPE_LABELS,
  MEDICAL_RECORD_TYPE_COLORS
} from '../../types/medicalRecord';
import { API_ENDPOINTS } from '../../config/api';
import { useAuth } from '../../contexts/AuthContext';
import { getAuthHeaders } from '../../utils/authUtils';

const MedicalRecordDetail: React.FC = () => {
  const { petId, recordId } = useParams<{ petId: string; recordId: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();

  const [record, setRecord] = useState<MedicalRecordWithRelations | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);

  useEffect(() => {
    if (recordId) {
      fetchRecord();
    }
  }, [recordId]);

  const fetchRecord = async () => {
    if (!recordId) return;

    try {
      setLoading(true);
      setError(null);

      const response = await fetch(API_ENDPOINTS.MEDICAL_RECORDS.GET(recordId), {
        headers: getAuthHeaders()
      });
      
      if (!response.ok) {
        if (response.status === 403) {
          throw new Error('Access denied to this medical record');
        }
        if (response.status === 404) {
          throw new Error('Medical record not found');
        }
        throw new Error('Failed to fetch medical record');
      }

      const recordData = await response.json();
      setRecord(recordData);
    } catch (err) {
      console.error('Error fetching medical record:', err);
      setError(err instanceof Error ? err.message : 'Failed to load medical record');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!recordId || isDeleting) return;

    try {
      setIsDeleting(true);
      
      const response = await fetch(API_ENDPOINTS.MEDICAL_RECORDS.DELETE(recordId), {
        method: 'DELETE',
        headers: getAuthHeaders()
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Failed to delete medical record');
      }

      // Navigate back to pet detail page
      navigate(`/pets/${petId}`);
    } catch (err) {
      console.error('Error deleting medical record:', err);
      setError(err instanceof Error ? err.message : 'Failed to delete medical record');
    } finally {
      setIsDeleting(false);
      setShowDeleteConfirm(false);
    }
  };

  const canEdit = () => {
    if (!record || !user) return false;
    return user.role === 'ADMIN' || 
           (user.role === 'VET_STAFF' && record.created_by_user_id === user.id);
  };

  const canDelete = () => {
    return user?.role === 'ADMIN';
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  const formatDateTime = (dateString: string) => {
    return new Date(dateString).toLocaleString('en-US', {
      year: 'numeric',
      month: 'long',
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
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span className="ml-2 text-gray-600">Loading medical record...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <AlertTriangle className="w-12 h-12 mx-auto text-red-500 mb-4" />
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Error</h2>
          <p className="text-gray-600 mb-4">{error}</p>
          <button
            onClick={() => navigate(`/pets/${petId}`)}
            className="text-blue-600 hover:text-blue-700 font-medium"
          >
            ← Back to Pet
          </button>
        </div>
      </div>
    );
  }

  if (!record) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <FileText className="w-12 h-12 mx-auto text-gray-400 mb-4" />
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Record Not Found</h2>
          <p className="text-gray-600 mb-4">The requested medical record could not be found.</p>
          <button
            onClick={() => navigate(`/pets/${petId}`)}
            className="text-blue-600 hover:text-blue-700 font-medium"
          >
            ← Back to Pet
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <button
            onClick={() => navigate(`/pets/${petId}`)}
            className="inline-flex items-center text-gray-600 hover:text-gray-900 mb-4"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to {record.pet.name}
          </button>
          
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <div className="flex items-center mb-2">
                <span className={`inline-flex items-center px-3 py-1 text-sm font-medium rounded-full ${getRecordTypeColor(record.record_type)}`}>
                  {getRecordTypeLabel(record.record_type)}
                </span>
                {!record.is_current && (
                  <span className="ml-3 inline-flex items-center px-2 py-1 text-xs font-medium bg-gray-100 text-gray-600 rounded-full">
                    Version {record.version}
                  </span>
                )}
                {record.follow_up_required && record.is_follow_up_due && (
                  <span className="ml-3 inline-flex items-center px-2 py-1 text-xs font-medium bg-yellow-100 text-yellow-800 rounded-full">
                    <Clock className="w-3 h-3 mr-1" />
                    Follow-up Due
                  </span>
                )}
              </div>
              
              <h1 className="text-3xl font-bold text-gray-900 mb-2">{record.title}</h1>
              
              <div className="flex items-center text-gray-600 space-x-6">
                <div className="flex items-center">
                  <Calendar className="w-4 h-4 mr-2" />
                  <span>{formatDateTime(record.visit_date)}</span>
                </div>
                <div className="flex items-center">
                  <Stethoscope className="w-4 h-4 mr-2" />
                  <Link 
                    to={`/pets/${record.pet_id}`}
                    className="text-blue-600 hover:text-blue-700 font-medium"
                  >
                    {record.pet.name} ({record.pet.species})
                  </Link>
                </div>
              </div>
            </div>

            <div className="flex items-center space-x-3 ml-6">
              {canEdit() && record.is_current && (
                <Link
                  to={`/pets/${petId}/medical-records/${record.id}/edit`}
                  className="inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-md transition-colors duration-200"
                >
                  <Edit className="w-4 h-4 mr-2" />
                  Edit
                </Link>
              )}
              {canDelete() && (
                <button
                  onClick={() => setShowDeleteConfirm(true)}
                  className="inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-red-600 hover:bg-red-700 rounded-md transition-colors duration-200"
                >
                  <Trash2 className="w-4 h-4 mr-2" />
                  Delete
                </button>
              )}
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Main Content */}
          <div className="lg:col-span-2 space-y-6">
            {/* Description */}
            {record.description && (
              <div className="bg-white shadow-sm rounded-lg p-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">Description</h2>
                <p className="text-gray-700 whitespace-pre-wrap">{record.description}</p>
              </div>
            )}

            {/* Medical Details */}
            <div className="bg-white shadow-sm rounded-lg p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-6">Medical Details</h2>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Vital Signs */}
                {(record.weight || record.temperature) && (
                  <div className="md:col-span-2">
                    <h3 className="text-md font-medium text-gray-900 mb-3">Vital Signs</h3>
                    <div className="grid grid-cols-2 gap-4">
                      {record.weight && (
                        <div className="flex items-center">
                          <Weight className="w-4 h-4 text-gray-500 mr-2" />
                          <span className="text-sm text-gray-600">Weight:</span>
                          <span className="ml-2 font-medium">{record.weight} lbs</span>
                        </div>
                      )}
                      {record.temperature && (
                        <div className="flex items-center">
                          <Thermometer className="w-4 h-4 text-gray-500 mr-2" />
                          <span className="text-sm text-gray-600">Temperature:</span>
                          <span className="ml-2 font-medium">{record.temperature}°F</span>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* Diagnosis */}
                {record.diagnosis && (
                  <div className="md:col-span-2">
                    <h3 className="text-md font-medium text-gray-900 mb-2">Diagnosis</h3>
                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                      <p className="text-gray-700 whitespace-pre-wrap">{record.diagnosis}</p>
                    </div>
                  </div>
                )}

                {/* Treatment */}
                {record.treatment && (
                  <div className="md:col-span-2">
                    <h3 className="text-md font-medium text-gray-900 mb-2">Treatment</h3>
                    <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                      <p className="text-gray-700 whitespace-pre-wrap">{record.treatment}</p>
                    </div>
                  </div>
                )}

                {/* Medications */}
                {record.medications && (
                  <div className="md:col-span-2">
                    <h3 className="text-md font-medium text-gray-900 mb-2">Medications</h3>
                    <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                      <p className="text-gray-700 whitespace-pre-wrap">{record.medications}</p>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Medical Data (Type-specific fields) */}
            {record.medical_data && Object.keys(record.medical_data).length > 0 && (
              <div className="bg-white shadow-sm rounded-lg p-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-6">
                  {getRecordTypeLabel(record.record_type)} Details
                </h2>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {Object.entries(record.medical_data).map(([field, value]) => (
                    value && (
                      <div key={field}>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          {field.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                        </label>
                        <p className="text-gray-900">{value as string}</p>
                      </div>
                    )
                  ))}
                </div>
              </div>
            )}

            {/* Follow-up */}
            {record.follow_up_required && (
              <div className="bg-white shadow-sm rounded-lg p-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">Follow-up</h2>
                <div className={`p-4 rounded-lg border ${record.is_follow_up_due ? 'bg-yellow-50 border-yellow-200' : 'bg-green-50 border-green-200'}`}>
                  <div className="flex items-center">
                    <Clock className={`w-5 h-5 mr-3 ${record.is_follow_up_due ? 'text-yellow-600' : 'text-green-600'}`} />
                    <div>
                      <p className={`font-medium ${record.is_follow_up_due ? 'text-yellow-800' : 'text-green-800'}`}>
                        {record.is_follow_up_due ? 'Follow-up Due' : 'Follow-up Scheduled'}
                      </p>
                      {record.follow_up_date && (
                        <p className={`text-sm ${record.is_follow_up_due ? 'text-yellow-700' : 'text-green-700'}`}>
                          {formatDateTime(record.follow_up_date)}
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Visit Information */}
            <div className="bg-white shadow-sm rounded-lg p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Visit Information</h3>
              <div className="space-y-4">
                {record.veterinarian_name && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Veterinarian</label>
                    <div className="flex items-center">
                      <User className="w-4 h-4 text-gray-500 mr-2" />
                      <span className="text-gray-900">{record.veterinarian_name}</span>
                    </div>
                  </div>
                )}

                {record.clinic_name && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Clinic/Hospital</label>
                    <div className="flex items-center">
                      <Building className="w-4 h-4 text-gray-500 mr-2" />
                      <span className="text-gray-900">{record.clinic_name}</span>
                    </div>
                  </div>
                )}

                {record.cost && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Cost</label>
                    <div className="flex items-center">
                      <DollarSign className="w-4 h-4 text-gray-500 mr-2" />
                      <span className="text-gray-900 font-medium">${record.cost}</span>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Record Information */}
            <div className="bg-white shadow-sm rounded-lg p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Record Information</h3>
              <div className="space-y-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Created By</label>
                  <p className="text-gray-900">{record.created_by.full_name || record.created_by.email}</p>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Created</label>
                  <p className="text-gray-600 text-sm">{formatDateTime(record.created_at)}</p>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Last Updated</label>
                  <p className="text-gray-600 text-sm">{formatDateTime(record.updated_at)}</p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Version</label>
                  <p className="text-gray-600 text-sm">
                    {record.version} {record.is_current ? '(Current)' : '(Historical)'}
                  </p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Days Since Visit</label>
                  <p className="text-gray-600 text-sm">
                    {record.days_since_visit === 0 ? 'Today' : 
                     record.days_since_visit === 1 ? '1 day ago' : 
                     `${record.days_since_visit} days ago`}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Delete Confirmation Modal */}
        {showDeleteConfirm && (
          <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
            <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
              <div className="mt-3">
                <div className="flex items-center mb-4">
                  <div className="mx-auto flex-shrink-0 flex items-center justify-center h-12 w-12 rounded-full bg-red-100">
                    <Trash2 className="h-6 w-6 text-red-600" />
                  </div>
                </div>
                
                <h3 className="text-lg font-medium text-gray-900 text-center mb-2">
                  Delete Medical Record
                </h3>
                
                <p className="text-gray-600 text-center mb-6">
                  Are you sure you want to delete this medical record? This action cannot be undone.
                </p>
                
                <div className="flex justify-center space-x-3">
                  <button
                    onClick={() => setShowDeleteConfirm(false)}
                    disabled={isDeleting}
                    className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleDelete}
                    disabled={isDeleting}
                    className="px-4 py-2 text-sm font-medium text-white bg-red-600 hover:bg-red-700 rounded-md disabled:opacity-50"
                  >
                    {isDeleting ? 'Deleting...' : 'Delete Record'}
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default MedicalRecordDetail;