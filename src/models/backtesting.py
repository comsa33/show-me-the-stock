import logging
from datetime import datetime
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
import torch
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


class BacktestEngine:
    def __init__(
        self, initial_capital: float = 100000.0, transaction_cost: float = 0.001
    ):
        self.initial_capital = initial_capital
        self.transaction_cost = transaction_cost
        self.reset()

    def reset(self):
        """Reset the backtesting environment"""
        self.capital = self.initial_capital
        self.positions = 0
        self.portfolio_value = self.initial_capital
        self.trades = []
        self.portfolio_history = []
        self.benchmark_history = []

    def execute_trade(
        self,
        action: str,
        price: float,
        quantity: Optional[int] = None,
        timestamp: Optional[pd.Timestamp] = None,
    ):
        """Execute a trade (buy/sell/hold)"""
        if quantity is None:
            # Use all available capital for buy, all positions for sell
            if action == "buy":
                quantity = int(self.capital / (price * (1 + self.transaction_cost)))
            elif action == "sell":
                quantity = self.positions
            else:  # hold
                quantity = 0

        cost = 0
        if action == "buy" and quantity > 0:
            cost = quantity * price * (1 + self.transaction_cost)
            if cost <= self.capital:
                self.capital -= cost
                self.positions += quantity
                self.trades.append(
                    {
                        "timestamp": timestamp,
                        "action": "buy",
                        "quantity": quantity,
                        "price": price,
                        "cost": cost,
                    }
                )

        elif action == "sell" and quantity > 0:
            if quantity <= self.positions:
                revenue = quantity * price * (1 - self.transaction_cost)
                self.capital += revenue
                self.positions -= quantity
                self.trades.append(
                    {
                        "timestamp": timestamp,
                        "action": "sell",
                        "quantity": quantity,
                        "price": price,
                        "revenue": revenue,
                    }
                )

        # Update portfolio value
        self.portfolio_value = self.capital + self.positions * price

    def get_portfolio_metrics(
        self, prices: pd.Series, timestamps: pd.Series
    ) -> Dict[str, float]:
        """Calculate portfolio performance metrics"""
        if len(self.portfolio_history) < 2:
            return {}

        portfolio_values = np.array(self.portfolio_history)
        benchmark_values = np.array(self.benchmark_history)

        # Returns calculation
        portfolio_returns = np.diff(portfolio_values) / portfolio_values[:-1]
        benchmark_returns = np.diff(benchmark_values) / benchmark_values[:-1]

        # Total return
        total_return = (
            portfolio_values[-1] - self.initial_capital
        ) / self.initial_capital
        benchmark_total_return = (
            benchmark_values[-1] - benchmark_values[0]
        ) / benchmark_values[0]

        # Annualized metrics
        trading_days = len(portfolio_returns)
        annualized_return = (1 + total_return) ** (252 / trading_days) - 1

        # Volatility
        portfolio_volatility = np.std(portfolio_returns) * np.sqrt(252)

        # Sharpe ratio (assuming 2% risk-free rate)
        risk_free_rate = 0.02
        sharpe_ratio = (
            (annualized_return - risk_free_rate) / portfolio_volatility
            if portfolio_volatility > 0
            else 0
        )

        # Maximum drawdown
        peak = np.maximum.accumulate(portfolio_values)
        drawdown = (portfolio_values - peak) / peak
        max_drawdown = np.min(drawdown)

        # Win rate
        profitable_trades = sum(
            1
            for trade in self.trades[1:]
            if trade.get("action") == "sell"
            and trade.get("revenue", 0) > trade.get("cost", float("inf"))
        )
        total_trades = len([t for t in self.trades if t.get("action") == "sell"])
        win_rate = profitable_trades / total_trades if total_trades > 0 else 0

        return {
            "total_return": total_return,
            "annualized_return": annualized_return,
            "benchmark_return": benchmark_total_return,
            "alpha": total_return - benchmark_total_return,
            "volatility": portfolio_volatility,
            "sharpe_ratio": sharpe_ratio,
            "max_drawdown": max_drawdown,
            "win_rate": win_rate,
            "total_trades": total_trades,
            "final_portfolio_value": portfolio_values[-1],
        }


