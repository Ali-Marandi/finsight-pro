"""Causal Inference & Information Theory Engine for FinSight Pro.

Implements Granger causality (hand-rolled VAR), orthogonalized impulse
response functions, transfer entropy, mutual information, and a PC-algorithm
inspired causal discovery procedure.

All computations are offline/local using only numpy and scipy.
"""

import numpy as np
from scipy import stats, linalg


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

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


def _r(v, decimals=4):
    """Round a float to the given number of decimal places."""
    return round(float(v), decimals)


def _ensure_2d(series_list):
    """Convert list of 1-D arrays to a 2-D numpy array (T x N)."""
    return np.column_stack([np.asarray(s, dtype=np.float64).ravel() for s in series_list])


def _returns_from_prices(prices):
    """Compute simple percentage returns from a price series."""
    p = np.asarray(prices, dtype=np.float64).ravel()
    return np.diff(np.log(p))  # log-returns


# ---------------------------------------------------------------------------
# 1. Granger Causality via hand-rolled VAR
# ---------------------------------------------------------------------------

def _fit_var(Y, p):
    """Fit a VAR(p) model using OLS (numpy lstsq).

    Parameters
    ----------
    Y : ndarray, shape (T, K)
    p : int, lag order

    Returns
    -------
    A_list : list of ndarray, each (K, K) — coefficient matrices
    resid  : ndarray (T-p, K) — residuals
    Y_lagged : ndarray (T-p, K*p) — lagged regressors
    """
    T, K = Y.shape
    if T <= p + 1:
        raise ValueError("Not enough observations for the given lag order")

    # Build lagged matrix: each row is [y_{t-1}, ..., y_{t-p}]
    n_eff = T - p
    Y_lagged = np.zeros((n_eff, K * p))
    Y_target = Y[p:]  # shape (n_eff, K)

    for lag in range(1, p + 1):
        Y_lagged[:, (lag - 1) * K : lag * K] = Y[p - lag : T - lag]

    # OLS: Y_target = Y_lagged @ B + resid
    # Solve for B (K*p x K)
    B, _, _, _ = np.linalg.lstsq(Y_lagged, Y_target, rcond=None)
    resid = Y_target - Y_lagged @ B

    # Extract coefficient matrices
    A_list = []
    for lag in range(p):
        A_list.append(B[lag * K : (lag + 1) * K, :].T)  # each (K, K)

    return A_list, resid, Y_lagged


def _var_ic(Y, max_lag):
    """Select optimal lag via AIC and BIC for VAR."""
    T, K = Y.shape
    results = []

    for p in range(1, max_lag + 1):
        try:
            _, resid, _ = _fit_var(Y, p)
            n_eff = T - p
            Sigma = (resid.T @ resid) / n_eff
            log_det = np.log(np.linalg.det(Sigma + 1e-12 * np.eye(K)))

            n_params = p * K * K
            aic = log_det + 2 * n_params / n_eff
            bic = log_det + np.log(n_eff) * n_params / n_eff
            results.append((p, aic, bic, log_det))
        except Exception:
            continue

    if not results:
        return 1, 1, [(1, 0.0, 0.0)]

    aic_best = min(results, key=lambda x: x[1])
    bic_best = min(results, key=lambda x: x[2])
    all_ic = [(r[0], _r(r[1]), _r(r[2])) for r in results]

    return aic_best[0], bic_best[0], all_ic


def _granger_f_test(Y, i, j, p):
    """Test if variable j Granger-causes variable i at lag p.

    Restricted model: y_i(t) = sum_{k=1}^{p} a_k * y_i(t-k) + e
    Unrestricted model: y_i(t) = sum_{k=1}^{p} [a_k * y_i(t-k) + b_k * y_j(t-k)] + e

    Returns F-statistic and p-value.
    """
    T = Y.shape[0]
    n = T - p
    if n <= p + 2:
        return np.nan, 1.0

    yi = Y[:, i]
    yj = Y[:, j]

    # Build regressors for unrestricted model
    X_unres = np.zeros((n, 2 * p))
    for lag in range(1, p + 1):
        X_unres[:, 2 * (lag - 1)] = yi[p - lag : T - lag]
        X_unres[:, 2 * (lag - 1) + 1] = yj[p - lag : T - lag]
    y_target = yi[p:]

    # Unrestricted OLS
    beta_u, _, _, _ = np.linalg.lstsq(X_unres, y_target, rcond=None)
    resid_u = y_target - X_unres @ beta_u
    rss_u = np.sum(resid_u ** 2)

    # Restricted model (only own lags)
    X_res = X_unres[:, 0::2]  # columns 0, 2, 4, ... (yi lags)
    beta_r, _, _, _ = np.linalg.lstsq(X_res, y_target, rcond=None)
    resid_r = y_target - X_res @ beta_r
    rss_r = np.sum(resid_r ** 2)

    if rss_u < 1e-15:
        return 0.0, 1.0

    df1 = p  # number of restrictions
    df2 = n - 2 * p  # residual df
    if df2 <= 0:
        return np.nan, 1.0

    F = ((rss_r - rss_u) / df1) / (rss_u / df2)
    p_value = 1.0 - stats.f.cdf(F, df1, df2)

    return float(F), float(p_value)


