"""ANFIS-Inspired Fuzzy Neural Engine for FinSight Pro.

Provides offline fuzzy inference, ANFIS hybrid learning, and fuzzy rule
extraction capabilities for credit scoring, bankruptcy prediction, and
general financial data analysis.  All computations run locally using only
numpy and scipy.
"""

import numpy as np
from scipy import optimize


# ---------------------------------------------------------------------------
# Helpers – triangular membership functions
# ---------------------------------------------------------------------------

def _trimf(x: float, params: list[float]) -> float:
    """Triangular membership function.  params = [a, b, c]."""
    a, b, c = params
    if c == a:
        return 0.0
    val = max(0.0, min((x - a) / (b - a) if b != a else 0.0,
                        (c - x) / (c - b) if c != b else 0.0))
    return float(np.clip(val, 0.0, 1.0))


def _trimf_vec(x: np.ndarray, params: list[float]) -> np.ndarray:
    """Vectorized triangular MF over an array."""
    a, b, c = params
    left = np.zeros_like(x, dtype=float)
    right = np.zeros_like(x, dtype=float)
    mask_l = (b != a)
    mask_r = (c != b)
    left[mask_l] = (x[mask_l] - a) / (b - a)
    right[mask_r] = (c - x[mask_r]) / (c - b)
    return np.clip(np.minimum(left, right), 0.0, 1.0)


def _trimf_grad(x: float, params: list[float]) -> dict[str, float]:
    """Gradients of triangular MF w.r.t. a, b, c."""
    a, b, c = params
    grads = {"a": 0.0, "b": 0.0, "c": 0.0}
    eps = 1e-12
    if a < x < b:
        grads["a"] = -(x - b) / ((b - a) ** 2 + eps)
        grads["b"] = (x - a) / ((b - a) ** 2 + eps)
    elif b <= x < c:
        grads["b"] = -(c - x) / ((c - b) ** 2 + eps)
        grads["c"] = (x - b) / ((c - b) ** 2 + eps)
    return grads


def _centroid_defuzz(x_range: np.ndarray, mf_values: np.ndarray) -> float:
    """Centroid (centre-of-gravity) defuzzification."""
    total = np.sum(mf_values)
    if total < 1e-12:
        return float(np.mean(x_range))
    return float(np.sum(x_range * mf_values) / total)


def _sigmoid(z: np.ndarray) -> np.ndarray:
    z = np.clip(z, -500, 500)
    return 1.0 / (1.0 + np.exp(-z))


# ---------------------------------------------------------------------------
# Feature definitions for credit scoring
# ---------------------------------------------------------------------------

CREDIT_FEATURES = {
    "income": {
        "range": (0, 300),
        "terms": {
            "low": [0, 15, 50],
            "medium": [30, 80, 130],
            "high": [100, 200, 300],
        },
    },
    "debt_ratio": {
        "range": (0, 1.0),
        "terms": {
            "low": [0.0, 0.10, 0.25],
            "medium": [0.15, 0.40, 0.60],
            "high": [0.45, 0.75, 1.0],
        },
    },
    "employment_years": {
        "range": (0, 30),
        "terms": {
            "low": [0, 1, 3],
            "medium": [2, 6, 10],
            "high": [7, 15, 30],
        },
    },
    "credit_history_months": {
        "range": (0, 240),
        "terms": {
            "low": [0, 12, 36],
            "medium": [24, 72, 120],
            "high": [96, 168, 240],
        },
    },
    "age": {
        "range": (18, 70),
        "terms": {
            "low": [18, 23, 30],
            "medium": [26, 37, 50],
            "high": [44, 58, 70],
        },
    },
}

# Output MFs for credit score
CREDIT_OUTPUT = {
    "low": [0, 10, 35],
    "medium": [25, 50, 70],
    "high": [60, 85, 100],
}

# ---------------------------------------------------------------------------
# 27 reduced rules for credit scoring
# ---------------------------------------------------------------------------
# Rules focus on 3 primary features (income, debt_ratio, credit_history)
# with default medium for employment_years and age.
# Format: (income_term, debt_term, credit_term, employment_term, age_term, output_term, weight)

_PRIMARY_COMBOS = [
    ("low", "low", "low"), ("low", "low", "medium"), ("low", "low", "high"),
    ("low", "medium", "low"), ("low", "medium", "medium"), ("low", "medium", "high"),
    ("low", "high", "low"), ("low", "high", "medium"), ("low", "high", "high"),
    ("medium", "low", "low"), ("medium", "low", "medium"), ("medium", "low", "high"),
    ("medium", "medium", "low"), ("medium", "medium", "medium"), ("medium", "medium", "high"),
    ("medium", "high", "low"), ("medium", "high", "medium"), ("medium", "high", "high"),
    ("high", "low", "low"), ("high", "low", "medium"), ("high", "low", "high"),
    ("high", "medium", "low"), ("high", "medium", "medium"), ("high", "medium", "high"),
    ("high", "high", "low"), ("high", "high", "medium"), ("high", "high", "high"),
]


def _build_credit_rules() -> list[dict]:
    """Build 27 core rules + 9 bonus rules for employment/age sensitivity (36 total)."""
    rules = []
    # Heuristic: map (income, debt, credit) -> output
    def _output_term(inc_t: str, debt_t: str, cr_t: str) -> str:
        score = 0
        if inc_t == "high":
            score += 2
        elif inc_t == "medium":
            score += 1
        if debt_t == "low":
            score += 2
        elif debt_t == "medium":
            score += 1
        if cr_t == "high":
            score += 2
        elif cr_t == "medium":
            score += 1
        if score >= 5:
            return "high"
        elif score >= 3:
            return "medium"
        return "low"

    for inc_t, debt_t, cr_t in _PRIMARY_COMBOS:
        out_t = _output_term(inc_t, debt_t, cr_t)
        rules.append({
            "antecedents": {
                "income": inc_t, "debt_ratio": debt_t,
                "employment_years": "medium", "credit_history_months": cr_t,
                "age": "medium",
            },
            "consequent": out_t,
            "weight": 1.0,
        })

    # Bonus rules: override when employment or age are extreme
    bonus = [
        ("medium", "medium", "medium", "low", "medium", "low", 0.7),
        ("medium", "medium", "medium", "high", "medium", "medium", 0.8),
        ("low", "low", "medium", "medium", "low", "low", 0.7),
        ("high", "high", "medium", "medium", "high", "medium", 0.6),
        ("medium", "low", "medium", "high", "medium", "high", 0.9),
        ("high", "medium", "high", "medium", "medium", "high", 1.0),
        ("low", "high", "low", "low", "low", "low", 0.9),
        ("high", "low", "high", "high", "high", "high", 1.0),
        ("medium", "medium", "low", "medium", "medium", "low", 0.8),
    ]
    for inc_t, debt_t, cr_t, emp_t, age_t, out_t, w in bonus:
        rules.append({
            "antecedents": {
                "income": inc_t, "debt_ratio": debt_t,
                "employment_years": emp_t, "credit_history_months": cr_t,
                "age": age_t,
            },
            "consequent": out_t,
            "weight": w,
        })
    return rules


