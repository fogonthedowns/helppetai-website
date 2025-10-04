import React, { useState, useEffect } from 'react';
import { Plus, Loader, CheckCircle } from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import { API_BASE_URL } from '../../config/api';
import AddPaymentMethodPanel from '../billing/AddPaymentMethodPanel';

interface PaymentMethod {
  id: string;
  brand: string;
  last4: string;
  exp_month: number;
  exp_year: number;
  is_default: boolean;
}

const BillingSettings: React.FC = () => {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [paymentMethods, setPaymentMethods] = useState<PaymentMethod[]>([]);
  const [showAddCardPanel, setShowAddCardPanel] = useState(false);
  const [deletingCardId, setDeletingCardId] = useState<string | null>(null);
  const [settingDefaultId, setSettingDefaultId] = useState<string | null>(null);

  useEffect(() => {
    if (user?.practice_id) {
      loadPaymentMethods();
    }
  }, [user?.practice_id]);

  const loadPaymentMethods = async () => {
    if (!user?.practice_id) return;

    setLoading(true);

    try {
      const token = localStorage.getItem('access_token');
      
      // Fetch payment methods
      const pmResponse = await fetch(`${API_BASE_URL}/api/v1/stripe/customers/${user.practice_id}/payment-methods`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (pmResponse.ok) {
        const pmData = await pmResponse.json();
        setPaymentMethods(pmData.payment_methods || []);
      }
    } catch (err) {
      console.error('Error loading payment methods:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteCard = async (cardId: string) => {
    if (!user?.practice_id) return;
    if (!window.confirm('Remove this card?')) return;

    setDeletingCardId(cardId);

    try {
      const token = localStorage.getItem('access_token');
      await fetch(`${API_BASE_URL}/api/v1/stripe/customers/${user.practice_id}/payment-methods/${cardId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      loadPaymentMethods();
    } finally {
      setDeletingCardId(null);
    }
  };

  const handleSetDefault = async (cardId: string) => {
    if (!user?.practice_id) return;

    setSettingDefaultId(cardId);

    try {
      const token = localStorage.getItem('access_token');
      await fetch(`${API_BASE_URL}/api/v1/stripe/customers/${user.practice_id}/payment-methods/${cardId}/set-default`, {
        method: 'PUT',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      loadPaymentMethods();
    } finally {
      setSettingDefaultId(null);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader className="w-8 h-8 text-blue-600 animate-spin" />
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-8 py-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold text-gray-900">Billing</h1>
            <p className="text-sm text-gray-600 mt-1">Manage your payment methods</p>
          </div>
          <button
            onClick={() => setShowAddCardPanel(true)}
            className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-md text-sm font-medium hover:bg-blue-700"
          >
            <Plus className="w-4 h-4 mr-2" />
            Add Card
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto bg-gray-50">
        <div className="max-w-4xl mx-auto px-8 py-6">
          {paymentMethods.length > 0 ? (
            <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
              <table className="min-w-full">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Card</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Expires</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {paymentMethods.map((card) => (
                    <tr key={card.id} className="hover:bg-gray-50 transition-colors">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center gap-3">
                          <div className="text-sm font-medium text-gray-900 capitalize">{card.brand}</div>
                          <div className="text-sm text-gray-600">•••• {card.last4}</div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                        {card.exp_month}/{card.exp_year}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {card.is_default && (
                          <span className="inline-flex items-center px-2 py-1 text-xs font-medium bg-green-100 text-green-800 rounded-full">
                            Default
                          </span>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm space-x-2">
                        {!card.is_default && (
                          <button
                            onClick={() => handleSetDefault(card.id)}
                            disabled={settingDefaultId === card.id}
                            className="text-blue-600 hover:text-blue-900 font-medium disabled:opacity-50"
                          >
                            Set Default
                          </button>
                        )}
                        <button
                          onClick={() => handleDeleteCard(card.id)}
                          disabled={deletingCardId === card.id}
                          className="text-red-600 hover:text-red-900 font-medium disabled:opacity-50"
                        >
                          Remove
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="bg-white rounded-lg border border-gray-200 p-12 text-center">
              <p className="text-gray-600 mb-4">No payment methods added yet</p>
              <button
                onClick={() => setShowAddCardPanel(true)}
                className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-md text-sm font-medium hover:bg-blue-700"
              >
                <Plus className="w-4 h-4 mr-2" />
                Add your first card
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Add Card Panel */}
      <AddPaymentMethodPanel
        isOpen={showAddCardPanel}
        onClose={() => setShowAddCardPanel(false)}
        onSuccess={() => {
          setShowAddCardPanel(false);
          loadPaymentMethods();
        }}
        hasExistingCards={paymentMethods.length > 0}
      />
    </div>
  );
};

export default BillingSettings;

