"""
WebSocket 연결 관리자
실시간 주식 알림을 위한 WebSocket 연결들을 관리합니다.
"""

from typing import Dict, List, Set
from fastapi import WebSocket, WebSocketDisconnect
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class WebSocketManager:
    def __init__(self):
        # 활성 WebSocket 연결들
        self.active_connections: List[WebSocket] = []
        # 각 연결별 구독 종목들
        self.connection_subscriptions: Dict[WebSocket, Set[str]] = {}
        # 종목별 구독자들
        self.symbol_subscribers: Dict[str, Set[WebSocket]] = {}
        
    async def connect(self, websocket: WebSocket):
        """새로운 WebSocket 연결을 수락하고 관리 목록에 추가"""
        await websocket.accept()
        self.active_connections.append(websocket)
        self.connection_subscriptions[websocket] = set()
        logger.info(f"새로운 WebSocket 연결: {websocket.client}. 총 연결 수: {len(self.active_connections)}")
        
        # 환영 메시지 전송
        await self.send_personal_message(websocket, {
            "type": "welcome",
            "message": "실시간 주식 알림 서비스에 연결되었습니다",
            "timestamp": datetime.now().isoformat(),
            "connection_count": len(self.active_connections)
        })

    def disconnect(self, websocket: WebSocket):
        """WebSocket 연결을 종료하고 관리 목록에서 제거"""
        try:
            # 연결 목록에서 제거
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)
            
            # 구독 정보 정리
            if websocket in self.connection_subscriptions:
                subscribed_symbols = self.connection_subscriptions[websocket]
                for symbol in subscribed_symbols:
                    if symbol in self.symbol_subscribers:
                        self.symbol_subscribers[symbol].discard(websocket)
                        # 구독자가 없으면 종목 삭제
                        if not self.symbol_subscribers[symbol]:
                            del self.symbol_subscribers[symbol]
                
                del self.connection_subscriptions[websocket]
            
            logger.info(f"WebSocket 연결 종료. 남은 연결 수: {len(self.active_connections)}")
            
        except Exception as e:
            logger.error(f"WebSocket 연결 종료 중 오류: {e}")

    async def send_personal_message(self, websocket: WebSocket, message: dict):
        """특정 WebSocket 연결에 메시지 전송"""
        try:
            await websocket.send_text(json.dumps(message, ensure_ascii=False))
        except Exception as e:
            logger.error(f"개인 메시지 전송 실패: {e}")
            self.disconnect(websocket)

    async def broadcast_to_all(self, message: dict):
        """모든 연결된 클라이언트에게 메시지 브로드캐스트"""
        if not self.active_connections:
            return
        
        message_text = json.dumps(message, ensure_ascii=False)
        disconnected_connections = []
        
        for connection in self.active_connections:
            try:
                await connection.send_text(message_text)
            except Exception as e:
                logger.error(f"브로드캐스트 실패: {e}")
                disconnected_connections.append(connection)
        
        # 실패한 연결들 정리
        for connection in disconnected_connections:
            self.disconnect(connection)

    async def broadcast_to_symbol_subscribers(self, symbol: str, message: dict):
        """특정 종목 구독자들에게만 메시지 전송"""
        if symbol not in self.symbol_subscribers:
            return
        
        message_text = json.dumps(message, ensure_ascii=False)
        disconnected_connections = []
        
        for connection in self.symbol_subscribers[symbol].copy():
            try:
                await connection.send_text(message_text)
            except Exception as e:
                logger.error(f"종목별 브로드캐스트 실패: {e}")
                disconnected_connections.append(connection)
        
        # 실패한 연결들 정리
        for connection in disconnected_connections:
            self.disconnect(connection)

    def subscribe_to_symbol(self, websocket: WebSocket, symbol: str):
        """클라이언트가 특정 종목을 구독"""
        if websocket not in self.connection_subscriptions:
            self.connection_subscriptions[websocket] = set()
        
        self.connection_subscriptions[websocket].add(symbol)
        
        if symbol not in self.symbol_subscribers:
            self.symbol_subscribers[symbol] = set()
        
        self.symbol_subscribers[symbol].add(websocket)
        logger.info(f"종목 구독: {symbol}, 구독자 수: {len(self.symbol_subscribers[symbol])}")

    def unsubscribe_from_symbol(self, websocket: WebSocket, symbol: str):
        """클라이언트가 특정 종목 구독 해제"""
        if websocket in self.connection_subscriptions:
            self.connection_subscriptions[websocket].discard(symbol)
        
        if symbol in self.symbol_subscribers:
            self.symbol_subscribers[symbol].discard(websocket)
            if not self.symbol_subscribers[symbol]:
                del self.symbol_subscribers[symbol]
        
        logger.info(f"종목 구독 해제: {symbol}")

    def get_subscribed_symbols(self) -> Set[str]:
        """현재 구독 중인 모든 종목 목록 반환"""
        return set(self.symbol_subscribers.keys())

    def get_connection_count(self) -> int:
        """현재 활성 연결 수 반환"""
        return len(self.active_connections)

    def get_symbol_subscriber_count(self, symbol: str) -> int:
        """특정 종목의 구독자 수 반환"""
        return len(self.symbol_subscribers.get(symbol, set()))

# 전역 WebSocket 관리자 인스턴스
websocket_manager = WebSocketManager()