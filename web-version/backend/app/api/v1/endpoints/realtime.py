"""
실시간 주식 알림 WebSocket API
"""

import json
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from fastapi.responses import JSONResponse

from app.core.websocket_manager import websocket_manager
from app.services.realtime_service import realtime_service

logger = logging.getLogger(__name__)

router = APIRouter()

@router.websocket("/realtime")
async def websocket_endpoint(websocket: WebSocket):
    """
    실시간 주식 데이터 WebSocket 엔드포인트
    
    클라이언트는 이 엔드포인트로 연결하여 실시간 주식 알림을 받을 수 있습니다.
    
    메시지 형식:
    - 구독: {"action": "subscribe", "symbols": ["005930", "AAPL"]}
    - 구독해제: {"action": "unsubscribe", "symbols": ["005930"]}
    
    받을 수 있는 메시지 타입:
    - welcome: 연결 환영 메시지
    - price_update: 실시간 가격 업데이트
    - price_alert: 가격 변동 알림
    - market_alert: 시장 상황 알림
    - heartbeat: 연결 유지 신호
    """
    
    # WebSocket 연결 수락
    await websocket_manager.connect(websocket)
    
    try:
        while True:
            # 클라이언트로부터 메시지 수신
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                logger.debug(f"WebSocket 메시지 수신: {message}")
                
                # 구독 관련 메시지 처리
                if message.get('action') in ['subscribe', 'unsubscribe']:
                    await realtime_service.handle_client_subscription(websocket, message)
                else:
                    # 기타 메시지 처리
                    await websocket_manager.send_personal_message(websocket, {
                        "type": "error",
                        "message": "지원하지 않는 액션입니다.",
                        "received_action": message.get('action')
                    })
                    
            except json.JSONDecodeError:
                await websocket_manager.send_personal_message(websocket, {
                    "type": "error", 
                    "message": "잘못된 JSON 형식입니다."
                })
            except Exception as e:
                logger.error(f"메시지 처리 오류: {e}")
                await websocket_manager.send_personal_message(websocket, {
                    "type": "error",
                    "message": "메시지 처리 중 오류가 발생했습니다."
                })
                
    except WebSocketDisconnect:
        logger.info("WebSocket 클라이언트 연결 해제")
    except Exception as e:
        logger.error(f"WebSocket 연결 오류: {e}")
    finally:
        # 연결 정리
        websocket_manager.disconnect(websocket)

@router.get("/status")
async def get_realtime_status():
    """
    실시간 서비스 상태 조회
    
    Returns:
        dict: 현재 실시간 서비스 상태 정보
    """
    try:
        return JSONResponse({
            "status": "active" if realtime_service.is_running else "inactive",
            "active_connections": websocket_manager.get_connection_count(),
            "monitored_symbols": list(websocket_manager.get_subscribed_symbols()),
            "alert_thresholds": realtime_service.alert_thresholds,
            "message": "실시간 주식 알림 서비스가 정상 작동 중입니다." if realtime_service.is_running else "실시간 서비스가 비활성 상태입니다."
        })
    except Exception as e:
        logger.error(f"실시간 서비스 상태 조회 오류: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "서비스 상태 조회 중 오류가 발생했습니다."}
        )

@router.post("/start")
async def start_realtime_service():
    """
    실시간 모니터링 서비스 시작
    
    Returns:
        dict: 서비스 시작 결과
    """
    try:
        if realtime_service.is_running:
            return JSONResponse({
                "status": "already_running",
                "message": "실시간 서비스가 이미 실행 중입니다."
            })
        
        await realtime_service.initialize()
        await realtime_service.start_monitoring()
        
        return JSONResponse({
            "status": "started",
            "message": "실시간 주식 모니터링 서비스가 시작되었습니다.",
            "active_connections": websocket_manager.get_connection_count()
        })
        
    except Exception as e:
        logger.error(f"실시간 서비스 시작 오류: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "실시간 서비스 시작 중 오류가 발생했습니다."}
        )

@router.post("/stop")
async def stop_realtime_service():
    """
    실시간 모니터링 서비스 중지
    
    Returns:
        dict: 서비스 중지 결과
    """
    try:
        if not realtime_service.is_running:
            return JSONResponse({
                "status": "already_stopped",
                "message": "실시간 서비스가 이미 중지되어 있습니다."
            })
        
        await realtime_service.stop_monitoring()
        
        return JSONResponse({
            "status": "stopped",
            "message": "실시간 주식 모니터링 서비스가 중지되었습니다."
        })
        
    except Exception as e:
        logger.error(f"실시간 서비스 중지 오류: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "실시간 서비스 중지 중 오류가 발생했습니다."}
        )

@router.get("/connections")
async def get_connection_info():
    """
    현재 WebSocket 연결 정보 조회
    
    Returns:
        dict: 연결 상태 정보
    """
    try:
        subscribed_symbols = websocket_manager.get_subscribed_symbols()
        symbol_stats = {}
        
        for symbol in subscribed_symbols:
            symbol_stats[symbol] = websocket_manager.get_symbol_subscriber_count(symbol)
        
        return JSONResponse({
            "total_connections": websocket_manager.get_connection_count(),
            "total_subscribed_symbols": len(subscribed_symbols),
            "symbol_subscribers": symbol_stats,
            "service_status": "active" if realtime_service.is_running else "inactive"
        })
        
    except Exception as e:
        logger.error(f"연결 정보 조회 오류: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "연결 정보 조회 중 오류가 발생했습니다."}
        )