export interface ProviderAdapter {
  startPayment(payload: any): Promise<any>
  handleCallback(payload: any): Promise<any>
  fetchTransactions(since?: string): Promise<any[]>
}
