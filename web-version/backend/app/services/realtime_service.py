"""
실시간 주식 데이터 수집 및 알림 서비스
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
import pandas as pd
from pykrx import stock as krx_stock
import yfinance as yf
import redis.asyncio as redis

from app.core.config import get_settings
from app.core.websocket_manager import websocket_manager
# from app.services.stock_service import StockDataService  # 필요시 사용

logger = logging.getLogger(__name__)
settings = get_settings()

class RealTimeStockService:
    def __init__(self):
        # self.stocks_service = StockDataService()  # 필요시 사용
        self.redis_client: Optional[redis.Redis] = None
        self.is_running = False
        self.background_tasks: Set[asyncio.Task] = set()
        
        # 알림 설정
        self.alert_thresholds = {
            'minor': 3.0,    # 3% 변동
            'major': 5.0,    # 5% 변동  
            'critical': 10.0  # 10% 변동
        }
        
        # 이전 가격 캐시 (변동률 계산용)
        self.previous_prices: Dict[str, float] = {}
        
        # 인기 종목 리스트 (기본 모니터링 대상)
        self.default_symbols = {
            'KR': ['005930', '000660', '035420', '051910', '005380', '068270'],  # 삼성전자, SK하이닉스 등
            'US': ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META']  # 미국 주요 종목
        }

    async def initialize(self):
        """서비스 초기화"""
        try:
            self.redis_client = redis.from_url(settings.redis_url)
            await self.redis_client.ping()
            logger.info("실시간 주식 서비스 초기화 완료")
        except Exception as e:
            logger.error(f"실시간 주식 서비스 초기화 실패: {e}")
            self.redis_client = None

    async def start_monitoring(self):
        """실시간 모니터링 시작"""
        if self.is_running:
            logger.warning("실시간 모니터링이 이미 실행 중입니다")
            return
        
        self.is_running = True
        logger.info("실시간 주식 모니터링 시작")
        
        # 백그라운드 태스크들 시작
        tasks = [
            asyncio.create_task(self._monitor_korean_stocks()),
            asyncio.create_task(self._monitor_us_stocks()),
            asyncio.create_task(self._monitor_market_hours()),
            asyncio.create_task(self._send_heartbeat())
        ]
        
        for task in tasks:
            self.background_tasks.add(task)
            task.add_done_callback(self.background_tasks.discard)

    async def stop_monitoring(self):
        """실시간 모니터링 중지"""
        self.is_running = False
        
        # 모든 백그라운드 태스크 취소
        for task in self.background_tasks:
            task.cancel()
        
        if self.background_tasks:
            await asyncio.gather(*self.background_tasks, return_exceptions=True)
        
        self.background_tasks.clear()
        
        if self.redis_client:
            await self.redis_client.close()
        
        logger.info("실시간 주식 모니터링 중지")

    async def _monitor_korean_stocks(self):
        """한국 주식 모니터링"""
        while self.is_running:
            try:
                await self._process_korean_market()
                await asyncio.sleep(30)  # 30초마다 체크
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"한국 주식 모니터링 오류: {e}")
                await asyncio.sleep(60)  # 오류 시 1분 대기

    async def _monitor_us_stocks(self):
        """미국 주식 모니터링"""
        while self.is_running:
            try:
                await self._process_us_market()
                await asyncio.sleep(30)  # 30초마다 체크
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"미국 주식 모니터링 오류: {e}")
                await asyncio.sleep(60)  # 오류 시 1분 대기

    async def _process_korean_market(self):
        """한국 시장 데이터 처리"""
        # 현재 구독 중인 한국 종목들 + 기본 모니터링 종목들
        subscribed_symbols = {s for s in websocket_manager.get_subscribed_symbols() 
                            if len(s) == 6 and s.isdigit()}
        symbols_to_monitor = subscribed_symbols.union(self.default_symbols['KR'])
        
        if not symbols_to_monitor:
            return
        
        try:
            # pykrx로 실시간 가격 정보 수집
            current_prices = {}
            
            for symbol in symbols_to_monitor:
                try:
                    # 당일 주가 정보
                    today = datetime.now().strftime('%Y%m%d')
                    df = krx_stock.get_market_ohlcv_by_date(today, today, symbol)
                    
                    if not df.empty:
                        current_price = float(df.iloc[-1]['종가'])
                        current_prices[symbol] = current_price
                        
                        # 가격 변동 체크 및 알림 발송
                        await self._check_price_alert(symbol, current_price, 'KR')
                        
                except Exception as e:
                    logger.debug(f"종목 {symbol} 데이터 수집 실패: {e}")
                    continue
            
            # WebSocket으로 실시간 가격 전송
            if current_prices:
                await websocket_manager.broadcast_to_all({
                    "type": "price_update",
                    "market": "KR",
                    "data": current_prices,
                    "timestamp": datetime.now().isoformat()
                })
                
        except Exception as e:
            logger.error(f"한국 시장 데이터 처리 오류: {e}")

    async def _process_us_market(self):
        """미국 시장 데이터 처리"""
        # 현재 구독 중인 미국 종목들 + 기본 모니터링 종목들
        subscribed_symbols = {s for s in websocket_manager.get_subscribed_symbols() 
                            if not (len(s) == 6 and s.isdigit())}
        symbols_to_monitor = subscribed_symbols.union(self.default_symbols['US'])
        
        if not symbols_to_monitor:
            return
        
        try:
            # yfinance로 실시간 가격 정보 수집
            current_prices = {}
            
            for symbol in symbols_to_monitor:
                try:
                    ticker = yf.Ticker(symbol)
                    info = ticker.info
                    
                    current_price = info.get('currentPrice') or info.get('regularMarketPrice')
                    if current_price:
                        current_prices[symbol] = float(current_price)
                        
                        # 가격 변동 체크 및 알림 발송
                        await self._check_price_alert(symbol, current_price, 'US')
                        
                except Exception as e:
                    logger.debug(f"종목 {symbol} 데이터 수집 실패: {e}")
                    continue
            
            # WebSocket으로 실시간 가격 전송
            if current_prices:
                await websocket_manager.broadcast_to_all({
                    "type": "price_update",
                    "market": "US", 
                    "data": current_prices,
                    "timestamp": datetime.now().isoformat()
                })
                
        except Exception as e:
            logger.error(f"미국 시장 데이터 처리 오류: {e}")

    async def _check_price_alert(self, symbol: str, current_price: float, market: str):
        """가격 변동 알림 체크"""
        cache_key = f"{market}:{symbol}"
        
        if cache_key in self.previous_prices:
            previous_price = self.previous_prices[cache_key]
            change_percent = ((current_price - previous_price) / previous_price) * 100
            abs_change = abs(change_percent)
            
            # 임계값에 따른 알림 생성
            alert_level = None
            if abs_change >= self.alert_thresholds['critical']:
                alert_level = 'critical'
            elif abs_change >= self.alert_thresholds['major']:
                alert_level = 'high'
            elif abs_change >= self.alert_thresholds['minor']:
                alert_level = 'medium'
            
            if alert_level:
                await self._send_price_alert(symbol, current_price, previous_price, 
                                           change_percent, alert_level, market)
        
        # 현재 가격을 이전 가격으로 저장
        self.previous_prices[cache_key] = current_price

    async def _send_price_alert(self, symbol: str, current_price: float, 
                              previous_price: float, change_percent: float, 
                              alert_level: str, market: str):
        """가격 변동 알림 전송"""
        # 종목명 가져오기
        try:
            if market == 'KR':
                stock_name = krx_stock.get_market_ticker_name(symbol)
            else:
                ticker = yf.Ticker(symbol)
                stock_name = ticker.info.get('longName', symbol)
        except:
            stock_name = symbol
        
        # 알림 메시지 생성
        direction = "상승" if change_percent > 0 else "하락"
        emoji = "🚀" if change_percent > 0 else "📉"
        
        if alert_level == 'critical':
            emoji = "🚀" if change_percent > 0 else "🔥"
            title = f"{emoji} 급{direction} 알림"
        elif alert_level == 'high':
            title = f"{emoji} {direction} 알림"
        else:
            title = f"{emoji} 소폭 {direction}"
        
        alert_message = {
            "type": "price_alert",
            "id": f"price_{symbol}_{int(datetime.now().timestamp() * 1000)}",
            "alert_level": alert_level,
            "symbol": symbol,
            "stock_name": stock_name,
            "market": market,
            "title": title,
            "message": f"{stock_name}({symbol})이(가) {change_percent:.2f}% {direction}했습니다.",
            "data": {
                "current_price": current_price,
                "previous_price": previous_price,
                "change_percent": change_percent,
                "change_amount": current_price - previous_price
            },
            "timestamp": datetime.now().isoformat()
        }
        
        # 모든 클라이언트에게 알림 전송
        await websocket_manager.broadcast_to_all(alert_message)
        
        logger.info(f"가격 알림 전송: {symbol} {change_percent:.2f}% {direction}")

    async def _monitor_market_hours(self):
        """시장 시간 모니터링 및 알림"""
        while self.is_running:
            try:
                now = datetime.now()
                
                # 한국 시장 시간 체크 (KST 09:00)
                if now.hour == 9 and now.minute == 0 and now.second < 30:
                    await websocket_manager.broadcast_to_all({
                        "type": "market_alert",
                        "id": f"market_open_kr_{int(now.timestamp() * 1000)}",
                        "alert_level": "medium",
                        "title": "🇰🇷 한국 증시 개장",
                        "message": "코스피/코스닥 장이 개장되었습니다.",
                        "market": "KR",
                        "timestamp": now.isoformat()
                    })
                
                # 미국 시장 시간 체크는 복잡하므로 간소화
                # (실제로는 서머타임 등을 고려해야 함)
                
                await asyncio.sleep(30)  # 30초마다 체크
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"시장 시간 모니터링 오류: {e}")
                await asyncio.sleep(60)

    async def _send_heartbeat(self):
        """WebSocket 연결 유지를 위한 heartbeat"""
        while self.is_running:
            try:
                if websocket_manager.get_connection_count() > 0:
                    await websocket_manager.broadcast_to_all({
                        "type": "heartbeat",
                        "timestamp": datetime.now().isoformat(),
                        "active_connections": websocket_manager.get_connection_count()
                    })
                
                await asyncio.sleep(30)  # 30초마다 heartbeat
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Heartbeat 전송 오류: {e}")
                await asyncio.sleep(60)

    async def handle_client_subscription(self, websocket, message: dict):
        """클라이언트의 구독 요청 처리"""
        try:
            action = message.get('action')
            symbols = message.get('symbols', [])
            
            if action == 'subscribe':
                for symbol in symbols:
                    websocket_manager.subscribe_to_symbol(websocket, symbol)
                
                await websocket_manager.send_personal_message(websocket, {
                    "type": "subscription_confirmed",
                    "symbols": symbols,
                    "message": f"{len(symbols)}개 종목 구독이 완료되었습니다.",
                    "timestamp": datetime.now().isoformat()
                })
                
            elif action == 'unsubscribe':
                for symbol in symbols:
                    websocket_manager.unsubscribe_from_symbol(websocket, symbol)
                
                await websocket_manager.send_personal_message(websocket, {
                    "type": "unsubscription_confirmed", 
                    "symbols": symbols,
                    "message": f"{len(symbols)}개 종목 구독이 해제되었습니다.",
                    "timestamp": datetime.now().isoformat()
                })
                
        except Exception as e:
            logger.error(f"클라이언트 구독 처리 오류: {e}")
            await websocket_manager.send_personal_message(websocket, {
                "type": "error",
                "message": "구독 처리 중 오류가 발생했습니다.",
                "timestamp": datetime.now().isoformat()
            })

# 전역 실시간 서비스 인스턴스
realtime_service = RealTimeStockService()