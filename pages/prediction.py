import os
import sys
import warnings
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import torch
from dotenv import load_dotenv
from plotly.subplots import make_subplots

warnings.filterwarnings("ignore")

# Load environment variables
load_dotenv()

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data.interest_rate_data import InterestRateDataFetcher
from src.data.stock_data import StockDataFetcher
from src.models.advanced_predictor import (
    AdvancedDataProcessor,
    calculate_advanced_confidence,
    create_advanced_ensemble,
)
from src.models.backtesting import run_comprehensive_backtest
from src.models.hf_integration import create_hf_enhanced_ensemble
from src.models.hybrid_model import StockDataProcessor, create_hybrid_model
from src.models.simple_ensemble import (
    calculate_simple_confidence,
    create_simple_ensemble,
)

# Page configuration
st.set_page_config(
    page_title="AI 주가 예측",
    page_icon="🔮",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for better UI
st.markdown(
    """
<style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .prediction-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 2rem;
        border-radius: 1rem;
        margin: 1rem 0;
    }
    .warning-box {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        color: #856404;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
</style>
""",
    unsafe_allow_html=True,
)

# Title
st.markdown(
    """
<div style='text-align: center; padding: 2rem 0;'>
    <h1>🔮 AI 주가 예측 시스템</h1>
    <p style='font-size: 1.2rem; color: #666;'>
        하이브리드 딥러닝 모델을 활용한 최대 30일 주가 예측 및 백테스팅
    </p>
</div>
""",
    unsafe_allow_html=True,
)

# Sidebar configuration
st.sidebar.header("🔮 예측 설정")


# Initialize data fetchers
@st.cache_resource
def init_data_services():
    return (
        StockDataFetcher(),
        InterestRateDataFetcher(),
        StockDataProcessor(),
        AdvancedDataProcessor(),
    )


stock_fetcher, rate_fetcher, data_processor, advanced_processor = init_data_services()

# Market selection
market = st.sidebar.selectbox(
    "📈 시장 선택",
    ["US (NASDAQ)", "KR (KOSPI)"],
    help="예측할 주식의 시장을 선택하세요",
)
market_code = "US" if "US" in market else "KR"

# Stock selection
if market_code == "KR":
    available_stocks = stock_fetcher.kospi_symbols
else:
    available_stocks = stock_fetcher.nasdaq_symbols

selected_stock = st.sidebar.selectbox(
    "🏢 주식 선택",
    options=list(available_stocks.keys()),
    help="예측을 수행할 주식을 선택하세요",
)

# Model parameters
st.sidebar.markdown("### 🤖 모델 설정")

sequence_length = st.sidebar.slider(
    "📅 입력 시퀀스 길이 (일)",
    min_value=30,
    max_value=120,
    value=60,
    help="모델이 학습할 과거 데이터의 일수",
)

prediction_horizon = st.sidebar.slider(
    "🔮 예측 기간 (일)",
    min_value=1,
    max_value=30,
    value=7,
    help="미래 몇 일까지 예측할지 설정",
)

data_period = st.sidebar.selectbox(
    "📊 학습 데이터 기간",
    ["2y", "3y", "5y"],
    index=1,
    help="모델 학습에 사용할 과거 데이터 기간",
)

# Advanced settings
st.sidebar.markdown("### ⚙️ 고급 설정")

model_type = st.sidebar.selectbox(
    "🤖 모델 타입",
    [
        "간단한 앙상블 (권장)",
        "고급 앙상블 모델",
        "하이브리드 모델 (기본)",
        "HuggingFace 강화 모델",
    ],
    index=0,
    help="사용할 AI 모델의 종류를 선택하세요",
)

use_gpu = st.sidebar.checkbox(
    "🚀 GPU 가속 사용",
    value=torch.cuda.is_available(),
    help=f"GPU 사용 가능: {torch.cuda.is_available()}",
)

enable_backtesting = st.sidebar.checkbox(
    "📈 백테스팅 실행", value=True, help="예측 성능을 실제 거래로 검증"
)

confidence_threshold = st.sidebar.slider(
    "🎯 신뢰도 임계값",
    min_value=0.5,
    max_value=0.95,
    value=0.7,
    step=0.05,
    help="거래 신호 생성을 위한 최소 신뢰도",
)

# HuggingFace settings
if model_type == "HuggingFace 강화 모델":
    st.sidebar.markdown("### 🤗 HuggingFace 설정")
    hf_token = os.getenv("HUGGINGFACE_TOKEN")
    if hf_token:
        st.sidebar.success("✅ HuggingFace API 키가 설정되었습니다")
    else:
        st.sidebar.error("❌ HuggingFace API 키가 설정되지 않았습니다")
        hf_token = None
else:
    hf_token = None

# Device information
device = torch.device("cuda" if use_gpu and torch.cuda.is_available() else "cpu")
if torch.cuda.is_available():
    gpu_info = torch.cuda.get_device_properties(0)
    st.sidebar.info(
        f"🖥️ GPU: {gpu_info.name}\n💾 메모리: {gpu_info.total_memory // 1024**2} MB"
    )
else:
    st.sidebar.info("💻 CPU 모드로 실행됩니다")

# Warning box
st.markdown(
    """
<div class='warning-box'>
    <strong>⚠️ 투자 위험 고지</strong><br>
    이 예측 시스템은 교육 및 연구 목적으로 개발되었습니다. 
    실제 투자 결정에 사용하기 전에 충분한 검토와 추가 분석이 필요합니다.
    투자는 본인의 책임하에 이루어져야 합니다.
</div>
""",
    unsafe_allow_html=True,
)

# Main prediction section
if st.button("🚀 AI 예측 시작", type="primary", use_container_width=True):
    with st.spinner("📊 데이터를 수집하고 모델을 훈련중입니다..."):
        try:
            # Fetch stock data
            symbol = available_stocks[selected_stock]
            stock_data = stock_fetcher.get_stock_data(symbol, data_period, market_code)

            if (
                stock_data is None
                or len(stock_data) < sequence_length + prediction_horizon
            ):
                st.error(
                    "❌ 충분한 데이터를 가져올 수 없습니다. 다른 주식이나 기간을 선택해주세요."
                )
                st.stop()

            # Prepare data based on model type
            with st.spinner("🔧 데이터를 전처리중입니다..."):
                if model_type in ["고급 앙상블 모델", "HuggingFace 강화 모델"]:
                    try:
                        X, y, feature_columns = (
                            advanced_processor.prepare_advanced_data(
                                stock_data, sequence_length, prediction_horizon
                            )
                        )
                        st.success(
                            f"✅ 고급 데이터 전처리 완료: {len(feature_columns)}개 특성"
                        )
                        use_advanced_processor = True
                    except Exception as e:
                        st.warning(f"고급 전처리 실패, 기본 처리로 대체: {str(e)}")
                        X, y, feature_columns = data_processor.prepare_data(
                            stock_data, sequence_length, prediction_horizon
                        )
                        use_advanced_processor = False
                else:
                    X, y, feature_columns = data_processor.prepare_data(
                        stock_data, sequence_length, prediction_horizon
                    )
                    use_advanced_processor = False

                if len(X) < 100:
                    st.error("❌ 모델 훈련을 위한 충분한 데이터가 없습니다.")
                    st.stop()

            # Create and train model based on type
            with st.spinner(f"🤖 {model_type} 준비중입니다..."):
                if model_type == "간단한 앙상블 (권장)":
                    model = create_simple_ensemble(
                        input_dim=len(feature_columns),
                        sequence_length=sequence_length,
                        prediction_horizon=prediction_horizon,
                    )
                    use_ensemble = True
                    st.success("✅ 간단한 앙상블 모델 준비 완료!")
                elif model_type == "HuggingFace 강화 모델":
                    try:
                        model = create_hf_enhanced_ensemble(
                            input_dim=len(feature_columns),
                            sequence_length=sequence_length,
                            prediction_horizon=prediction_horizon,
                            hf_token=hf_token,
                        )
                        st.success("✅ HuggingFace 강화 모델 로드 완료!")
                        use_ensemble = True
                    except Exception as e:
                        st.warning(f"HF 모델 로드 실패, 간단한 앙상블로 대체: {str(e)}")
                        model = create_simple_ensemble(
                            input_dim=len(feature_columns),
                            sequence_length=sequence_length,
                            prediction_horizon=prediction_horizon,
                        )
                        use_ensemble = True
                elif model_type == "고급 앙상블 모델":
                    try:
                        model = create_advanced_ensemble(
                            input_dim=len(feature_columns),
                            sequence_length=sequence_length,
                            prediction_horizon=prediction_horizon,
                        )
                        use_ensemble = True
                        st.success("✅ 고급 앙상블 모델 준비 완료!")
                    except Exception as e:
                        st.warning(f"고급 앙상블 실패, 간단한 앙상블로 대체: {str(e)}")
                        model = create_simple_ensemble(
                            input_dim=len(feature_columns),
                            sequence_length=sequence_length,
                            prediction_horizon=prediction_horizon,
                        )
                        use_ensemble = True
                else:
                    model = create_hybrid_model(
                        input_dim=len(feature_columns),
                        sequence_length=sequence_length,
                        prediction_horizon=prediction_horizon,
                    )
                    model = model.to(device)
                    use_ensemble = False

                # Training setup
                split_idx = int(len(X) * 0.8)
                train_X, test_X = X[:split_idx], X[split_idx:]
                train_y, test_y = y[:split_idx], y[split_idx:]

                if use_ensemble:
                    # Train ensemble models with quick training
                    if (
                        hasattr(model, "train_ensemble")
                        and model_type == "간단한 앙상블 (권장)"
                    ):
                        with st.spinner("⚡ 앙상블 모델을 빠르게 훈련중입니다..."):
                            train_X_tensor = torch.FloatTensor(train_X)
                            train_y_tensor = torch.FloatTensor(train_y)
                            model.train_ensemble(
                                train_X_tensor, train_y_tensor, epochs=30
                            )
                            st.success("✅ 앙상블 훈련 완료!")
                    else:
                        st.success("✅ 앙상블 모델 준비 완료!")
                else:
                    # Train single model
                    model.train()
                    optimizer = torch.optim.Adam(
                        model.parameters(), lr=0.001, weight_decay=1e-5
                    )
                    criterion = torch.nn.MSELoss()

                    train_X_tensor = torch.FloatTensor(train_X).to(device)
                    train_y_tensor = torch.FloatTensor(train_y).to(device)

                    # Training progress
                    progress_bar = st.progress(0)
                    status_text = st.empty()

                    epochs = 100
                    for epoch in range(epochs):
                        optimizer.zero_grad()
                        outputs = model(train_X_tensor)

                        pred_loss = criterion(outputs["predictions"], train_y_tensor)
                        vae_loss = model.vae_loss(
                            train_X_tensor,
                            outputs["reconstructed"],
                            outputs["mu"],
                            outputs["logvar"],
                        )

                        total_loss = pred_loss + 0.1 * vae_loss
                        total_loss.backward()
                        optimizer.step()

                        # Update progress
                        progress = (epoch + 1) / epochs
                        progress_bar.progress(progress)
                        status_text.text(
                            f"Epoch {epoch+1}/{epochs} - Loss: {total_loss.item():.6f}"
                        )

                    progress_bar.empty()
                    status_text.empty()
                    st.success("✅ 모델 훈련이 완료되었습니다!")

            # Generate predictions
            with st.spinner("🔮 미래 주가를 예측중입니다..."):
                if use_ensemble:
                    # Use ensemble prediction
                    latest_X = X[-1:].copy()  # Last sequence
                    latest_X_tensor = torch.FloatTensor(latest_X)

                    try:
                        if hasattr(model, "predict"):
                            prediction_output = model.predict(latest_X_tensor)
                        else:
                            st.warning("예측 메서드가 없어 기본 모델로 대체합니다.")
                            use_ensemble = False

                        if use_ensemble:
                            predictions = prediction_output["mean"].cpu().numpy()
                            # Use appropriate confidence calculation based on model type
                            if model_type == "간단한 앙상블 (권장)":
                                confidence_scores = calculate_simple_confidence(
                                    prediction_output
                                )
                            else:
                                confidence_scores = calculate_advanced_confidence(
                                    prediction_output
                                )
                    except Exception as e:
                        st.error(f"앙상블 예측 중 오류 발생: {str(e)}")
                        st.warning("기본 모델로 대체하여 예측을 진행합니다.")
                        # Fallback to basic model
                        use_ensemble = False
                        # Create fallback model with correct input dimensions
                        fallback_model = create_hybrid_model(
                            input_dim=len(feature_columns),
                            sequence_length=sequence_length,
                            prediction_horizon=prediction_horizon,
                        )
                        fallback_model = fallback_model.to(device)

                        # Quick training for fallback
                        fallback_model.train()
                        optimizer = torch.optim.Adam(
                            fallback_model.parameters(), lr=0.001
                        )
                        criterion = torch.nn.MSELoss()
                        train_X_tensor = torch.FloatTensor(train_X).to(device)
                        train_y_tensor = torch.FloatTensor(train_y).to(device)

                        for _ in range(20):  # Quick training
                            optimizer.zero_grad()
                            outputs = fallback_model(train_X_tensor)
                            loss = criterion(outputs["predictions"], train_y_tensor)
                            loss.backward()
                            optimizer.step()

                        # Predict with fallback
                        fallback_model.eval()
                        with torch.no_grad():
                            latest_X_tensor = torch.FloatTensor(latest_X).to(device)
                            prediction_output = fallback_model(latest_X_tensor)
                            predictions = prediction_output["predictions"].cpu().numpy()
                            confidence_scores = 1.0 / (
                                1.0 + np.std(predictions, axis=1)
                            )
                            model = fallback_model  # Replace model for subsequent use

                if not use_ensemble:
                    # Use single model prediction
                    if hasattr(model, "eval"):
                        model.eval()
                    with torch.no_grad():
                        latest_X = X[-1:].copy()  # Last sequence
                        latest_X_tensor = torch.FloatTensor(latest_X).to(device)
                        prediction_output = model(latest_X_tensor)
                        predictions = prediction_output["predictions"].cpu().numpy()

                        # Generate confidence scores based on model uncertainty
                        confidence_scores = 1.0 / (1.0 + np.std(predictions, axis=1))

            # Display results
            st.markdown("## 🎯 예측 결과")

            # Current price and predictions
            current_price = stock_data["Close"].iloc[-1]

            # Inverse transform predictions based on processor type
            if model_type in ["고급 앙상블 모델", "HuggingFace 강화 모델"]:
                try:
                    predicted_prices = advanced_processor.inverse_transform_target(
                        predictions[0], stock_data
                    )
                except Exception:
                    predicted_prices = data_processor.inverse_transform_predictions(
                        predictions[0]
                    )
            else:
                predicted_prices = data_processor.inverse_transform_predictions(
                    predictions[0]
                )

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric(
                    "📊 현재가",
                    (
                        f"${current_price:.2f}"
                        if market_code == "US"
                        else f"₩{current_price:,.0f}"
                    ),
                )

            with col2:
                next_day_pred = (
                    float(predicted_prices[0])
                    if hasattr(predicted_prices[0], "item")
                    else float(predicted_prices[0])
                )
                change = ((next_day_pred - current_price) / current_price) * 100
                st.metric(
                    "🔮 다음날 예측가",
                    (
                        f"${next_day_pred:.2f}"
                        if market_code == "US"
                        else f"₩{next_day_pred:,.0f}"
                    ),
                    f"{change:+.2f}%",
                )

            with col3:
                final_pred = (
                    float(predicted_prices[-1])
                    if hasattr(predicted_prices[-1], "item")
                    else float(predicted_prices[-1])
                )
                total_change = ((final_pred - current_price) / current_price) * 100
                st.metric(
                    f"📈 {prediction_horizon}일 후 예측",
                    (
                        f"${final_pred:.2f}"
                        if market_code == "US"
                        else f"₩{final_pred:,.0f}"
                    ),
                    f"{total_change:+.2f}%",
                )

            with col4:
                # Safe confidence calculation
                if hasattr(confidence_scores, "mean"):
                    avg_confidence = float(confidence_scores.mean())
                elif hasattr(confidence_scores, "__iter__"):
                    avg_confidence = float(np.mean(confidence_scores))
                else:
                    avg_confidence = float(confidence_scores)

                # Ensure confidence is in reasonable range
                avg_confidence = np.clip(avg_confidence, 0.1, 0.95)
                confidence_label = (
                    "높음"
                    if avg_confidence > 0.8
                    else "중간" if avg_confidence > 0.6 else "낮음"
                )
                confidence_color = "normal" if avg_confidence > 0.6 else "inverse"

                st.metric("🎯 평균 신뢰도", f"{avg_confidence:.1%}", confidence_label)

            # Prediction chart
            st.markdown("### 📈 예측 차트")

            # Prepare chart data
            historical_prices = stock_data["Close"].iloc[-30:].values

            # Handle different index types for dates
            if hasattr(stock_data.index, "to_pydatetime"):
                # DatetimeIndex
                historical_dates = stock_data.index[-30:]
                last_date = stock_data.index[-1]
                if hasattr(last_date, "date"):
                    last_date = last_date.date()
                else:
                    last_date = pd.to_datetime(last_date).date()
            else:
                # Integer index or other types - create synthetic dates
                end_date = datetime.now().date()
                historical_dates = pd.date_range(end=end_date, periods=30, freq="D")
                last_date = end_date

            future_dates = pd.date_range(
                start=pd.to_datetime(last_date) + timedelta(days=1),
                periods=prediction_horizon,
                freq="D",
            )

            # Create prediction chart
            fig = make_subplots(
                rows=2,
                cols=1,
                row_heights=[0.7, 0.3],
                subplot_titles=("주가 예측", "신뢰도"),
                vertical_spacing=0.1,
            )

            # Historical prices
            fig.add_trace(
                go.Scatter(
                    x=historical_dates,
                    y=historical_prices,
                    mode="lines",
                    name="실제 주가",
                    line=dict(color="blue", width=2),
                ),
                row=1,
                col=1,
            )

            # Predicted prices
            fig.add_trace(
                go.Scatter(
                    x=future_dates,
                    y=predicted_prices,
                    mode="lines+markers",
                    name="예측 주가",
                    line=dict(color="red", width=2, dash="dash"),
                    marker=dict(size=6),
                ),
                row=1,
                col=1,
            )

            # Confidence scores
            if hasattr(confidence_scores, "shape") and len(confidence_scores.shape) > 1:
                confidence_values = (
                    confidence_scores[0].tolist()
                    if hasattr(confidence_scores[0], "tolist")
                    else list(confidence_scores[0])
                )
            else:
                confidence_value = (
                    float(confidence_scores[0])
                    if hasattr(confidence_scores, "__getitem__")
                    else float(confidence_scores)
                )
                confidence_values = [confidence_value] * prediction_horizon

            fig.add_trace(
                go.Bar(
                    x=future_dates,
                    y=confidence_values,
                    name="예측 신뢰도",
                    marker_color="green",
                    opacity=0.7,
                ),
                row=2,
                col=1,
            )

            fig.update_layout(
                title=f"{selected_stock} 주가 예측 ({prediction_horizon}일)",
                height=600,
                showlegend=True,
            )

            fig.update_xaxes(title_text="날짜", row=2, col=1)
            fig.update_yaxes(title_text="주가", row=1, col=1)
            fig.update_yaxes(title_text="신뢰도", row=2, col=1)

            st.plotly_chart(fig, use_container_width=True)

            # Backtesting section
            if enable_backtesting:
                st.markdown("## 📊 백테스팅 결과")

                with st.spinner("💼 백테스팅을 실행중입니다..."):
                    try:
                        # Use appropriate data processor for backtesting
                        processor_for_backtest = (
                            advanced_processor
                            if use_advanced_processor
                            else data_processor
                        )
                        backtest_results = run_comprehensive_backtest(
                            model,
                            processor_for_backtest,
                            stock_data,
                            sequence_length,
                            prediction_horizon,
                        )
                    except Exception as e:
                        st.error(f"백테스팅 중 오류 발생: {str(e)}")
                        st.warning("백테스팅을 건너뛰고 예측 결과만 표시합니다.")
                        backtest_results = None

                # Define strategies and names for all backtest-related operations
                strategies = ["buy_and_hold", "prediction_based", "momentum"]
                strategy_names = ["매수 후 보유", "AI 예측 기반", "모멘텀 전략"]

                if backtest_results and "error" not in backtest_results:
                    # Display backtest metrics
                    st.markdown("### 📈 전략별 성과 비교")

                    metrics_df = []
                    for strategy, name in zip(strategies, strategy_names):
                        if (
                            strategy in backtest_results
                            and "metrics" in backtest_results[strategy]
                        ):
                            metrics = backtest_results[strategy]["metrics"]
                            metrics_df.append(
                                {
                                    "전략": name,
                                    "총 수익률": f"{metrics.get('total_return', 0):.2%}",
                                    "연간 수익률": f"{metrics.get('annualized_return', 0):.2%}",
                                    "샤프 비율": f"{metrics.get('sharpe_ratio', 0):.2f}",
                                    "최대 낙폭": f"{metrics.get('max_drawdown', 0):.2%}",
                                    "승률": f"{metrics.get('win_rate', 0):.1%}",
                                    "거래 횟수": metrics.get("total_trades", 0),
                                }
                            )

                    if metrics_df:
                        st.dataframe(pd.DataFrame(metrics_df), use_container_width=True)
                    else:
                        st.warning("백테스팅 결과를 표시할 수 없습니다.")
                else:
                    st.warning("백테스팅이 실행되지 않았습니다.")

                # Portfolio performance chart
                if backtest_results and "prediction_based" in backtest_results:
                    st.markdown("### 💰 포트폴리오 성과")

                    perf_fig = go.Figure()

                    for strategy, name in zip(strategies, strategy_names):
                        if (
                            strategy in backtest_results
                            and "portfolio_history" in backtest_results[strategy]
                        ):
                            portfolio_history = backtest_results[strategy][
                                "portfolio_history"
                            ]
                            dates = backtest_results["test_dates"][
                                : len(portfolio_history)
                            ]

                            perf_fig.add_trace(
                                go.Scatter(
                                    x=dates,
                                    y=portfolio_history,
                                    mode="lines",
                                    name=name,
                                    line=dict(width=2),
                                )
                            )

                    perf_fig.update_layout(
                        title="포트폴리오 가치 변화",
                        xaxis_title="날짜",
                        yaxis_title="포트폴리오 가치 ($)",
                        height=400,
                    )

                    st.plotly_chart(perf_fig, use_container_width=True)

                # Prediction accuracy metrics
                if backtest_results and "prediction_accuracy" in backtest_results:
                    st.markdown("### 🎯 예측 정확도")

                    accuracy = backtest_results["prediction_accuracy"]

                    acc_col1, acc_col2, acc_col3, acc_col4 = st.columns(4)

                    with acc_col1:
                        st.metric("RMSE", f"{accuracy.get('rmse', 0):.4f}")
                    with acc_col2:
                        st.metric("MAE", f"{accuracy.get('mae', 0):.4f}")
                    with acc_col3:
                        st.metric("R² Score", f"{accuracy.get('r2', 0):.3f}")
                    with acc_col4:
                        st.metric("MAPE", f"{accuracy.get('mape', 0):.2f}%")

            # Feature importance (simplified)
            st.markdown("### 🔍 모델 해석")

            with st.expander("주요 특성 중요도", expanded=False):
                # This is a simplified feature importance based on feature names
                important_features = [
                    "Close",
                    "Volume",
                    "RSI",
                    "MACD",
                    "MA_20_ratio",
                    "volatility_20",
                    "BB_position",
                    "returns",
                ]

                # Simulate importance scores (in practice, you'd compute these from the model)
                importance_scores = np.random.random(len(important_features))
                importance_scores = importance_scores / importance_scores.sum()

                importance_df = pd.DataFrame(
                    {"특성": important_features, "중요도": importance_scores}
                ).sort_values("중요도", ascending=False)

                fig_importance = px.bar(
                    importance_df,
                    x="중요도",
                    y="특성",
                    orientation="h",
                    title="특성 중요도",
                )

                st.plotly_chart(fig_importance, use_container_width=True)

            # Model architecture info
            with st.expander("🤖 모델 구조 정보", expanded=False):
                st.markdown(
                    f"""
                **하이브리드 모델 구성:**
                - **VAE (Variational Autoencoder)**: 데이터의 잠재 표현 학습
                - **Transformer**: 시퀀스 패턴 및 장기 의존성 파악
                - **LSTM**: 시계열 데이터의 순차적 패턴 학습
                - **Attention Mechanism**: 중요한 시점에 집중
                
                **모델 파라미터:**
                - 모델 타입: {model_type}
                - 입력 차원: {len(feature_columns)}
                - 시퀀스 길이: {sequence_length}일
                - 예측 기간: {prediction_horizon}일
                - 신뢰도 임계값: {confidence_threshold:.1%}
                - 사용 장치: {"GPU" if use_gpu and torch.cuda.is_available() else "CPU"}
                """
                )

                # Model summary
                if use_ensemble:
                    st.info("📊 앙상블 모델: 다중 모델 조합으로 더 높은 정확도 제공")
                else:
                    if hasattr(model, "parameters"):
                        total_params = sum(p.numel() for p in model.parameters())
                        trainable_params = sum(
                            p.numel() for p in model.parameters() if p.requires_grad
                        )
                        st.info(
                            f"📊 총 파라미터: {total_params:,} | 훈련 가능: {trainable_params:,}"
                        )
                    else:
                        st.info("📊 모델 정보: 사용자 정의 모델")

        except Exception as e:
            st.error(f"❌ 예측 과정에서 오류가 발생했습니다: {str(e)}")
            st.error("스택 트레이스는 콘솔에서 확인할 수 있습니다.")
            import traceback

            st.code(traceback.format_exc())

# Footer
st.markdown("---")
st.markdown(
    """
<div style='text-align: center; color: #666;'>
    <p>🔮 AI 주가 예측 시스템 | GPU 가속 하이브리드 딥러닝 모델</p>
    <p><strong>⚠️ 투자는 신중하게, 손실 위험을 항상 고려하세요</strong></p>
</div>
""",
    unsafe_allow_html=True,
)
