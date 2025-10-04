import React, { useState } from 'react';
import { loadStripe } from '@stripe/stripe-js';
import { Elements, CardElement, useStripe, useElements } from '@stripe/react-stripe-js';
import { X, CheckCircle, Loader } from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import { API_BASE_URL } from '../../config/api';

// Initialize Stripe (will be loaded from backend config)
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

interface AddPaymentMethodModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

const CardForm: React.FC<{ onClose: () => void; onSuccess: () => void }> = ({ onClose, onSuccess }) => {
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
      
      // First, ensure Stripe customer exists (creates one if needed with $10 credit)
      const customerCheckResponse = await fetch(`${API_BASE_URL}/api/v1/stripe/customers/${user.practice_id}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (customerCheckResponse.ok) {
        const customerData = await customerCheckResponse.json();
        if (!customerData.customer) {
          // Create customer with $10 credit
          const createCustomerResponse = await fetch(`${API_BASE_URL}/api/v1/stripe/customers`, {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              practice_id: user.practice_id,
              email: user.email || '',
              practice_name: 'Practice', // You might want to get this from context
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
        payment_method: {
          card: cardElement,
        },
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
    <form onSubmit={handleSubmit}>
      <div className="mb-6">
        <h3 className="text-xl font-semibold text-gray-900 mb-2">
          Add payment method
        </h3>
        <p className="text-sm text-gray-600 mb-6">
          Add a card to activate your phone number and receive $10 in free credits.
        </p>

        {/* Welcome Credit Banner */}
        <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-6">
          <div className="flex items-start gap-3">
            <CheckCircle className="h-5 w-5 text-green-600 mt-0.5 flex-shrink-0" />
            <div>
              <p className="text-sm font-medium text-green-900">
                $10 in free credits to get started
              </p>
            </div>
          </div>
        </div>

        {/* Card Input */}
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Card details
          </label>
          <div className="border border-gray-300 rounded-md p-3 hover:border-gray-400 focus-within:border-blue-500 focus-within:ring-1 focus-within:ring-blue-500">
            <CardElement
              options={{
                style: {
                  base: {
                    fontSize: '16px',
                    color: '#1f2937',
                    '::placeholder': {
                      color: '#9ca3af',
                    },
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

      <div className="flex gap-3">
        <button
          type="button"
          onClick={onClose}
          disabled={loading}
          className="flex-1 px-4 py-2.5 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50"
        >
          Cancel
        </button>
        <button
          type="submit"
          disabled={!stripe || loading}
          className="flex-1 px-4 py-2.5 bg-blue-600 text-white rounded-md text-sm font-medium hover:bg-blue-700 disabled:opacity-50 flex items-center justify-center gap-2"
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

const AddPaymentMethodModal: React.FC<AddPaymentMethodModalProps> = ({ isOpen, onClose, onSuccess }) => {
  const [stripePromise, setStripePromise] = useState<Promise<any> | null>(null);

  React.useEffect(() => {
    if (isOpen) {
      getStripe().then(setStripePromise);
    }
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/20 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-8 border border-gray-200 relative">
        <button
          onClick={onClose}
          className="absolute top-6 right-6 text-gray-400 hover:text-gray-600"
        >
          <X className="h-5 w-5" />
        </button>

        {stripePromise ? (
          <Elements stripe={stripePromise}>
            <CardForm onClose={onClose} onSuccess={onSuccess} />
          </Elements>
        ) : (
          <div className="flex items-center justify-center py-12">
            <Loader className="h-8 w-8 text-blue-600 animate-spin" />
          </div>
        )}
      </div>
    </div>
  );
};

export default AddPaymentMethodModal;

