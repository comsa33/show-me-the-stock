"""
AI 챗봇 API (Gemini 멀티턴 스트리밍)
"""

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Optional
import json
import asyncio
import logging
from datetime import datetime

from google import genai
from google.genai import types

from app.core.config import get_settings
from app.core.redis_client import RedisClient
import uuid

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["Chat"])

# 설정 가져오기
settings = get_settings()

# Gemini 클라이언트 생성
client = genai.Client(api_key=settings.gemini_api_key)

# Redis 클라이언트
redis_client = RedisClient.get_instance()

class ChatMessage(BaseModel):
    message: str
    session_id: Optional[str] = None

class ChatSession:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.chat = client.chats.create(
            model="gemini-2.5-flash-lite-preview-06-17",
            config=types.GenerateContentConfig(
                max_output_tokens=64000,
                thinking_config=types.ThinkingConfig(
                    thinking_budget=0
                )
            )
        )
        self.created_at = datetime.now()
        
    def is_expired(self, timeout_minutes: int = 30) -> bool:
        """세션이 만료되었는지 확인 (30분)"""
        return (datetime.now() - self.created_at).total_seconds() > timeout_minutes * 60

# 메모리 기반 세션 관리 (실제로는 Redis 등을 사용하는 것이 좋음)
chat_sessions: Dict[str, ChatSession] = {}
last_cleanup_time = datetime.now()

async def cleanup_expired_sessions():
    """만료된 세션 정리"""
    global last_cleanup_time
    current_time = datetime.now()
    
    # 5분마다 정리 수행
    if (current_time - last_cleanup_time).total_seconds() < 300:
        return
    
    expired_sessions = []
    for session_id, session in chat_sessions.items():
        if session.is_expired():
            expired_sessions.append(session_id)
    
    for session_id in expired_sessions:
        del chat_sessions[session_id]
        logger.info(f"Expired session cleaned up: {session_id}")
    
    last_cleanup_time = current_time
    if expired_sessions:
        logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")

def get_or_create_session(session_id: Optional[str] = None) -> tuple[str, ChatSession]:
    """세션 가져오기 또는 생성"""
    if not session_id:
        session_id = str(uuid.uuid4())
    
    if session_id in chat_sessions:
        session = chat_sessions[session_id]
        if not session.is_expired():
            return session_id, session
        else:
            # 만료된 세션 삭제
            del chat_sessions[session_id]
    
    # 새 세션 생성
    session = ChatSession(session_id)
    chat_sessions[session_id] = session
    
    # 세션 수 제한 (메모리 관리)
    if len(chat_sessions) > 100:
        # 가장 오래된 세션 삭제
        oldest_id = min(chat_sessions.keys(), 
                       key=lambda k: chat_sessions[k].created_at)
        del chat_sessions[oldest_id]
    
    return session_id, session

async def generate_sse_response(message: str, session_id: Optional[str] = None):
    """SSE 형식으로 스트리밍 응답 생성"""
    # 주기적으로 만료된 세션 정리
    await cleanup_expired_sessions()
    
    session_id, session = get_or_create_session(session_id)
    
    try:
        # 시스템 프롬프트 설정 (첫 메시지인 경우)
        if len(session.chat.get_history()) == 0:
            system_prompt = """당신은 'Show Me The Stock' 앱의 주식 투자 전문 AI 어시스턴트입니다. 

## 앱 정보
- **앱 이름**: Show Me The Stock (쇼미더스탁)
- **목적**: 한국과 미국 주식 시장에 대한 종합적인 정보 제공 및 투자 분석 플랫폼
- **주요 기능**:
  1. **대시보드**: 한국/미국 주요 지수, 인기 종목, 거래량 상위 종목 실시간 표시
  2. **종목 검색**: 한국과 미국 주식 통합 검색 (종목명, 티커로 검색 가능)
  3. **종목 분석**: AI 기반 기술적 분석, 투자 신호, 감정 분석 제공
  4. **백테스트**: 과거 데이터 기반 투자 전략 시뮬레이션
  5. **뉴스**: 실시간 주식 관련 뉴스와 AI 요약
  6. **퀀트 분석**: 모멘텀, 기술적 지표 기반 종목 추천
  7. **포트폴리오**: 보유 종목 관리 및 수익률 추적
- **지원 시장**: 한국 (KOSPI, KOSDAQ), 미국 (NYSE, NASDAQ)
- **데이터 소스**: 실시간 시장 데이터, pykrx, yfinance, FinanceDataReader

## 답변 가이드라인
- 사용자의 주식 투자 관련 질문에 친절하고 전문적으로 답변해주세요
- 한국과 미국 주식 시장에 대한 지식이 풍부합니다
- 기술적 분석, 펀더멘털 분석, 퀀트 투자 등 다양한 투자 방법론에 대해 설명할 수 있습니다
- 앱의 기능을 활용한 투자 방법을 안내할 수 있습니다
- 구체적인 투자 조언보다는 교육적이고 정보 제공 차원의 답변을 합니다
- 항상 투자의 위험성을 함께 안내합니다"""
            
            # 시스템 프롬프트를 첫 번째 메시지로 전송
            session.chat.send_message(system_prompt)
        
        # 세션 ID 전송
        yield f"data: {json.dumps({'type': 'session', 'session_id': session_id})}\n\n"
        
        # 사용자 메시지에 대한 응답 스트리밍
        response_stream = session.chat.send_message_stream(message)
        
        for chunk in response_stream:
            if chunk.text:
                # SSE 형식으로 전송
                data = {
                    'type': 'message',
                    'content': chunk.text
                }
                response_text = f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
                yield response_text
                await asyncio.sleep(0.01)  # 10ms 딜레이로 부드러운 스트리밍
        
        # 스트림 종료 신호
        yield f"data: {json.dumps({'type': 'end'})}\n\n"
        
    except Exception as e:
        logger.error(f"Chat streaming error: {str(e)}")
        error_data = {
            'type': 'error',
            'message': '응답 생성 중 오류가 발생했습니다.'
        }
        yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"

