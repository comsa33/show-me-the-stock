import React, { useMemo, useState, useRef, useEffect, useCallback } from 'react';
import {
  ComposedChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  AreaChart,
  Area
} from 'recharts';
import { useTheme } from '../context/ThemeContext';
import './ProfessionalStockChart.css';

interface StockDataPoint {
  Date: string;
  Open: number;
  High: number;
  Low: number;
  Close: number;
  Volume: number;
}

interface ChartProps {
  data: StockDataPoint[];
  symbol: string;
  market: string;
  period: string;
  showInterestRate: boolean;
  interestRateData?: Array<{ date: string; rate: number }>;
  onToggleInterestRate?: (enabled: boolean) => void;
}


const ProfessionalStockChart: React.FC<ChartProps> = ({
  data,
  symbol,
  market,
  period,
  showInterestRate,
  interestRateData = [],
  onToggleInterestRate
}) => {
  const { theme } = useTheme();
  const isDarkMode = theme === 'dark';
  
  // 스크롤 관련 상태
  const [scrollPosition, setScrollPosition] = useState(0);
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const [isDragging, setIsDragging] = useState(false);
  const dragStartX = useRef(0);
  const dragStartScroll = useRef(0);
  
  // 차트 폭 계산 - 기간에 따라 동적으로 조정
  const chartWidthPercentage = useMemo(() => {
    switch (period) {
      case '1d':
      case '5d':
        return 100; // 스크롤 없음
      case '1mo':
        return 150;
      case '3mo':
        return 200;
      case '6mo':
        return 250;
      case '1y':
      case 'ytd':
        return 300;
      case '5y':
        return 400;
      case 'max':
        return 500;
      default:
        return 250;
    }
  }, [period]);


  // 데이터 전처리
  const processedData = useMemo(() => {
    return data.map((point, index) => {
      const prevClose = index > 0 ? data[index - 1].Close : point.Open;
      const change = point.Close - prevClose;
      const changePercent = (change / prevClose) * 100;
      
      // 금리 데이터 매칭
      const interestRate = interestRateData.find(rate => rate.date === point.Date)?.rate || null;
      
      // 날짜 포맷팅 - 모든 데이터 포인트에 날짜 표시
      const dateObj = new Date(point.Date);
      let displayDate = '';
      
      if (period === '1d' || period === '5d') {
        // 1일, 5일: 월/일 시간
        displayDate = dateObj.toLocaleDateString('ko-KR', { 
          month: 'numeric', 
          day: 'numeric',
          hour: '2-digit',
          minute: '2-digit'
        });
      } else if (period === '1mo') {
        // 1개월: 월/일
        displayDate = dateObj.toLocaleDateString('ko-KR', { 
          month: 'numeric', 
          day: 'numeric' 
        });
      } else if (period === '3mo') {
        // 3개월: 월/일 (주 단위로 표시)
        if (index % 5 === 0) {
          displayDate = dateObj.toLocaleDateString('ko-KR', { 
            month: 'numeric', 
            day: 'numeric' 
          });
        }
      } else if (period === '6mo' || period === '1y' || period === 'ytd') {
        // 6개월, 1년, YTD: 년도가 바뀔 때는 YY.MM, 그 외에는 MM
        const currentYear = dateObj.getFullYear();
        const currentMonth = dateObj.getMonth();
        const prevYear = index > 0 ? new Date(data[index - 1].Date).getFullYear() : null;
        const prevMonth = index > 0 ? new Date(data[index - 1].Date).getMonth() : null;
        
        if (index === 0) {
          // 첫 번째 데이터는 항상 YY.MM 형식
          displayDate = dateObj.toLocaleDateString('ko-KR', { 
            year: '2-digit', 
            month: 'numeric' 
          }).replace('. ', '.').replace('.', '');
        } else if (prevYear !== currentYear) {
          // 년도가 바뀌면 YY.MM 형식
          displayDate = dateObj.toLocaleDateString('ko-KR', { 
            year: '2-digit', 
            month: 'numeric' 
          }).replace('. ', '.').replace('.', '');
        } else if (prevMonth !== currentMonth) {
          // 같은 년도 내에서 월이 바뀌면 MM만 표시
          displayDate = (currentMonth + 1).toString();
        }
      } else { // 5y, max
        // 5년 이상: 년/월 (분기 단위로 표시)
        if (index % 60 === 0) {
          displayDate = dateObj.toLocaleDateString('ko-KR', { 
            year: 'numeric', 
            month: 'numeric' 
          });
        }
      }
      
      return {
        ...point,
        date: displayDate,
        fullDate: point.Date,
        change,
        changePercent,
        isPositive: point.Close >= point.Open,
        interestRate,
      };
    });
  }, [data, interestRateData, period]);

  // Y축 도메인 계산 (최소/최대값의 위아래 10% 추가)
  const yDomain = useMemo(() => {
    if (!processedData.length) return [0, 100];
    
    const prices = processedData.map(d => d.Close);
    const minPrice = Math.min(...prices);
    const maxPrice = Math.max(...prices);
    const padding = (maxPrice - minPrice) * 0.1;
    
    return [
      Math.floor(minPrice - padding),
      Math.ceil(maxPrice + padding)
    ];
  }, [processedData]);

  // 금리 Y축 도메인 계산 (최소/최대값의 위아래 10% 추가)
  const interestRateDomain = useMemo(() => {
    if (!processedData.length || !showInterestRate || !interestRateData.length) return [0, 5];
    
    const rates = processedData
      .map(d => d.interestRate)
      .filter(rate => rate !== null && rate !== undefined) as number[];
    
    if (rates.length === 0) return [0, 5];
    
    const minRate = Math.min(...rates);
    const maxRate = Math.max(...rates);
    const padding = (maxRate - minRate) * 0.1;
    
    return [
      Math.max(0, minRate - padding), // 금리는 0 이하로 가지 않도록
      maxRate + padding
    ];
  }, [processedData, showInterestRate, interestRateData]);

  // 스크롤 이벤트 핸들러 (디바운스 적용)
  useEffect(() => {
    const container = scrollContainerRef.current;
    if (!container) return;

    let scrollTimeout: NodeJS.Timeout;
    const handleScroll = () => {
      clearTimeout(scrollTimeout);
      scrollTimeout = setTimeout(() => {
        const scrollLeft = container.scrollLeft;
        const scrollWidth = container.scrollWidth;
        const clientWidth = container.clientWidth;
        const maxScroll = scrollWidth - clientWidth;
        
        if (maxScroll > 0) {
          const scrollPercentage = (scrollLeft / maxScroll) * 100;
          setScrollPosition(scrollPercentage);
        }
      }, 10); // 10ms 디바운스
    };

    const handleResize = () => {
      // 필요시 컨테이너 크기 처리
    };

    container.addEventListener('scroll', handleScroll, { passive: true });
    window.addEventListener('resize', handleResize);
    handleResize();

    return () => {
      clearTimeout(scrollTimeout);
      container.removeEventListener('scroll', handleScroll);
      window.removeEventListener('resize', handleResize);
    };
  }, []);

  // 글로벌 마우스 이벤트 (드래그 중 미니맵 밖에서도 작동)
  useEffect(() => {
    const handleGlobalMouseMove = (e: MouseEvent) => {
      if (!isDragging) return;
      
      const container = scrollContainerRef.current;
      const minimapElement = document.querySelector('.minimap-container');
      if (!container || !minimapElement) return;

      const rect = minimapElement.getBoundingClientRect();
      const currentX = Math.max(0, Math.min(e.clientX - rect.left, rect.width));
      const percentage = currentX / rect.width;
      
      const scrollWidth = container.scrollWidth;
      const clientWidth = container.clientWidth;
      const maxScroll = scrollWidth - clientWidth;
      
      container.scrollLeft = maxScroll * percentage;
    };

    const handleGlobalMouseUp = () => {
      setIsDragging(false);
    };

    if (isDragging) {
      document.addEventListener('mousemove', handleGlobalMouseMove);
      document.addEventListener('mouseup', handleGlobalMouseUp);
    }

    return () => {
      document.removeEventListener('mousemove', handleGlobalMouseMove);
      document.removeEventListener('mouseup', handleGlobalMouseUp);
    };
  }, [isDragging]);

  // 미니맵 드래그 핸들러
  const handleMinimapMouseDown = useCallback((e: React.MouseEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(true);
    dragStartX.current = e.clientX;
    
    const container = scrollContainerRef.current;
    if (container) {
      dragStartScroll.current = container.scrollLeft;
    }
  }, []);

  const handleMinimapMouseMove = useCallback((e: React.MouseEvent<HTMLDivElement>) => {
    if (!isDragging) return;
    
    const container = scrollContainerRef.current;
    if (!container) return;

    const rect = e.currentTarget.getBoundingClientRect();
    const currentX = e.clientX - rect.left;
    const percentage = currentX / rect.width;
    
    const scrollWidth = container.scrollWidth;
    const clientWidth = container.clientWidth;
    const maxScroll = scrollWidth - clientWidth;
    
    container.scrollLeft = maxScroll * percentage;
  }, [isDragging]);

  const handleMinimapMouseUp = useCallback(() => {
    setIsDragging(false);
  }, []);

  const handleMinimapClick = useCallback((e: React.MouseEvent<HTMLDivElement>) => {
    if (isDragging) return; // 드래그 중이면 클릭 무시
    
    const container = scrollContainerRef.current;
    if (!container) return;

    const rect = e.currentTarget.getBoundingClientRect();
    const clickX = e.clientX - rect.left;
    const clickPercentage = clickX / rect.width;
    
    const scrollWidth = container.scrollWidth;
    const clientWidth = container.clientWidth;
    const maxScroll = scrollWidth - clientWidth;
    
    container.scrollLeft = maxScroll * clickPercentage;
  }, [isDragging]);

  // 포맷팅 함수들
  const formatPrice = (price: number) => {
    if (market === 'KR') {
      return `₩${price.toLocaleString()}`;
    }
    return `$${price.toFixed(2)}`;
  };


  // 커스텀 툴팁
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="custom-tooltip">
          <div className="tooltip-header">
            <strong>{new Date(data.fullDate).toLocaleDateString('ko-KR')}</strong>
          </div>
          <div className="tooltip-content">
            <div className="price-info">
              <div className="price-row">
                <span>종가:</span>
                <span className={data.change >= 0 ? 'positive-price' : 'negative-price'}>
                  {formatPrice(data.Close)}
                </span>
              </div>
              <div className="price-row">
                <span>고가:</span>
                <span className="high-price">{formatPrice(data.High)}</span>
              </div>
              <div className="price-row">
                <span>저가:</span>
                <span className="low-price">{formatPrice(data.Low)}</span>
              </div>
              <div className="price-row">
                <span>시가:</span>
                <span>{formatPrice(data.Open)}</span>
              </div>
              <div className="price-row">
                <span>변동:</span>
                <span className={data.change >= 0 ? 'positive-change' : 'negative-change'}>
                  {data.change >= 0 ? '+' : ''}{formatPrice(data.change)} 
                  ({data.changePercent >= 0 ? '+' : ''}{data.changePercent.toFixed(2)}%)
                </span>
              </div>
              {showInterestRate && data.interestRate && (
                <div className="price-row">
                  <span>금리:</span>
                  <span className="interest-rate">{data.interestRate}%</span>
                </div>
              )}
            </div>
          </div>
        </div>
      );
    }
    return null;
  };

  // 선형 차트 - 메모이제이션으로 성능 최적화
  const SimpleLineChart = React.memo(() => (
    <div style={{ position: 'relative' }}>
      <ResponsiveContainer width="100%" height={window.innerWidth <= 768 ? 520 : 460}>
        <ComposedChart 
          data={processedData} 
          margin={{ 
            top: 20, 
            right: showInterestRate ? (window.innerWidth <= 768 ? 40 : 60) : 30, 
            left: 20, 
            bottom: window.innerWidth <= 768 ? 65 : 60 
          }}
        >
          {/* 가로줄만 표시되는 격자 */}
          <CartesianGrid 
            horizontal={true} 
            vertical={false} 
            stroke={isDarkMode ? '#2d2d2d' : '#f0f0f0'} 
            strokeDasharray="1 1" 
          />
          
          {/* X축 - 동적 틱 포맷 적용 */}
          <XAxis 
            dataKey="date" 
            tick={{ fontSize: 11, fill: isDarkMode ? '#9ca3af' : '#666' }}
            axisLine={{ stroke: isDarkMode ? '#374151' : '#ddd' }}
            tickLine={false}
            interval="preserveStartEnd"
            angle={-45}
            textAnchor="end"
            height={60}
          />
          
          {/* Y축 - 주가 */}
          <YAxis 
            domain={yDomain}
            tick={{ fontSize: 12, fill: isDarkMode ? '#9ca3af' : '#666' }}
            axisLine={false}
            tickLine={false}
            tickFormatter={formatPrice}
          />
          
          {/* 금리 오버레이를 위한 Y축 */}
          {showInterestRate && interestRateData.length > 0 && (
            <YAxis 
              yAxisId="right" 
              orientation="right"
              domain={interestRateDomain}
              tick={{ fontSize: 12, fill: isDarkMode ? '#34d399' : '#10b981' }}
              axisLine={false}
              tickLine={false}
              tickFormatter={(value) => `${value.toFixed(1)}%`}
            />
          )}
          
          {/* 커스텀 툴팁 */}
          <Tooltip content={<CustomTooltip />} />
          
          {/* 주가 라인 - 마지막 점에만 dot 표시 */}
          <Line 
            type="monotone" 
            dataKey="Close" 
            stroke={isDarkMode ? '#60a5fa' : '#2563eb'} 
            strokeWidth={2.5}
            dot={(dotProps: any) => {
              if (dotProps.index === processedData.length - 1) {
                return <circle key={`dot-${dotProps.index}`} cx={dotProps.cx} cy={dotProps.cy} r={5} fill={isDarkMode ? '#60a5fa' : '#2563eb'} stroke={isDarkMode ? '#1f2937' : '#ffffff'} strokeWidth={2} />;
              }
              return <g key={`empty-dot-${dotProps.index}`}></g>;
            }}
            activeDot={{ r: 4, fill: isDarkMode ? '#60a5fa' : '#2563eb' }}
          />
          
          {/* 금리 라인 오버레이 */}
          {showInterestRate && interestRateData.length > 0 && (
            <Line 
              yAxisId="right"
              type="monotone" 
              dataKey="interestRate" 
              stroke={isDarkMode ? '#34d399' : '#10b981'} 
              strokeWidth={1.5}
              dot={(dotProps: any) => {
                if (dotProps.index === processedData.length - 1) {
                  return <circle key={`rate-dot-${dotProps.index}`} cx={dotProps.cx} cy={dotProps.cy} r={4} fill={isDarkMode ? '#34d399' : '#10b981'} stroke={isDarkMode ? '#1f2937' : '#ffffff'} strokeWidth={2} />;
                }
                return <g key={`empty-rate-dot-${dotProps.index}`}></g>;
              }}
              activeDot={{ r: 3, fill: isDarkMode ? '#34d399' : '#10b981' }}
            />
          )}
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  ));


  // 미니맵 차트
  const MiniMapChart = () => {
    const visibleWidth = (100 / chartWidthPercentage) * 100;
    const visibleLeft = scrollPosition * (100 - visibleWidth) / 100;
    
    return (
      <div 
        className="minimap-container" 
        onClick={handleMinimapClick}
        onMouseDown={handleMinimapMouseDown}
        onMouseMove={handleMinimapMouseMove}
        onMouseUp={handleMinimapMouseUp}
        onMouseLeave={handleMinimapMouseUp}
        style={{ cursor: isDragging ? 'grabbing' : 'pointer' }}
      >
        <ResponsiveContainer width="100%" height={60}>
          <AreaChart 
            data={processedData} 
            margin={{ top: 5, right: 5, left: 5, bottom: 5 }}
          >
            <defs>
              <linearGradient id="colorArea" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={isDarkMode ? '#60a5fa' : '#2563eb'} stopOpacity={0.3}/>
                <stop offset="95%" stopColor={isDarkMode ? '#60a5fa' : '#2563eb'} stopOpacity={0.1}/>
              </linearGradient>
            </defs>
            <Area 
              type="monotone" 
              dataKey="Close" 
              stroke={isDarkMode ? '#60a5fa' : '#2563eb'} 
              strokeWidth={1}
              fill="url(#colorArea)"
            />
          </AreaChart>
        </ResponsiveContainer>
        
        {/* 현재 보이는 영역 표시 */}
        {chartWidthPercentage > 100 && (
          <div 
            className="minimap-viewport"
            style={{
              left: `${visibleLeft}%`,
              width: `${visibleWidth}%`,
              backgroundColor: isDarkMode ? 'rgba(96, 165, 250, 0.2)' : 'rgba(37, 99, 235, 0.2)',
              borderColor: isDarkMode ? '#60a5fa' : '#2563eb',
              pointerEvents: 'auto'
            }}
            onMouseDown={(e) => {
              e.stopPropagation();
              handleMinimapMouseDown(e);
            }}
          />
        )}
      </div>
    );
  };

  return (
    <div className="professional-stock-chart">
      {/* 메인 차트 */}
      <div className="main-chart">
        <div 
          className="chart-scroll-container" 
          ref={scrollContainerRef}
          style={{ overflowX: chartWidthPercentage > 100 ? 'auto' : 'hidden' }}
        >
          <div className="chart-content" style={{ width: `${chartWidthPercentage}%` }}>
            <SimpleLineChart />
          </div>
        </div>
      </div>

      {/* 미니맵 - 스크롤이 필요한 경우만 표시 */}
      {chartWidthPercentage > 100 && (
        <MiniMapChart />
      )}

      {/* 차트 범례 */}
      <div className="chart-legend">
        <div className="legend-item">
          <span className="legend-color" style={{ backgroundColor: isDarkMode ? '#60a5fa' : '#2563eb' }}></span>
          주가
        </div>
        {showInterestRate && interestRateData.length > 0 && (
          <div className="legend-item">
            <span className="legend-color" style={{ backgroundColor: isDarkMode ? '#34d399' : '#10b981' }}></span>
            금리 ({market === 'KR' ? '한국은행 기준금리' : '연준 기준금리'})
          </div>
        )}
      </div>
    </div>
  );
};

export default ProfessionalStockChart;