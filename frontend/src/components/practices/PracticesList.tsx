import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Building2, Plus, MapPin, Phone, Mail, Users } from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import { API_ENDPOINTS } from '../../config/api';

interface Practice {
  uuid: string;
  name: string;
  admin_user_id: string;
  phone?: string;
  email?: string;
  address?: string;
  license_number?: string;
  specialties: string[];
  created_at: string;
  updated_at: string;
  is_active: boolean;
}

const PracticesList = () => {
  const [practices, setPractices] = useState<Practice[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { isAuthenticated, user } = useAuth();

  const isAdmin = user?.role === 'ADMIN';

  useEffect(() => {
    fetchPractices();
  }, []);

  const fetchPractices = async () => {
    try {
      const response = await fetch(API_ENDPOINTS.PRACTICES.LIST);
      if (!response.ok) {
        throw new Error('Failed to fetch practices');
      }
      const data = await response.json();
      setPractices(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load practices');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="w-8 h-8 border-2 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">Loading practices...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <Building2 className="w-8 h-8 text-red-600" />
          </div>
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Error Loading Practices</h2>
          <p className="text-gray-600 mb-4">{error}</p>
          <button
            onClick={fetchPractices}
            className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header Section */}
      <section className="bg-gradient-to-br from-blue-50 to-indigo-50 py-16">
        <div className="max-w-7xl mx-auto px-6">
          <div className="flex justify-between items-center">
            <div>
              <div className="flex items-center mb-6">
                <div className="w-16 h-16 bg-blue-600 rounded-2xl flex items-center justify-center mr-4">
                  <Building2 className="w-8 h-8 text-white" />
                </div>
                <div>
                  <h1 className="text-5xl font-bold text-gray-900 mb-2" style={{
                    fontFamily: 'Calibre, ui-sans-serif, system-ui, -apple-system, "system-ui", "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans", sans-serif'
                  }}>
                    Veterinary Practices
                  </h1>
                  <p className="text-xl text-gray-600">
                    Find qualified veterinary professionals near you
                  </p>
                </div>
              </div>
            </div>
            
            {isAdmin && (
              <Link
                to="/practices/new"
                className="bg-blue-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-blue-700 transition-colors flex items-center space-x-2"
              >
                <Plus className="w-5 h-5" />
                <span>Add Practice</span>
              </Link>
            )}
          </div>
        </div>
      </section>

      {/* Practices Grid */}
      <section className="py-16">
        <div className="max-w-7xl mx-auto px-6">
          {practices.length === 0 ? (
            <div className="text-center py-16">
              <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <Building2 className="w-8 h-8 text-gray-400" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">No Practices Found</h3>
              <p className="text-gray-600 mb-6">There are no veterinary practices to display.</p>

            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {practices.map((practice) => (
                <PracticeCard key={practice.uuid} practice={practice} isAdmin={isAdmin} />
              ))}
            </div>
          )}
        </div>
      </section>
    </div>
  );
};

interface PracticeCardProps {
  practice: Practice;
  isAdmin: boolean;
}

const PracticeCard: React.FC<PracticeCardProps> = ({ practice, isAdmin }) => {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 hover:shadow-md transition-shadow">
      <div className="p-6">
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center">
            <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mr-3">
              <Building2 className="w-6 h-6 text-blue-600" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-gray-900">{practice.name}</h3>
              {practice.specialties.length > 0 && (
                <p className="text-sm text-gray-600">{practice.specialties.join(', ')}</p>
              )}
            </div>
          </div>
        </div>

        <div className="space-y-2 mb-4">
          {practice.address && (
            <div className="flex items-center text-sm text-gray-600">
              <MapPin className="w-4 h-4 mr-2 flex-shrink-0" />
              <span>{practice.address}</span>
            </div>
          )}
          
          {practice.phone && (
            <div className="flex items-center text-sm text-gray-600">
              <Phone className="w-4 h-4 mr-2 flex-shrink-0" />
              <span>{practice.phone}</span>
            </div>
          )}
          
          {practice.email && (
            <div className="flex items-center text-sm text-gray-600">
              <Mail className="w-4 h-4 mr-2 flex-shrink-0" />
              <span>{practice.email}</span>
            </div>
          )}
        </div>

        <div className="flex items-center justify-between pt-4 border-t border-gray-100">
          <Link
            to={`/practices/${practice.uuid}`}
            className="text-blue-600 hover:text-blue-700 font-medium text-sm"
          >
            View Details
          </Link>
          
          {isAdmin && (
            <Link
              to={`/practices/${practice.uuid}/edit`}
              className="bg-gray-100 text-gray-700 px-3 py-1 rounded-md text-sm hover:bg-gray-200 transition-colors"
            >
              Edit
            </Link>
          )}
        </div>
      </div>
    </div>
  );
};

export default PracticesList;
