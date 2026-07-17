import { ProviderAdapter } from './provider-adapter'

export class MockAdapter implements ProviderAdapter {
  async startPayment(payload: any) {
    return { provider_ref: 'mock-123', status: 'pending' }
  }
  async handleCallback(payload: any) {
    return { provider_ref: payload.provider_ref || 'mock-123', status: 'success' }
  }
  async fetchTransactions() {
    return []
  }
}