CREDIT_RULES = _build_credit_rules()


# ===================================================================
# 1. Fuzzy Credit Scoring
# ===================================================================

def fuzzy_credit_scoring(applicant: dict) -> dict:
    """Fuzzy inference system for credit scoring.

    Args:
        applicant: dict with keys income, debt_ratio, employment_years,
                    credit_history_months, age.

    Returns:
        Fuzzy credit score (0-100), risk category, membership degrees,
        activated rules count, and feature sensitivity analysis.
    """
    features = {"income", "debt_ratio", "employment_years",
                "credit_history_months", "age"}
    if not features.issubset(applicant):
        missing = features - set(applicant)
        return {"error": f"Missing applicant features: {missing}"}

    # --- fuzzify each input ---
    memberships: dict[str, dict[str, float]] = {}
    for fname, finfo in CREDIT_FEATURES.items():
        x = float(applicant[fname])
        lo, hi = finfo["range"]
        x = np.clip(x, lo, hi)
        memberships[fname] = {}
        for term, params in finfo["terms"].items():
            memberships[fname][term] = round(_trimf(x, params), 6)

    # --- Mamdani inference ---
    x_out = np.linspace(0, 100, 500)
    aggregated = np.zeros_like(x_out)
    activated_count = 0
    activated_details: list[dict] = []

    for rule in CREDIT_RULES:
        ant = rule["antecedents"]
        # T-norm: minimum
        firing = 1.0
        for fname, term in ant.items():
            firing = min(firing, memberships[fname][term])
        firing *= rule["weight"]
        if firing < 1e-6:
            continue
        activated_count += 1
        activated_details.append({
            "antecedents": ant,
            "consequent": rule["consequent"],
            "firing_strength": round(firing, 6),
        })
        # Clip output MF
        out_params = CREDIT_OUTPUT[rule["consequent"]]
        out_mf = _trimf_vec(x_out, out_params)
        aggregated = np.maximum(aggregated, np.minimum(firing, out_mf))

    # --- centroid defuzzification ---
    raw_score = _centroid_defuzz(x_out, aggregated)
    score = float(np.clip(raw_score, 0, 100))

    # Risk category
    if score >= 70:
        category = "low_risk"
    elif score >= 45:
        category = "medium_risk"
    else:
        category = "high_risk"

    # --- Feature sensitivity analysis ---
    sensitivity: dict[str, dict] = {}
    base_score = score
    for fname, finfo in CREDIT_FEATURES.items():
        original_val = float(applicant[fname])
        lo, hi = finfo["range"]
        # Perturb +10%
        perturbed_hi = min(original_val * 1.10 + 1e-6, hi)
        # Perturb -10%
        perturbed_lo = max(original_val * 0.90 - 1e-6, lo)
        scores_up = []
        scores_dn = []
        for pv in [perturbed_hi, perturbed_lo]:
            temp_app = dict(applicant)
            temp_app[fname] = pv
            temp_membs = {}
            for fn2, fi2 in CREDIT_FEATURES.items():
                xv = float(temp_app[fn2])
                xv = np.clip(xv, *fi2["range"])
                temp_membs[fn2] = {
                    t: _trimf(xv, p) for t, p in fi2["terms"].items()
                }
            agg_tmp = np.zeros_like(x_out)
            for rule in CREDIT_RULES:
                ant = rule["antecedents"]
                firing = 1.0
                for fn3, term in ant.items():
                    firing = min(firing, temp_membs[fn3][term])
                firing *= rule["weight"]
                if firing < 1e-6:
                    continue
                out_params = CREDIT_OUTPUT[rule["consequent"]]
                out_mf = _trimf_vec(x_out, out_params)
                agg_tmp = np.maximum(agg_tmp, np.minimum(firing, out_mf))
            s = float(np.clip(_centroid_defuzz(x_out, agg_tmp), 0, 100))
            if pv > original_val:
                scores_up.append(s)
            else:
                scores_dn.append(s)
        sens_up = (scores_up[0] - base_score) if scores_up else 0.0
        sens_dn = (scores_dn[0] - base_score) if scores_dn else 0.0
        sensitivity[fname] = {
            "score_impact_up": round(sens_up, 4),
            "score_impact_down": round(sens_dn, 4),
            "sensitivity_magnitude": round(max(abs(sens_up), abs(sens_dn)), 4),
        }

    # Sort features by sensitivity
    sorted_sens = sorted(sensitivity.items(),
                         key=lambda kv: kv[1]["sensitivity_magnitude"], reverse=True)

    return {
        "fuzzy_score": round(score, 4),
        "risk_category": category,
        "membership_degrees": memberships,
        "activated_rules_count": activated_count,
        "total_rules": len(CREDIT_RULES),
        "activated_rules_sample": activated_details[:5],
        "feature_sensitivity": {k: v for k, v in sorted_sens},
        "most_sensitive_feature": sorted_sens[0][0] if sorted_sens else None,
    }


# ===================================================================
# 2. ANFIS Bankruptcy Prediction
# ===================================================================

ANFIS_FEATURES = ["current_ratio", "debt_to_equity", "roe",
                   "net_margin", "interest_coverage", "altman_z"]

ANFIS_RANGES = {
    "current_ratio": (0.0, 5.0),
    "debt_to_equity": (0.0, 5.0),
    "roe": (-0.5, 0.5),
    "net_margin": (-0.3, 0.3),
    "interest_coverage": (0.0, 15.0),
    "altman_z": (-5.0, 10.0),
}


