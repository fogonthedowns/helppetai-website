import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { 
  Users, 
  ArrowLeft, 
  MapPin, 
  Phone, 
  Mail, 
  Calendar,
  Edit,
  Trash2,
  AlertCircle,
  User
} from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import { API_ENDPOINTS } from '../../config/api';
import PetsList from '../pets/PetsList';
import AppointmentsList from '../appointments/AppointmentsList';
import Breadcrumb, { BreadcrumbItem } from '../common/Breadcrumb';

interface PetOwner {
  uuid: string;
  user_id?: string;  // Optional user reference
  full_name: string;
  email?: string;
  phone?: string;
  emergency_contact?: string;
  secondary_phone?: string;
  address?: string;
  preferred_communication: string;
  notifications_enabled: boolean;
  created_at: string;
  updated_at: string;
}

const PetOwnerDetail = () => {
  const { uuid } = useParams<{ uuid: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();

  const [petOwner, setPetOwner] = useState<PetOwner | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deleting, setDeleting] = useState(false);

  const isAdmin = user?.role === 'ADMIN';

  useEffect(() => {
    if (uuid) {
      fetchPetOwner();
    }
  }, [uuid]);

  const fetchPetOwner = async () => {
    if (!uuid) return;
    
    setLoading(true);
    try {
      const response = await fetch(API_ENDPOINTS.PET_OWNERS.GET(uuid));
      if (!response.ok) {
        if (response.status === 403) {
          throw new Error('Access denied. You can only view your own pet owner profile.');
        }
        if (response.status === 404) {
          throw new Error('Pet owner not found');
        }
        throw new Error('Failed to fetch pet owner');
      }
      const data = await response.json();
      setPetOwner(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load pet owner');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!petOwner || !isAdmin) return;
    
    if (!window.confirm('Are you sure you want to delete this pet owner? This action cannot be undone.')) {
      return;
    }

    setDeleting(true);
    try {
      const response = await fetch(API_ENDPOINTS.PET_OWNERS.DELETE(petOwner.uuid), {
        method: 'DELETE',
      });
      
      if (!response.ok) {
        throw new Error('Failed to delete pet owner');
      }
      
      navigate('/pet_owners');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete pet owner');
    } finally {
      setDeleting(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading pet owner...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center max-w-md mx-auto">
          <div className="bg-red-50 p-8 rounded-lg border border-red-200">
            <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
            <h2 className="text-xl font-semibold text-red-800 mb-2">Pet Owner Not Found</h2>
            <p className="text-red-600 mb-6">{error}</p>
          </div>
        </div>
      </div>
    );
  }

  if (!petOwner) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <Users className="w-16 h-16 text-gray-300 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Pet Owner Not Found</h2>
          <p className="text-gray-600 mb-6">Pet owner not found</p>
        </div>
      </div>
    );
  }

  const canEdit = isAdmin; // Users can edit their own profile, but we need to check if this is their profile
  const canDelete = isAdmin;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <section className="bg-white border-b border-gray-200">
        <div className="max-w-4xl mx-auto px-6 py-8">
          {/* Breadcrumbs */}
          <Breadcrumb 
            items={[
              { label: 'Pet Owners', href: '/pet_owners' },
              { label: petOwner.full_name, isActive: true }
            ]}
            className="mb-6"
          />
          
          <div className="flex items-center justify-between mb-6">
            <div className="flex space-x-3">
              {canEdit && (
                <Link
                  to={`/pet_owners/${petOwner.uuid}/edit`}
                  className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors flex items-center space-x-2"
                >
                  <Edit className="w-4 h-4" />
                  <span>Edit</span>
                </Link>
              )}
              
              {canDelete && (
                <button
                  onClick={handleDelete}
                  disabled={deleting}
                  className="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 transition-colors flex items-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <Trash2 className="w-4 h-4" />
                  <span>{deleting ? 'Deleting...' : 'Delete'}</span>
                </button>
              )}
            </div>
          </div>

          <div className="flex items-center space-x-4">
            <div className="bg-blue-100 p-4 rounded-xl">
              <User className="w-8 h-8 text-blue-600" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-gray-900">
                {petOwner.full_name}
              </h1>
              {petOwner.phone && (
                <p className="text-gray-600 mt-1 flex items-center">
                  <Phone className="w-4 h-4 mr-1" />
                  {petOwner.phone}
                </p>
              )}
            </div>
          </div>
        </div>
      </section>

      {/* Content */}
      <section className="py-8">
        <div className="max-w-4xl mx-auto px-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* Contact Information */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-6 flex items-center">
                <Phone className="w-5 h-5 mr-2 text-gray-600" />
                Contact Information
              </h2>
              
              <div className="space-y-4">
                {petOwner.emergency_contact && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Emergency Contact
                    </label>
                    <div className="flex items-center text-gray-900">
                      <Phone className="w-4 h-4 mr-2 text-gray-400" />
                      {petOwner.emergency_contact}
                    </div>
                  </div>
                )}
                
                {petOwner.secondary_phone && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Secondary Phone
                    </label>
                    <div className="flex items-center text-gray-900">
                      <Phone className="w-4 h-4 mr-2 text-gray-400" />
                      {petOwner.secondary_phone}
                    </div>
                  </div>
                )}

                {petOwner.address && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Address
                    </label>
                    <div className="flex items-start text-gray-900">
                      <MapPin className="w-4 h-4 mr-2 text-gray-400 mt-1 flex-shrink-0" />
                      <span>{petOwner.address}</span>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Preferences */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-6 flex items-center">
                <Mail className="w-5 h-5 mr-2 text-gray-600" />
                Preferences
              </h2>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Preferred Communication
                  </label>
                  <div className="flex items-center text-gray-900">
                    <Mail className="w-4 h-4 mr-2 text-gray-400" />
                    <span className="capitalize">{petOwner.preferred_communication}</span>
                  </div>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Notifications
                  </label>
                  <div className="flex items-center text-gray-900">
                    <div className={`w-3 h-3 rounded-full mr-2 ${
                      petOwner.notifications_enabled ? 'bg-green-500' : 'bg-red-500'
                    }`} />
                    <span>{petOwner.notifications_enabled ? 'Enabled' : 'Disabled'}</span>
                  </div>
                </div>
              </div>
            </div>

            {/* System Information */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 lg:col-span-2">
              <h2 className="text-xl font-semibold text-gray-900 mb-6 flex items-center">
                <Calendar className="w-5 h-5 mr-2 text-gray-600" />
                System Information
              </h2>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    User ID
                  </label>
                  <p className="text-gray-900 font-mono text-sm">{petOwner.user_id}</p>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Created
                  </label>
                  <p className="text-gray-900">
                    {new Date(petOwner.created_at).toLocaleDateString()}
                  </p>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Last Updated
                  </label>
                  <p className="text-gray-900">
                    {new Date(petOwner.updated_at).toLocaleDateString()}
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Pets Section */}
          <div className="mt-8">
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <PetsList 
                ownerUuid={petOwner.uuid} 
                petOwner={{
                  id: petOwner.uuid,
                  user_id: petOwner.user_id,
                  full_name: petOwner.full_name
                }}
              />
            </div>
          </div>

          {/* Scheduled Appointments Section */}
          <div className="mt-8">
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <AppointmentsList 
                petOwnerId={petOwner.uuid}
                showHeader={true}
                maxItems={5}
                showCreateButton={true}
              />
            </div>
          </div>
        </div>
      </section>
    </div>
  );
};

export default PetOwnerDetail;
