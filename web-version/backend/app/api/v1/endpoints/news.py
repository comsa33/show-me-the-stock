"""
뉴스 API 엔드포인트
네이버 뉴스 검색 API 프록시
"""

import httpx
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
import logging
from app.core.config import get_settings

logger = logging.getLogger(__name__)

router = APIRouter()

# 설정 가져오기
settings = get_settings()

@router.get("/search")
async def search_news(
    query: str = Query(..., description="검색할 키워드"),
    display: int = Query(10, ge=1, le=100, description="한 번에 표시할 검색 결과 개수"),
    start: int = Query(1, ge=1, le=1000, description="검색 시작 위치"),
    sort: str = Query("sim", regex="^(sim|date)$", description="정렬 옵션 (sim: 유사도순, date: 날짜순)")
):
    """
    네이버 뉴스 검색 API 프록시
    
    Args:
        query: 검색 키워드
        display: 검색 결과 출력 건수 (기본값: 10, 최대: 100)
        start: 검색 시작 위치 (기본값: 1, 최대: 1000)
        sort: 정렬 옵션 (sim: 유사도순, date: 날짜순)
    
    Returns:
        네이버 뉴스 검색 결과
    """
    
    # 설정에서 네이버 API 키 가져오기
    client_id = settings.naver_client_id
    client_secret = settings.naver_client_secret
    
    if not client_id or not client_secret:
        logger.error("Naver API credentials not found in environment variables")
        raise HTTPException(
            status_code=500,
            detail="네이버 API 키가 설정되지 않았습니다."
        )
    
    # 네이버 뉴스 검색 API 호출
    async with httpx.AsyncClient() as client:
        try:
            logger.info(f"Searching news for query: {query}")
            response = await client.get(
                "https://openapi.naver.com/v1/search/news.json",
                params={
                    "query": query,
                    "display": display,
                    "start": start,
                    "sort": sort
                },
                headers={
                    "X-Naver-Client-Id": client_id,
                    "X-Naver-Client-Secret": client_secret
                },
                timeout=10.0
            )
            
            response.raise_for_status()
            data = response.json()
            logger.info(f"Found {data.get('total', 0)} news items for query: {query}")
            return data
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Naver API HTTP error: {e.response.status_code} - {e.response.text}")
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"네이버 API 오류: {e.response.text}"
            )
        except httpx.RequestError as e:
            logger.error(f"Network error while calling Naver API: {str(e)}")
            raise HTTPException(
                status_code=503,
                detail=f"네트워크 오류: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Unexpected error in news search: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"서버 오류: {str(e)}"
            )