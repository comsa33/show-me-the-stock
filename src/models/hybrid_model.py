import math
import warnings
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from sklearn.preprocessing import MinMaxScaler, StandardScaler

warnings.filterwarnings("ignore")


class PositionalEncoding(nn.Module):
    def __init__(self, d_model: int, dropout: float = 0.1, max_len: int = 5000):
        super().__init__()
        self.dropout = nn.Dropout(p=dropout)

        position = torch.arange(max_len).unsqueeze(1)
        div_term = torch.exp(
            torch.arange(0, d_model, 2) * (-math.log(10000.0) / d_model)
        )
        pe = torch.zeros(max_len, 1, d_model)
        pe[:, 0, 0::2] = torch.sin(position * div_term)
        pe[:, 0, 1::2] = torch.cos(position * div_term)
        self.register_buffer("pe", pe)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = x + self.pe[: x.size(0)]
        return self.dropout(x)


class VAEEncoder(nn.Module):
    def __init__(self, input_dim: int, hidden_dim: int, latent_dim: int):
        super().__init__()
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.latent_dim = latent_dim

        self.encoder = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(0.2),
        )

        self.mu_layer = nn.Linear(hidden_dim // 2, latent_dim)
        self.logvar_layer = nn.Linear(hidden_dim // 2, latent_dim)

    def forward(
        self, x: torch.Tensor
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        encoded = self.encoder(x)
        mu = self.mu_layer(encoded)
        logvar = self.logvar_layer(encoded)

        # Reparameterization trick
        std = torch.exp(0.5 * logvar)
        eps = torch.randn_like(std)
        z = mu + eps * std

        return z, mu, logvar


class VAEDecoder(nn.Module):
    def __init__(self, latent_dim: int, hidden_dim: int, output_dim: int):
        super().__init__()
        self.decoder = nn.Sequential(
            nn.Linear(latent_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden_dim // 2, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden_dim, output_dim),
        )

    def forward(self, z: torch.Tensor) -> torch.Tensor:
        return self.decoder(z)


class TransformerPredictor(nn.Module):
    def __init__(
        self,
        input_dim: int,
        d_model: int,
        nhead: int,
        num_layers: int,
        dim_feedforward: int,
        dropout: float = 0.1,
    ):
        super().__init__()
        self.d_model = d_model
        self.input_projection = nn.Linear(input_dim, d_model)
        self.pos_encoder = PositionalEncoding(d_model, dropout)

        encoder_layers = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=nhead,
            dim_feedforward=dim_feedforward,
            dropout=dropout,
            batch_first=True,
        )
        self.transformer_encoder = nn.TransformerEncoder(encoder_layers, num_layers)

    def forward(
        self, src: torch.Tensor, src_mask: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        src = self.input_projection(src) * math.sqrt(self.d_model)
        src = src.permute(1, 0, 2)  # (seq_len, batch, d_model)
        src = self.pos_encoder(src)
        src = src.permute(1, 0, 2)  # (batch, seq_len, d_model)

        output = self.transformer_encoder(src, src_mask)
        return output


class LSTMPredictor(nn.Module):
    def __init__(
        self, input_dim: int, hidden_dim: int, num_layers: int, dropout: float = 0.2
    ):
        super().__init__()
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers

        self.lstm = nn.LSTM(
            input_size=input_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            dropout=dropout if num_layers > 1 else 0,
            batch_first=True,
        )

    def forward(
        self, x: torch.Tensor
    ) -> Tuple[torch.Tensor, Tuple[torch.Tensor, torch.Tensor]]:
        lstm_out, (hidden, cell) = self.lstm(x)
        return lstm_out, (hidden, cell)


class HybridStockPredictor(nn.Module):
    def __init__(
        self,
        input_dim: int,
        sequence_length: int,
        prediction_horizon: int,
        vae_hidden_dim: int = 128,
        vae_latent_dim: int = 32,
        transformer_d_model: int = 128,
        transformer_nhead: int = 8,
        transformer_layers: int = 4,
        lstm_hidden_dim: int = 128,
        lstm_layers: int = 2,
        dropout: float = 0.2,
    ):

        super().__init__()
        self.input_dim = input_dim
        self.sequence_length = sequence_length
        self.prediction_horizon = prediction_horizon
        self.vae_latent_dim = vae_latent_dim

        # VAE Components
        self.vae_encoder = VAEEncoder(input_dim, vae_hidden_dim, vae_latent_dim)
        self.vae_decoder = VAEDecoder(vae_latent_dim, vae_hidden_dim, input_dim)

        # Transformer Component
        self.transformer = TransformerPredictor(
            input_dim + vae_latent_dim,  # Original features + VAE latent features
            transformer_d_model,
            transformer_nhead,
            transformer_layers,
            transformer_d_model * 4,
            dropout,
        )

        # LSTM Component
        self.lstm = LSTMPredictor(
            transformer_d_model, lstm_hidden_dim, lstm_layers, dropout
        )

        # Output layers
        self.output_projection = nn.Sequential(
            nn.Linear(lstm_hidden_dim, lstm_hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(lstm_hidden_dim // 2, prediction_horizon),
            nn.Tanh(),  # For bounded output
        )

        # Attention mechanism for ensemble
        self.attention = nn.MultiheadAttention(
            embed_dim=lstm_hidden_dim, num_heads=4, batch_first=True
        )

    def forward(self, x: torch.Tensor) -> Dict[str, torch.Tensor]:
        batch_size, seq_len, features = x.shape

        # Reshape for VAE (process each time step)
        x_reshaped = x.view(-1, features)  # (batch * seq_len, features)

        # VAE Encoding
        z, mu, logvar = self.vae_encoder(x_reshaped)

        # VAE Decoding (for reconstruction loss)
        x_reconstructed = self.vae_decoder(z)

        # Reshape back to sequence format
        z = z.view(batch_size, seq_len, self.vae_latent_dim)
        x_reconstructed = x_reconstructed.view(batch_size, seq_len, features)

        # Combine original features with VAE latent features
        enhanced_features = torch.cat([x, z], dim=-1)

        # Transformer processing
        transformer_output = self.transformer(enhanced_features)

        # LSTM processing
        lstm_output, _ = self.lstm(transformer_output)

        # Use the last hidden state for prediction
        final_hidden = lstm_output[:, -1, :]  # (batch, hidden_dim)

        # Apply attention mechanism
        attended_output, _ = self.attention(
            final_hidden.unsqueeze(1), lstm_output, lstm_output  # query  # key  # value
        )

        # Final prediction
        predictions = self.output_projection(attended_output.squeeze(1))

        return {
            "predictions": predictions,
            "reconstructed": x_reconstructed,
            "mu": mu.view(batch_size, seq_len, self.vae_latent_dim),
            "logvar": logvar.view(batch_size, seq_len, self.vae_latent_dim),
            "latent_features": z,
        }

    def vae_loss(
        self,
        x: torch.Tensor,
        reconstructed: torch.Tensor,
        mu: torch.Tensor,
        logvar: torch.Tensor,
    ) -> torch.Tensor:
        """VAE loss: reconstruction + KL divergence"""
        # Reconstruction loss
        recon_loss = nn.MSELoss()(reconstructed, x)

        # KL divergence loss
        kl_loss = -0.5 * torch.sum(1 + logvar - mu.pow(2) - logvar.exp())
        kl_loss = kl_loss / (
            x.size(0) * x.size(1)
        )  # Normalize by batch and sequence length

        return recon_loss + 0.1 * kl_loss  # Weight KL loss


class StockDataProcessor:
    def __init__(self):
        self.price_scaler = MinMaxScaler()
        self.volume_scaler = StandardScaler()
        self.feature_scaler = StandardScaler()
        self.target_scaler = MinMaxScaler()

    def add_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add technical indicators to the dataframe"""
        data = df.copy()

        # Price-based indicators
        data["returns"] = data["Close"].pct_change()
        data["log_returns"] = np.log(data["Close"] / data["Close"].shift(1))

        # Moving averages
        for window in [5, 10, 20, 50]:
            data[f"MA_{window}"] = data["Close"].rolling(window=window).mean()
            data[f"MA_{window}_ratio"] = data["Close"] / data[f"MA_{window}"]

        # Volatility
        data["volatility_5"] = data["returns"].rolling(window=5).std()
        data["volatility_20"] = data["returns"].rolling(window=20).std()

        # RSI
        delta = data["Close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        data["RSI"] = 100 - (100 / (1 + rs))

        # Bollinger Bands
        bb_window = 20
        data["BB_middle"] = data["Close"].rolling(window=bb_window).mean()
        bb_std = data["Close"].rolling(window=bb_window).std()
        data["BB_upper"] = data["BB_middle"] + (bb_std * 2)
        data["BB_lower"] = data["BB_middle"] - (bb_std * 2)
        data["BB_position"] = (data["Close"] - data["BB_lower"]) / (
            data["BB_upper"] - data["BB_lower"]
        )

        # MACD
        ema12 = data["Close"].ewm(span=12).mean()
        ema26 = data["Close"].ewm(span=26).mean()
        data["MACD"] = ema12 - ema26
        data["MACD_signal"] = data["MACD"].ewm(span=9).mean()
        data["MACD_histogram"] = data["MACD"] - data["MACD_signal"]

        # Volume indicators
        data["volume_ma"] = data["Volume"].rolling(window=20).mean()
        data["volume_ratio"] = data["Volume"] / data["volume_ma"]

        # Price position indicators
        data["high_low_ratio"] = data["High"] / data["Low"]
        data["close_position"] = (data["Close"] - data["Low"]) / (
            data["High"] - data["Low"]
        )

        return data

    def prepare_data(
        self, df: pd.DataFrame, sequence_length: int = 60, prediction_horizon: int = 30
    ) -> Tuple[np.ndarray, np.ndarray, List[str]]:
        """Prepare data for training"""
        # Add technical indicators
        data = self.add_technical_indicators(df)

        # Select features
        feature_columns = [
            "Open",
            "High",
            "Low",
            "Close",
            "Volume",
            "returns",
            "log_returns",
            "MA_5_ratio",
            "MA_10_ratio",
            "MA_20_ratio",
            "MA_50_ratio",
            "volatility_5",
            "volatility_20",
            "RSI",
            "BB_position",
            "MACD",
            "MACD_signal",
            "MACD_histogram",
            "volume_ratio",
            "high_low_ratio",
            "close_position",
        ]

        # Remove rows with NaN values
        data = data[feature_columns].dropna()

        if len(data) < sequence_length + prediction_horizon:
            raise ValueError(
                f"Not enough data. Need at least {sequence_length + prediction_horizon} rows, got {len(data)}"
            )

        # Scale features
        scaled_data = self.feature_scaler.fit_transform(data)

        # Create sequences
        X, y = [], []
        for i in range(len(scaled_data) - sequence_length - prediction_horizon + 1):
            X.append(scaled_data[i : (i + sequence_length)])
            # Predict the 'Close' price (index 3) for next 'prediction_horizon' days
            close_idx = feature_columns.index("Close")
            y.append(
                scaled_data[
                    (i + sequence_length) : (i + sequence_length + prediction_horizon),
                    close_idx,
                ]
            )

        return np.array(X), np.array(y), feature_columns

    def inverse_transform_predictions(
        self, predictions: np.ndarray, feature_idx: int = 3
    ) -> np.ndarray:
        """Inverse transform predictions back to original scale"""
        # Handle case where scaler doesn't have feature_names_in_ attribute
        if hasattr(self.feature_scaler, "feature_names_in_"):
            n_features = len(self.feature_scaler.feature_names_in_)
        else:
            n_features = self.feature_scaler.n_features_in_

        # Create dummy array with same number of features
        dummy = np.zeros((predictions.shape[0], n_features))
        dummy[:, feature_idx] = predictions.flatten()

        # Inverse transform and extract the price column
        inversed = self.feature_scaler.inverse_transform(dummy)
        return inversed[:, feature_idx].reshape(predictions.shape)


def create_hybrid_model(
    input_dim: int, sequence_length: int = 60, prediction_horizon: int = 30
) -> HybridStockPredictor:
    """Create and return a hybrid model instance"""
    return HybridStockPredictor(
        input_dim=input_dim,
        sequence_length=sequence_length,
        prediction_horizon=prediction_horizon,
        vae_hidden_dim=128,
        vae_latent_dim=32,
        transformer_d_model=128,
        transformer_nhead=8,
        transformer_layers=4,
        lstm_hidden_dim=128,
        lstm_layers=2,
        dropout=0.2,
    )
