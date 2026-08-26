"""
Reinforcement Learning Engine for FinSight Pro.

Implements Q-Learning based optimal trade execution (slippage minimization),
TWAP/VWAP benchmark strategies, and dynamic portfolio allocation via RL.
All computations are offline/local using numpy only (no RL libraries).
"""

import numpy as np


def _to_native(obj):
    """Recursively convert numpy types to native Python types."""
    if isinstance(obj, np.ndarray):
        return [_to_native(x) for x in obj.tolist()]
    if isinstance(obj, (np.floating, np.float64, np.float32)):
        return round(float(obj), 6)
    if isinstance(obj, (np.integer, np.int64, np.int32)):
        return int(obj)
    if isinstance(obj, dict):
        return {k: _to_native(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_to_native(x) for x in obj]
    if isinstance(obj, (np.bool_, bool)):
        return bool(obj)
    return obj


def _round4(v):
    """Round a float to 4 decimal places."""
    return round(float(v), 4)


def _round6(v):
    """Round a float to 6 decimal places."""
    return round(float(v), 6)


# ---------------------------------------------------------------------------
# 1. Q-Learning Optimal Order Execution
# ---------------------------------------------------------------------------

def q_learning_execution(
    price_series: list,
    total_shares: int = 100000,
    n_steps: int = 300,
    learning_rate: float = 0.1,
    discount_factor: float = 0.95,
    episodes: int = 5000,
) -> dict:
    """
    Q-Learning agent for optimal order execution to minimize slippage.

    At each step the agent chooses: sell nothing, sell small, sell medium, sell large.
    State: (remaining_shares_pct, price_vs_vwap, time_progress, volatility).
    Reward: negative of execution shortfall vs VWAP.

    Returns Q-table summary, optimal execution schedule, comparison vs TWAP/VWAP.
    """
    prices = np.array(price_series, dtype=np.float64)
    n_prices = len(prices)

    # --- Discretization ---
    # Remaining shares: 5 bins (0-20%, 20-40%, ..., 80-100%)
    N_REMAIN = 5
    # Price vs VWAP: 3 bins (below, at, above)
    N_PV = 3
    # Time progress: 5 bins
    N_TIME = 5
    # Volatility: 3 bins (low, medium, high)
    N_VOL = 3

    STATE_SHAPE = (N_REMAIN, N_PV, N_TIME, N_VOL)
    # Actions: 0=none(0%), 1=small(2%), 2=medium(5%), 3=large(10%)
    N_ACTIONS = 4
    ACTION_FRACS = [0.0, 0.02, 0.05, 0.10]

    # Precompute VWAP for the price series (use overall mean as target VWAP)
    vwap_target = float(np.mean(prices))

    # Precompute rolling volatility (10-step window)
    rolling_vol = np.zeros(n_prices)
    for i in range(n_prices):
        start = max(0, i - 9)
        window = prices[start:i + 1]
        if len(window) > 1:
            rets = np.diff(window) / window[:-1]
            rolling_vol[i] = float(np.std(rets))
        else:
            rolling_vol[i] = 0.0

    vol_max = float(np.max(rolling_vol)) if np.max(rolling_vol) > 0 else 1.0

    # Initialize Q-table
    Q = np.zeros(STATE_SHAPE + (N_ACTIONS,))

    # --- Training loop ---
    for ep in range(episodes):
        # Pick a random starting index for the execution window
        if n_prices >= n_steps:
            start_idx = np.random.randint(0, n_prices - n_steps + 1)
        else:
            start_idx = 0

        exec_prices = prices[start_idx:start_idx + n_steps]
        exec_vol = rolling_vol[start_idx:start_idx + n_steps]
        remaining = total_shares
        cumulative_value = 0.0
        cumulative_shares = 0

        for t in range(n_steps):
            # Discretize state
            remain_pct = remaining / total_shares
            remain_bin = min(int(remain_pct * N_REMAIN), N_REMAIN - 1)

            # Price vs VWAP
            current_vwap = (
                float(np.mean(prices[start_idx:start_idx + t + 1])) if t > 0
                else exec_prices[0]
            )
            diff = (exec_prices[t] - current_vwap) / current_vwap if current_vwap > 0 else 0
            if diff < -0.002:
                pv_bin = 0  # below
            elif diff > 0.002:
                pv_bin = 2  # above
            else:
                pv_bin = 1  # at

            # Time progress
            time_bin = min(int((t / n_steps) * N_TIME), N_TIME - 1)

            # Volatility
            vol_norm = exec_vol[t] / vol_max if vol_max > 0 else 0
            if vol_norm < 0.33:
                vol_bin = 0
            elif vol_norm < 0.66:
                vol_bin = 1
            else:
                vol_bin = 2

            state = (remain_bin, pv_bin, time_bin, vol_bin)

            # Epsilon-greedy action selection (epsilon decays)
            epsilon = max(0.05, 1.0 - ep / (episodes * 0.6))
            if np.random.random() < epsilon:
                action = np.random.randint(N_ACTIONS)
            else:
                action = int(np.argmax(Q[state]))

            # Execute action
            sell_shares = int(remaining * ACTION_FRACS[action])
            # Ensure we don't sell more than remaining
            sell_shares = min(sell_shares, remaining)

            # Slippage reward: negative of (execution price - VWAP) per share
            if sell_shares > 0:
                slippage_per_share = exec_prices[t] - current_vwap
                reward = -slippage_per_share * sell_shares / total_shares
                cumulative_value += sell_shares * exec_prices[t]
                cumulative_shares += sell_shares
            else:
                reward = 0.0

            remaining -= sell_shares

            # Terminal penalty for not finishing
            if t == n_steps - 1 and remaining > 0:
                penalty = -0.5 * (remaining / total_shares)
                reward += penalty
                # Force sell remaining at last price
                cumulative_value += remaining * exec_prices[t]
                cumulative_shares += remaining
                remaining = 0

            # Next state
            next_remain_pct = remaining / total_shares
            next_remain_bin = min(int(next_remain_pct * N_REMAIN), N_REMAIN - 1)

            if t + 1 < n_steps:
                next_current_vwap = float(np.mean(prices[start_idx:start_idx + t + 2]))
                next_diff = (exec_prices[min(t + 1, n_steps - 1)] - next_current_vwap) / next_current_vwap
                if next_diff < -0.002:
                    next_pv_bin = 0
                elif next_diff > 0.002:
                    next_pv_bin = 2
                else:
                    next_pv_bin = 1
                next_time_bin = min(int(((t + 1) / n_steps) * N_TIME), N_TIME - 1)
                next_vol_norm = exec_vol[min(t + 1, n_steps - 1)] / vol_max if vol_max > 0 else 0
                if next_vol_norm < 0.33:
                    next_vol_bin = 0
                elif next_vol_norm < 0.66:
                    next_vol_bin = 1
                else:
                    next_vol_bin = 2
                next_state = (next_remain_bin, next_pv_bin, next_time_bin, next_vol_bin)
            else:
                next_state = state

            # Q-learning update
            best_next = float(np.max(Q[next_state]))
            Q[state + (action,)] += learning_rate * (
                reward + discount_factor * best_next - Q[state + (action,)]
            )

    # --- Extract optimal execution schedule ---
    if n_prices >= n_steps:
        eval_start = 0
    else:
        eval_start = 0
    eval_prices = prices[eval_start:eval_start + n_steps]
    eval_vol = rolling_vol[eval_start:eval_start + n_steps]

    schedule = []
    remaining = total_shares
    rl_total_value = 0.0

    for t in range(n_steps):
        remain_pct = remaining / total_shares
        remain_bin = min(int(remain_pct * N_REMAIN), N_REMAIN - 1)

        current_vwap = (
            float(np.mean(prices[eval_start:eval_start + t + 1])) if t > 0
            else eval_prices[0]
        )
        diff = (eval_prices[t] - current_vwap) / current_vwap if current_vwap > 0 else 0
        if diff < -0.002:
            pv_bin = 0
        elif diff > 0.002:
            pv_bin = 2
        else:
            pv_bin = 1

        time_bin = min(int((t / n_steps) * N_TIME), N_TIME - 1)
        vol_norm = eval_vol[t] / vol_max if vol_max > 0 else 0
        if vol_norm < 0.33:
            vol_bin = 0
        elif vol_norm < 0.66:
            vol_bin = 1
        else:
            vol_bin = 2

        state = (remain_bin, pv_bin, time_bin, vol_bin)
        action = int(np.argmax(Q[state]))
        sell_shares = int(remaining * ACTION_FRACS[action])
        sell_shares = min(sell_shares, remaining)

        if t == n_steps - 1:
            sell_shares = remaining

        rl_total_value += sell_shares * eval_prices[t]
        schedule.append({
            "step": t,
            "action": action,
            "action_label": ["none", "small", "medium", "large"][action],
            "shares_sold": sell_shares,
            "price": _round4(eval_prices[t]),
            "remaining": remaining - sell_shares,
        })
        remaining -= sell_shares

    rl_avg_price = rl_total_value / total_shares if total_shares > 0 else 0
    eval_vwap = float(np.mean(eval_prices))
    rl_slippage = eval_vwap - rl_avg_price  # positive = good for seller

    # --- TWAP benchmark ---
    twap_per_step = total_shares / n_steps
    twap_total = 0.0
    twap_schedule = []
    cum_shares = 0
    for t in range(n_steps):
        s = min(int(np.ceil(twap_per_step)), total_shares - cum_shares)
        twap_total += s * eval_prices[t]
        twap_schedule.append({"step": t, "shares": s, "price": _round4(eval_prices[t])})
        cum_shares += s
    twap_avg = twap_total / total_shares if total_shares > 0 else 0
    twap_slippage = eval_vwap - twap_avg

    # --- VWAP benchmark (sell proportional to inverse volatility - more in low vol) ---
    vol_weights = 1.0 / (eval_vol + 1e-8)
    vol_weights = vol_weights / np.sum(vol_weights)
    vwap_total = 0.0
    vwap_schedule = []
    cum_s = 0
    for t in range(n_steps):
        s = int(round(total_shares * vol_weights[t]))
        s = min(s, total_shares - cum_s)
        vwap_total += s * eval_prices[t]
        vwap_schedule.append({"step": t, "shares": s, "price": _round4(eval_prices[t])})
        cum_s += s
    # Fix rounding remainder
    if cum_s < total_shares:
        vwap_total += (total_shares - cum_s) * eval_prices[-1]
    vwap_avg = vwap_total / total_shares if total_shares > 0 else 0
    vwap_slippage = eval_vwap - vwap_avg

    # --- Q-table summary ---
    q_summary = {
        "shape": list(STATE_SHAPE) + [N_ACTIONS],
        "mean_q_value": _round4(float(np.mean(Q))),
        "max_q_value": _round4(float(np.max(Q))),
        "min_q_value": _round4(float(np.min(Q))),
        "std_q_value": _round4(float(np.std(Q))),
        "non_zero_entries": int(np.sum(Q != 0)),
        "total_entries": int(np.prod(STATE_SHAPE) * N_ACTIONS),
        "action_labels": ["none", "small", "medium", "large"],
    }

    comparison = {
        "rl_avg_execution_price": _round4(rl_avg_price),
        "twap_avg_execution_price": _round4(twap_avg),
        "vwap_avg_execution_price": _round4(vwap_avg),
        "benchmark_vwap": _round4(eval_vwap),
        "rl_slippage_vs_vwap": _round4(rl_slippage),
        "twap_slippage_vs_vwap": _round4(twap_slippage),
        "vwap_strategy_slippage_vs_vwap": _round4(vwap_slippage),
        "rl_advantage_vs_twap_bps": _round4((rl_avg_price - twap_avg) / twap_avg * 10000),
        "rl_advantage_vs_vwap_bps": _round4((rl_avg_price - vwap_avg) / vwap_avg * 10000),
    }

    slippage_metrics = {
        "rl_total_slippage": _round6(rl_slippage * total_shares),
        "twap_total_slippage": _round6(twap_slippage * total_shares),
        "vwap_total_slippage": _round6(vwap_slippage * total_shares),
        "rl_improvement_over_twap_pct": _round4(
            (rl_slippage - twap_slippage) / abs(twap_slippage) * 100
        ) if abs(twap_slippage) > 1e-10 else 0.0,
        "rl_improvement_over_vwap_pct": _round4(
            (rl_slippage - vwap_slippage) / abs(vwap_slippage) * 100
        ) if abs(vwap_slippage) > 1e-10 else 0.0,
    }

    return _to_native({
        "q_table_summary": q_summary,
        "optimal_execution_schedule": schedule,
        "strategy_comparison": comparison,
        "slippage_metrics": slippage_metrics,
        "parameters": {
            "total_shares": total_shares,
            "n_steps": n_steps,
            "learning_rate": learning_rate,
            "discount_factor": discount_factor,
            "episodes": episodes,
            "n_price_points": n_prices,
        },
    })


# ---------------------------------------------------------------------------
# 2. TWAP / VWAP Benchmark Strategies
# ---------------------------------------------------------------------------

def twap_vwap_strategy(
    price_series: list,
    volumes: list | None = None,
    total_shares: int = 100000,
    n_steps: int = 300,
) -> dict:
    """
    Implement TWAP and VWAP execution strategies as benchmarks.

    TWAP: equal slices over time.
    VWAP: slices proportional to volume (if provided) or inverse volatility.

    Returns execution schedules, average prices, and slippage vs ideal VWAP.
    """
    prices = np.array(price_series, dtype=np.float64)
    n_prices = len(prices)

    # Use the first n_steps prices or resample
    if n_prices >= n_steps:
        # Sample n_steps evenly spaced points
        indices = np.linspace(0, n_prices - 1, n_steps, dtype=int)
        exec_prices = prices[indices]
        if volumes is not None:
            vols = np.array(volumes, dtype=np.float64)
            exec_vols = vols[indices]
        else:
            exec_vols = None
    else:
        exec_prices = prices
        exec_vols = np.array(volumes, dtype=np.float64) if volumes is not None else None

    actual_steps = len(exec_prices)
    ideal_vwap = float(np.average(exec_prices, weights=exec_vols)) if exec_vols is not None else float(np.mean(exec_prices))

    # --- TWAP ---
    twap_per_step = total_shares / actual_steps
    twap_schedule = []
    twap_total_value = 0.0
    twap_cum = 0
    for t in range(actual_steps):
        s = min(int(np.ceil(twap_per_step)), total_shares - twap_cum)
        twap_total_value += s * exec_prices[t]
        twap_schedule.append({
            "step": t,
            "shares": s,
            "price": _round4(exec_prices[t]),
            "cumulative_shares": twap_cum + s,
        })
        twap_cum += s
    twap_avg_price = twap_total_value / total_shares if total_shares > 0 else 0
    twap_slippage = ideal_vwap - twap_avg_price

    # --- VWAP ---
    if exec_vols is not None and np.sum(exec_vols) > 0:
        vol_weights = exec_vols / np.sum(exec_vols)
    else:
        # Use inverse of local volatility as proxy
        rolling_vol = np.zeros(actual_steps)
        for i in range(actual_steps):
            start = max(0, i - 9)
            w = exec_prices[start:i + 1]
            if len(w) > 1:
                r = np.diff(w) / w[:-1]
                rolling_vol[i] = float(np.std(r))
        vol_weights = 1.0 / (rolling_vol + 1e-8)
        vol_weights = vol_weights / np.sum(vol_weights)

    vwap_schedule = []
    vwap_total_value = 0.0
    vwap_cum = 0
    for t in range(actual_steps):
        s = int(round(total_shares * vol_weights[t]))
        s = min(s, total_shares - vwap_cum)
        vwap_total_value += s * exec_prices[t]
        vwap_schedule.append({
            "step": t,
            "shares": s,
            "price": _round4(exec_prices[t]),
            "weight": _round6(vol_weights[t]),
            "cumulative_shares": vwap_cum + s,
        })
        vwap_cum += s
    if vwap_cum < total_shares:
        vwap_total_value += (total_shares - vwap_cum) * exec_prices[-1]
    vwap_avg_price = vwap_total_value / total_shares if total_shares > 0 else 0
    vwap_slippage = ideal_vwap - vwap_avg_price

    # --- Comparison ---
    comparison = {
        "ideal_vwap": _round4(ideal_vwap),
        "twap_avg_price": _round4(twap_avg_price),
        "vwap_avg_price": _round4(vwap_avg_price),
        "twap_slippage_vs_ideal": _round4(twap_slippage),
        "vwap_slippage_vs_ideal": _round4(vwap_slippage),
        "twap_advantage_bps": _round4((twap_avg_price - vwap_avg_price) / vwap_avg_price * 10000) if vwap_avg_price != 0 else 0.0,
        "price_range": [_round4(float(np.min(exec_prices))), _round4(float(np.max(exec_prices)))],
        "price_std": _round4(float(np.std(exec_prices))),
    }

    slippage_detail = {
        "twap_total_slippage_value": _round6(twap_slippage * total_shares),
        "vwap_total_slippage_value": _round6(vwap_slippage * total_shares),
        "twap_slippage_bps": _round4(twap_slippage / ideal_vwap * 10000) if ideal_vwap != 0 else 0.0,
        "vwap_slippage_bps": _round4(vwap_slippage / ideal_vwap * 10000) if ideal_vwap != 0 else 0.0,
    }

    return _to_native({
        "twap_schedule": twap_schedule,
        "vwap_schedule": vwap_schedule,
        "comparison": comparison,
        "slippage_detail": slippage_detail,
        "parameters": {
            "total_shares": total_shares,
            "n_steps": n_steps,
            "actual_execution_steps": actual_steps,
            "volume_provided": volumes is not None,
        },
    })


# ---------------------------------------------------------------------------
# 3. Portfolio RL Allocation
# ---------------------------------------------------------------------------

def portfolio_rl_allocation(
    returns_matrix: list,
    n_assets: int | None = None,
    episodes: int = 3000,
) -> dict:
    """
    Simplified Q-Learning for dynamic portfolio allocation between N assets.

    State: (weight discretization index, recent return pattern, current Sharpe bucket).
    Action: shift weight between assets.
    Reward: portfolio return - risk_penalty.

    Compares learned policy vs equal-weight and buy-and-hold.
    """
    returns = np.array(returns_matrix, dtype=np.float64)
    n_a, T = returns.shape
    if n_assets is not None:
        n_a = n_assets
    n_a = min(n_a, returns.shape[0])
    returns = returns[:n_a, :]

    # --- Discretization ---
    # Weight state: 5 levels for the dominant asset weight
    N_WEIGHT = 5
    # Return pattern: 3^N_A possibilities (simplified to N_A * 3 = per-asset up/down/flat)
    N_PATTERN = 3  # per asset: 0=down, 1=flat, 2=up
    # Sharpe bucket: 3
    N_SHARPE = 3

    STATE_SHAPE = (N_WEIGHT, N_PATTERN, N_SHARPE)
    # Actions: for 3 assets, allow pairwise shifts
    # Action encoding: (from_asset, to_asset, amount_idx)
    # Simplified: for each pair, 3 amounts; plus hold
    # With n_a assets: hold + n_a*(n_a-1) shift directions * 3 amounts
    pair_shifts = []
    for i in range(n_a):
        for j in range(n_a):
            if i != j:
                pair_shifts.append((i, j))
    n_pairs = len(pair_shifts)
    SHIFT_AMTS = [0.05, 0.10, 0.20]  # fraction of portfolio
    # Actions: 0 = hold, then for each (from, to, amount)
    N_ACTIONS = 1 + n_pairs * len(SHIFT_AMTS)

    Q = np.zeros(STATE_SHAPE + (N_ACTIONS,))

    # --- Helper: compute portfolio metrics ---
    def _sharpe(weights_arr, rets_window):
        w = np.asarray(weights_arr)[:, None]
        port_ret = np.sum(w * rets_window, axis=0)
        if np.std(port_ret) < 1e-10:
            return 0.0
        return float(np.mean(port_ret) / np.std(port_ret) * np.sqrt(252))

    # --- Training ---
    lr = 0.1
    gamma = 0.95
    risk_penalty = 2.0  # multiplier for variance penalty
    lookback = 5  # days for recent return pattern

    for ep in range(episodes):
        weights = np.ones(n_a) / n_a
        ep_returns = []

        for t in range(lookback, T - 1):
            # Discretize state
            # Weight state: max weight index
            max_w = float(np.max(weights))
            w_bin = min(int(max_w * N_WEIGHT), N_WEIGHT - 1)

            # Recent return pattern: majority direction
            recent = returns[:, t - lookback:t]
            mean_ret = np.mean(recent, axis=1)
            # Encode as sum of (up=2, flat=1, down=0) per asset
            pattern_sum = 0
            for a in range(n_a):
                if mean_ret[a] > 0.001:
                    pattern_sum += 2 * (3 ** a)
                elif mean_ret[a] < -0.001:
                    pattern_sum += 0 * (3 ** a)
                else:
                    pattern_sum += 1 * (3 ** a)
            # Reduce to N_PATTERN bins
            p_bin = pattern_sum % N_PATTERN

            # Sharpe bucket
            window_rets = returns[:, max(0, t - 20):t]
            sh = _sharpe(weights, window_rets)
            if sh < 0:
                s_bin = 0
            elif sh < 1.0:
                s_bin = 1
            else:
                s_bin = 2

            state = (w_bin, p_bin, s_bin)

            # Epsilon-greedy
            epsilon = max(0.05, 1.0 - ep / (episodes * 0.5))
            if np.random.random() < epsilon:
                action = np.random.randint(N_ACTIONS)
            else:
                action = int(np.argmax(Q[state]))

            # Apply action
            new_weights = weights.copy()
            if action > 0:
                act_idx = action - 1
                pair_idx = act_idx // len(SHIFT_AMTS)
                amt_idx = act_idx % len(SHIFT_AMTS)
                from_a, to_a = pair_shifts[pair_idx]
                shift = SHIFT_AMTS[amt_idx]
                shift = min(shift, new_weights[from_a])
                new_weights[from_a] -= shift
                new_weights[to_a] += shift
            # Normalize to sum to 1
            new_weights = np.maximum(new_weights, 0.01)
            new_weights = new_weights / np.sum(new_weights)

            # Compute reward: next day portfolio return - risk penalty
            next_day_ret = float(np.dot(new_weights, returns[:, t + 1]))
            window_rets_next = returns[:, max(0, t - 19):t + 1]
            port_rets_window = np.sum(new_weights[:, None] * window_rets_next, axis=0)
            var_penalty = risk_penalty * float(np.var(port_rets_window))
            reward = next_day_ret - var_penalty

            # Next state
            next_max_w = float(np.max(new_weights))
            next_w_bin = min(int(next_max_w * N_WEIGHT), N_WEIGHT - 1)

            if t + 1 < T - 1:
                next_recent = returns[:, t - lookback + 1:t + 1]
                next_mean_ret = np.mean(next_recent, axis=1)
                next_pattern_sum = 0
                for a in range(n_a):
                    if next_mean_ret[a] > 0.001:
                        next_pattern_sum += 2 * (3 ** a)
                    elif next_mean_ret[a] < -0.001:
                        next_pattern_sum += 0 * (3 ** a)
                    else:
                        next_pattern_sum += 1 * (3 ** a)
                next_p_bin = next_pattern_sum % N_PATTERN

                next_window = returns[:, max(0, t - 18):t + 2]
                next_sh = _sharpe(new_weights, next_window)
                if next_sh < 0:
                    next_s_bin = 0
                elif next_sh < 1.0:
                    next_s_bin = 1
                else:
                    next_s_bin = 2
                next_state = (next_w_bin, next_p_bin, next_s_bin)
            else:
                next_state = state

            # Q-update
            best_next = float(np.max(Q[next_state]))
            Q[state + (action,)] += lr * (
                reward + gamma * best_next - Q[state + (action,)]
            )

            weights = new_weights
            ep_returns.append(next_day_ret)

    # --- Extract learned policy & evaluate ---
    # Evaluate on the full period
    rl_weights_history = []
    weights = np.ones(n_a) / n_a
    rl_daily_returns = []

    for t in range(lookback, T):
        max_w = float(np.max(weights))
        w_bin = min(int(max_w * N_WEIGHT), N_WEIGHT - 1)
        recent = returns[:, t - lookback:t]
        mean_ret = np.mean(recent, axis=1)
        pattern_sum = 0
        for a in range(n_a):
            if mean_ret[a] > 0.001:
                pattern_sum += 2 * (3 ** a)
            elif mean_ret[a] < -0.001:
                pattern_sum += 0 * (3 ** a)
            else:
                pattern_sum += 1 * (3 ** a)
        p_bin = pattern_sum % N_PATTERN
        window_rets = returns[:, max(0, t - 20):t]
        sh = _sharpe(weights, window_rets)
        if sh < 0:
            s_bin = 0
        elif sh < 1.0:
            s_bin = 1
        else:
            s_bin = 2

        state = (w_bin, p_bin, s_bin)
        action = int(np.argmax(Q[state]))

        new_weights = weights.copy()
        if action > 0:
            act_idx = action - 1
            pair_idx = act_idx // len(SHIFT_AMTS)
            amt_idx = act_idx % len(SHIFT_AMTS)
            from_a, to_a = pair_shifts[pair_idx]
            shift = SHIFT_AMTS[amt_idx]
            shift = min(shift, new_weights[from_a])
            new_weights[from_a] -= shift
            new_weights[to_a] += shift
        new_weights = np.maximum(new_weights, 0.01)
        new_weights = new_weights / np.sum(new_weights)

        rl_weights_history.append([_round4(float(w)) for w in new_weights])
        if t < T:
            rl_daily_returns.append(float(np.dot(new_weights, returns[:, t])))
        weights = new_weights

    # --- Equal-weight benchmark ---
    ew_weights = np.ones(n_a) / n_a
    ew_daily = [float(np.dot(ew_weights, returns[:, t])) for t in range(T)]

    # --- Buy-and-hold benchmark ---
    # Start equal weight, drift with returns
    bh_weights = np.ones(n_a) / n_a
    bh_daily = []
    for t in range(T):
        bh_daily.append(float(np.dot(bh_weights, returns[:, t])))
        if t < T - 1:
            # Drift weights by returns
            bh_weights = bh_weights * (1 + returns[:, t])
            bh_weights = bh_weights / np.sum(bh_weights)

    # --- Compute metrics ---
    def _calc_metrics(daily_rets):
        r = np.array(daily_rets)
        mean_r = float(np.mean(r))
        std_r = float(np.std(r))
        sharpe = mean_r / std_r * np.sqrt(252) if std_r > 1e-10 else 0.0
        cum_ret = float(np.prod(1 + r) - 1)
        # Max drawdown
        cumwealth = np.cumprod(1 + r)
        peak = np.maximum.accumulate(cumwealth)
        drawdown = (cumwealth - peak) / peak
        max_dd = float(np.min(drawdown))
        # Calmar
        calmar = cum_ret / abs(max_dd) if abs(max_dd) > 1e-10 else 0.0
        return {
            "annualized_return_pct": _round4(mean_r * 252 * 100),
            "annualized_volatility_pct": _round4(std_r * np.sqrt(252) * 100),
            "sharpe_ratio": _round4(sharpe),
            "cumulative_return_pct": _round4(cum_ret * 100),
            "max_drawdown_pct": _round4(max_dd * 100),
            "calmar_ratio": _round4(calmar),
            "mean_daily_return": _round6(mean_r),
            "daily_volatility": _round6(std_r),
        }

    rl_metrics = _calc_metrics(rl_daily_returns)
    ew_metrics = _calc_metrics(ew_daily)
    bh_metrics = _calc_metrics(bh_daily)

    # Q-table summary
    q_summary = {
        "shape": list(STATE_SHAPE) + [N_ACTIONS],
        "mean_q_value": _round4(float(np.mean(Q))),
        "max_q_value": _round4(float(np.max(Q))),
        "min_q_value": _round4(float(np.min(Q))),
        "non_zero_entries": int(np.sum(Q != 0)),
        "total_entries": int(np.prod(STATE_SHAPE) * N_ACTIONS),
        "n_actions": N_ACTIONS,
        "action_description": (
            "0=hold, then (from_asset, to_asset, shift_amount) for all pairs"
        ),
    }

    # Final weights
    final_weights = {f"asset_{i}": _round4(float(weights[i])) for i in range(n_a)}

    return _to_native({
        "q_table_summary": q_summary,
        "learned_policy": {
            "final_weights": final_weights,
            "weights_history_sample": rl_weights_history[:20],
            "n_rebalance_days": len(rl_weights_history),
        },
        "rl_performance": rl_metrics,
        "equal_weight_performance": ew_metrics,
        "buy_and_hold_performance": bh_metrics,
        "sharpe_comparison": {
            "rl": rl_metrics["sharpe_ratio"],
            "equal_weight": ew_metrics["sharpe_ratio"],
            "buy_and_hold": bh_metrics["sharpe_ratio"],
        },
        "parameters": {
            "n_assets": n_a,
            "n_days": T,
            "episodes": episodes,
            "lookback_days": lookback,
            "risk_penalty": risk_penalty,
            "shift_amounts": SHIFT_AMTS,
        },
    })


# ---------------------------------------------------------------------------
# 4. Comprehensive Demo
# ---------------------------------------------------------------------------

def reinforcement_learning_demo() -> dict:
    """
    Demo with a TSE stock price series (504 days, realistic volatility).

    Shows Q-learning execution vs TWAP vs VWAP for selling 100,000 shares
    over 30 minutes (300 steps with simulated intraday prices).
    Also shows portfolio RL allocation across 3 assets.
    """
    np.random.seed(42)

    # --- Generate TSE-like daily price series (504 days ~ 2 years) ---
    days = 504
    s0 = 12500.0  # Starting price in IRR (TSE typical)
    mu_daily = 0.0006  # ~15% annualized
    sigma_daily = 0.018  # ~28% annualized (realistic TSE volatility)

    daily_prices = np.zeros(days)
    daily_prices[0] = s0
    Z = np.random.standard_normal(days)
    for t in range(1, days):
        daily_prices[t] = daily_prices[t - 1] * np.exp(
            (mu_daily - 0.5 * sigma_daily**2) + sigma_daily * Z[t]
        )

    # --- Simulate 300-step intraday price series (30 minutes, 6-second intervals) ---
    n_intraday = 300
    base_price = daily_prices[-1]
    intraday_sigma = 0.0003  # per-step volatility
    intraday_prices = np.zeros(n_intraday)
    intraday_prices[0] = base_price
    # Add a slight downtrend (we're selling) and mean-reverting component
    for t in range(1, n_intraday):
        drift = -0.00002  # slight downward drift (market impact simulation)
        noise = intraday_sigma * np.random.standard_normal()
        # Mean reversion toward base_price
        mr = 0.001 * (base_price - intraday_prices[t - 1]) / base_price
        intraday_prices[t] = intraday_prices[t - 1] * (1 + drift + mr + noise)

    # --- Simulate intraday volume profile (U-shaped) ---
    time_idx = np.arange(n_intraday)
    volume_profile = (
        0.3 * np.exp(-((time_idx - 30) / 40) ** 2)  # opening spike
        + 0.5 * np.exp(-((time_idx - 250) / 50) ** 2)  # closing spike
        + 0.2 * np.ones(n_intraday)  # base volume
    )
    volume_profile += 0.1 * np.random.randn(n_intraday)  # noise
    volume_profile = np.maximum(volume_profile, 0.01)
    volumes = volume_profile.tolist()

    # --- 1. Q-Learning Execution ---
    ql_result = q_learning_execution(
        price_series=intraday_prices.tolist(),
        total_shares=100000,
        n_steps=100,
        learning_rate=0.1,
        discount_factor=0.95,
        episodes=500,
    )

    # --- 2. TWAP/VWAP Strategy ---
    tv_result = twap_vwap_strategy(
        price_series=intraday_prices.tolist(),
        volumes=volumes,
        total_shares=100000,
        n_steps=100,
    )

    # --- 3. Generate 3-asset returns matrix for portfolio RL ---
    n_assets = 3
    asset_names = ["Khodro", "Sepid", "Melat"]  # TSE-relevant names
    # Different characteristics per asset
    asset_mu = [0.0005, 0.0008, 0.0003]  # daily expected returns
    asset_sigma = [0.018, 0.025, 0.012]  # daily volatilities
    # Correlation structure
    corr_matrix = np.array([
        [1.0, 0.4, 0.2],
        [0.4, 1.0, 0.3],
        [0.2, 0.3, 1.0],
    ])
    L = np.linalg.cholesky(corr_matrix)

    raw_Z = np.random.standard_normal((n_assets, days))
    correlated_Z = L @ raw_Z

    returns_matrix = np.zeros((n_assets, days))
    for a in range(n_assets):
        for t in range(1, days):
            returns_matrix[a, t] = (
                asset_mu[a] + asset_sigma[a] * correlated_Z[a, t]
            )
        returns_matrix[a, 0] = asset_mu[a]

    port_result = portfolio_rl_allocation(
        returns_matrix=returns_matrix.tolist(),
        n_assets=3,
        episodes=300,
    )

    # --- Daily price summary ---
    daily_summary = {
        "start_date_price": _round4(daily_prices[0]),
        "end_date_price": _round4(daily_prices[-1]),
        "mean_price": _round4(float(np.mean(daily_prices))),
        "std_price": _round4(float(np.std(daily_prices))),
        "min_price": _round4(float(np.min(daily_prices))),
        "max_price": _round4(float(np.max(daily_prices))),
        "total_return_pct": _round4(float((daily_prices[-1] / daily_prices[0] - 1) * 100)),
        "annualized_vol_pct": _round4(float(sigma_daily * np.sqrt(252) * 100)),
        "n_days": days,
    }

    # --- Intraday summary ---
    intraday_summary = {
        "base_price": _round4(base_price),
        "final_price": _round4(intraday_prices[-1]),
        "mean_price": _round4(float(np.mean(intraday_prices))),
        "std_price": _round4(float(np.std(intraday_prices))),
        "price_range": [_round4(float(np.min(intraday_prices))), _round4(float(np.max(intraday_prices)))],
        "n_steps": n_intraday,
        "time_window_minutes": 30,
    }

    return {
        "demo_title": "FinSight Pro — Reinforcement Learning Engine Demo (TSE)",
        "description": (
            "Comprehensive RL demo using Tehran Stock Exchange data: "
            "Q-learning optimal execution of 100,000 shares over 30 minutes (300 steps), "
            "TWAP/VWAP benchmarks, and dynamic 3-asset portfolio allocation. "
            "Simulated 504-day TSE price series at 12,500 IRR with 28% annualized volatility."
        ),
        "daily_price_series_summary": daily_summary,
        "intraday_execution_summary": intraday_summary,
        "asset_names": asset_names,
        "q_learning_execution": ql_result,
        "twap_vwap_strategy": tv_result,
        "portfolio_rl_allocation": port_result,
    }
