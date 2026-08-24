"""Financial Engineering Service — VaR, Monte Carlo, Black-Scholes, Markowitz.

Provides offline-capable quantitative finance tools.
All computations run locally — no data leaves the machine.
"""

import numpy as np
import math
from typing import Optional


def calculate_var(
    prices: list[float],
    confidence: float = 0.95,
    method: str = "historical",
    position_value: float = 1_000_000,
) -> dict:
    """Calculate Value at Risk (VaR) and Conditional VaR (CVaR/Expected Shortfall).

    Methods: historical, parametric (normal), cornish_fisher
    """
    returns = np.diff(prices) / prices[:-1]
    n = len(returns)

    if method == "historical":
        sorted_returns = np.sort(returns)
        idx = int((1 - confidence) * n)
        var_return = sorted_returns[idx]
        cvar_return = np.mean(sorted_returns[: idx + 1])

    elif method == "parametric":
        mu = np.mean(returns)
        sigma = np.std(returns)
        from scipy import stats

        z = stats.norm.ppf(1 - confidence)
        var_return = mu + z * sigma
        cvar_return = mu - sigma * stats.norm.pdf(z) / (1 - confidence)

    elif method == "cornish_fisher":
        mu = np.mean(returns)
        sigma = np.std(returns)
        S = float(np.mean(((returns - mu) / sigma) ** 3))  # skewness
        K = float(np.mean(((returns - mu) / sigma) ** 4) - 3)  # excess kurtosis
        from scipy import stats

        z = stats.norm.ppf(1 - confidence)
        z_cf = z + (z**2 - 1) * S / 6 + (z**3 - 3 * z) * K / 24 - (2 * z**3 - 5 * z) * S**2 / 36
        var_return = mu + z_cf * sigma
        cvar_return = var_return  # simplified
    else:
        return {"error": f"Unknown VaR method: {method}"}

    var_abs = abs(var_return * position_value)
    cvar_abs = abs(cvar_return * position_value)

    return {
        "method": method,
        "confidence": confidence,
        "position_value": position_value,
        "var_return_pct": round(float(var_return * 100), 4),
        "var_absolute": round(var_abs, 2),
        "cvar_return_pct": round(float(cvar_return * 100), 4),
        "cvar_absolute": round(cvar_abs, 2),
        "interpretation": f"With {confidence:.0%} confidence, max daily loss is {var_abs:,.0f} ({var_return*100:.2f}%)",
    }


