import { ProviderAdapter } from './provider-adapter'

export class PayPalAdapter implements ProviderAdapter {
  constructor(private config: any) {}
  async startPayment(payload: any) {
    // Create PayPal order and return approval link
    return { provider_ref: 'paypal-ord-123', status: 'pending', approval_url: 'https://www.sandbox.paypal.com/' }
  }
  async handleCallback(payload: any) {
    return { provider_ref: payload.resource?.id || 'paypal-123', status: 'success' }
  }
  async fetchTransactions() {
    return []
  }
}
