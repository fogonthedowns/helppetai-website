import React, { useState } from 'react';
import { loadStripe } from '@stripe/stripe-js';
import { Elements, CardElement, useStripe, useElements } from '@stripe/react-stripe-js';
import { X, CheckCircle, Loader } from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import { API_BASE_URL } from '../../config/api';

// Initialize Stripe
let stripePromise: Promise<any> | null = null;

const getStripe = async () => {
  if (!stripePromise) {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/stripe/config`);
      const { publishable_key } = await response.json();
      stripePromise = loadStripe(publishable_key);
    } catch (error) {
      console.error('Failed to load Stripe config:', error);
    }
  }
  return stripePromise;
};

interface AddPaymentMethodPanelProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  hasExistingCards?: boolean;
}

const CardForm: React.FC<{ onClose: () => void; onSuccess: () => void; hasExistingCards?: boolean }> = ({ onClose, onSuccess, hasExistingCards }) => {
  const stripe = useStripe();
  const elements = useElements();
  const { user } = useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!stripe || !elements || !user?.practice_id) {
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const token = localStorage.getItem('access_token');
      
      // Ensure Stripe customer exists
      const customerCheckResponse = await fetch(`${API_BASE_URL}/api/v1/stripe/customers/${user.practice_id}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (customerCheckResponse.ok) {
        const customerData = await customerCheckResponse.json();
        if (!customerData.customer) {
          const createCustomerResponse = await fetch(`${API_BASE_URL}/api/v1/stripe/customers`, {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              practice_id: user.practice_id,
              email: user.email || '',
              practice_name: 'Practice',
            }),
          });

          if (!createCustomerResponse.ok) {
            throw new Error('Failed to create Stripe customer');
          }
        }
      }
      
      // Create setup intent
      const setupResponse = await fetch(`${API_BASE_URL}/api/v1/stripe/customers/${user.practice_id}/setup-intent`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!setupResponse.ok) {
        throw new Error('Failed to create setup intent');
      }

      const { client_secret } = await setupResponse.json();

      // Confirm card setup
      const cardElement = elements.getElement(CardElement);
      if (!cardElement) {
        throw new Error('Card element not found');
      }

      const { error: stripeError, setupIntent } = await stripe.confirmCardSetup(client_secret, {
        payment_method: { card: cardElement },
      });

      if (stripeError) {
        throw new Error(stripeError.message);
      }

      // Add payment method to backend
      const addResponse = await fetch(`${API_BASE_URL}/api/v1/stripe/customers/${user.practice_id}/payment-methods`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          payment_method_id: setupIntent.payment_method,
          set_as_default: true,
        }),
      });

      if (!addResponse.ok) {
        throw new Error('Failed to save payment method');
      }

      onSuccess();
    } catch (err: any) {
      setError(err.message || 'Failed to add payment method');
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="flex flex-col h-full">
      <div className="flex-1 overflow-y-auto px-6 py-6">
        {!hasExistingCards && (
          <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-6">
            <div className="flex items-start gap-3">
              <CheckCircle className="h-5 w-5 text-green-600 mt-0.5 flex-shrink-0" />
              <p className="text-sm font-medium text-green-900">
                $10 in free credits to get started
              </p>
            </div>
          </div>
        )}

        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Card details
          </label>
          <div className="border border-gray-300 rounded-md p-3">
            <CardElement
              options={{
                style: {
                  base: {
                    fontSize: '16px',
                    color: '#1f2937',
                    '::placeholder': { color: '#9ca3af' },
                  },
                },
              }}
            />
          </div>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md">
            <p className="text-sm text-red-800">{error}</p>
          </div>
        )}
      </div>

      <div className="border-t border-gray-200 px-6 py-4 flex gap-3">
        <button
          type="button"
          onClick={onClose}
          disabled={loading}
          className="flex-1 px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50"
        >
          Cancel
        </button>
        <button
          type="submit"
          disabled={!stripe || loading}
          className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-md text-sm font-medium hover:bg-blue-700 disabled:opacity-50 flex items-center justify-center gap-2"
        >
          {loading ? (
            <>
              <Loader className="h-4 w-4 animate-spin" />
              Adding...
            </>
          ) : (
            'Add card'
          )}
        </button>
      </div>
    </form>
  );
};

const AddPaymentMethodPanel: React.FC<AddPaymentMethodPanelProps> = ({ isOpen, onClose, onSuccess, hasExistingCards }) => {
  const [stripePromise, setStripePromise] = useState<Promise<any> | null>(null);

  React.useEffect(() => {
    if (isOpen) {
      getStripe().then(setStripePromise);
    }
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <>
      {/* Backdrop */}
      <div 
        className="fixed inset-0 bg-black/20 z-40 transition-opacity"
        onClick={onClose}
      />
      
      {/* Slide-in panel */}
      <div className="fixed inset-y-0 right-0 w-96 bg-white shadow-xl z-50 flex flex-col">
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">Add payment method</h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {stripePromise ? (
          <Elements stripe={stripePromise}>
            <CardForm onClose={onClose} onSuccess={onSuccess} hasExistingCards={hasExistingCards} />
          </Elements>
        ) : (
          <div className="flex items-center justify-center py-12">
            <Loader className="h-8 w-8 text-blue-600 animate-spin" />
          </div>
        )}
      </div>
    </>
  );
};

export default AddPaymentMethodPanel;