@router.post("/stream")
async def stream_chat(chat_message: ChatMessage):
    """스트리밍 챗봇 응답"""
    if not chat_message.message.strip():
        raise HTTPException(status_code=400, detail="메시지가 비어있습니다")
    
    return StreamingResponse(
        generate_sse_response(chat_message.message, chat_message.session_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "X-Accel-Buffering": "no",  # Nginx 버퍼링 비활성화
            "Connection": "keep-alive",
            "Content-Encoding": "none",  # 압축 비활성화
        }
    )

@router.get("/history/{session_id}")
async def get_chat_history(session_id: str):
    """채팅 히스토리 가져오기"""
    if session_id not in chat_sessions:
        return {"history": []}
    
    session = chat_sessions[session_id]
    if session.is_expired():
        del chat_sessions[session_id]
        return {"history": []}
    
    try:
        history = session.chat.get_history()
        
        # 시스템 프롬프트 제외하고 반환
        formatted_history = []
        skip_next = False
        
        # 연속된 메시지를 하나로 합치기 위한 변수
        current_user_message = None
        current_model_message = None
        
        for i, message in enumerate(history):
            # 첫 번째 메시지가 시스템 프롬프트인 경우 제외
            if i == 0 and message.role == "user" and message.parts and len(message.parts) > 0:
                text_content = getattr(message.parts[0], 'text', None)
                if text_content and "주식 투자 전문 AI" in text_content:
                    skip_next = True  # 다음 응답도 건너뛰기
                    continue
            
            # 시스템 프롬프트에 대한 응답 건너뛰기
            if skip_next and message.role == "model":
                skip_next = False
                continue
            
            # 사용자 메시지 처리
            if message.role == "user":
                # 이전 model 메시지가 있으면 먼저 저장
                if current_model_message:
                    formatted_history.append(current_model_message)
                    current_model_message = None
                
                # 새로운 user 메시지 시작
                if message.parts and len(message.parts) > 0:
                    content_parts = []
                    for part in message.parts:
                        if hasattr(part, 'text'):
                            content_parts.append(part.text)
                    
                    if content_parts:
                        current_user_message = {
                            "role": "user",
                            "content": "".join(content_parts),
                            "timestamp": datetime.now().isoformat()
                        }
                        formatted_history.append(current_user_message)
            
            # 모델 메시지 처리
            elif message.role == "model":
                if message.parts and len(message.parts) > 0:
                    content_parts = []
                    for part in message.parts:
                        if hasattr(part, 'text'):
                            content_parts.append(part.text)
                    
                    if content_parts:
                        # 현재 model 메시지가 없으면 새로 생성
                        if not current_model_message:
                            current_model_message = {
                                "role": "assistant",
                                "content": "".join(content_parts),
                                "timestamp": datetime.now().isoformat()
                            }
                        else:
                            # 이미 있으면 내용 추가 (연속된 model 응답인 경우)
                            current_model_message["content"] += "".join(content_parts)
        
        # 마지막 model 메시지가 있으면 추가
        if current_model_message:
            formatted_history.append(current_model_message)
        
        return {"history": formatted_history}
    except Exception as e:
        logger.error(f"Error getting history: {str(e)}")
        # Debug logging without causing errors
        try:
            if 'history' in locals() and history:
                logger.error(f"History length: {len(history)}")
        except Exception:
            pass
        return {"history": []}

@router.delete("/session/{session_id}")
async def clear_session(session_id: str):
    """세션 삭제"""
    if session_id in chat_sessions:
        del chat_sessions[session_id]
    
    return {"message": "세션이 삭제되었습니다"}

@router.get("/status")
async def get_chat_status():
    """챗봇 상태 확인"""
    active_sessions = len(chat_sessions)
    
    # 만료된 세션 정리
    expired_sessions = [sid for sid, session in chat_sessions.items() 
                       if session.is_expired()]
    for sid in expired_sessions:
        del chat_sessions[sid]
    
    return {
        "status": "active",
        "active_sessions": active_sessions - len(expired_sessions),
        "cleaned_sessions": len(expired_sessions)
    }