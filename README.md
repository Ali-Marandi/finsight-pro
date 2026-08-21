<h1 align="center">FinSight Pro</h1>

<p align="center">
  <b>Professional Financial Statement Analysis</b><br>
  CLI tool (MIT) + Desktop Application (Commercial)
</p>

<p align="center">
  <a href="https://github.com/Ali-Marandi/finsight-pro/stargazers"><img src="https://img.shields.io/github/stars/Ali-Marandi/finsight-pro?style=social" alt="Stars"></a>
  <a href="https://github.com/Ali-Marandi/finsight-pro/blob/main/LICENSE"><img src="https://img.shields.io/github/license/Ali-Marandi/finsight-pro" alt="License"></a>
  <a href="https://github.com/Ali-Marandi/finsight-pro/releases"><img src="https://img.shields.io/github/v/release/Ali-Marandi/finsight-pro" alt="Release"></a>
  <a href="https://pypi.org/project/finsight-pro/"><img src="https://img.shields.io/pypi/v/finsight-pro" alt="PyPI"></a>
  <img src="https://img.shields.io/badge/Platform-Windows-blue" alt="Windows">
</p>

---

FinSight Pro transforms raw financial data from CSV/Excel files into comprehensive analytical reports with 17+ validated ratios, interactive charts, and publication-ready PDF exports.

## Two Editions

| Edition | License | Status |
|---------|---------|--------|
| **CLI** | MIT (Open Source) | Stable |
| **Desktop Pro** | Commercial | Early Access |

## CLI Quick Start

```bash
pip install .
finsight examples/sample_statement.csv --output ./reports
```

> Requires Python 3.10+

## Desktop App

A professional Windows desktop application built with Electron + React + FastAPI:

- **Drag-and-drop** CSV/XLSX import with smart column detection
- **17+ financial ratios** across 4 categories with status indicators
- **Interactive charts** — bar, radar, and trend visualizations
- **PDF & Excel report generation** with professional Cascade design
- **100% offline** — all data processed locally, nothing leaves your machine
- **Multi-language** — English, فارسی, العربية

### Development Setup

```bash
# Frontend
cd desktop
npm install
npm run dev

# Backend API
cd api
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Production Build

```bash
cd desktop
npm run electron:build:win
```

## Financial Ratios

| Category | Ratios |
|----------|--------|
| **Profitability** | Gross Margin, Net Margin, Operating Margin, ROA, ROE |
| **Liquidity** | Current Ratio, Quick Ratio, Cash Ratio, Working Capital |
| **Leverage** | Debt-to-Equity, Debt-to-Assets, Interest Coverage, Equity Multiplier |
| **Efficiency** | Asset Turnover, Inventory Turnover, Receivables Turnover, DSO |

## Project Structure

```
finsight-pro/
├── src/finsight/          # Core CLI analysis engine (MIT)
├── tests/                 # CLI test suite
├── desktop/               # Electron + React desktop app
│   ├── electron/          # Electron main process
│   ├── src/main/          # React entry + routing
│   └── src/renderer/      # UI components, pages, hooks
├── api/                   # FastAPI backend
│   └── app/               # Routers, services, models
├── docs/                  # Architecture, brand, legal
├── landing/               # Validation landing page
├── examples/              # Sample data
└── .github/               # CI/CD & templates
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines. CLI contributions are under MIT; desktop/API contributions require a CLA.

## License

- **CLI** (`src/finsight/`): [MIT License](LICENSE)
- **Desktop & API**: [Commercial License](docs/legal/LICENSE-COMMERCIAL)

---

<p align="center">
  Built with precision by <a href="https://github.com/Ali-Marandi">Ali Marandi</a>
</p>
