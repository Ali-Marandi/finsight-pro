"""Fuzzy AHP & Fuzzy TOPSIS — Multi-Criteria Decision Making for Financial Analysis.

Provides offline-capable MCDM tools for ranking stocks, evaluating
investment opportunities, and portfolio selection under uncertainty.
All computations run locally — no data leaves the machine.
"""

import numpy as np
from typing import Optional


def _triangular_fuzzy_to_crisp(fuzzy_matrix: list[list[float]]) -> np.ndarray:
    """Convert a list of triangular fuzzy number matrices to crisp values.

    Input shape: (criteria, criteria, 3) where last dim is (l, m, u).
    Uses centroid method: (l + m + u) / 3.
    """
    arr = np.array(fuzzy_matrix)
    if arr.ndim == 3 and arr.shape[-1] == 3:
        return (arr[:, :, 0] + arr[:, :, 1] + arr[:, :, 2]) / 3.0
    return np.array(fuzzy_matrix)


def _normalize_pairwise(matrix: np.ndarray) -> np.ndarray:
    """Normalize a pairwise comparison matrix (column-wise normalization)."""
    col_sums = matrix.sum(axis=0)
    return matrix / col_sums


def _compute_weights(matrix: np.ndarray) -> np.ndarray:
    """Compute priority weights from normalized pairwise matrix (row averages)."""
    normalized = _normalize_pairwise(matrix)
    return normalized.mean(axis=1)


def _consistency_ratio(matrix: np.ndarray, weights: np.ndarray) -> dict:
    """Calculate Consistency Index (CI) and Consistency Ratio (CR).

    Uses Saaty's Random Index (RI) table for n=1..15.
    """
    n = len(weights)
    RI_TABLE = {
        1: 0.0, 2: 0.0, 3: 0.58, 4: 0.90, 5: 1.12,
        6: 1.24, 7: 1.32, 8: 1.41, 9: 1.45, 10: 1.49,
        11: 1.51, 12: 1.48, 13: 1.56, 14: 1.57, 15: 1.59,
    }
    ri = RI_TABLE.get(n, 1.59)

    # Weighted sum vector
    aw = matrix @ weights
    # Consistency vector
    lambda_vec = aw / weights
    # Max eigenvalue (approximate)
    lambda_max = float(np.mean(lambda_vec))

    ci = (lambda_max - n) / (n - 1) if n > 1 else 0.0
    cr = ci / ri if ri > 0 else 0.0

    return {
        "lambda_max": round(lambda_max, 4),
        "ci": round(ci, 6),
        "ri": ri,
        "cr": round(cr, 6),
        "consistent": cr < 0.10,
    }


def fuzzy_ahp(
    criteria_matrix: list[list[float]],
    criteria_names: list[str],
) -> dict:
    """Fuzzy AHP for deriving criteria weights.

    Args:
        criteria_matrix: Pairwise comparison matrix (n x n).
            If 2D (n x n), treated as crisp Saaty scale.
            If 3D (n x n x 3), treated as triangular fuzzy numbers (l, m, u).
        criteria_names: Names of criteria.

    Returns:
        Criteria weights, consistency analysis, and ranking.
    """
    matrix = np.array(criteria_matrix, dtype=float)
    n = matrix.shape[0]

    if n != len(criteria_names):
        return {"error": f"Matrix size ({n}) does not match criteria count ({len(criteria_names)})"}

    # Handle fuzzy input
    if matrix.ndim == 3 and matrix.shape[-1] == 3:
        crisp_matrix = _triangular_fuzzy_to_crisp(criteria_matrix)
        is_fuzzy = True
    else:
        crisp_matrix = matrix
        is_fuzzy = False

    # Compute weights
    weights = _compute_weights(crisp_matrix)

    # Consistency check
    consistency = _consistency_ratio(crisp_matrix, weights)

    # Rank criteria
    ranked_indices = np.argsort(-weights)
    ranking = [
        {
            "rank": i + 1,
            "name": criteria_names[idx],
            "weight": round(float(weights[idx]), 4),
            "weight_pct": round(float(weights[idx] * 100), 2),
        }
        for i, idx in enumerate(ranked_indices)
    ]

    return {
        "method": "Fuzzy AHP" if is_fuzzy else "AHP",
        "criteria_count": n,
        "weights": [round(float(w), 4) for w in weights],
        "criteria_names": criteria_names,
        "ranking": ranking,
        "consistency": consistency,
        "is_fuzzy": is_fuzzy,
        "recommendation": (
            "Consistent pairwise comparison (CR < 0.10). Weights are reliable."
            if consistency["consistent"]
            else "Inconsistent comparison (CR >= 0.10). Consider revising pairwise judgments."
        ),
    }