def monte_carlo_simulation(
    s0: float,
    mu: float,
    sigma: float,
    days: int = 252,
    simulations: int = 10000,
    position_value: float = 1_000_000,
) -> dict:
    """Run Monte Carlo simulation for price paths.

    Uses geometric Brownian motion.
    """
    dt = 1 / 252
    rng = np.random.default_rng(42)

    # Generate all paths at once
    z = rng.standard_normal((simulations, days))
    returns = np.exp((mu - 0.5 * sigma**2) * dt + sigma * np.sqrt(dt) * z)
    paths = s0 * np.cumprod(returns, axis=1)

    # Prepend starting price
    paths = np.hstack([np.full((simulations, 1), s0), paths])

    # Final prices
    final_prices = paths[:, -1]

    # Statistics
    mean_final = float(np.mean(final_prices))
    median_final = float(np.median(final_prices))
    percentiles = {
        5: round(float(np.percentile(final_prices, 5)), 2),
        25: round(float(np.percentile(final_prices, 25)), 2),
        50: round(float(np.percentile(final_prices, 50)), 2),
        75: round(float(np.percentile(final_prices, 75)), 2),
        95: round(float(np.percentile(final_prices, 95)), 2),
    }

    # VaR from simulation
    final_returns = (final_prices - s0) / s0
    var_95 = float(np.percentile(final_returns, 5))

    # Sample paths for charting (5 representative paths)
    sample_indices = [0, simulations // 4, simulations // 2, 3 * simulations // 4, simulations - 1]
    sample_paths = []
    for idx in sample_indices:
        sample_paths.append([round(float(v), 2) for v in paths[idx].tolist()])

    return {
        "parameters": {
            "s0": s0,
            "mu_annual": mu,
            "sigma_annual": sigma,
            "days": days,
            "simulations": simulations,
        },
        "statistics": {
            "mean_final_price": round(mean_final, 2),
            "median_final_price": round(median_final, 2),
            "prob_profit": round(float(np.mean(final_prices > s0)) * 100, 1),
            "prob_loss": round(float(np.mean(final_prices < s0)) * 100, 1),
            "var_95_pct": round(float(var_95 * 100), 2),
            "expected_return_pct": round(float((mean_final - s0) / s0 * 100), 2),
        },
        "percentiles": percentiles,
        "sample_paths": sample_paths,
    }


def black_scholes(
    s: float,
    k: float,
    t: float,
    r: float,
    sigma: float,
    option_type: str = "call",
) -> dict:
    """Black-Scholes option pricing.

    Args:
        s: Spot price
        k: Strike price
        t: Time to maturity (years)
        r: Risk-free rate (annualized)
        sigma: Volatility (annualized)
        option_type: 'call' or 'put'
    """
    try:
        from scipy.stats import norm
    except ImportError:
        return {"error": "scipy is required for Black-Scholes pricing"}

    d1 = (math.log(s / k) + (r + 0.5 * sigma**2) * t) / (sigma * math.sqrt(t))
    d2 = d1 - sigma * math.sqrt(t)

    if option_type == "call":
        price = s * norm.cdf(d1) - k * math.exp(-r * t) * norm.cdf(d2)
    else:
        price = k * math.exp(-r * t) * norm.cdf(-d2) - s * norm.cdf(-d1)

    # Greeks
    delta = norm.cdf(d1) if option_type == "call" else norm.cdf(d1) - 1
    gamma = norm.pdf(d1) / (s * sigma * math.sqrt(t))
    vega = s * norm.pdf(d1) * math.sqrt(t) / 100  # per 1% vol change
    theta = (-(s * norm.pdf(d1) * sigma) / (2 * math.sqrt(t)) - r * k * math.exp(-r * t) * norm.cdf(d2 if option_type == "call" else -d2)) / 365

    return {
        "option_type": option_type,
        "inputs": {"spot": s, "strike": k, "time": t, "rate": r, "volatility": sigma},
        "price": round(price, 4),
        "d1": round(d1, 4),
        "d2": round(d2, 4),
        "greeks": {
            "delta": round(delta, 4),
            "gamma": round(gamma, 6),
            "vega": round(vega, 4),
            "theta": round(theta, 4),
        },
    }


def markowitz_optimize(
    expected_returns: list[float],
    cov_matrix: list[list[float]],
    risk_free_rate: float = 0.0,
) -> dict:
    """Markowitz mean-variance portfolio optimization.

    Finds the optimal portfolio weights that maximize the Sharpe ratio.
    Falls back to equal-weight if scipy.optimize is unavailable.
    """
    n = len(expected_returns)
    mu = np.array(expected_returns)
    sigma = np.array(cov_matrix)

    try:
        from scipy.optimize import minimize

        def neg_sharpe(w):
            port_ret = np.dot(w, mu)
            port_vol = np.sqrt(np.dot(w.T, np.dot(sigma, w)))
            return -(port_ret - risk_free_rate) / port_vol if port_vol > 0 else 0

        constraints = [{"type": "eq", "fun": lambda w: np.sum(w) - 1}]
        bounds = [(0.0, 1.0) for _ in range(n)]
        x0 = np.array([1.0 / n] * n)

        result = minimize(neg_sharpe, x0, method="SLSQP", bounds=bounds, constraints=constraints)

        if result.success:
            weights = result.x
        else:
            weights = x0
    except ImportError:
        weights = np.array([1.0 / n] * n)

    # Portfolio metrics
    port_return = float(np.dot(weights, mu))
    port_vol = float(np.sqrt(np.dot(weights.T, np.dot(sigma, weights))))
    sharpe = (port_return - risk_free_rate) / port_vol if port_vol > 0 else 0

    # Minimum variance portfolio
    try:
        from scipy.optimize import minimize

        def portfolio_vol(w):
            return np.sqrt(np.dot(w.T, np.dot(sigma, w)))

        constraints = [{"type": "eq", "fun": lambda w: np.sum(w) - 1}]
        bounds = [(0.0, 1.0) for _ in range(n)]
        min_var_result = minimize(portfolio_vol, x0, method="SLSQP", bounds=bounds, constraints=constraints)
        min_var_weights = min_var_result.x if min_var_result.success else weights
        min_var_vol = float(np.sqrt(np.dot(min_var_weights.T, np.dot(sigma, min_var_weights))))
        min_var_ret = float(np.dot(min_var_weights, mu))
    except ImportError:
        min_var_weights = weights
        min_var_vol = port_vol
        min_var_ret = port_return

    return {
        "optimal_weights": [round(float(w), 4) for w in weights],
        "optimal_return": round(port_return * 100, 2),
        "optimal_volatility": round(port_vol * 100, 2),
        "sharpe_ratio": round(sharpe, 4),
        "min_var_weights": [round(float(w), 4) for w in min_var_weights],
        "min_var_return": round(min_var_ret * 100, 2),
        "min_var_volatility": round(min_var_vol * 100, 2),
        "num_assets": n,
    }
