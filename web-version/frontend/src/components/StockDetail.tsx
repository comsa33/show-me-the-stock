import React, { useState, useEffect } from 'react';
import { useApp } from '../context/AppContext';
import { API_BASE } from '../config';
import ProfessionalStockChart from './ProfessionalStockChart';
import { BookOpen, TrendingUp, Gem, ArrowLeft, Sparkles, Download, ChevronDown, ChevronUp, Brain, ExternalLink, Activity, BarChart3, TestTube, Newspaper } from 'lucide-react';
import './StockDetail.css';

interface StockData {
  symbol: string;
  data: Array<{
    Date: string;
    Open: number;
    High: number;
    Low: number;
    Close: number;
    Volume: number;
  }>;
  current_price: number;
}

interface DetailedStockInfo {
  symbol: string;
  market: string;
  basic_info: {
    current_price: number;
    previous_close: number;
    change: number;
    change_percent: number;
  };
  price_ranges: {
    daily_low: number;
    daily_high: number;
    daily_range: string;
    year_low: number;
    year_high: number;
    week_52_range: string;
  };
  trading_info: {
    current_volume: number;
    avg_volume_20d: number;
    volume_ratio: number;
  };
  financial_metrics: {
    market_cap: number | null;
    market_cap_formatted: string;
    per: number | null;
    pbr: number | null;
    dividend_yield: number | null;
  };
  last_updated: string;
}

interface SourceCitation {
  title: string;
  url: string;
  snippet: string;
}

interface GroundingSupport {
  start_index: number;
  end_index: number;
  text: string;
  source_indices: number[];
}

interface AnalysisData {
  symbol: string;
  market: string;
  analysis_type: string;
  timestamp: string;
  analysis: {
    summary: {
      overall_signal: string;
      confidence: string;
      recommendation: string;
      target_price: string;
      analysis_period: string;
    };
    technical_analysis: {
      rsi: {
        value: number | null;
        signal: string;
        description: string;
      };
      moving_average: {
        signal: string;
        description: string;
      };
      volume_analysis: {
        trend: string;
        description: string;
      };
    };
    news_analysis: {
      sentiment: string;
      score: number;
      summary: string;
      key_topics: string[];
    };
    risk_factors: string[];
    ai_insights: string[];
    sources: SourceCitation[];
    grounding_supports: GroundingSupport[];
    original_text: string;
  };
}

