import os
import sys

import streamlit as st

# 프로젝트 루트 디렉토리를 파이썬 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.ai.gemini_analyzer import GeminiStockAnalyzer
from src.data.interest_rate_data import InterestRateDataFetcher
from src.data.stock_data import StockDataFetcher
from src.utils.helpers import (
    calculate_price_change,
    calculate_technical_indicators,
    create_candlestick_chart,
    create_comparison_chart,
    create_interest_rate_chart,
    create_line_chart,
    create_stock_with_interest_rate_chart,
    create_volume_chart,
    format_currency,
    get_market_status,
)

# 페이지 설정
st.set_page_config(
    page_title="주식 정보 대시보드",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 제목
st.title("📈 주식 정보 대시보드")
st.markdown("국내(KOSPI) 및 해외(NASDAQ) 주식 정보를 실시간으로 확인하세요!")

# Navigation
col1, col2 = st.columns([3, 1])
with col2:
    if st.button("🔮 AI 예측 페이지", type="secondary", use_container_width=True):
        st.switch_page("pages/prediction.py")

# 사이드바 설정
st.sidebar.header("필터 설정")


# 데이터 페처 및 AI 분석기 초기화
@st.cache_resource
def init_data_fetcher():
    return StockDataFetcher()


@st.cache_resource
def init_ai_analyzer():
    return GeminiStockAnalyzer()


@st.cache_resource
def init_rate_fetcher():
    return InterestRateDataFetcher()


data_fetcher = init_data_fetcher()
ai_analyzer = init_ai_analyzer()
rate_fetcher = init_rate_fetcher()

# 시장 선택
market = st.sidebar.selectbox("시장 선택", ["US (NASDAQ)", "KR (KOSPI)"], index=0)

market_code = "US" if "US" in market else "KR"

# 주식 선택
if market_code == "KR":
    available_stocks = data_fetcher.kospi_symbols
    stock_symbol_type = "종목 코드"
else:
    available_stocks = data_fetcher.nasdaq_symbols
    stock_symbol_type = "심볼"

selected_stock_names = st.sidebar.multiselect(
    f"주식 선택 ({stock_symbol_type})",
    options=list(available_stocks.keys()),
    default=list(available_stocks.keys())[:3],
)

# 기간 선택
period_options = {
    "1개월": "1mo",
    "3개월": "3mo",
    "6개월": "6mo",
    "1년": "1y",
    "2년": "2y",
    "5년": "5y",
}

selected_period = st.sidebar.selectbox(
    "조회 기간", options=list(period_options.keys()), index=3
)

# 차트 타입 선택
chart_type = st.sidebar.selectbox("차트 타입", ["캔들스틱", "라인", "비교"], index=0)

# 차트 옵션
st.sidebar.markdown("### 📊 차트 옵션")
show_indicators = st.sidebar.checkbox(
    "📈 기술적 지표 (이동평균선, RSI)",
    value=False,
    help="차트에 이동평균선을 표시하고 하단에 지표 요약을 보여줍니다",
)
show_volume = st.sidebar.checkbox(
    "📊 거래량 차트", value=True, help="주가 차트 하단에 거래량 차트를 표시합니다"
)

# AI 분석 옵션
st.sidebar.markdown("### 🤖 AI 분석 옵션")
show_ai_analysis = st.sidebar.checkbox(
    "🤖 AI 종합 분석",
    value=True,
    help="AI가 주가 데이터를 분석하여 인사이트를 제공합니다",
)
show_technical_ai = st.sidebar.checkbox(
    "🔍 AI 기술적 분석",
    value=False,
    help="AI가 기술적 지표를 해석하여 추가 분석을 제공합니다",
)
show_realtime_ai = st.sidebar.checkbox(
    "🌐 실시간 정보 AI 분석",
    value=False,
    help="최신 뉴스와 시장 정보를 포함한 Google 검색 기반 종합 분석을 제공합니다",
)

# 금리 정보 옵션
st.sidebar.markdown("### 💰 금리 정보 옵션")
show_interest_rates = st.sidebar.checkbox(
    "📊 금리 차트 (별도)",
    value=False,
    help="한국/미국 금리 변동을 별도 차트로 표시합니다",
)
show_rate_overlay = st.sidebar.checkbox(
    "📈 주가+금리 (동일 차트)",
    value=False,
    help="주가 차트에 금리를 듀얼축으로 함께 표시합니다 (단일 주식 선택 시만 가능)",
)

# 시장 상태 표시
st.sidebar.markdown("---")
st.sidebar.subheader("시장 상태")
market_status = get_market_status()
for market_name, status in market_status.items():
    color = "🟢" if status == "장중" else "🔴"
    st.sidebar.markdown(f"{color} {market_name}: {status}")

# 현재 금리 표시
if show_interest_rates:
    st.sidebar.markdown("---")
    st.sidebar.subheader("📊 현재 금리")
    current_rates = rate_fetcher.get_current_rates()

    if current_rates.get("US_10Y"):
        st.sidebar.metric("🇺🇸 미국 10Y", f"{current_rates['US_10Y']:.2f}%")
    if current_rates.get("KR_3Y"):
        st.sidebar.metric("🇰🇷 한국 3Y", f"{current_rates['KR_3Y']:.2f}%")

# 캐시 상태 표시
if show_ai_analysis or show_technical_ai or show_realtime_ai:
    st.sidebar.markdown("---")
    st.sidebar.subheader("💾 AI 분석 캐시")
    cache_count = len(st.session_state.get("ai_cache", {}))
    st.sidebar.info(f"저장된 분석 결과: {cache_count}개")

    if st.sidebar.button("🗑️ 캐시 초기화"):
        if "ai_cache" in st.session_state:
            st.session_state.ai_cache = {}
        st.sidebar.success("캐시가 초기화되었습니다!")

# 메인 컨테이너
if selected_stock_names:
    # 선택된 주식들의 심볼 가져오기
    selected_symbols = [available_stocks[name] for name in selected_stock_names]

    # 데이터 로딩
    with st.spinner("데이터를 불러오는 중..."):
        stock_data = data_fetcher.get_multiple_stocks(
            selected_symbols, period_options[selected_period], market_code
        )

    if stock_data:
        # 단일 주식 선택 시 상세 정보 표시
        if len(selected_symbols) == 1:
            symbol = selected_symbols[0]
            stock_name = selected_stock_names[0]
            data = stock_data[symbol]

            # 주식 정보 헤더
            col1, col2, col3, col4 = st.columns(4)

            current_price = data["Close"].iloc[-1]
            prev_price = data["Close"].iloc[-2] if len(data) > 1 else current_price
            change, change_percent = calculate_price_change(current_price, prev_price)

            with col1:
                st.metric(
                    label="현재가",
                    value=format_currency(
                        current_price, "KRW" if market_code == "KR" else "USD"
                    ),
                    delta=f"{change:+.2f} ({change_percent:+.2f}%)",
                )

            with col2:
                st.metric(label="거래량", value=f"{data['Volume'].iloc[-1]:,}")

            with col3:
                st.metric(
                    label="고가",
                    value=format_currency(
                        data["High"].iloc[-1], "KRW" if market_code == "KR" else "USD"
                    ),
                )

            with col4:
                st.metric(
                    label="저가",
                    value=format_currency(
                        data["Low"].iloc[-1], "KRW" if market_code == "KR" else "USD"
                    ),
                )

            # 기술적 지표 계산 (AI 분석이나 기술적 지표 표시 시 필요)
            if (
                show_indicators
                or show_ai_analysis
                or show_technical_ai
                or show_realtime_ai
            ):
                data = calculate_technical_indicators(data)

            # 차트 표시
            if show_rate_overlay:
                # 금리 데이터 가져오기
                with st.spinner("금리 데이터를 불러오는 중..."):
                    if market_code == "US":
                        rate_data = rate_fetcher.get_us_interest_rate(
                            period_options[selected_period]
                        )
                        rate_name = "미국"
                    else:
                        rate_data = rate_fetcher.get_kr_interest_rate(
                            period_options[selected_period]
                        )
                        rate_name = "한국"

                if rate_data is not None:
                    # 듀얼 축 차트 생성
                    chart_type_for_overlay = (
                        "candlestick" if chart_type == "캔들스틱" else "line"
                    )
                    fig = create_stock_with_interest_rate_chart(
                        data, rate_data, stock_name, rate_name, chart_type_for_overlay
                    )

                    # 기술적 지표 추가
                    if show_indicators:
                        fig.add_scatter(
                            x=(
                                data.index
                                if "Date" not in data.columns
                                else data["Date"]
                            ),
                            y=data["MA5"],
                            name="MA5",
                            line=dict(color="blue", width=1),
                            secondary_y=False,
                        )
                        fig.add_scatter(
                            x=(
                                data.index
                                if "Date" not in data.columns
                                else data["Date"]
                            ),
                            y=data["MA20"],
                            name="MA20",
                            line=dict(color="red", width=1),
                            secondary_y=False,
                        )

                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("금리 데이터를 불러올 수 없어 일반 차트를 표시합니다.")
                    # 일반 차트로 대체
                    if chart_type == "캔들스틱":
                        fig = create_candlestick_chart(data, stock_name)
                    else:
                        fig = create_line_chart(data, stock_name)
                    st.plotly_chart(fig, use_container_width=True)
            else:
                # 일반 차트
                if chart_type == "캔들스틱":
                    fig = create_candlestick_chart(data, stock_name)

                    # 기술적 지표 추가
                    if show_indicators:
                        fig.add_scatter(
                            x=(
                                data.index
                                if "Date" not in data.columns
                                else data["Date"]
                            ),
                            y=data["MA5"],
                            name="MA5",
                            line=dict(color="blue", width=1),
                        )
                        fig.add_scatter(
                            x=(
                                data.index
                                if "Date" not in data.columns
                                else data["Date"]
                            ),
                            y=data["MA20"],
                            name="MA20",
                            line=dict(color="red", width=1),
                        )

                    st.plotly_chart(fig, use_container_width=True)

                elif chart_type == "라인":
                    fig = create_line_chart(data, stock_name)
                    st.plotly_chart(fig, use_container_width=True)

            # 거래량 차트
            if show_volume:
                vol_fig = create_volume_chart(data, stock_name)
                st.plotly_chart(vol_fig, use_container_width=True)

            # 기술적 지표 상세 정보
            if show_indicators:
                st.subheader("📈 기술적 지표")
                st.info("💡 차트 위의 파란색(MA5), 빨간색(MA20) 선이 이동평균선입니다.")

                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    rsi_value = data["RSI"].iloc[-1]
                    rsi_status = (
                        "과매수"
                        if rsi_value > 70
                        else "과매도" if rsi_value < 30 else "중립"
                    )
                    st.metric(
                        "RSI", f"{rsi_value:.1f}", help=f"현재 상태: {rsi_status}"
                    )
                with col2:
                    st.metric(
                        "MA5 (5일 평균)",
                        format_currency(
                            data["MA5"].iloc[-1],
                            "KRW" if market_code == "KR" else "USD",
                        ),
                    )
                with col3:
                    st.metric(
                        "MA20 (20일 평균)",
                        format_currency(
                            data["MA20"].iloc[-1],
                            "KRW" if market_code == "KR" else "USD",
                        ),
                    )
                with col4:
                    current_vs_ma20 = (
                        (data["Close"].iloc[-1] - data["MA20"].iloc[-1])
                        / data["MA20"].iloc[-1]
                    ) * 100
                    st.metric("MA20 대비", f"{current_vs_ma20:+.1f}%")

            # AI 분석 섹션
            if show_ai_analysis:
                st.subheader("🤖 AI 분석")

                # 종합 분석 (항상 표시)
                with st.spinner("AI가 주식을 분석중입니다..."):
                    ai_analysis = ai_analyzer.analyze_stock_data(
                        data, stock_name, market_code
                    )

                with st.expander("📊 AI 종합 분석", expanded=True):
                    st.markdown(ai_analysis)

                # 기술적 AI 분석 (선택 사항)
                if show_technical_ai:
                    with st.spinner("기술적 분석을 수행중입니다..."):
                        technical_analysis = ai_analyzer.get_technical_analysis(
                            data, stock_name
                        )

                    with st.expander("🔍 AI 기술적 분석", expanded=True):
                        st.markdown(technical_analysis)

                # 실시간 정보 AI 분석 (선택 사항)
                if show_realtime_ai:
                    with st.spinner(
                        "실시간 정보를 검색하고 분석중입니다... (Google 검색 포함)"
                    ):
                        realtime_analysis = ai_analyzer.analyze_with_real_time_info(
                            data, stock_name, market_code
                        )

                    with st.expander("🌐 실시간 정보 AI 분석", expanded=True):
                        st.markdown(realtime_analysis)
                        st.info(
                            "💡 이 분석은 Google 검색을 통한 최신 뉴스와 시장 정보를 포함합니다."
                        )

        # 여러 주식 비교
        elif chart_type == "비교" and len(selected_symbols) > 1:
            comparison_data = {}
            for i, symbol in enumerate(selected_symbols):
                if symbol in stock_data:
                    comparison_data[selected_stock_names[i]] = stock_data[symbol]

            if comparison_data:
                fig = create_comparison_chart(comparison_data, "주식 비교")
                st.plotly_chart(fig, use_container_width=True)

                # 비교 테이블
                st.subheader("주식 비교 테이블")
                comparison_df = []
                for name, symbol in zip(selected_stock_names, selected_symbols):
                    if symbol in stock_data:
                        data = stock_data[symbol]
                        current_price = data["Close"].iloc[-1]
                        prev_price = (
                            data["Close"].iloc[-2] if len(data) > 1 else current_price
                        )
                        change, change_percent = calculate_price_change(
                            current_price, prev_price
                        )

                        comparison_df.append(
                            {
                                "주식명": name,
                                "현재가": format_currency(
                                    current_price,
                                    "KRW" if market_code == "KR" else "USD",
                                ),
                                "변동률": f"{change_percent:+.2f}%",
                                "거래량": f"{data['Volume'].iloc[-1]:,}",
                            }
                        )

                st.dataframe(comparison_df, use_container_width=True)

                # AI 비교 분석
                if show_ai_analysis:
                    st.subheader("🤖 AI 비교 분석")
                    with st.spinner("AI가 주식들을 비교 분석중입니다..."):
                        comparison_analysis = ai_analyzer.compare_stocks(
                            comparison_data, market_code
                        )
                        st.markdown(comparison_analysis)

        # 개별 주식들 표시
        else:
            for i, symbol in enumerate(selected_symbols):
                if symbol in stock_data:
                    st.subheader(f"📊 {selected_stock_names[i]} ({symbol})")
                    data = stock_data[symbol]

                    # 기술적 지표 계산
                    if (
                        show_indicators
                        or show_ai_analysis
                        or show_technical_ai
                        or show_realtime_ai
                    ):
                        data = calculate_technical_indicators(data)

                    # 차트 표시
                    if chart_type == "캔들스틱":
                        fig = create_candlestick_chart(data, selected_stock_names[i])

                        # 기술적 지표 추가
                        if show_indicators:
                            fig.add_scatter(
                                x=(
                                    data.index
                                    if "Date" not in data.columns
                                    else data["Date"]
                                ),
                                y=data["MA5"],
                                name="MA5",
                                line=dict(color="blue", width=1),
                            )
                            fig.add_scatter(
                                x=(
                                    data.index
                                    if "Date" not in data.columns
                                    else data["Date"]
                                ),
                                y=data["MA20"],
                                name="MA20",
                                line=dict(color="red", width=1),
                            )
                    else:
                        fig = create_line_chart(data, selected_stock_names[i])

                        # 기술적 지표 추가
                        if show_indicators:
                            fig.add_scatter(
                                x=(
                                    data.index
                                    if "Date" not in data.columns
                                    else data["Date"]
                                ),
                                y=data["MA5"],
                                name="MA5",
                                line=dict(color="blue", width=1),
                            )
                            fig.add_scatter(
                                x=(
                                    data.index
                                    if "Date" not in data.columns
                                    else data["Date"]
                                ),
                                y=data["MA20"],
                                name="MA20",
                                line=dict(color="red", width=1),
                            )

                    st.plotly_chart(fig, use_container_width=True)

                    # 거래량 차트
                    if show_volume:
                        vol_fig = create_volume_chart(data, selected_stock_names[i])
                        st.plotly_chart(vol_fig, use_container_width=True)

                    # 기술적 지표 요약 (개별 주식용)
                    if show_indicators:
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            rsi_value = data["RSI"].iloc[-1]
                            rsi_status = (
                                "과매수"
                                if rsi_value > 70
                                else "과매도" if rsi_value < 30 else "중립"
                            )
                            st.metric(
                                "RSI", f"{rsi_value:.1f}", help=f"상태: {rsi_status}"
                            )
                        with col2:
                            st.metric(
                                "MA5",
                                format_currency(
                                    data["MA5"].iloc[-1],
                                    "KRW" if market_code == "KR" else "USD",
                                ),
                            )
                        with col3:
                            st.metric(
                                "MA20",
                                format_currency(
                                    data["MA20"].iloc[-1],
                                    "KRW" if market_code == "KR" else "USD",
                                ),
                            )

                    # AI 분석 (개별 주식용)
                    if show_ai_analysis:
                        with st.expander(f"🤖 {selected_stock_names[i]} AI 분석"):
                            with st.spinner("AI 분석중..."):
                                individual_analysis = ai_analyzer.analyze_stock_data(
                                    data, selected_stock_names[i], market_code
                                )
                                st.markdown(individual_analysis)

                    # 실시간 AI 분석 (개별 주식용)
                    if show_realtime_ai:
                        with st.expander(f"🌐 {selected_stock_names[i]} 실시간 분석"):
                            with st.spinner("실시간 정보 분석중..."):
                                realtime_analysis = (
                                    ai_analyzer.analyze_with_real_time_info(
                                        data, selected_stock_names[i], market_code
                                    )
                                )
                                st.markdown(realtime_analysis)

                    st.markdown("---")

        # 금리 정보 표시 (주식 데이터가 있을 때)
        if show_interest_rates:
            st.markdown("---")
            st.subheader("📊 금리 정보")

            with st.spinner("금리 데이터를 불러오는 중..."):
                rate_data = rate_fetcher.get_interest_rate_comparison(
                    period_options[selected_period]
                )

            if rate_data:
                fig = create_interest_rate_chart(rate_data, "한국/미국")
                st.plotly_chart(fig, use_container_width=True)

                # 금리 요약 테이블
                rate_summary = []
                for name, data in rate_data.items():
                    if not data.empty:
                        current_rate = data["Rate"].iloc[-1]
                        prev_rate = (
                            data["Rate"].iloc[-2] if len(data) > 1 else current_rate
                        )
                        change = current_rate - prev_rate

                        rate_summary.append(
                            {
                                "국가/기간": name,
                                "현재 금리": f"{current_rate:.2f}%",
                                "변동": f"{change:+.2f}%",
                            }
                        )

                if rate_summary:
                    st.dataframe(rate_summary, use_container_width=True)
            else:
                st.warning("금리 데이터를 불러올 수 없습니다.")
    else:
        st.error("선택한 주식의 데이터를 불러올 수 없습니다.")
else:
    st.info("사이드바에서 주식을 선택해주세요.")

    # 주식이 선택되지 않았을 때 시장 인사이트 표시
    if show_ai_analysis:
        st.subheader("🌐 시장 인사이트")
        top_stocks = list(available_stocks.keys())[:5]
        with st.spinner("시장 인사이트를 생성중입니다..."):
            market_insight = ai_analyzer.generate_market_insight(
                market_code, top_stocks
            )
            st.markdown(market_insight)

    # 주식이 선택되지 않았을 때도 금리 정보 표시
    if show_interest_rates:
        st.subheader("📊 금리 정보")

        with st.spinner("금리 데이터를 불러오는 중..."):
            rate_data = rate_fetcher.get_interest_rate_comparison("1y")

        if rate_data:
            fig = create_interest_rate_chart(rate_data, "한국/미국")
            st.plotly_chart(fig, use_container_width=True)

            # 금리 요약 테이블
            rate_summary = []
            for name, data in rate_data.items():
                if not data.empty:
                    current_rate = data["Rate"].iloc[-1]
                    prev_rate = data["Rate"].iloc[-2] if len(data) > 1 else current_rate
                    change = current_rate - prev_rate

                    rate_summary.append(
                        {
                            "국가/기간": name,
                            "현재 금리": f"{current_rate:.2f}%",
                            "변동": f"{change:+.2f}%",
                        }
                    )

            if rate_summary:
                st.dataframe(rate_summary, use_container_width=True)
        else:
            st.warning("금리 데이터를 불러올 수 없습니다.")

# 푸터
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center'>
        <p>📈 주식 정보 대시보드 | 데이터 제공: Yahoo Finance, FinanceDataReader</p>
        <p>⚠️ 투자 결정은 본인의 책임하에 이루어져야 합니다.</p>
    </div>
    """,
    unsafe_allow_html=True,
)
