# FinSight Pro API Specification

Base URL (dev): `http://localhost:8000/api/v1`

## Authentication

All Pro and Enterprise endpoints require a valid license key in the header:
```
Authorization: Bearer <license_key>
```

## Endpoints

### Analysis

#### Upload & Analyze
```http
POST /analysis/upload
Content-Type: multipart/form-data

Response 200:
{
  "analysis_id": "uuid",
  "company_name": "Example Corp",
  "period": "2024-Q4",
  "ratios": {
    "profitability": {
      "gross_profit_margin": 0.42,
      "net_profit_margin": 0.18,
      "return_on_assets": 0.12,
      "return_on_equity": 0.24
    },
    "liquidity": {
      "current_ratio": 2.1,
      "quick_ratio": 1.8,
      "cash_ratio": 0.9
    },
    "leverage": {
      "debt_to_equity": 0.65,
      "debt_to_assets": 0.39,
      "interest_coverage": 8.2
    },
    "efficiency": {
      "asset_turnover": 0.95,
      "inventory_turnover": 5.3,
      "receivables_turnover": 8.1
    }
  },
  "charts": {
    "profitability_bar": "base64_png",
    "liquidity_radar": "base64_png"
  }
}
```

#### Get Analysis History
```http
GET /analysis/history?page=1&per_page=20
```

### Reports

#### Generate PDF Report
```http
POST /reports/generate
Content-Type: application/json

{
  "analysis_id": "uuid",
  "template": "professional",
  "language": "en",
  "include_charts": true
}

Response: PDF file download
```

#### Export to Excel
```http
POST /reports/export/xlsx
Content-Type: application/json

{
  "analysis_id": "uuid",
  "include_raw_data": true
}

Response: XLSX file download
```

### License

#### Validate License
```http
POST /license/validate
Content-Type: application/json

{
  "key": "XXXX-XXXX-XXXX-XXXX",
  "machine_id": "hardware_fingerprint"
}

Response 200:
{
  "valid": true,
  "tier": "pro",
  "expires_at": "2025-12-31",
  "features": ["all_ratios", "pdf_reports", "xlsx_export", "batch_processing"]
}
```

### Settings

#### Get User Preferences
```http
GET /settings/preferences
```

#### Update Preferences
```http
PUT /settings/preferences
Content-Type: application/json

{
  "default_language": "en",
  "chart_theme": "light",
  "decimal_places": 2,
  "auto_save": true
}
```

## Error Format

```json
{
  "error": {
    "code": "INVALID_FILE_FORMAT",
    "message": "Unsupported file format. Please upload CSV or XLSX.",
    "details": null
  }
}
```

## Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request |
| 401 | Invalid or expired license |
| 403 | Feature not available in your tier |
| 422 | Validation error |
| 500 | Internal server error |
