"""Time Series Analysis Service — ARIMA, GARCH, and decomposition for financial data.

Provides offline-capable time series analysis using statsmodels and arch.
All computations run locally — no data leaves the machine.
"""

import numpy as np
import pandas as pd
from typing import Optional


def generate_sample_prices(n: int = 252, seed: int = 42) -> list[float]:
    """Generate realistic sample daily closing prices for demo purposes."""
    rng = np.random.RandomState(seed)
    returns = rng.normal(0.0005, 0.02, n)
    prices = [100.0]
    for r in returns[1:]:
        prices.append(prices[-1] * (1 + r))
    return [round(p, 2) for p in prices]


def time_series_summary(prices: list[float]) -> dict:
    """Compute basic summary statistics for a price series."""
    series = pd.Series(prices, dtype=float)
    returns = series.pct_change().dropna()

    return {
        "count": len(series),
        "first": float(series.iloc[0]),
        "last": float(series.iloc[-1]),
        "min": float(series.min()),
        "max": float(series.max()),
        "mean": float(series.mean()),
        "std": float(series.std()),
        "total_return_pct": round(float((series.iloc[-1] / series.iloc[0] - 1) * 100), 2),
        "volatility_annual": round(float(returns.std() * np.sqrt(252) * 100), 2),
        "skewness": round(float(returns.skew()), 4),
        "kurtosis": round(float(returns.kurtosis()), 4),
    }


