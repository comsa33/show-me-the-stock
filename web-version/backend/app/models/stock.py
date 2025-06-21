"""
주식 데이터 모델
Pydantic 기반 타입 안전한 데이터 모델
"""

from datetime import datetime
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, validator
from enum import Enum


class MarketType(str, Enum):
    """시장 타입"""
    KR = "KR"
    US = "US"


class ChartType(str, Enum):
    """차트 타입"""
    CANDLESTICK = "candlestick"
    LINE = "line"
    AREA = "area"
    COMPARISON = "comparison"


class PeriodType(str, Enum):
    """기간 타입"""
    ONE_DAY = "1d"
    FIVE_DAYS = "5d"
    ONE_MONTH = "1mo"
    THREE_MONTHS = "3mo"
    SIX_MONTHS = "6mo"
    ONE_YEAR = "1y"
    TWO_YEARS = "2y"
    FIVE_YEARS = "5y"
    MAX = "max"


class StockInfo(BaseModel):
    """주식 기본 정보"""
    symbol: str = Field(..., description="주식 심볼")
    name: str = Field(..., description="주식명")
    market: MarketType = Field(..., description="시장")
    currency: str = Field(default="USD", description="통화")
    exchange: str = Field(default="", description="거래소")
    sector: Optional[str] = Field(None, description="섹터")
    industry: Optional[str] = Field(None, description="산업")


class PriceData(BaseModel):
    """가격 데이터"""
    timestamp: datetime = Field(..., description="시간")
    open: float = Field(..., description="시가")
    high: float = Field(..., description="고가")
    low: float = Field(..., description="저가")
    close: float = Field(..., description="종가")
    volume: int = Field(..., description="거래량")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class TechnicalIndicators(BaseModel):
    """기술적 지표"""
    ma5: Optional[float] = Field(None, description="5일 이동평균")
    ma20: Optional[float] = Field(None, description="20일 이동평균")
    ma60: Optional[float] = Field(None, description="60일 이동평균")
    rsi: Optional[float] = Field(None, description="RSI")
    macd: Optional[float] = Field(None, description="MACD")
    signal: Optional[float] = Field(None, description="Signal")
    bb_upper: Optional[float] = Field(None, description="볼린저 밴드 상단")
    bb_middle: Optional[float] = Field(None, description="볼린저 밴드 중간")
    bb_lower: Optional[float] = Field(None, description="볼린저 밴드 하단")


class EnrichedPriceData(PriceData):
    """기술적 지표가 포함된 가격 데이터"""
    indicators: Optional[TechnicalIndicators] = None


class StockDataResponse(BaseModel):
    """주식 데이터 응답"""
    info: StockInfo
    data: List[EnrichedPriceData]
    period: PeriodType
    total_points: int = Field(..., description="총 데이터 포인트 수")
    last_updated: datetime = Field(default_factory=datetime.utcnow)


class MultiStockDataResponse(BaseModel):
    """다중 주식 데이터 응답"""
    stocks: Dict[str, StockDataResponse]
    requested_symbols: List[str]
    successful_symbols: List[str]
    failed_symbols: List[str]


class MarketStatus(BaseModel):
    """시장 상태"""
    market: MarketType
    status: str = Field(..., description="장중/장마감")
    current_time: str = Field(..., description="현재 시간")
    day_info: str = Field(..., description="날짜 정보")
    trading_hours: str = Field(..., description="거래 시간")
    next_info: Optional[str] = Field(None, description="다음 거래 정보")


class InterestRateData(BaseModel):
    """금리 데이터"""
    date: datetime
    rate: float
    country: str = Field(..., description="국가 (KR/US)")
    term: str = Field(..., description="만기 (3Y/10Y)")


class StockSearchRequest(BaseModel):
    """주식 검색 요청"""
    query: str = Field(..., min_length=1, max_length=100, description="검색어")
    market: MarketType = Field(..., description="시장")
    limit: int = Field(default=20, ge=1, le=100, description="결과 수 제한")


class StockSearchResult(BaseModel):
    """주식 검색 결과"""
    symbol: str
    name: str
    display: str
    score: int = Field(..., description="매칭 점수")
    market: MarketType


class StockDataRequest(BaseModel):
    """주식 데이터 요청"""
    symbols: List[str] = Field(..., min_items=1, max_items=10, description="주식 심볼 목록")
    period: PeriodType = Field(default=PeriodType.ONE_YEAR, description="조회 기간")
    market: MarketType = Field(..., description="시장")
    include_indicators: bool = Field(default=True, description="기술적 지표 포함 여부")
    include_volume: bool = Field(default=True, description="거래량 포함 여부")


class ChartRequest(BaseModel):
    """차트 요청"""
    symbols: List[str] = Field(..., min_items=1, max_items=5)
    chart_type: ChartType = Field(default=ChartType.CANDLESTICK)
    period: PeriodType = Field(default=PeriodType.ONE_YEAR)
    market: MarketType = Field(...)
    include_indicators: bool = Field(default=False)
    include_volume: bool = Field(default=True)
    include_interest_rate: bool = Field(default=False)


class FavoriteStock(BaseModel):
    """즐겨찾기 주식"""
    symbol: str
    name: str
    market: MarketType
    added_at: datetime = Field(default_factory=datetime.utcnow)


class UserFavorites(BaseModel):
    """사용자 즐겨찾기"""
    user_id: str
    favorites: List[FavoriteStock] = Field(default_factory=list)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class APIResponse(BaseModel):
    """표준 API 응답"""
    success: bool = Field(default=True)
    message: str = Field(default="Success")
    data: Optional[Any] = None
    error: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ErrorResponse(BaseModel):
    """에러 응답"""
    success: bool = Field(default=False)
    message: str
    error_code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)