def fuzzy_topsis(
    decision_matrix: list[list[float]],
    criteria_names: list[str],
    alternative_names: list[str],
    criteria_weights: list[float],
    benefit_criteria: list[bool] | None = None,
) -> dict:
    """Fuzzy TOPSIS for ranking alternatives.

    Args:
        decision_matrix: Performance ratings (alternatives x criteria).
            If 2D (m x n), treated as crisp values.
            If 3D (m x n x 3), treated as triangular fuzzy numbers.
        criteria_names: Names of criteria.
        alternative_names: Names of alternatives (stocks, projects, etc.).
        criteria_weights: Weight of each criterion (from AHP or manual).
        benefit_criteria: True for benefit (higher=better), False for cost.
    """
    matrix = np.array(decision_matrix, dtype=float)
    n_alt = matrix.shape[0]
    n_crit = matrix.shape[1]

    if n_alt != len(alternative_names):
        return {"error": f"Alternatives count ({n_alt}) does not match names ({len(alternative_names)})"}
    if n_crit != len(criteria_names):
        return {"error": f"Criteria count ({n_crit}) does not match names ({len(criteria_names)})"}
    if len(criteria_weights) != n_crit:
        return {"error": f"Weights count ({len(criteria_weights)}) does not match criteria ({n_crit})"}

    # Default: all benefit criteria
    if benefit_criteria is None:
        benefit_criteria = [True] * n_crit

    # Handle fuzzy input
    if matrix.ndim == 3 and matrix.shape[-1] == 3:
        crisp_matrix = _triangular_fuzzy_to_crisp(decision_matrix)
        is_fuzzy = True
    else:
        crisp_matrix = matrix
        is_fuzzy = False

    weights = np.array(criteria_weights)

    # Step 1: Normalize (vector normalization)
    norms = np.sqrt((crisp_matrix ** 2).sum(axis=0))
    norms[norms == 0] = 1.0  # avoid division by zero
    normalized = crisp_matrix / norms

    # Step 2: Weighted normalized
    weighted = normalized * weights

    # Step 3: Ideal and anti-ideal solutions
    ideal = np.zeros(n_crit)
    anti_ideal = np.zeros(n_crit)
    for j in range(n_crit):
        if benefit_criteria[j]:
            ideal[j] = weighted[:, j].max()
            anti_ideal[j] = weighted[:, j].min()
        else:
            ideal[j] = weighted[:, j].min()
            anti_ideal[j] = weighted[:, j].max()

    # Step 4: Distances
    d_positive = np.sqrt(((weighted - ideal) ** 2).sum(axis=1))
    d_negative = np.sqrt(((weighted - anti_ideal) ** 2).sum(axis=1))

    # Step 5: Closeness coefficient
    total_dist = d_positive + d_negative
    total_dist[total_dist == 0] = 1.0
    cc = d_negative / total_dist

    # Ranking
    ranked_indices = np.argsort(-cc)
    ranking = [
        {
            "rank": i + 1,
            "name": alternative_names[idx],
            "closeness": round(float(cc[idx]), 4),
            "d_positive": round(float(d_positive[idx]), 4),
            "d_negative": round(float(d_negative[idx]), 4),
        }
        for i, idx in enumerate(ranked_indices)
    ]

    return {
        "method": "Fuzzy TOPSIS" if is_fuzzy else "TOPSIS",
        "alternatives_count": n_alt,
        "criteria_count": n_crit,
        "closeness_coefficients": [round(float(c), 4) for c in cc],
        "ideal_solution": [round(float(v), 4) for v in ideal],
        "anti_ideal_solution": [round(float(v), 4) for v in anti_ideal],
        "ranking": ranking,
        "is_fuzzy": is_fuzzy,
        "best_alternative": alternative_names[ranked_indices[0]],
        "best_score": round(float(cc[ranked_indices[0]]), 4),
    }


