import warnings
from typing import Dict, Optional

import numpy as np
import pandas as pd
import torch
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

warnings.filterwarnings("ignore")


class PerformanceEvaluator:
    """Advanced performance evaluation for time series prediction"""

    def __init__(self):
        self.metrics_history = []

    def calculate_comprehensive_metrics(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        prices: Optional[np.ndarray] = None,
    ) -> Dict[str, float]:
        """Calculate comprehensive prediction metrics"""

        # Flatten arrays if multidimensional
        if y_true.ndim > 1:
            y_true = y_true.flatten()
        if y_pred.ndim > 1:
            y_pred = y_pred.flatten()

        # Remove any NaN or infinite values
        mask = np.isfinite(y_true) & np.isfinite(y_pred)
        y_true = y_true[mask]
        y_pred = y_pred[mask]

        if len(y_true) == 0:
            return {"error": "No valid predictions"}

        metrics = {}

        # Basic regression metrics
        metrics["mse"] = mean_squared_error(y_true, y_pred)
        metrics["rmse"] = np.sqrt(metrics["mse"])
        metrics["mae"] = mean_absolute_error(y_true, y_pred)
        metrics["r2"] = r2_score(y_true, y_pred)

        # Mean Absolute Percentage Error
        epsilon = 1e-8  # Avoid division by zero
        metrics["mape"] = np.mean(np.abs((y_true - y_pred) / (y_true + epsilon))) * 100

        # Symmetric Mean Absolute Percentage Error
        metrics["smape"] = (
            np.mean(
                2
                * np.abs(y_pred - y_true)
                / (np.abs(y_true) + np.abs(y_pred) + epsilon)
            )
            * 100
        )

        # Direction accuracy (for price movements)
        if len(y_true) > 1:
            true_direction = np.diff(y_true) > 0
            pred_direction = np.diff(y_pred) > 0
            metrics["direction_accuracy"] = (
                np.mean(true_direction == pred_direction) * 100
            )
        else:
            metrics["direction_accuracy"] = 0

        # Mean Directional Accuracy
        if prices is not None and len(prices) > 1:
            true_returns = np.diff(prices) / prices[:-1]
            pred_returns = (y_pred[1:] - prices[:-1]) / prices[:-1]
            same_direction = np.sign(true_returns) == np.sign(pred_returns)
            metrics["mda"] = np.mean(same_direction) * 100
        else:
            metrics["mda"] = metrics["direction_accuracy"]

        # Theil's U statistic
        if len(y_true) > 1:
            naive_forecast = y_true[:-1]  # Naive forecast (previous value)
            actual_change = y_true[1:]

            if len(naive_forecast) == len(y_pred[1:]):
                naive_mse = mean_squared_error(actual_change, naive_forecast)
                pred_mse = mean_squared_error(actual_change, y_pred[1:])
                metrics["theil_u"] = (
                    np.sqrt(pred_mse) / np.sqrt(naive_mse)
                    if naive_mse > 0
                    else float("inf")
                )
            else:
                metrics["theil_u"] = float("inf")
        else:
            metrics["theil_u"] = float("inf")

        # Correlation coefficient
        if np.std(y_true) > 0 and np.std(y_pred) > 0:
            metrics["correlation"] = np.corrcoef(y_true, y_pred)[0, 1]
        else:
            metrics["correlation"] = 0

        # Forecast bias
        metrics["bias"] = np.mean(y_pred - y_true)
        metrics["bias_percentage"] = (
            (metrics["bias"] / np.mean(y_true)) * 100 if np.mean(y_true) != 0 else 0
        )

        # Prediction intervals metrics (if variance is available)
        # This would require confidence intervals from the model

        return metrics

    def evaluate_financial_performance(
        self,
        predictions: np.ndarray,
        actual_prices: np.ndarray,
        initial_capital: float = 100000,
    ) -> Dict[str, float]:
        """Evaluate financial performance of predictions"""

        if len(predictions) != len(actual_prices):
            min_len = min(len(predictions), len(actual_prices))
            predictions = predictions[:min_len]
            actual_prices = actual_prices[:min_len]

        metrics = {}

        # Simple trading strategy: buy if prediction > current, sell if prediction < current
        positions = []
        portfolio_value = initial_capital
        cash = initial_capital
        shares = 0

        for i in range(len(predictions) - 1):
            current_price = actual_prices[i]
            predicted_price = predictions[i]
            next_price = actual_prices[i + 1]

            # Trading decision
            if predicted_price > current_price * 1.02:  # Buy if prediction > 2% higher
                if cash > current_price:
                    shares_to_buy = cash // current_price
                    shares += shares_to_buy
                    cash -= shares_to_buy * current_price
            elif (
                predicted_price < current_price * 0.98
            ):  # Sell if prediction < 2% lower
                if shares > 0:
                    cash += shares * current_price
                    shares = 0

            # Calculate portfolio value
            portfolio_value = cash + shares * next_price
            positions.append(portfolio_value)

        if positions:
            # Performance metrics
            returns = np.array(positions) / initial_capital - 1
            metrics["total_return"] = returns[-1] * 100
            metrics["max_return"] = np.max(returns) * 100
            metrics["min_return"] = np.min(returns) * 100

            # Volatility
            daily_returns = np.diff(returns)
            metrics["volatility"] = (
                np.std(daily_returns) * np.sqrt(252) * 100
            )  # Annualized

            # Sharpe ratio (assuming 2% risk-free rate)
            risk_free_rate = 0.02
            excess_returns = returns[-1] - risk_free_rate
            metrics["sharpe_ratio"] = (
                excess_returns / (metrics["volatility"] / 100)
                if metrics["volatility"] > 0
                else 0
            )

            # Maximum drawdown
            peak = np.maximum.accumulate(np.array(positions))
            drawdown = (np.array(positions) - peak) / peak
            metrics["max_drawdown"] = np.min(drawdown) * 100

            # Win rate
            profitable_trades = np.sum(daily_returns > 0)
            total_trades = len(daily_returns)
            metrics["win_rate"] = (
                (profitable_trades / total_trades) * 100 if total_trades > 0 else 0
            )

        return metrics

    def confidence_interval_coverage(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        lower_bound: np.ndarray,
        upper_bound: np.ndarray,
    ) -> Dict[str, float]:
        """Evaluate prediction interval coverage"""

        # Flatten arrays
        y_true = y_true.flatten()
        y_pred = y_pred.flatten()
        lower_bound = lower_bound.flatten()
        upper_bound = upper_bound.flatten()

        # Remove invalid values
        mask = (
            np.isfinite(y_true)
            & np.isfinite(y_pred)
            & np.isfinite(lower_bound)
            & np.isfinite(upper_bound)
        )
        y_true = y_true[mask]
        lower_bound = lower_bound[mask]
        upper_bound = upper_bound[mask]

        if len(y_true) == 0:
            return {"error": "No valid predictions"}

        # Coverage rate
        in_interval = (y_true >= lower_bound) & (y_true <= upper_bound)
        coverage_rate = np.mean(in_interval) * 100

        # Interval width
        avg_width = np.mean(upper_bound - lower_bound)
        relative_width = avg_width / np.mean(np.abs(y_true)) * 100

        # Calibration score (closer to expected coverage is better)
        expected_coverage = 90  # Assuming 90% prediction intervals
        calibration_score = 100 - abs(coverage_rate - expected_coverage)

        return {
            "coverage_rate": coverage_rate,
            "average_interval_width": avg_width,
            "relative_interval_width": relative_width,
            "calibration_score": calibration_score,
        }

    def model_comparison(self, results: Dict[str, Dict[str, float]]) -> pd.DataFrame:
        """Compare multiple models"""

        comparison_df = pd.DataFrame(results).T

        # Rank models by different metrics
        ranking_metrics = ["rmse", "mae", "mape", "direction_accuracy", "r2"]

        for metric in ranking_metrics:
            if metric in comparison_df.columns:
                ascending = metric not in ["direction_accuracy", "r2", "correlation"]
                comparison_df[f"{metric}_rank"] = comparison_df[metric].rank(
                    ascending=ascending
                )

        # Calculate overall score (lower is better for error metrics)
        error_metrics = ["rmse", "mae", "mape"]
        performance_metrics = ["direction_accuracy", "r2", "correlation"]

        # Normalize metrics to 0-1 scale
        for metric in error_metrics:
            if metric in comparison_df.columns:
                comparison_df[f"{metric}_norm"] = 1 - (
                    comparison_df[metric] - comparison_df[metric].min()
                ) / (comparison_df[metric].max() - comparison_df[metric].min())

        for metric in performance_metrics:
            if metric in comparison_df.columns:
                comparison_df[f"{metric}_norm"] = (
                    comparison_df[metric] - comparison_df[metric].min()
                ) / (comparison_df[metric].max() - comparison_df[metric].min())

        # Calculate composite score
        norm_columns = [col for col in comparison_df.columns if col.endswith("_norm")]
        if norm_columns:
            comparison_df["composite_score"] = comparison_df[norm_columns].mean(axis=1)
            comparison_df["overall_rank"] = comparison_df["composite_score"].rank(
                ascending=False
            )

        return comparison_df

    def generate_performance_report(
        self, y_true: np.ndarray, y_pred: np.ndarray, model_name: str = "Model"
    ) -> str:
        """Generate a comprehensive performance report"""

        metrics = self.calculate_comprehensive_metrics(y_true, y_pred)

        report = f"""
📊 {model_name} 성능 보고서
{'='*50}

🎯 예측 정확도:
- RMSE: {metrics.get('rmse', 0):.4f}
- MAE: {metrics.get('mae', 0):.4f}
- MAPE: {metrics.get('mape', 0):.2f}%
- R² Score: {metrics.get('r2', 0):.4f}

📈 방향성 예측:
- 방향 정확도: {metrics.get('direction_accuracy', 0):.2f}%
- 상관계수: {metrics.get('correlation', 0):.4f}

⚖️ 모델 안정성:
- Theil's U: {metrics.get('theil_u', float('inf')):.4f}
- 편향(Bias): {metrics.get('bias', 0):.4f}
- 편향율: {metrics.get('bias_percentage', 0):.2f}%

📊 평가 요약:
"""

        # Performance rating
        r2_score = metrics.get("r2", 0)
        direction_acc = metrics.get("direction_accuracy", 0)
        mape = metrics.get("mape", 100)

        if r2_score > 0.8 and direction_acc > 80 and mape < 10:
            rating = "🟢 우수 (Excellent)"
        elif r2_score > 0.6 and direction_acc > 70 and mape < 20:
            rating = "🟡 양호 (Good)"
        elif r2_score > 0.4 and direction_acc > 60 and mape < 30:
            rating = "🟠 보통 (Fair)"
        else:
            rating = "🔴 개선 필요 (Needs Improvement)"

        report += f"- 종합 평가: {rating}\n"

        # Recommendations
        report += "\n💡 개선 제안:\n"

        if mape > 30:
            report += (
                "- MAPE가 높습니다. 더 복잡한 모델이나 추가 특성을 고려해보세요.\n"
            )
        if direction_acc < 60:
            report += "- 방향성 예측이 부정확합니다. 기술적 지표나 시장 신호를 추가해보세요.\n"
        if r2_score < 0.5:
            report += "- R² 점수가 낮습니다. 모델 복잡도를 증가시키거나 데이터 품질을 검토해보세요.\n"
        if abs(metrics.get("bias_percentage", 0)) > 10:
            report += "- 예측에 편향이 있습니다. 모델 보정을 고려해보세요.\n"

        return report

    def save_metrics(self, metrics: Dict[str, float], model_name: str, timestamp: str):
        """Save metrics for tracking over time"""

        metrics_entry = {"model_name": model_name, "timestamp": timestamp, **metrics}

        self.metrics_history.append(metrics_entry)

    def get_metrics_history(self) -> pd.DataFrame:
        """Get historical metrics as DataFrame"""

        if not self.metrics_history:
            return pd.DataFrame()

        return pd.DataFrame(self.metrics_history)


