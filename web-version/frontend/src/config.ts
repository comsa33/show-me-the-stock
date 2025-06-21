// API 엔드포인트 기본 경로를 한곳에서 관리합니다.
// ─ 빌드 시점(환경변수) → 런타임( env.js ) 둘 다 지원
export const API_BASE =
  (window as any).env?.REACT_APP_API_URL ||   // nginx로 주입된 런타임 변수
  process.env.REACT_APP_API_URL ||            // CRA/Vite 빌드 시 변수
  '/api';                                     // 기본값: 같은 호스트의 /api