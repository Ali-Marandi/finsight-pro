"""
Stochastic Calculus Engine for FinSight Pro.

Implements GBM (Itô), Heston stochastic volatility, Black-Scholes Greeks surfaces,
barrier option Monte Carlo pricing, and Merton jump-diffusion models.
All computations are offline/local using numpy and scipy.
"""

import numpy as np
from scipy import stats


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


# ---------------------------------------------------------------------------
# 1. Itô GBM Simulation
# ---------------------------------------------------------------------------

def ito_simulation(
    s0: float = 1000.0,
    mu: float = 0.15,
    sigma: float = 0.25,
    days: int = 252,
    n_paths: int = 1000,
    dt: float | None = None,
) -> dict:
    """
    Simulate geometric Brownian motion paths using Itô's Lemma.

    dS = mu*S*dt + sigma*S*dW

    Returns paths matrix, terminal statistics, and drift/diffusion decomposition.
    """
    if dt is None:
        dt = 1.0 / 252.0

    n_steps = days
    S = np.zeros((n_paths, n_steps + 1))
    S[:, 0] = s0

    drift_component = np.zeros((n_paths, n_steps))
    diffusion_component = np.zeros((n_paths, n_steps))

    Z = np.random.standard_normal((n_paths, n_steps))
    dW = np.sqrt(dt) * Z

    for t in range(n_steps):
        S_t = S[:, t]
        drift = mu * S_t * dt
        diffusion = sigma * S_t * dW[:, t]
        S[:, t + 1] = S_t + drift + diffusion
        drift_component[:, t] = drift
        diffusion_component[:, t] = diffusion

    final_prices = S[:, -1]
    log_returns = np.log(S[:, -1] / s0)

    statistics = {
        "mean_final_price": _round4(np.mean(final_prices)),
        "std_final_price": _round4(np.std(final_prices)),
        "median_final_price": _round4(np.median(final_prices)),
        "percentile_5": _round4(np.percentile(final_prices, 5)),
        "percentile_25": _round4(np.percentile(final_prices, 25)),
        "percentile_75": _round4(np.percentile(final_prices, 75)),
        "percentile_95": _round4(np.percentile(final_prices, 95)),
        "min_final_price": _round4(np.min(final_prices)),
        "max_final_price": _round4(np.max(final_prices)),
        "mean_log_return": _round4(np.mean(log_returns)),
        "std_log_return": _round4(np.std(log_returns)),
        "theoretical_mean": _round4(s0 * np.exp(mu * days * dt)),
        "theoretical_std": _round4(
            s0 * np.exp(mu * days * dt)
            * np.sqrt(np.exp(sigma**2 * days * dt) - 1)
        ),
    }

    # Per-step mean drift and diffusion for plotting
    mean_drift = np.mean(drift_component, axis=0).tolist()
    mean_diffusion = np.mean(diffusion_component, axis=0).tolist()
    std_diffusion = np.std(diffusion_component, axis=0).tolist()

    return _to_native({
        "paths": S.tolist(),
        "statistics": statistics,
        "drift_diffusion": {
            "mean_drift_per_step": mean_drift,
            "mean_diffusion_per_step": mean_diffusion,
            "std_diffusion_per_step": std_diffusion,
        },
        "parameters": {
            "s0": s0, "mu": mu, "sigma": sigma,
            "days": days, "n_paths": n_paths, "dt": dt,
        },
    })


# ---------------------------------------------------------------------------
# 2. Heston Stochastic Volatility Model
# ---------------------------------------------------------------------------

