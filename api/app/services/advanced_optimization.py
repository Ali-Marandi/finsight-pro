"""Advanced Portfolio Optimization Engine.

Implements SOCP portfolio optimization, robust optimization, hierarchical
risk parity (HRP), and multi-objective Pareto frontier analysis.
All computations run locally — offline-capable.
"""

import numpy as np
from typing import Optional
from scipy import optimize, cluster, spatial, stats, linalg


# ---------------------------------------------------------------------------
# 1. SOCP Portfolio Optimization
# ---------------------------------------------------------------------------

def socp_portfolio(
    expected_returns: list[float],
    cov_matrix: list[list[float]],
    constraints: dict | None = None,
    risk_free_rate: float = 0.0,
    current_weights: list[float] | None = None,
) -> dict:
    """Second-Order Cone Programming portfolio via SLSQP.

    Args:
        expected_returns: Expected annualised returns for each asset.
        cov_matrix: Covariance matrix of returns (n x n).
        constraints: Dict of optional constraints:
            - max_turnover: float  (default 1.0)
            - min_weight: float    (default 0.0)
            - max_weight: float    (default 1.0)
            - sector_limits: dict  {sector_name: [list of asset indices], max_pct}
            - cardinality_approx: int or None
            - transaction_costs: float (default 0.001)
            - target_return: float or None
        risk_free_rate: Risk-free rate for Sharpe ratio.
        current_weights: Current portfolio weights for turnover constraint.

    Returns:
        Optimisation result with weights, metrics, and constraint report.
    """
    mu = np.array(expected_returns, dtype=float)
    sigma = np.array(cov_matrix, dtype=float)
    n = len(mu)

    if sigma.shape != (n, n):
        return {"error": f"Covariance matrix must be {n}x{n}, got {sigma.shape}"}

    # Defaults
    c = constraints or {}
    max_turnover = c.get("max_turnover", 1.0)
    min_w = c.get("min_weight", 0.0)
    max_w = c.get("max_weight", 1.0)
    sector_limits = c.get("sector_limits", {})
    tc = c.get("transaction_costs", 0.001)
    target_ret = c.get("target_return", None)

    w_current = np.array(current_weights, dtype=float) if current_weights else np.ones(n) / n

    # --- Objective: maximise Sharpe ≡ minimise negative Sharpe ---
    def neg_sharpe(w):
        port_ret = w @ mu
        port_vol = np.sqrt(w @ sigma @ w + 1e-12)
        return -(port_ret - risk_free_rate) / port_vol

    # If target_return is specified, switch to risk minimisation
    if target_ret is not None:
        def objective(w):
            return w @ sigma @ w
    else:
        objective = neg_sharpe

    # --- Constraints & bounds ---
    cons = []

    # Full investment
    cons.append({"type": "eq", "fun": lambda w: np.sum(w) - 1.0})

    # Target return constraint
    if target_ret is not None:
        cons.append({"type": "ineq", "fun": lambda w: w @ mu - target_ret})

    # Sector exposure limits
    sector_cons_report = []
    for sector_name, sector_info in sector_limits.items():
        idx = sector_info["assets"]
        max_pct = sector_info["max"]
        cons.append({
            "type": "ineq",
            "fun": lambda w, ii=idx, mp=max_pct: mp - np.sum(w[ii]),
        })
        sector_cons_report.append({
            "sector": sector_name,
            "assets": idx,
            "max_pct": max_pct,
        })

    # Turnover constraint
    cons.append({
        "type": "ineq",
        "fun": lambda w: max_turnover - np.sum(np.abs(w - w_current)),
    })

    bounds = [(min_w, max_w)] * n

    # Initial guess: equal weight
    w0 = np.ones(n) / n

    # Transaction cost penalty (additive to objective)
    tc_enabled = tc > 0

    if tc_enabled and target_ret is not None:
        def objective_with_tc(w):
            return w @ sigma @ w + tc * np.sum(np.abs(w - w_current))
    elif tc_enabled:
        def objective_with_tc(w):
            port_ret = w @ mu - tc * np.sum(np.abs(w - w_current))
            port_vol = np.sqrt(w @ sigma @ w + 1e-12)
            return -(port_ret - risk_free_rate) / port_vol
        objective = objective_with_tc

    # Solve
    result = optimize.minimize(
        objective, w0, method="SLSQP", bounds=bounds, constraints=cons,
        options={"maxiter": 1000, "ftol": 1e-12},
    )

    w_opt = result.x
    w_opt = np.maximum(w_opt, 0.0)
    w_opt = w_opt / w_opt.sum() if w_opt.sum() > 0 else np.ones(n) / n

    port_ret = float(w_opt @ mu)
    port_vol = float(np.sqrt(w_opt @ sigma @ w_opt))
    sharpe = (port_ret - risk_free_rate) / port_vol if port_vol > 1e-10 else 0.0
    turnover = float(np.sum(np.abs(w_opt - w_current)))
    tc_total = float(tc * turnover)

    # Constraint satisfaction report
    constraint_report = {
        "sum_to_one": round(float(w_opt.sum()), 6),
        "no_short_selling": bool(np.all(w_opt >= -1e-6)),
        "max_position": round(float(w_opt.max()), 6),
        "min_position": round(float(w_opt.min()), 6),
        "turnover": round(turnover, 6),
        "max_turnover_limit": max_turnover,
        "turnover_satisfied": turnover <= max_turnover + 1e-4,
        "transaction_cost_total": round(tc_total, 6),
    }

    # Sector exposure
    for sn, si in sector_limits.items():
        idx = si["assets"]
        constraint_report[f"sector_{sn}_exposure"] = round(float(w_opt[idx].sum()), 6)
        constraint_report[f"sector_{sn}_limit"] = si["max"]

    if target_ret is not None:
        constraint_report["target_return"] = target_ret
        constraint_report["achieved_return"] = round(port_ret, 6)
        constraint_report["return_constraint_satisfied"] = port_ret >= target_ret - 1e-4

    convergence = {
        "success": bool(result.success),
        "message": str(result.message),
        "iterations": int(result.nit),
        "objective_value": round(float(result.fun), 8),
    }

    return {
        "method": "SOCP-SLSQP",
        "num_assets": n,
        "optimal_weights": [round(float(w), 6) for w in w_opt],
        "expected_return": round(port_ret, 6),
        "expected_risk": round(port_vol, 6),
        "sharpe_ratio": round(sharpe, 6),
        "turnover": round(turnover, 6),
        "transaction_costs": round(tc_total, 6),
        "constraint_report": constraint_report,
        "convergence": convergence,
    }


