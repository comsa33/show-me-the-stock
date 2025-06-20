import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from typing import Dict

def create_candlestick_chart(data: pd.DataFrame, title: str) -> go.Figure:
    fig = go.Figure(data=go.Candlestick(
        x=data.index if 'Date' not in data.columns else data['Date'],
        open=data['Open'],
        high=data['High'],
        low=data['Low'],
        close=data['Close'],
        name=title
    ))
    
    fig.update_layout(
        title=f"{title} 주가 차트",
        yaxis_title="가격",
        xaxis_title="날짜",
        template="plotly_white",
        height=600
    )
    
    return fig

def create_line_chart(data: pd.DataFrame, title: str, y_column: str = 'Close') -> go.Figure:
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=data.index if 'Date' not in data.columns else data['Date'],
        y=data[y_column],
        mode='lines',
        name=title,
        line=dict(width=2)
    ))
    
    fig.update_layout(
        title=f"{title} {y_column} 추이",
        yaxis_title="가격",
        xaxis_title="날짜",
        template="plotly_white",
        height=400
    )
    
    return fig

def create_volume_chart(data: pd.DataFrame, title: str) -> go.Figure:
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=data.index if 'Date' not in data.columns else data['Date'],
        y=data['Volume'],
        name='거래량',
        marker_color='lightblue'
    ))
    
    fig.update_layout(
        title=f"{title} 거래량",
        yaxis_title="거래량",
        xaxis_title="날짜",
        template="plotly_white",
        height=300
    )
    
    return fig

def create_comparison_chart(data_dict: Dict[str, pd.DataFrame], title: str) -> go.Figure:
    fig = go.Figure()
    
    for name, data in data_dict.items():
        fig.add_trace(go.Scatter(
            x=data.index if 'Date' not in data.columns else data['Date'],
            y=data['Close'],
            mode='lines',
            name=name,
            line=dict(width=2)
        ))
    
    fig.update_layout(
        title=f"{title} 비교",
        yaxis_title="가격",
        xaxis_title="날짜",
        template="plotly_white",
        height=500,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    return fig

def calculate_technical_indicators(data: pd.DataFrame) -> pd.DataFrame:
    df = data.copy()
    
    # 이동평균선
    df['MA5'] = df['Close'].rolling(window=5).mean()
    df['MA20'] = df['Close'].rolling(window=20).mean()
    df['MA60'] = df['Close'].rolling(window=60).mean()
    
    # RSI
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).fillna(0)
    loss = (-delta.where(delta < 0, 0)).fillna(0)
    avg_gain = gain.rolling(window=14).mean()
    avg_loss = loss.rolling(window=14).mean()
    rs = avg_gain / avg_loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # 볼린저 밴드
    df['BB_Middle'] = df['Close'].rolling(window=20).mean()
    bb_std = df['Close'].rolling(window=20).std()
    df['BB_Upper'] = df['BB_Middle'] + (bb_std * 2)
    df['BB_Lower'] = df['BB_Middle'] - (bb_std * 2)
    
    return df

def format_currency(value: float, currency: str = 'KRW') -> str:
    if currency == 'KRW':
        return f"₩{value:,.0f}"
    else:
        return f"${value:,.2f}"

def calculate_price_change(current: float, previous: float) -> tuple:
    change = current - previous
    change_percent = (change / previous) * 100 if previous != 0 else 0
    return change, change_percent

def get_market_status() -> Dict[str, str]:
    now = datetime.now()
    
    # 한국 시장 (KST 기준)
    kr_open = now.replace(hour=9, minute=0, second=0, microsecond=0)
    kr_close = now.replace(hour=15, minute=20, second=0, microsecond=0)
    
    # 미국 시장 (EST 기준, 간단히 UTC+9 기준으로 계산)
    us_open = now.replace(hour=23, minute=30, second=0, microsecond=0)
    us_close = now.replace(hour=6, minute=0, second=0, microsecond=0)
    
    kr_status = "장중" if kr_open <= now <= kr_close and now.weekday() < 5 else "장마감"
    us_status = "장중" if (now >= us_open or now <= us_close) and now.weekday() < 5 else "장마감"
    
    return {
        'KR': kr_status,
        'US': us_status
    }