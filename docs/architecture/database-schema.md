# Database Schema (SQLite)

## Entity Relationship Diagram

```
┌──────────────┐       ┌──────────────────┐       ┌───────────────┐
│   analyses   │       │  ratio_results   │       │   reports     │
├──────────────┤       ├──────────────────┤       ├───────────────┤
│ id (PK)      │──┐    │ id (PK)          │       │ id (PK)       │
│ company_name │  └───>│ analysis_id (FK) │       │ analysis_id   │
│ period       │       │ category         │       │ format        │
│ file_name    │       │ ratio_name       │       │ file_path     │
│ file_hash    │       │ value            │       │ created_at    │
│ created_at   │       │ benchmark        │       │ size_bytes    │
│ updated_at   │       │ status           │       └───────────────┘
└──────────────┘       └──────────────────┘
                              │
┌──────────────┐              │
│  settings    │              │
├──────────────┤       ┌──────┴───────────┐
│ key (PK)     │       │ benchmark_data   │
│ value (JSON) │       ├──────────────────┤
│ updated_at   │       │ id (PK)          │
└──────────────┘       │ industry         │
                       │ ratio_name       │
┌──────────────┐       │ percentile_25    │
│  licenses    │       │ percentile_50    │
├──────────────┤       │ percentile_75    │
│ id (PK)      │       │ source           │
│ license_key  │       │ year             │
│ tier         │       └──────────────────┘
│ machine_id   │
│ activated_at │
│ expires_at   │
│ is_active    │
└──────────────┘
```

## Table Definitions

### analyses
Stores each uploaded financial statement analysis session.

| Column | Type | Description |
|--------|------|-------------|
| id | TEXT (UUID) | Primary key |
| company_name | TEXT | Extracted or user-entered company name |
| period | TEXT | Financial period (e.g. "2024-Q4") |
| file_name | TEXT | Original uploaded filename |
| file_hash | TEXT | SHA-256 hash for duplicate detection |
| notes | TEXT | User notes |
| created_at | DATETIME | Timestamp |
| updated_at | DATETIME | Last modified timestamp |

### ratio_results
Individual ratio calculations for each analysis.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Auto-increment PK |
| analysis_id | TEXT (UUID) | FK to analyses.id |
| category | TEXT | profitability, liquidity, leverage, efficiency |
| ratio_name | TEXT | e.g. "current_ratio" |
| value | REAL | Calculated value |
| benchmark | REAL | Industry benchmark (optional) |
| status | TEXT | good, warning, critical |

### reports
Generated report history.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Auto-increment PK |
| analysis_id | TEXT (UUID) | FK to analyses.id |
| format | TEXT | pdf, xlsx, html |
| file_path | TEXT | Local file path |
| created_at | DATETIME | Timestamp |
| size_bytes | INTEGER | File size |

### settings
Key-value store for user preferences.

| Column | Type | Description |
|--------|------|-------------|
| key | TEXT | Primary key |
| value | TEXT | JSON-encoded value |
| updated_at | DATETIME | Last modified |

### licenses
Local license cache for offline validation.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Auto-increment PK |
| license_key | TEXT | Encrypted license key |
| tier | TEXT | free, pro, enterprise |
| machine_id | TEXT | Hardware fingerprint |
| activated_at | DATETIME | First activation |
| expires_at | DATETIME | Expiration date |
| is_active | BOOLEAN | Whether currently valid |

### benchmark_data
Industry benchmark ratios for comparison.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Auto-increment PK |
| industry | TEXT | Industry classification |
| ratio_name | TEXT | Ratio identifier |
| percentile_25 | REAL | 25th percentile value |
| percentile_50 | REAL | Median value |
| percentile_75 | REAL | 75th percentile value |
| source | TEXT | Data source reference |
| year | INTEGER | Benchmark year |