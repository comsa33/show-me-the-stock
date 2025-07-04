import React, { useState, useRef, useEffect } from 'react';
import { MessageCircle, X } from 'lucide-react';
import ChatView from '../views/ChatView';
import '../views/ChatView.css';

const FloatingChatButton: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [position, setPosition] = useState({ x: 20, y: 80 }); // 우측 하단 기준, 모바일 고려
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0, time: 0 });
  const [hasMoved, setHasMoved] = useState(false);
  const buttonRef = useRef<HTMLButtonElement>(null);

  // 로컬 스토리지에서 위치 불러오기
  useEffect(() => {
    const savedPosition = localStorage.getItem('chatButtonPosition');
    const isDesktop = window.innerWidth >= 1025;
    
    if (savedPosition) {
      const pos = JSON.parse(savedPosition);
      
      // 데스크톱에서 사이드바/헤더 영역에 있으면 안전한 위치로 이동
      if (isDesktop) {
        const maxX = window.innerWidth - 280 - 70;
        const maxY = window.innerHeight - 64 - 70;
        
        setPosition({
          x: Math.min(maxX, pos.x), // 사이드바 영역 밖으로
          y: Math.min(maxY, pos.y)  // 헤더 영역 밖으로
        });
      } else {
        // 모바일에서도 화면 안에 있도록 확인
        setPosition({
          x: Math.min(window.innerWidth - 70, pos.x),
          y: Math.min(window.innerHeight - 70, pos.y)
        });
      }
    } else {
      // 저장된 위치가 없을 때 기본 위치 설정
      if (isDesktop) {
        // 데스크톱: 사이드바 왼쪽, 하단
        setPosition({ x: 300, y: 80 });
      } else {
        // 모바일: 우측 하단
        setPosition({ x: 20, y: 80 });
      }
    }
  }, []);

  // 위치 저장
  useEffect(() => {
    if (!isDragging) {
      localStorage.setItem('chatButtonPosition', JSON.stringify(position));
    }
  }, [position, isDragging]);

  // 창 크기 변경 시 위치 재조정
  useEffect(() => {
    const handleResize = () => {
      const isDesktop = window.innerWidth >= 1025;
      
      if (isDesktop) {
        const maxX = window.innerWidth - 280 - 70;
        const maxY = window.innerHeight - 64 - 70;
        
        setPosition(prev => ({
          x: Math.min(maxX, prev.x), // 사이드바 영역 밖으로
          y: Math.min(maxY, prev.y)  // 헤더 영역 밖으로
        }));
      }
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const handleMouseDown = (e: React.MouseEvent) => {
    const startTime = Date.now();
    setIsDragging(true);
    setHasMoved(false);
    setDragStart({
      x: e.clientX + position.x,
      y: e.clientY + position.y,
      time: startTime
    });
  };

  const handleTouchStart = (e: React.TouchEvent) => {
    const startTime = Date.now();
    setIsDragging(true);
    setHasMoved(false);
    const touch = e.touches[0];
    setDragStart({
      x: touch.clientX + position.x,
      y: touch.clientY + position.y,
      time: startTime
    });
  };

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isDragging) return;
      
      const newX = dragStart.x - e.clientX;
      const newY = dragStart.y - e.clientY;  // Fixed: calculation was inverted
      
      // Check if actually moved
      const distance = Math.sqrt(Math.pow(newX - position.x, 2) + Math.pow(newY - position.y, 2));
      if (distance > 5) {
        setHasMoved(true);
      }
      
      // 화면 경계 체크
      const isDesktop = window.innerWidth >= 1025;
      
      // 버튼이 화면 밖으로 나가지 않도록 제한
      let minX = 10;
      let maxX = window.innerWidth - 70;
      let minY = 10;
      let maxY = window.innerHeight - 70;
      
      // 데스크톱에서만 사이드바와 헤더 영역 제외
      if (isDesktop) {
        maxX = window.innerWidth - 280 - 70; // 오른쪽에서 사이드바(280px) + 버튼크기(70px)
        maxY = window.innerHeight - 64 - 70; // 아래에서 헤더(64px) + 버튼크기(70px)
      }
      
      setPosition({
        x: Math.max(minX, Math.min(maxX, newX)),
        y: Math.max(minY, Math.min(maxY, newY))
      });
    };

    const handleTouchMove = (e: TouchEvent) => {
      if (!isDragging) return;
      
      const touch = e.touches[0];
      const newX = dragStart.x - touch.clientX;
      const newY = dragStart.y - touch.clientY;  // Fixed: calculation was inverted
      
      // Check if actually moved
      const distance = Math.sqrt(Math.pow(newX - position.x, 2) + Math.pow(newY - position.y, 2));
      if (distance > 5) {
        setHasMoved(true);
      }
      
      // 화면 경계 체크
      const isDesktop = window.innerWidth >= 1025;
      
      // 버튼이 화면 밖으로 나가지 않도록 제한
      let minX = 10;
      let maxX = window.innerWidth - 70;
      let minY = 10;
      let maxY = window.innerHeight - 70;
      
      // 데스크톱에서만 사이드바와 헤더 영역 제외
      if (isDesktop) {
        maxX = window.innerWidth - 280 - 70; // 오른쪽에서 사이드바(280px) + 버튼크기(70px)
        maxY = window.innerHeight - 64 - 70; // 아래에서 헤더(64px) + 버튼크기(70px)
      }
      
      setPosition({
        x: Math.max(minX, Math.min(maxX, newX)),
        y: Math.max(minY, Math.min(maxY, newY))
      });
      
      // Prevent scrolling while dragging
      e.preventDefault();
    };

    const handleMouseUp = (e: MouseEvent) => {
      const endTime = Date.now();
      const duration = endTime - dragStart.time;
      
      // If it was a quick action (less than 200ms) and didn't move much, treat as click
      if (duration < 200 && !hasMoved) {
        setIsOpen(prev => !prev);
      }
      
      setIsDragging(false);
      setHasMoved(false);
    };

    const handleTouchEnd = (e: TouchEvent) => {
      const endTime = Date.now();
      const duration = endTime - dragStart.time;
      
      // If it was a quick action (less than 200ms) and didn't move much, treat as click
      if (duration < 200 && !hasMoved) {
        setIsOpen(prev => !prev);
      }
      
      setIsDragging(false);
      setHasMoved(false);
    };

    if (isDragging) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
      document.addEventListener('touchmove', handleTouchMove, { passive: false });
      document.addEventListener('touchend', handleTouchEnd);
      
      return () => {
        document.removeEventListener('mousemove', handleMouseMove);
        document.removeEventListener('mouseup', handleMouseUp);
        // Must match the options when removing
        document.removeEventListener('touchmove', handleTouchMove as any);
        document.removeEventListener('touchend', handleTouchEnd);
      };
    }
  }, [isDragging, dragStart.x, dragStart.y, dragStart.time, position, hasMoved, isOpen]);

  return (
    <>
      <button
        ref={buttonRef}
        className={`floating-chat-button ${isOpen ? 'active' : ''} ${isDragging ? 'dragging' : ''}`}
        onMouseDown={handleMouseDown}
        onTouchStart={handleTouchStart}
        style={{ 
          right: `${position.x}px`, 
          bottom: `${position.y}px` 
        }}
        title={isOpen ? '채팅 닫기' : 'AI 어시스턴트와 대화하기'}
      >
        {isOpen ? <X size={24} /> : <MessageCircle size={24} />}
      </button>

      {isOpen && (
        <ChatView isFloating={true} onClose={() => setIsOpen(false)} />
      )}
    </>
  );
};

export default FloatingChatButton;