def granger_causality(series_list, max_lag=5, significance_level=0.05):
    """Test Granger causality between multiple time series using VAR model.

    For each ordered pair (i, j), fit restricted and unrestricted models
    and compute an F-test.  A significant p-value means j Granger-causes i.

    Parameters
    ----------
    series_list : list of list[float] — N price/return series (same length)
    max_lag : int — maximum lag to test (default 5)
    significance_level : float — threshold for significance (default 0.05)

    Returns
    -------
    dict with causality_matrix, significant_links, lag_results, optimal_lag
    """
    Y = _ensure_2d(series_list)
    T, K = Y.shape

    # Optimal lag selection
    aic_lag, bic_lag, all_ic = _var_ic(Y, max_lag)
    opt_lag = aic_lag  # use AIC as default

    # P-value matrix: pval[i][j] = p-value for "j Granger-causes i"
    pval_matrix = np.full((K, K), np.nan)
    f_matrix = np.full((K, K), np.nan)

    # Per-lag results
    lag_results = {}
    for p in range(1, max_lag + 1):
        lag_pvals = np.full((K, K), np.nan)
        lag_fs = np.full((K, K), np.nan)
        for i in range(K):
            for j in range(K):
                if i != j:
                    f_val, pv = _granger_f_test(Y, i, j, p)
                    lag_pvals[i, j] = pv
                    lag_fs[i, j] = f_val
        lag_results[str(p)] = {
            "p_values": _to_native(lag_pvals),
            "f_statistics": _to_native(lag_fs),
        }

    # Use optimal lag for the main matrix
    for i in range(K):
        for j in range(K):
            if i != j:
                f_val, pv = _granger_f_test(Y, i, j, opt_lag)
                pval_matrix[i, j] = pv
                f_matrix[i, j] = f_val

    # Significant causal links
    significant_links = []
    for i in range(K):
        for j in range(K):
            if i != j and not np.isnan(pval_matrix[i, j]) and pval_matrix[i, j] < significance_level:
                significant_links.append({
                    "source": j,
                    "target": i,
                    "p_value": _r(pval_matrix[i, j]),
                    "f_statistic": _r(f_matrix[i, j]),
                    "lag": opt_lag,
                })

    return _to_native({
        "optimal_lag": {
            "aic": aic_lag,
            "bic": bic_lag,
            "selected": opt_lag,
            "all_criteria": all_ic,
        },
        "causality_pvalues": pval_matrix,
        "causality_f_statistics": f_matrix,
        "significant_links": significant_links,
        "n_variables": K,
        "n_observations": T,
        "significance_level": significance_level,
        "lag_results": lag_results,
    })


# ---------------------------------------------------------------------------
# 2. Impulse Response Functions & FEVD
# ---------------------------------------------------------------------------

