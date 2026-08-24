"""Black-Litterman Portfolio Model.

Combines market equilibrium (CAPM/implied returns) with investor views
to produce posterior expected returns and optimal portfolio weights.
All computations run locally — offline-capable.
"""

import numpy as np
from typing import Optional


def black_litterman(
    market_cap_weights: list[float],
    covariance_matrix: list[list[float]],
    risk_aversion: float = 2.5,
    tau: float = 0.05,
    views: list[dict] | None = None,
    risk_free_rate: float = 0.0,
) -> dict:
    """Black-Litterman model for portfolio allocation.

    Args:
        market_cap_weights: Market capitalization weights (sum to 1).
        covariance_matrix: Covariance matrix of asset returns (n x n).
        risk_aversion: Risk aversion parameter (delta). Default 2.5.
        tau: Uncertainty parameter (scaling factor for prior). Default 0.05.
        views: List of investor views. Each view is a dict with:
            - "assets": list of asset indices involved
            - "value": the view return (e.g., "Asset 0 will return 15%" → 0.15)
            - "confidence": confidence in the view (1=high, 0.01=low). Default 1.0
        risk_free_rate: Risk-free rate for Sharpe calculation.

    Returns:
        Posterior expected returns, covariance, optimal weights, and analysis.
    """
    n = len(market_cap_weights)
    w_eq = np.array(market_cap_weights)
    sigma = np.array(covariance_matrix)

    if sigma.shape != (n, n):
        return {"error": f"Covariance matrix must be {n}x{n}, got {sigma.shape}"}

    if abs(w_eq.sum() - 1.0) > 0.01:
        w_eq = w_eq / w_eq.sum()  # normalize

    # Step 1: Implied equilibrium returns (reverse optimization)
    # pi = delta * Sigma * w_eq
    pi = risk_aversion * (sigma @ w_eq)

    # Step 2: Build view matrices
    if views is None or len(views) == 0:
        # No views — return equilibrium
        posterior_returns = pi
        posterior_cov = sigma
    else:
        k = len(views)
        P = np.zeros((k, n))  # pick matrix
        Q = np.zeros(k)  # view returns
        omega_diag = np.zeros(k)  # view uncertainty

        for i, view in enumerate(views):
            assets = view.get("assets", [])
            value = view.get("value", 0)
            confidence = view.get("confidence", 1.0)

            if not assets:
                continue

            # Relative or absolute view
            if len(assets) == 1:
                # Absolute view: "Asset i will return X%"
                P[i, assets[0]] = 1.0
                Q[i] = value
            elif len(assets) == 2:
                # Relative view: "Asset i will outperform Asset j by X%"
                P[i, assets[0]] = 1.0
                P[i, assets[1]] = -1.0
                Q[i] = value
            else:
                # Multi-asset view
                total = sum(1.0 for a in assets if a < n)
                for a in assets[:len(assets)-1]:
                    if a < n:
                        P[i, a] = 1.0 / (total - 1)
                if assets[-1] < n:
                    P[i, assets[-1]] = -1.0
                Q[i] = value

            # Omega from confidence: omega = (1/confidence) * P * tau * Sigma * P'
            p_row = P[i].reshape(1, -1)
            omega_var = float(p_row @ (tau * sigma) @ p_row.T)
            omega_diag[i] = omega_var / max(confidence, 0.01)

        Omega = np.diag(omega_diag)

        # Step 3: Compute posterior
        # mu_BL = [(tau*Sigma)^-1 + P'*Omega^-1*P]^-1 * [(tau*Sigma)^-1*pi + P'*Omega^-1*Q]
        tau_sigma = tau * sigma
        tau_sigma_inv = np.linalg.inv(tau_sigma + np.eye(n) * 1e-8)  # regularize

        try:
            omega_inv = np.linalg.inv(Omega + np.eye(k) * 1e-8)
        except np.linalg.LinAlgError:
            omega_inv = np.eye(k)

        M = tau_sigma_inv + P.T @ omega_inv @ P
        try:
            M_inv = np.linalg.inv(M + np.eye(n) * 1e-8)
        except np.linalg.LinAlgError:
            M_inv = np.eye(n) / n

        posterior_returns = M_inv @ (tau_sigma_inv @ pi + P.T @ omega_inv @ Q)

        # Posterior covariance
        M_plus = M_inv + tau_sigma
        posterior_cov = M_plus

    # Step 4: Optimal portfolio from posterior (mean-variance)
    try:
        cov_inv = np.linalg.inv(posterior_cov + np.eye(n) * 1e-8)
        raw_weights = cov_inv @ posterior_returns
        # Normalize to sum to 1 (allowing long-only)
        raw_weights = np.maximum(raw_weights, 0)  # long-only constraint
        if raw_weights.sum() > 0:
            optimal_weights = raw_weights / raw_weights.sum()
        else:
            optimal_weights = w_eq
    except np.linalg.LinAlgError:
        optimal_weights = w_eq

    # Portfolio metrics
    port_return = float(optimal_weights @ posterior_returns)
    port_vol = float(np.sqrt(optimal_weights @ posterior_cov @ optimal_weights))
    sharpe = (port_return - risk_free_rate) / port_vol if port_vol > 0 else 0

    # Active weights vs market
    active_weights = optimal_weights - w_eq
    tracking_error = float(np.sqrt(active_weights @ sigma @ active_weights))
    info_ratio = (port_return - float(w_eq @ pi)) / tracking_error if tracking_error > 0 else 0

    return {
        "method": "Black-Litterman",
        "num_assets": n,
        "parameters": {
            "risk_aversion": risk_aversion,
            "tau": tau,
            "risk_free_rate": risk_free_rate,
            "num_views": len(views) if views else 0,
        },
        "implied_equilibrium_returns": [round(float(r), 6) for r in pi],
        "posterior_returns": [round(float(r), 6) for r in posterior_returns],
        "optimal_weights": [round(float(w), 4) for w in optimal_weights],
        "market_weights": [round(float(w), 4) for w in w_eq],
        "active_weights": [round(float(w), 4) for w in active_weights],
        "portfolio_metrics": {
            "expected_return": round(port_return * 100, 2),
            "volatility": round(port_vol * 100, 2),
            "sharpe_ratio": round(sharpe, 4),
            "tracking_error": round(tracking_error * 100, 2),
            "information_ratio": round(info_ratio, 4),
        },
        "return_changes": [
            round(float(posterior_returns[i] - pi[i]) * 100, 4)
            for i in range(n)
        ],
    }


def black_litterman_demo() -> dict:
    """Generate a demo Black-Litterman analysis with 5 assets and 3 views."""
    # 5-asset market
    w_market = [0.30, 0.25, 0.20, 0.15, 0.10]

    # Realistic covariance matrix
    sigma = [
        [0.0400, 0.0060, 0.0030, 0.0010, 0.0005],
        [0.0060, 0.0300, 0.0040, 0.0020, 0.0010],
        [0.0030, 0.0040, 0.0350, 0.0015, 0.0008],
        [0.0010, 0.0020, 0.0015, 0.0200, 0.0012],
        [0.0005, 0.0010, 0.0008, 0.0012, 0.0150],
    ]

    # 3 investor views
    views = [
        {"assets": [0], "value": 0.15, "confidence": 0.75},  # Asset 1 returns 15%
        {"assets": [0, 1], "value": 0.03, "confidence": 0.50},  # Asset 1 outperforms Asset 2 by 3%
        {"assets": [3], "value": 0.08, "confidence": 0.60},  # Asset 4 returns 8%
    ]

    return black_litterman(w_market, sigma, 2.5, 0.05, views, 0.03)