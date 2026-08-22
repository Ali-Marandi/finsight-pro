# FinSight Pro — Current-State Audit

## Scope examined

The repository contains an MIT-licensed Python CLI analytics engine, a React + Electron + FastAPI desktop scaffold, and a static marketing landing page. The intended product is an offline desktop tool for importing normalized CSV/XLSX statements, calculating financial ratios, showing dashboards, and generating reports.

## Evidence-based findings

| Area | Current state | Impact | Priority |
|---|---|---|---|
| Core-engine tests | `python3 -m unittest discover -s tests -v` currently fails: test fixtures do not include `cost_of_goods_sold` and `accounts_receivable`, both required by the current schema. | The advertised baseline is not regression-safe. | P0 |
| Desktop distributability | Electron spawns `python`/`python3` and `uvicorn` externally; the package configuration copies API files but does not package a Python runtime or demonstrated dependency environment. | A production installer cannot be assumed to work on a clean end-user system. | P0 |
| Product claims | The marketing page claims PDF export, branding, batch processing, custom ratios, schema auto-detection, API import, and 12+ language/RTL support. These are absent or incomplete in the engine/desktop implementation. | Trust and conversion risk; scope must be aligned. | P0 |
| Import UX | The current UI accepts one dropped file and the engine demands a fixed canonical 16-column schema. There is no column-mapping flow, template download, sample import, detected-sheet selection, or row-level correction screen. | Users’ existing financial exports will often fail before seeing product value. | P0 |
| Export flow | The API creates chart/report files inside a temporary directory, returns their paths, and exits the temporary directory before response use. The desktop UI does not expose report download or export. | The desktop export promise is non-functional. | P0 |
| Globalization | React, FastAPI, Matplotlib, HTML reports, landing page, and ratio labels have English strings embedded in source. Layout uses directional CSS and HTML roots use `lang="en"`; locale, number/currency/date formatting, translation catalogs, language selection, and RTL testing are absent. | The product cannot credibly support international markets yet. | P0 |
| Market data model | Input is a single generic schema and does not model reporting basis, currency, scale, fiscal-year end, entity identity, industry, or taxonomy mappings. | Cross-company and cross-country comparisons could be misleading. | P0 |
| Desktop security | Electron uses `contextIsolation: true` and has Node integration disabled, which is a sound baseline. However no documented CSP, sandboxing policy, navigation/window-open policy, IPC sender validation, dependency security process, or release-signing implementation was found. API CORS allows all origins with credentials. | Security hardening is insufficient for public distribution. | P1 |
| Release engineering | Desktop target is Windows x64 only. No test automation or release verification workflow is present in the repository. Package scripts also reference `npm run lint` in the React project although no `lint` script is defined there. | No repeatable quality gate or global operating-system release path. | P1 |
| Analysis UX | The desktop shows two interactive chart panels and a categorical ratio table. It does not surface data quality insight, explanations, benchmarks, trend interpretation, alerts, reports, or disclosure of metric definitions. | The product behaves as a calculator rather than a decision-support product. | P1 |
| Ratio consistency | The engine computes `cash_flow_margin`, but it is missing from README’s published ratio list and several UI/report groupings. | Documentation and UI cannot be relied on as a complete representation of the engine. | P1 |

## Product implications

FinSight Pro should first become a reliable, transparent, locally useful analysis product before expanding feature claims, countries, or paid tiers. The initial strategic wedge should be **offline, trustworthy financial-statement normalization and explainable ratio analytics for SMB finance teams, accountants, and analysts**. International expansion should be designed around a canonical data model plus regional adapters—not English UI translation on top of a US-style template.

## Research anchors

The external findings and their URLs are recorded in `docs/research_findings.md`. They support the priority of structured reporting data, an i18n-first architecture, Electron security hardening, and signed desktop distribution.
