"""Financial ratio engine with safe, auditable formulas."""

from __future__ import annotations

import math

import pandas as pd


def _divide(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    result = numerator.div(denominator.where(denominator.ne(0)))
    return result.replace([math.inf, -math.inf], pd.NA)


def calculate_ratios(statement: pd.DataFrame) -> pd.DataFrame:
    """Return one row per period with profitability, liquidity and leverage ratios."""

    ratios = pd.DataFrame({"period": statement["period"].astype(str)})
    ratios["gross_margin"] = _divide(statement["gross_profit"], statement["revenue"])
    ratios["operating_margin"] = _divide(statement["operating_income"], statement["revenue"])
    ratios["net_margin"] = _divide(statement["net_income"], statement["revenue"])
    ratios["current_ratio"] = _divide(statement["current_assets"], statement["current_liabilities"])
    ratios["quick_ratio"] = _divide(
        statement["current_assets"] - statement["inventory"],
        statement["current_liabilities"],
    )
    ratios["cash_ratio"] = _divide(statement["cash"], statement["current_liabilities"])
    ratios["debt_to_equity"] = _divide(statement["total_liabilities"], statement["equity"])
    ratios["debt_to_assets"] = _divide(statement["total_liabilities"], statement["total_assets"])
    ratios["return_on_assets"] = _divide(statement["net_income"], statement["total_assets"])
    ratios["return_on_equity"] = _divide(statement["net_income"], statement["equity"])
    ratios["cash_flow_margin"] = _divide(statement["operating_cash_flow"], statement["revenue"])
    ratios["interest_coverage"] = _divide(statement["operating_income"], statement["interest_expense"])
    
    # Efficiency Ratios
    ratios["asset_turnover"] = _divide(statement["revenue"], statement["total_assets"])
    ratios["inventory_turnover"] = _divide(statement["cost_of_goods_sold"], statement["inventory"])
    ratios["receivables_turnover"] = _divide(statement["revenue"], statement["accounts_receivable"])
    
    return ratios


RATIO_LABELS = {
    "gross_margin": "Gross margin",
    "operating_margin": "Operating margin",
    "net_margin": "Net margin",
    "current_ratio": "Current ratio",
    "quick_ratio": "Quick ratio",
    "cash_ratio": "Cash ratio",
    "debt_to_equity": "Debt / equity",
    "debt_to_assets": "Debt / assets",
    "return_on_assets": "Return on assets",
    "return_on_equity": "Return on equity",
    "cash_flow_margin": "Operating cash-flow margin",
    "interest_coverage": "Interest coverage",
    "asset_turnover": "Asset turnover",
    "inventory_turnover": "Inventory turnover",
    "receivables_turnover": "Receivables turnover",
}