def impulse_response(series_list, n_lags=2, horizon=10):
    """Compute Orthogonalized Impulse Response Functions from VAR model.

    Uses Cholesky decomposition of the residual covariance matrix to
    orthogonalize the shocks.

    Parameters
    ----------
    series_list : list of list[float] — N price/return series
    n_lags : int — VAR lag order (default 2)
    horizon : int — IRF horizon (default 10)

    Returns
    -------
    dict with irf_matrices, cumulative_irf, fevd
    """
    Y = _ensure_2d(series_list)
    T, K = Y.shape

    # Fit VAR
    A_list, resid, _ = _fit_var(Y, n_lags)
    Sigma = (resid.T @ resid) / (T - n_lags)

    # Cholesky decomposition for orthogonalization
    try:
        P = np.linalg.cholesky(Sigma)  # Sigma = P @ P.T, P is lower triangular
    except np.linalg.LinAlgError:
        # If not PD, use nearest PD approximation
        eigvals, eigvecs = np.linalg.eigh(Sigma)
        eigvals = np.maximum(eigvals, 1e-8)
        Sigma = eigvecs @ np.diag(eigvals) @ eigvecs.T
        P = np.linalg.cholesky(Sigma)

    # Build companion form
    # Phi = [[A1, A2, ..., Ap],
    #        [I,  0,  ..., 0 ],
    #        [0,  I,  ..., 0 ],
    #        [0,  0,  ..., 0 ]]
    kp = K * n_lags
    Phi = np.zeros((kp, kp))
    for lag in range(n_lags):
        Phi[0:K, lag * K : (lag + 1) * K] = A_list[lag]
    for lag in range(n_lags - 1):
        Phi[(lag + 1) * K : (lag + 2) * K, lag * K : (lag + 1) * K] = np.eye(K)

    # Compute IRF: Psi_h = Phi^h @ [P; 0; ...; 0]
    # The bottom block selects the first K rows (corresponding to variables)
    selection = np.zeros((kp, K))
    selection[0:K, :] = P

    irf = np.zeros((horizon + 1, K, K))  # irf[h, i, j] = response of i to shock in j
    cumulative_irf = np.zeros((horizon + 1, K, K))
    Phi_power = np.eye(kp)

    for h in range(horizon + 1):
        if h == 0:
            irf[h] = P  # impact response
        else:
            Phi_power = Phi_power @ Phi
            irf[h] = Phi_power[0:K, :] @ selection

        if h == 0:
            cumulative_irf[h] = irf[h]
        else:
            cumulative_irf[h] = cumulative_irf[h - 1] + irf[h]

    # Forecast Error Variance Decomposition (FEVD)
    # At horizon h, variance of forecast error for variable i decomposed into
    # contributions from each shock j
    total_var = np.zeros((horizon + 1, K))
    contrib = np.zeros((horizon + 1, K, K))

    for h in range(horizon + 1):
        # MSE = sum_{s=0}^{h} Psi_s @ Sigma @ Psi_s.T
        # With orthogonalization: MSE = sum_{s=0}^{h} Psi_s @ P @ P.T @ Psi_s.T
        # Contribution of shock j to variable i: sum_{s=0}^{h} (Psi_s @ P)[i, j]^2
        for i in range(K):
            for j in range(K):
                contrib[h, i, j] = sum(irf[s, i, j] ** 2 for s in range(h + 1))
            total_var[h, i] = sum(contrib[h, i, :])

    fevd_pct = np.zeros((horizon + 1, K, K))
    for h in range(horizon + 1):
        for i in range(K):
            if total_var[h, i] > 1e-15:
                fevd_pct[h, i, :] = contrib[h, i, :] / total_var[h, i] * 100.0

    return _to_native({
        "n_variables": K,
        "n_observations": T,
        "n_lags": n_lags,
        "horizon": horizon,
        "irf": _to_native(irf),
        "cumulative_irf": _to_native(cumulative_irf),
        "fevd_percent": _to_native(fevd_pct),
        "residual_covariance": _to_native(Sigma),
        "cholesky_factor": _to_native(P),
    })


# ---------------------------------------------------------------------------
# 3. Transfer Entropy
# ---------------------------------------------------------------------------

def _histogram_entropy(x, bins):
    """Compute Shannon entropy of a 1-D discretized series."""
    counts, _ = np.histogram(x, bins=bins, density=False)
    probs = counts[counts > 0] / len(x)
    return -np.sum(probs * np.log2(probs))


def _joint_histogram_entropy(x, y, bins):
    """Compute joint entropy H(X, Y) using 2-D histogram."""
    counts, _, _ = np.histogram2d(x, y, bins=bins)
    probs = counts[counts > 0] / len(x)
    return -np.sum(probs * np.log2(probs))


def _transfer_entropy_univariate(x, y, k, l, bins):
    """TE(X -> Y) using histogram-based probability estimation.

    TE(X->Y) = H(Y_t | Y_{t-1}^{t-k}) - H(Y_t | Y_{t-1}^{t-k}, X_{t-1}^{t-l})
    """
    T = min(len(x), len(y))
    x = x[:T]
    y = y[:T]

    max_hist = max(k, l)
    if T <= max_hist + 1:
        return 0.0

    # Build target vectors: y_t
    yt = y[max_hist:]

    # Build target history: (y_{t-1}, ..., y_{t-k})
    y_hist = np.zeros((len(yt), k))
    for i in range(k):
        y_hist[:, i] = y[max_hist - 1 - i : T - 1 - i]

    # Build source history: (x_{t-1}, ..., x_{t-l})
    x_hist = np.zeros((len(yt), l))
    for i in range(l):
        x_hist[:, i] = x[max_hist - 1 - i : T - 1 - i]

    # TE = H(yt | y_hist) - H(yt | y_hist, x_hist)
    #    = H(yt, y_hist) - H(y_hist) - H(yt, y_hist, x_hist) + H(y_hist, x_hist)

    h_yt_yhist = 0.0
    h_yhist = 0.0
    h_yt_yhist_xhist = 0.0
    h_yhist_xhist = 0.0

    for ki in range(k):
        h_yt_yhist += _joint_histogram_entropy(yt, y_hist[:, ki], bins)
        h_yhist += _histogram_entropy(y_hist[:, ki], bins)

    h_yt_yhist -= (k - 1) * _histogram_entropy(yt, bins)
    h_yhist -= (k - 1) * _histogram_entropy(y_hist[:, 0], bins)

    # Joint of (yt, y_hist, x_hist) via chain rule
    h_yt_yhist_xhist = _joint_histogram_entropy(yt, y_hist[:, 0], bins)
    for ki in range(1, k):
        h_yt_yhist_xhist += _joint_histogram_entropy(yt, y_hist[:, ki], bins)
    h_yt_yhist_xhist -= (k - 1) * _histogram_entropy(yt, bins)

    for li in range(l):
        h_yt_yhist_xhist += _joint_histogram_entropy(yt, x_hist[:, li], bins)
        h_yt_yhist_xhist -= _histogram_entropy(yt, bins)

    # Joint of (y_hist, x_hist)
    h_yhist_xhist = _histogram_entropy(y_hist[:, 0], bins)
    for ki in range(1, k):
        h_yhist_xhist += _joint_histogram_entropy(y_hist[:, 0], y_hist[:, ki], bins)
        h_yhist_xhist -= _histogram_entropy(y_hist[:, 0], bins)

    for li in range(l):
        h_yhist_xhist += _joint_histogram_entropy(y_hist[:, 0], x_hist[:, li], bins)
        h_yhist_xhist -= _histogram_entropy(y_hist[:, 0], bins)

    te = (h_yt_yhist - h_yhist) - (h_yt_yhist_xhist - h_yhist_xhist)
    return max(0.0, float(te))


