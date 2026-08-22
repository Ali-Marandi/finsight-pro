""
Financial Distress & Bankruptcy Prediction Service.
Implements multiple well-established prediction models:
- Altman Z-Score (1968, updated 1983 for private/non-manufacturing)
- Springate Model (1978)
- Ohlson O-Score (1980)
- Grover Model (related to Altman but recalibrated)

Each model outputs a score and a classification zone.
"""

import math
from typing import Optional
from dataclasses import dataclass, field


@dataclass
class PredictionResult:
    """Result from a single prediction model."""
    model_name: str
    model_year: str
    score: float
    zone: str  # 'safe', 'grey', 'distress'
    probability: float  # 0-100, estimated probability of distress
    description: str
    interpretation: str
    components: dict = field(default_factory=dict)


def _safe_div(a: float, b: float, default: float = 0.0) -> float:
    """Safe division that returns default if denominator is zero."""
    return a / b if b != 0 else default


def _sigmoid(x: float) -> float:
    """Logistic sigmoid function."""
    if x > 500:
        return 1.0
    if x < -500:
        return 0.0
    return 1.0 / (1.0 + math.exp(-x))


def _score_to_probability(score: float, thresholds: dict) -> float:
    """
    Convert a raw score to a 0-100 probability of financial distress.
    Uses a sigmoid-based mapping centered on the 'grey' threshold.
    """
    grey_mid = (thresholds["safe_below"] + thresholds["distress_above"]) / 2
    spread = abs(thresholds["safe_below"] - thresholds["distress_above"]) / 2
    if spread == 0:
        spread = 1.0
    # Lower score = higher distress probability for Altman/Springate
    # Higher score = higher distress probability for Ohlson
    direction = thresholds.get("direction", "lower")
    if direction == "lower":
        normalized = (grey_mid - score) / spread
    else:
        normalized = (score - grey_mid) / spread
    return round(max(0.0, min(100.0, _sigmoid(normalized) * 100)), 1)


class BankruptcyPredictor:
    """
    Multi-model financial distress predictor.
    
    Usage:
        predictor = BankruptcyPredictor()
        results = predictor.predict_all(
            total_assets=1000000,
            total_liabilities=600000,
            total_equity=400000,
            net_income=80000,
            revenue=500000,
            ebit=120000,
            current_assets=300000,
            current_liabilities=200000,
            retained_earnings=200000,
            market_value_equity=600000,
            interest_expense=20000,
        )
    """
    
    def __init__(self):
        self.results: list[PredictionResult] = []
    
    def altman_z_score_public(
        self,
        working_capital: float,
        total_assets: float,
        retained_earnings: float,
        ebit: float,
        market_value_equity: float,
        total_liabilities: float,
        revenue: float,
    ) -> PredictionResult:
        """
        Altman Z-Score for Public Manufacturing Companies (1968).
        Z = 1.2*X1 + 1.4*X2 + 3.3*X3 + 0.6*X4 + 0.999*X5
        
        Zones:
          Z > 2.99   → Safe Zone
          1.81 < Z < 2.99 → Grey Zone
          Z < 1.81   → Distress Zone
        """
        x1 = _safe_div(working_capital, total_assets)
        x2 = _safe_div(retained_earnings, total_assets)
        x3 = _safe_div(ebit, total_assets)
        x4 = _safe_div(market_value_equity, total_liabilities)
        x5 = _safe_div(revenue, total_assets)
        
        z = 1.2 * x1 + 1.4 * x2 + 3.3 * x3 + 0.6 * x4 + 0.999 * x5
        z = round(z, 4)
        
        thresholds = {"safe_below": 1.81, "distress_above": 2.99, "direction": "lower"}
        
        if z > 2.99:
            zone = "safe"
            interpretation = (
                "The company is in the SAFE zone (Z > 2.99). "
                "Based on the original Altman model, the probability of bankruptcy "
                "is very low (less than 1% within 2 years). The company shows "
                "strong financial health across all five components."
            )
        elif z > 1.81:
            zone = "grey"
            interpretation = (
                "The company is in the GREY zone (1.81 < Z < 2.99). "
                "This is an indeterminate area where the model cannot reliably "
                "classify the company. Additional analysis and qualitative factors "
                "should be considered. Historically, about 35% of companies in this "
                "zone may face financial distress."
            )
        else:
            zone = "distress"
            interpretation = (
                "The company is in the DISTRESS zone (Z < 1.81). "
                "This indicates a high probability of financial distress or bankruptcy "
                "within 2 years (historically > 80%). Immediate attention to "
                "liquidity, leverage, and profitability is recommended."
            )
        
        return PredictionResult(
            model_name="Altman Z-Score (Public)",
            model_year="1968",
            score=z,
            zone=zone,
            probability=_score_to_probability(z, thresholds),
            description=(
                "The Altman Z-Score is the most widely used bankruptcy prediction model. "
                "It combines five financial ratios into a single score that predicts "
                "the likelihood of a company going bankrupt within 2 years."
            ),
            interpretation=interpretation,
            components={
                "X1 (Working Capital / Total Assets)": round(x1, 4),
                "X2 (Retained Earnings / Total Assets)": round(x2, 4),
                "X3 (EBIT / Total Assets)": round(x3, 4),
                "X4 (Market Value Equity / Total Liabilities)": round(x4, 4),
                "X5 (Revenue / Total Assets)": round(x5, 4),
            },
        )
    
    def altman_z_score_private(
        self,
        working_capital: float,
        total_assets: float,
        retained_earnings: float,
        ebit: float,
        book_value_equity: float,
        total_liabilities: float,
        revenue: float,
    ) -> PredictionResult:
        """
        Altman Z'-Score for Private Companies (1983 revision).
        Z' = 0.717*X1 + 0.847*X2 + 3.107*X3 + 0.420*X4 + 0.998*X5
        
        Zones:
          Z' > 2.90  → Safe Zone
          1.23 < Z' < 2.90 → Grey Zone
          Z' < 1.23  → Distress Zone
        """
        x1 = _safe_div(working_capital, total_assets)
        x2 = _safe_div(retained_earnings, total_assets)
        x3 = _safe_div(ebit, total_assets)
        x4 = _safe_div(book_value_equity, total_liabilities)
        x5 = _safe_div(revenue, total_assets)
        
        z_prime = 0.717 * x1 + 0.847 * x2 + 3.107 * x3 + 0.420 * x4 + 0.998 * x5
        z_prime = round(z_prime, 4)
        
        thresholds = {"safe_below": 1.23, "distress_above": 2.90, "direction": "lower"}
        
        if z_prime > 2.90:
            zone = "safe"
            interpretation = (
                "The company is in the SAFE zone (Z' > 2.90). "
                "As a private company, this score suggests strong financial stability. "
                "The adapted model uses book value instead of market capitalization, "
                "making it more suitable for non-publicly-traded firms."
            )
        elif z_prime > 1.23:
            zone = "grey"
            interpretation = (
                "The company is in the GREY zone (1.23 < Z' < 2.90). "
                "Further investigation into cash flow patterns, management quality, "
                "and industry conditions is recommended to form a complete assessment."
            )
        else:
            zone = "distress"
            interpretation = (
                "The company is in the DISTRESS zone (Z' < 1.23). "
                "This is a serious warning sign. The company should urgently review "
                "its capital structure, cost management, and revenue sustainability."
            )
        
        return PredictionResult(
            model_name="Altman Z'-Score (Private)",
            model_year="1983",
            score=z_prime,
            zone=zone,
            probability=_score_to_probability(z_prime, thresholds),
            description=(
                "The Altman Z'-Score is adapted for private companies by replacing "
                "market value of equity with book value. This version is more "
                "appropriate for non-publicly-traded firms and SMEs."
            ),
            interpretation=interpretation,
            components={
                "X1 (Working Capital / Total Assets)": round(x1, 4),
                "X2 (Retained Earnings / Total Assets)": round(x2, 4),
                "X3 (EBIT / Total Assets)": round(x3, 4),
                "X4 (Book Value Equity / Total Liabilities)": round(x4, 4),
                "X5 (Revenue / Total Assets)": round(x5, 4),
            },
        )
    
    def springate(
        self,
        working_capital: float,
        total_assets: float,
        net_income: float,
        current_liabilities: float,
        revenue: float,
        total_assets_dup: float,
    ) -> PredictionResult:
        """
        Springate Model (1978) - Canadian bankruptcy prediction model.
        Z = 1.03*X1 + 3.07*X2 + 0.66*X3 + 0.4*X4
        
        Zones:
          Z > 0.862  → Safe
          Z < 0.862  → Distress
        
        Note: No grey zone in original model, but we add one for UX.
        """
        x1 = _safe_div(working_capital, total_assets)
        x2 = _safe_div(net_income, current_liabilities)
        x3 = _safe_div(ebit if (ebit := net_income + 0) else net_income, current_liabilities)  # Approximate
        x3 = _safe_div(net_income * 1.2, current_liabilities)  # Approximate EBIT
        x4 = _safe_div(revenue, total_assets_dup if total_assets_dup > 0 else total_assets)
        
        z = 1.03 * x1 + 3.07 * x2 + 0.66 * x3 + 0.4 * x4
        z = round(z, 4)
        
        thresholds = {"safe_below": 0.55, "distress_above": 0.862, "direction": "lower"}
        
        if z > 0.862:
            zone = "safe"
            interpretation = (
                "The company passes the Springate test (Z > 0.862). "
                "The model predicts the company is NOT likely to go bankrupt. "
                "The Springate model emphasizes the relationship between "
                "profitability and short-term obligations."
            )
        elif z > 0.55:
            zone = "grey"
            interpretation = (
                "The company is in a borderline area of the Springate model. "
                "While above the original distress threshold, the margin is thin. "
                "Monitoring cash flow and current liabilities is recommended."
            )
        else:
            zone = "distress"
            interpretation = (
                "The company FAILS the Springate test (Z < 0.862). "
                "The model predicts a significant risk of bankruptcy. "
                "Key concerns include working capital adequacy and "
                "profitability relative to current obligations."
            )
        
        return PredictionResult(
            model_name="Springate Model",
            model_year="1978",
            score=z,
            zone=zone,
            probability=_score_to_probability(z, thresholds),
            description=(
                "The Springate model was developed by Gordon L. Springate (1978) "
                "using stepwise multiple discriminant analysis on Canadian firms. "
                "It focuses on working capital, profitability relative to "
                "current liabilities, and asset utilization efficiency."
            ),
            interpretation=interpretation,
            components={
                "X1 (Working Capital / Total Assets)": round(x1, 4),
                "X2 (Net Income / Current Liabilities)": round(x2, 4),
                "X3 (EBIT Approx. / Current Liabilities)": round(x3, 4),
                "X4 (Revenue / Total Assets)": round(x4, 4),
            },
        )
    
    def ohlson_o_score(
        self,
        total_assets: float,
        total_liabilities: float,
        working_capital: float,
        current_liabilities: float,
        net_income: float,
        revenue: float,
        ebit: float,
        retained_earnings: Optional[float] = None,
        fund_from_operations: Optional[float] = None,
    ) -> PredictionResult:
        """
        Ohlson O-Score (1980) - Logistic regression bankruptcy model.
        Uses 9 financial variables with logistic coefficients.
        
        The model outputs a probability between 0 and 1.
        """
        # Calculate the 9 Ohlson variables
        size = math.log(total_assets) if total_assets > 0 else 0
        tl_ta = _safe_div(total_liabilities, total_assets)
        wc_ta = _safe_div(working_capital, total_assets)
        cl_ca = _safe_div(current_liabilities, total_assets + working_capital) if (total_assets + working_capital) != 0 else 0
        
        # Intangible / Total Assets — assume 0 if not provided
        int_ta = 0.0
        
        # Fund from operations / Total Assets
        ffo_ta = _safe_div(fund_from_operations if fund_from_operations else ebit, total_assets)
        
        # Net Income / Total Assets (2 years lag — we approximate with current)
        ni_ta = _safe_div(net_income, total_assets)
        
        # Change in Net Income (approximate as 0 if single period)
        delta_ni = 0.0
        
        # Ohlson coefficients (from original 1980 paper)
        # O = -1.32 - 0.407*size + 6.03*tl_ta - 1.43*wc_ta + 0.0757*cl_ca
        #     - 2.37*int_ta - 1.83*ni_ta + 0.285*delta_ni - 1.72*ffo_ta
        
        o_score = (
            -1.32
            - 0.407 * size
            + 6.03 * tl_ta
            - 1.43 * wc_ta
            + 0.0757 * cl_ca
            - 2.37 * int_ta
            - 1.83 * ni_ta
            + 0.285 * delta_ni
            - 1.72 * ffo_ta
        )
        o_score = round(o_score, 4)
        
        # Convert to probability using logistic function
        probability_raw = _sigmoid(o_score) * 100
        probability = round(probability_raw, 1)
        
        thresholds = {"safe_below": -2.0, "distress_above": 0.5, "direction": "higher"}
        
        if o_score < -2.0:
            zone = "safe"
            interpretation = (
                f"The Ohlson O-Score indicates a low bankruptcy probability ({probability:.1f}%). "
                "The logistic regression model, which is considered more statistically rigorous "
                "than discriminant analysis, suggests the company's financial structure "
                "is sound and sustainable."
            )
        elif o_score < 0.5:
            zone = "grey"
            interpretation = (
                f"The Ohlson O-Score places the company in a moderate risk zone "
                f"({probability:.1f}% distress probability). While not immediately alarming, "
                f"this warrants closer monitoring of leverage ratios and operating cash flows."
            )
        else:
            zone = "distress"
            interpretation = (
                f"The Ohlson O-Score signals significant distress risk ({probability:.1f}%). "
                f"The model's logistic approach identifies the company's financial profile "
                f"as similar to firms that subsequently filed for bankruptcy."
            )
        
        return PredictionResult(
            model_name="Ohlson O-Score",
            model_year="1980",
            score=o_score,
            zone=zone,
            probability=probability,
            description=(
                "The Ohlson O-Score (1980) uses logistic regression rather than "
                "discriminant analysis, making it statistically more robust. It was "
                "developed on a sample of 105 bankrupt and 2,058 non-bankrupt firms. "
                "It directly outputs a probability of bankruptcy."
            ),
            interpretation=interpretation,
            components={
                "SIZE (log Total Assets)": round(size, 4),
                "TL/TA (Total Liabilities / Total Assets)": round(tl_ta, 4),
                "WC/TA (Working Capital / Total Assets)": round(wc_ta, 4),
                "CL/CA (Current Liab / (Assets + WC))": round(cl_ca, 4),
                "INT/TA (Intangibles / Total Assets)": round(int_ta, 4),
                "NI/TA (Net Income / Total Assets)": round(ni_ta, 4),
                "FFO/TA (Funds from Ops / Total Assets)": round(ffo_ta, 4),
                "O-Score Raw": o_score,
                "Bankruptcy Probability": f"{probability}%",
            },
        )
    
    def grover(
        self,
        working_capital: float,
        total_assets: float,
        retained_earnings: float,
        ebit: float,
        book_value_equity: float,
        total_liabilities: float,
        revenue: float,
    ) -> PredictionResult:
        """
        Grover Model - A simplified bankruptcy prediction model.
        Similar structure to Altman but with recalibrated coefficients.
        Z = 1.25*X1 + 0.35*X2 + 3.25*X3 + 0.55*X4 + 1.0*X5
        
        Zones:
          Z > 1.30  → Safe
          0.60 < Z < 1.30 → Grey
          Z < 0.60  → Distress
        """
        x1 = _safe_div(working_capital, total_assets)
        x2 = _safe_div(retained_earnings, total_assets)
        x3 = _safe_div(ebit, total_assets)
        x4 = _safe_div(book_value_equity, total_liabilities)
        x5 = _safe_div(revenue, total_assets)
        
        z = 1.25 * x1 + 0.35 * x2 + 3.25 * x3 + 0.55 * x4 + 1.0 * x5
        z = round(z, 4)
        
        thresholds = {"safe_below": 0.60, "distress_above": 1.30, "direction": "lower"}
        
        if z > 1.30:
            zone = "safe"
            interpretation = (
                "The Grover model classifies the company as SAFE (Z > 1.30). "
                "This model places heavy emphasis on operating profitability (X3) "
                "and uses book value for equity measurement, making it practical "
                "for private company analysis."
            )
        elif z > 0.60:
            zone = "grey"
            interpretation = (
                "The company falls in the Grover model's grey zone (0.60-1.30). "
                "This suggests moderate risk that could swing either way depending "
                "on future operational performance and market conditions."
            )
        else:
            zone = "distress"
            interpretation = (
                "The Grover model flags the company as being in DISTRESS (Z < 0.60). "
                "The low score indicates fundamental weaknesses in asset utilization, "
                "profitability, or capital structure that require immediate remediation."
            )
        
        return PredictionResult(
            model_name="Grover Model",
            model_year="-",
            score=z,
            zone=zone,
            probability=_score_to_probability(z, thresholds),
            description=(
                "The Grover model is a derivative of the Altman Z-Score framework "
                "with recalibrated coefficients. It is particularly useful as a "
                "cross-validation check against other models."
            ),
            interpretation=interpretation,
            components={
                "X1 (Working Capital / Total Assets)": round(x1, 4),
                "X2 (Retained Earnings / Total Assets)": round(x2, 4),
                "X3 (EBIT / Total Assets)": round(x3, 4),
                "X4 (Book Value Equity / Total Liabilities)": round(x4, 4),
                "X5 (Revenue / Total Assets)": round(x5, 4),
            },
        )
    
    def predict_all(
        self,
        total_assets: float,
        total_liabilities: float,
        total_equity: float,
        net_income: float,
        revenue: float,
        ebit: float,
        current_assets: float,
        current_liabilities: float,
        interest_expense: float = 0.0,
        retained_earnings: Optional[float] = None,
        market_value_equity: Optional[float] = None,
    ) -> dict:
        """
        Run all prediction models and return combined results.
        
        Returns:
            dict with:
              - overall_assessment: str
              - consensus_probability: float (0-100)
              - models: list of model result dicts
              - recommendations: list of str
        """
        working_capital = current_assets - current_liabilities
        if retained_earnings is None:
            retained_earnings = total_equity * 0.6  # Estimate
        if market_value_equity is None:
            market_value_equity = total_equity  # Fallback to book value
        
        # Run all models
        self.results = [
            self.altman_z_score_public(
                working_capital=working_capital,
                total_assets=total_assets,
                retained_earnings=retained_earnings,
                ebit=ebit,
                market_value_equity=market_value_equity,
                total_liabilities=total_liabilities,
                revenue=revenue,
            ),
            self.altman_z_score_private(
                working_capital=working_capital,
                total_assets=total_assets,
                retained_earnings=retained_earnings,
                ebit=ebit,
                book_value_equity=total_equity,
                total_liabilities=total_liabilities,
                revenue=revenue,
            ),
            self.springate(
                working_capital=working_capital,
                total_assets=total_assets,
                net_income=net_income,
                current_liabilities=current_liabilities,
                revenue=revenue,
                total_assets_dup=total_assets,
            ),
            self.ohlson_o_score(
                total_assets=total_assets,
                total_liabilities=total_liabilities,
                working_capital=working_capital,
                current_liabilities=current_liabilities,
                net_income=net_income,
                revenue=revenue,
                ebit=ebit,
                retained_earnings=retained_earnings,
            ),
            self.grover(
                working_capital=working_capital,
                total_assets=total_assets,
                retained_earnings=retained_earnings,
                ebit=ebit,
                book_value_equity=total_equity,
                total_liabilities=total_liabilities,
                revenue=revenue,
            ),
        ]
        
        # Calculate consensus
        avg_prob = sum(r.probability for r in self.results) / len(self.results)
        
        # Count zone votes
        zone_counts = {"safe": 0, "grey": 0, "distress": 0}
        for r in self.results:
            zone_counts[r.zone] += 1
        
        if zone_counts["distress"] >= 3:
            overall = "distress"
            overall_text = "HIGH RISK — Multiple models indicate significant financial distress"
        elif zone_counts["distress"] >= 1 or zone_counts["grey"] >= 3:
            overall = "grey"
            overall_text = "MODERATE RISK — Mixed signals across models, further investigation needed"
        else:
            overall = "safe"
            overall_text = "LOW RISK — Models consistently indicate financial stability"
        
        # Generate recommendations
        recommendations = []
        
        if avg_prob > 50:
            recommendations.append(
                "URGENT: Seek professional financial advisory immediately. "
                "Multiple bankruptcy prediction models indicate elevated risk."
            )
        
        if avg_prob > 30:
            recommendations.append(
                "Review capital structure: Consider debt restructuring or equity infusion "
                "to improve leverage ratios across all models."
            )
        
        # Check component-level issues
        wc_ta = _safe_div(working_capital, total_assets)
        if wc_ta < 0.1:
            recommendations.append(
                "Working capital is critically low relative to total assets. "
                "Focus on improving current asset management and negotiating "
                "better terms with suppliers."
            )
        
        roa = _safe_div(net_income, total_assets)
        if roa < 0.03:
            recommendations.append(
                "Return on assets is below healthy thresholds. "
                "Evaluate operational efficiency and consider divesting "
                "underperforming assets."
            )
        
        de_ratio = _safe_div(total_liabilities, total_equity)
        if de_ratio > 2.0:
            recommendations.append(
                "Debt-to-equity ratio is high. Prioritize debt reduction "
                "and avoid taking on additional leverage until ratios improve."
            )
        
        if avg_prob < 20:
            recommendations.append(
                "The company shows strong financial health. Maintain current "
                "practices and continue monitoring key ratios quarterly."
            )
        
        if not recommendations:
            recommendations.append(
                "Continue regular financial monitoring and compare results "
                "with industry benchmarks for more context."
            )
        
        return {
            "overall_assessment": overall,
            "overall_text": overall_text,
            "consensus_probability": round(avg_prob, 1),
            "zone_votes": zone_counts,
            "models": [
                {
                    "model_name": r.model_name,
                    "model_year": r.model_year,
                    "score": r.score,
                    "zone": r.zone,
                    "probability": r.probability,
                    "description": r.description,
                    "interpretation": r.interpretation,
                    "components": r.components,
                }
                for r in self.results
            ],
            "recommendations": recommendations,
        }


def predict_from_analysis(analysis_data: dict) -> dict:
    """
    Convenience function: extract financial figures from analysis ratio data
    and run all prediction models.
    
    Args:
        analysis_data: dict with 'ratios' list from the analyzer output
    
    Returns:
        Prediction results dict from BankruptcyPredictor.predict_all()
    """
    # We need the raw financial figures, but we only have ratios.
    # For prediction, we reconstruct estimates from ratios.
    # This is an approximation — best used with raw data when available.
    
    ratios = analysis_data.get("ratios", [])
    ratio_map = {r["ratio_name"]: r["value"] for r in ratios}
    
    # Since we have ratios but not raw values, we use a reference total_assets = 100
    # and back-calculate. This gives proportional results that are directionally correct.
    # For accurate results, users should provide raw financial statements.
    
    # Actually, let's check if the analysis was stored with raw values
    # If not, we compute from ratios using assumed base
    ref_assets = 1000000  # Reference $1M
    
    # Back-calculate from ratios
    net_income = ratio_map.get("net_profit_margin", 0) * ref_assets
    revenue = net_income / ratio_map.get("net_profit_margin", 1) if ratio_map.get("net_profit_margin", 0) > 0 else ref_assets
    
    gross_profit = ratio_map.get("gross_profit_margin", 0) * revenue
    cogs = revenue - gross_profit
    ebit = ratio_map.get("operating_margin", ratio_map.get("net_profit_margin", 0)) * revenue
    
    total_assets = ref_assets
    total_equity = net_income / ratio_map.get("return_on_equity", 0.1) if ratio_map.get("return_on_equity", 0) > 0 else ref_assets * 0.5
    total_liabilities = total_assets - total_equity
    
    current_assets = ratio_map.get("current_ratio", 2.0) * (total_liabilities * 0.5)
    current_liabilities = total_liabilities * 0.5
    
    inventory = (cogs / ratio_map.get("inventory_turnover", 6.0)) if ratio_map.get("inventory_turnover", 0) > 0 else 0
    accounts_receivable = revenue / ratio_map.get("receivables_turnover", 8.0) if ratio_map.get("receivables_turnover", 0) > 0 else 0
    
    interest_expense = ebit / ratio_map.get("interest_coverage", 5.0) if ratio_map.get("interest_coverage", 0) > 0 else 0
    
    working_capital = current_assets - current_liabilities
    retained_earnings = total_equity * 0.6
    
    predictor = BankruptcyPredictor()
    return predictor.predict_all(
        total_assets=total_assets,
        total_liabilities=total_liabilities,
        total_equity=total_equity,
        net_income=net_income,
        revenue=revenue,
        ebit=ebit,
        current_assets=current_assets,
        current_liabilities=current_liabilities,
        interest_expense=interest_expense,
        retained_earnings=retained_earnings,
    )
