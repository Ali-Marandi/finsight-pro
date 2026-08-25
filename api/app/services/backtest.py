"""Backtesting Engine — Strategy simulation, performance metrics, and risk analysis.

Provides offline-capable backtesting tools for single-asset and portfolio strategies.
All computations run locally — no data leaves the machine.

Metrics: Total return, CAGR, Sharpe, Sortino, Max Drawdown, VaR, CVaR,
         Calmar ratio, Win rate, Profit factor, Expectancy.
"""

import numpy as np
from typing import Optional


def _compute_returns(prices: np.ndarray) -> np.ndarray:
    """Simple returns from price series."""
    return np.diff(prices) / prices[:-1]


def _compute_log_returns(prices: np.ndarray) -> np.ndarray:
    """Log returns from price series."""
    return np.diff(np.log(prices))


def backtest_strategy(
    prices: list[float],
    signals: list[int] | None = None,
    initial_capital: float = 1_000_000,
    commission: float = 0.001,
    slippage: float = 0.0005,
    benchmark_prices: list[float] | None = None,
 strategy_name: str = "Strategy",
) -> dict:
    """Run a full backtest on a single asset.

    Args:
        prices: Daily close prices (ascending chronological order).
        signals: Trading signals per bar. 1=buy, -1=sell, 0=hold.
                If None, uses a simple SMA crossover (20/50).
        initial_capital: Starting portfolio value.
        commission: Commission per trade (fraction of notional).
        slippage: Slippage per trade (fraction of price).
        benchmark_prices: Optional benchmark prices for comparison.
        strategy_name: Name of the strategy for reporting.
    """
    prices_arr = np.array(prices, dtype=float)
    n = len(prices_arr)
    if n < 10:
        return {"error": "Need at least 10 price points"}

    # Generate signals if not provided
    if signals is None:
        signals = _sma_crossover(prices_arr, fast=20, slow=50)
    else:
        signals = np.array(signals, dtype=int)

    # Pad signals to match prices length (signal applies to next bar)
    # signals[i] = action taken at start of bar i, affecting bar i+1
    if len(signals) < n:
        signals = np.concatenate([signals, np.zeros(n - len(signals), dtype=int)])
    signals = signals[:n]

    # Simulate portfolio
    cash = float(initial_capital)
    position = 0.0  # number of shares held
    portfolio_value = np.zeros(n)
    trades: list[dict] = []

    for i in range(n):
        current_price = prices_arr[i]
        if i > 0 and position > 0:
            # Mark-to-market
            portfolio_value[i] = cash + position * current_price
        elif i == 0:
            portfolio_value[i] = cash
        else:
            portfolio_value[i] = cash

        if i < n - 1:
            signal = signals[i]
            exec_price = current_price * (1 + slippage * (1 if signal > 0 else -1 if signal < 0 else 0))

            if signal == 1 and position == 0:
                # Buy
                shares_to_buy = cash / (exec_price * (1 + commission))
                cost = shares_to_buy * exec_price * commission
                actual_shares = (cash - cost) / exec_price
                position = actual_shares
                cash = 0.0
                trades.append({"day": int(i), "action": "BUY", "price": round(float(exec_price), 2),
                                "shares": round(float(actual_shares), 4), "pnl": 0.0})
            elif signal == -1 and position > 0:
                # Sell
                proceeds = position * exec_price
                cost = proceeds * commission
                cash = proceeds - cost
                buy_price = trades[-1]["price"] if trades else exec_price
                buy_shares = trades[-1]["shares"] if trades else position
                pnl = (exec_price - buy_price) * buy_shares - cost
                trades.append({"day": int(i), "action": "SELL", "price": round(float(exec_price), 2),
                                "shares": round(float(position), 4), "pnl": round(float(pnl), 2)})
                position = 0.0

    # Final mark-to-market
    if position > 0:
        portfolio_value[-1] = cash + position * prices_arr[-1]
    elif portfolio_value[-1] == 0:
        portfolio_value[-1] = cash

    # Compute returns
    pv_returns = _compute_returns(portfolio_value)
    pv_returns = pv_returns[~np.isnan(pv_returns)]

    if len(pv_returns) == 0:
        return {"error": "No valid return data computed"}

    # Performance metrics
    total_return = (portfolio_value[-1] / initial_capital) - 1
    trading_days = len(pv_returns)
    years = trading_days / 252
    cagr = (portfolio_value[-1] / initial_capital) ** (1 / max(years, 0.01)) - 1

    # Risk metrics
    annual_vol = float(np.std(pv_returns) * np.sqrt(252))
    sharpe = (float(np.mean(pv_returns)) * 252 - 0.04) / annual_vol if annual_vol > 0 else 0

    # Sortino (downside deviation)
    neg_returns = pv_returns[pv_returns < 0]
    downside_dev = float(np.std(neg_returns) * np.sqrt(252)) if len(neg_returns) > 0 else annual_vol
    sortino = (float(np.mean(pv_returns)) * 252 - 0.04) / downside_dev if downside_dev > 0 else 0

    # Max Drawdown
    peak = np.maximum.accumulate(portfolio_value)
    drawdown = (portfolio_value - peak) / peak
    max_drawdown = float(np.min(drawdown))
    max_dd_end_idx = int(np.argmin(drawdown))
    max_dd_start_idx = int(np.argmax(portfolio_value[:max_dd_end_idx + 1]))
    max_dd_duration = max_dd_end_idx - max_dd_start_idx

    # Calmar
    calmar = cagr / abs(max_drawdown) if max_drawdown != 0 else 0

    # VaR & CVaR (historical 95%)
    sorted_returns = np.sort(pv_returns)
    var_idx = int(0.05 * len(sorted_returns))
    var_95 = float(sorted_returns[var_idx])
    cvar_95 = float(np.mean(sorted_returns[:var_idx + 1]))

    # Trade statistics
    sell_trades = [t for t in trades if t["action"] == "SELL"]
    winning_trades = [t for t in sell_trades if t["pnl"] > 0]
    losing_trades = [t for t in sell_trades if t["pnl"] <= 0]
    win_rate = len(winning_trades) / len(sell_trades) if sell_trades else 0
    avg_win = float(np.mean([t["pnl"] for t in winning_trades])) if winning_trades else 0
    avg_loss = float(np.mean([t["pnl"] for t in losing_trades])) if losing_trades else 0
    total_profit = sum(t["pnl"] for t in winning_trades)
    total_loss = abs(sum(t["pnl"] for t in losing_trades))
    profit_factor = total_profit / total_loss if total_loss > 0 else float('inf') if total_profit > 0 else 0
    expectancy = (win_rate * avg_win - (1 - win_rate) * abs(avg_loss)) if sell_trades else 0

    # Benchmark comparison
    benchmark_data = None
    if benchmark_prices is not None and len(benchmark_prices) >= n:
        bm_arr = np.array(benchmark_prices[:n], dtype=float)
        bm_returns = _compute_returns(bm_arr)
        bm_total_return = float((bm_arr[-1] / bm_arr[0]) - 1)
        bm_cagr = float((bm_arr[-1] / bm_arr[0]) ** (1 / max(years, 0.01)) - 1)
        bm_vol = float(np.std(bm_returns) * np.sqrt(252))
        bm_sharpe = (float(np.mean(bm_returns)) * 252 - 0.04) / bm_vol if bm_vol > 0 else 0

        # Alpha & Beta
        min_len = min(len(pv_returns), len(bm_returns))
        strat_r = pv_returns[:min_len]
        bm_r = bm_returns[:min_len]
        cov_mat = np.cov(strat_r, bm_r)
        beta = float(cov_mat[0, 1] / cov_mat[1, 1]) if cov_mat[1, 1] > 0 else 0
        alpha = float(np.mean(strat_r) * 252 - (0.04 + beta * (np.mean(bm_r) * 252 - 0.04)))

        # Tracking error & Information ratio
        active_returns = strat_r - bm_r
        tracking_error = float(np.std(active_returns) * np.sqrt(252))
        info_ratio = (float(np.mean(active_returns)) * 252) / tracking_error if tracking_error > 0 else 0

        benchmark_data = {
            "total_return_pct": round(bm_total_return * 100, 2),
            "cagr_pct": round(bm_cagr * 100, 2),
            "volatility_pct": round(bm_vol * 100, 2),
            "sharpe": round(bm_sharpe, 4),
            "alpha_pct": round(alpha * 100, 2),
            "beta": round(beta, 4),
            "tracking_error_pct": round(tracking_error * 100, 2),
            "information_ratio": round(info_ratio, 4),
            "excess_return_pct": round((total_return - bm_total_return) * 100, 2),
        }

    # Sample equity curve (every Nth point for charting)
    sample_step = max(1, n // 200)
    equity_curve = portfolio_value[::sample_step].tolist()
    benchmark_curve = None
    if benchmark_prices is not None and len(benchmark_prices) >= n:
        bm_arr = np.array(benchmark_prices[:n], dtype=float)
        benchmark_curve = (bm_arr / bm_arr[0] * initial_capital)[::sample_step].tolist()

    # Drawdown series (for chart)
    dd_series = drawdown[::sample_step].tolist()

    return {
        "strategy_name": strategy_name,
        "period": {"days": trading_days, "years": round(years, 2)},
        "capital": {"initial": initial_capital, "final": round(float(portfolio_value[-1]), 2)},
        "performance": {
            "total_return_pct": round(total_return * 100, 2),
            "cagr_pct": round(cagr * 100, 2),
            "annual_volatility_pct": round(annual_vol * 100, 2),
        },
        "risk": {
            "sharpe_ratio": round(sharpe, 4),
            "sortino_ratio": round(sortino, 4),
            "max_drawdown_pct": round(max_drawdown * 100, 2),
            "max_drawdown_duration_days": max_dd_duration,
            "calmar_ratio": round(calmar, 4),
            "var_95_pct": round(var_95 * 100, 4),
            "cvar_95_pct": round(cvar_95 * 100, 4),
        },
        "trades": {
            "total": len(trades),
            "buy_count": len([t for t in trades if t["action"] == "BUY"]),
            "sell_count": len(sell_trades),
            "win_rate": round(win_rate * 100, 1),
            "profit_factor": round(profit_factor, 2) if profit_factor != float('inf') else 999.99,
            "expectancy": round(expectancy, 2),
            "avg_win": round(avg_win, 2),
            "avg_loss": round(avg_loss, 2),
            "winning_trades": len(winning_trades),
            "losing_trades": len(losing_trades),
        },
        "benchmark": benchmark_data,
        "charts": {
            "equity_curve": [round(v, 2) for v in equity_curve],
            "benchmark_curve": [round(v, 2) for v in benchmark_curve] if benchmark_curve else None,
            "drawdown_series": [round(v * 100, 2) for v in dd_series],
        },
        "trade_log": trades[-20:],  # Last 20 trades for display
    }


def portfolio_backtest(
    asset_prices: list[list[float]],
    weights: list[float] | None = None,
    rebalance_days: int = 21,
    initial_capital: float = 10_000_000,
    benchmark_prices: list[float] | None = None,
    asset_names: list[str] | None = None,
) -> dict:
    """Run a portfolio backtest with periodic rebalancing.

    Args:
        asset_prices: List of price series (one per asset), same length.
        weights: Target portfolio weights. If None, equal-weight.
        rebalance_days: Rebalance every N trading days.
        initial_capital: Starting portfolio value.
        benchmark_prices: Optional benchmark price series.
        asset_names: Optional names for the assets.
    """
    n_assets = len(asset_prices)
    if n_assets == 0:
        return {"error": "No asset prices provided"}

    # Find minimum length
    min_len = min(len(p) for p in asset_prices)
    if min_len < 10:
        return {"error": "Need at least 10 price points per asset"}

    # Trim all to same length
    prices_matrix = np.array([p[:min_len] for p in asset_prices], dtype=float)  # (assets, days)
    n_days = min_len

    if weights is None:
        weights = [1.0 / n_assets] * n_assets
    weights_arr = np.array(weights, dtype=float)
    weights_arr = weights_arr / weights_arr.sum()  # normalize

    if asset_names is None:
        asset_names = [f"Asset {i+1}" for i in range(n_assets)]

    # Simulate portfolio
    portfolio_value = np.zeros(n_days)
    portfolio_value[0] = initial_capital
    asset_values = np.zeros((n_assets, n_days))

    # Initial allocation
    for a in range(n_assets):
        asset_values[a, 0] = initial_capital * weights_arr[a]

    for d in range(1, n_days):
        # Mark-to-market: each asset grows by its daily return
        daily_returns = prices_matrix[:, d] / prices_matrix[:, d - 1]
        asset_values[:, d] = asset_values[:, d - 1] * daily_returns
        portfolio_value[d] = np.sum(asset_values[:, d])

        # Rebalance check
        if d % rebalance_days == 0:
            current_weights = asset_values[:, d] / portfolio_value[d]
            # Rebalance if any weight deviates by > 5%
            if np.max(np.abs(current_weights - weights_arr)) > 0.05:
                for a in range(n_assets):
                    asset_values[a, d] = portfolio_value[d] * weights_arr[a]

    # Portfolio returns
    pv_returns = _compute_returns(portfolio_value)
    pv_returns = pv_returns[~np.isnan(pv_returns)]

    if len(pv_returns) == 0:
        return {"error": "No valid return data"}

    # Metrics
    total_return = (portfolio_value[-1] / initial_capital) - 1
    years = len(pv_returns) / 252
    cagr = (portfolio_value[-1] / initial_capital) ** (1 / max(years, 0.01)) - 1
    annual_vol = float(np.std(pv_returns) * np.sqrt(252))
    sharpe = (float(np.mean(pv_returns)) * 252 - 0.04) / annual_vol if annual_vol > 0 else 0

    neg_returns = pv_returns[pv_returns < 0]
    downside_dev = float(np.std(neg_returns) * np.sqrt(252)) if len(neg_returns) > 0 else annual_vol
    sortino = (float(np.mean(pv_returns)) * 252 - 0.04) / downside_dev if downside_dev > 0 else 0

    peak = np.maximum.accumulate(portfolio_value)
    drawdown = (portfolio_value - peak) / peak
    max_drawdown = float(np.min(drawdown))
    calmar = cagr / abs(max_drawdown) if max_drawdown != 0 else 0

    # Per-asset contribution
    asset_returns = []
    for a in range(n_assets):
        a_returns = _compute_returns(prices_matrix[a, :min_len])
        a_total_ret = float((prices_matrix[a, -1] / prices_matrix[a, 0]) - 1)
        asset_returns.append({
            "name": asset_names[a],
            "weight_pct": round(weights_arr[a] * 100, 1),
            "total_return_pct": round(a_total_ret * 100, 2),
            "volatility_pct": round(float(np.std(a_returns) * np.sqrt(252)) * 100, 2),
        })

    # Benchmark
    benchmark_data = None
    benchmark_curve = None
    if benchmark_prices is not None and len(benchmark_prices) >= n_days:
        bm_arr = np.array(benchmark_prices[:n_days], dtype=float)
        bm_returns = _compute_returns(bm_arr)
        bm_total_return = float((bm_arr[-1] / bm_arr[0]) - 1)
        benchmark_data = {
            "total_return_pct": round(bm_total_return * 100, 2),
            "excess_return_pct": round((total_return - bm_total_return) * 100, 2),
        }
        benchmark_curve = (bm_arr / bm_arr[0] * initial_capital).tolist()

    # Chart data
    sample_step = max(1, n_days // 200)
    equity_curve = portfolio_value[::sample_step].tolist()
    dd_series = drawdown[::sample_step].tolist()

    return {
        "strategy_name": "Portfolio",
        "num_assets": n_assets,
        "asset_names": asset_names,
        "period": {"days": len(pv_returns), "years": round(years, 2)},
        "capital": {"initial": initial_capital, "final": round(float(portfolio_value[-1]), 2)},
        "weights": [round(float(w), 4) for w in weights_arr],
        "rebalance_days": rebalance_days,
        "performance": {
            "total_return_pct": round(total_return * 100, 2),
            "cagr_pct": round(cagr * 100, 2),
            "annual_volatility_pct": round(annual_vol * 100, 2),
        },
        "risk": {
            "sharpe_ratio": round(sharpe, 4),
            "sortino_ratio": round(sortino, 4),
            "max_drawdown_pct": round(max_drawdown * 100, 2),
            "calmar_ratio": round(calmar, 4),
        },
        "assets": asset_returns,
        "benchmark": benchmark_data,
        "charts": {
            "equity_curve": [round(v, 2) for v in equity_curve],
            "benchmark_curve": [round(v, 2) for v in benchmark_curve[::sample_step]] if benchmark_curve else None,
            "drawdown_series": [round(v * 100, 2) for v in dd_series],
        },
    }


def _sma_crossover(prices: np.ndarray, fast: int = 20, slow: int = 50) -> np.ndarray:
    """Generate SMA crossover signals: 1=buy, -1=sell, 0=hold."""
    n = len(prices)
    signals = np.zeros(n, dtype=int)

    if n < slow:
        return signals

    fast_sma = np.convolve(prices, np.ones(fast) / fast, mode='valid')
    slow_sma = np.convolve(prices, np.ones(slow) / slow, mode='valid')

    # Align indices
    offset_fast = n - len(fast_sma)
    offset_slow = n - len(slow_sma)
    min_len = min(len(fast_sma), len(slow_sma))

    for i in range(1, min_len):
        fast_idx = offset_fast + i
        slow_idx = offset_slow + i
        prev_fast_idx = offset_fast + i - 1
        prev_slow_idx = offset_slow + i - 1

        curr_diff = fast_sma[i] - slow_sma[i]
        prev_diff = fast_sma[i - 1] - slow_sma[i - 1]

        if prev_diff <= 0 and curr_diff > 0:
            signals[fast_idx] = 1   # Buy signal
        elif prev_diff >= 0 and curr_diff < 0:
            signals[fast_idx] = -1  # Sell signal

    return signals


def _momentum_signals(prices: np.ndarray, lookback: int = 20, threshold: float = 0.02) -> np.ndarray:
    """Generate momentum-based signals: 1=enter long, -1=exit to cash."""
    n = len(prices)
    signals = np.zeros(n, dtype=int)
    for i in range(lookback, n - 1):
        mom = (prices[i] / prices[i - lookback]) - 1
        prev_mom = (prices[i - 1] / prices[i - 1 - lookback]) - 1
        if mom > threshold and prev_mom <= threshold:
            signals[i] = 1
        elif mom < -threshold and prev_mom >= -threshold:
            signals[i] = -1
    return signals


def backtest_demo() -> dict:
    """Generate demo backtest with synthetic price data for 5 TSE stocks."""
    np.random.seed(42)
    n_days = 504  # 2 years

    names = ["خودرو", "فولاد", "پتروشیمی", "بانک", "فناوری"]
    names_en = ["Khodro", "Foolad", "Petrochem", "Bank", "Tech"]

    # Generate 5 assets with trend + noise (more realistic)
    drifts = [0.0005, 0.0003, 0.0002, 0.0001, 0.0007]  # annual ~12-18%
    vols = [0.018, 0.022, 0.020, 0.015, 0.025]
    start_prices = [950, 3200, 7800, 2100, 4500]

    all_prices = []
    for i in range(5):
        noise = np.random.normal(0, vols[i], n_days)
        # Add some regime changes for realism
        regime = np.ones(n_days)
        for r in range(4):
            start = 126 * r
            end = min(126 * (r + 1), n_days)
            regime[start:end] = 1 + np.random.uniform(-0.3, 0.3)
        log_returns = noise * regime + drifts[i]
        prices = start_prices[i] * np.exp(np.cumsum(log_returns))
        all_prices.append(prices.tolist())

    # Benchmark (market index — lower drift, lower vol)
    market_noise = np.random.normal(0, 0.013, n_days)
    market_prices = 50000 * np.exp(np.cumsum(market_noise + 0.00025))

    # Single-asset: Momentum strategy on Tech stock (separate seed for clean data)
    rng = np.random.RandomState(99)
    tech_noise = rng.normal(0, 0.022, n_days)
    tech_regime = np.ones(n_days)
    for r in range(4):
        rs = 126 * r
        re_ = min(126 * (r + 1), n_days)
        tech_regime[rs:re_] = 1 + rng.uniform(-0.3, 0.3)
    tech_prices = (4500 * np.exp(np.cumsum(tech_noise * tech_regime + 0.0006))).tolist()

    mom_signals = _momentum_signals(np.array(tech_prices), lookback=20, threshold=0.02)
    single_result = backtest_strategy(
        prices=tech_prices,
        signals=mom_signals.tolist(),
        initial_capital=1_000_000,
        commission=0.0005,
        slippage=0.0002,
        benchmark_prices=market_prices.tolist(),
        strategy_name="Momentum (20d)",
    )

    # Run portfolio backtest
    port_weights = [0.30, 0.25, 0.20, 0.15, 0.10]
    port_result = portfolio_backtest(
        asset_prices=all_prices,
        weights=port_weights,
        rebalance_days=21,
        initial_capital=10_000_000,
        benchmark_prices=market_prices.tolist(),
        asset_names=names_en,
    )

    return {
        "demo_info": {
            "description": "Demo backtest with 5 synthetic TSE stocks (2 years)",
            "assets": names_en,
            "assets_fa": names,
            "period_days": n_days,
        },
        "single_asset": single_result,
        "portfolio": port_result,
    }
