"""
주요 지수 데이터 API 엔드포인트
"""

from fastapi import APIRouter, Query, HTTPException
from typing import List, Dict, Optional
import logging

from app.services.index_data_service import index_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/korean")
async def get_korean_indices():
    """
    한국 주요 지수 데이터 조회
    """
    try:
        indices = index_service.get_korean_indices()
        
        logger.info(f"한국 지수 {len(indices)}개 조회 완료")
        return {
            "indices": indices,
            "count": len(indices),
            "market": "KR"
        }
        
    except Exception as e:
        logger.error(f"한국 지수 조회 실패: {e}")
        raise HTTPException(status_code=500, detail="한국 지수 데이터 조회에 실패했습니다.")


@router.get("/us")
async def get_us_indices():
    """
    미국 주요 지수 데이터 조회
    """
    try:
        indices = index_service.get_us_indices()
        
        logger.info(f"미국 지수 {len(indices)}개 조회 완료")
        return {
            "indices": indices,
            "count": len(indices),
            "market": "US"
        }
        
    except Exception as e:
        logger.error(f"미국 지수 조회 실패: {e}")
        raise HTTPException(status_code=500, detail="미국 지수 데이터 조회에 실패했습니다.")


@router.get("/all")
async def get_all_indices():
    """
    전체 지수 데이터 조회
    """
    try:
        result = index_service.get_all_indices()
        
        logger.info(f"전체 지수 조회 완료: 한국 {len(result['korean_indices'])}개, 미국 {len(result['us_indices'])}개")
        return result
        
    except Exception as e:
        logger.error(f"전체 지수 조회 실패: {e}")
        raise HTTPException(status_code=500, detail="지수 데이터 조회에 실패했습니다.")


@router.get("/{symbol}")
async def get_index_by_symbol(
    symbol: str,
    market: str = Query("auto", description="시장 (KR/US/auto)")
):
    """
    개별 지수 데이터 조회
    """
    try:
        index_data = index_service.get_index_data(symbol, market)
        
        if not index_data:
            raise HTTPException(status_code=404, detail=f"지수 {symbol}을 찾을 수 없습니다.")
        
        logger.info(f"지수 {symbol} 조회 완료")
        return index_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"지수 {symbol} 조회 실패: {e}")
        raise HTTPException(status_code=500, detail="지수 데이터 조회에 실패했습니다.")


@router.get("/market/{market_code}")
async def get_market_indices(
    market_code: str
):
    """
    특정 시장의 지수 데이터 조회
    """
    try:
        if market_code.upper() == "KR":
            indices = index_service.get_korean_indices()
        elif market_code.upper() == "US":
            indices = index_service.get_us_indices()
        else:
            raise HTTPException(status_code=400, detail="지원되지 않는 시장 코드입니다. (KR/US)")
        
        logger.info(f"{market_code} 시장 지수 {len(indices)}개 조회 완료")
        return {
            "indices": indices,
            "count": len(indices),
            "market": market_code.upper()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"{market_code} 시장 지수 조회 실패: {e}")
        raise HTTPException(status_code=500, detail="시장 지수 데이터 조회에 실패했습니다.")