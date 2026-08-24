"""PCA & Fama-French Factor Analysis.

Provides offline-capable factor analysis tools for identifying
systematic risk factors in stock returns. Includes PCA-based
dimensionality reduction and Fama-French 3-factor model estimation.
All computations run locally — no data leaves the machine.
"""

import numpy as np
from typing import Optional


def pca_analysis(
    returns_matrix: list[list[float]],
    asset_names: list[str] | None = None,
    n_components: int | None = None,
) -> dict:
    """Principal Component Analysis on asset returns.

    Args:
        returns_matrix: T x N matrix of returns (time periods x assets).
        asset_names: Names of assets. If None, uses "Asset 1", "Asset 2", etc.
        n_components: Number of principal components to return.
            If None, returns min(T, N) components.

    Returns:
        PCA results: eigenvalues, explained variance, loadings, scores.
    """
    data = np.array(returns_matrix, dtype=float)
    t, n = data.shape

    if asset_names is None:
        asset_names = [f"Asset {i+1}" for i in range(n)]

    if n_components is None:
        n_components = min(t, n)
    n_components = min(n_components, min(t, n))

    # Center the data (demean)
    mean_returns = data.mean(axis=0)
    centered = data - mean_returns

    # Covariance matrix of returns (N x N)
    cov_matrix = (centered.T @ centered) / (t - 1)

    # Eigenvalue decomposition
    try:
        eigenvalues, eigenvectors = np.linalg.eigh(cov_matrix)
    except np.linalg.LinAlgError:
        return {"error": "Failed to decompose covariance matrix"}

    # Sort by descending eigenvalue
    idx = np.argsort(eigenvalues)[::-1]
    eigenvalues = eigenvalues[idx]
    eigenvectors = eigenvectors[:, idx]

    # Keep only positive eigenvalues
    positive_mask = eigenvalues > 1e-10
    eigenvalues = eigenvalues[positive_mask]
    eigenvectors = eigenvectors[:, positive_mask]

    total_variance = eigenvalues.sum()
    explained_variance = eigenvalues[:n_components] / total_variance if total_variance > 0 else np.zeros(n_components)
    cumulative_variance = np.cumsum(explained_variance)

    # Factor loadings (principal component coefficients)
    loadings = eigenvectors[:, :n_components].T

    # Factor scores (projection of data onto components)
    scores = centered @ eigenvectors[:, :n_components]

    # Kaiser criterion: keep components with eigenvalue > 1
    kaiser_components = int(np.sum(eigenvalues > 1.0))

    # Scree plot data
    scree_data = [
        {
            "component": i + 1,
            "eigenvalue": round(float(eigenvalues[i]), 6) if i < len(eigenvalues) else 0,
            "explained_var_pct": round(float(explained_variance[i] * 100), 2) if i < len(explained_variance) else 0,
            "cumulative_var_pct": round(float(cumulative_variance[i] * 100), 2) if i < len(cumulative_variance) else 0,
        }
        for i in range(min(n_components, len(eigenvalues)))
    ]

    # Top loading assets per component
    top_loadings = []
    for comp in range(min(3, n_components)):
        comp_loadings = loadings[comp]
        top_idx = np.argsort(-np.abs(comp_loadings))[:5]
        top_loadings.append(
            {
                "component": comp + 1,
                "explained_var_pct": round(float(explained_variance[comp] * 100), 2),
                "top_assets": [
                    {
                        "name": asset_names[j] if j < len(asset_names) else f"Asset {j+1}",
                        "loading": round(float(comp_loadings[j]), 4),
                    }
                    for j in top_idx
                ],
            }
        )

    # Factor correlation matrix (component correlations)
    if scores.shape[1] > 1:
        factor_corr = np.corrcoef(scores.T)
    else:
        factor_corr = np.ones((1, 1))

    return {
        "method": "PCA",
        "observations": t,
        "assets": n,
        "components_analyzed": n_components,
        "kaiser_components": kaiser_components,
        "total_explained_variance_pct": round(float(cumulative_variance[min(n_components - 1, len(cumulative_variance) - 1)]) * 100, 2) if n_components > 0 else 0,
        "eigenvalues": [round(float(e), 6) for e in eigenvalues[:n_components]],
        "explained_variance_pct": [round(float(v * 100), 2) for v in explained_variance],
        "cumulative_variance_pct": [round(float(v * 100), 2) for v in cumulative_variance],
        "scree_plot_data": scree_data,
        "top_loadings": top_loadings,
        "mean_returns": [round(float(m), 6) for m in mean_returns],
        "recommendation": (
            f"PCA identifies {kaiser_components} significant factors (Kaiser criterion). "
            f"First {min(3, kaiser_components)} components explain {cumulative_variance[min(2, kaiser_components-1)]*100:.1f}% of variance."
            if kaiser_components > 0
            else "No significant principal components found (all eigenvalues <= 1)."
        ),
    }


