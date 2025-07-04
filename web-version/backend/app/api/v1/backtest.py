from fastapi import APIRouter, Query, HTTPException
from typing import Dict, Any
from datetime import datetime
import logging

from app.services.backtest_service import backtest_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/backtest", tags=["Backtest"])


@router.post("/run")
async def run_backtest(
    symbol: str = Query(..., description="종목 코드"),
    market: str = Query("KR", description="시장 (KR/US)"),
    start_date: str = Query(..., description="시작일 (YYYY-MM-DD)"),
    end_date: str = Query(..., description="종료일 (YYYY-MM-DD)"),
    investment_amount: float = Query(..., description="투자 금액"),
    strategy: str = Query("buy_hold", description="투자 전략 (buy_hold/technical/value)")
) -> Dict[str, Any]:
    """
    실제 과거 데이터를 사용한 백테스트 실행
    
    전략:
    - buy_hold: 매수 후 보유
    - technical: 기술적 분석 (20일/60일 이동평균 교차)
    - value: 가치 투자 (52주 최고가 대비 20% 하락 시 매수)
    """
    try:
        # 날짜 검증
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        
        if start_dt >= end_dt:
            raise ValueError("종료일은 시작일보다 이후여야 합니다")
        
        if end_dt > datetime.now():
            raise ValueError("종료일은 오늘 이전이어야 합니다")
        
        # 백테스트 실행
        result = await backtest_service.run_backtest(
            symbol=symbol,
            market=market,
            start_date=start_date,
            end_date=end_date,
            investment_amount=investment_amount,
            strategy=strategy
        )
        
        if not result:
            raise HTTPException(
                status_code=404,
                detail=f"백테스트 실행 실패: {symbol}의 데이터를 찾을 수 없습니다"
            )
        
        return {
            "success": True,
            "result": result.dict()
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Backtest error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"백테스트 실행 중 오류가 발생했습니다: {str(e)}"
        )