# ---------------------------------------------------------------------------
# 2. Robust Portfolio Optimization
# ---------------------------------------------------------------------------

def robust_optimization(
    expected_returns: list[float],
    cov_matrix: list[list[float]],
    uncertainty_budget: float = 0.1,
    delta: float = 0.95,
    risk_free_rate: float = 0.0,
) -> dict:
    """Robust portfolio optimisation under return and covariance uncertainty.

    (a) Return uncertainty set: mu_hat can deviate by epsilon in L2-norm.
    (b) Covariance uncertainty: factor model with uncertain factor loadings.

    Returns robust optimal weights and comparison vs nominal Markowitz.
    """
    mu = np.array(expected_returns, dtype=float)
    sigma = np.array(cov_matrix, dtype=float)
    n = len(mu)

    if sigma.shape != (n, n):
        return {"error": f"Covariance matrix must be {n}x{n}, got {sigma.shape}"}

    epsilon = uncertainty_budget
    # ---- Nominal Markowitz (max Sharpe) ----
    def neg_sharpe_nominal(w):
        r = w @ mu
        v = np.sqrt(w @ sigma @ w + 1e-12)
        return -(r - risk_free_rate) / v

    cons_nom = [{"type": "eq", "fun": lambda w: np.sum(w) - 1.0}]
    bnds = [(0.0, 1.0)] * n
    w0 = np.ones(n) / n

    res_nom = optimize.minimize(
        neg_sharpe_nominal, w0, method="SLSQP",
        bounds=bnds, constraints=cons_nom,
        options={"maxiter": 1000, "ftol": 1e-12},
    )
    w_nom = res_nom.x
    w_nom = np.maximum(w_nom, 0.0)
    w_nom = w_nom / w_nom.sum() if w_nom.sum() > 0 else w0.copy()

    # ---- Robust: worst-case return objective ----
    # worst-case return = w'mu - epsilon * ||w||_2
    # We maximise worst-case Sharpe: minimise -(wc_return - rf) / vol

    def neg_wc_sharpe(w):
        wc_return = w @ mu - epsilon * np.sqrt(w @ w + 1e-12)
        v = np.sqrt(w @ sigma @ w + 1e-12)
        return -(wc_return - risk_free_rate) / v

    # Covariance uncertainty: inflate covariance by delta factor
    # delta is confidence level; higher delta → more inflation
    # We use a chi-squared scaling: sigma_robust = sigma * (1 + epsilon_cov)
    # where epsilon_cov derived from delta
    epsilon_cov = epsilon * (delta / 0.95)  # scale with confidence
    sigma_robust = sigma * (1.0 + epsilon_cov)

    def neg_wc_sharpe_robust(w):
        wc_return = w @ mu - epsilon * np.sqrt(w @ w + 1e-12)
        v = np.sqrt(w @ sigma_robust @ w + 1e-12)
        return -(wc_return - risk_free_rate) / v

    cons_rob = [{"type": "eq", "fun": lambda w: np.sum(w) - 1.0}]

    res_rob = optimize.minimize(
        neg_wc_sharpe_robust, w0, method="SLSQP",
        bounds=bnds, constraints=cons_rob,
        options={"maxiter": 1000, "ftol": 1e-12},
    )
    w_rob = res_rob.x
    w_rob = np.maximum(w_rob, 0.0)
    w_rob = w_rob / w_rob.sum() if w_rob.sum() > 0 else w0.copy()

    # ---- Metrics ----
    nom_ret = float(w_nom @ mu)
    nom_vol = float(np.sqrt(w_nom @ sigma @ w_nom))
    nom_sharpe = (nom_ret - risk_free_rate) / nom_vol if nom_vol > 1e-10 else 0.0

    rob_ret = float(w_rob @ mu)
    rob_vol = float(np.sqrt(w_rob @ sigma @ w_rob))
    rob_sharpe = (rob_ret - risk_free_rate) / rob_vol if rob_vol > 1e-10 else 0.0

    # Worst-case returns
    wc_ret_nom = nom_ret - epsilon * float(np.sqrt(w_nom @ w_nom))
    wc_ret_rob = rob_ret - epsilon * float(np.sqrt(w_rob @ w_rob))

    # Robust vol
    rob_vol_robust_cov = float(np.sqrt(w_rob @ sigma_robust @ w_rob))

    # Divergence between nominal and robust
    weight_diff = float(np.sum(np.abs(w_nom - w_rob)))

    return {
        "method": "Robust Optimization",
        "num_assets": n,
        "parameters": {
            "uncertainty_budget": epsilon,
            "confidence_level": delta,
            "covariance_inflation": round(epsilon_cov, 6),
            "risk_free_rate": risk_free_rate,
        },
        "nominal_weights": [round(float(w), 6) for w in w_nom],
        "robust_weights": [round(float(w), 6) for w in w_rob],
        "nominal_metrics": {
            "expected_return": round(nom_ret, 6),
            "volatility": round(nom_vol, 6),
            "sharpe_ratio": round(nom_sharpe, 6),
            "worst_case_return": round(wc_ret_nom, 6),
        },
        "robust_metrics": {
            "expected_return": round(rob_ret, 6),
            "volatility": round(rob_vol, 6),
            "volatility_robust_cov": round(rob_vol_robust_cov, 6),
            "sharpe_ratio": round(rob_sharpe, 6),
            "worst_case_return": round(wc_ret_rob, 6),
        },
        "comparison": {
            "return_sacrifice": round(nom_ret - rob_ret, 6),
            "risk_reduction": round(nom_vol - rob_vol, 6),
            "worst_case_improvement": round(wc_ret_rob - wc_ret_nom, 6),
            "weight_divergence": round(weight_diff, 6),
        },
        "uncertainty_analysis": {
            "return_uncertainty_radius": epsilon,
            "cov_inflation_factor": round(1.0 + epsilon_cov, 6),
            "robustness_margin": round(wc_ret_rob - risk_free_rate, 6),
        },
    }