def heston_model(
    s0: float = 1000.0,
    v0: float = 0.04,
    kappa: float = 2.0,
    theta: float = 0.04,
    xi: float = 0.3,
    rho: float = -0.7,
    days: int = 252,
    n_paths: int = 1000,
) -> dict:
    """
    Heston stochastic volatility model.

    dS = mu*S*dt + sqrt(v)*S*dW1
    dv = kappa*(theta - v)*dt + xi*sqrt(v)*dW2
    Corr(dW1, dW2) = rho
    """
    dt = 1.0 / 252.0
    n_steps = days
    mu = 0.15  # risk-neutral drift for asset

    S = np.zeros((n_paths, n_steps + 1))
    V = np.zeros((n_paths, n_steps + 1))
    S[:, 0] = s0
    V[:, 0] = v0

    # Generate correlated Brownian motions via Cholesky
    Z1 = np.random.standard_normal((n_paths, n_steps))
    Z2 = np.random.standard_normal((n_paths, n_steps))
    dW1 = np.sqrt(dt) * Z1
    dW2 = np.sqrt(dt) * (rho * Z1 + np.sqrt(1 - rho**2) * Z2)

    for t in range(n_steps):
        sqrt_v = np.sqrt(np.maximum(V[:, t], 0))
        S[:, t + 1] = S[:, t] + mu * S[:, t] * dt + sqrt_v * S[:, t] * dW1[:, t]
        V[:, t + 1] = (
            V[:, t]
            + kappa * (theta - V[:, t]) * dt
            + xi * sqrt_v * dW2[:, t]
        )
        # Floor variance at zero (full truncation)
        V[:, t + 1] = np.maximum(V[:, t + 1], 0)

    final_prices = S[:, -1]
    final_vols = np.sqrt(V[:, -1])
    mean_vol_path = np.mean(np.sqrt(V), axis=0)

    vol_stats = {
        "mean_terminal_vol": _round4(np.mean(final_vols)),
        "std_terminal_vol": _round4(np.std(final_vols)),
        "min_terminal_vol": _round4(np.min(final_vols)),
        "max_terminal_vol": _round4(np.max(final_vols)),
        "vol_of_vol": _round4(np.std(np.sqrt(V), axis=1).mean()),
        "mean_vol_path_initial": _round4(mean_vol_path[0]),
        "mean_vol_path_final": _round4(mean_vol_path[-1]),
    }

    asset_stats = {
        "mean_final_price": _round4(np.mean(final_prices)),
        "std_final_price": _round4(np.std(final_prices)),
        "median_final_price": _round4(np.median(final_prices)),
        "percentile_5": _round4(np.percentile(final_prices, 5)),
        "percentile_95": _round4(np.percentile(final_prices, 95)),
    }

    return _to_native({
        "asset_paths": S.tolist(),
        "volatility_paths": V.tolist(),
        "mean_volatility_path": mean_vol_path.tolist(),
        "asset_terminal_stats": asset_stats,
        "volatility_stats": vol_stats,
        "parameters": {
            "s0": s0, "v0": v0, "kappa": kappa, "theta": theta,
            "xi": xi, "rho": rho, "days": days, "n_paths": n_paths,
        },
    })


# ---------------------------------------------------------------------------
# 3. Option Greeks Surface (Black-Scholes)
# ---------------------------------------------------------------------------

def _bs_d1(S, K, T, r, sigma):
    return (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))


def _bs_price(S, K, T, r, sigma, option_type="call"):
    if T <= 0 or sigma <= 0:
        intrinsic = np.maximum(S - K, 0) if option_type == "call" else np.maximum(K - S, 0)
        return intrinsic
    d1 = _bs_d1(S, K, T, r, sigma)
    d2 = d1 - sigma * np.sqrt(T)
    if option_type == "call":
        return S * stats.norm.cdf(d1) - K * np.exp(-r * T) * stats.norm.cdf(d2)
    else:
        return K * np.exp(-r * T) * stats.norm.cdf(-d2) - S * stats.norm.cdf(-d1)


