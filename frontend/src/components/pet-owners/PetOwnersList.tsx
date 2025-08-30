import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Users, Plus, MapPin, Phone, Mail, User } from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import { API_ENDPOINTS } from '../../config/api';
import '../../utils/authUtils'; // Import to ensure fetch interceptor is set up

interface PetOwner {
  uuid: string;
  user_id?: string;  // Optional user reference
  full_name: string;
  email?: string;
  phone?: string;
  emergency_contact?: string;
  secondary_phone?: string;
  address?: string;
  preferred_communication: 'email' | 'sms' | 'phone';
  notifications_enabled: boolean;
  created_at: string;
  updated_at: string;
}

const PetOwnersList = () => {
  const [petOwners, setPetOwners] = useState<PetOwner[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { isAuthenticated, user } = useAuth();

  const isAdmin = user?.role === 'ADMIN';
  const canCreatePetOwners = user?.role === 'ADMIN' || user?.role === 'VET_STAFF';
  const canViewPetOwners = user?.role === 'ADMIN' || user?.role === 'VET_STAFF';
  const canEditPetOwners = user?.role === 'ADMIN' || user?.role === 'VET_STAFF';

  useEffect(() => {
    if (canViewPetOwners) {
      fetchPetOwners();
    } else {
      setError('Admin or Vet Staff access required');
      setLoading(false);
    }
  }, [canViewPetOwners]);

  const fetchPetOwners = async () => {
    try {
      const response = await fetch(API_ENDPOINTS.PET_OWNERS.LIST);
      if (!response.ok) {
        throw new Error('Failed to fetch pet owners');
      }
      const data = await response.json();
      setPetOwners(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load pet owners');
    } finally {
      setLoading(false);
    }
  };

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900 mb-4">Please log in</h1>
          <p className="text-gray-600 mb-6">You need to be logged in to view pet owners.</p>
          <Link
            to="/login"
            className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors"
          >
            Login
          </Link>
        </div>
      </div>
    );
  }

  if (!canViewPetOwners) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900 mb-4">Access Denied</h1>
          <p className="text-gray-600 mb-6">Admin or Vet Staff access required to view pet owners list.</p>
          <Link
            to="/"
            className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors"
          >
            Go Home
          </Link>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading pet owners...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="bg-red-50 border border-red-200 rounded-md p-4 mb-4">
            <div className="text-red-800 text-sm">{error}</div>
          </div>
          <button
            onClick={fetchPetOwners}
            className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <section className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-6 py-8">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="bg-blue-100 p-3 rounded-xl">
                <Users className="w-8 h-8 text-blue-600" />
              </div>
              <div>
                <h1 className="text-5xl font-bold text-gray-900 mb-2" style={{
                  fontFamily: 'Calibre, ui-sans-serif, system-ui, -apple-system, "system-ui", "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans", sans-serif'
                }}>
                  Pet Owners
                </h1>
                <p className="text-xl text-gray-600">
                  Manage pet owner profiles and information
                </p>
              </div>
            </div>
            
            {canCreatePetOwners && (
              <Link
                to="/pet_owners/new"
                className="bg-blue-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-blue-700 transition-colors flex items-center space-x-2"
              >
                <Plus className="w-5 h-5" />
                <span>Create Pet Owner</span>
              </Link>
            )}
          </div>
        </div>
      </section>

      {/* Pet Owners Table */}
      <section className="py-16">
        <div className="max-w-7xl mx-auto px-6">
          {petOwners.length === 0 ? (
            <div className="text-center py-12">
              <Users className="w-16 h-16 text-gray-300 mx-auto mb-4" />
              <h3 className="text-xl font-semibold text-gray-900 mb-2">No Pet Owners Found</h3>
              <p className="text-gray-600 mb-6">There are no pet owners to display.</p>
            </div>
          ) : (
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Owner Name
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Email
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Emergency Contact
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Communication
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {petOwners.map((petOwner) => (
                    <PetOwnerRow key={petOwner.uuid} petOwner={petOwner} canEdit={canEditPetOwners} />
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </section>
    </div>
  );
};

interface PetOwnerRowProps {
  petOwner: PetOwner;
  canEdit: boolean;
}

const PetOwnerRow: React.FC<PetOwnerRowProps> = ({ petOwner, canEdit }) => {
  return (
    <tr className="hover:bg-gray-50">
      <td className="px-6 py-4 whitespace-nowrap">
        <div className="flex items-center">
          <div className="bg-blue-100 p-2 rounded-lg mr-3">
            <User className="w-4 h-4 text-blue-600" />
          </div>
          <div>
            <div className="text-sm font-medium text-gray-900">
              {petOwner.full_name}
            </div>
            <div className="text-sm text-gray-500">ID: {petOwner.uuid.slice(0, 8)}...</div>
          </div>
        </div>
      </td>
      <td className="px-6 py-4 whitespace-nowrap">
        <div className="text-sm text-gray-900">{petOwner.email || 'N/A'}</div>
      </td>
      <td className="px-6 py-4 whitespace-nowrap">
        <div className="text-sm text-gray-900">
          {petOwner.emergency_contact || 'Not provided'}
        </div>
      </td>
      <td className="px-6 py-4 whitespace-nowrap">
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 capitalize">
          {petOwner.preferred_communication}
        </span>
      </td>
      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium space-x-3">
        <Link
          to={`/pet_owners/${petOwner.uuid}`}
          className="inline-flex items-center px-3 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-md transition-colors duration-200"
        >
          View
        </Link>
        {canEdit && (
          <Link
            to={`/pet_owners/${petOwner.uuid}/edit`}
            className="inline-flex items-center px-3 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-md transition-colors duration-200"
          >
            Edit
          </Link>
        )}
      </td>
    </tr>
  );
};

export default PetOwnersList;