def _conditional_transfer_entropy(x, y, z, k, l, bins):
    """Conditional TE(X -> Y | Z) using a simpler histogram approach.

    Approximate by computing TE on residuals of y regressed on z.
    """
    T = min(len(x), len(y), len(z))
    x = x[:T]
    y = y[:T]
    z = z[:T]

    # Regress y on z to remove confounding, use residuals
    z_col = z.reshape(-1, 1)
    z_aug = np.column_stack([np.ones(T), z_col])
    beta, _, _, _ = np.linalg.lstsq(z_aug, y, rcond=None)
    y_resid = y - z_aug @ beta

    # Also residualize x on z
    beta_x, _, _, _ = np.linalg.lstsq(z_aug, x, rcond=None)
    x_resid = x - z_aug @ beta_x

    return _transfer_entropy_univariate(x_resid, y_resid, k, l, bins)


def transfer_entropy(series_x, series_y, k=1, l=1, bins=10, series_z=None, n_permutations=100):
    """Compute transfer entropy TE(X -> Y).

    TE(X->Y) measures directed information flow from X to Y, beyond
    what is predicted by Y's own history.

    Parameters
    ----------
    series_x : list[float] — source series
    series_y : list[float] — target series
    k : int — history length of target (default 1)
    l : int — history length of source (default 1)
    bins : int — number of bins for histogram discretization (default 10)
    series_z : list[float] | None — conditioning series for conditional TE
    n_permutations : int — number of surrogate shuffles (default 100)

    Returns
    -------
    dict with te_value, significance, conditional_te
    """
    x = np.asarray(series_x, dtype=np.float64).ravel()
    y = np.asarray(series_y, dtype=np.float64).ravel()

    # Compute observed TE
    te_observed = _transfer_entropy_univariate(x, y, k, l, bins)

    # Surrogate testing: shuffle x to generate null distribution
    te_surrogates = np.zeros(n_permutations)
    rng = np.random.RandomState(42)
    for perm in range(n_permutations):
        x_shuffled = rng.permutation(x)
        te_surrogates[perm] = _transfer_entropy_univariate(x_shuffled, y, k, l, bins)

    p_value = float(np.mean(te_surrogates >= te_observed))
    surrogate_mean = float(np.mean(te_surrogates))
    surrogate_std = float(np.std(te_surrogates))
    z_score = float((te_observed - surrogate_mean) / surrogate_std) if surrogate_std > 1e-12 else 0.0

    result = {
        "te_x_to_y": _r(te_observed, 6),
        "surrogate_mean": _r(surrogate_mean, 6),
        "surrogate_std": _r(surrogate_std, 6),
        "z_score": _r(z_score, 4),
        "p_value": _r(p_value, 4),
        "significant_at_0.05": bool(p_value < 0.05),
        "n_permutations": n_permutations,
        "parameters": {"k": k, "l": l, "bins": bins},
    }

    # Reverse direction
    te_reverse = _transfer_entropy_univariate(y, x, l, k, bins)
    result["te_y_to_x"] = _r(te_reverse, 6)
    result["directional_asymmetry"] = _r(te_observed - te_reverse, 6)
    result["dominant_direction"] = "X -> Y" if te_observed > te_reverse else "Y -> X" if te_reverse > te_observed else "bidirectional"

    # Conditional TE
    if series_z is not None:
        z = np.asarray(series_z, dtype=np.float64).ravel()
        cte = _conditional_transfer_entropy(x, y, z, k, l, bins)
        result["conditional_te_x_to_y_given_z"] = _r(cte, 6)

    return result


# ---------------------------------------------------------------------------
# 4. Mutual Information
# ---------------------------------------------------------------------------