def option_greeks_surface(
    s_min: float = 500.0,
    s_max: float = 1500.0,
    n_spot_points: int = 20,
    t_min: float = 0.02,
    t_max: float = 1.0,
    n_time_points: int = 15,
    strike: float = 1000.0,
    rate: float = 0.05,
    vol: float = 0.25,
) -> dict:
    """
    Compute full Black-Scholes Greeks surfaces over a 2D grid of spot and time.

    Returns Delta, Gamma, Theta, Vega, Rho for both calls and puts.
    """
    S_grid = np.linspace(s_min, s_max, n_spot_points)
    T_grid = np.linspace(t_min, t_max, n_time_points)
    K = strike
    r = rate
    sig = vol

    delta_call = np.zeros((n_time_points, n_spot_points))
    delta_put = np.zeros((n_time_points, n_spot_points))
    gamma_surf = np.zeros((n_time_points, n_spot_points))
    theta_call = np.zeros((n_time_points, n_spot_points))
    theta_put = np.zeros((n_time_points, n_spot_points))
    vega_surf = np.zeros((n_time_points, n_spot_points))
    rho_call = np.zeros((n_time_points, n_spot_points))
    rho_put = np.zeros((n_time_points, n_spot_points))
    price_call = np.zeros((n_time_points, n_spot_points))
    price_put = np.zeros((n_time_points, n_spot_points))

    for i, T in enumerate(T_grid):
        for j, S in enumerate(S_grid):
            if T <= 1e-10 or sig <= 1e-10:
                continue
            sqrt_T = np.sqrt(T)
            d1 = (np.log(S / K) + (r + 0.5 * sig**2) * T) / (sig * sqrt_T)
            d2 = d1 - sig * sqrt_T
            nd1 = stats.norm.pdf(d1)
            Nd1 = stats.norm.cdf(d1)
            Nd2 = stats.norm.cdf(d2)
            Nmd1 = stats.norm.cdf(-d1)
            Nmd2 = stats.norm.cdf(-d2)
            exp_rt = np.exp(-r * T)

            delta_call[i, j] = Nd1
            delta_put[i, j] = Nd1 - 1.0
            gamma_surf[i, j] = nd1 / (S * sig * sqrt_T)
            theta_call[i, j] = (
                -(S * nd1 * sig) / (2 * sqrt_T)
                - r * K * exp_rt * Nd2
            ) / 365.0  # per day
            theta_put[i, j] = (
                -(S * nd1 * sig) / (2 * sqrt_T)
                + r * K * exp_rt * Nmd2
            ) / 365.0
            vega_surf[i, j] = S * nd1 * sqrt_T / 100.0  # per 1% vol move
            rho_call[i, j] = K * T * exp_rt * Nd2 / 100.0  # per 1% rate move
            rho_put[i, j] = -K * T * exp_rt * Nmd2 / 100.0
            price_call[i, j] = S * Nd1 - K * exp_rt * Nd2
            price_put[i, j] = K * exp_rt * Nmd2 - S * Nmd1

    return _to_native({
        "spot_points": S_grid.tolist(),
        "time_points": T_grid.tolist(),
        "call_price_surface": price_call.tolist(),
        "put_price_surface": price_put.tolist(),
        "delta_call": delta_call.tolist(),
        "delta_put": delta_put.tolist(),
        "gamma": gamma_surf.tolist(),
        "theta_call": theta_call.tolist(),
        "theta_put": theta_put.tolist(),
        "vega": vega_surf.tolist(),
        "rho_call": rho_call.tolist(),
        "rho_put": rho_put.tolist(),
        "parameters": {
            "strike": K, "rate": r, "volatility": sig,
            "s_range": [s_min, s_max],
            "t_range": [t_min, t_max],
            "n_spot_points": n_spot_points,
            "n_time_points": n_time_points,
        },
    })


# ---------------------------------------------------------------------------
# 4. Barrier Option Pricing (Monte Carlo)
# ---------------------------------------------------------------------------

def barrier_option_pricing(
    s0: float = 1000.0,
    strike: float = 1000.0,
    barrier: float = 1200.0,
    barrier_type: str = "up-and-out",
    option_type: str = "call",
    days: int = 252,
    n_sims: int = 50000,
    mu: float = 0.15,
    sigma: float = 0.25,
    rate: float = 0.05,
) -> dict:
    """
    Price barrier options via Monte Carlo with GBM.

    Supports: up-and-out, down-and-out, up-and-in, down-and-in.
    Returns price, std error, barrier hit probability, expected hit time.
    """
    dt = 1.0 / 252.0
    n_steps = days

    Z = np.random.standard_normal((n_sims, n_steps))
    dW = np.sqrt(dt) * Z

    # Build price paths incrementally
    S = np.zeros((n_sims, n_steps + 1))
    S[:, 0] = s0
    for t in range(n_steps):
        S[:, t + 1] = S[:, t] * np.exp(
            (mu - 0.5 * sigma**2) * dt + sigma * dW[:, t]
        )

    final_price = S[:, -1]

    # Determine barrier hits
    if barrier_type == "up-and-out":
        hit = np.any(S[:, 1:] >= barrier, axis=1)
    elif barrier_type == "down-and-out":
        hit = np.any(S[:, 1:] <= barrier, axis=1)
    elif barrier_type == "up-and-in":
        hit = np.any(S[:, 1:] >= barrier, axis=1)
    elif barrier_type == "down-and-in":
        hit = np.any(S[:, 1:] <= barrier, axis=1)
    else:
        raise ValueError(f"Unknown barrier_type: {barrier_type}")

    # Payoff
    if option_type == "call":
        payoff = np.maximum(final_price - strike, 0)
    else:
        payoff = np.maximum(strike - final_price, 0)

    # Knock-out: active only if NOT hit. Knock-in: active only if hit.
    if "out" in barrier_type:
        active = ~hit
    else:  # "in"
        active = hit

    discounted = payoff * active * np.exp(-rate * days * dt)
    price = float(np.mean(discounted))
    std_error = float(np.std(discounted) / np.sqrt(n_sims))

    # Barrier hit probability and expected hit time
    hit_prob = float(np.mean(hit))
    hit_times = []
    for i in range(n_sims):
        if hit[i]:
            if barrier_type.startswith("up"):
                idx = np.argmax(S[i, 1:] >= barrier) + 1
            else:
                idx = np.argmax(S[i, 1:] <= barrier) + 1
            hit_times.append(idx)

    expected_hit_time = float(np.mean(hit_times)) if hit_times else None
    std_hit_time = float(np.std(hit_times)) if len(hit_times) > 1 else None

    # Also compute vanilla price for reference
    vanilla_price = float(np.mean(payoff * np.exp(-rate * days * dt)))

    return {
        "price": _round4(price),
        "std_error": _round4(std_error),
        "barrier_hit_probability": _round4(hit_prob),
        "expected_barrier_hit_time": _round4(expected_hit_time) if expected_hit_time is not None else None,
        "std_barrier_hit_time": _round4(std_hit_time) if std_hit_time is not None else None,
        "n_barrier_hits": int(np.sum(hit)),
        "vanilla_price": _round4(vanilla_price),
        "barrier_discount": _round4(vanilla_price - price) if "out" in barrier_type else _round4(price - vanilla_price),
        "parameters": {
            "s0": s0, "strike": strike, "barrier": barrier,
            "barrier_type": barrier_type, "option_type": option_type,
            "days": days, "n_sims": n_sims, "mu": mu,
            "sigma": sigma, "rate": rate,
        },
    }