def _init_anfis_mf_params() -> dict[str, dict[str, list[float]]]:
    """Initialize triangular MF parameters via grid partitioning (3 terms per feature)."""
    params = {}
    for fname, (lo, hi) in ANFIS_RANGES.items():
        step = (hi - lo) / 3.0
        params[fname] = {
            "low": [lo, lo + step * 0.5, lo + step],
            "medium": [lo + step * 0.5, lo + step * 1.5, lo + step * 2.5],
            "high": [lo + step * 2.0, lo + step * 2.5, hi],
        }
    return params


def _anfis_forward(X: np.ndarray, mf_params: dict, n_rules: int,
                   consequent_params: np.ndarray) -> tuple:
    """Forward pass of ANFIS.

    Returns:
        (output, firing_strengths, normalized_firing, layer1_outs)
    """
    n_samples = X.shape[0]
    n_features = X.shape[1]
    feature_names = list(ANFIS_RANGES.keys())
    terms = ["low", "medium", "high"]

    # Layer 1: fuzzify
    layer1 = np.zeros((n_samples, n_features, 3))
    for i, fname in enumerate(feature_names):
        for j, term in enumerate(terms):
            a, b, c = mf_params[fname][term]
            layer1[:, i, j] = _trimf_vec(X[:, i], [a, b, c])

    # Layer 2: rule firing strengths (T-norm = product)
    # Generate rule combinations (reduce to 27 rules from 3^6=729 by
    # pairing features and using 3^3 combinations)
    # We pick 3 key feature groups:
    # Group A: current_ratio, debt_to_equity, altman_z
    # Group B: roe, net_margin, interest_coverage
    # Use all 27 combos of Group A terms, with Group B using the max-firing term
    group_a_idx = [0, 1, 5]  # current_ratio, debt_to_equity, altman_z
    group_b_idx = [2, 3, 4]  # roe, net_margin, interest_coverage

    firing = np.zeros((n_samples, n_rules))
    rule_map = []  # (ga_terms, gb_terms)
    rule_idx = 0
    for ta in range(3):
        for tb in range(3):
            for tc in range(3):
                if rule_idx >= n_rules:
                    break
                # Group A terms fixed
                ga_terms = [ta, tb, tc]
                # Group B: pick max-firing term per sample
                rule_map.append((ga_terms, None))
                f_a = (layer1[:, group_a_idx[0], ta]
                       * layer1[:, group_a_idx[1], tb]
                       * layer1[:, group_a_idx[2], tc])
                # For Group B, take max membership across terms
                f_b = np.ones(n_samples)
                for gi in group_b_idx:
                    f_b = f_b * np.max(layer1[:, gi, :], axis=1)
                firing[:, rule_idx] = f_a * f_b
                rule_idx += 1

    # Layer 3: normalize
    firing_sum = firing.sum(axis=1, keepdims=True)
    firing_sum[firing_sum < 1e-12] = 1e-12
    norm_firing = firing / firing_sum

    # Layer 4+5: weighted consequent
    # Each rule has a linear consequent: p0 + p1*x1 + ... + p6*x6
    # Augment X with bias
    X_aug = np.hstack([np.ones((n_samples, 1)), X])
    # consequent_params shape: (n_rules, n_features+1)
    rule_outputs = X_aug @ consequent_params.T  # (n_samples, n_rules)
    output = np.sum(norm_firing * rule_outputs, axis=1)

    return output, firing, norm_firing, layer1, rule_map


def _logistic_regression(X_train: np.ndarray, y_train: np.ndarray,
                         X_test: np.ndarray, y_test: np.ndarray,
                         lr: float = 0.1, epochs: int = 200) -> dict:
    """Simple logistic regression for comparison."""
    n_samples, n_features = X_train.shape
    w = np.zeros(n_features + 1)
    X_aug = np.hstack([np.ones((n_samples, 1)), X_train])
    X_test_aug = np.hstack([np.ones((X_test.shape[0], 1)), X_test])

    for _ in range(epochs):
        z = X_aug @ w
        pred = _sigmoid(z)
        error = pred - y_train
        grad = (X_aug.T @ error) / n_samples
        w -= lr * grad

    # Predictions
    train_prob = _sigmoid(X_aug @ w)
    train_pred = (train_prob >= 0.5).astype(int)
    test_prob = _sigmoid(X_test_aug @ w)
    test_pred = (test_prob >= 0.5).astype(int)

    train_acc = float(np.mean(train_pred == y_train))
    test_acc = float(np.mean(test_pred == y_test))

    return {
        "train_accuracy": round(train_acc, 4),
        "test_accuracy": round(test_acc, 4),
        "train_probabilities": [round(float(p), 4) for p in train_prob],
        "test_probabilities": [round(float(p), 4) for p in test_prob],
        "weights": [round(float(wi), 6) for wi in w],
    }


def _compute_metrics(y_true: np.ndarray, y_pred: np.ndarray,
                     y_prob: np.ndarray) -> dict:
    """Compute classification metrics and ROC curve points."""
    tp = int(np.sum((y_pred == 1) & (y_true == 1)))
    tn = int(np.sum((y_pred == 0) & (y_true == 0)))
    fp = int(np.sum((y_pred == 1) & (y_true == 0)))
    fn = int(np.sum((y_pred == 0) & (y_true == 1)))

    precision_1 = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall_1 = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1_1 = (2 * precision_1 * recall_1 / (precision_1 + recall_1)
             if (precision_1 + recall_1) > 0 else 0.0)

    precision_0 = tn / (tn + fn) if (tn + fn) > 0 else 0.0
    recall_0 = tn / (tn + fp) if (tn + fp) > 0 else 0.0
    f1_0 = (2 * precision_0 * recall_0 / (precision_0 + recall_0)
             if (precision_0 + recall_0) > 0 else 0.0)

    accuracy = (tp + tn) / max(len(y_true), 1)

    # ROC curve points
    thresholds = np.linspace(0, 1, 50)
    roc_points = []
    for thresh in thresholds:
        pred_t = (y_prob >= thresh).astype(int)
        tpr = np.sum((pred_t == 1) & (y_true == 1)) / max(np.sum(y_true == 1), 1)
        fpr = np.sum((pred_t == 1) & (y_true == 0)) / max(np.sum(y_true == 0), 1)
        roc_points.append({
            "threshold": round(float(thresh), 4),
            "tpr": round(float(tpr), 4),
            "fpr": round(float(fpr), 4),
        })

    # AUC via trapezoidal (sort by FPR first)
    roc_sorted = sorted(roc_points, key=lambda p: p["fpr"])
    auc = 0.0
    for i in range(1, len(roc_sorted)):
        dx = roc_sorted[i]["fpr"] - roc_sorted[i - 1]["fpr"]
        dy = (roc_sorted[i]["tpr"] + roc_sorted[i - 1]["tpr"]) / 2
        auc += dx * dy
    auc = max(0.0, min(1.0, auc))  # clamp to valid range

    return {
        "accuracy": round(accuracy, 4),
        "confusion_matrix": {"tp": tp, "tn": tn, "fp": fp, "fn": fn},
        "per_class": {
            "healthy": {
                "precision": round(precision_0, 4),
                "recall": round(recall_0, 4),
                "f1": round(f1_0, 4),
                "support": int(tn + fp),
            },
            "distressed": {
                "precision": round(precision_1, 4),
                "recall": round(recall_1, 4),
                "f1": round(f1_1, 4),
                "support": int(tp + fn),
            },
        },
        "roc_curve": roc_points,
        "auc": round(float(auc), 4),
    }


