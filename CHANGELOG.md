# Changelog

All notable changes to FinSight Pro will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
