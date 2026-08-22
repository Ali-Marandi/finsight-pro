"""Consolidation Engine — Combine financial statements from multiple companies (parent + subsidiaries). Handles elimination entries, minority interest, and generates consolidated ratios."""
from typing import Optional


def consolidate_statements(
    companies: list[dict],
    ownership_pcts: Optional[list[float]] = None,
    parent_index: int = 0,
) -> dict:
    """Consolidate multiple company financial statements.
    
    Args:
        companies: List of company financial data dicts, each with ratio/financial data
        ownership_pcts: Ownership percentage for each company (0-100). First is parent (100%)
        parent_index: Index of the parent company in the list
    
    Returns:
        Consolidated financial data and ratios
    """
    if not companies:
        raise ValueError("At least one company is required")
    
    if ownership_pcts is None:
        ownership_pcts = [100.0] + [100.0] * (len(companies) - 1)
    
    if len(ownership_pcts) != len(companies):
        raise ValueError("ownership_pcts must match companies length")
    
    # Step 1: Aggregate all financial figures (proportional to ownership)
    total_revenue = sum(
        c.get('revenue', c.get('total_revenue', 0)) * (ownership_pcts[i] / 100)
        for i, c in enumerate(companies)
    )
    total_cogs = sum(
        c.get('cogs', c.get('cost_of_goods_sold', 0)) * (ownership_pcts[i] / 100)
        for i, c in enumerate(companies)
    )
    total_gross_profit = total_revenue - total_cogs
    total_net_income = sum(
        c.get('net_income', c.get('net_profit', 0)) * (ownership_pcts[i] / 100)
        for i, c in enumerate(companies)
    )
    total_ebit = sum(
        c.get('ebit', c.get('operating_income', 0)) * (ownership_pcts[i] / 100)
        for i, c in enumerate(companies)
    )
    total_interest_expense = sum(
        c.get('interest_expense', 0) * (ownership_pcts[i] / 100)
        for i, c in enumerate(companies)
    )
    total_tax_expense = sum(
        c.get('tax_expense', 0) * (ownership_pcts[i] / 100)
        for i, c in enumerate(companies)
    )
    
    total_assets = sum(
        c.get('total_assets', 0) * (ownership_pcts[i] / 100)
        for i, c in enumerate(companies)
    )
    total_equity = sum(
        c.get('total_equity', 0) * (ownership_pcts[i] / 100)
        for i, c in enumerate(companies)
    )
    total_liabilities = sum(
        c.get('total_liabilities', 0) * (ownership_pcts[i] / 100)
        for i, c in enumerate(companies)
    )
    total_current_assets = sum(
        c.get('current_assets', 0) * (ownership_pcts[i] / 100)
        for i, c in enumerate(companies)
    )
    total_current_liabilities = sum(
        c.get('current_liabilities', 0) * (ownership_pcts[i] / 100)
        for i, c in enumerate(companies)
    )
    total_inventory = sum(
        c.get('inventory', 0) * (ownership_pcts[i] / 100)
        for i, c in enumerate(companies)
    )
    total_cash = sum(
        c.get('cash', 0) * (ownership_pcts[i] / 100)
        for i, c in enumerate(companies)
    )
    total_ar = sum(
        c.get('accounts_receivable', 0) * (ownership_pcts[i] / 100)
        for i, c in enumerate(companies)
    )
    
    # Step 2: Elimination entries (intercompany transactions)
    # Simplified: estimate 5-15% of intercompany transactions
    elimination_rate = 0.05 if len(companies) <= 2 else (0.10 if len(companies) <= 4 else 0.15)
    eliminations = {
        'revenue_elimination': round(total_revenue * elimination_rate, 2),
        'cogs_elimination': round(total_cogs * elimination_rate, 2),
        'ar_elimination': round(total_ar * elimination_rate * 0.5, 2),
        'ap_elimination': round(total_current_liabilities * elimination_rate * 0.3, 2),
    }
    
    # Apply eliminations
    adj_revenue = total_revenue - eliminations['revenue_elimination']
    adj_cogs = total_cogs - eliminations['cogs_elimination']
    adj_gross_profit = adj_revenue - adj_cogs
    adj_assets = total_assets - eliminations['ar_elimination']
    adj_liabilities = total_liabilities - eliminations['ap_elimination']
    adj_ar = total_ar - eliminations['ar_elimination']
    
    # Recalculate equity to maintain balance
    adj_equity = adj_assets - adj_liabilities
    
    # Step 3: Minority Interest
    minority_interest = 0
    for i, c in enumerate(companies):
        if i == parent_index:
            continue
        pct = ownership_pcts[i] / 100
        if pct < 1.0:
            equity_contribution = c.get('total_equity', 0) * (1 - pct)
            ni_contribution = c.get('net_income', 0) * (1 - pct)
            minority_interest += equity_contribution
    
    parent_equity = adj_equity - minority_interest
    
    # Step 4: Compute consolidated ratios
    ratios = []
    
    if adj_revenue > 0:
        ratios.append({"category": "profitability", "ratio_name": "gross_profit_margin", "value": adj_gross_profit / adj_revenue, "unit": "%", "benchmark": 0.35, "status": _classify(adj_gross_profit / adj_revenue, (0.30, 0.60), (0.15, 0.70))})
        ratios.append({"category": "profitability", "ratio_name": "net_profit_margin", "value": total_net_income / adj_revenue, "unit": "%", "benchmark": 0.12, "status": _classify(total_net_income / adj_revenue, (0.08, 0.25), (0.02, 0.30))})
        ratios.append({"category": "profitability", "ratio_name": "operating_margin", "value": total_ebit / adj_revenue, "unit": "%", "benchmark": 0.15, "status": _classify(total_ebit / adj_revenue, (0.10, 0.25), (0.03, 0.30))})
    
    if adj_assets > 0:
        ratios.append({"category": "profitability", "ratio_name": "return_on_assets", "value": total_net_income / adj_assets, "unit": "%", "benchmark": 0.08, "status": _classify(total_net_income / adj_assets, (0.05, 0.20), (0.01, 0.25))})
    
    if parent_equity > 0:
        ratios.append({"category": "profitability", "ratio_name": "return_on_equity", "value": total_net_income / parent_equity, "unit": "%", "benchmark": 0.15, "status": _classify(total_net_income / parent_equity, (0.10, 0.30), (0.03, 0.35))})
    
    if adj_current_liabilities > 0:
        cr = adj_current_assets / adj_current_liabilities
        ratios.append({"category": "liquidity", "ratio_name": "current_ratio", "value": cr, "unit": "x", "benchmark": 2.0, "status": _classify(cr, (1.5, 3.0), (1.0, 4.0))})
        qr = (adj_current_assets - total_inventory) / adj_current_liabilities
        ratios.append({"category": "liquidity", "ratio_name": "quick_ratio", "value": qr, "unit": "x", "benchmark": 1.5, "status": _classify(qr, (1.0, 2.5), (0.5, 3.0))})
    
    if parent_equity > 0:
        de = adj_liabilities / parent_equity
        ratios.append({"category": "leverage", "ratio_name": "debt_to_equity", "value": de, "unit": "x", "benchmark": 0.6, "status": _classify(de, (0.2, 1.0), (0.1, 2.0))})
    
    if adj_assets > 0:
        da = adj_liabilities / adj_assets
        ratios.append({"category": "leverage", "ratio_name": "debt_to_assets", "value": da, "unit": "%", "benchmark": 0.40, "status": _classify(da, (0.20, 0.50), (0.10, 0.70))})
    
    if total_interest_expense > 0:
        icr = total_ebit / total_interest_expense
        ratios.append({"category": "leverage", "ratio_name": "interest_coverage", "value": icr, "unit": "x", "benchmark": 5.0, "status": _classify(icr, (3.0, 10.0), (1.5, 15.0))})
    
    if adj_assets > 0:
        ratios.append({"category": "efficiency", "ratio_name": "asset_turnover", "value": adj_revenue / adj_assets, "unit": "x", "benchmark": 1.0, "status": _classify(adj_revenue / adj_assets, (0.5, 2.0), (0.3, 3.0))})
    
    # Per-company contribution summary
    contributions = []
    for i, c in enumerate(companies):
        c_rev = c.get('revenue', c.get('total_revenue', 0))
        c_ni = c.get('net_income', c.get('net_profit', 0))
        contributions.append({
            "company_name": c.get('company_name', f'Company {i+1}'),
            "revenue": c_rev,
            "net_income": c_ni,
            "ownership_pct": ownership_pcts[i],
            "revenue_contribution": round(c_rev / max(total_revenue, 1) * 100, 1),
        })
    
    return {
        "consolidated_financials": {
            "revenue": round(adj_revenue, 2),
            "gross_profit": round(adj_gross_profit, 2),
            "net_income": round(total_net_income, 2),
            "ebit": round(total_ebit, 2),
            "total_assets": round(adj_assets, 2),
            "total_equity": round(adj_equity, 2),
            "total_liabilities": round(adj_liabilities, 2),
            "current_assets": round(total_current_assets, 2),
            "current_liabilities": round(total_current_liabilities, 2),
            "inventory": round(total_inventory, 2),
            "cash": round(total_cash, 2),
            "accounts_receivable": round(adj_ar, 2),
            "minority_interest": round(minority_interest, 2),
        },
        "eliminations": eliminations,
        "ratios": ratios,
        "contributions": contributions,
        "company_count": len(companies),
    }


def _classify(value: float, good: tuple, warn: tuple) -> str:
    if good[0] <= value <= good[1]:
        return "good"
    elif warn[0] <= value <= warn[1]:
        return "warning"
    return "critical"
