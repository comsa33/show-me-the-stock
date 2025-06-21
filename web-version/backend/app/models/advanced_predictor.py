import logging
import warnings
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from sklearn.preprocessing import RobustScaler

warnings.filterwarnings("ignore")
logging.basicConfig(level=logging.INFO)


class ConformalPredictor:
    """Conformal prediction for uncertainty quantification"""

    def __init__(self, alpha: float = 0.1):
        self.alpha = alpha  # Miscoverage level (e.g., 0.1 for 90% prediction intervals)
        self.cal_scores = None
        self.quantile = None

    def calibrate(self, y_true: np.ndarray, y_pred: np.ndarray):
        """Calibrate the conformal predictor on validation data"""
        self.cal_scores = np.abs(y_true - y_pred)
        n = len(self.cal_scores)
        self.quantile = np.quantile(self.cal_scores, (1 - self.alpha) * (n + 1) / n)

    def predict_with_intervals(
        self, y_pred: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Generate prediction intervals"""
        if self.quantile is None:
            raise ValueError("Must calibrate before prediction")

        lower = y_pred - self.quantile
        upper = y_pred + self.quantile
        return lower, upper


class MultiScaleAttention(nn.Module):
    """Multi-scale attention mechanism for time series"""

    def __init__(self, d_model: int, num_heads: int = 8):
        super().__init__()
        self.d_model = d_model
        self.num_heads = num_heads

        # Different scale attention layers
        self.short_attn = nn.MultiheadAttention(d_model, num_heads, batch_first=True)
        self.medium_attn = nn.MultiheadAttention(d_model, num_heads, batch_first=True)
        self.long_attn = nn.MultiheadAttention(d_model, num_heads, batch_first=True)

        # Scale fusion
        self.fusion = nn.Linear(d_model * 3, d_model)
        self.layer_norm = nn.LayerNorm(d_model)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x shape: (batch, seq_len, d_model)
        seq_len = x.size(1)

        # Short-term: last 1/4 of sequence
        short_start = max(0, seq_len - seq_len // 4)
        x_short = x[:, short_start:, :]
        short_out, _ = self.short_attn(x_short, x_short, x_short)

        # Medium-term: last 1/2 of sequence
        medium_start = max(0, seq_len - seq_len // 2)
        x_medium = x[:, medium_start:, :]
        medium_out, _ = self.medium_attn(x_medium, x_medium, x_medium)

        # Long-term: full sequence
        long_out, _ = self.long_attn(x, x, x)

        # Pad shorter sequences to match long sequence length
        if short_out.size(1) < seq_len:
            padding = torch.zeros(
                short_out.size(0), seq_len - short_out.size(1), short_out.size(2)
            ).to(x.device)
            short_out = torch.cat([padding, short_out], dim=1)

        if medium_out.size(1) < seq_len:
            padding = torch.zeros(
                medium_out.size(0), seq_len - medium_out.size(1), medium_out.size(2)
            ).to(x.device)
            medium_out = torch.cat([padding, medium_out], dim=1)

        # Fuse all scales
        fused = torch.cat([short_out, medium_out, long_out], dim=-1)
        output = self.fusion(fused)
        return self.layer_norm(output + x)


class WaveNet1D(nn.Module):
    """1D WaveNet for time series feature extraction"""

    def __init__(
        self, in_channels: int, hidden_channels: int = 64, num_layers: int = 6
    ):
        super().__init__()
        self.num_layers = num_layers

        self.dilated_convs = nn.ModuleList()
        self.residual_convs = nn.ModuleList()
        self.skip_convs = nn.ModuleList()

        for i in range(num_layers):
            dilation = 2**i
            # Use smaller kernel size to avoid size mismatch
            kernel_size = min(3, 2 ** (i + 1))
            self.dilated_convs.append(
                nn.Conv1d(
                    in_channels if i == 0 else hidden_channels,
                    hidden_channels,
                    kernel_size=kernel_size,
                    dilation=dilation,
                    padding=dilation,
                )
            )
            self.residual_convs.append(nn.Conv1d(hidden_channels, hidden_channels, 1))
            self.skip_convs.append(nn.Conv1d(hidden_channels, hidden_channels, 1))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x shape: (batch, seq_len, features) -> (batch, features, seq_len)
        x = x.transpose(1, 2)

        skip_connections = []

        for i in range(self.num_layers):
            residual = x

            # Dilated convolution with padding
            x = self.dilated_convs[i](x)
            x = torch.tanh(x)

            # Skip connection
            skip = self.skip_convs[i](x)
            skip_connections.append(skip)

            # Residual connection
            x = self.residual_convs[i](x)
            if x.size(-1) == residual.size(-1):
                x = x + residual

        # Sum skip connections with proper size handling
        if skip_connections:
            min_size = min(skip.size(-1) for skip in skip_connections)
            aligned_skips = [skip[:, :, :min_size] for skip in skip_connections]
            skip_sum = sum(aligned_skips)
        else:
            skip_sum = x

        return skip_sum.transpose(1, 2)


class AdvancedStockPredictor(nn.Module):
    """Advanced ensemble model with state-of-the-art techniques"""

    def __init__(
        self,
        input_dim: int,
        sequence_length: int,
        prediction_horizon: int,
        d_model: int = 256,
        num_heads: int = 8,
        num_layers: int = 6,
        dropout: float = 0.1,
    ):

        super().__init__()
        self.input_dim = input_dim
        self.sequence_length = sequence_length
        self.prediction_horizon = prediction_horizon
        self.d_model = d_model

        # Input projection
        self.input_projection = nn.Linear(input_dim, d_model)

        # Feature extractors
        self.wavenet = WaveNet1D(d_model, d_model // 2, 6)

        # Multi-scale attention
        self.ms_attention = MultiScaleAttention(d_model, num_heads)

        # Transformer layers
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=num_heads,
            dim_feedforward=d_model * 4,
            dropout=dropout,
            batch_first=True,
            norm_first=True,
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers)

        # LSTM with skip connections
        self.lstm = nn.LSTM(
            input_size=d_model,
            hidden_size=d_model,
            num_layers=2,
            dropout=dropout,
            batch_first=True,
            bidirectional=True,
        )

        # Prediction heads
        self.mean_head = nn.Sequential(
            nn.Linear(d_model * 2, d_model),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(d_model, d_model // 2),
            nn.ReLU(),
            nn.Linear(d_model // 2, prediction_horizon),
        )

        self.variance_head = nn.Sequential(
            nn.Linear(d_model * 2, d_model),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(d_model, d_model // 2),
            nn.ReLU(),
            nn.Linear(d_model // 2, prediction_horizon),
            nn.Softplus(),  # Ensure positive variance
        )

        # Quantile heads for robust uncertainty
        self.quantile_heads = nn.ModuleDict(
            {
                "q10": nn.Linear(d_model * 2, prediction_horizon),
                "q25": nn.Linear(d_model * 2, prediction_horizon),
                "q75": nn.Linear(d_model * 2, prediction_horizon),
                "q90": nn.Linear(d_model * 2, prediction_horizon),
            }
        )

    def forward(self, x: torch.Tensor) -> Dict[str, torch.Tensor]:
        batch_size = x.size(0)

        # Input projection
        x = self.input_projection(x)

        # WaveNet feature extraction (skip for now to avoid dimension issues)
        # wavenet_features = self.wavenet(x)

        # Multi-scale attention (use original features only for stability)
        attended = self.ms_attention(x)

        # Transformer encoding
        transformer_out = self.transformer(attended)

        # LSTM processing
        lstm_out, _ = self.lstm(transformer_out)

        # Use last hidden state
        final_hidden = lstm_out[:, -1, :]

        # Predictions
        mean_pred = self.mean_head(final_hidden)
        variance_pred = self.variance_head(final_hidden)

        quantiles = {}
        for name, head in self.quantile_heads.items():
            quantiles[name] = head(final_hidden)

        return {
            "mean": mean_pred,
            "variance": variance_pred,
            "quantiles": quantiles,
            "features": final_hidden,
        }


class EnsemblePredictor:
    """Ensemble of multiple prediction models"""

    def __init__(self, models: List[nn.Module], weights: Optional[List[float]] = None):
        self.models = models
        self.weights = weights or [1.0 / len(models)] * len(models)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        for model in self.models:
            model.to(self.device)

    def predict(self, x: torch.Tensor) -> Dict[str, torch.Tensor]:
        predictions = []
        variances = []

        # Ensure input tensor is on the correct device
        x = x.to(self.device)

        with torch.no_grad():
            for model, weight in zip(self.models, self.weights):
                model.eval()
                # Ensure model is on the same device as input
                model = model.to(self.device)
                output = model(x)
                predictions.append(output["mean"] * weight)
                if "variance" in output:
                    variances.append(output["variance"] * weight)

        ensemble_mean = torch.stack(predictions).sum(dim=0)
        ensemble_variance = torch.stack(variances).sum(dim=0) if variances else None

        # Calculate ensemble uncertainty (variance of predictions + average variance)
        pred_variance = torch.stack(
            [pred / weight for pred, weight in zip(predictions, self.weights)]
        ).var(dim=0)
        if ensemble_variance is not None:
            total_variance = pred_variance + ensemble_variance
        else:
            total_variance = pred_variance

        return {
            "mean": ensemble_mean,
            "variance": total_variance,
            "uncertainty": torch.sqrt(total_variance),
        }


class AdvancedDataProcessor:
    """Advanced data preprocessing with feature engineering"""

    def __init__(self):
        self.scalers = {
            "price": RobustScaler(),
            "volume": RobustScaler(),
            "returns": RobustScaler(),
            "technical": RobustScaler(),
        }
        self.target_scaler = RobustScaler()

    def engineer_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Advanced feature engineering"""
        data = df.copy()

        # Basic returns and log returns
        data["returns"] = data["Close"].pct_change()
        data["log_returns"] = np.log(data["Close"] / data["Close"].shift(1))
        data["returns_volatility"] = data["returns"].rolling(20).std()

        # Price momentum features
        for window in [5, 10, 20, 50]:
            data[f"price_momentum_{window}"] = (
                data["Close"] / data["Close"].shift(window) - 1
            )
            data[f"volume_momentum_{window}"] = (
                data["Volume"] / data["Volume"].rolling(window).mean()
            )

        # Advanced technical indicators
        # Commodity Channel Index
        typical_price = (data["High"] + data["Low"] + data["Close"]) / 3
        data["CCI"] = (typical_price - typical_price.rolling(20).mean()) / (
            0.015 * typical_price.rolling(20).std()
        )

        # Williams %R
        data["Williams_R"] = (
            (data["High"].rolling(14).max() - data["Close"])
            / (data["High"].rolling(14).max() - data["Low"].rolling(14).min())
            * -100
        )

        # Stochastic Oscillator
        data["Stoch_K"] = (
            (data["Close"] - data["Low"].rolling(14).min())
            / (data["High"].rolling(14).max() - data["Low"].rolling(14).min())
            * 100
        )
        data["Stoch_D"] = data["Stoch_K"].rolling(3).mean()

        # MACD with different periods
        for fast, slow in [(8, 21), (12, 26), (19, 39)]:
            ema_fast = data["Close"].ewm(span=fast).mean()
            ema_slow = data["Close"].ewm(span=slow).mean()
            data[f"MACD_{fast}_{slow}"] = ema_fast - ema_slow
            data[f"MACD_signal_{fast}_{slow}"] = (
                data[f"MACD_{fast}_{slow}"].ewm(span=9).mean()
            )

        # Ichimoku Cloud components
        high_9 = data["High"].rolling(9).max()
        low_9 = data["Low"].rolling(9).min()
        data["Ichimoku_conversion"] = (high_9 + low_9) / 2

        high_26 = data["High"].rolling(26).max()
        low_26 = data["Low"].rolling(26).min()
        data["Ichimoku_base"] = (high_26 + low_26) / 2

        # Volume-based indicators
        data["OBV"] = (data["Volume"] * np.sign(data["Close"].diff())).cumsum()
        data["Volume_SMA"] = data["Volume"].rolling(20).mean()
        data["Volume_ratio"] = data["Volume"] / data["Volume_SMA"]

        # Volatility indicators
        data["ATR"] = self._calculate_atr(data)
        data["Volatility_ratio"] = data["ATR"] / data["Close"]

        # Market structure indicators
        data["Higher_high"] = (data["High"] > data["High"].shift(1)).astype(int)
        data["Lower_low"] = (data["Low"] < data["Low"].shift(1)).astype(int)

        # Fractal indicators
        data["Resistance_level"] = data["High"].rolling(10, center=True).max()
        data["Support_level"] = data["Low"].rolling(10, center=True).min()
        data["Distance_to_resistance"] = (
            data["Resistance_level"] - data["Close"]
        ) / data["Close"]
        data["Distance_to_support"] = (data["Close"] - data["Support_level"]) / data[
            "Close"
        ]

        return data

    def _calculate_atr(self, data: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate Average True Range"""
        high_low = data["High"] - data["Low"]
        high_close = np.abs(data["High"] - data["Close"].shift())
        low_close = np.abs(data["Low"] - data["Close"].shift())

        true_range = np.maximum(high_low, np.maximum(high_close, low_close))
        return true_range.rolling(period).mean()

    def prepare_advanced_data(
        self, df: pd.DataFrame, sequence_length: int = 60, prediction_horizon: int = 7
    ) -> Tuple[np.ndarray, np.ndarray, List[str]]:
        """Prepare data with advanced preprocessing"""

        # Feature engineering
        data = self.engineer_features(df)

        # Select features
        price_features = ["Open", "High", "Low", "Close"]
        volume_features = ["Volume", "OBV", "Volume_ratio"]
        return_features = ["returns", "log_returns", "returns_volatility"]
        technical_features = [
            col
            for col in data.columns
            if any(
                indicator in col
                for indicator in [
                    "momentum",
                    "CCI",
                    "Williams",
                    "Stoch",
                    "MACD",
                    "Ichimoku",
                    "ATR",
                    "Volatility_ratio",
                ]
            )
        ]

        # Market structure features
        structure_features = [
            "Higher_high",
            "Lower_low",
            "Distance_to_resistance",
            "Distance_to_support",
        ]

        all_features = (
            price_features
            + volume_features
            + return_features
            + technical_features
            + structure_features
        )

        # Remove features with too many NaN values
        feature_data = data[all_features].dropna()

        if len(feature_data) < sequence_length + prediction_horizon + 50:
            raise ValueError(
                f"Insufficient data after feature engineering. Need at least {sequence_length + prediction_horizon + 50} rows"
            )

        # Scale different feature groups separately
        price_data = self.scalers["price"].fit_transform(feature_data[price_features])
        volume_data = self.scalers["volume"].fit_transform(
            feature_data[volume_features]
        )
        return_data = self.scalers["returns"].fit_transform(
            feature_data[return_features]
        )

        if technical_features:
            technical_data = self.scalers["technical"].fit_transform(
                feature_data[technical_features + structure_features]
            )
            scaled_data = np.concatenate(
                [price_data, volume_data, return_data, technical_data], axis=1
            )
        else:
            scaled_data = np.concatenate([price_data, volume_data, return_data], axis=1)

        # Create sequences
        X, y = [], []
        for i in range(len(scaled_data) - sequence_length - prediction_horizon + 1):
            X.append(scaled_data[i : (i + sequence_length)])
            # Predict close price (index 3 in price_features)
            close_prices = feature_data.iloc[
                i + sequence_length : i + sequence_length + prediction_horizon
            ]["Close"].values
            y.append(close_prices)

        return np.array(X), np.array(y), all_features

    def inverse_transform_target(
        self, predictions: np.ndarray, feature_data: pd.DataFrame
    ) -> np.ndarray:
        """Inverse transform predictions back to original scale"""
        # Use actual close prices for fitting the target scaler
        close_prices = feature_data["Close"].values
        if hasattr(close_prices, "reshape"):
            close_prices = close_prices.reshape(-1, 1)
        else:
            close_prices = np.array(close_prices).reshape(-1, 1)

        self.target_scaler.fit(close_prices)

        # Reshape predictions for inverse transform
        pred_shape = predictions.shape
        predictions_reshaped = predictions.reshape(-1, 1)

        # Inverse transform
        inversed = self.target_scaler.inverse_transform(predictions_reshaped)
        return inversed.reshape(pred_shape)


def create_advanced_ensemble(
    input_dim: int,
    sequence_length: int = 60,
    prediction_horizon: int = 7,
    hf_token: str = None,
) -> EnsemblePredictor:
    """Create an advanced ensemble model"""

    models = []

    # Model 1: Large advanced model
    model1 = AdvancedStockPredictor(
        input_dim=input_dim,
        sequence_length=sequence_length,
        prediction_horizon=prediction_horizon,
        d_model=256,
        num_heads=8,
        num_layers=6,
    )
    models.append(model1)

    # Model 2: Smaller but deeper model
    model2 = AdvancedStockPredictor(
        input_dim=input_dim,
        sequence_length=sequence_length,
        prediction_horizon=prediction_horizon,
        d_model=128,
        num_heads=4,
        num_layers=8,
    )
    models.append(model2)

    # Model 3: Wide model with more attention heads
    model3 = AdvancedStockPredictor(
        input_dim=input_dim,
        sequence_length=sequence_length,
        prediction_horizon=prediction_horizon,
        d_model=192,
        num_heads=12,
        num_layers=4,
    )
    models.append(model3)

    # Create ensemble with equal weights initially
    ensemble = EnsemblePredictor(models)

    logging.info(f"Created ensemble with {len(models)} models")
    return ensemble


def calculate_advanced_confidence(
    predictions: Dict[str, torch.Tensor], actual_prices: Optional[np.ndarray] = None
) -> np.ndarray:
    """Calculate sophisticated confidence scores"""

    mean_pred = predictions["mean"].cpu().numpy()
    uncertainty = predictions["uncertainty"].cpu().numpy()

    # Normalize uncertainty to confidence (0-1 scale)
    # Lower uncertainty = higher confidence
    max_uncertainty = np.percentile(uncertainty, 95)
    normalized_uncertainty = np.clip(uncertainty / max_uncertainty, 0, 1)

    # Base confidence from uncertainty
    base_confidence = 1 - normalized_uncertainty

    # Additional confidence factors
    confidence_factors = []

    # Factor 1: Prediction consistency (lower variance across ensemble)
    if "variance" in predictions:
        variance = predictions["variance"].cpu().numpy()
        consistency_factor = 1 / (1 + variance)
        confidence_factors.append(consistency_factor)

    # Factor 2: Quantile spread (tighter quantiles = higher confidence)
    if "quantiles" in predictions and isinstance(predictions["quantiles"], dict):
        q10 = predictions["quantiles"]["q10"].cpu().numpy()
        q90 = predictions["quantiles"]["q90"].cpu().numpy()
        quantile_spread = np.abs(q90 - q10)
        spread_factor = 1 / (1 + quantile_spread)
        confidence_factors.append(spread_factor)

    # Combine all factors
    if confidence_factors:
        combined_factor = np.mean(confidence_factors, axis=0)
        final_confidence = base_confidence * combined_factor
    else:
        final_confidence = base_confidence

    # Ensure confidence is in [0.1, 0.95] range to avoid overconfidence
    final_confidence = np.clip(final_confidence, 0.1, 0.95)

    return final_confidence