# ---------------------------------------------------------------------------
# 5. Merton Jump-Diffusion Model
# ---------------------------------------------------------------------------

def jump_diffusion_model(
    s0: float = 1000.0,
    mu: float = 0.15,
    sigma: float = 0.20,
    days: int = 252,
    n_paths: int = 1000,
    jump_lambda: float = 0.1,
    jump_mu: float = -0.02,
    jump_sigma: float = 0.05,
) -> dict:
    """
    Merton Jump-Diffusion model.

    dS = (mu - lambda*expected_jump) * S * dt + sigma * S * dW + J * S * dN
    J ~ LogNormal(mu_j, sigma_j^2),  N ~ Poisson(lambda)
    """
    dt = 1.0 / 252.0
    n_steps = days

    # Expected jump size: E[J-1] = exp(jump_mu + 0.5*jump_sigma^2) - 1
    expected_jump = np.exp(jump_mu + 0.5 * jump_sigma**2) - 1
    compensated_mu = mu - jump_lambda * expected_jump

    S_jd = np.zeros((n_paths, n_steps + 1))
    S_gbm = np.zeros((n_paths, n_steps + 1))
    S_jd[:, 0] = s0
    S_gbm[:, 0] = s0

    Z = np.random.standard_normal((n_paths, n_steps))
    dW = np.sqrt(dt) * Z

    # Jump process
    N = np.random.poisson(jump_lambda * dt, (n_paths, n_steps))
    J_sizes = np.exp(np.random.normal(jump_mu, jump_sigma, (n_paths, n_steps)))

    for t in range(n_steps):
        # GBM path (no jumps, same Brownian motion)
        S_gbm[:, t + 1] = S_gbm[:, t] * np.exp(
            (mu - 0.5 * sigma**2) * dt + sigma * dW[:, t]
        )

        # Jump-diffusion path
        jump_multiplier = np.where(N[:, t] > 0, J_sizes[:, t], 1.0)
        S_jd[:, t + 1] = S_jd[:, t] * np.exp(
            (compensated_mu - 0.5 * sigma**2) * dt + sigma * dW[:, t]
        ) * jump_multiplier

    # Collect jump statistics
    total_jumps = np.sum(N, axis=1)
    paths_with_jumps = int(np.sum(total_jumps > 0))
    total_jump_events = int(np.sum(N))

    # Compute log-returns
    log_ret_jd = np.log(S_jd[:, -1] / s0)
    log_ret_gbm = np.log(S_gbm[:, -1] / s0)

    # Excess kurtosis comparison
    kurt_jd = float(stats.kurtosis(log_ret_jd))
    kurt_gbm = float(stats.kurtosis(log_ret_gbm))

    # Skewness comparison
    skew_jd = float(stats.skew(log_ret_jd))
    skew_gbm = float(stats.skew(log_ret_gbm))

    comparison = {
        "jd_mean_final": _round4(np.mean(S_jd[:, -1])),
        "gbm_mean_final": _round4(np.mean(S_gbm[:, -1])),
        "jd_std_final": _round4(np.std(S_jd[:, -1])),
        "gbm_std_final": _round4(np.std(S_gbm[:, -1])),
        "jd_kurtosis": _round4(kurt_jd),
        "gbm_kurtosis": _round4(kurt_gbm),
        "jd_skewness": _round4(skew_jd),
        "gbm_skewness": _round4(skew_gbm),
        "mean_price_diff": _round4(np.mean(S_jd[:, -1] - S_gbm[:, -1])),
        "jd_percentile_5": _round4(np.percentile(S_jd[:, -1], 5)),
        "jd_percentile_95": _round4(np.percentile(S_jd[:, -1], 95)),
        "gbm_percentile_5": _round4(np.percentile(S_gbm[:, -1], 5)),
        "gbm_percentile_95": _round4(np.percentile(S_gbm[:, -1], 95)),
    }

    jump_stats = {
        "expected_jump_size": _round4(expected_jump),
        "compensated_drift": _round4(compensated_mu),
        "paths_with_jumps": paths_with_jumps,
        "total_jump_events": total_jump_events,
        "avg_jumps_per_path": _round4(np.mean(total_jumps)),
        "max_jumps_single_path": int(np.max(total_jumps)),
        "jump_intensity_per_year": _round4(jump_lambda * 252),
    }

    return _to_native({
        "jump_diffusion_paths": S_jd.tolist(),
        "gbm_comparison_paths": S_gbm.tolist(),
        "jump_statistics": jump_stats,
        "comparison": comparison,
        "parameters": {
            "s0": s0, "mu": mu, "sigma": sigma,
            "days": days, "n_paths": n_paths,
            "jump_lambda": jump_lambda, "jump_mu": jump_mu,
            "jump_sigma": jump_sigma,
        },
    })