const StockDetail: React.FC = () => {
  const { selectedStock, currentView, setCurrentView } = useApp();
  const [stockData, setStockData] = useState<StockData | null>(null);
  const [detailedInfo, setDetailedInfo] = useState<DetailedStockInfo | null>(null);
  const [analysisData, setAnalysisData] = useState<AnalysisData | null>(null);
  const [loading, setLoading] = useState(false);
  const [detailLoading, setDetailLoading] = useState(false);
  const [analysisLoading, setAnalysisLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [period, setPeriod] = useState('1y');
  const [showInterestRate, setShowInterestRate] = useState(false);
  const [interestRateData, setInterestRateData] = useState<Array<{ date: string; rate: number }>>([]);
  const [analysisType, setAnalysisType] = useState<'beginner' | 'swing' | 'invest'>('beginner');
  const [showSources, setShowSources] = useState(false); // 참고자료 접기/펼치기

  const periods = [
    { value: '1d', label: '1일' },
    { value: '5d', label: '5일' },
    { value: '1mo', label: '1개월' },
    { value: '6mo', label: '6개월' },
    { value: 'ytd', label: 'YTD' },
    { value: '1y', label: '1년' },
    { value: '5y', label: '5년' },
    { value: 'max', label: '최대' }
  ];

  const fetchStockData = async () => {
    if (!selectedStock) return;
    
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(
        `${API_BASE}/v1/stocks/v2/data/${selectedStock.symbol}?market=${selectedStock.market}&period=${period}`
      );
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || '데이터를 불러올 수 없습니다.');
      }
      
      const data = await response.json();
      
      // chart_data 유효성 검사
      if (!data.chart_data || !Array.isArray(data.chart_data)) {
        throw new Error(`Invalid chart_data: expected array, got ${typeof data.chart_data}`);
      }
      
      if (data.chart_data.length === 0) {
        throw new Error('차트 데이터가 비어있습니다.');
      }
      
      // v2 API 응답 형식을 기존 형식에 맞게 변환
      const transformedData = {
        symbol: data.symbol,
        current_price: data.current_price,
        data: data.chart_data.map((item: any) => ({
          Date: item.date,
          Open: item.open,
          High: item.high,
          Low: item.low,
          Close: item.close,
          Volume: item.volume
        }))
      };
      
      setStockData(transformedData);
      // 주식 데이터를 받은 후 금리 데이터 생성
      generateInterestRateData(transformedData);
    } catch (error) {
      console.error('주식 데이터 로딩 실패:', error);
      setError(error instanceof Error ? error.message : '알 수 없는 오류가 발생했습니다.');
      setStockData(null);
    } finally {
      setLoading(false);
    }
  };

  const fetchDetailedInfo = async () => {
    if (!selectedStock) return;
    
    setDetailLoading(true);
    try {
      const response = await fetch(
        `${API_BASE}/v1/stocks/v2/detail/${selectedStock.symbol}?market=${selectedStock.market}`
      );
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || '상세 정보를 불러올 수 없습니다.');
      }
      
      const data = await response.json();
      setDetailedInfo(data);
    } catch (error) {
      console.error('상세 정보 로딩 실패:', error);
      setDetailedInfo(null);
    } finally {
      setDetailLoading(false);
    }
  };

  const fetchAnalysis = async (type: 'beginner' | 'swing' | 'invest') => {
    if (!selectedStock) return;
    
    setAnalysisLoading(true);
    try {
      const response = await fetch(
        `${API_BASE}/v1/ai/stock/analyze?symbol=${selectedStock.symbol}&market=${selectedStock.market}&analysis_type=${type}`,
        { method: 'POST' }
      );
      const data = await response.json();
      setAnalysisData(data);
    } catch (error) {
      console.error('AI 분석 실패:', error);
    } finally {
      setAnalysisLoading(false);
    }
  };

  useEffect(() => {
    if (selectedStock && currentView === 'stocks') {
      fetchStockData();
      fetchDetailedInfo();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedStock, period, currentView]);


  if (currentView !== 'stocks' || !selectedStock) {
    return null;
  }

  const formatPrice = (price: number) => {
    return selectedStock.market === 'KR' 
      ? `₩${price.toLocaleString()}` 
      : `$${price.toFixed(2)}`;
  };

  // AI 분석 리포트를 마크다운으로 생성
  const generateMarkdownReport = () => {
    if (!analysisData) return '';
    
    const { analysis, symbol, market, analysis_type, timestamp } = analysisData;
    const date = new Date(timestamp).toLocaleString('ko-KR');
    
    let markdown = `# ${symbol} AI 분석 리포트\n\n`;
    markdown += `**분석 유형**: ${analysis_type === 'beginner' ? '초보자 분석' : analysis_type === 'swing' ? '스윙 분석' : '투자 분석'}\n`;
    markdown += `**시장**: ${market}\n`;
    markdown += `**분석 일시**: ${date}\n\n`;
    
    // 요약
    markdown += `## 📊 분석 요약\n\n`;
    markdown += `- **전체 신호**: ${analysis.summary.overall_signal}\n`;
    markdown += `- **신뢰도**: ${analysis.summary.confidence}\n`;
    markdown += `- **추천**: ${analysis.summary.recommendation}\n`;
    markdown += `- **목표 가격**: ${analysis.summary.target_price}\n`;
    markdown += `- **분석 기간**: ${analysis.summary.analysis_period}\n\n`;
    
    // 기술적 분석
    markdown += `## 📈 기술적 분석\n\n`;
    markdown += `### RSI${analysis.technical_analysis.rsi.value !== null ? ` (${analysis.technical_analysis.rsi.value.toFixed(1)})` : ''}\n`;
    markdown += `- **신호**: ${analysis.technical_analysis.rsi.signal}\n`;
    markdown += `- **설명**: ${analysis.technical_analysis.rsi.description}\n\n`;
    
    markdown += `### 이동평균선\n`;
    markdown += `- **신호**: ${analysis.technical_analysis.moving_average.signal}\n`;
    markdown += `- **설명**: ${analysis.technical_analysis.moving_average.description}\n\n`;
    
    markdown += `### 거래량 분석\n`;
    markdown += `- **추세**: ${analysis.technical_analysis.volume_analysis.trend}\n`;
    markdown += `- **설명**: ${analysis.technical_analysis.volume_analysis.description}\n\n`;
    
    // 뉴스 감성 분석
    markdown += `## 📰 뉴스 감성 분석\n\n`;
    markdown += `- **감성**: ${analysis.news_analysis.sentiment} (${analysis.news_analysis.score}점)\n`;
    markdown += `- **요약**: ${analysis.news_analysis.summary}\n`;
    markdown += `- **주요 토픽**: ${analysis.news_analysis.key_topics.join(', ')}\n\n`;
    
    // AI 인사이트
    markdown += `## 🤖 AI 인사이트\n\n`;
    analysis.ai_insights.forEach((insight, index) => {
      markdown += `${index + 1}. ${insight}\n`;
    });
    markdown += '\n';
    
    // 리스크 요인
    markdown += `## ⚠️ 리스크 요인\n\n`;
    analysis.risk_factors.forEach((risk, index) => {
      markdown += `${index + 1}. ${risk}\n`;
    });
    markdown += '\n';
    
    // 출처
    if (analysis.sources && analysis.sources.length > 0) {
      markdown += `## 📚 참고 자료\n\n`;
      analysis.sources.forEach((source, index) => {
        markdown += `${index + 1}. [${source.title}](${source.url})\n`;
        if (source.snippet) {
          markdown += `   > ${source.snippet}\n`;
        }
      });
      markdown += '\n';
    }
    
    // 원본 텍스트 (있을 경우)
    if (analysis.original_text) {
      markdown += `## 📄 상세 분석 내용\n\n`;
      markdown += `\`\`\`\n${analysis.original_text}\n\`\`\`\n`;
    }
    
    return markdown;
  };
  
  // 마크다운 파일 다운로드
  const downloadMarkdownReport = () => {
    if (!analysisData) return;
    
    const markdown = generateMarkdownReport();
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-').split('T')[0];
    const filename = `${analysisData.symbol}_${timestamp}.md`;
    
    const blob = new Blob([markdown], { type: 'text/markdown;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  // 풋노트가 포함된 텍스트 렌더링 함수
  const renderTextWithFootnotes = (
    text: string, 
    groundingSupports: GroundingSupport[], 
    sources: SourceCitation[]
  ): React.ReactElement => {
    // 텍스트에 이미 풋노트가 포함되어 있는지 확인
    const footnotePattern = /\[(\d+(?:,\s*\d+)*)\]/g;
    const hasFootnotes = footnotePattern.test(text);
    
    if (hasFootnotes) {
      // 텍스트에 이미 풋노트가 있는 경우 직접 파싱하여 링크로 변환
      const parts: (string | React.ReactElement)[] = [];
      let lastIndex = 0;
      let match: RegExpExecArray | null;
      
      // 패턴 재설정 (test() 호출로 인한 lastIndex 변경 방지)
      footnotePattern.lastIndex = 0;
      
      while ((match = footnotePattern.exec(text)) !== null) {
        const currentMatch = match; // match를 로컬 변수에 저장
        // 풋노트 앞의 텍스트 추가
        if (currentMatch.index > lastIndex) {
          parts.push(text.substring(lastIndex, currentMatch.index));
        }
        
        // 풋노트 번호들을 파싱하여 링크 추가
        const numbers = currentMatch[1].split(',').map(n => parseInt(n.trim()));
        numbers.forEach((num, idx) => {
          if (num - 1 < sources.length) {
            parts.push(
              <a 
                key={`${currentMatch.index}-${num}`}
                href={sources[num - 1]?.url || '#'} 
                target="_blank" 
                rel="noopener noreferrer"
                className="footnote-link"
                title={sources[num - 1]?.title || ''}
              >
                {num}
              </a>
            );
          } else {
            parts.push(
              <span 
                key={`${currentMatch.index}-${num}-text`}
                className="footnote-link-disabled"
                title="출처 정보 없음"
              >
                {num}
              </span>
            );
          }
        });
        
        lastIndex = currentMatch.index + currentMatch[0].length;
      }
      
      // 마지막 부분 추가
      if (lastIndex < text.length) {
        parts.push(text.substring(lastIndex));
      }
      
      return <span className="footnote-text">{parts}</span>;
    }
    
    // 기존 로직: groundingSupports를 사용한 풋노트 추가
    if (!groundingSupports || groundingSupports.length === 0) {
      return <span>{text}</span>;
    }

    // 현재 텍스트와 일치하는 support만 필터링
    const matchingSupport = groundingSupports.find(support => 
      support.text === text || support.text.includes(text) || text.includes(support.text)
    );

    if (!matchingSupport) {
      return <span>{text}</span>;
    }

    // 풋노트 번호 추출
    const sourceNumbers = matchingSupport.source_indices
      .filter(index => index < sources.length)
      .map(index => index + 1);

    if (sourceNumbers.length > 0) {
      return (
        <span className="footnote-text">
          {text}
          {sourceNumbers.map(num => (
            <a 
              key={num}
              href={sources[num - 1]?.url || '#'} 
              target="_blank" 
              rel="noopener noreferrer"
              className="footnote-link"
              title={sources[num - 1]?.title || ''}
            >
              {num}
            </a>
          ))}
        </span>
      );
    }

    return <span>{text}</span>;
  };

  // 모의 금리 데이터 생성 함수
  const generateInterestRateData = (stockData: StockData) => {
    const baseRate = selectedStock.market === 'KR' ? 3.5 : 5.25; // 한국: 3.5%, 미국: 5.25%
    const rateData = stockData.data.map((point, index) => {
      // 시간에 따른 금리 변동 시뮬레이션 (실제로는 API에서 가져와야 함)
      const variation = Math.sin(index / 30) * 0.5 + Math.random() * 0.2 - 0.1;
      const rate = Math.max(0.1, baseRate + variation);
      
      return {
        date: point.Date,
        rate: parseFloat(rate.toFixed(2))
      };
    });
    
    setInterestRateData(rateData);
  };


  return (
    <div className="stock-detail-container slide-up">
      <div className="stock-detail-header">
        <div className="header-left">
          <button 
            className="back-button"
            onClick={() => setCurrentView('dashboard')}
          >
            <ArrowLeft size={16} />
            돌아가기
          </button>
        </div>
        
        <div className="stock-header-info">
          <h2>{selectedStock.name}</h2>
          <span className="stock-symbol-large">{selectedStock.symbol}</span>
          <span className="market-badge">{selectedStock.market === 'KR' ? '한국' : '미국'}</span>
        </div>
        
        <div className="header-actions">
          <button 
            className="action-button"
            onClick={() => setCurrentView('quant')}
            title="백테스트"
          >
            <TestTube size={16} />
            <span>백테스트</span>
          </button>
          <button 
            className="action-button"
            onClick={() => setCurrentView('news')}
            title="뉴스 보기"
          >
            <Newspaper size={16} />
            <span>뉴스</span>
          </button>
        </div>

        {stockData && (
          <div className="current-price-info">
            <div className="current-price">{formatPrice(stockData.current_price)}</div>
            <div className="price-change">
              {stockData.data.length > 1 && (
                <span className={
                  stockData.current_price > stockData.data[stockData.data.length - 2].Close
                    ? 'status-positive' 
                    : stockData.current_price < stockData.data[stockData.data.length - 2].Close
                    ? 'status-negative'
                    : 'status-neutral'
                }>
                  {stockData.current_price > stockData.data[stockData.data.length - 2].Close ? '▲' : 
                   stockData.current_price < stockData.data[stockData.data.length - 2].Close ? '▼' : '—'}
                  {((stockData.current_price - stockData.data[stockData.data.length - 2].Close) / stockData.data[stockData.data.length - 2].Close * 100).toFixed(2)}%
                </span>
              )}
            </div>
          </div>
        )}
      </div>

      <div className="stock-detail-content">
        <div className="chart-section">
          <div className="chart-controls">
            <div className="period-selector">
              {periods.map(p => (
                <button 
                  key={p.value}
                  className={`period-btn ${period === p.value ? 'active' : ''}`}
                  onClick={() => setPeriod(p.value)}
                >
                  {p.label}
                </button>
              ))}
            </div>
            
            <div className="chart-options">
              <label className="toggle-switch-label">
                <input 
                  type="checkbox" 
                  className="toggle-input"
                  checked={showInterestRate}
                  onChange={(e) => setShowInterestRate(e.target.checked)}
                />
                <span className="toggle-slider"></span>
                금리 오버레이
              </label>
            </div>
          </div>

          <div className="chart-container">
            {loading ? (
              <div className="chart-loading">
                <div className="loading-spinner"></div>
                <p>차트 데이터 로딩 중...</p>
              </div>
            ) : error ? (
              <div className="chart-error">
                <div className="error-icon">⚠️</div>
                <h3>데이터를 불러올 수 없습니다</h3>
                <p>{error}</p>
                <button onClick={fetchStockData} className="btn-primary">다시 시도</button>
              </div>
            ) : stockData ? (
              <>
                <ProfessionalStockChart 
                  data={stockData.data}
                  symbol={selectedStock.symbol}
                  market={selectedStock.market}
                  period={period}
                  showInterestRate={showInterestRate}
                  interestRateData={interestRateData}
                  onToggleInterestRate={setShowInterestRate}
                />

                {/* 네이버 스타일 상세 정보 */}
                {detailLoading ? (
                  <div className="detail-info-loading">
                    <div className="loading-spinner"></div>
                    <p>상세 정보 로딩 중...</p>
                  </div>
                ) : detailedInfo ? (
                  <div className="stock-detail-info">
                    <div className="detail-info-grid">
                      <div className="info-card">
                        <span className="info-label">전일 종가</span>
                        <span className="info-value">
                          {selectedStock.market === 'KR' 
                            ? `₩${detailedInfo.basic_info.previous_close.toLocaleString()}`
                            : `$${detailedInfo.basic_info.previous_close.toFixed(2)}`
                          }
                        </span>
                      </div>
                      
                      <div className="info-card">
                        <span className="info-label">일일 변동폭</span>
                        <span className="info-value">{detailedInfo.price_ranges.daily_range}</span>
                      </div>
                      
                      <div className="info-card">
                        <span className="info-label">52주 변동폭</span>
                        <span className="info-value">{detailedInfo.price_ranges.week_52_range}</span>
                      </div>
                      
                      {detailedInfo.financial_metrics.market_cap && (
                        <div className="info-card">
                          <span className="info-label">시가총액</span>
                          <span className="info-value">{detailedInfo.financial_metrics.market_cap_formatted}</span>
                        </div>
                      )}
                      
                      <div className="info-card">
                        <span className="info-label">평균 거래량</span>
                        <span className="info-value">
                          {(detailedInfo.trading_info.avg_volume_20d / 10000).toFixed(1)}만
                        </span>
                      </div>
                      
                      {detailedInfo.financial_metrics.per && (
                        <div className="info-card">
                          <span className="info-label">주가수익률 (PER)</span>
                          <span className="info-value">{detailedInfo.financial_metrics.per.toFixed(2)}</span>
                        </div>
                      )}
                      
                      {detailedInfo.financial_metrics.pbr && (
                        <div className="info-card">
                          <span className="info-label">주가순자산비율 (PBR)</span>
                          <span className="info-value">{detailedInfo.financial_metrics.pbr.toFixed(2)}</span>
                        </div>
                      )}
                      
                      {detailedInfo.financial_metrics.dividend_yield && (
                        <div className="info-card">
                          <span className="info-label">배당수익률</span>
                          <span className="info-value">{detailedInfo.financial_metrics.dividend_yield.toFixed(2)}%</span>
                        </div>
                      )}
                    </div>
                  </div>
                ) : null}
              </>
            ) : (
              <div className="chart-error">
                <p>차트 데이터를 불러올 수 없습니다.</p>
                <button onClick={fetchStockData} className="btn-primary">다시 시도</button>
              </div>
            )}
          </div>
        </div>

        <div className="analysis-section">
          <div className="analysis-header">
            <h3><Brain size={20} /> AI 분석</h3>
            <div className="analysis-controls">
              <div className="analysis-type-selector">
                <button 
                  className={`analysis-btn ${analysisType === 'beginner' ? 'active' : ''}`}
                  onClick={() => setAnalysisType('beginner')}
                  title="초보자를 위한 쉬운 분석 (1~3일)"
                >
                  <BookOpen size={20} />
                  <span>
                    <div className="btn-title">초보자</div>
                    <div className="btn-subtitle">1~3일</div>
                  </span>
                </button>
                <button 
                  className={`analysis-btn ${analysisType === 'swing' ? 'active' : ''}`}
                  onClick={() => setAnalysisType('swing')}
                  title="스윙 트레이딩 분석 (1주~1개월)"
                >
                  <TrendingUp size={20} />
                  <span>
                    <div className="btn-title">스윙</div>
                    <div className="btn-subtitle">1주~1개월</div>
                  </span>
                </button>
                <button 
                  className={`analysis-btn ${analysisType === 'invest' ? 'active' : ''}`}
                  onClick={() => setAnalysisType('invest')}
                  title="중장기 투자 분석 (3개월~1년)"
                >
                  <Gem size={20} />
                  <span>
                    <div className="btn-title">투자</div>
                    <div className="btn-subtitle">3개월~1년</div>
                  </span>
                </button>
              </div>
              <button 
                className="btn-primary ai-analyze-btn"
                onClick={() => fetchAnalysis(analysisType)}
                disabled={analysisLoading}
              >
                {analysisLoading ? (
                  <>
                    <div className="loading-spinner small"></div>
                    <span>분석 중...</span>
                  </>
                ) : (
                  <>
                    <Sparkles size={18} />
                    <span>AI 분석 실행</span>
                  </>
                )}
              </button>
            </div>
          </div>

          {analysisLoading && (
            <div className="analysis-loading">
              <div className="loading-spinner"></div>
              <p>AI가 주식을 분석하고 있습니다...</p>
            </div>
          )}

          {analysisData && analysisData.analysis && (
            <div className="analysis-results">
              <div className="analysis-summary">
                <h4>분석 요약</h4>
                <div className="summary-grid">
                  <div className="summary-card">
                    <div className="summary-label">전체 신호</div>
                    <div className={`summary-value signal-${analysisData.analysis.summary.overall_signal.toLowerCase()}`}>
                      {analysisData.analysis.summary.overall_signal}
                    </div>
                  </div>
                  <div className="summary-card">
                    <div className="summary-label">신뢰도</div>
                    <div className="summary-value">{analysisData.analysis.summary.confidence}</div>
                  </div>
                  <div className="summary-card">
                    <div className="summary-label">추천</div>
                    <div className="summary-value">{analysisData.analysis.summary.recommendation}</div>
                  </div>
                  <div className="summary-card">
                    <div className="summary-label">목표가</div>
                    <div className="summary-value">{analysisData.analysis.summary.target_price}</div>
                  </div>
                </div>
              </div>

              <div className="analysis-details">
                <div className="analysis-section-item">
                  <h5>기술적 분석</h5>
                  <div className="technical-indicators-cards">
                    {/* RSI 카드 */}
                    <div className="indicator-card">
                      <div className="indicator-header">
                        <div className="indicator-title-group">
                          <span className="indicator-name">RSI</span>
                          <Activity className="indicator-icon" size={20} />
                        </div>
                        <span className={`indicator-value rsi-${analysisData.analysis.technical_analysis.rsi.signal?.toLowerCase() || 'none'}`}>
                          {analysisData.analysis.technical_analysis.rsi.value !== null && analysisData.analysis.technical_analysis.rsi.value !== undefined
                            ? analysisData.analysis.technical_analysis.rsi.value.toFixed(1)
                            : '—'}
                        </span>
                      </div>
                      <div className="indicator-signal">
                        <span className={`signal-badge rsi-${analysisData.analysis.technical_analysis.rsi.signal?.toLowerCase() || 'none'}`}>
                          {analysisData.analysis.technical_analysis.rsi.signal || '정보 없음'}
                        </span>
                      </div>
                      {analysisData.analysis.technical_analysis.rsi.description && (
                        <p className="indicator-description">
                          {analysisData.analysis.grounding_supports && analysisData.analysis.grounding_supports.length > 0 
                            ? renderTextWithFootnotes(analysisData.analysis.technical_analysis.rsi.description, analysisData.analysis.grounding_supports, analysisData.analysis.sources)
                            : analysisData.analysis.technical_analysis.rsi.description
                          }
                        </p>
                      )}
                    </div>
                    
                    {/* 이동평균 카드 */}
                    <div className="indicator-card">
                      <div className="indicator-header">
                        <span className="indicator-name">이동평균선</span>
                        <TrendingUp className="indicator-icon" size={24} />
                      </div>
                      <div className="indicator-signal">
                        <span className={`signal-badge ma-${analysisData.analysis.technical_analysis.moving_average.signal?.toLowerCase() || 'neutral'}`}>
                          {analysisData.analysis.technical_analysis.moving_average.signal}
                        </span>
                      </div>
                      {analysisData.analysis.technical_analysis.moving_average.description && (
                        <p className="indicator-description">
                          {analysisData.analysis.grounding_supports && analysisData.analysis.grounding_supports.length > 0 
                            ? renderTextWithFootnotes(analysisData.analysis.technical_analysis.moving_average.description, analysisData.analysis.grounding_supports, analysisData.analysis.sources)
                            : analysisData.analysis.technical_analysis.moving_average.description
                          }
                        </p>
                      )}
                    </div>
                    
                    {/* 거래량 카드 */}
                    <div className="indicator-card">
                      <div className="indicator-header">
                        <span className="indicator-name">거래량 분석</span>
                        <BarChart3 className="indicator-icon" size={24} />
                      </div>
                      <div className="indicator-signal">
                        <span className={`signal-badge volume-${analysisData.analysis.technical_analysis.volume_analysis.trend?.toLowerCase() || 'average'}`}>
                          {analysisData.analysis.technical_analysis.volume_analysis.trend}
                        </span>
                      </div>
                      {analysisData.analysis.technical_analysis.volume_analysis.description && (
                        <p className="indicator-description">
                          {analysisData.analysis.grounding_supports && analysisData.analysis.grounding_supports.length > 0 
                            ? renderTextWithFootnotes(analysisData.analysis.technical_analysis.volume_analysis.description, analysisData.analysis.grounding_supports, analysisData.analysis.sources)
                            : analysisData.analysis.technical_analysis.volume_analysis.description
                          }
                        </p>
                      )}
                    </div>
                  </div>
                </div>

                <div className="analysis-section-item">
                  <h5>뉴스 감성 분석</h5>
                  <div className="sentiment-analysis">
                    <div className="sentiment-score">
                      <span className={`sentiment-value sentiment-${analysisData.analysis.news_analysis.sentiment.toLowerCase()}`}>
                        {analysisData.analysis.news_analysis.sentiment} ({analysisData.analysis.news_analysis.score}점)
                      </span>
                    </div>
                    <p>
                      {analysisData.analysis.grounding_supports && analysisData.analysis.grounding_supports.length > 0 
                        ? renderTextWithFootnotes(analysisData.analysis.news_analysis.summary, analysisData.analysis.grounding_supports, analysisData.analysis.sources)
                        : analysisData.analysis.news_analysis.summary
                      }
                    </p>
                    <div className="key-topics">
                      {analysisData.analysis.news_analysis.key_topics.map((topic, index) => (
                        <span key={index} className="topic-tag">
                          {analysisData.analysis.grounding_supports && analysisData.analysis.grounding_supports.length > 0 
                            ? renderTextWithFootnotes(topic, analysisData.analysis.grounding_supports, analysisData.analysis.sources)
                            : topic
                          }
                        </span>
                      ))}
                    </div>
                  </div>
                </div>

                <div className="analysis-section-item">
                  <h5>AI 인사이트</h5>
                  <ul className="insights-list">
                    {analysisData.analysis.ai_insights.map((insight, index) => (
                      <li key={index}>
                        {analysisData.analysis.grounding_supports && analysisData.analysis.grounding_supports.length > 0 
                          ? renderTextWithFootnotes(insight, analysisData.analysis.grounding_supports, analysisData.analysis.sources)
                          : insight
                        }
                      </li>
                    ))}
                  </ul>
                </div>

                <div className="analysis-section-item">
                  <h5>리스크 요인</h5>
                  <ul className="risk-list">
                    {analysisData.analysis.risk_factors.map((risk, index) => (
                      <li key={index}>
                        {analysisData.analysis.grounding_supports && analysisData.analysis.grounding_supports.length > 0 
                          ? renderTextWithFootnotes(risk, analysisData.analysis.grounding_supports, analysisData.analysis.sources)
                          : risk
                        }
                      </li>
                    ))}
                  </ul>
                </div>

                {analysisData.analysis.sources && analysisData.analysis.sources.length > 0 && (
                  <div className="analysis-section-item collapsible-section">
                    <div 
                      className="section-header clickable"
                      onClick={() => setShowSources(!showSources)}
                    >
                      <h5>
                        <ExternalLink size={18} />
                        참고 자료 및 출처 ({analysisData.analysis.sources.length})
                      </h5>
                      <button className="collapse-btn">
                        {showSources ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
                      </button>
                    </div>
                    {showSources && (
                      <div className="sources-list">
                        {analysisData.analysis.sources.map((source, index) => (
                          <div key={index} className="source-card">
                            <div className="source-header">
                              <span className="source-number">{index + 1}</span>
                              <a 
                                href={source.url} 
                                target="_blank" 
                                rel="noopener noreferrer"
                                className="source-title"
                              >
                                {source.title}
                                <ExternalLink size={12} className="external-link-icon" />
                              </a>
                            </div>
                            <p className="source-snippet">{source.snippet}</p>
                            <div className="source-url">
                              {source.url.startsWith('http') ? new URL(source.url).hostname : source.url}
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {/* 리포트 다운로드 버튼 */}
                {analysisData.analysis.original_text && (
                  <button 
                    className="btn-primary ai-analyze-btn"
                    onClick={downloadMarkdownReport}
                    title="마크다운 파일로 다운로드"
                    style={{ marginTop: '24px', width: '100%' }}
                  >
                    <Download size={18} />
                    <span>리포트 다운로드</span>
                  </button>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default StockDetail;