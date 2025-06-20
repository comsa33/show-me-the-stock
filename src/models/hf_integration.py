import logging
import warnings
from typing import Dict, List

import torch
import torch.nn as nn
from huggingface_hub import list_models, login
from transformers import AutoConfig, AutoModel

warnings.filterwarnings("ignore")
logging.basicConfig(level=logging.INFO)


class HuggingFaceTimeSeriesModel(nn.Module):
    """Wrapper for Hugging Face time series models"""

    def __init__(
        self, model_name: str, input_dim: int, prediction_horizon: int, hf_token: str
    ):
        super().__init__()
        self.model_name = model_name
        self.input_dim = input_dim
        self.prediction_horizon = prediction_horizon

        # Login to Hugging Face
        if hf_token:
            login(token=hf_token)

        try:
            # Load pre-trained model and config
            self.config = AutoConfig.from_pretrained(model_name, trust_remote_code=True)
            self.backbone = AutoModel.from_pretrained(
                model_name, trust_remote_code=True
            )

            # Get hidden size from model config
            if hasattr(self.config, "hidden_size"):
                hidden_size = self.config.hidden_size
            elif hasattr(self.config, "d_model"):
                hidden_size = self.config.d_model
            elif hasattr(self.config, "embed_dim"):
                hidden_size = self.config.embed_dim
            else:
                hidden_size = 768  # Default

            # Adaptation layers
            self.input_adapter = nn.Linear(input_dim, hidden_size)
            self.output_adapter = nn.Sequential(
                nn.Linear(hidden_size, hidden_size // 2),
                nn.ReLU(),
                nn.Dropout(0.1),
                nn.Linear(hidden_size // 2, prediction_horizon),
            )

            # Uncertainty estimation
            self.uncertainty_head = nn.Sequential(
                nn.Linear(hidden_size, hidden_size // 4),
                nn.ReLU(),
                nn.Linear(hidden_size // 4, prediction_horizon),
                nn.Softplus(),
            )

            logging.info(f"Successfully loaded {model_name}")

        except Exception as e:
            logging.warning(f"Failed to load {model_name}: {e}")
            # Fallback to a simple model
            self.backbone = None
            self.simple_model = nn.LSTM(input_dim, 256, 2, batch_first=True)
            self.output_adapter = nn.Linear(256, prediction_horizon)
            self.uncertainty_head = nn.Sequential(
                nn.Linear(256, prediction_horizon), nn.Softplus()
            )

    def forward(self, x: torch.Tensor) -> Dict[str, torch.Tensor]:
        # Ensure input is on the same device as the model
        device = next(self.parameters()).device
        x = x.to(device)

        if self.backbone is not None:
            # Use pre-trained model
            try:
                # Adapt input to model's expected format
                x_adapted = self.input_adapter(x)

                # Forward through backbone
                if hasattr(self.backbone, "encoder"):
                    # Transformer-like models
                    outputs = self.backbone.encoder(x_adapted)
                    if hasattr(outputs, "last_hidden_state"):
                        hidden = outputs.last_hidden_state[:, -1, :]
                    else:
                        hidden = outputs[:, -1, :]
                else:
                    # Other architectures
                    outputs = self.backbone(x_adapted)
                    if isinstance(outputs, tuple):
                        hidden = outputs[0][:, -1, :]
                    else:
                        hidden = outputs[:, -1, :]

                # Generate predictions
                mean_pred = self.output_adapter(hidden)
                uncertainty = self.uncertainty_head(hidden)

            except Exception as e:
                logging.warning(f"Error in backbone forward pass: {e}")
                # Fallback to simple processing
                hidden = x.mean(dim=1)
                mean_pred = self.output_adapter(hidden)
                uncertainty = torch.ones_like(mean_pred).to(device) * 0.1
        else:
            # Use simple LSTM fallback
            lstm_out, _ = self.simple_model(x)
            hidden = lstm_out[:, -1, :]
            mean_pred = self.output_adapter(hidden)
            uncertainty = self.uncertainty_head(hidden)

        return {
            "mean": mean_pred,
            "variance": uncertainty,
            "uncertainty": torch.sqrt(uncertainty),
        }


class ChronosWrapper(nn.Module):
    """Wrapper for Amazon Chronos time series foundation model"""

    def __init__(self, input_dim: int, prediction_horizon: int, hf_token: str):
        super().__init__()
        self.model_name = "amazon/chronos-t5-small"
        self.input_dim = input_dim
        self.prediction_horizon = prediction_horizon

        try:
            from chronos import ChronosPipeline

            if hf_token:
                login(token=hf_token)

            # Load Chronos pipeline
            self.pipeline = ChronosPipeline.from_pretrained(
                self.model_name,
                device_map="cpu",  # Use CPU to avoid device conflicts
                torch_dtype=torch.float32,
            )
            self.has_chronos = True
            logging.info("Successfully loaded Chronos model")

        except Exception as e:
            logging.warning(f"Failed to load Chronos: {e}")
            self.has_chronos = False

        # Always initialize fallback model
        self.fallback_model = nn.Sequential(
            nn.Linear(input_dim, 256),
            nn.ReLU(),
            nn.LSTM(256, 128, 2, batch_first=True),
        )
        self.output_head = nn.Linear(128, prediction_horizon)

    def forward(self, x: torch.Tensor) -> Dict[str, torch.Tensor]:
        # Ensure input is on the same device as the model
        device = next(self.parameters()).device
        x = x.to(device)

        if self.has_chronos:
            try:
                # Chronos expects time series data in specific format
                batch_size = x.size(0)
                predictions = []
                uncertainties = []

                for i in range(batch_size):
                    # Use Close price (assuming it's the last feature)
                    time_series = x[i, :, -1].cpu().numpy()

                    # Generate forecast
                    forecast = self.pipeline.predict(
                        context=torch.tensor(time_series).unsqueeze(0),
                        prediction_length=self.prediction_horizon,
                        num_samples=20,  # Generate multiple samples for uncertainty
                    )

                    # Calculate mean and std from samples
                    forecast_mean = forecast.mean(dim=0)
                    forecast_std = forecast.std(dim=0)

                    predictions.append(forecast_mean)
                    uncertainties.append(forecast_std)

                mean_pred = torch.stack(predictions).to(device)
                uncertainty = torch.stack(uncertainties).to(device)

                return {
                    "mean": mean_pred,
                    "variance": uncertainty**2,
                    "uncertainty": uncertainty,
                }

            except Exception as e:
                logging.warning(f"Error in Chronos prediction: {e}")
                # Fall through to fallback

        # Fallback model
        lstm_out, _ = self.fallback_model(x)
        hidden = lstm_out[0][:, -1, :]  # Get last hidden state
        mean_pred = self.output_head(hidden)
        uncertainty = torch.ones_like(mean_pred).to(device) * 0.1

        return {
            "mean": mean_pred,
            "variance": uncertainty**2,
            "uncertainty": uncertainty,
        }


class HuggingFaceEnsemble:
    """Ensemble of Hugging Face time series models"""

    def __init__(self, input_dim: int, prediction_horizon: int, hf_token: str):
        self.input_dim = input_dim
        self.prediction_horizon = prediction_horizon
        self.hf_token = hf_token
        self.models = []
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        # List of promising time series models
        model_configs = [
            {
                "name": "microsoft/DialoGPT-medium",
                "type": "transformer",
                "weight": 0.15,
            },
            {"name": "google/flan-t5-small", "type": "seq2seq", "weight": 0.2},
            {"name": "chronos", "type": "chronos", "weight": 0.3},
        ]

        self._initialize_models(model_configs)

    def _initialize_models(self, model_configs: List[Dict]):
        """Initialize all models in the ensemble"""

        for config in model_configs:
            try:
                if config["type"] == "chronos":
                    model = ChronosWrapper(
                        self.input_dim, self.prediction_horizon, self.hf_token
                    )
                else:
                    model = HuggingFaceTimeSeriesModel(
                        config["name"],
                        self.input_dim,
                        self.prediction_horizon,
                        self.hf_token,
                    )

                model = model.to(self.device)
                self.models.append(
                    {"model": model, "weight": config["weight"], "name": config["name"]}
                )

                logging.info(f"Added {config['name']} to ensemble")

            except Exception as e:
                logging.warning(f"Failed to initialize {config['name']}: {e}")
                continue

        if not self.models:
            # Add at least one fallback model
            fallback = HuggingFaceTimeSeriesModel(
                "fallback", self.input_dim, self.prediction_horizon, self.hf_token
            ).to(self.device)
            self.models.append({"model": fallback, "weight": 1.0, "name": "fallback"})
            logging.info("Added fallback model to ensemble")

    def predict(self, x: torch.Tensor) -> Dict[str, torch.Tensor]:
        """Generate ensemble predictions"""

        if not self.models:
            raise ValueError("No models available in ensemble")

        # Ensure input tensor is on the correct device
        x = x.to(self.device)

        weighted_predictions = []
        weighted_uncertainties = []
        total_weight = sum(model["weight"] for model in self.models)

        with torch.no_grad():
            for model_info in self.models:
                try:
                    model = model_info["model"]
                    weight = model_info["weight"] / total_weight

                    # Ensure model is on the same device
                    model = model.to(self.device)
                    model.eval()
                    output = model(x)

                    weighted_predictions.append(output["mean"] * weight)
                    weighted_uncertainties.append(output["uncertainty"] * weight)

                except Exception as e:
                    logging.warning(f"Error in model {model_info['name']}: {e}")
                    continue

        if not weighted_predictions:
            raise RuntimeError("All models failed to generate predictions")

        # Combine predictions
        ensemble_mean = torch.stack(weighted_predictions).sum(dim=0)
        ensemble_uncertainty = torch.stack(weighted_uncertainties).sum(dim=0)

        # Add epistemic uncertainty (disagreement between models)
        if len(weighted_predictions) > 1:
            individual_preds = torch.stack(
                [
                    pred / (model["weight"] / total_weight)
                    for pred, model in zip(weighted_predictions, self.models)
                ]
            )
            epistemic_uncertainty = individual_preds.std(dim=0)
            total_uncertainty = torch.sqrt(
                ensemble_uncertainty**2 + epistemic_uncertainty**2
            )
        else:
            total_uncertainty = ensemble_uncertainty

        return {
            "mean": ensemble_mean,
            "variance": total_uncertainty**2,
            "uncertainty": total_uncertainty,
        }

    def train_models(
        self,
        train_data: torch.Tensor,
        train_targets: torch.Tensor,
        epochs: int = 50,
        lr: float = 0.001,
    ):
        """Fine-tune the ensemble models"""

        for model_info in self.models:
            try:
                model = model_info["model"]
                optimizer = torch.optim.AdamW(
                    model.parameters(), lr=lr, weight_decay=1e-5
                )
                criterion = nn.MSELoss()

                model.train()

                for epoch in range(epochs):
                    optimizer.zero_grad()

                    output = model(train_data)
                    loss = criterion(output["mean"], train_targets)

                    # Add uncertainty loss to encourage calibration
                    if "variance" in output:
                        uncertainty_loss = -torch.log(output["variance"]).mean()
                        loss += 0.1 * uncertainty_loss

                    loss.backward()
                    torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                    optimizer.step()

                    if epoch % 10 == 0:
                        logging.info(
                            f"Model {model_info['name']} - Epoch {epoch}, Loss: {loss.item():.6f}"
                        )

                logging.info(f"Finished training {model_info['name']}")

            except Exception as e:
                logging.warning(f"Error training {model_info['name']}: {e}")
                continue


def get_available_hf_timeseries_models(hf_token: str) -> List[str]:
    """Get list of available time series models from Hugging Face"""

    try:
        if hf_token:
            login(token=hf_token)

        # Search for time series related models
        models = list_models(
            filter=["time-series", "forecasting", "prediction"], limit=50
        )

        model_names = [model.modelId for model in models]
        logging.info(f"Found {len(model_names)} time series models")
        return model_names

    except Exception as e:
        logging.warning(f"Error fetching HF models: {e}")
        return []


def create_hf_enhanced_ensemble(
    input_dim: int,
    sequence_length: int = 60,
    prediction_horizon: int = 7,
    hf_token: str = None,
):
    """Create enhanced ensemble with stable local models (HF integration disabled for stability)"""

    from .simple_ensemble import create_simple_ensemble

    # For stability, use the proven simple ensemble instead of problematic HF models
    logging.info("Creating enhanced local ensemble (HF models disabled for stability)")

    # Create a robust local ensemble
    ensemble = create_simple_ensemble(input_dim, sequence_length, prediction_horizon)

    # Add a wrapper to maintain compatibility
    class EnhancedLocalEnsemble:
        def __init__(self, base_ensemble):
            self.base_ensemble = base_ensemble

        def predict(self, x: torch.Tensor) -> Dict[str, torch.Tensor]:
            return self.base_ensemble.predict(x)

        def train_ensemble(self, train_X, train_y, epochs=50):
            if hasattr(self.base_ensemble, "train_ensemble"):
                return self.base_ensemble.train_ensemble(train_X, train_y, epochs)

    return EnhancedLocalEnsemble(ensemble)
