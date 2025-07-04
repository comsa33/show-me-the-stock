import React, { useState, useEffect, useRef } from 'react';
import { Send, X, Loader2, Bot, User } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { API_BASE } from '../../config';
import './ChatView.css';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  isStreaming?: boolean;
}

interface ChatViewProps {
  isFloating?: boolean;
  onClose?: () => void;
}

const ChatView: React.FC<ChatViewProps> = ({ isFloating = false, onClose }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const eventSourceRef = useRef<EventSource | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  // 세션 ID 로드 및 히스토리 가져오기
  useEffect(() => {
    const savedSessionId = localStorage.getItem('chatSessionId');
    if (savedSessionId) {
      setSessionId(savedSessionId);
      // 히스토리를 매번 로드
      loadChatHistory(savedSessionId);
    }
  }, []);

  // 메시지 스크롤
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Cleanup on unmount
  useEffect(() => {
    // Store refs in local variables to avoid stale closure issues
    const abortController = abortControllerRef.current;
    const eventSource = eventSourceRef.current;
    
    return () => {
      // Abort any ongoing fetch requests
      if (abortController) {
        abortController.abort();
      }
      // Close any EventSource connections
      if (eventSource) {
        eventSource.close();
      }
    };
  }, []);

  const loadChatHistory = async (sessionId: string) => {
    try {
      const response = await fetch(`${API_BASE}/v1/chat/history/${sessionId}`);
      const data = await response.json();
      if (data.history && data.history.length > 0) {
        const formattedHistory = data.history.map((msg: any) => ({
          role: msg.role === 'user' ? 'user' : 'assistant',
          content: msg.content,
          timestamp: new Date(msg.timestamp),
          isStreaming: false // 히스토리는 스트리밍 중이 아님
        }));
        setMessages(formattedHistory);
      }
    } catch (error) {
      console.error('Failed to load chat history:', error);
    }
  };

  const sendMessage = async () => {
    if (!input.trim() || isLoading) return;

    // Cancel any ongoing request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    const userMessage: Message = {
      role: 'user',
      content: input.trim(),
      timestamp: new Date()
    };

    // 먼저 사용자 메시지를 추가하고
    const newMessages = [...messages, userMessage];
    setMessages(newMessages);
    setInput('');
    setIsLoading(true);

    // AI 응답 메시지 플레이스홀더 추가
    const assistantMessage: Message = {
      role: 'assistant',
      content: '',
      timestamp: new Date(),
      isStreaming: true
    };
    
    // 올바른 인덱스 계산: 현재 메시지 배열의 길이가 assistant 메시지의 인덱스
    const assistantMessageIndex = newMessages.length;
    setMessages(prev => [...prev, assistantMessage]);

    // Create new AbortController for this request
    const abortController = new AbortController();
    abortControllerRef.current = abortController;

    // 먼저 POST 요청으로 메시지 전송
    try {
      const response = await fetch(`${API_BASE}/v1/chat/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Cache-Control': 'no-cache',
        },
        body: JSON.stringify({
          message: userMessage.content,
          session_id: sessionId
        }),
        signal: abortController.signal,
        cache: 'no-cache'
      });

      if (!response.ok) {
        throw new Error('Failed to send message');
      }

      // Response body를 통한 실시간 스트리밍
      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (!reader) {
        throw new Error('No response body');
      }

      let buffer = '';
      let accumulatedContent = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        // 디코딩된 청크를 버퍼에 추가
        buffer += decoder.decode(value, { stream: true });
        
        // 완전한 라인들을 처리
        const lines = buffer.split('\n');
        buffer = lines.pop() || ''; // 마지막 불완전한 라인은 버퍼에 보관

        for (const line of lines) {
          if (line.trim() === '') continue;
          
          if (line.startsWith('data: ')) {
            try {
              const jsonStr = line.slice(6).trim();
              if (jsonStr === '') continue;
              
              const data = JSON.parse(jsonStr);
              
              if (data.type === 'session' && !sessionId) {
                setSessionId(data.session_id);
                localStorage.setItem('chatSessionId', data.session_id);
              } else if (data.type === 'message') {
                accumulatedContent += data.content;
                const currentContent = accumulatedContent; // Capture current value
                // console.log('Streaming chunk:', data.content); // 디버깅용
                setMessages(prev => {
                  const newMessages = [...prev];
                  newMessages[assistantMessageIndex] = {
                    ...newMessages[assistantMessageIndex],
                    content: currentContent,
                    isStreaming: true
                  };
                  return newMessages;
                });
              } else if (data.type === 'end') {
                setMessages(prev => {
                  const newMessages = [...prev];
                  newMessages[assistantMessageIndex] = {
                    ...newMessages[assistantMessageIndex],
                    isStreaming: false
                  };
                  return newMessages;
                });
              } else if (data.type === 'error') {
                throw new Error(data.message);
              }
            } catch (e) {
              console.error('Error parsing SSE data:', e, 'Line:', line);
            }
          }
        }
      }

      // 남은 버퍼 처리
      if (buffer.trim() !== '' && buffer.startsWith('data: ')) {
        try {
          const data = JSON.parse(buffer.slice(6));
          if (data.type === 'message') {
            accumulatedContent += data.content;
            const finalContent = accumulatedContent; // Capture final value
            setMessages(prev => {
              const newMessages = [...prev];
              newMessages[assistantMessageIndex] = {
                ...newMessages[assistantMessageIndex],
                content: finalContent,
                isStreaming: false
              };
              return newMessages;
            });
          }
        } catch (e) {
          console.error('Error parsing final buffer:', e);
        }
      }

    } catch (error: any) {
      // Don't show error for aborted requests
      if (error.name === 'AbortError') {
        console.log('Request was aborted');
        return;
      }
      
      console.error('Chat error:', error);
      setMessages(prev => {
        const newMessages = [...prev];
        newMessages[assistantMessageIndex] = {
          ...newMessages[assistantMessageIndex],
          content: '죄송합니다. 메시지 전송 중 오류가 발생했습니다.',
          isStreaming: false
        };
        return newMessages;
      });
    } finally {
      setIsLoading(false);
      // Clear abort controller reference
      if (abortControllerRef.current?.signal.aborted) {
        abortControllerRef.current = null;
      }
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const clearChat = () => {
    if (sessionId) {
      fetch(`${API_BASE}/v1/chat/session/${sessionId}`, {
        method: 'DELETE'
      });
      localStorage.removeItem('chatSessionId');
    }
    setMessages([]);
    setSessionId(null);
  };

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString('ko-KR', { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  return (
    <div className={`chat-view ${isFloating ? 'floating' : ''}`}>
      <div className="chat-header">
        <div className="chat-header-info">
          <Bot size={24} />
          <div>
            <h3>AI 투자 어시스턴트</h3>
            <p>주식 투자에 대해 무엇이든 물어보세요</p>
          </div>
        </div>
        <div className="chat-header-actions">
          <button 
            className="clear-btn" 
            onClick={clearChat}
            title="대화 초기화"
          >
            새 대화
          </button>
          {isFloating && (
            <button 
              className="close-btn" 
              onClick={onClose}
              title="닫기"
            >
              <X size={20} />
            </button>
          )}
        </div>
      </div>

      <div className="chat-messages">
        {messages.length === 0 && (
          <div className="empty-state">
            <Bot size={48} />
            <h4>안녕하세요! AI 투자 어시스턴트입니다</h4>
            <p>주식 투자에 대한 궁금한 점을 물어보세요</p>
            <div className="suggested-questions">
              <button onClick={() => setInput('퀀트 투자란 무엇인가요?')}>
                퀀트 투자란 무엇인가요?
              </button>
              <button onClick={() => setInput('PER과 PBR의 차이점은?')}>
                PER과 PBR의 차이점은?
              </button>
              <button onClick={() => setInput('백테스트는 어떻게 활용하나요?')}>
                백테스트는 어떻게 활용하나요?
              </button>
            </div>
          </div>
        )}

        {messages.map((message, index) => (
          <div 
            key={`${message.role}-${index}-${message.timestamp.getTime()}`} 
            className={`message ${message.role}`}
          >
            <div className="message-avatar">
              {message.role === 'user' ? <User size={20} /> : <Bot size={20} />}
            </div>
            <div className="message-content">
              <div className="message-bubble">
                {message.role === 'assistant' ? (
                  <>
                    {message.isStreaming ? (
                      // 스트리밍 중에는 plain text로 표시
                      <div className="streaming-content">
                        <span className="streaming-text">{message.content}</span>
                        <span className="typing-indicator"></span>
                      </div>
                    ) : (
                      // 스트리밍 완료 후 마크다운 렌더링
                      <div className="markdown-content">
                        <ReactMarkdown remarkPlugins={[remarkGfm]}>
                          {message.content}
                        </ReactMarkdown>
                      </div>
                    )}
                  </>
                ) : (
                  message.content
                )}
              </div>
              <div className="message-time">
                {formatTime(message.timestamp)}
              </div>
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      <div className="chat-input-container">
        <textarea
          className="chat-input"
          placeholder="메시지를 입력하세요..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyPress}
          disabled={isLoading}
          rows={1}
        />
        <button 
          className="send-btn"
          onClick={sendMessage}
          disabled={!input.trim() || isLoading}
        >
          {isLoading ? <Loader2 size={20} className="spinning" /> : <Send size={20} />}
        </button>
      </div>
    </div>
  );
};

export default ChatView;