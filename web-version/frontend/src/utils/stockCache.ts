// 종목 목록 캐싱 유틸리티
import { useState, useEffect } from 'react';

interface CachedData<T> {
  data: T;
  timestamp: number;
  expiry: number;
}

class StockCache {
  private readonly CACHE_KEY_PREFIX = 'stock_cache_';
  private readonly DEFAULT_TTL = 24 * 60 * 60 * 1000; // 24시간
  
  // localStorage에 캐시 저장
  set<T>(key: string, data: T, ttlMs: number = this.DEFAULT_TTL): void {
    const cacheData: CachedData<T> = {
      data,
      timestamp: Date.now(),
      expiry: Date.now() + ttlMs
    };
    
    try {
      localStorage.setItem(
        this.CACHE_KEY_PREFIX + key,
        JSON.stringify(cacheData)
      );
    } catch (error) {
      // localStorage 용량 초과 등의 에러 처리
      console.warn('Failed to cache data:', error);
      this.clearExpiredCache(); // 만료된 캐시 정리 후 재시도
      try {
        localStorage.setItem(
          this.CACHE_KEY_PREFIX + key,
          JSON.stringify(cacheData)
        );
      } catch (retryError) {
        console.error('Failed to cache after cleanup:', retryError);
      }
    }
  }
  
  // 캐시에서 데이터 가져오기
  get<T>(key: string): T | null {
    try {
      const cached = localStorage.getItem(this.CACHE_KEY_PREFIX + key);
      if (!cached) return null;
      
      const parsedCache = JSON.parse(cached) as CachedData<T>;
      
      // 만료 확인
      if (Date.now() > parsedCache.expiry) {
        this.remove(key);
        return null;
      }
      
      return parsedCache.data;
    } catch (error) {
      console.error('Failed to get cached data:', error);
      return null;
    }
  }
  
  // 특정 캐시 삭제
  remove(key: string): void {
    localStorage.removeItem(this.CACHE_KEY_PREFIX + key);
  }
  
  // 모든 종목 캐시 삭제
  clearAll(): void {
    const keys = Object.keys(localStorage);
    keys.forEach(key => {
      if (key.startsWith(this.CACHE_KEY_PREFIX)) {
        localStorage.removeItem(key);
      }
    });
  }
  
  // 만료된 캐시 정리
  clearExpiredCache(): void {
    const keys = Object.keys(localStorage);
    keys.forEach(key => {
      if (key.startsWith(this.CACHE_KEY_PREFIX)) {
        try {
          const cached = localStorage.getItem(key);
          if (cached) {
            const parsedCache = JSON.parse(cached) as CachedData<any>;
            if (Date.now() > parsedCache.expiry) {
              localStorage.removeItem(key);
            }
          }
        } catch (error) {
          // 파싱 실패한 캐시는 삭제
          localStorage.removeItem(key);
        }
      }
    });
  }
  
  // 캐시 정보 가져오기
  getCacheInfo(key: string): { age: number; remainingTTL: number } | null {
    try {
      const cached = localStorage.getItem(this.CACHE_KEY_PREFIX + key);
      if (!cached) return null;
      
      const parsedCache = JSON.parse(cached) as CachedData<any>;
      const age = Date.now() - parsedCache.timestamp;
      const remainingTTL = parsedCache.expiry - Date.now();
      
      return { age, remainingTTL };
    } catch (error) {
      return null;
    }
  }
}

// 싱글톤 인스턴스
export const stockCache = new StockCache();

// React Hook for cached API calls
export function useCachedStocks<T>(
  key: string,
  fetcher: () => Promise<T>,
  options?: {
    ttl?: number;
    staleWhileRevalidate?: boolean;
  }
) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const [isStale, setIsStale] = useState(false);

  useEffect(() => {
    let mounted = true;

    const loadData = async () => {
      // 캐시 확인
      const cached = stockCache.get<T>(key);
      
      if (cached) {
        if (mounted) {
          setData(cached);
          setLoading(false);
        }
        
        // stale-while-revalidate 패턴
        if (options?.staleWhileRevalidate) {
          const cacheInfo = stockCache.getCacheInfo(key);
          // 캐시가 12시간 이상 되었으면 백그라운드에서 갱신
          if (cacheInfo && cacheInfo.age > 12 * 60 * 60 * 1000) {
            setIsStale(true);
            fetcher()
              .then(freshData => {
                if (mounted) {
                  setData(freshData);
                  stockCache.set(key, freshData, options.ttl);
                  setIsStale(false);
                }
              })
              .catch(console.error);
          }
        }
        return;
      }
      
      // 캐시가 없으면 API 호출
      try {
        setLoading(true);
        const freshData = await fetcher();
        if (mounted) {
          setData(freshData);
          stockCache.set(key, freshData, options?.ttl);
        }
      } catch (err) {
        if (mounted) {
          setError(err as Error);
        }
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    };

    loadData();

    return () => {
      mounted = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key]); // fetcher는 의존성에서 제외 (무한 루프 방지)

  return { data, loading, error, isStale };
}