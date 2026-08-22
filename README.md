<h1 align="center">
  <img src="https://raw.githubusercontent.com/Ali-Marandi/finsight-pro/main/.github/assets/banner.png" alt="FinSight Pro" width="600">
</h1>

<p align="center">
  <b>Professional Financial Statement Analysis</b><br>
  CLI (MIT) · Desktop App (Commercial)
</p>

<p align="center">
  <a href="https://github.com/Ali-Marandi/finsight-pro/stargazers"><img src="https://img.shields.io/github/stars/Ali-Marandi/finsight-pro?style=social" alt="Stars"></a>
  <a href="https://github.com/Ali-Marandi/finsight-pro/releases/latest"><img src="https://img.shields.io/github/v/release/Ali-Marandi/finsight-pro" alt="Latest Release"></a>
  <a href="https://github.com/Ali-Marandi/finsight-pro/blob/main/LICENSE"><img src="https://img.shields.io/github/license/Ali-Marandi/finsight-pro" alt="License"></a>
  <img src="https://img.shields.io/badge/Platform-Windows-0078D6?logo=windows" alt="Windows">
  <img src="https://img.shields.io/badge/Electron-32-47848F?logo=electron" alt="Electron">
  <img src="https://img.shields.io/badge/React-18-61DAFB?logo=react" alt="React">
</p>

---

FinSight Pro transforms raw financial data from CSV/Excel files into comprehensive analytical reports with **17+ validated ratios**, interactive charts, and publication-ready PDF/Excel exports.

## Download