class PredictionValidator:
    def __init__(self):
        self.results = {}

    def cross_validate_predictions(
        self,
        model,
        data_processor,
        df: pd.DataFrame,
        n_folds: int = 5,
        sequence_length: int = 60,
        prediction_horizon: int = 30,
    ) -> Dict[str, List[float]]:
        """Perform time series cross-validation"""

        # Prepare data
        X, y, feature_columns = data_processor.prepare_data(
            df, sequence_length, prediction_horizon
        )

        fold_size = len(X) // n_folds
        metrics = {"mse": [], "mae": [], "rmse": [], "r2": [], "mape": []}

        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        model = model.to(device)

        for fold in range(n_folds):
            start_idx = fold * fold_size
            end_idx = start_idx + fold_size if fold < n_folds - 1 else len(X)

            # Split data
            train_X = (
                np.concatenate([X[:start_idx], X[end_idx:]], axis=0)
                if start_idx > 0
                else X[end_idx:]
            )
            train_y = (
                np.concatenate([y[:start_idx], y[end_idx:]], axis=0)
                if start_idx > 0
                else y[end_idx:]
            )
            val_X = X[start_idx:end_idx]
            val_y = y[start_idx:end_idx]

            if len(train_X) == 0 or len(val_X) == 0:
                continue

            # Train model
            trained_model = self._train_model_fold(model, train_X, train_y, device)

            # Predict
            with torch.no_grad():
                val_X_tensor = torch.FloatTensor(val_X).to(device)
                predictions = trained_model(val_X_tensor)["predictions"].cpu().numpy()

            # Calculate metrics
            fold_metrics = self._calculate_metrics(val_y, predictions)
            for metric, value in fold_metrics.items():
                metrics[metric].append(value)

        return metrics

    def _train_model_fold(self, model, train_X, train_y, device, epochs=50):
        """Train model for one fold"""
        model.train()
        optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
        criterion = torch.nn.MSELoss()

        train_X_tensor = torch.FloatTensor(train_X).to(device)
        train_y_tensor = torch.FloatTensor(train_y).to(device)

        for epoch in range(epochs):
            optimizer.zero_grad()
            outputs = model(train_X_tensor)

            # Combined loss: prediction + VAE
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

        return model

    def _calculate_metrics(self, y_true, y_pred):
        """Calculate prediction metrics"""
        # Flatten arrays for multi-step predictions
        y_true_flat = y_true.flatten()
        y_pred_flat = y_pred.flatten()

        mse = mean_squared_error(y_true_flat, y_pred_flat)
        mae = mean_absolute_error(y_true_flat, y_pred_flat)
        rmse = np.sqrt(mse)
        r2 = r2_score(y_true_flat, y_pred_flat)

        # MAPE (Mean Absolute Percentage Error)
        mape = np.mean(np.abs((y_true_flat - y_pred_flat) / y_true_flat)) * 100

        return {"mse": mse, "mae": mae, "rmse": rmse, "r2": r2, "mape": mape}


class TradingStrategy:
    def __init__(self, confidence_threshold: float = 0.6):
        self.confidence_threshold = confidence_threshold

    def generate_signals(
        self,
        predictions: np.ndarray,
        current_prices: np.ndarray,
        confidence_scores: Optional[np.ndarray] = None,
    ) -> List[str]:
        """Generate trading signals based on predictions"""
        signals = []

        for i, (pred, current) in enumerate(zip(predictions, current_prices)):
            # Calculate expected return
            expected_return = (pred - current) / current

            # Apply confidence threshold if available
            confidence = confidence_scores[i] if confidence_scores is not None else 1.0

            if confidence < self.confidence_threshold:
                signals.append("hold")
            elif expected_return > 0.02:  # 2% threshold for buy
                signals.append("buy")
            elif expected_return < -0.02:  # -2% threshold for sell
                signals.append("sell")
            else:
                signals.append("hold")

        return signals

    def momentum_strategy(
        self, predictions: np.ndarray, lookback_window: int = 5
    ) -> List[str]:
        """Momentum-based trading strategy"""
        signals = []

        for i in range(len(predictions)):
            if i < lookback_window:
                signals.append("hold")
                continue

            # Calculate momentum
            recent_predictions = predictions[max(0, i - lookback_window) : i]
            momentum = np.mean(np.diff(recent_predictions))

            if momentum > 0.01:
                signals.append("buy")
            elif momentum < -0.01:
                signals.append("sell")
            else:
                signals.append("hold")

        return signals