def calculate_model_confidence_score(metrics: Dict[str, float]) -> float:
    """Calculate overall model confidence score (0-100)"""

    # Weights for different metrics (higher weight = more important)
    weights = {
        "r2": 0.25,
        "direction_accuracy": 0.25,
        "mape": 0.20,  # Lower is better
        "correlation": 0.15,
        "bias_percentage": 0.10,  # Lower absolute value is better
        "theil_u": 0.05,  # Lower is better
    }

    score = 0
    total_weight = 0

    for metric, weight in weights.items():
        if metric in metrics:
            if metric == "r2":
                # R² score: 0-1, higher is better
                normalized = max(0, min(1, metrics[metric])) * 100
            elif metric == "direction_accuracy":
                # Direction accuracy: 0-100, higher is better
                normalized = max(0, min(100, metrics[metric]))
            elif metric == "mape":
                # MAPE: lower is better, normalize to 0-100 scale
                normalized = max(0, 100 - min(100, metrics[metric]))
            elif metric == "correlation":
                # Correlation: -1 to 1, convert to 0-100 scale
                normalized = (max(-1, min(1, metrics[metric])) + 1) * 50
            elif metric == "bias_percentage":
                # Bias percentage: lower absolute value is better
                abs_bias = abs(metrics[metric])
                normalized = max(0, 100 - min(100, abs_bias))
            elif metric == "theil_u":
                # Theil's U: lower is better, 1.0 is neutral
                if metrics[metric] == float("inf"):
                    normalized = 0
                else:
                    normalized = max(0, 100 - min(100, metrics[metric] * 100))
            else:
                normalized = 0

            score += normalized * weight
            total_weight += weight

    if total_weight > 0:
        final_score = score / total_weight
    else:
        final_score = 0

    return max(0, min(100, final_score))


# Performance testing functions
def stress_test_model(
    model, test_data: torch.Tensor, iterations: int = 100
) -> Dict[str, float]:
    """Stress test model with repeated predictions"""

    prediction_times = []
    memory_usage = []

    import gc
    import time

    import psutil

    process = psutil.Process()

    for i in range(iterations):
        start_time = time.time()
        start_memory = process.memory_info().rss / 1024 / 1024  # MB

        with torch.no_grad():
            _ = model(test_data)

        end_time = time.time()
        end_memory = process.memory_info().rss / 1024 / 1024  # MB

        prediction_times.append(end_time - start_time)
        memory_usage.append(end_memory - start_memory)

        # Cleanup
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    return {
        "avg_prediction_time": np.mean(prediction_times),
        "max_prediction_time": np.max(prediction_times),
        "min_prediction_time": np.min(prediction_times),
        "std_prediction_time": np.std(prediction_times),
        "avg_memory_usage": np.mean(memory_usage),
        "max_memory_usage": np.max(memory_usage),
    }
