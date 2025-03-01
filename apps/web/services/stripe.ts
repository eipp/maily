import { loadStripe } from '@stripe/stripe-js';
import { api } from './api';

// Initialize Stripe
const stripePromise = loadStripe(process.env.NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY!);

export interface PriceOption {
  id: string;
  name: string;
  price: number;
  currency: string;
  interval: 'month' | 'year';
  features: string[];
}

export interface SubscriptionDetails {
  subscriptionId: string;
  customerId: string;
  status: string;
  currentPeriodEnd: string;
  cancelAtPeriodEnd: boolean;
}

class StripeService {
  /**
   * Create a checkout session for subscription
   */
  async createCheckoutSession(priceId: string): Promise<string> {
    const response = await api.post('/payments/create-checkout-session', {
      priceId,
      successUrl: `${window.location.origin}/dashboard?session_id={CHECKOUT_SESSION_ID}`,
      cancelUrl: `${window.location.origin}/pricing`,
    });

    const stripe = await stripePromise;
    if (!stripe) throw new Error('Stripe failed to load');

    const { error } = await stripe.redirectToCheckout({
      sessionId: response.data.sessionId,
    });

    if (error) throw new Error(error.message);

    return response.data.sessionId;
  }

  /**
   * Create a billing portal session
   */
  async createPortalSession(): Promise<string> {
    const response = await api.post('/payments/create-portal-session', {
      returnUrl: `${window.location.origin}/dashboard`,
    });
    return response.data.url;
  }

  /**
   * Get subscription details
   */
  async getSubscriptionDetails(): Promise<SubscriptionDetails> {
    const response = await api.get('/payments/subscription');
    return response.data;
  }

  /**
   * Get available price options
   */
  async getPriceOptions(): Promise<PriceOption[]> {
    const response = await api.get('/payments/prices');
    return response.data;
  }

  /**
   * Handle successful checkout
   */
  async handleCheckoutSuccess(sessionId: string): Promise<void> {
    await api.post('/payments/checkout-success', { sessionId });
  }

  /**
   * Cancel subscription
   */
  async cancelSubscription(subscriptionId: string): Promise<void> {
    await api.post('/payments/cancel-subscription', { subscriptionId });
  }

  /**
   * Resume subscription
   */
  async resumeSubscription(subscriptionId: string): Promise<void> {
    await api.post('/payments/resume-subscription', { subscriptionId });
  }

  /**
   * Update payment method
   */
  async updatePaymentMethod(): Promise<string> {
    const response = await api.post('/payments/update-payment-method', {
      returnUrl: `${window.location.origin}/dashboard`,
    });
    return response.data.url;
  }

  /**
   * Get invoice history
   */
  async getInvoiceHistory(): Promise<any[]> {
    const response = await api.get('/payments/invoices');
    return response.data;
  }
}

export const stripeService = new StripeService();