| Format | Link |
|--------|------|
| **NSIS Installer** (.exe) | [Latest Release](https://github.com/Ali-Marandi/finsight-pro/releases/latest) |
| **Portable** (.exe, no install) | [Latest Release](https://github.com/Ali-Marandi/finsight-pro/releases/latest) |
| **CLI** (pip) | `pip install finsight-pro` |

## Two Editions

| | CLI | Desktop Pro |
|--|-----|-------------|
| **License** | MIT (Open Source) | Commercial |
| **Status** | Stable (109+ stars) | Early Access Beta |
| **UI** | Terminal | Modern GUI |
| **Charts** | Static PNG | Interactive (Bar + Radar) |
| **Export** | PDF | PDF + Excel |
| **Platform** | Any (Python 3.10+) | Windows 10/11 |
| **Data** | Local | Local (offline) |

## Desktop App Screenshots

The desktop app features a professional Cascade design system with:

- **Dashboard** with quick-upload and recent analyses
- **Analysis Page** with interactive charts and status-colored ratio cards
- **Reports Page** with one-click PDF/Excel export
- **History** with category-level health scores
- **Settings** with license activation, appearance, and multi-language (EN/FA/AR)

```
┌──────────────────────────────────────────────┐
│  F FinSight Pro          [PRO] [●API] [v]  │
├──────┬───────────────────────────────────────┤
│  ▣   │  Dashboard                            │
│  ▤   │  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐      │
│  ■   │  │  3  │ │ 17  │ │  3  │ │<2s  │      │
│  ◉   │  │Anlys│ │Ratios│ │Xprt │ │Time │      │
│  ⚙   │  └─────┘ └─────┘ └─────┘ └─────┘      │
│      │                                       │
│      │  ┌─ Quick Analysis ─────────────────┐  │
│      │  │                                │  │
│      │  │   ┌──────────────────────┐      │  │
│      │  │   │  Drop CSV/XLSX here │      │  │
│      │  │   └──────────────────────┘      │  │
│      │  └────────────────────────────────┘  │
└──────┴───────────────────────────────────────┘
```

## Financial Ratios (17+)

| Category | Ratios | Status Classification |
|----------|--------|----------------------|
| **Profitability** | Gross Margin, Net Margin, Operating Margin, ROA, ROE | Good / Warning / Critical |
| **Liquidity** | Current Ratio, Quick Ratio, Cash Ratio, Working Capital | Compared to industry norms |
| **Leverage** | Debt-to-Equity, Debt-to-Assets, Interest Coverage, Equity Multiplier | Risk-level color coding |
| **Efficiency** | Asset Turnover, Inventory Turnover, Receivables Turnover, DSO | Benchmark thresholds |

## Development

```bash
# 1. Clone

# 2. Frontend (Electron + React)
cd desktop
npm install
npm run dev              # Vite dev server on :5173
npm run electron:dev     # Full Electron dev mode

# 3. Backend API (FastAPI)
cd api
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# 4. Production Build
cd desktop
npm run electron:build:win
```

### Project Structure

```
finsight-pro/
├── src/finsight/              # Core CLI analysis engine (MIT)
├── desktop/                  # Electron + React desktop app
│   ├── electron/             #   Main process + preload
│   ├── src/main/             #   React entry + HashRouter
│   ├── src/renderer/         #   Components, pages, hooks, styles
│   │   ├── components/       #     Layout, Titlebar, Header, Toast,
│   │   │                    #     FileUpload, RatioCard, RatioChart, Spinner
│   │   ├── pages/            #     Dashboard, Analysis, Reports, History, Settings
│   │   ├── hooks/            #     useAnalysisStore (Zustand), useLicense
│   │   ├── lib/              #     api.ts (Axios), utils.ts
│   │   └── styles/           #     Tailwind + Cascade design tokens
│   ├── build/                #   NSIS custom installer script
│   └── electron-builder.yml  #   Build config (NSIS + Portable)
├── api/                      # FastAPI backend
│   └── app/
│       ├── routers/          #   analysis, reports, license, settings
│       ├── services/         #   analyzer (17 ratios), report_generator (PDF)
│       ├── models/           #   SQLAlchemy ORM, Pydantic schemas
│       └── middleware/       #   License validation
├── docs/                     # Architecture, API spec, DB schema, brand, legal
├── landing/                  # Validation landing page (HTML)
├── examples/                 # Sample CSV data
├── tests/                    # CLI test suite
└── .github/workflows/        # CI (lint, typecheck, build) + Release (Windows NSIS)
```

## CI/CD

| Workflow | Trigger | What it does |
|----------|---------|-------------|
| **CI** | Push to main/develop, PRs | Python tests, API health check, TypeScript check, build smoke test, ruff lint |
| **Release** | Push tag `v*` | Build Windows NSIS installer + Portable EXE on `windows-latest`, publish to GitHub Releases |

### Creating a Release

```bash
git tag v0.2.0
git push origin v0.2.0
```

GitHub Actions will automatically:
1. Build on Windows runner (real NSIS installer)
2. Create both `.exe` installer and portable
3. Publish to GitHub Releases with auto-generated notes

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Desktop Shell** | Electron 32 (Chromium, Node.js) |
| **UI Framework** | React 18.3 + TypeScript 5.5 |
| **Styling** | Tailwind CSS 3.4 + Custom Cascade palette |
| **State** | Zustand 4.5 |
| **Charts** | Recharts 2.15 (Bar, Radar) |
| **Icons** | Lucide React |
| **UI Primitives** | Radix UI (Dialog, Select, Tabs, Toast, Tooltip) |
| **HTTP** | Axios |
| **File Upload** | react-dropzone + Electron native dialog |
| **Backend** | FastAPI 0.115 + Uvicorn |
| **Database** | SQLAlchemy 2.0 + SQLite |
| **PDF Generation** | ReportLab |
| **Data Processing** | pandas, openpyxl |
| **Build** | Vite 5.4 + electron-builder 25 |

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). CLI contributions are under MIT; desktop/API contributions require a CLA.

## License

- **CLI** (`src/finsight/`): [MIT License](LICENSE)
- **Desktop & API**: [Commercial License](docs/legal/LICENSE-COMMERCIAL)

---

<p align="center">
  Built with precision by <a href="https://github.com/Ali-Marandi">Ali Marandi</a>
</p>
