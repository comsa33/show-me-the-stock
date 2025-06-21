from datetime import datetime, timedelta
from typing import Dict

import pandas as pd
import plotly.graph_objects as go


def create_candlestick_chart(data: pd.DataFrame, title: str) -> go.Figure:
    fig = go.Figure(
        data=go.Candlestick(
            x=data.index if "Date" not in data.columns else data["Date"],
            open=data["Open"],
            high=data["High"],
            low=data["Low"],
            close=data["Close"],
            name=title,
        )
    )

    fig.update_layout(
        title=f"{title} 주가 차트",
        yaxis_title="가격",
        xaxis_title="날짜",
        template="plotly_white",
        height=600,
    )

    return fig


def create_line_chart(
    data: pd.DataFrame, title: str, y_column: str = "Close"
) -> go.Figure:
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=data.index if "Date" not in data.columns else data["Date"],
            y=data[y_column],
            mode="lines",
            name=title,
            line=dict(width=2),
        )
    )

    fig.update_layout(
        title=f"{title} {y_column} 추이",
        yaxis_title="가격",
        xaxis_title="날짜",
        template="plotly_white",
        height=400,
    )

    return fig


def create_volume_chart(data: pd.DataFrame, title: str) -> go.Figure:
    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=data.index if "Date" not in data.columns else data["Date"],
            y=data["Volume"],
            name="거래량",
            marker_color="lightblue",
        )
    )

    fig.update_layout(
        title=f"{title} 거래량",
        yaxis_title="거래량",
        xaxis_title="날짜",
        template="plotly_white",
        height=300,
    )

    return fig


def create_comparison_chart(
    data_dict: Dict[str, pd.DataFrame], title: str
) -> go.Figure:
    fig = go.Figure()

    for name, data in data_dict.items():
        fig.add_trace(
            go.Scatter(
                x=data.index if "Date" not in data.columns else data["Date"],
                y=data["Close"],
                mode="lines",
                name=name,
                line=dict(width=2),
            )
        )

    fig.update_layout(
        title=f"{title} 비교",
        yaxis_title="가격",
        xaxis_title="날짜",
        template="plotly_white",
        height=500,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )

    return fig


def calculate_technical_indicators(data: pd.DataFrame) -> pd.DataFrame:
    df = data.copy()

    # 이동평균선
    df["MA5"] = df["Close"].rolling(window=5).mean()
    df["MA20"] = df["Close"].rolling(window=20).mean()
    df["MA60"] = df["Close"].rolling(window=60).mean()

    # RSI
    delta = df["Close"].diff()
    gain = (delta.where(delta > 0, 0)).fillna(0)
    loss = (-delta.where(delta < 0, 0)).fillna(0)
    avg_gain = gain.rolling(window=14).mean()
    avg_loss = loss.rolling(window=14).mean()
    rs = avg_gain / avg_loss
    df["RSI"] = 100 - (100 / (1 + rs))

    # 볼린저 밴드
    df["BB_Middle"] = df["Close"].rolling(window=20).mean()
    bb_std = df["Close"].rolling(window=20).std()
    df["BB_Upper"] = df["BB_Middle"] + (bb_std * 2)
    df["BB_Lower"] = df["BB_Middle"] - (bb_std * 2)

    return df


def format_currency(value: float, currency: str = "KRW") -> str:
    if currency == "KRW":
        return f"₩{value:,.0f}"
    else:
        return f"${value:,.2f}"


def calculate_price_change(current: float, previous: float) -> tuple:
    change = current - previous
    change_percent = (change / previous) * 100 if previous != 0 else 0
    return change, change_percent


def create_interest_rate_chart(
    data_dict: Dict[str, pd.DataFrame], title: str
) -> go.Figure:
    fig = go.Figure()

    colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728"]

    for i, (name, data) in enumerate(data_dict.items()):
        fig.add_trace(
            go.Scatter(
                x=data["Date"],
                y=data["Rate"],
                mode="lines",
                name=name,
                line=dict(width=2, color=colors[i % len(colors)]),
            )
        )

    fig.update_layout(
        title=f"{title} 금리 비교",
        yaxis_title="금리 (%)",
        xaxis_title="날짜",
        template="plotly_white",
        height=400,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )

    return fig


def create_stock_with_interest_rate_chart(
    stock_data: pd.DataFrame,
    rate_data: pd.DataFrame,
    stock_name: str,
    rate_name: str,
    chart_type: str = "line",
) -> go.Figure:
    from plotly.subplots import make_subplots

    # 서브플롯 생성 (듀얼 y축)
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # 주식 데이터 (왼쪽 y축)
    if chart_type == "candlestick":
        fig.add_trace(
            go.Candlestick(
                x=(
                    stock_data.index
                    if "Date" not in stock_data.columns
                    else stock_data["Date"]
                ),
                open=stock_data["Open"],
                high=stock_data["High"],
                low=stock_data["Low"],
                close=stock_data["Close"],
                name=stock_name,
                yaxis="y",
            ),
            secondary_y=False,
        )
    else:
        fig.add_trace(
            go.Scatter(
                x=(
                    stock_data.index
                    if "Date" not in stock_data.columns
                    else stock_data["Date"]
                ),
                y=stock_data["Close"],
                mode="lines",
                name=stock_name,
                line=dict(width=2, color="#1f77b4"),
                yaxis="y",
            ),
            secondary_y=False,
        )

    # 금리 데이터 (오른쪽 y축)
    fig.add_trace(
        go.Scatter(
            x=rate_data["Date"],
            y=rate_data["Rate"],
            mode="lines",
            name=f"{rate_name} 금리",
            line=dict(width=2, color="#ff7f0e", dash="dash"),
            yaxis="y2",
        ),
        secondary_y=True,
    )

    # 축 설정
    fig.update_yaxes(title_text=f"{stock_name} 주가", secondary_y=False)
    fig.update_yaxes(title_text="금리 (%)", secondary_y=True)

    fig.update_layout(
        title=f"{stock_name} 주가 vs {rate_name} 금리",
        xaxis_title="날짜",
        template="plotly_white",
        height=600,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )

    return fig