# ---------------------------------------------------------------------------
# 3. Hierarchical Risk Parity (HRP)
# ---------------------------------------------------------------------------

def hierarchical_risk_parity(
    returns_matrix: list[list[float]],
    asset_names: list[str] | None = None,
    risk_free_rate: float = 0.0,
) -> dict:
    """Hierarchical Risk Parity using correlation-based clustering.

    Steps: correlation/distance matrices → hierarchical clustering →
    quasi-diagonalisation (seriation) → recursive bisection.

    Args:
        returns_matrix: T x N matrix of asset returns.
        asset_names: Optional names for assets.
        risk_free_rate: For Sharpe ratio computation.

    Returns:
        HRP weights, dendrogram, cluster assignments, comparisons.
    """
    R = np.array(returns_matrix, dtype=float)
    n_assets = R.shape[1]
    t_periods = R.shape[0]

    if asset_names is None:
        asset_names = [f"Asset_{i}" for i in range(n_assets)]

    # Step (a): Correlation and distance matrices
    corr = np.corrcoef(R.T)
    # Distance: d_ij = sqrt(0.5 * (1 - rho_ij))
    dist = np.sqrt(np.clip(0.5 * (1.0 - corr), 0, None))
    dist = (dist + dist.T) / 2  # ensure exact symmetry
    np.fill_diagonal(dist, 0.0)  # force zero diagonal

    # Condensed distance matrix for scipy linkage
    condensed = spatial.distance.squareform(dist)

    # Step (b): Hierarchical clustering (single-linkage)
    try:
        linkage_matrix = cluster.hierarchy.linkage(condensed, method="single")
    except Exception:
        # Fallback: implement single-linkage manually
        linkage_matrix = _single_linkage_manual(dist)

    # Step (c): Quasi-diagonalisation (seriation)
    sorted_indices = _get_quasi_diag(linkage_matrix)
    sorted_indices = [int(i) for i in sorted_indices]

    # Step (d): Recursive bisection for weight allocation
    cov = np.cov(R.T)
    hrp_weights = _recursive_bisection(cov, sorted_indices)

    # Normalise weights
    hrp_weights = np.array(hrp_weights)
    total = hrp_weights.sum()
    if total > 0:
        hrp_weights = hrp_weights / total

    # Expected returns from historical mean
    mu = R.mean(axis=0)

    # HRP portfolio metrics
    hrp_ret = float(hrp_weights @ mu)
    hrp_vol = float(np.sqrt(hrp_weights @ cov @ hrp_weights))
    hrp_sharpe = (hrp_ret - risk_free_rate) / hrp_vol if hrp_vol > 1e-10 else 0.0

    # Equal-weight benchmark
    w_eq = np.ones(n_assets) / n_assets
    eq_ret = float(w_eq @ mu)
    eq_vol = float(np.sqrt(w_eq @ cov @ w_eq))
    eq_sharpe = (eq_ret - risk_free_rate) / eq_vol if eq_vol > 1e-10 else 0.0

    # Inverse-variance benchmark
    inv_var = 1.0 / np.diag(cov)
    w_iv = inv_var / inv_var.sum()
    iv_ret = float(w_iv @ mu)
    iv_vol = float(np.sqrt(w_iv @ cov @ w_iv))
    iv_sharpe = (iv_ret - risk_free_rate) / iv_vol if iv_vol > 1e-10 else 0.0

    # Cluster assignments (cut at ~half the max distance)
    max_d = float(linkage_matrix[:, 2].max())
    cluster_labels = cluster.hierarchy.fcluster(
        linkage_matrix, t=max_d * 0.6, criterion="distance"
    )
    n_clusters = int(cluster_labels.max())

    # Cluster-level analysis
    clusters = {}
    for c_id in range(1, n_clusters + 1):
        members = [int(i) for i in np.where(cluster_labels == c_id)[0]]
        if not members:
            continue
        w_cluster = sum(hrp_weights[i] for i in members)
        clusters[f"cluster_{c_id}"] = {
            "assets": [asset_names[i] for i in members],
            "indices": members,
            "total_weight": round(float(w_cluster), 6),
            "num_assets": len(members),
        }

    return {
        "method": "Hierarchical Risk Parity",
        "num_assets": n_assets,
        "num_periods": t_periods,
        "asset_names": asset_names,
        "hrp_weights": [round(float(w), 6) for w in hrp_weights],
        "dendrogram": {
            "linkage_matrix": [[round(float(x), 6) for x in row]
                                for row in linkage_matrix.tolist()],
            "num_clusters": n_clusters,
        },
        "cluster_assignments": {
            asset_names[i]: int(cluster_labels[i]) for i in range(n_assets)
        },
        "clusters": clusters,
        "hrp_metrics": {
            "expected_return": round(hrp_ret, 6),
            "volatility": round(hrp_vol, 6),
            "sharpe_ratio": round(hrp_sharpe, 6),
        },
        "comparison": {
            "equal_weight": {
                "weights": [round(float(w), 6) for w in w_eq],
                "return": round(eq_ret, 6),
                "volatility": round(eq_vol, 6),
                "sharpe": round(eq_sharpe, 6),
            },
            "inverse_variance": {
                "weights": [round(float(w), 6) for w in w_iv],
                "return": round(iv_ret, 6),
                "volatility": round(iv_vol, 6),
                "sharpe": round(iv_sharpe, 6),
            },
            "hrp_vs_eq_sharpe_delta": round(hrp_sharpe - eq_sharpe, 6),
            "hrp_vs_iv_sharpe_delta": round(hrp_sharpe - iv_sharpe, 6),
        },
        "distance_matrix": [
            [round(float(d), 6) for d in row] for row in dist.tolist()
        ],
        "seriation_order": sorted_indices,
    }


