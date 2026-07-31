"""Command-line interface."""

from __future__ import annotations

import argparse
from pathlib import Path

from .charts import create_dashboard
from .io import load_statement
from .ratios import calculate_ratios
from .report import create_html_report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Analyze CSV/XLSX financial statements")
    parser.add_argument("input", help="financial statement CSV or Excel file")
    parser.add_argument("--output", default="finsight-output", help="output directory")
    parser.add_argument("--sheet", default=0, help="Excel sheet name or zero-based index")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    output = Path(args.output)
    statement = load_statement(args.input, sheet_name=args.sheet)
    ratios = calculate_ratios(statement)
    output.mkdir(parents=True, exist_ok=True)
    ratios.to_csv(output / "ratios.csv", index=False)
    chart = create_dashboard(statement, ratios, output / "dashboard.png")
    report = create_html_report(ratios, chart, output / "report.html")
    print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
