import logging
from typing import Dict

import numpy as np
import torch
import torch.nn as nn


class SimpleStockPredictor(nn.Module):
    """Simplified but effective stock prediction model"""

    def __init__(
        self,
        input_dim: int,
        sequence_length: int,
        prediction_horizon: int,
        hidden_dim: int = 128,
        num_layers: int = 2,
        dropout: float = 0.2,
    ):
        super().__init__()
        self.input_dim = input_dim
        self.sequence_length = sequence_length
        self.prediction_horizon = prediction_horizon
        self.hidden_dim = hidden_dim

        # Input normalization
        self.input_norm = nn.LayerNorm(input_dim)

        # LSTM backbone
        self.lstm = nn.LSTM(
            input_size=input_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            dropout=dropout if num_layers > 1 else 0,
            batch_first=True,
            bidirectional=True,
        )

        # Attention mechanism
        self.attention = nn.MultiheadAttention(
            embed_dim=hidden_dim * 2,  # Bidirectional
            num_heads=4,
            dropout=dropout,
            batch_first=True,
        )

        # Prediction head
        self.predictor = nn.Sequential(
            nn.Linear(hidden_dim * 2, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim // 2, prediction_horizon),
        )

        # Uncertainty estimation
        self.uncertainty_head = nn.Sequential(
            nn.Linear(hidden_dim * 2, hidden_dim // 2),
            nn.ReLU(),
            nn.Linear(hidden_dim // 2, prediction_horizon),
            nn.Softplus(),
        )

    def forward(self, x: torch.Tensor) -> Dict[str, torch.Tensor]:
        # Input normalization
        x = self.input_norm(x)

        # LSTM processing
        lstm_out, _ = self.lstm(x)

        # Self-attention
        attended_out, _ = self.attention(lstm_out, lstm_out, lstm_out)

        # Use last hidden state
        final_hidden = attended_out[:, -1, :]

        # Predictions
        mean_pred = self.predictor(final_hidden)
        uncertainty = self.uncertainty_head(final_hidden)

        return {
            "mean": mean_pred,
            "predictions": mean_pred,  # For compatibility
            "variance": uncertainty,
            "uncertainty": torch.sqrt(uncertainty),
        }


class SimpleEnsemble:
    """Simple but effective ensemble of models"""

    def __init__(
        self,
        input_dim: int,
        sequence_length: int = 60,
        prediction_horizon: int = 7,
        num_models: int = 3,
    ):
        self.input_dim = input_dim
        self.sequence_length = sequence_length
        self.prediction_horizon = prediction_horizon
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        # Create diverse models
        self.models = []
        configs = [
            {"hidden_dim": 128, "num_layers": 2, "dropout": 0.1},
            {"hidden_dim": 96, "num_layers": 3, "dropout": 0.2},
            {"hidden_dim": 160, "num_layers": 2, "dropout": 0.15},
        ]

        for i, config in enumerate(configs[:num_models]):
            model = SimpleStockPredictor(
                input_dim=input_dim,
                sequence_length=sequence_length,
                prediction_horizon=prediction_horizon,
                **config,
            )
            model.to(self.device)
            self.models.append(model)

        self.weights = [1.0 / len(self.models)] * len(self.models)

    def predict(self, x: torch.Tensor) -> Dict[str, torch.Tensor]:
        """Generate ensemble predictions"""
        x = x.to(self.device)

        predictions = []
        uncertainties = []

        with torch.no_grad():
            for model, weight in zip(self.models, self.weights):
                model.eval()
                output = model(x)
                predictions.append(output["mean"] * weight)
                uncertainties.append(output["uncertainty"] * weight)

        ensemble_mean = torch.stack(predictions).sum(dim=0)
        ensemble_uncertainty = torch.stack(uncertainties).sum(dim=0)

        # Add epistemic uncertainty from model disagreement
        individual_preds = torch.stack(
            [pred / weight for pred, weight in zip(predictions, self.weights)]
        )
        epistemic_uncertainty = individual_preds.std(dim=0)
        total_uncertainty = torch.sqrt(
            ensemble_uncertainty**2 + epistemic_uncertainty**2
        )

        return {
            "mean": ensemble_mean,
            "predictions": ensemble_mean,  # For compatibility
            "variance": total_uncertainty**2,
            "uncertainty": total_uncertainty,
        }

    def train_ensemble(
        self,
        train_X: torch.Tensor,
        train_y: torch.Tensor,
        epochs: int = 50,
        lr: float = 0.001,
    ):
        """Train all models in the ensemble"""
        train_X = train_X.to(self.device)
        train_y = train_y.to(self.device)

        for i, model in enumerate(self.models):
            model.train()
            optimizer = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=1e-5)
            criterion = nn.MSELoss()

            for epoch in range(epochs):
                optimizer.zero_grad()
                output = model(train_X)

                # Main prediction loss
                pred_loss = criterion(output["mean"], train_y)

                # Uncertainty regularization
                uncertainty_loss = -torch.log(output["uncertainty"]).mean()

                total_loss = pred_loss + 0.1 * uncertainty_loss
                total_loss.backward()

                # Gradient clipping
                torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                optimizer.step()

        logging.info(f"Trained ensemble with {len(self.models)} models")


def create_simple_ensemble(
    input_dim: int, sequence_length: int = 60, prediction_horizon: int = 7
) -> SimpleEnsemble:
    """Create a simple but effective ensemble model"""
    return SimpleEnsemble(
        input_dim=input_dim,
        sequence_length=sequence_length,
        prediction_horizon=prediction_horizon,
        num_models=3,
    )


def calculate_simple_confidence(predictions: Dict[str, torch.Tensor]) -> np.ndarray:
    """Calculate confidence scores for simple ensemble"""
    uncertainty = predictions["uncertainty"].cpu().numpy()

    # Convert uncertainty to confidence (inverse relationship)
    # Lower uncertainty = higher confidence
    max_uncertainty = np.percentile(uncertainty, 95)
    normalized_uncertainty = np.clip(uncertainty / max_uncertainty, 0, 1)
    confidence = 1 - normalized_uncertainty

    # Ensure confidence is in reasonable range
    confidence = np.clip(confidence, 0.1, 0.9)

    return confidence
