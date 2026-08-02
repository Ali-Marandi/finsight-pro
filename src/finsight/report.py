"""Generate a portable HTML analysis report."""

from __future__ import annotations

import base64
from datetime import datetime, timezone
from html import escape
from pathlib import Path

import pandas as pd

from .ratios import RATIO_LABELS


def _format(value: object, ratio: str) -> str:
    if pd.isna(value):
        return "N/A"
    number = float(value)
    if ratio in {"gross_margin", "operating_margin", "net_margin", "debt_to_assets",
                 "return_on_assets", "return_on_equity", "cash_flow_margin"}:
        return f"{number:.2%}"
    return f"{number:,.2f}"


def create_html_report(ratios: pd.DataFrame, chart: str | Path, output: str | Path) -> Path:
    target = Path(output)
    target.parent.mkdir(parents=True, exist_ok=True)
    image = base64.b64encode(Path(chart).read_bytes()).decode("ascii")
    columns = [column for column in ratios.columns if column != "period"]
    
    # Define groups for a cleaner table layout
    profitability = ["gross_margin", "operating_margin", "net_margin", "return_on_assets", "return_on_equity"]
    liquidity = ["current_ratio", "quick_ratio", "cash_ratio"]
    leverage = ["debt_to_equity", "debt_to_assets", "interest_coverage"]
    efficiency = ["asset_turnover", "inventory_turnover", "receivables_turnover"]
    
    def generate_table_section(title: str, cols: list[str]):
        head = "".join(f"<th>{escape(RATIO_LABELS[c])}</th>" for c in cols if c in ratios.columns)
        rows = []
        for _, row in ratios.iterrows():
            cells = "".join(f"<td>{_format(row[c], c)}</td>" for c in cols if c in ratios.columns)
            rows.append(f"<tr><th>{escape(str(row['period']))}</th>{cells}</tr>")
        return f"""
        <div class="section">
            <h2>{escape(title)}</h2>
            <div class="table-container">
                <table>
                    <thead><tr><th>Period</th>{head}</tr></thead>
                    <tbody>{''.join(rows)}</tbody>
                </table>
            </div>
        </div>
        """

    sections = [
        generate_table_section("Profitability & Returns", profitability),
        generate_table_section("Liquidity", liquidity),
        generate_table_section("Leverage & Coverage", leverage),
        generate_table_section("Efficiency", efficiency)
    ]

    generated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    
    html = f"""<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>FinSight Pro - Financial Analysis Report</title>
    <style>
        :root {{
            --primary: #2563eb;
            --bg: #f8fafc;
            --text: #1e293b;
            --border: #e2e8f0;
            --card-bg: #ffffff;
        }}
        body {{
            font-family: 'Inter', system-ui, -apple-system, sans-serif;
            line-height: 1.5;
            margin: 0;
            background-color: var(--bg);
            color: var(--text);
        }}
        header {{
            background: #1e293b;
            color: white;
            padding: 2rem 1rem;
            text-align: center;
        }}
        main {{
            max-width: 1200px;
            margin: 2rem auto;
            padding: 0 1rem;
        }}
        .meta {{
            font-size: 0.875rem;
            color: #94a3b8;
            margin-top: 0.5rem;
        }}
        .dashboard-img {{
            width: 100%;
            height: auto;
            border-radius: 0.75rem;
            box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);
            background: white;
            margin-bottom: 2rem;
        }}
        .section {{
            background: var(--card-bg);
            border-radius: 0.75rem;
            padding: 1.5rem;
            margin-bottom: 2rem;
            box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1);
        }}
        h2 {{
            margin-top: 0;
            font-size: 1.25rem;
            border-bottom: 2px solid var(--primary);
            display: inline-block;
            padding-bottom: 0.25rem;
            margin-bottom: 1.5rem;
        }}
        .table-container {{
            overflow-x: auto;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            text-align: right;
        }}
        th, td {{
            padding: 0.75rem 1rem;
            border-bottom: 1px solid var(--border);
        }}
        thead th {{
            background: #f1f5f9;
            font-weight: 600;
            color: #475569;
        }}
        tbody th {{
            text-align: left;
            font-weight: 600;
        }}
        tr:hover {{
            background-color: #f8fafc;
        }}
    </style>
</head>
<body>
    <header>
        <h1>FinSight Pro Analysis</h1>
        <div class="meta">Report generated on {escape(generated)}</div>
    </header>
    <main>
        <img class="dashboard-img" alt="Financial Performance Dashboard" src="data:image/png;base64,{image}">
        {''.join(sections)}
    </main>
</body>
</html>"""
    target.write_text(html, encoding="utf-8")
    return target
