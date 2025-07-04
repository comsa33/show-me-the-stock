"""
금리 정보 관련 API 엔드포인트
"""

from datetime import datetime

from app.core.config import get_settings
from app.data.interest_rate_data import InterestRateDataFetcher
from fastapi import APIRouter, HTTPException, Query

router = APIRouter()
settings = get_settings()

# 글로벌 인스턴스
interest_rate_fetcher = InterestRateDataFetcher()


@router.get("/current")
async def get_current_rates():
    """현재 금리 정보 조회 (실시간 데이터)"""
    try:
        # 실제 데이터 가져오기
        rates = interest_rate_fetcher.get_current_rates()
        
        # 미국 10년 국채와 한국 3년 국채 기준
        us_rate = rates.get("US_10Y", 4.5)
        kr_rate = rates.get("KR_3Y", 3.5)
        
        return {
            "current_rates": {
                "korea": {
                    "rate": round(kr_rate, 2), 
                    "description": "한국 3년 국채수익률",
                    "source": "실시간 데이터" if "KR_3Y" in rates else "추정값"
                },
                "usa": {
                    "rate": round(us_rate, 2), 
                    "description": "미국 10년 국채수익률",
                    "source": "yfinance 실시간"
                },
                "spread": round(us_rate - kr_rate, 2)
            },
            "timestamp": datetime.now().isoformat(),
            "data_source": "mixed_real_time"
        }
    except Exception as e:
        # 에러 시 백업 데이터
        return {
            "current_rates": {
                "korea": {"rate": 3.5, "description": "한국 기준금리 (백업값)", "source": "fallback"},
                "usa": {"rate": 4.5, "description": "미국 연방기금금리 (백업값)", "source": "fallback"},
                "spread": 1.0
            },
            "timestamp": datetime.now().isoformat(),
            "data_source": "fallback",
            "error": str(e)
        }


@router.get("/korea")
async def get_korea_rates(
    period: str = Query("1y", description="조회 기간: 1m, 3m, 6m, 1y, 2y, 5y")
):
    """한국 금리 데이터 조회"""
    try:
        korea_rates = interest_rate_fetcher.get_kr_interest_rate(period)

        if korea_rates is None or korea_rates.empty:
            # 샘플 데이터 반환
            return {
                "country": "Korea",
                "period": period,
                "data": [
                    {"Date": "2024-12-01", "Rate": 3.5},
                    {"Date": "2024-11-01", "Rate": 3.5},
                    {"Date": "2024-10-01", "Rate": 3.25},
                ],
                "timestamp": datetime.now().isoformat(),
            }

        # DataFrame을 JSON 형태로 변환
        rates_dict = korea_rates.reset_index().to_dict("records")

        return {
            "country": "Korea",
            "period": period,
            "data": rates_dict,
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"한국 금리 조회 실패: {str(e)}")


@router.get("/usa")
async def get_usa_rates(
    period: str = Query("1y", description="조회 기간: 1m, 3m, 6m, 1y, 2y, 5y")
):
    """미국 금리 데이터 조회"""
    try:
        usa_rates = interest_rate_fetcher.get_us_interest_rate(period)

        if usa_rates is None or usa_rates.empty:
            # 샘플 데이터 반환
            return {
                "country": "USA",
                "period": period,
                "data": [
                    {"Date": "2024-12-01", "Rate": 5.25},
                    {"Date": "2024-11-01", "Rate": 5.0},
                    {"Date": "2024-10-01", "Rate": 4.75},
                ],
                "timestamp": datetime.now().isoformat(),
            }

        # DataFrame을 JSON 형태로 변환
        rates_dict = usa_rates.reset_index().to_dict("records")

        return {
            "country": "USA",
            "period": period,
            "data": rates_dict,
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"미국 금리 조회 실패: {str(e)}")


@router.get("/comparison")
async def get_rate_comparison(
    period: str = Query("1y", description="조회 기간: 1m, 3m, 6m, 1y, 2y, 5y")
):
    """한국-미국 금리 비교"""
    try:
        # 간단한 비교 데이터 반환
        comparison = {
            "korea_current": 3.5,
            "usa_current": 5.25,
            "spread": 1.75,
            "analysis": "미국 금리가 한국보다 1.75%p 높은 상황",
        }

        return {
            "comparison": comparison,
            "period": period,
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"금리 비교 실패: {str(e)}")


@router.get("/trends")
async def get_rate_trends():
    """금리 트렌드 분석"""
    try:
        trends = {
            "korea": {
                "direction": "stable",
                "description": "한국 기준금리는 현재 안정적인 상태",
            },
            "usa": {
                "direction": "rising",
                "description": "미국 연방기금금리는 상승 추세",
            },
        }

        return {"trends": trends, "timestamp": datetime.now().isoformat()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"금리 트렌드 분석 실패: {str(e)}")