def _mi_histogram(x, y, bins):
    """Mutual information I(X;Y) via histogram method.

    I(X;Y) = H(X) + H(Y) - H(X,Y)
    """
    hx = _histogram_entropy(x, bins)
    hy = _histogram_entropy(y, bins)
    hxy = _joint_histogram_entropy(x, y, bins)
    mi = hx + hy - hxy
    return max(0.0, float(mi))


def _mi_knn(x, y, k=5):
    """KNN estimator for mutual information (Kraskov et al. 2004, estimator 1).

    I(X;Y) ≈ psi(k) - <psi(nx+1) + psi(ny+1)> + psi(N)
    where nx, ny are counts of points within the max-distance.
    """
    from scipy.special import psi, digamma

    N = len(x)
    if N <= k + 1:
        return 0.0

    # Build joint space
    joint = np.column_stack([x, y])
    distances = np.zeros(N)

    for i in range(N):
        diffs = joint - joint[i]
        # Exclude self by setting to inf
        diffs[i] = np.inf
        dists = np.sqrt(np.sum(diffs ** 2, axis=1))
        sorted_dists = np.sort(dists)
        distances[i] = sorted_dists[k - 1]  # k-th nearest neighbor distance

    # Count neighbors in marginal spaces
    mi_sum = 0.0
    for i in range(N):
        eps = distances[i] + 1e-10
        nx = np.sum(np.abs(x - x[i]) < eps) - 1
        ny = np.sum(np.abs(y - y[i]) < eps) - 1
        mi_sum += digamma(nx + 1) + digamma(ny + 1)

    mi = digamma(k) - mi_sum / N + digamma(N)
    return max(0.0, float(mi))


