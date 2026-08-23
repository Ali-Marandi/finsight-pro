# Changelog

All notable changes to FinSight Pro will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.4.0] - 2025-08-23

### Added
- **Document Intelligence Engine** — OCR extraction from PDF, scanned docs & images (Persian + English)
- **Industry Benchmarking Engine** — Compare against 8 industry profiles with percentile rankings
- **Compliance Engine** — 12+ automated checks against IAS, IFRS, and Iran-specific standards
- **Consolidation Engine** — Multi-company financial statement consolidation with eliminations
- **TSETMC Live Market** — Tehran Stock Exchange real-time data integration
- **AI Financial Copilot** — Chat with financial data in English & Persian (built-in + LLM connect)
- **Bankruptcy Prediction** — 5 statistical models (Altman, Springate, Ohlson, Grover) with consensus
- 5 new frontend pages (DocumentIntelligence, Benchmarking, Compliance, Consolidation, TSETMC)
- 5 new API routers and service modules
- Dashboard expanded to 10 feature cards
- Navigation expanded to 12 items
- GitHub Pages landing page
- GitHub Topics (20 SEO-optimized topics)
- Professional README with comparison table and CI badges

### Changed
- Version bumped to 0.4.0
- API version updated to 0.4.0
- Electron main process updated for PDF + image file formats

## [Unreleased]

### Added
- Desktop application scaffold (Electron + React + TypeScript)
- FastAPI backend with financial analysis endpoints
- Validation landing page with waitlist
- GitHub CI/CD workflows

## [1.2.0] - 2024-12-15

### Added
- Debt-to-Equity ratio calculation
- Interest Coverage Ratio
- Export to XLSX format support

### Fixed
- CSV parsing for multi-line headers
- Chart rendering with missing data points

## [1.1.0] - 2024-10-01

### Added
- Quick Ratio and Cash Ratio
- Vertical analysis (common-size statements)
- Color-coded HTML reports

### Changed
- Improved error messages for invalid file formats

## [1.0.0] - 2024-07-20

### Added
- Initial CLI release
- 15 financial ratios (profitability, liquidity, leverage, efficiency)
- CSV and XLSX file input support
- Matplotlib chart generation
- Jinja2 HTML report output
- Basic test suite
