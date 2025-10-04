# Stripe Integration - HelpPetAI

## Overview
This document describes the Stripe payment integration added to HelpPetAI to support billing for phone calls, transcriptions, and website hosting.

## Features Implemented

### 1. Database Schema
**Migration**: `k0l1m2n3o4p5_add_stripe_customer_table.py`

A new `stripe_customers` table has been added with the following fields:
- `id`: UUID primary key
- `practice_id`: Foreign key to veterinary_practices (one-to-one relationship)
- `stripe_customer_id`: Stripe's customer ID
- `created_by_user_id`: User who set up Stripe for the practice
- `email`: Email for Stripe customer
- `default_payment_method_id`: Default payment method
- `balance_credits_cents`: Credit balance in cents (starts at $10.00 = 1000 cents)
- `created_at`, `updated_at`: Audit timestamps

### 2. Pricing Model
- **Phone Calls**: 20¢ per minute
- **Phone Number Registration**: $10-15 (one-time)
- **Recording Transcriptions**: 25¢ per recording
- **Website Hosting**: $7/month
- **Initial Credits**: $10 given to each practice when they add a payment method

### 3. Backend API Endpoints

All endpoints are prefixed with `/api/v1/stripe/`

#### Customer Management
- `POST /customers` - Create a Stripe customer for a practice (automatically adds $10 credits)
- `GET /customers/{practice_id}` - Get customer info including balance and payment methods
- `GET /customers/{practice_id}/has-payment-method` - Check if practice has payment method (for paywall)

#### Payment Method Management
- `POST /customers/{practice_id}/setup-intent` - Create SetupIntent for adding payment method
- `POST /customers/{practice_id}/payment-methods` - Add payment method to customer
- `GET /customers/{practice_id}/payment-methods` - List all payment methods
- `DELETE /customers/{practice_id}/payment-methods/{payment_method_id}` - Remove payment method
- `PUT /customers/{practice_id}/payment-methods/{payment_method_id}/set-default` - Set default payment method

#### Configuration
- `GET /config` - Get Stripe publishable key for frontend

### 4. Backend Components

**Models** (`src/models_pg/stripe_customer.py`):
- `StripeCustomer` - SQLAlchemy model with helper properties

**Repositories** (`src/repositories_pg/stripe_customer_repository.py`):
- `StripeCustomerRepository` - Database operations for Stripe customers
- Methods for balance management, payment method updates, etc.

**Services** (`src/services/stripe_service.py`):
- `StripeService` - Business logic and Stripe API integration
- Handles customer creation, payment method management, credits, etc.

**Routes** (`src/routes_pg/stripe.py`):
- FastAPI routes with authentication and authorization
- Validates user permissions (must belong to practice or be admin)

### 5. Frontend Implementation

**Phone Number Registration Paywall** (`frontend/src/components/voice-agents/PhoneConfigSection.tsx`):
- Added check for payment method before allowing phone number registration
- Shows paywall modal if no payment method exists
- Modal explains pricing and benefits
- Button kept visible but shows modal instead of configuration form

**Paywall Modal Features**:
- Explains requirement to add credit card
- Lists pricing and initial credits
- Has "Add Payment Method" button (currently shows alert, ready for billing page)
- Can be dismissed with Cancel button

### 6. Configuration

Add these environment variables to your `.env` file:

```bash
# Stripe Configuration
STRIPE_API_KEY=sk_test_...           # Your Stripe secret key
STRIPE_PUBLISHABLE_KEY=pk_test_...   # Your Stripe publishable key
STRIPE_WEBHOOK_SECRET=whsec_...      # Webhook secret for events (optional for now)
```

## Next Steps

### To Deploy:
1. Run the migration:
   ```bash
   cd backend
   make migrate  # Local testing
   make deploy && make migrate-production  # Production
   ```

2. Install Stripe SDK:
   ```bash
   pip install stripe
   ```

3. Set up Stripe environment variables in production

### Future Implementation:
1. **Billing Dashboard Page**: Create a frontend page for:
   - Viewing current balance and credits
   - Adding/removing payment methods
   - Viewing transaction history
   - Setting up Stripe Elements for card input

2. **Usage Tracking**: Implement deduction of credits for:
   - Phone call minutes
   - Transcription processing
   - Monthly charges

3. **Stripe Webhooks**: Handle Stripe events:
   - Payment method updates
   - Payment failures
   - Subscription changes

4. **Notifications**: Email/SMS alerts for:
   - Low balance warnings
   - Payment failures
   - Successful charges

## Security Notes

- All Stripe endpoints require authentication
- Users can only manage payment for their own practice (or if admin)
- Stripe secret keys should never be exposed to frontend
- Only publishable keys are sent to client

## Testing

To test locally:
1. Get Stripe test API keys from https://dashboard.stripe.com/test/apikeys
2. Add them to your `.env` file
3. Use Stripe's test card numbers: https://stripe.com/docs/testing
   - Success: `4242 4242 4242 4242`
   - Decline: `4000 0000 0000 0002`

## Database Migration Notes

- One Stripe customer per practice (enforced by unique constraint)
- If practice is deleted, Stripe customer record is also deleted (CASCADE)
- Balance is stored in cents to avoid floating point precision issues
- Migration file follows Alembic best practices from the workspace rules