def _conditional_mi(x, y, z, bins, method="histogram"):
    """Conditional mutual information I(X;Y|Z).

    I(X;Y|Z) = H(X,Z) + H(Y,Z) - H(X,Y,Z) - H(Z)
    """
    if method == "histogram":
        # Discretize z into bins to compute conditional
        z_binned = np.digitize(z, bins=np.linspace(z.min() - 1e-10, z.max() + 1e-10, bins + 1)) - 1
        z_binned = np.clip(z_binned, 0, bins - 1)

        cmi = 0.0
        for b in range(bins):
            mask = z_binned == b
            if mask.sum() > 5:
                cmi += (mask.sum() / len(z)) * _mi_histogram(x[mask], y[mask], bins=max(3, bins // 2))
        return max(0.0, float(cmi))
    else:
        # Approximate using KNN on residuals
        from scipy.special import digamma
        N = len(x)
        k = 5
        if N <= k + 1:
            return 0.0

        # Joint space (x, y, z)
        joint_xyz = np.column_stack([x, y, z])
        distances = np.zeros(N)
        for i in range(N):
            diffs = joint_xyz - joint_xyz[i]
            diffs[i] = np.inf
            dists = np.sqrt(np.sum(diffs ** 2, axis=1))
            distances[i] = np.sort(dists)[k - 1]

        mi_sum = 0.0
        for i in range(N):
            eps = distances[i] + 1e-10
            nx = np.sum(np.abs(x - x[i]) < eps) - 1
            ny = np.sum(np.abs(y - y[i]) < eps) - 1
            nz = np.sum(np.abs(z - z[i]) < eps) - 1
            mi_sum += digamma(nx + 1) + digamma(ny + 1) - digamma(nz + 1)

        from scipy.special import psi
        cmi = digamma(k) - mi_sum / N + psi(N)
        return max(0.0, float(cmi))


def mutual_information(series_x=None, series_y=None, series_list=None, bins=10, method="histogram", series_z=None):
    """Compute mutual information and conditional mutual information.

    Parameters
    ----------
    series_x : list[float] | None — first series
    series_y : list[float] | None — second series
    series_list : list[list[float]] | None — multiple series for pairwise MI matrix
    bins : int — number of bins (histogram method) or k neighbors (knn)
    method : str — 'histogram' or 'knn'
    series_z : list[float] | None — conditioning series

    Returns
    -------
    dict with mi values, normalized MI, conditional MI, and optionally pairwise matrix
    """
    result = {"method": method, "bins_or_k": bins}

    # Pairwise MI for two series
    if series_x is not None and series_y is not None:
        x = np.asarray(series_x, dtype=np.float64).ravel()
        y = np.asarray(series_y, dtype=np.float64).ravel()

        if method == "histogram":
            mi = _mi_histogram(x, y, bins)
        else:
            mi = _mi_knn(x, y, k=max(3, bins))

        hx = _histogram_entropy(x, bins)
        hy = _histogram_entropy(y, bins)
        h_max = max(hx, hy)
        nmi = mi / h_max if h_max > 1e-12 else 0.0

        result["mi"] = _r(mi, 6)
        result["mi_normalized"] = _r(min(nmi, 1.0), 6)
        result["h_x"] = _r(hx, 6)
        result["h_y"] = _r(hy, 6)

        # Conditional MI
        if series_z is not None:
            z = np.asarray(series_z, dtype=np.float64).ravel()
            cmi = _conditional_mi(x, y, z, bins, method)
            result["conditional_mi"] = _r(cmi, 6)

    # Pairwise MI matrix for multiple series
    if series_list is not None and len(series_list) > 1:
        data = _ensure_2d(series_list)
        T, K = data.shape
        mi_matrix = np.zeros((K, K))
        nmi_matrix = np.zeros((K, K))
        entropies = np.zeros(K)

        for i in range(K):
            entropies[i] = _histogram_entropy(data[:, i], bins)

        for i in range(K):
            for j in range(K):
                if i == j:
                    mi_matrix[i, j] = entropies[i]
                    nmi_matrix[i, j] = 1.0
                else:
                    if method == "histogram":
                        mi_matrix[i, j] = _mi_histogram(data[:, i], data[:, j], bins)
                    else:
                        mi_matrix[i, j] = _mi_knn(data[:, i], data[:, j], k=max(3, bins))
                    h_max = max(entropies[i], entropies[j])
                    nmi_matrix[i, j] = mi_matrix[i, j] / h_max if h_max > 1e-12 else 0.0

        result["n_variables"] = K
        result["entropies"] = _to_native(entropies)
        result["mi_matrix"] = _to_native(mi_matrix)
        result["nmi_matrix"] = _to_native(nmi_matrix)

    return result


# ---------------------------------------------------------------------------
# 5. Causal Discovery (PC-algorithm inspired)
# ---------------------------------------------------------------------------

def _partial_correlation(corr_matrix, i, j, S):
    """Compute partial correlation between i and j given separation set S.

    Uses the recursive formula:
    rho(i,j|S) = (rho(i,j) - rho(i,k)*rho(j,k)) / sqrt((1-rho(i,k)^2)*(1-rho(j,k)^2))
    where k is the last element of S.
    """
    if len(S) == 0:
        return corr_matrix[i, j]

    C = corr_matrix.copy()
    S_list = list(S)

    # Recursive formula using precision matrix approach
    # For efficiency, compute using the submatrix inversion
    idx = [i, j] + S_list
    sub_C = C[np.ix_(idx, idx)]

    try:
        P = np.linalg.inv(sub_C)
        # Partial correlation from precision matrix
        pc = -P[0, 1] / np.sqrt(abs(P[0, 0] * P[1, 1]))
        return float(np.clip(pc, -1, 1))
    except np.linalg.LinAlgError:
        return 0.0


def causal_discovery(corr_matrix, threshold=0.2):
    """PC-algorithm inspired causal discovery from correlation matrix.

    Parameters
    ----------
    corr_matrix : list[list[float]] — N x N correlation matrix
    threshold : float — partial correlation significance threshold (default 0.2)

    Returns
    -------
    dict with adjacency_matrix, separation_sets, orientations, topological_order
    """
    C = np.asarray(corr_matrix, dtype=np.float64)
    n = C.shape[0]

    if C.shape[0] != C.shape[1]:
        return {"error": "Correlation matrix must be square"}

    # Phase 1: Skeleton discovery
    # Start with complete undirected graph
    adj = np.ones((n, n), dtype=bool)
    np.fill_diagonal(adj, False)

    # Separation sets
    sep_sets = [[set() for _ in range(n)] for _ in range(n)]

    # Iterate over increasing conditioning set sizes
    for depth in range(n):
        changed = False
        edges_to_check = []
        for i in range(n):
            for j in range(i + 1, n):
                if adj[i, j]:
                    edges_to_check.append((i, j))

        for i, j in edges_to_check:
            if not adj[i, j]:
                continue

            # Find neighbors of i (excluding j)
            neighbors_i = [k for k in range(n) if adj[i, k] and k != j]

            # Try all subsets of size 'depth'
            if len(neighbors_i) >= depth:
                from itertools import combinations
                for S in combinations(neighbors_i, depth):
                    pc = abs(_partial_correlation(C, i, j, set(S)))
                    if pc < threshold:
                        adj[i, j] = False
                        adj[j, i] = False
                        sep_sets[i][j] = set(S)
                        sep_sets[j][i] = set(S)
                        changed = True
                        break

            if adj[i, j]:
                # Also try conditioning on neighbors of j
                neighbors_j = [k for k in range(n) if adj[j, k] and k != i]
                if len(neighbors_j) >= depth:
                    from itertools import combinations
                    for S in combinations(neighbors_j, depth):
                        pc = abs(_partial_correlation(C, i, j, set(S)))
                        if pc < threshold:
                            adj[i, j] = False
                            adj[j, i] = False
                            sep_sets[i][j] = set(S)
                            sep_sets[j][i] = set(S)
                            changed = True
                            break

        if not changed and depth > 0:
            break

    # Phase 2: Orientation rules
    # directed[i][j] = True means i -> j
    directed = np.zeros((n, n), dtype=bool)

    # Rule 1: Orient colliders — if i - k - j and k not in sep(i,j), orient i -> k <- j
    for k in range(n):
        # Find pairs (i, j) both connected to k but not to each other
        neighbors_k = [m for m in range(n) if adj[m, k]]
        for ii in range(len(neighbors_k)):
            for jj in range(ii + 1, len(neighbors_k)):
                i = neighbors_k[ii]
                j = neighbors_k[jj]
                if not adj[i, j] and k not in sep_sets[i][j]:
                    # Collider: i -> k <- j
                    directed[i, k] = True
                    directed[j, k] = True

    # Rule 2: Orient chains — if i -> k - j and i and j not adjacent, orient k -> j
    for i in range(n):
        for k in range(n):
            if directed[i, k] and adj[k, i]:  # i -> k
                for j in range(n):
                    if j != i and adj[k, j] and not adj[i, j] and not directed[j, k]:
                        if not directed[k, j]:
                            directed[k, j] = True

    # Rule 3: Orient away from colliders — if i -> k -> j and i - j, orient i -> j
    for i in range(n):
        for k in range(n):
            if directed[i, k]:
                for j in range(n):
                    if j != i and directed[k, j] and adj[i, j] and not directed[j, i]:
                        directed[i, j] = True

    # Build adjacency matrix: 2 = i->j, 1 = undirected i-j, 0 = no edge
    adj_final = np.zeros((n, n), dtype=int)
    for i in range(n):
        for j in range(n):
            if directed[i, j]:
                adj_final[i, j] = 2
            elif adj[i, j] and not directed[j, i]:
                adj_final[i, j] = 1  # undirected (if neither direction)

    # Topological ordering (Kahn's algorithm on directed edges)
    in_degree = np.sum(directed, axis=0).astype(int)
    queue = [i for i in range(n) if in_degree[i] == 0]
    topo_order = []
    while queue:
        node = queue.pop(0)
        topo_order.append(node)
        for j in range(n):
            if directed[node, j]:
                in_degree[j] -= 1
                if in_degree[j] == 0:
                    queue.append(j)

    # If there are cycles, add remaining nodes
    if len(topo_order) < n:
        for i in range(n):
            if i not in topo_order:
                topo_order.append(i)

    # Build edge list
    edges = []
    for i in range(n):
        for j in range(i + 1, n):
            if directed[i, j] and directed[j, i]:
                edges.append({"from": i, "to": j, "type": "bidirected"})
            elif directed[i, j]:
                edges.append({"from": i, "to": j, "type": "directed"})
            elif directed[j, i]:
                edges.append({"from": j, "to": i, "type": "directed"})
            elif adj[i, j]:
                edges.append({"from": i, "to": j, "type": "undirected"})

    # Format separation sets for output
    sep_sets_out = {}
    for i in range(n):
        for j in range(i + 1, n):
            if sep_sets[i][j]:
                sep_sets_out[f"{i}-{j}"] = sorted(list(sep_sets[i][j]))

    return _to_native({
        "n_variables": n,
        "skeleton_edges": int(adj.sum() // 2),
        "directed_edges": int(directed.sum()),
        "adjacency_matrix": adj_final.tolist(),
        "undirected_adjacency": adj.astype(int).tolist(),
        "directed_adjacency": directed.astype(int).tolist(),
        "edges": edges,
        "separation_sets": sep_sets_out,
        "topological_order": topo_order,
        "threshold": threshold,
    })


# ---------------------------------------------------------------------------
# 6. Demo with TSE-related time series
# ---------------------------------------------------------------------------

def causal_inference_demo():
    """Demo with 6 TSE-related time series showcasing causal structure recovery.

    Series:
      0 — PetroBank (petroleum stock, influenced by oil & FX)
      1 — OilTech (oil services, influenced by oil)
      2 — MellatBank (banking, influenced by interest rate & FX)
      3 — Oil Price (influences PetroBank, OilTech)
      4 — USD/IRR Exchange Rate (influences all stocks)
      5 — Interest Rate (influences MellatBank)

    Known causal structure:
      Oil -> PetroBank, Oil -> OilTech
      FX -> PetroBank, FX -> OilTech, FX -> MellatBank
      Interest -> MellatBank
    """
    np.random.seed(42)
    n_days = 504

    # Generate exogenous drivers
    oil_shocks = np.random.normal(0, 0.025, n_days)
    oil = 70.0 * np.exp(np.cumsum(oil_shocks))

    fx_shocks = np.random.normal(0, 0.008, n_days)
    fx_rate = 50000.0 * np.exp(np.cumsum(fx_shocks))

    interest_shocks = np.random.normal(0, 0.05, n_days)
    interest = 22.0 + np.cumsum(interest_shocks) * 0.1
    interest = np.clip(interest, 15.0, 35.0)

    # Generate stock returns with known causal structure
    # PetroBank: 30% oil, 20% FX, 50% idiosyncratic
    petro_returns = (0.30 * oil_shocks + 0.20 * fx_shocks
                     + 0.50 * np.random.normal(0, 0.015, n_days) + 0.0005)
    petro = 1000.0 * np.exp(np.cumsum(petro_returns))

    # OilTech: 40% oil, 15% FX, 45% idiosyncratic
    oiltech_returns = (0.40 * oil_shocks + 0.15 * fx_shocks
                       + 0.45 * np.random.normal(0, 0.018, n_days) + 0.0003)
    oiltech = 500.0 * np.exp(np.cumsum(oiltech_returns))

    # MellatBank: 10% oil, 25% FX, 30% interest, 35% idiosyncratic
    interest_change = np.diff(interest, prepend=interest[0]) / interest
    mellat_returns = (0.10 * oil_shocks + 0.25 * fx_shocks
                      - 0.30 * interest_change
                      + 0.35 * np.random.normal(0, 0.012, n_days) + 0.0004)
    mellat = 2000.0 * np.exp(np.cumsum(mellat_returns))

    # Build series list (using returns for causal analysis)
    returns_list = [
        petro_returns.tolist(),
        oiltech_returns.tolist(),
        mellat_returns.tolist(),
        oil_shocks.tolist(),
        fx_shocks.tolist(),
        interest_change.tolist(),
    ]

    names = ["PetroBank", "OilTech", "MellatBank", "Oil Price", "USD/IRR FX", "Interest Rate"]

    # --- Analysis 1: Granger Causality ---
    granger_result = granger_causality(returns_list, max_lag=5, significance_level=0.05)
    granger_result["variable_names"] = names

    # Interpret Granger results against known structure
    known_links = [
        (3, 0, "Oil -> PetroBank"),
        (3, 1, "Oil -> OilTech"),
        (4, 0, "FX -> PetroBank"),
        (4, 1, "FX -> OilTech"),
        (4, 2, "FX -> MellatBank"),
        (5, 2, "Interest -> MellatBank"),
    ]
    recovered = []
    for src, tgt, desc in known_links:
        pvals = granger_result["causality_pvalues"]
        pval = pvals[tgt][src] if tgt < len(pvals) and src < len(pvals[tgt]) else 1.0
        recovered.append({
            "known_causal_link": desc,
            "p_value": pval,
            "recovered": pval < 0.05,
        })
    granger_result["recovery_analysis"] = recovered

    # --- Analysis 2: Impulse Response ---
    irf_result = impulse_response(returns_list, n_lags=2, horizon=10)
    irf_result["variable_names"] = names

    # --- Analysis 3: Transfer Entropy (key pairs) ---
    te_results = []
    key_pairs = [
        (3, 0, "Oil -> PetroBank"),
        (3, 1, "Oil -> OilTech"),
        (4, 2, "FX -> MellatBank"),
        (5, 2, "Interest -> MellatBank"),
        (0, 1, "PetroBank -> OilTech (spurious)"),
    ]
    for src, tgt, desc in key_pairs:
        te = transfer_entropy(
            returns_list[src], returns_list[tgt],
            k=1, l=1, bins=10, n_permutations=100,
        )
        te["description"] = desc
        te["source"] = names[src]
        te["target"] = names[tgt]
        te_results.append(te)

    # --- Analysis 4: Mutual Information (pairwise matrix) ---
    mi_result = mutual_information(series_list=returns_list, bins=10, method="histogram")
    mi_result["variable_names"] = names

    # Conditional MI: Oil->PetroBank given FX
    cmi = mutual_information(
        series_x=returns_list[3], series_y=returns_list[0],
        series_z=returns_list[4], bins=10, method="histogram",
    )
    cmi["description"] = "MI(Oil, PetroBank | FX) — direct oil effect after removing FX"
    mi_result["conditional_mi_oil_petrobank_given_fx"] = cmi

    # --- Analysis 5: Causal Discovery ---
    # Build correlation matrix from returns
    data = np.column_stack([np.asarray(r) for r in returns_list])
    corr = np.corrcoef(data.T)
    corr_list = corr.tolist()

    cd_result = causal_discovery(corr_list, threshold=0.2)
    cd_result["variable_names"] = names

    # Build summary
    n_recovered = sum(1 for r in recovered if r["recovered"])
    summary = {
        "demo_name": "TSE Causal Structure Recovery",
        "n_days": n_days,
        "n_variables": 6,
        "variable_names": names,
        "known_causal_links": [d for _, _, d in known_links],
        "granger_links_recovered": f"{n_recovered}/{len(known_links)}",
        "recovery_rate": _r(n_recovered / len(known_links) * 100, 1),
    }

    return _to_native({
        "summary": summary,
        "granger_causality": granger_result,
        "impulse_response": irf_result,
        "transfer_entropy": te_results,
        "mutual_information": mi_result,
        "causal_discovery": cd_result,
    })