def _single_linkage_manual(dist_matrix: np.ndarray) -> np.ndarray:
    """Manual single-linkage hierarchical clustering."""
    n = dist_matrix.shape[0]
    active = list(range(n))
    clusters = {i: [i] for i in range(n)}
    linkage = []
    step = 0

    for _ in range(n - 1):
        min_dist = np.inf
        merge_i, merge_j = 0, 1

        for ii in range(len(active)):
            for jj in range(ii + 1, len(active)):
                ci, cj = active[ii], active[jj]
                # Single linkage: min distance between any pair
                d = np.min(dist_matrix[np.ix_(clusters[ci], clusters[cj])])
                if d < min_dist:
                    min_dist = d
                    merge_i, merge_j = ii, jj

        ci, cj = active[merge_i], active[merge_j]
        new_size = len(clusters[ci]) + len(clusters[cj])
        linkage.append([ci, cj, min_dist, new_size])

        new_id = n + step
        clusters[new_id] = clusters[ci] + clusters[cj]
        del clusters[ci]
        del clusters[cj]
        active.pop(merge_i)
        active[merge_j] = new_id
        step += 1

    return np.array(linkage)


def _get_quasi_diag(linkage: np.ndarray) -> list:
    """Quasi-diagonalisation: retrieve sorted order of leaf nodes."""
    n = linkage.shape[0] + 1
    idx = int(linkage[-1, 0]), int(linkage[-1, 1])
    order = []

    def _traverse(node):
        if node < n:
            order.append(node)
        else:
            left = int(linkage[node - n, 0])
            right = int(linkage[node - n, 1])
            _traverse(left)
            _traverse(right)

    _traverse(idx[0])
    _traverse(idx[1])
    return order