def stock_ranking(
    stocks: list[dict],
    criteria: list[str] | None = None,
) -> dict:
    """Convenience function: Rank stocks using Fuzzy AHP + TOPSIS pipeline.

    Args:
        stocks: List of stock dicts with financial metrics.
            Each dict should have keys matching criteria.
            Example: [{"name": "Stock A", "pe": 12, "roe": 0.15, "debt_ratio": 0.4}, ...]
        criteria: List of metric keys to use. If None, auto-detects numeric fields.

    Returns:
        Combined AHP weights + TOPSIS ranking.
    """
    if not stocks:
        return {"error": "No stocks provided"}

    # Auto-detect criteria from first stock
    if criteria is None:
        criteria = [k for k, v in stocks[0].items() if isinstance(v, (int, float)) and k != "name"]

    alt_names = [s.get("name", f"Stock {i+1}") for i, s in enumerate(stocks)]
    n_crit = len(criteria)

    # Build decision matrix
    decision_matrix = []
    for stock in stocks:
        row = [float(stock.get(c, 0)) for c in criteria]
        decision_matrix.append(row)

    # Auto-determine benefit/cost
    benefit_criteria = []
    for c in criteria:
        lower_better = any(kw in c.lower() for kw in ["debt", "ratio_debt", "pe", "p/e", "pb", "p/b", "risk", "volatility"])
        benefit_criteria.append(not lower_better)

    # Build AHP pairwise matrix using correlation-based approximation
    data_matrix = np.array(decision_matrix)
    corr = np.corrcoef(data_matrix.T) if n_crit > 1 else np.ones((n_crit, n_crit))

    # Convert correlation to Saaty scale (1-9)
    saaty_matrix = np.ones((n_crit, n_crit))
    for i in range(n_crit):
        for j in range(n_crit):
            if i != j:
                # Map correlation [-1, 1] to Saaty [1/9, 9]
                r = max(-0.99, min(0.99, corr[i, j] if not np.isnan(corr[i, j]) else 0))
                if r >= 0:
                    saaty_matrix[i, j] = 1 + 8 * r
                else:
                    saaty_matrix[i, j] = 1.0 / (1 + 8 * abs(r))

    # Run AHP
    ahp_result = fuzzy_ahp(saaty_matrix.tolist(), criteria)
    if "error" in ahp_result:
        return ahp_result

    # Run TOPSIS with AHP weights
    topsis_result = fuzzy_topsis(
        decision_matrix,
        criteria,
        alt_names,
        ahp_result["weights"],
        benefit_criteria,
    )
    if "error" in topsis_result:
        return topsis_result

    return {
        "method": "Fuzzy AHP-TOPSIS",
        "stocks_analyzed": len(stocks),
        "criteria_used": criteria,
        "ahp_weights": ahp_result["weights"],
        "ahp_ranking": ahp_result["ranking"],
        "consistency": ahp_result["consistency"],
        "topsis_ranking": topsis_result["ranking"],
        "best_stock": topsis_result["best_alternative"],
        "best_score": topsis_result["best_score"],
    }
