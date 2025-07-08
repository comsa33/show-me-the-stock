/**
 * Stock Search Service
 * Centralized service for fetching and caching stock lists
 */
import { API_BASE } from '../config';

export interface StockSearchItem {
  symbol: string;
  name: string;
  market: 'KR' | 'US';
  exchange?: string;
}

export interface StockSearchResponse {
  stocks: StockSearchItem[];
  total: number;
  market?: string;
}

class StockSearchService {
  private cache: Map<string, { data: StockSearchResponse; timestamp: number }> = new Map();
  private cacheDuration = 24 * 60 * 60 * 1000; // 24 hours
  private pendingRequests: Map<string, Promise<StockSearchResponse>> = new Map();

  /**
   * Get all stocks for search (combined KR + US)
   */
  async getAllStocks(): Promise<StockSearchResponse> {
    const cacheKey = 'all_stocks';
    
    // Check cache
    const cached = this.getFromCache(cacheKey);
    if (cached) {
      return cached;
    }

    // Check if request is already pending
    const pending = this.pendingRequests.get(cacheKey);
    if (pending) {
      return pending;
    }

    // Make new request
    const requestPromise = this.fetchStocks('/stocks/search/combined');
    this.pendingRequests.set(cacheKey, requestPromise);

    try {
      const data = await requestPromise;
      this.setCache(cacheKey, data);
      return data;
    } finally {
      this.pendingRequests.delete(cacheKey);
    }
  }

  /**
   * Get stocks by market
   */
  async getStocksByMarket(market: 'KR' | 'US'): Promise<StockSearchResponse> {
    const cacheKey = `stocks_${market}`;
    
    // Check cache
    const cached = this.getFromCache(cacheKey);
    if (cached) {
      return cached;
    }

    // Check if request is already pending
    const pending = this.pendingRequests.get(cacheKey);
    if (pending) {
      return pending;
    }

    // Make new request
    const requestPromise = this.fetchStocks(`/stocks/search/all?market=${market}`);
    this.pendingRequests.set(cacheKey, requestPromise);

    try {
      const data = await requestPromise;
      this.setCache(cacheKey, data);
      return data;
    } finally {
      this.pendingRequests.delete(cacheKey);
    }
  }

  /**
   * Search stocks by query
   */
  searchStocks(stocks: StockSearchItem[], query: string): StockSearchItem[] {
    if (!query) return stocks;

    const lowerQuery = query.toLowerCase();
    
    return stocks.filter(stock => 
      stock.symbol.toLowerCase().includes(lowerQuery) ||
      stock.name.toLowerCase().includes(lowerQuery)
    );
  }

  /**
   * Format stock for display
   */
  formatStockDisplay(stock: StockSearchItem): string {
    return `${stock.name} (${stock.symbol})`;
  }

  /**
   * Clear cache
   */
  clearCache(): void {
    this.cache.clear();
  }

  /**
   * Clear specific cache entry
   */
  clearCacheEntry(key: string): void {
    this.cache.delete(key);
  }

  private async fetchStocks(endpoint: string): Promise<StockSearchResponse> {
    const response = await fetch(`${API_BASE}/v1${endpoint}`);
    
    if (!response.ok) {
      throw new Error(`Failed to fetch stocks: ${response.statusText}`);
    }

    return response.json();
  }

  private getFromCache(key: string): StockSearchResponse | null {
    const cached = this.cache.get(key);
    
    if (!cached) return null;

    // Check if cache is still valid
    if (Date.now() - cached.timestamp > this.cacheDuration) {
      this.cache.delete(key);
      return null;
    }

    return cached.data;
  }

  private setCache(key: string, data: StockSearchResponse): void {
    this.cache.set(key, {
      data,
      timestamp: Date.now()
    });
  }
}

// Export singleton instance
export const stockSearchService = new StockSearchService();