def run_comprehensive_backtest(
    model,
    data_processor,
    df: pd.DataFrame,
    sequence_length: int = 60,
    prediction_horizon: int = 30,
    initial_capital: float = 100000.0,
) -> Dict:
    """Run comprehensive backtesting with multiple strategies"""

    try:
        # Prepare data - handle different processor types
        if hasattr(data_processor, "prepare_advanced_data"):
            # Advanced data processor
            X, y, feature_columns = data_processor.prepare_advanced_data(
                df, sequence_length, prediction_horizon
            )
        else:
            # Standard data processor
            X, y, feature_columns = data_processor.prepare_data(
                df, sequence_length, prediction_horizon
            )

        # Split data for training and testing
        split_idx = int(len(X) * 0.8)
        train_X, test_X = X[:split_idx], X[split_idx:]
        train_y, test_y = y[:split_idx], y[split_idx:]

        # Check for dimension mismatch
        expected_input_dim = X.shape[-1]
        if hasattr(model, "input_dim") and model.input_dim != expected_input_dim:
            raise ValueError(
                f"Model expects {model.input_dim} features but data has {expected_input_dim}"
            )

    except Exception as e:
        logging.warning(f"Error in data preparation for backtesting: {e}")
        # Return minimal results
        return {
            "error": str(e),
            "buy_and_hold": {"metrics": {}, "portfolio_history": [], "trades": []},
            "prediction_based": {"metrics": {}, "portfolio_history": [], "trades": []},
            "momentum": {"metrics": {}, "portfolio_history": [], "trades": []},
            "prediction_accuracy": {},
            "test_dates": [],
            "actual_prices": [],
            "predicted_prices": [],
        }

    # Get corresponding price data for testing
    test_start_idx = split_idx + sequence_length
    test_end_idx = test_start_idx + len(test_X)

    # Handle different index types
    if hasattr(df.index, "to_pydatetime"):
        test_dates = df.index[test_start_idx:test_end_idx]
    else:
        # Create synthetic dates if index is not datetime
        end_date = datetime.now()
        test_dates = pd.date_range(end=end_date, periods=len(test_X), freq="D")

    test_prices = df["Close"].iloc[test_start_idx : test_start_idx + len(test_X)].values

    # Ensure lengths match
    min_length = min(len(test_dates), len(test_prices), len(test_X))
    test_dates = test_dates[:min_length]
    test_prices = test_prices[:min_length]
    test_X = test_X[:min_length]
    test_y = test_y[:min_length]

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # Check if model has 'to' method (for ensemble models)
    if hasattr(model, "to"):
        model = model.to(device)
    elif hasattr(model, "device"):
        # For ensemble models that manage device internally
        pass
    else:
        logging.warning("Model doesn't support device movement, using as-is")

    # Train model (only for PyTorch models, not ensemble models)
    if hasattr(model, "train") and hasattr(model, "parameters"):
        # This is a PyTorch model
        model.train()
        optimizer = torch.optim.Adam(model.parameters(), lr=0.001, weight_decay=1e-5)
        criterion = torch.nn.MSELoss()

        train_X_tensor = torch.FloatTensor(train_X).to(device)
        train_y_tensor = torch.FloatTensor(train_y).to(device)

        # Training loop
        for epoch in range(100):
            optimizer.zero_grad()
            outputs = model(train_X_tensor)

            pred_loss = criterion(outputs["predictions"], train_y_tensor)
            if "reconstructed" in outputs and hasattr(model, "vae_loss"):
                vae_loss = model.vae_loss(
                    train_X_tensor,
                    outputs["reconstructed"],
                    outputs["mu"],
                    outputs["logvar"],
                )
                total_loss = pred_loss + 0.1 * vae_loss
            else:
                total_loss = pred_loss

            total_loss.backward()
            optimizer.step()
    elif hasattr(model, "train_ensemble"):
        # This is an ensemble model with its own training method
        train_X_tensor = torch.FloatTensor(train_X)
        train_y_tensor = torch.FloatTensor(train_y)
        model.train_ensemble(train_X_tensor, train_y_tensor, epochs=50)
    else:
        # Model is already trained or doesn't need training
        logging.info("Model doesn't need training or is already trained")

    # Generate predictions
    if hasattr(model, "eval"):
        model.eval()

    with torch.no_grad():
        test_X_tensor = torch.FloatTensor(test_X)
        if hasattr(model, "predict"):
            # Use ensemble predict method
            test_outputs = model.predict(test_X_tensor)
            predictions = test_outputs["mean"].cpu().numpy()
        else:
            # Use PyTorch model
            test_X_tensor = test_X_tensor.to(device)
            test_outputs = model(test_X_tensor)
            predictions = test_outputs["predictions"].cpu().numpy()

    # Inverse transform predictions (use first day prediction for trading)
    if len(predictions.shape) > 1 and predictions.shape[1] > 0:
        predictions_for_trading = predictions[:, 0]  # First day prediction
    else:
        predictions_for_trading = predictions.flatten()

    # Inverse transform predictions
    if hasattr(data_processor, "inverse_transform_target"):
        # Advanced data processor
        predictions_original = data_processor.inverse_transform_target(
            predictions_for_trading, df
        )
    else:
        # Standard data processor
        predictions_original = data_processor.inverse_transform_predictions(
            predictions_for_trading
        )

    # Initialize backtesting engines
    strategies = {
        "buy_and_hold": BacktestEngine(initial_capital),
        "prediction_based": BacktestEngine(initial_capital),
        "momentum": BacktestEngine(initial_capital),
    }

    trading_strategy = TradingStrategy()

    # Run backtests
    for i, (date, current_price, predicted_price) in enumerate(
        zip(test_dates, test_prices, predictions_original)
    ):
        # Buy and hold strategy
        if i == 0:
            strategies["buy_and_hold"].execute_trade(
                "buy", current_price, timestamp=date
            )
        else:
            strategies["buy_and_hold"].execute_trade(
                "hold", current_price, timestamp=date
            )

        # Prediction-based strategy
        signals = trading_strategy.generate_signals([predicted_price], [current_price])
        strategies["prediction_based"].execute_trade(
            signals[0], current_price, timestamp=date
        )

        # Momentum strategy
        if i >= 5:
            momentum_signals = trading_strategy.momentum_strategy(
                predictions_original[: i + 1]
            )
            strategies["momentum"].execute_trade(
                momentum_signals[-1], current_price, timestamp=date
            )
        else:
            strategies["momentum"].execute_trade("hold", current_price, timestamp=date)

        # Update portfolio histories
        for strategy in strategies.values():
            strategy.portfolio_history.append(strategy.portfolio_value)
            strategy.benchmark_history.append(
                initial_capital * current_price / test_prices[0]
            )

    # Calculate metrics for all strategies
    results = {}
    for name, engine in strategies.items():
        metrics = engine.get_portfolio_metrics(
            pd.Series(test_prices, index=test_dates), pd.Series(test_dates)
        )
        results[name] = {
            "metrics": metrics,
            "portfolio_history": engine.portfolio_history,
            "trades": engine.trades,
        }

    # Add prediction accuracy metrics
    validator = PredictionValidator()
    accuracy_metrics = validator._calculate_metrics(
        test_y[: len(predictions), 0], predictions[:, 0]
    )

    results["prediction_accuracy"] = accuracy_metrics
    results["test_dates"] = test_dates
    results["actual_prices"] = test_prices
    results["predicted_prices"] = predictions_original

    return results