def _recursive_bisection(cov: np.ndarray, sorted_indices: list) -> list:
    """Recursive bisection for HRP weight allocation."""
    n = len(sorted_indices)
    weights = [0.0] * (max(sorted_indices) + 1) if sorted_indices else [0.0] * n

    # Map to contiguous indices for covariance sub-matrix access
    items = list(sorted_indices)

    def _bisect(items_list, w_total):
        if len(items_list) == 1:
            weights[items_list[0]] = w_total
            return

        mid = len(items_list) // 2
        left = items_list[:mid]
        right = items_list[mid:]

        # Inverse-variance split
        var_left = _get_cluster_var(cov, left)
        var_right = _get_cluster_var(cov, right)

        alpha = 1.0 - var_left / (var_left + var_right + 1e-12)

        _bisect(left, w_total * alpha)
        _bisect(right, w_total * (1.0 - alpha))

    _bisect(items, 1.0)
    return weights


def _get_cluster_var(cov: np.ndarray, items: list) -> float:
    """Compute cluster variance for HRP bisection."""
    if not items:
        return 1e-12
    cov_sub = cov[np.ix_(items, items)]
    w = np.ones(len(items)) / len(items)
    return float(w @ cov_sub @ w)


# ---------------------------------------------------------------------------
# 4. Multi-Objective Optimization (Pareto Frontier)
# ---------------------------------------------------------------------------