# ---------------------------------------------------------------------------
# 6. Comprehensive Demo
# ---------------------------------------------------------------------------

def stochastic_calculus_demo() -> dict:
    """
    Run all stochastic calculus analyses with preset TSE-relevant parameters.
    Uses small path counts for fast execution.
    """
    np.random.seed(42)

    # 1. GBM on a TSE stock starting at 1000 IRR
    gbm_result = ito_simulation(
        s0=1000.0,
        mu=0.18,
        sigma=0.28,
        days=252,
        n_paths=8,
    )

    # 2. Heston with TSE-like vol dynamics
    heston_result = heston_model(
        s0=1000.0,
        v0=0.06,
        kappa=1.5,
        theta=0.04,
        xi=0.35,
        rho=-0.6,
        days=252,
        n_paths=8,
    )

    # 3. Greeks surface
    greeks_result = option_greeks_surface(
        s_min=700.0,
        s_max=1300.0,
        n_spot_points=15,
        t_min=0.04,
        t_max=0.8,
        n_time_points=10,
        strike=1000.0,
        rate=0.23,  # ~23% risk-free rate in IRR
        vol=0.28,
    )

    # 4. Barrier option on a TSE stock
    barrier_result = barrier_option_pricing(
        s0=1000.0,
        strike=1000.0,
        barrier=1200.0,
        barrier_type="up-and-out",
        option_type="call",
        days=126,
        n_sims=10000,
        mu=0.18,
        sigma=0.28,
        rate=0.23,
    )

    # 5. Jump-diffusion during a stress period
    jd_result = jump_diffusion_model(
        s0=1000.0,
        mu=0.15,
        sigma=0.22,
        days=252,
        n_paths=8,
        jump_lambda=0.15,
        jump_mu=-0.03,
        jump_sigma=0.06,
    )

    return {
        "demo_title": "FinSight Pro — Stochastic Calculus Engine Demo (TSE)",
        "description": (
            "Comprehensive demo using Tehran Stock Exchange relevant parameters: "
            "GBM at 1000 IRR, Heston vol dynamics, BS Greeks, barrier options, "
            "and Merton jump-diffusion for stress scenarios."
        ),
        "gbm_ito_simulation": gbm_result,
        "heston_stochastic_volatility": heston_result,
        "option_greeks_surface": greeks_result,
        "barrier_option_pricing": barrier_result,
        "jump_diffusion_model": jd_result,
    }
