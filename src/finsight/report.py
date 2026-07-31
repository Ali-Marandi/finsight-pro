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
    head = "".join(f"<th>{escape(RATIO_LABELS[column])}</th>" for column in columns)
    rows = []
    for _, row in ratios.iterrows():
        cells = "".join(f"<td>{_format(row[column], column)}</td>" for column in columns)
        rows.append(f"<tr><th>{escape(str(row['period']))}</th>{cells}</tr>")
    generated = datetime.now(timezone.utc).isoformat(timespec="seconds")
    html = f"""<!doctype html>
<html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>FinSight financial analysis</title>
<style>
body{{font:14px system-ui;margin:0;background:#f4f7fb;color:#15202b}}
main{{max-width:1400px;margin:auto;padding:32px}}h1{{margin-bottom:4px}}
.meta{{color:#5c6b7a;margin-bottom:24px}}img{{width:100%;background:white;border-radius:16px}}
.table{{overflow:auto;background:white;border-radius:16px;margin-top:24px}}
table{{border-collapse:collapse;width:100%;white-space:nowrap}}th,td{{padding:11px 13px;border-bottom:1px solid #e8edf2;text-align:right}}
thead th{{background:#102a43;color:white;position:sticky;top:0}}tbody th{{text-align:left}}
</style><main><h1>FinSight financial analysis</h1><div class="meta">Generated {escape(generated)}</div>
<img alt="Financial charts" src="data:image/png;base64,{image}">
<div class="table"><table><thead><tr><th>Period</th>{head}</tr></thead>
<tbody>{''.join(rows)}</tbody></table></div></main></html>"""
    target.write_text(html, encoding="utf-8")
    return target