def anfis_bankruptcy_prediction(
    training_data: list[dict],
    test_data: list[dict],
    epochs: int = 50,
    learning_rate: float = 0.01,
) -> dict:
    """ANFIS-inspired hybrid model for bankruptcy prediction.

    Args:
        training_data: list of dicts with financial ratios + 'label' (0=healthy, 1=distressed).
        test_data: same format.
        epochs: number of training epochs.
        learning_rate: gradient descent step size.

    Returns:
        Training/test metrics, confusion matrix, ROC curve, learned MF params,
        logistic regression comparison.
    """
    if not training_data or not test_data:
        return {"error": "training_data and test_data must be non-empty"}

    required = set(ANFIS_FEATURES + ["label"])
    if not required.issubset(training_data[0]):
        missing = required - set(training_data[0])
        return {"error": f"Missing fields in training_data: {missing}"}

    # Prepare data
    def _to_matrix(data: list[dict]) -> tuple:
        X = np.array([[float(d[f]) for f in ANFIS_FEATURES] for d in data])
        y = np.array([int(d["label"]) for d in data], dtype=float)
        # Normalize features to [0, 1] based on ANFIS_RANGES
        X_norm = np.zeros_like(X)
        for i, fname in enumerate(ANFIS_FEATURES):
            lo, hi = ANFIS_RANGES[fname]
            X_norm[:, i] = np.clip((X[:, i] - lo) / max(hi - lo, 1e-12), 0, 1)
        return X_norm, y, X

    X_train, y_train, X_train_raw = _to_matrix(training_data)
    X_test, y_test, X_test_raw = _to_matrix(test_data)

    n_train = X_train.shape[0]
    n_rules = 27
    n_features = len(ANFIS_FEATURES)

    # Initialize MF parameters
    mf_params = _init_anfis_mf_params()
    # Normalize MF params to [0, 1] space
    mf_params_norm = {}
    for fname, (lo, hi) in ANFIS_RANGES.items():
        span = hi - lo
        mf_params_norm[fname] = {}
        for term, (a, b, c) in mf_params[fname].items():
            mf_params_norm[fname][term] = [
                (a - lo) / span, (b - lo) / span, (c - lo) / span
            ]

    # Initialize consequent parameters randomly
    np.random.seed(42)
    consequent_params = np.random.randn(n_rules, n_features + 1) * 0.1

    # Training loop
    train_losses = []
    for epoch in range(epochs):
        # Forward pass
        output, firing, norm_firing, layer1, rule_map = _anfis_forward(
            X_train, mf_params_norm, n_rules, consequent_params
        )

        # Loss (MSE)
        error = output - y_train
        loss = float(np.mean(error ** 2))
        train_losses.append(round(loss, 6))

        # --- Backward pass: gradient descent on consequent params ---
        # dL/dp_k = (1/N) * sum_i (f_i_k * error_i * x_i)
        X_aug = np.hstack([np.ones((n_train, 1)), X_train])
        for k in range(n_rules):
            weighted_error = norm_firing[:, k] * error
            grad_k = (weighted_error @ X_aug) / n_train
            consequent_params[k] -= learning_rate * grad_k

        # --- Backward pass: gradient descent on MF params ---
        # Simplified: adjust MF params to reduce error
        mf_lr = learning_rate * 0.1
        feature_names = list(ANFIS_RANGES.keys())
        group_a_idx = [0, 1, 5]
        terms_list = ["low", "medium", "high"]

        for i in range(n_train):
            for ri in range(n_rules):
                ga_terms, _ = rule_map[ri]
                d_output = error[i]
                # derivative of output w.r.t. firing of rule ri
                # output = sum_k norm_firing_k * rule_output_k
                # For simplicity, update group_a MF params
                for g_idx, fi in enumerate(group_a_idx):
                    term_idx = ga_terms[g_idx]
                    fname = feature_names[fi]
                    x_val = X_train[i, fi]
                    params = mf_params_norm[fname][terms_list[term_idx]]
                    grads = _trimf_grad(x_val, params)
                    # Chain rule: dL/d(param) = dL/d_output * d_output/d_firing * d_firing/d_mu * d_mu/d_param
                    scale = mf_lr * d_output / n_train
                    # Approximate: adjust params slightly
                    mf_params_norm[fname][terms_list[term_idx]][0] -= scale * grads["a"] * 0.01
                    mf_params_norm[fname][terms_list[term_idx]][1] -= scale * grads["b"] * 0.01
                    mf_params_norm[fname][terms_list[term_idx]][2] -= scale * grads["c"] * 0.01
                    # Clip to valid range
                    for p_idx in range(3):
                        mf_params_norm[fname][terms_list[term_idx]][p_idx] = float(
                            np.clip(mf_params_norm[fname][terms_list[term_idx]][p_idx], -0.1, 1.1)
                        )

    # Final predictions
    train_output, _, _, _, _ = _anfis_forward(
        X_train, mf_params_norm, n_rules, consequent_params
    )
    test_output, _, _, _, _ = _anfis_forward(
        X_test, mf_params_norm, n_rules, consequent_params
    )

    train_prob = _sigmoid(train_output)
    test_prob = _sigmoid(test_output)
    train_pred = (train_prob >= 0.5).astype(int)
    test_pred = (test_prob >= 0.5).astype(int)

    train_metrics = _compute_metrics(y_train, train_pred, train_prob)
    test_metrics = _compute_metrics(y_test, test_pred, test_prob)

    # Logistic regression comparison
    lr_result = _logistic_regression(X_train, y_train, X_test, y_test)

    # Convert learned MF params back to original scale for reporting
    learned_mf = {}
    for fname, (lo, hi) in ANFIS_RANGES.items():
        span = hi - lo
        learned_mf[fname] = {}
        for term, params in mf_params_norm[fname].items():
            learned_mf[fname][term] = [
                round(p * span + lo, 4) for p in params
            ]

    return {
        "model": "ANFIS-Hybrid",
        "training_samples": n_train,
        "test_samples": X_test.shape[0],
        "epochs": epochs,
        "final_training_loss": train_losses[-1] if train_losses else None,
        "training_loss_curve": train_losses[::max(1, epochs // 20)],
        "training_metrics": train_metrics,
        "test_metrics": test_metrics,
        "logistic_regression_comparison": lr_result,
        "anfis_vs_lr_test_accuracy_diff": round(
            test_metrics["accuracy"] - lr_result["test_accuracy"], 4
        ),
        "learned_membership_functions": learned_mf,
        "n_rules": n_rules,
    }


# ===================================================================
# 3. Fuzzy Rule Extraction (with FCM clustering)
# ===================================================================

def _fcm_clustering(data: np.ndarray, n_clusters: int = 3,
                    m: float = 2.0, max_iter: int = 200,
                    tol: float = 1e-6) -> tuple:
    """Fuzzy C-Means clustering implemented with numpy.

    Returns:
        (centers, membership_matrix, iterations)
    """
    n_samples, n_features = data.shape
    if n_samples < n_clusters:
        n_clusters = n_samples

    # Initialize membership matrix randomly
    np.random.seed(0)
    U = np.random.dirichlet(np.ones(n_clusters), size=n_samples)

    centers = np.zeros((n_clusters, n_features))
    prev_centers = np.copy(centers)
    n_iter = 0

    for iteration in range(max_iter):
        # Update centers
        um = U ** m
        for j in range(n_clusters):
            denom = um[:, j].sum()
            if denom > 1e-12:
                centers[j] = (um[:, j, np.newaxis] * data).sum(axis=0) / denom
            else:
                centers[j] = data[np.random.randint(n_samples)]

        # Check convergence
        center_shift = float(np.max(np.abs(centers - prev_centers)))
        prev_centers = np.copy(centers)
        n_iter = iteration + 1
        if center_shift < tol:
            break

        # Update membership
        dist = np.zeros((n_samples, n_clusters))
        for j in range(n_clusters):
            diff = data - centers[j]
            dist[:, j] = np.sqrt((diff ** 2).sum(axis=1))

        # Avoid division by zero
        dist = np.maximum(dist, 1e-12)
        exp = 2.0 / (m - 1.0)
        for j in range(n_clusters):
            denom = sum((dist[:, j] / dist[:, k]) ** exp for k in range(n_clusters))
            U[:, j] = 1.0 / denom

    return centers, U, n_iter


def fuzzy_rule_extraction(
    data_matrix: list[list[float]],
    feature_names: list[str],
    n_clusters: int = 3,
    output_column: int = -1,
) -> dict:
    """Extract interpretable fuzzy if-then rules from data.

    Args:
        data_matrix: 2D list (samples x features).  Last column is the output.
        feature_names: names for each column (including output).
        n_clusters: number of fuzzy terms per feature.
        output_column: index of the output column (default -1 = last).

    Returns:
        Extracted rules, quality metrics, coverage statistics.
    """
    data = np.array(data_matrix, dtype=float)
    if data.ndim != 2 or data.shape[0] < 3:
        return {"error": "data_matrix must be 2D with at least 3 samples"}

    if len(feature_names) != data.shape[1]:
        return {"error": f"feature_names length ({len(feature_names)}) must match data columns ({data.shape[1]})"}

    n_samples, n_cols = data.shape
    n_features = n_cols - 1
    out_idx = output_column if output_column >= 0 else n_cols + output_column

    # Separate input and output
    X = np.delete(data, out_idx, axis=1)
    y = data[:, out_idx]

    # Cluster each feature to derive MFs
    term_names = ["low", "medium", "high"] if n_clusters == 3 else [
        f"term_{i}" for i in range(n_clusters)
    ]
    if n_clusters > len(term_names):
        term_names = [f"term_{i}" for i in range(n_clusters)]

    feature_mfs = {}  # {feature_idx: {term: (a, b, c)}}
    for fi in range(n_features):
        col = X[:, fi:fi+1]
        centers, U, iters = _fcm_clustering(col, n_clusters)
        # Sort centers
        order = np.argsort(centers.flatten())
        sorted_centers = centers[order].flatten()

        # Build triangular MFs from cluster centers
        mfs = {}
        for ti in range(n_clusters):
            if ti == 0:
                a = float(np.min(col)) - 0.1 * (sorted_centers[-1] - sorted_centers[0] + 1e-6)
                b = sorted_centers[0]
                c = (sorted_centers[0] + sorted_centers[1]) / 2 if n_clusters > 1 else sorted_centers[0] + 0.5
            elif ti == n_clusters - 1:
                prev_c = (sorted_centers[ti - 1] + sorted_centers[ti]) / 2 if ti > 0 else sorted_centers[ti] - 0.5
                a = prev_c
                b = sorted_centers[ti]
                c = float(np.max(col)) + 0.1 * (sorted_centers[-1] - sorted_centers[0] + 1e-6)
            else:
                a = (sorted_centers[ti - 1] + sorted_centers[ti]) / 2
                b = sorted_centers[ti]
                c = (sorted_centers[ti] + sorted_centers[ti + 1]) / 2
            mfs[term_names[ti]] = [round(a, 4), round(b, 4), round(c, 4)]
        feature_mfs[fi] = mfs

    # Cluster output
    y_col = y.reshape(-1, 1)
    out_centers, out_U, _ = _fcm_clustering(y_col, n_clusters)
    out_order = np.argsort(out_centers.flatten())
    out_sorted = out_centers[out_order].flatten()
    output_terms = {}
    for ti in range(n_clusters):
        if ti == 0:
            a = float(np.min(y_col)) - 0.1 * (out_sorted[-1] - out_sorted[0] + 1e-6)
            b = out_sorted[0]
            c = (out_sorted[0] + out_sorted[1]) / 2 if n_clusters > 1 else out_sorted[0] + 0.5
        elif ti == n_clusters - 1:
            a = (out_sorted[ti - 1] + out_sorted[ti]) / 2 if ti > 0 else out_sorted[ti] - 0.5
            b = out_sorted[ti]
            c = float(np.max(y_col)) + 0.1 * (out_sorted[-1] - out_sorted[0] + 1e-6)
        else:
            a = (out_sorted[ti - 1] + out_sorted[ti]) / 2
            b = out_sorted[ti]
            c = (out_sorted[ti] + out_sorted[ti + 1]) / 2
        output_terms[term_names[ti]] = [round(a, 4), round(b, 4), round(c, 4)]

    # Compute membership for all samples
    input_memberships = np.zeros((n_samples, n_features, n_clusters))
    for fi in range(n_features):
        for ti in range(n_clusters):
            params = feature_mfs[fi][term_names[ti]]
            input_memberships[:, fi, ti] = _trimf_vec(X[:, fi], params)

    output_memberships = np.zeros((n_samples, n_clusters))
    for ti in range(n_clusters):
        params = output_terms[term_names[ti]]
        output_memberships[:, ti] = _trimf_vec(y, params)

    # Generate rules: find strongest input-output associations
    # For each sample, find the dominant term per feature and output
    rules_strength: dict[tuple, list[float]] = {}
    rule_samples: dict[tuple, set] = {}

    for si in range(n_samples):
        antecedent = tuple(int(np.argmax(input_memberships[si, fi, :])) for fi in range(n_features))
        consequent = int(np.argmax(output_memberships[si, :]))
        key = (antecedent, consequent)
        # Strength = product of memberships
        strength = 1.0
        for fi in range(n_features):
            strength *= float(input_memberships[si, fi, antecedent[fi]])
        strength *= float(output_memberships[si, consequent])

        if key not in rules_strength:
            rules_strength[key] = []
            rule_samples[key] = set()
        rules_strength[key].append(strength)
        rule_samples[key].add(si)

    # Build rules list
    extracted_rules = []
    for (ant, con), strengths in sorted(rules_strength.items(),
                                          key=lambda kv: -np.mean(kv[1])):
        if len(strengths) < 1:
            continue
        ant_str = " AND ".join(
            f"{feature_names[fi]} is {term_names[ant[fi]]}"
            for fi in range(n_features)
        )
        rule = {
            "rule": f"IF {ant_str} THEN {feature_names[out_idx]} is {term_names[con]}",
            "antecedent_terms": [term_names[ant[fi]] for fi in range(n_features)],
            "consequent_term": term_names[con],
            "strength": round(float(np.mean(strengths)), 4),
            "max_strength": round(float(np.max(strengths)), 4),
            "support_count": len(strengths),
            "support_ratio": round(len(strengths) / n_samples, 4),
            "confidence": round(float(np.mean(strengths)), 4),
        }
        extracted_rules.append(rule)

    # Limit to top 50 rules
    extracted_rules = extracted_rules[:50]

    # Coverage statistics
    covered_samples = set()
    for key, samples in rule_samples.items():
        covered_samples |= samples

    coverage = len(covered_samples) / n_samples if n_samples > 0 else 0.0

    # Quality metrics
    avg_strength = float(np.mean([r["strength"] for r in extracted_rules])) if extracted_rules else 0.0
    avg_confidence = float(np.mean([r["confidence"] for r in extracted_rules])) if extracted_rules else 0.0

    # Feature importance: how often each feature appears in top rules
    feature_importance = {}
    for fi in range(n_features):
        term_counts = {t: 0 for t in term_names[:n_clusters]}
        for rule in extracted_rules[:20]:
            term_counts[rule["antecedent_terms"][fi]] += 1
        total = sum(term_counts.values())
        feature_importance[feature_names[fi]] = {
            term: round(cnt / max(total, 1), 4) for term, cnt in term_counts.items()
        }

    return {
        "method": "Fuzzy C-Means Rule Extraction",
        "samples": n_samples,
        "features": n_features,
        "n_clusters_per_feature": n_clusters,
        "fcm_iterations": iters,
        "extracted_rules": extracted_rules,
        "total_rules_found": len(rules_strength),
        "top_rules_returned": len(extracted_rules),
        "rule_quality": {
            "average_strength": round(avg_strength, 4),
            "average_confidence": round(avg_confidence, 4),
            "rules_with_support_ge_3": sum(1 for r in extracted_rules if r["support_count"] >= 3),
            "rules_with_confidence_ge_0_5": sum(1 for r in extracted_rules if r["confidence"] >= 0.5),
        },
        "coverage": {
            "samples_covered": len(covered_samples),
            "total_samples": n_samples,
            "coverage_ratio": round(coverage, 4),
        },
        "feature_importance": feature_importance,
        "learned_membership_functions": {
            feature_names[fi]: feature_mfs[fi] for fi in range(n_features)
        },
        "output_membership_functions": output_terms,
    }


# ===================================================================
# 4. Demo with TSE-relevant data
# ===================================================================

def fuzzy_neural_demo() -> dict:
    """Demo with TSE-relevant data.

    20 loan applicants (Iranian economic context) for credit scoring,
    30 companies (15 healthy, 15 distressed) for bankruptcy prediction,
    and rule extraction from the company data.
    """
    # --- 20 Loan Applicants (Iranian context) ---
    # Income in million IRR/month, debt_ratio, employment_years,
    # credit_history_months, age
    applicants = [
        {"income": 250, "debt_ratio": 0.15, "employment_years": 12,
         "credit_history_months": 180, "age": 42, "name": "Applicant 1"},
        {"income": 45, "debt_ratio": 0.65, "employment_years": 2,
         "credit_history_months": 18, "age": 28, "name": "Applicant 2"},
        {"income": 120, "debt_ratio": 0.30, "employment_years": 7,
         "credit_history_months": 96, "age": 35, "name": "Applicant 3"},
        {"income": 15, "debt_ratio": 0.80, "employment_years": 1,
         "credit_history_months": 6, "age": 24, "name": "Applicant 4"},
        {"income": 180, "debt_ratio": 0.20, "employment_years": 15,
         "credit_history_months": 200, "age": 48, "name": "Applicant 5"},
        {"income": 60, "debt_ratio": 0.50, "employment_years": 4,
         "credit_history_months": 48, "age": 32, "name": "Applicant 6"},
        {"income": 300, "debt_ratio": 0.10, "employment_years": 20,
         "credit_history_months": 240, "age": 55, "name": "Applicant 7"},
        {"income": 30, "debt_ratio": 0.70, "employment_years": 1,
         "credit_history_months": 12, "age": 25, "name": "Applicant 8"},
        {"income": 90, "debt_ratio": 0.35, "employment_years": 6,
         "credit_history_months": 72, "age": 38, "name": "Applicant 9"},
        {"income": 200, "debt_ratio": 0.18, "employment_years": 10,
         "credit_history_months": 150, "age": 45, "name": "Applicant 10"},
        {"income": 50, "debt_ratio": 0.55, "employment_years": 3,
         "credit_history_months": 30, "age": 29, "name": "Applicant 11"},
        {"income": 150, "debt_ratio": 0.25, "employment_years": 8,
         "credit_history_months": 120, "age": 40, "name": "Applicant 12"},
        {"income": 25, "debt_ratio": 0.75, "employment_years": 1,
         "credit_history_months": 8, "age": 23, "name": "Applicant 13"},
        {"income": 110, "debt_ratio": 0.40, "employment_years": 5,
         "credit_history_months": 60, "age": 34, "name": "Applicant 14"},
        {"income": 280, "debt_ratio": 0.12, "employment_years": 18,
         "credit_history_months": 216, "age": 52, "name": "Applicant 15"},
        {"income": 35, "debt_ratio": 0.60, "employment_years": 2,
         "credit_history_months": 24, "age": 27, "name": "Applicant 16"},
        {"income": 160, "debt_ratio": 0.22, "employment_years": 9,
         "credit_history_months": 108, "age": 41, "name": "Applicant 17"},
        {"income": 75, "debt_ratio": 0.45, "employment_years": 4,
         "credit_history_months": 42, "age": 31, "name": "Applicant 18"},
        {"income": 220, "debt_ratio": 0.14, "employment_years": 14,
         "credit_history_months": 168, "age": 47, "name": "Applicant 19"},
        {"income": 40, "debt_ratio": 0.58, "employment_years": 2,
         "credit_history_months": 15, "age": 26, "name": "Applicant 20"},
    ]

    # --- Credit Scoring Results ---
    credit_results = []
    for app in applicants:
        result = fuzzy_credit_scoring(app)
        result["name"] = app["name"]
        credit_results.append(result)

    # Summary stats
    scores = [r["fuzzy_score"] for r in credit_results if "fuzzy_score" in r]
    risk_counts = {"low_risk": 0, "medium_risk": 0, "high_risk": 0}
    for r in credit_results:
        cat = r.get("risk_category", "")
        if cat in risk_counts:
            risk_counts[cat] += 1

    # --- 30 Companies: 15 Healthy, 15 Distressed (Iranian TSE context) ---
    companies = [
        # 15 Healthy companies
        {"current_ratio": 2.1, "debt_to_equity": 0.5, "roe": 0.18,
         "net_margin": 0.12, "interest_coverage": 6.5, "altman_z": 3.2, "label": 0,
         "name": "Mobarakeh Steel"},
        {"current_ratio": 1.8, "debt_to_equity": 0.7, "roe": 0.15,
         "net_margin": 0.09, "interest_coverage": 5.2, "altman_z": 2.8, "label": 0,
         "name": "Persian Gulf Petro"},
        {"current_ratio": 2.5, "debt_to_equity": 0.3, "roe": 0.22,
         "net_margin": 0.15, "interest_coverage": 8.0, "altman_z": 3.8, "label": 0,
         "name": "Telecom Iran"},
        {"current_ratio": 1.9, "debt_to_equity": 0.6, "roe": 0.14,
         "net_margin": 0.08, "interest_coverage": 4.8, "altman_z": 2.6, "label": 0,
         "name": "National Copper"},
        {"current_ratio": 2.3, "debt_to_equity": 0.4, "roe": 0.20,
         "net_margin": 0.13, "interest_coverage": 7.2, "altman_z": 3.5, "label": 0,
         "name": "Iran Khodro"},
        {"current_ratio": 1.7, "debt_to_equity": 0.8, "roe": 0.12,
         "net_margin": 0.07, "interest_coverage": 4.0, "altman_z": 2.3, "label": 0,
         "name": "Saipa"},
        {"current_ratio": 2.8, "debt_to_equity": 0.2, "roe": 0.25,
         "net_margin": 0.18, "interest_coverage": 9.5, "altman_z": 4.2, "label": 0,
         "name": "Mapna Group"},
        {"current_ratio": 2.0, "debt_to_equity": 0.55, "roe": 0.16,
         "net_margin": 0.10, "interest_coverage": 5.8, "altman_z": 3.0, "label": 0,
         "name": "Tamin Oil"},
        {"current_ratio": 1.6, "debt_to_equity": 0.9, "roe": 0.10,
         "net_margin": 0.05, "interest_coverage": 3.5, "altman_z": 2.1, "label": 0,
         "name": "Melli Bank"},
        {"current_ratio": 2.4, "debt_to_equity": 0.35, "roe": 0.21,
         "net_margin": 0.14, "interest_coverage": 7.8, "altman_z": 3.6, "label": 0,
         "name": "Kish Free Zone"},
        {"current_ratio": 1.9, "debt_to_equity": 0.65, "roe": 0.13,
         "net_margin": 0.08, "interest_coverage": 4.5, "altman_z": 2.5, "label": 0,
         "name": "Saderat Bank"},
        {"current_ratio": 2.2, "debt_to_equity": 0.45, "roe": 0.19,
         "net_margin": 0.11, "interest_coverage": 6.8, "altman_z": 3.3, "label": 0,
         "name": "Pasargad Bank"},
        {"current_ratio": 2.6, "debt_to_equity": 0.28, "roe": 0.23,
         "net_margin": 0.16, "interest_coverage": 8.5, "altman_z": 4.0, "label": 0,
         "name": "Irankhodro Shipping"},
        {"current_ratio": 1.8, "debt_to_equity": 0.72, "roe": 0.14,
         "net_margin": 0.09, "interest_coverage": 5.0, "altman_z": 2.7, "label": 0,
         "name": "Tablo Melli"},
        {"current_ratio": 2.1, "debt_to_equity": 0.50, "roe": 0.17,
         "net_margin": 0.11, "interest_coverage": 6.2, "altman_z": 3.1, "label": 0,
         "name": "Ghadir Inv"},
        # 15 Distressed companies
        {"current_ratio": 0.6, "debt_to_equity": 3.5, "roe": -0.15,
         "net_margin": -0.12, "interest_coverage": 0.5, "altman_z": -1.5, "label": 1,
         "name": "Parsian Development"},
        {"current_ratio": 0.8, "debt_to_equity": 2.8, "roe": -0.10,
         "net_margin": -0.08, "interest_coverage": 0.8, "altman_z": -0.8, "label": 1,
         "name": "Mehre Iran"},
        {"current_ratio": 0.5, "debt_to_equity": 4.0, "roe": -0.22,
         "net_margin": -0.18, "interest_coverage": 0.3, "altman_z": -2.2, "label": 1,
         "name": "Kourosh Mall"},
        {"current_ratio": 0.9, "debt_to_equity": 2.2, "roe": -0.05,
         "net_margin": -0.04, "interest_coverage": 1.2, "altman_z": -0.2, "label": 1,
         "name": "Omid Inv"},
        {"current_ratio": 0.7, "debt_to_equity": 3.0, "roe": -0.12,
         "net_margin": -0.10, "interest_coverage": 0.6, "altman_z": -1.2, "label": 1,
         "name": "Bahman Group"},
        {"current_ratio": 0.4, "debt_to_equity": 4.5, "roe": -0.28,
         "net_margin": -0.22, "interest_coverage": 0.2, "altman_z": -2.8, "label": 1,
         "name": "Hafez Tile"},
        {"current_ratio": 0.8, "debt_to_equity": 2.5, "roe": -0.08,
         "net_margin": -0.06, "interest_coverage": 1.0, "altman_z": -0.5, "label": 1,
         "name": "Tadbir Garan"},
        {"current_ratio": 0.6, "debt_to_equity": 3.2, "roe": -0.14,
         "net_margin": -0.11, "interest_coverage": 0.4, "altman_z": -1.8, "label": 1,
         "name": "Goltash"},
        {"current_ratio": 0.5, "debt_to_equity": 3.8, "roe": -0.20,
         "net_margin": -0.15, "interest_coverage": 0.3, "altman_z": -2.0, "label": 1,
         "name": "Rayan Sazeh"},
        {"current_ratio": 1.0, "debt_to_equity": 2.0, "roe": -0.03,
         "net_margin": -0.02, "interest_coverage": 1.5, "altman_z": 0.1, "label": 1,
         "name": "Pishgaman"},
        {"current_ratio": 0.7, "debt_to_equity": 3.3, "roe": -0.13,
         "net_margin": -0.10, "interest_coverage": 0.5, "altman_z": -1.4, "label": 1,
         "name": "Arj Mandegar"},
        {"current_ratio": 0.9, "debt_to_equity": 2.4, "roe": -0.06,
         "net_margin": -0.05, "interest_coverage": 0.9, "altman_z": -0.6, "label": 1,
         "name": "Tehran Cement"},
        {"current_ratio": 0.5, "debt_to_equity": 4.2, "roe": -0.25,
         "net_margin": -0.20, "interest_coverage": 0.2, "altman_z": -2.5, "label": 1,
         "name": "Zamyad"},
        {"current_ratio": 0.8, "debt_to_equity": 2.6, "roe": -0.09,
         "net_margin": -0.07, "interest_coverage": 0.7, "altman_z": -1.0, "label": 1,
         "name": "Shabahang"},
        {"current_ratio": 0.6, "debt_to_equity": 3.6, "roe": -0.18,
         "net_margin": -0.14, "interest_coverage": 0.4, "altman_z": -1.9, "label": 1,
         "name": "Parto Sanat"},
    ]

    # --- Bankruptcy Prediction ---
    np.random.seed(42)
    indices = list(range(30))
    np.random.shuffle(indices)
    train_idx = indices[:20]
    test_idx = indices[20:]
    train_data = [companies[i] for i in train_idx]
    test_data = [companies[i] for i in test_idx]

    bankruptcy_result = anfis_bankruptcy_prediction(
        training_data=train_data, test_data=test_data, epochs=50
    )

    # --- Rule Extraction ---
    feature_names_re = ["current_ratio", "debt_to_equity", "roe",
                        "net_margin", "interest_coverage", "altman_z", "financial_health"]
    data_matrix_re = []
    for c in companies:
        data_matrix_re.append([
            c["current_ratio"], c["debt_to_equity"], c["roe"],
            c["net_margin"], c["interest_coverage"], c["altman_z"],
            float(c["label"]),
        ])

    rule_result = fuzzy_rule_extraction(
        data_matrix=data_matrix_re,
        feature_names=feature_names_re,
        n_clusters=3,
        output_column=6,
    )

    return {
        "demo_title": "ANFIS Fuzzy Neural Engine — TSE Demo",
        "description": (
            "Comprehensive demo with 20 Iranian loan applicants (credit scoring), "
            "30 TSE-listed companies (15 healthy + 15 distressed) for bankruptcy prediction, "
            "and fuzzy rule extraction from financial data."
        ),
        "credit_scoring": {
            "applicants_analyzed": len(applicants),
            "results": credit_results,
            "summary": {
                "mean_score": round(float(np.mean(scores)), 4) if scores else 0.0,
                "min_score": round(float(np.min(scores)), 4) if scores else 0.0,
                "max_score": round(float(np.max(scores)), 4) if scores else 0.0,
                "std_score": round(float(np.std(scores)), 4) if scores else 0.0,
                "risk_distribution": risk_counts,
            },
        },
        "bankruptcy_prediction": bankruptcy_result,
        "rule_extraction": rule_result,
    }