def fama_french(
    returns_matrix: list[list[float]],
    market_returns: list[float],
    asset_names: list[str] | None = None,
    market_cap: list[float] | None = None,
    book_to_market: list[float] | None = None,
) -> dict:
    """Fama-French 3-Factor Model estimation.

    Factors:
    - Market Risk Premium (MKT): Rm - Rf
    - Size (SMB): Small Minus Big
    - Value (HML): High Minus Low (book-to-market)

    Args:
        returns_matrix: T x N matrix of asset excess returns.
        market_returns: T-length vector of market returns.
        asset_names: Names of assets.
        market_cap: T x N or N-length market capitalizations for SMB.
        book_to_market: T x N or N-length book-to-market ratios for HML.

    Returns:
        Factor returns, asset loadings (betas), and model fit statistics.
    """
    data = np.array(returns_matrix, dtype=float)
    rm = np.array(market_returns, dtype=float)
    t, n = data.shape

    if len(rm) != t:
        return {"error": f"Market returns length ({len(rm)}) must match data periods ({t})"}

    if asset_names is None:
        asset_names = [f"Asset {i+1}" for i in range(n)]

    # Market risk premium
    rf = 0.0  # risk-free (can be parameterized)
    mkt_premium = rm - rf

    # Build SMB and HML factors
    # If no market_cap/btm provided, estimate from return data
    if market_cap is not None:
        mc = np.array(market_cap, dtype=float)
        if mc.ndim == 1:
            mc = np.tile(mc, (t, 1))
        median_mc = np.median(mc, axis=1, keepdims=True)
        small_mask = mc <= median_mc
        big_mask = mc > median_mc

        # Small and big portfolio returns
        small_returns = np.where(small_mask, data, np.nan).mean(axis=1)
        big_returns = np.where(big_mask, data, np.nan).mean(axis=1)
        # Replace NaN with 0
        small_returns = np.nan_to_num(small_returns)
        big_returns = np.nan_to_num(big_returns)
        smb = small_returns - big_returns
    else:
        # Estimate SMB from return variance (proxy)
        var_returns = np.var(data, axis=1)
        median_var = np.median(var_returns)
        small_mask = var_returns <= median_var
        big_mask = var_returns > median_var
        small_returns = data[small_mask].mean(axis=0) if small_mask.sum() > 0 else np.zeros(n)
        big_returns = data[big_mask].mean(axis=0) if big_mask.sum() > 0 else np.zeros(n)
        smb = small_returns - big_returns
        # Extend to full time series
        smb = np.full(t, np.mean(smb))

    if book_to_market is not None:
        btm = np.array(book_to_market, dtype=float)
        if btm.ndim == 1:
            btm = np.tile(btm, (t, 1))
        median_btm = np.median(btm, axis=1, keepdims=True)
        high_mask = btm >= median_btm
        low_mask = btm < median_btm

        high_returns = np.where(high_mask, data, np.nan).mean(axis=1)
        low_returns = np.where(low_mask, data, np.nan).mean(axis=1)
        high_returns = np.nan_to_num(high_returns)
        low_returns = np.nan_to_num(low_returns)
        hml = high_returns - low_returns
    else:
        # Estimate HML from mean returns (proxy)
        mean_ret = data.mean(axis=0)
        median_ret = np.median(mean_ret)
        high_returns = data[:, mean_ret >= median_ret].mean(axis=1) if (mean_ret >= median_ret).sum() > 0 else np.zeros(t)
        low_returns = data[:, mean_ret < median_ret].mean(axis=1) if (mean_ret < median_ret).sum() > 0 else np.zeros(t)
        hml = high_returns - low_returns

    # Build factor matrix (T x 3)
    factors = np.column_stack([mkt_premium, smb, hml])
    factor_names = ["MKT (Market)", "SMB (Size)", "HML (Value)"]

    # OLS regression for each asset: Ri = alpha + beta_MKT*MKT + beta_SMB*SMB + beta_HML*HML + ei
    # Add intercept
    X = np.column_stack([np.ones(t), factors])
    XtX = X.T @ X
    try:
        XtX_inv = np.linalg.inv(XtX + np.eye(4) * 1e-8)
    except np.linalg.LinAlgError:
        XtX_inv = np.eye(4) / t

    betas_list = []
    r_squared_list = []
    alpha_list = []

    for j in range(n):
        y = data[:, j]
        beta = XtX_inv @ (X.T @ y)
        y_hat = X @ beta
        ss_res = float(np.sum((y - y_hat) ** 2))
        ss_tot = float(np.sum((y - y.mean()) ** 2))
        r_sq = 1 - ss_res / ss_tot if ss_tot > 0 else 0

        alpha_list.append(round(float(beta[0]), 6))
        betas_list.append(
            {
                "asset": asset_names[j],
                "alpha": round(float(beta[0]), 6),
                "beta_mkt": round(float(beta[1]), 4),
                "beta_smb": round(float(beta[2]), 4),
                "beta_hml": round(float(beta[3]), 4),
                "r_squared": round(r_sq, 4),
            }
        )
        r_squared_list.append(r_sq)

    # Factor return statistics
    factor_stats = []
    for i, name in enumerate(factor_names):
        f = factors[:, i]
        factor_stats.append(
            {
                "factor": name,
                "mean_annual_pct": round(float(f.mean() * 252 * 100), 2),
                "volatility_annual_pct": round(float(f.std() * np.sqrt(252) * 100), 2),
                "sharpe": round(float(f.mean() / f.std()) if f.std() > 0 else 0, 4),
            }
        )

    # Factor correlation matrix
    factor_corr = np.corrcoef(factors.T)

    avg_r_squared = float(np.mean(r_squared_list))

    return {
        "method": "Fama-French 3-Factor",
        "observations": t,
        "assets": n,
        "factor_names": factor_names,
        "factor_statistics": factor_stats,
        "factor_correlation": [
            [round(float(factor_corr[i][j]), 4) for j in range(3)]
            for i in range(3)
        ],
        "asset_loadings": betas_list,
        "avg_r_squared": round(avg_r_squared, 4),
        "mean_alpha_pct": round(float(np.mean(alpha_list)) * 252 * 100, 4),
        "recommendation": (
            f"Model explains {avg_r_squared*100:.1f}% of return variation on average. "
            f"Assets with R-squared > 0.7 are well-explained by systematic factors. "
            f"Consider adding momentum (UMD) factor for improved fit."
            if avg_r_squared > 0.3
            else "Factor model has low explanatory power. Consider using PCA to identify "
            "dominant factors specific to this market (e.g., TSE-specific factors)."
        ),
    }