def run_arima(prices: list[float], forecast_steps: int = 30) -> dict:
    """Fit ARIMA model and produce forecast.

    Uses ARIMA(5,1,0) as a robust default for financial time series.
    Falls back to simple moving average if statsmodels is unavailable.
    """
    series = pd.Series(prices, dtype=float)
    n = len(series)
    dates = pd.date_range(end="2025-01-01", periods=n, freq="B")
    series.index = dates

    try:
        from statsmodels.tsa.arima.model import ARIMA

        model = ARIMA(series, order=(5, 1, 0))
        fit = model.fit()
        forecast = fit.forecast(steps=forecast_steps)

        # Confidence intervals
        fc_results = fit.get_forecast(steps=forecast_steps)
        ci = fc_results.conf_int(alpha=0.05)

        forecast_dates = pd.date_range(start=dates[-1] + pd.Timedelta(days=1), periods=forecast_steps, freq="B")

        return {
            "method": "ARIMA(5,1,0)",
            "aic": round(float(fit.aic), 2),
            "bic": round(float(fit.bic), 2),
            "historical": {
                "dates": [d.strftime("%Y-%m-%d") for d in dates],
                "values": [round(v, 2) for v in series.values],
            },
            "forecast": {
                "dates": [d.strftime("%Y-%m-%d") for d in forecast_dates],
                "values": [round(v, 2) for v in forecast.values],
                "lower": [round(v, 2) for v in ci.iloc[:, 0].values],
                "upper": [round(v, 2) for v in ci.iloc[:, 1].values],
            },
            "forecast_steps": forecast_steps,
        }
    except ImportError:
        # Fallback: simple moving average
        window = min(20, n // 2)
        ma = series.rolling(window=window).mean().iloc[-1]
        last_price = series.iloc[-1]
        forecast_values = [last_price + (ma - last_price) * (i / forecast_steps) * 0.5 for i in range(forecast_steps)]

        return {
            "method": "Moving Average (fallback)",
            "aic": None,
            "bic": None,
            "historical": {
                "dates": [d.strftime("%Y-%m-%d") for d in dates],
                "values": [round(v, 2) for v in series.values],
            },
            "forecast": {
                "dates": [(dates[-1] + pd.Timedelta(days=i + 1)).strftime("%Y-%m-%d") for i in range(forecast_steps)],
                "values": [round(v, 2) for v in forecast_values],
                "lower": [round(v * 0.97, 2) for v in forecast_values],
                "upper": [round(v * 1.03, 2) for v in forecast_values],
            },
            "forecast_steps": forecast_steps,
        }
    except Exception as e:
        return {"error": str(e)[:300], "method": "ARIMA"}


def run_garch(prices: list[float]) -> dict:
    """Fit GARCH(1,1) model to estimate conditional volatility.

    Returns volatility clustering analysis for risk management.
    """
    series = pd.Series(prices, dtype=float)
    returns = series.pct_change().dropna() * 100  # percentage returns

    try:
        from arch import arch_model

        am = arch_model(returns, vol="Garch", p=1, q=1, dist="normal")
        fit = am.fit(disp="off", show_warning=False)

        # Conditional volatility
        cond_vol = fit.conditional_volatility / np.sqrt(252) * 100  # annualized

        # Forecast volatility
        forecasts = fit.forecast(horizon=30)
        forecast_var = forecasts.variance.iloc[-1]
        forecast_vol = np.sqrt(forecast_var.values) / np.sqrt(252) * 100

        # Annualized numbers
        omega = float(fit.params["omega"])
        alpha = float(fit.params["alpha[1]"])
        beta = float(fit.params["beta[1]"])

        return {
            "method": "GARCH(1,1)",
            "parameters": {
                "omega": round(omega, 6),
                "alpha": round(alpha, 4),
                "beta": round(beta, 4),
            },
            "persistence": round(alpha + beta, 4),
            "long_run_volatility": round(float(np.sqrt(omega / (1 - alpha - beta))), 2) if (alpha + beta) < 1 else None,
            "current_annual_volatility": round(float(cond_vol.iloc[-1]), 2),
            "conditional_volatility": [round(float(v), 2) for v in cond_vol.tolist()],
            "forecast_volatility": [round(float(v), 2) for v in forecast_vol.tolist()],
            "aic": round(float(fit.aic), 2),
        }
    except ImportError:
        # Fallback: simple rolling volatility
        rolling_vol = returns.rolling(21).std().dropna() * np.sqrt(252)
        return {
            "method": "Rolling Volatility (fallback)",
            "parameters": None,
            "persistence": None,
            "long_run_volatility": round(float(rolling_vol.iloc[-1]), 2),
            "current_annual_volatility": round(float(rolling_vol.iloc[-1]), 2),
            "conditional_volatility": [round(float(v), 2) for v in rolling_vol.tolist()],
            "forecast_volatility": None,
            "aic": None,
        }
    except Exception as e:
        return {"error": str(e)[:300], "method": "GARCH"}


def decompose_series(prices: list[float], period: Optional[int] = None) -> dict:
    """Decompose time series into trend, seasonal, and residual components.

    Uses statsmodels seasonal_decompose with additive model.
    """
    series = pd.Series(prices, dtype=float)
    n = len(series)

    # Auto-detect period if not provided
    if period is None:
        period = min(21, max(5, n // 12))  # default ~monthly for daily data

    try:
        from statsmodels.tsa.seasonal import seasonal_decompose

        decomp = seasonal_decompose(series, model="additive", period=period)

        # Clean NaN values
        def clean(s):
            vals = s.fillna(method="bfill").fillna(method="ffill").tolist()
            return [round(v, 2) for v in vals]

        return {
            "method": f"Additive Decomposition (period={period})",
            "period": period,
            "trend": clean(decomp.trend),
            "seasonal": clean(decomp.seasonal),
            "residual": clean(decomp.resid),
            "observed": [round(v, 2) for v in series.tolist()],
        }
    except ImportError:
        return {"error": "statsmodels not available", "method": "Decomposition"}
    except Exception as e:
        return {"error": str(e)[:300], "method": "Decomposition"}


def run_full_pipeline(prices: list[float], forecast_steps: int = 30) -> dict:
    """Run complete time series analysis pipeline."""
    summary = time_series_summary(prices)
    arima_result = run_arima(prices, forecast_steps)
    garch_result = run_garch(prices)
    decomp_result = decompose_series(prices)

    # Generate recommendations
    recommendations = []
    vol = summary.get("volatility_annual", 0)
    if vol > 40:
        recommendations.append({"level": "warning", "text": "High annualized volatility — consider hedging strategies"})
    elif vol < 10:
        recommendations.append({"level": "info", "text": "Low volatility — suitable for conservative strategies"})

    if garch_result.get("persistence") and garch_result["persistence"] > 0.9:
        recommendations.append({"level": "warning", "text": "Volatility clustering is strong — GARCH effects significant"})

    skew = summary.get("skewness", 0)
    if skew < -1:
        recommendations.append({"level": "warning", "text": "Negative skewness — fat left tail, downside risk"})

    return {
        "summary": summary,
        "arima": arima_result,
        "garch": garch_result,
        "decomposition": decomp_result,
        "recommendations": recommendations,
    }