def get_market_status() -> Dict[str, Dict[str, str]]:
    import pytz

    # 한국 시간 (KST)
    kr_tz = pytz.timezone("Asia/Seoul")
    kr_now = datetime.now(kr_tz)

    # 미국 동부 시간 (EST/EDT)
    us_tz = pytz.timezone("America/New_York")
    us_now = datetime.now(us_tz)

    # 한국 시장 시간 (09:00 - 15:20, 월-금)
    kr_open = kr_now.replace(hour=9, minute=0, second=0, microsecond=0)
    kr_close = kr_now.replace(hour=15, minute=20, second=0, microsecond=0)
    kr_is_open = kr_open <= kr_now <= kr_close and kr_now.weekday() < 5

    # 미국 시장 시간 (09:30 - 16:00 EST/EDT, 월-금)
    us_open = us_now.replace(hour=9, minute=30, second=0, microsecond=0)
    us_close = us_now.replace(hour=16, minute=0, second=0, microsecond=0)
    us_is_open = us_open <= us_now <= us_close and us_now.weekday() < 5

    # 요일 이름
    days_kr = ["월", "화", "수", "목", "금", "토", "일"]
    days_en = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

    # 다음 거래일 정보
    def get_next_trading_day_info(is_open, current_time, open_time, close_time):
        if is_open:
            remaining = close_time - current_time
            hours = remaining.seconds // 3600
            minutes = (remaining.seconds % 3600) // 60
            return f"마감까지 {hours}시간 {minutes}분"
        else:
            # 주말인지 확인 (토요일=5, 일요일=6)
            if current_time.weekday() >= 5:  # 주말
                # 다음 월요일까지 계산
                days_until_monday = (7 - current_time.weekday()) % 7
                if days_until_monday == 0:  # 일요일인 경우
                    days_until_monday = 1

                next_monday = (
                    current_time + timedelta(days=days_until_monday)
                ).replace(
                    hour=open_time.hour,
                    minute=open_time.minute,
                    second=0,
                    microsecond=0,
                )
                remaining = next_monday - current_time

            elif current_time.weekday() < 5:  # 평일 (월-금)
                # 금요일 오후인 경우 다음 월요일까지
                if current_time.weekday() == 4 and current_time.hour >= close_time.hour:
                    # 금요일 장마감 후
                    next_monday = (current_time + timedelta(days=3)).replace(
                        hour=open_time.hour,
                        minute=open_time.minute,
                        second=0,
                        microsecond=0,
                    )
                    remaining = next_monday - current_time
                else:
                    # 평일 장 시작 전이거나 장 마감 후
                    if current_time.hour < open_time.hour or (
                        current_time.hour == open_time.hour
                        and current_time.minute < open_time.minute
                    ):
                        # 오늘 장 시작 전
                        remaining = open_time - current_time
                    else:
                        # 오늘 장 마감 후, 내일 장 시작까지
                        next_day = (current_time + timedelta(days=1)).replace(
                            hour=open_time.hour,
                            minute=open_time.minute,
                            second=0,
                            microsecond=0,
                        )
                        remaining = next_day - current_time

            hours = remaining.total_seconds() // 3600
            days = int(hours // 24)
            hours = int(hours % 24)

            if days > 0:
                return f"장 시작까지 {days}일 {hours}시간"
            else:
                return f"장 시작까지 {hours}시간"

    kr_next_info = get_next_trading_day_info(kr_is_open, kr_now, kr_open, kr_close)
    us_next_info = get_next_trading_day_info(us_is_open, us_now, us_open, us_close)

    return {
        "KR (KOSPI)": {
            "status": "장중" if kr_is_open else "장마감",
            "current_time": kr_now.strftime("%H:%M:%S KST"),
            "day_info": f"{kr_now.strftime('%m/%d')} ({days_kr[kr_now.weekday()]})",
            "trading_hours": "09:00 - 15:20 (월~금)",
            "next_info": kr_next_info,
        },
        "US (NASDAQ)": {
            "status": "장중" if us_is_open else "장마감",
            "current_time": us_now.strftime("%H:%M:%S EST"),
            "day_info": f"{us_now.strftime('%m/%d')} ({days_en[us_now.weekday()]})",
            "trading_hours": "09:30 - 16:00 (월~금)",
            "next_info": us_next_info,
        },
    }