def factor_analysis_demo() -> dict:
    """Generate a demo factor analysis with 10 assets and 120 periods."""
    np.random.seed(42)
    n_assets = 10
    t = 120

    # Generate correlated returns using factor structure
    # 3 hidden factors
    factor_loadings_true = np.random.randn(n_assets, 3) * 0.5
    factor_returns = np.random.randn(t, 3) * np.array([0.12, 0.06, 0.04]).reshape(1, 3) / np.sqrt(252)
    noise = np.random.randn(t, n_assets) * 0.02 / np.sqrt(252)
    asset_returns = factor_returns @ factor_loadings_true.T + noise
    asset_returns *= 100  # convert to percentage for clarity

    # Market returns (weighted average)
    w = np.array([0.20, 0.15, 0.12, 0.10, 0.10, 0.08, 0.08, 0.07, 0.05, 0.05])
    market_returns = (asset_returns * w).sum(axis=1)

    # Market caps (for SMB)
    market_caps = np.array([50, 40, 35, 30, 25, 20, 18, 15, 12, 10])

    # Book-to-market (for HML)
    btm = np.array([0.3, 0.8, 1.2, 0.5, 1.5, 0.4, 1.0, 0.6, 1.3, 0.9])

    asset_names = [
        "Persian Gulf Petro", "Melli Bank", "Sepah Oil", "Iran Khodro",
        "Mobarakeh Steel", "Saipa Auto", "Khouzestan Steel", "Telecom Iran",
        "Mapna Group", "National Copper"
    ]

    pca_result = pca_analysis(asset_returns.tolist(), asset_names)
    ff_result = fama_french(
        asset_returns.tolist(), market_returns.tolist(),
        asset_names, market_caps.tolist(), btm.tolist()
    )

    return {
        "pca": pca_result,
        "fama_french": ff_result,
    }
