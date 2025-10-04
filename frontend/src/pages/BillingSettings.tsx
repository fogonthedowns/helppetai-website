import React, { useState, useEffect } from 'react';
import { CreditCard, Plus, Loader, CheckCircle, Trash2 } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { API_BASE_URL } from '../config/api';
import AddPaymentMethodModal from '../components/billing/AddPaymentMethodModal';

interface PaymentMethod {
  id: string;
  brand: string;
  last4: string;
  exp_month: number;
  exp_year: number;
  is_default: boolean;
}

interface CustomerInfo {
  balance_credits_cents: number;
  balance_credits_dollars: number;
  payment_methods: PaymentMethod[];
}

const BillingSettings: React.FC = () => {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [customerInfo, setCustomerInfo] = useState<CustomerInfo | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showAddCardModal, setShowAddCardModal] = useState(false);
  const [deletingCardId, setDeletingCardId] = useState<string | null>(null);
  const [settingDefaultId, setSettingDefaultId] = useState<string | null>(null);

  useEffect(() => {
    if (user?.practice_id) {
      loadCustomerInfo();
    }
  }, [user?.practice_id]);

  const loadCustomerInfo = async () => {
    if (!user?.practice_id) return;

    setLoading(true);
    setError(null);

    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`${API_BASE_URL}/api/v1/stripe/customers/${user.practice_id}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (!response.ok) {
        throw new Error('Failed to load billing information');
      }

      const data = await response.json();
      setCustomerInfo(data.customer);
    } catch (err: any) {
      console.error('Error loading customer info:', err);
      setError(err.message || 'Failed to load billing information');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteCard = async (cardId: string) => {
    if (!user?.practice_id) return;
    if (!window.confirm('Are you sure you want to remove this card?')) return;

    setDeletingCardId(cardId);

    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(
        `${API_BASE_URL}/api/v1/stripe/customers/${user.practice_id}/payment-methods/${cardId}`,
        {
          method: 'DELETE',
          headers: { 'Authorization': `Bearer ${token}` }
        }
      );

      if (!response.ok) {
        throw new Error('Failed to remove card');
      }

      await loadCustomerInfo();
    } catch (err: any) {
      alert(err.message || 'Failed to remove card');
    } finally {
      setDeletingCardId(null);
    }
  };

  const handleSetDefault = async (cardId: string) => {
    if (!user?.practice_id) return;

    setSettingDefaultId(cardId);

    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(
        `${API_BASE_URL}/api/v1/stripe/customers/${user.practice_id}/payment-methods/${cardId}/set-default`,
        {
          method: 'PUT',
          headers: { 'Authorization': `Bearer ${token}` }
        }
      );

      if (!response.ok) {
        throw new Error('Failed to set default card');
      }

      await loadCustomerInfo();
    } catch (err: any) {
      alert(err.message || 'Failed to set default card');
    } finally {
      setSettingDefaultId(null);
    }
  };

  const getCardBrandColor = (brand: string) => {
    const colors: { [key: string]: string } = {
      visa: 'text-blue-600',
      mastercard: 'text-orange-600',
      amex: 'text-teal-600',
      discover: 'text-orange-500',
    };
    return colors[brand.toLowerCase()] || 'text-gray-600';
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <Loader className="w-8 h-8 text-blue-600 animate-spin" />
      </div>
    );
  }

  if (error || !customerInfo) {
    return (
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="max-w-4xl mx-auto px-6">
          <div className="bg-red-50 border border-red-200 rounded-lg p-6">
            <p className="text-red-800">{error || 'No billing information found'}</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <section className="bg-white border-b border-gray-200 py-8">
        <div className="max-w-4xl mx-auto px-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-4">
              <div className="bg-blue-100 p-4 rounded-xl">
                <CreditCard className="w-8 h-8 text-blue-600" />
              </div>
              <div>
                <h1 className="text-3xl font-bold text-gray-900">Billing</h1>
                <p className="text-gray-600 mt-1">Manage your payment methods and credits</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Content */}
      <section className="py-8">
        <div className="max-w-4xl mx-auto px-6 space-y-8">
          {/* Credits Balance */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Account Balance</h2>
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <div className="flex items-center gap-3">
                <CheckCircle className="h-6 w-6 text-green-600" />
                <div>
                  <p className="text-2xl font-bold text-green-900">
                    ${customerInfo.balance_credits_dollars.toFixed(2)}
                  </p>
                  <p className="text-sm text-green-700">Available credits</p>
                </div>
              </div>
            </div>
          </div>

          {/* Payment Methods */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-lg font-semibold text-gray-900">Payment Methods</h2>
              <button
                onClick={() => setShowAddCardModal(true)}
                className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-md text-sm font-medium hover:bg-blue-700"
              >
                <Plus className="w-4 h-4 mr-2" />
                Add Card
              </button>
            </div>

            {customerInfo.payment_methods.length === 0 ? (
              <div className="text-center py-12">
                <CreditCard className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-600 mb-4">No payment methods added yet</p>
                <button
                  onClick={() => setShowAddCardModal(true)}
                  className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-md text-sm font-medium hover:bg-blue-700"
                >
                  <Plus className="w-4 h-4 mr-2" />
                  Add your first card
                </button>
              </div>
            ) : (
              <div className="grid gap-4 md:grid-cols-2">
                {customerInfo.payment_methods.map((card) => (
                  <div
                    key={card.id}
                    className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow duration-200"
                  >
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex items-center gap-3">
                        <CreditCard className={`w-8 h-8 ${getCardBrandColor(card.brand)}`} />
                        <div>
                          <p className="font-medium text-gray-900 capitalize">{card.brand}</p>
                          <p className="text-sm text-gray-600">•••• {card.last4}</p>
                          <p className="text-xs text-gray-500">
                            Expires {card.exp_month}/{card.exp_year}
                          </p>
                        </div>
                      </div>
                    </div>

                    {card.is_default && (
                      <div className="mb-3">
                        <span className="inline-flex items-center px-2 py-1 text-xs font-medium bg-green-100 text-green-800 rounded-full">
                          Default
                        </span>
                      </div>
                    )}

                    <div className="flex gap-2 mt-3">
                      {!card.is_default && (
                        <button
                          onClick={() => handleSetDefault(card.id)}
                          disabled={settingDefaultId === card.id}
                          className="flex-1 px-3 py-1.5 text-xs font-medium text-blue-600 border border-blue-600 rounded hover:bg-blue-50 disabled:opacity-50"
                        >
                          {settingDefaultId === card.id ? (
                            <Loader className="w-3 h-3 animate-spin mx-auto" />
                          ) : (
                            'Set as default'
                          )}
                        </button>
                      )}
                      <button
                        onClick={() => handleDeleteCard(card.id)}
                        disabled={deletingCardId === card.id}
                        className="px-3 py-1.5 text-xs font-medium text-red-600 border border-red-600 rounded hover:bg-red-50 disabled:opacity-50"
                      >
                        {deletingCardId === card.id ? (
                          <Loader className="w-3 h-3 animate-spin" />
                        ) : (
                          <Trash2 className="w-3 h-3" />
                        )}
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </section>

      {/* Add Card Modal */}
      <AddPaymentMethodModal
        isOpen={showAddCardModal}
        onClose={() => setShowAddCardModal(false)}
        onSuccess={() => {
          setShowAddCardModal(false);
          loadCustomerInfo();
        }}
      />
    </div>
  );
};

export default BillingSettings;

