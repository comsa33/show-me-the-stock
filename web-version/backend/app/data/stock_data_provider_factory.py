"""
주식 데이터 제공자 팩토리
환경 설정에 따라 적절한 데이터 제공자를 선택
"""
import os
import logging
from typing import Optional

from .base_stock_data_provider import StockDataProvider
from .pykrx_data_provider import PykrxDataProvider
from .fdr_data_provider import FDRDataProvider
from .yahoo_data_provider import YahooDataProvider
from .hybrid_data_provider import HybridDataProvider

logger = logging.getLogger(__name__)


class StockDataProviderFactory:
    """데이터 제공자 팩토리 클래스"""
    
    # 싱글톤 인스턴스
    _providers = {}
    
    @classmethod
    def get_provider(cls, provider_type: Optional[str] = None) -> StockDataProvider:
        """
        데이터 제공자 인스턴스 반환
        
        Args:
            provider_type: 제공자 타입 (pykrx, fdr, auto)
                         None인 경우 환경변수 확인
        
        Returns:
            StockDataProvider 인스턴스
        """
        # 환경변수에서 제공자 타입 확인
        if provider_type is None:
            provider_type = os.getenv('STOCK_DATA_PROVIDER', 'auto')
        
        # 이미 생성된 인스턴스가 있으면 반환
        if provider_type in cls._providers:
            return cls._providers[provider_type]
        
        # 새 인스턴스 생성
        provider = cls._create_provider(provider_type)
        cls._providers[provider_type] = provider
        
        return provider
    
    @classmethod
    def _create_provider(cls, provider_type: str) -> StockDataProvider:
        """데이터 제공자 생성"""
        provider_type = provider_type.lower()
        
        if provider_type == 'pykrx':
            logger.info("Using pykrx data provider")
            return PykrxDataProvider()
            
        elif provider_type == 'fdr':
            logger.info("Using FinanceDataReader data provider")
            return FDRDataProvider()
            
        elif provider_type == 'yahoo':
            logger.info("Using Yahoo Finance data provider")
            return YahooDataProvider()
            
        elif provider_type == 'hybrid':
            logger.info("Using Hybrid (FDR + Yahoo) data provider")
            return HybridDataProvider()
            
        elif provider_type == 'auto':
            # 자동 선택 로직 - Hybrid를 기본으로
            try:
                provider = HybridDataProvider()
                logger.info("Auto-selected Hybrid provider")
                return provider
            except Exception as e:
                logger.warning(f"Hybrid provider failed: {e}")
            
            # Hybrid 실패시 FDR 시도
            try:
                provider = FDRDataProvider()
                test_result = provider.get_stock_price_realtime('005930')
                if test_result:
                    logger.info("Auto-selected FinanceDataReader provider")
                    return provider
            except Exception as e:
                logger.warning(f"FDR provider test failed: {e}")
            
            # 모두 실패시 Yahoo
            logger.warning("All provider tests failed, defaulting to Yahoo")
            return YahooDataProvider()
            
        else:
            raise ValueError(f"Unknown provider type: {provider_type}")
    
    @classmethod
    def clear_cache(cls):
        """캐시된 인스턴스 초기화"""
        cls._providers.clear()
        logger.info("Cleared all cached data providers")
    
    @classmethod
    def get_available_providers(cls) -> list:
        """사용 가능한 제공자 목록 반환"""
        return ['pykrx', 'fdr', 'auto']