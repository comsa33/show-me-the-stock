import React, { useState, useMemo } from 'react';
import {
  ComposedChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Area,
  AreaChart,
  BarChart,
  Bar
} from 'recharts';
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
  showInterestRate: boolean;
  interestRateData?: Array<{ date: string; rate: number }>;
  onToggleInterestRate?: (enabled: boolean) => void;
}

type ChartType = 'candlestick' | 'line' | 'area' | 'volume';

const ProfessionalStockChart: React.FC<ChartProps> = ({
  data,
  symbol,
  market,
  showInterestRate,
  interestRateData = [],
  onToggleInterestRate
}) => {
  const [chartType, setChartType] = useState<ChartType>('candlestick');
  const [showVolume, setShowVolume] = useState(true);

  // 데이터 전처리
  const processedData = useMemo(() => {
    return data.map((point, index) => {
      const prevClose = index > 0 ? data[index - 1].Close : point.Open;
      const change = point.Close - prevClose;
      const changePercent = (change / prevClose) * 100;
      
      // 금리 데이터 매칭
      const interestRate = interestRateData.find(rate => rate.date === point.Date)?.rate || null;
      
      return {
        ...point,
        date: new Date(point.Date).toLocaleDateString('ko-KR', {
          month: 'short',
          day: 'numeric'
        }),
        fullDate: point.Date,
        change,
        changePercent,
        isPositive: point.Close >= point.Open,
        bodyHeight: Math.abs(point.Close - point.Open),
        shadowTop: point.High,
        shadowBottom: point.Low,
        interestRate,
        // 이동평균 계산 (5일, 20일)
        ma5: index >= 4 ? data.slice(index - 4, index + 1).reduce((sum, d) => sum + d.Close, 0) / 5 : null,
        ma20: index >= 19 ? data.slice(index - 19, index + 1).reduce((sum, d) => sum + d.Close, 0) / 20 : null,
      };
    });
  }, [data, interestRateData]);

  // 가격 범위 계산
  const priceRange = useMemo(() => {
    const prices = data.flatMap(d => [d.High, d.Low]);
    const min = Math.min(...prices);
    const max = Math.max(...prices);
    const padding = (max - min) * 0.1;
    return { min: min - padding, max: max + padding };
  }, [data]);


  // 포맷팅 함수들
  const formatPrice = (price: number) => {
    if (market === 'KR') {
      return `₩${price.toLocaleString()}`;
    }
    return `$${price.toFixed(2)}`;
  };

  const formatVolume = (volume: number) => {
    if (volume >= 1000000) {
      return `${(volume / 1000000).toFixed(1)}M`;
    } else if (volume >= 1000) {
      return `${(volume / 1000).toFixed(1)}K`;
    }
    return volume.toString();
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
                <span>시가:</span>
                <span>{formatPrice(data.Open)}</span>
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
                <span>종가:</span>
                <span className={data.isPositive ? 'positive-price' : 'negative-price'}>
                  {formatPrice(data.Close)}
                </span>
              </div>
              <div className="price-row">
                <span>변동:</span>
                <span className={data.change >= 0 ? 'positive-change' : 'negative-change'}>
                  {data.change >= 0 ? '+' : ''}{formatPrice(data.change)} 
                  ({data.changePercent >= 0 ? '+' : ''}{data.changePercent.toFixed(2)}%)
                </span>
              </div>
              <div className="price-row">
                <span>거래량:</span>
                <span>{formatVolume(data.Volume)}</span>
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

  // 캔들스틱 컴포넌트
  const CandlestickChart = () => (
    <div className="candlestick-container">
      <ResponsiveContainer width="100%" height={400}>
        <ComposedChart data={processedData} margin={{ top: 20, right: showInterestRate ? 60 : 30, left: 20, bottom: 20 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis 
            dataKey="date" 
            tick={{ fontSize: 12, fill: '#666' }}
            axisLine={{ stroke: '#ddd' }}
          />
          <YAxis 
            domain={[priceRange.min, priceRange.max]}
            tick={{ fontSize: 12, fill: '#666' }}
            axisLine={{ stroke: '#ddd' }}
            tickFormatter={formatPrice}
          />
          <Tooltip content={<CustomTooltip />} />
          
          {/* 이동평균선 */}
          <Line 
            type="monotone" 
            dataKey="ma5" 
            stroke="#ff7300" 
            strokeWidth={1}
            dot={false}
            connectNulls={false}
            name="5일 이평"
          />
          <Line 
            type="monotone" 
            dataKey="ma20" 
            stroke="#8884d8" 
            strokeWidth={1}
            dot={false}
            connectNulls={false}
            name="20일 이평"
          />
          
          {/* 금리 오버레이 */}
          {showInterestRate && interestRateData.length > 0 && (
            <>
              <YAxis 
                yAxisId="right" 
                orientation="right"
                tick={{ fontSize: 12, fill: '#82ca9d' }}
                axisLine={{ stroke: '#82ca9d' }}
                tickFormatter={(value) => `${value}%`}
              />
              <Line 
                yAxisId="right"
                type="monotone" 
                dataKey="interestRate" 
                stroke="#82ca9d" 
                strokeWidth={2}
                dot={false}
                name="금리"
                strokeDasharray="5 5"
              />
            </>
          )}
        </ComposedChart>
      </ResponsiveContainer>
      
      {/* 커스텀 캔들스틱 오버레이 */}
      <div className="candlestick-overlay">
        {processedData.map((point, index) => {
          const x = (index / (processedData.length - 1)) * 100;
          const bodyTop = ((priceRange.max - Math.max(point.Open, point.Close)) / (priceRange.max - priceRange.min)) * 100;
          const bodyHeight = (Math.abs(point.Close - point.Open) / (priceRange.max - priceRange.min)) * 100;
          const wickTop = ((priceRange.max - point.High) / (priceRange.max - priceRange.min)) * 100;
          const wickBottom = ((priceRange.max - point.Low) / (priceRange.max - priceRange.min)) * 100;
          
          return (
            <div key={index} className="candle" style={{ left: `${x}%` }}>
              {/* 심지 (Wick) */}
              <div 
                className="wick"
                style={{
                  top: `${wickTop}%`,
                  height: `${wickBottom - wickTop}%`
                }}
              />
              {/* 몸통 (Body) */}
              <div 
                className={`body ${point.isPositive ? 'positive' : 'negative'}`}
                style={{
                  top: `${bodyTop}%`,
                  height: `${Math.max(bodyHeight, 0.5)}%`
                }}
              />
            </div>
          );
        })}
      </div>
    </div>
  );

  // 선형 차트
  const LineChart = () => (
    <ResponsiveContainer width="100%" height={400}>
      <AreaChart data={processedData} margin={{ top: 20, right: showInterestRate ? 60 : 30, left: 20, bottom: 20 }}>
        <defs>
          <linearGradient id="colorPrice" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#8884d8" stopOpacity={0.8}/>
            <stop offset="95%" stopColor="#8884d8" stopOpacity={0}/>
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
        <XAxis 
          dataKey="date" 
          tick={{ fontSize: 12, fill: '#666' }}
          axisLine={{ stroke: '#ddd' }}
        />
        <YAxis 
          tick={{ fontSize: 12, fill: '#666' }}
          axisLine={{ stroke: '#ddd' }}
          tickFormatter={formatPrice}
        />
        
        {/* 금리 오버레이 */}
        {showInterestRate && interestRateData.length > 0 && (
          <YAxis 
            yAxisId="right" 
            orientation="right"
            tick={{ fontSize: 12, fill: '#82ca9d' }}
            axisLine={{ stroke: '#82ca9d' }}
            tickFormatter={(value) => `${value}%`}
          />
        )}
        
        <Tooltip content={<CustomTooltip />} />
        <Area 
          type="monotone" 
          dataKey="Close" 
          stroke="#8884d8" 
          fillOpacity={1} 
          fill="url(#colorPrice)" 
          strokeWidth={2}
        />
        
        {/* 이동평균선 */}
        <Line type="monotone" dataKey="ma5" stroke="#ff7300" strokeWidth={1} dot={false} />
        <Line type="monotone" dataKey="ma20" stroke="#82ca9d" strokeWidth={1} dot={false} />
        
        {/* 금리 오버레이 */}
        {showInterestRate && interestRateData.length > 0 && (
          <Line 
            yAxisId="right"
            type="monotone" 
            dataKey="interestRate" 
            stroke="#82ca9d" 
            strokeWidth={2}
            dot={false}
            name="금리"
            strokeDasharray="5 5"
          />
        )}
      </AreaChart>
    </ResponsiveContainer>
  );

  // 거래량 차트
  const VolumeChart = () => (
    <ResponsiveContainer width="100%" height={150}>
      <BarChart data={processedData} margin={{ top: 10, right: 30, left: 20, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
        <XAxis dataKey="date" tick={{ fontSize: 10, fill: '#666' }} />
        <YAxis tick={{ fontSize: 10, fill: '#666' }} tickFormatter={formatVolume} />
        <Tooltip 
          formatter={(value: any) => [formatVolume(value), '거래량']}
          labelFormatter={(label) => `날짜: ${label}`}
        />
        <Bar dataKey="Volume" fill="#8884d8" opacity={0.7} />
      </BarChart>
    </ResponsiveContainer>
  );

  return (
    <div className="professional-stock-chart">
      {/* 차트 컨트롤 */}
      <div className="chart-controls-advanced">
        <div className="chart-type-selector">
          <button 
            className={`chart-type-btn ${chartType === 'candlestick' ? 'active' : ''}`}
            onClick={() => setChartType('candlestick')}
          >
            <span className="icon">📊</span>
            캔들스틱
          </button>
          <button 
            className={`chart-type-btn ${chartType === 'line' ? 'active' : ''}`}
            onClick={() => setChartType('line')}
          >
            <span className="icon">📈</span>
            선형
          </button>
          <button 
            className={`chart-type-btn ${chartType === 'area' ? 'active' : ''}`}
            onClick={() => setChartType('area')}
          >
            <span className="icon">🏔️</span>
            영역
          </button>
        </div>
        
        <div className="chart-options-advanced">
          <label className="toggle-switch">
            <input 
              type="checkbox" 
              checked={showVolume}
              onChange={(e) => setShowVolume(e.target.checked)}
            />
            <span className="slider"></span>
            거래량 표시
          </label>
          
          <label className="toggle-switch">
            <input 
              type="checkbox" 
              checked={showInterestRate}
              onChange={(e) => onToggleInterestRate?.(e.target.checked)}
            />
            <span className="slider"></span>
            금리 오버레이
          </label>
        </div>
      </div>

      {/* 메인 차트 */}
      <div className="main-chart">
        {chartType === 'candlestick' && <CandlestickChart />}
        {chartType === 'line' && <LineChart />}
        {chartType === 'area' && <LineChart />}
      </div>

      {/* 거래량 차트 */}
      {showVolume && (
        <div className="volume-chart">
          <h4>거래량</h4>
          <VolumeChart />
        </div>
      )}

      {/* 차트 범례 */}
      <div className="chart-legend">
        <div className="legend-item">
          <span className="legend-color" style={{ backgroundColor: '#ff7300' }}></span>
          5일 이동평균
        </div>
        <div className="legend-item">
          <span className="legend-color" style={{ backgroundColor: '#8884d8' }}></span>
          20일 이동평균
        </div>
        {showInterestRate && interestRateData.length > 0 && (
          <div className="legend-item">
            <span className="legend-color legend-dashed" style={{ backgroundColor: '#82ca9d' }}></span>
            금리 ({market === 'KR' ? '한국은행 기준금리' : '연준 기준금리'})
          </div>
        )}
      </div>
    </div>
  );
};

export default ProfessionalStockChart;