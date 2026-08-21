"""
Financial statement analyzer service.
Wraps the core finsight-pro CLI engine for the desktop API.
"""

import io
import pandas as pd
from typing import Optional


def _classify_status(value: float, good_range: tuple, warn_range: tuple) -> str:
    """Classify a ratio value as good, warning, or critical."""
    if good_range[0] <= value <= good_range[1]:
        return "good"
    elif warn_range[0] <= value <= warn_range[1]:
        return "warning"
    return "critical"


def analyze_financial_statement(
    file_content: bytes,
    filename: str,
    extension: str,
) -> dict:
    """
    Parse a financial statement file and compute all financial ratios.
    
    Returns:
        dict with company_name, period, and ratios list
    """
    # Parse file
    if extension == "csv":
        df = pd.read_csv(io.BytesIO(file_content))
    elif extension in ("xlsx", "xls"):
        df = pd.read_excel(io.BytesIO(file_content))
    else:
        raise ValueError(f"Unsupported format: {extension}")
    
    # Normalize column names
    df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]
    
    # Try to detect company name and period from data
    company_name = filename.replace(f".{extension}", "").replace("_", " ").title()
    period = "Unknown"
    
    # Extract financial figures (flexible column matching)
    def get_value(*possible_names, default=0.0) -> float:
        for name in possible_names:
            for col in df.columns:
                if name in col:
                    val = df[col].iloc[0] if len(df) > 0 else 0
                    try:
                        return float(val)
                    except (ValueError, TypeError):
                        continue
        return default
    
    # Core financial figures
    revenue = get_value("revenue", "sales", "net_sales", "total_revenue")
    cogs = get_value("cost_of_goods", "cogs", "cost_of_revenue")
    gross_profit = get_value("gross_profit", "gross_margin")
    if gross_profit == 0 and revenue > 0:
        gross_profit = revenue - cogs
    
    net_income = get_value("net_income", "net_profit", "net_earnings")
    ebit = get_value("ebit", "operating_income", "operating_profit")
    interest_expense = get_value("interest_expense", "interest")
    tax_expense = get_value("tax", "income_tax")
    
    total_assets = get_value("total_assets", "assets")
    total_equity = get_value("total_equity", "shareholders_equity", "stockholders_equity")
    total_liabilities = get_value("total_liabilities", "liabilities")
    if total_liabilities == 0 and total_assets > 0 and total_equity > 0:
        total_liabilities = total_assets - total_equity
    
    current_assets = get_value("current_assets")
    current_liabilities = get_value("current_liabilities")
    inventory = get_value("inventory", "inventories")
    cash = get_value("cash", "cash_and_equivalents")
    
    accounts_receivable = get_value("accounts_receivable", "receivables")
    average_inventory = get_value("average_inventory")
    if average_inventory == 0:
        average_inventory = inventory
    
    # Calculate all ratios
    ratios = []
    
    # --- Profitability ---
    if revenue > 0:
        gpm = gross_profit / revenue
        ratios.append({
            "category": "profitability",
            "ratio_name": "gross_profit_margin",
            "value": gpm,
            "unit": "%",
            "benchmark": 0.35,
            "status": _classify_status(gpm, (0.30, 0.60), (0.15, 0.70)),
        })
    
    if revenue > 0:
        npm = net_income / revenue
        ratios.append({
            "category": "profitability",
            "ratio_name": "net_profit_margin",
            "value": npm,
            "unit": "%",
            "benchmark": 0.12,
            "status": _classify_status(npm, (0.08, 0.25), (0.02, 0.30)),
        })
    
    if total_assets > 0:
        roa = net_income / total_assets
        ratios.append({
            "category": "profitability",
            "ratio_name": "return_on_assets",
            "value": roa,
            "unit": "%",
            "benchmark": 0.08,
            "status": _classify_status(roa, (0.05, 0.20), (0.01, 0.25)),
        })
    
    if total_equity > 0:
        roe = net_income / total_equity
        ratios.append({
            "category": "profitability",
            "ratio_name": "return_on_equity",
            "value": roe,
            "unit": "%",
            "benchmark": 0.15,
            "status": _classify_status(roe, (0.10, 0.30), (0.03, 0.35)),
        })
    
    if revenue > 0:
        om = ebit / revenue
        ratios.append({
            "category": "profitability",
            "ratio_name": "operating_margin",
            "value": om,
            "unit": "%",
            "benchmark": 0.15,
            "status": _classify_status(om, (0.10, 0.25), (0.03, 0.30)),
        })
    
    # --- Liquidity ---
    if current_liabilities > 0:
        cr = current_assets / current_liabilities
        ratios.append({
            "category": "liquidity",
            "ratio_name": "current_ratio",
            "value": cr,
            "unit": "x",
            "benchmark": 2.0,
            "status": _classify_status(cr, (1.5, 3.0), (1.0, 4.0)),
        })
    
    if current_liabilities > 0:
        quick_assets = current_assets - inventory
        qr = quick_assets / current_liabilities
        ratios.append({
            "category": "liquidity",
            "ratio_name": "quick_ratio",
            "value": qr,
            "unit": "x",
            "benchmark": 1.5,
            "status": _classify_status(qr, (1.0, 2.5), (0.5, 3.0)),
        })
    
    if current_liabilities > 0:
        cashr = cash / current_liabilities
        ratios.append({
            "category": "liquidity",
            "ratio_name": "cash_ratio",
            "value": cashr,
            "unit": "x",
            "benchmark": 0.5,
            "status": _classify_status(cashr, (0.2, 1.0), (0.1, 1.5)),
        })
    
    ratios.append({
        "category": "liquidity",
        "ratio_name": "working_capital",
        "value": current_assets - current_liabilities,
        "unit": "$",
        "benchmark": None,
        "status": "good" if current_assets > current_liabilities else "warning",
    })
    
    # --- Leverage ---
    if total_equity > 0:
        de = total_liabilities / total_equity
        ratios.append({
            "category": "leverage",
            "ratio_name": "debt_to_equity",
            "value": de,
            "unit": "x",
            "benchmark": 0.6,
            "status": _classify_status(de, (0.2, 1.0), (0.1, 2.0)),
        })
    
    if total_assets > 0:
        da = total_liabilities / total_assets
        ratios.append({
            "category": "leverage",
            "ratio_name": "debt_to_assets",
            "value": da,
            "unit": "%",
            "benchmark": 0.40,
            "status": _classify_status(da, (0.20, 0.50), (0.10, 0.70)),
        })
    
    if interest_expense > 0:
        icr = ebit / interest_expense
        ratios.append({
            "category": "leverage",
            "ratio_name": "interest_coverage",
            "value": icr,
            "unit": "x",
            "benchmark": 5.0,
            "status": _classify_status(icr, (3.0, 10.0), (1.5, 15.0)),
        })
    
    if total_equity > 0:
        em = total_assets / total_equity
        ratios.append({
            "category": "leverage",
            "ratio_name": "equity_multiplier",
            "value": em,
            "unit": "x",
            "benchmark": 2.0,
            "status": _classify_status(em, (1.5, 3.0), (1.0, 4.0)),
        })
    
    # --- Efficiency ---
    if total_assets > 0:
        at = revenue / total_assets
        ratios.append({
            "category": "efficiency",
            "ratio_name": "asset_turnover",
            "value": at,
            "unit": "x",
            "benchmark": 1.0,
            "status": _classify_status(at, (0.5, 2.0), (0.3, 3.0)),
        })
    
    if average_inventory > 0:
        it = cogs / average_inventory
        ratios.append({
            "category": "efficiency",
            "ratio_name": "inventory_turnover",
            "value": it,
            "unit": "x",
            "benchmark": 6.0,
            "status": _classify_status(it, (4.0, 10.0), (2.0, 15.0)),
        })
    
    if accounts_receivable > 0:
        rt = revenue / accounts_receivable
        ratios.append({
            "category": "efficiency",
            "ratio_name": "receivables_turnover",
            "value": rt,
            "unit": "x",
            "benchmark": 8.0,
            "status": _classify_status(rt, (5.0, 12.0), (3.0, 15.0)),
        })
    
    if revenue > 0:
        dso = (accounts_receivable / revenue) * 365
        ratios.append({
            "category": "efficiency",
            "ratio_name": "days_sales_outstanding",
            "value": dso,
            "unit": "days",
            "benchmark": 45,
            "status": _classify_status(dso, (20, 45), (15, 60)),
        })
    
    return {
        "company_name": company_name,
        "period": period,
        "ratios": ratios,
    }
