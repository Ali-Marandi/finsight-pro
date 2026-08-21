<h1 align="center">FinSight Pro</h1>

<p align="center">
  <b>Professional-grade financial statement analytics engine</b><br>
  Transform CSV/Excel data into validated ratios, dashboards, and reports.
</p>

<p align="center">
  <a href="https://github.com/Ali-Marandi/finsight-pro/stargazers"><img src="https://img.shields.io/github/stars/Ali-Marandi/finsight-pro?style=social" alt="Stars"></a>
  <a href="https://github.com/Ali-Marandi/finsight-pro/blob/main/LICENSE"><img src="https://img.shields.io/github/license/Ali-Marandi/finsight-pro" alt="License"></a>
  <a href="https://github.com/Ali-Marandi/finsight-pro/releases"><img src="https://img.shields.io/github/v/release/Ali-Marandi/finsight-pro" alt="Release"></a>
  <a href="https://pypi.org/project/finsight-pro/"><img src="https://img.shields.io/pypi/v/finsight-pro" alt="PyPI"></a>
</p>

---

FinSight Pro is a Python library and CLI tool that transforms raw financial data from CSV or Excel files into comprehensive analytical reports with validated ratios, interactive-ready dashboards, and portable HTML reports.

## Features

- **15 Validated Financial Ratios** across Profitability, Liquidity, Leverage, and Efficiency categories
- **Strict Data Validation** with schema checks and numeric consistency verification
- **Visual Dashboards** - High-resolution 4-panel performance charts via Matplotlib
- **Portable HTML Reports** - Modern, responsive reports shareable in any browser
- **Multi-format Ingestion** - CSV, Excel (.xlsx, .xlsm) support
- **Auditable Formulas** - Every ratio is calculated with explicit, inspectable logic

## Quick Start

```bash
n# Install
pip install .

# Analyze a financial statement
finsight path/to/statement.csv --output ./reports
```

> Requires Python 3.10+

## Input Data Schema

| Category | Required Columns |
| --- | --- |
| **Identity** | `period` (e.g., 2023, Q1-2024) |
| **Income Statement** | `revenue`, `gross_profit`, `operating_income`, `net_income`, `cost_of_goods_sold` |
| **Balance Sheet** | `total_assets`, `current_assets`, `inventory`, `cash`, `accounts_receivable`, `total_liabilities`, `current_liabilities`, `equity` |
| **Cash Flow** | `operating_cash_flow`, `interest_expense` |

## Financial Ratios

| Category | Ratios |
| --- | --- |
| **Profitability** | Gross Margin, Operating Margin, Net Margin, ROA, ROE |
| **Liquidity** | Current Ratio, Quick Ratio, Cash Ratio |
| **Leverage** | Debt-to-Equity, Debt-to-Assets, Interest Coverage |
| **Efficiency** | Asset Turnover, Inventory Turnover, Receivables Turnover |

## Example

See [`examples/sample_statement.csv`](examples/sample_statement.csv) for a sample financial statement with 4 periods of data.

```bash
finsight examples/sample_statement.csv --output ./demo-reports
```

This generates:
- `demo-reports/ratios.csv` - All calculated ratios in tabular form
- `demo-reports/dashboard.png` - Visual performance dashboard
- `demo-reports/report.html` - Complete HTML analysis report

## Coming Soon: FinSight Pro Desktop

<p align="center">
  <img src="https://img.shields.io/badge/Status-In_Development-yellow" alt="Status">
</p>

A professional Windows desktop application with:
- Drag-and-drop file import
- Interactive charts with drill-down
- PDF report export with custom branding
- Batch processing of multiple statements
- Industry benchmarking
- Dark/Light themes
- 12+ language support

**[Join the Waitlist](https://finsightpro.com)** to get early access and founding-member pricing.

## Project Structure

```
finsight-pro/
├── src/finsight/       # Python analysis engine (MIT License)
│   ├── cli.py          # Command-line interface
│   ├── io.py           # File ingestion & validation
│   ├── ratios.py       # Financial ratio calculations
│   ├── charts.py       # Dashboard generation
│   └── report.py       # HTML report generation
├── tests/              # Test suite
├── examples/           # Sample data files
├── desktop/            # Commercial desktop application
├── docs/               # Extended documentation
└── .github/            # Templates & CI/CD
```

## Contributing

Contributions to the open-source CLI engine are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

The Python analysis engine (`src/finsight/`) is licensed under the [MIT License](LICENSE).
