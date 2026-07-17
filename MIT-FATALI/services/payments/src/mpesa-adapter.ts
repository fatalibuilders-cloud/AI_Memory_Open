import { ProviderAdapter } from './provider-adapter'

export class MpesaAdapter implements ProviderAdapter {
  constructor(private config: any) {}
  async startPayment(payload: any) {
    // Implement Daraja STK Push call using consumer key/secret
    // This is a stub for now
    return { provider_ref: 'mpesa-stk-123', status: 'pending' }
  }
  async handleCallback(payload: any) {
    // Verify and normalize Daraja callback
    return { provider_ref: payload.MerchantRequestID || payload.provider_ref, status: 'success' }
  }
  async fetchTransactions() {
    return []
  }
}
