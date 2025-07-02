import React, { useMemo } from 'react';
import {
  ComposedChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer
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


  // 데이터 전처리
  const processedData = useMemo(() => {
    return data.map((point, index) => {
      const prevClose = index > 0 ? data[index - 1].Close : point.Open;
      const change = point.Close - prevClose;
      const changePercent = (change / prevClose) * 100;
      
      // 금리 데이터 매칭
      const interestRate = interestRateData.find(rate => rate.date === point.Date)?.rate || null;
      
      // 기간에 따른 동적 날짜 포맷
      let displayDate = '';
      if (period === '1d' || period === '5d') {
        displayDate = new Date(point.Date).toLocaleDateString('ko-KR', { month: 'short', day: 'numeric' });
      } else if (period === '1mo') {
        if (index % 7 === 0) { // 주 단위
          displayDate = new Date(point.Date).toLocaleDateString('ko-KR', { month: 'short', day: 'numeric' });
        }
      } else if (period === '6mo' || period === '1y' || period === 'ytd') {
        if (index % 60 === 0) { // 2개월 단위
          displayDate = new Date(point.Date).toLocaleDateString('ko-KR', { year: '2-digit', month: 'short' });
        }
      } else { // 5y, max
        if (index % 250 === 0) { // 년 단위
          displayDate = new Date(point.Date).getFullYear().toString();
        }
      }
      
      return {
        ...point,
        date: displayDate || '', // 조건에 맞지 않으면 빈 문자열
        fullDate: point.Date,
        change,
        changePercent,
        isPositive: point.Close >= point.Open,
        interestRate,
      };
    });
  }, [data, interestRateData, period]);



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

  // 선형 차트 - 단순하고 트렌디한 디자인
  const SimpleLineChart = () => (
    <div style={{ position: 'relative' }}>
      <ResponsiveContainer width="100%" height={400}>
        <ComposedChart 
          data={processedData} 
          margin={{ 
            top: 20, 
            right: showInterestRate ? (window.innerWidth <= 768 ? 40 : 60) : 30, 
            left: 20, 
            bottom: 20 
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
            tick={{ fontSize: 12, fill: isDarkMode ? '#9ca3af' : '#666' }}
            axisLine={{ stroke: isDarkMode ? '#374151' : '#ddd' }}
            tickLine={false}
          />
          
          {/* Y축 - 주가 */}
          <YAxis 
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
              tick={{ fontSize: 12, fill: isDarkMode ? '#34d399' : '#10b981' }}
              axisLine={false}
              tickLine={false}
              tickFormatter={(value) => `${value}%`}
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
  );


  return (
    <div className="professional-stock-chart">
      {/* 메인 차트 */}
      <div className="main-chart">
        <div className="chart-scroll-container">
          <div className="chart-content">
            <SimpleLineChart />
          </div>
        </div>
      </div>

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