def multi_objective_optimization(
    expected_returns: list[float],
    cov_matrix: list[list[float]],
    n_points: int = 50,
    risk_free_rate: float | None = None,
) -> dict:
    """Compute the Pareto (efficient) frontier for return vs risk trade-off.

    Solves a series of mean-variance problems with varying target returns.

    Args:
        expected_returns: Expected returns.
        cov_matrix: Covariance matrix.
        n_points: Number of points on the frontier.
        risk_free_rate: If provided, also compute capital market line.

    Returns:
        Pareto frontier, optimal Sharpe portfolio, min-variance portfolio.
    """
    mu = np.array(expected_returns, dtype=float)
    sigma = np.array(cov_matrix, dtype=float)
    n = len(mu)

    if sigma.shape != (n, n):
        return {"error": f"Covariance matrix must be {n}x{n}, got {sigma.shape}"}

    rf = risk_free_rate if risk_free_rate is not None else 0.0

    # Bounds and constraints
    bounds = [(0.0, 1.0)] * n
    eq_con = {"type": "eq", "fun": lambda w: np.sum(w) - 1.0}
    w0 = np.ones(n) / n

    # --- Min variance portfolio ---
    def port_var(w):
        return w @ sigma @ w

    res_mv = optimize.minimize(
        port_var, w0, method="SLSQP",
        bounds=bounds, constraints=[eq_con],
        options={"maxiter": 1000, "ftol": 1e-12},
    )
    w_mv = np.maximum(res_mv.x, 0.0)
    w_mv = w_mv / w_mv.sum()
    mv_ret = float(w_mv @ mu)
    mv_vol = float(np.sqrt(w_mv @ sigma @ w_mv))

    # --- Max return portfolio (concentrate in highest-return asset) ---
    def neg_return(w):
        return -(w @ mu)

    res_mr = optimize.minimize(
        neg_return, w0, method="SLSQP",
        bounds=bounds, constraints=[eq_con],
        options={"maxiter": 1000, "ftol": 1e-12},
    )
    w_mr = np.maximum(res_mr.x, 0.0)
    w_mr = w_mr / w_mr.sum()
    mr_ret = float(w_mr @ mu)

    # --- Trace efficient frontier ---
    target_returns = np.linspace(mv_ret, mr_ret, n_points)
    frontier = []

    for t_ret in target_returns:
        cons = [
            eq_con,
            {"type": "ineq", "fun": lambda w, tr=t_ret: w @ mu - tr},
        ]
        res = optimize.minimize(
            port_var, w0, method="SLSQP",
            bounds=bounds, constraints=cons,
            options={"maxiter": 500, "ftol": 1e-12},
        )
        if res.success or res.fun < 1e6:
            w = np.maximum(res.x, 0.0)
            w = w / w.sum() if w.sum() > 0 else w0.copy()
            ret = float(w @ mu)
            vol = float(np.sqrt(w @ sigma @ w))
            sharpe = (ret - rf) / vol if vol > 1e-10 else 0.0
            frontier.append({
                "target_return": round(float(t_ret), 6),
                "return": round(ret, 6),
                "risk": round(vol, 6),
                "sharpe": round(sharpe, 6),
                "weights": [round(float(ww), 6) for ww in w],
            })

    # --- Max Sharpe portfolio ---
    def neg_sharpe(w):
        r = w @ mu
        v = np.sqrt(w @ sigma @ w + 1e-12)
        return -(r - rf) / v

    res_ms = optimize.minimize(
        neg_sharpe, w0, method="SLSQP",
        bounds=bounds, constraints=[eq_con],
        options={"maxiter": 1000, "ftol": 1e-12},
    )
    w_ms = np.maximum(res_ms.x, 0.0)
    w_ms = w_ms / w_ms.sum()
    ms_ret = float(w_ms @ mu)
    ms_vol = float(np.sqrt(w_ms @ sigma @ w_ms))
    ms_sharpe = (ms_ret - rf) / ms_vol if ms_vol > 1e-10 else 0.0

    # --- Capital Market Line ---
    cml = None
    if risk_free_rate is not None:
        # CML: E[r_p] = rf + (E[r_ms] - rf) / sigma_ms * sigma_p
        cml_slope = (ms_ret - rf) / ms_vol if ms_vol > 1e-10 else 0.0
        cml_points = []
        for vol_pct in np.linspace(0, ms_vol * 2.0, 20):
            cml_ret = rf + cml_slope * vol_pct
            cml_points.append({
                "risk": round(float(vol_pct), 6),
                "return": round(float(cml_ret), 6),
            })
        cml = {
            "slope": round(cml_slope, 6),
            "tangency_portfolio": {
                "return": round(ms_ret, 6),
                "risk": round(ms_vol, 6),
                "sharpe": round(ms_sharpe, 6),
                "weights": [round(float(w), 6) for w in w_ms],
            },
            "points": cml_points,
        }

    return {
        "method": "Multi-Objective Pareto Frontier",
        "num_assets": n,
        "num_frontier_points": len(frontier),
        "risk_free_rate": rf,
        "frontier": frontier,
        "minimum_variance_portfolio": {
            "weights": [round(float(w), 6) for w in w_mv],
            "return": round(mv_ret, 6),
            "risk": round(mv_vol, 6),
            "sharpe": round((mv_ret - rf) / mv_vol, 6) if mv_vol > 1e-10 else 0.0,
        },
        "max_sharpe_portfolio": {
            "weights": [round(float(w), 6) for w in w_ms],
            "return": round(ms_ret, 6),
            "risk": round(ms_vol, 6),
            "sharpe": round(ms_sharpe, 6),
        },
        "capital_market_line": cml,
        "return_range": {
            "min": round(mv_ret, 6),
            "max": round(mr_ret, 6),
        },
    }


# ---------------------------------------------------------------------------
# 5. Advanced Optimization Demo
# ---------------------------------------------------------------------------

def advanced_optimization_demo() -> dict:
    """Demo with 8 TSE stocks across 4 sectors.

    Sectors: Banking, Petrochemical, Automotive, Technology
    Stocks: 2 per sector.
    """
    np.random.seed(42)

    asset_names = [
        "Melat Bank", "Saderat Bank",       # Banking
        "Sanat Petrochemical", "Bandar Petrochemical",  # Petrochemical
        "Iran Khodro", "Saipa",             # Automotive
        "Fars Telecom", "Mabna ICT",        # Technology
    ]

    n = len(asset_names)
    sectors = {
        "Banking": [0, 1],
        "Petrochemical": [2, 3],
        "Automotive": [4, 5],
        "Technology": [6, 7],
    }

    # Realistic expected annual returns (TSE context)
    mu = np.array([0.22, 0.18, 0.28, 0.25, 0.15, 0.12, 0.32, 0.35])

    # Build a realistic covariance matrix
    base_vol = np.array([0.20, 0.22, 0.30, 0.28, 0.25, 0.28, 0.35, 0.40])
    # Sector correlations
    sector_corr = np.array([
        [1.0, 0.7, 0.3, 0.1, 0.2, 0.15, 0.1, 0.05],
        [0.7, 1.0, 0.25, 0.1, 0.15, 0.1, 0.1, 0.05],
        [0.3, 0.25, 1.0, 0.65, 0.2, 0.15, 0.15, 0.1],
        [0.1, 0.1, 0.65, 1.0, 0.15, 0.1, 0.1, 0.08],
        [0.2, 0.15, 0.2, 0.15, 1.0, 0.6, 0.2, 0.15],
        [0.15, 0.1, 0.15, 0.1, 0.6, 1.0, 0.15, 0.1],
        [0.1, 0.1, 0.15, 0.1, 0.2, 0.15, 1.0, 0.55],
        [0.05, 0.05, 0.1, 0.08, 0.15, 0.1, 0.55, 1.0],
    ])
    D = np.diag(base_vol)
    sigma = D @ sector_corr @ D
    sigma = (sigma + sigma.T) / 2  # ensure symmetry

    mu_list = mu.tolist()
    sigma_list = sigma.tolist()

    # ---- 1. SOCP with sector limits ----
    sector_limits = {
        "Banking": {"assets": [0, 1], "max": 0.35},
        "Petrochemical": {"assets": [2, 3], "max": 0.30},
        "Automotive": {"assets": [4, 5], "max": 0.25},
        "Technology": {"assets": [6, 7], "max": 0.35},
    }
    socp_result = socp_portfolio(
        mu_list, sigma_list,
        constraints={
            "max_turnover": 0.8,
            "min_weight": 0.02,
            "max_weight": 0.30,
            "sector_limits": sector_limits,
            "transaction_costs": 0.002,
        },
        risk_free_rate=0.05,
        current_weights=[0.15, 0.15, 0.12, 0.10, 0.13, 0.10, 0.15, 0.10],
    )

    # ---- 2. Robust vs Nominal ----
    robust_result = robust_optimization(
        mu_list, sigma_list,
        uncertainty_budget=0.08,
        delta=0.95,
        risk_free_rate=0.05,
    )

    # ---- 3. HRP ----
    # Generate 120-day return series for HRP
    L = np.linalg.cholesky(sigma)
    raw_returns = (np.random.randn(120, n) @ L.T) + mu
    # Scale to daily
    daily_returns = (raw_returns - mu) / np.sqrt(252)
    hrp_result = hierarchical_risk_parity(
        daily_returns.tolist(), asset_names, risk_free_rate=0.05
    )

    # ---- 4. Pareto Frontier ----
    pareto_result = multi_objective_optimization(
        mu_list, sigma_list, n_points=30, risk_free_rate=0.05
    )

    return {
        "demo": "Advanced Optimization Engine — 8 TSE Stocks across 4 Sectors",
        "assets": asset_names,
        "sectors": sectors,
        "expected_returns": [round(float(r), 4) for r in mu],
        "socp_optimization": socp_result,
        "robust_optimization": robust_result,
        "hrp_optimization": hrp_result,
        "pareto_frontier": pareto_result,
    }
