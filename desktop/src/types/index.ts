export interface RatioResult {
  category: 'profitability' | 'liquidity' | 'leverage' | 'efficiency';
  ratioName: string;
  value: number;
  unit: string;
  benchmark: number | null;
  status: 'good' | 'warning' | 'critical';
}

export interface AnalysisResult {
  analysisId: string;
  companyName: string;
  period: string;
  fileName: string;
  createdAt: string;
  ratios: RatioResult[];
}

export interface AnalysisHistoryItem {
  analysisId: string;
  companyName: string;
  period: string;
  fileName: string;
  createdAt: string;
  summary: {
    profitability: number;
    liquidity: number;
    leverage: number;
    efficiency: number;
  };
}

export interface UserPreferences {
  defaultLanguage: 'en' | 'fa' | 'ar';
  chartTheme: 'light' | 'dark';
  decimalPlaces: number;
  autoSave: boolean;
}

export interface LicenseInfo {
  valid: boolean;
  tier: 'free' | 'pro' | 'enterprise';
  expiresAt: string | null;
  features: string[];
}

export interface ApiResponse<T> {
  data?: T;
  error?: {
    code: string;
    message: string;
    details: string | null;
  };
}

export interface AIConfig {
  configured: boolean;
  model: string;
  endpoint: string;
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  sources?: string[];
  modelUsed?: string;
}

export type EvidenceSeverity = 'info' | 'warning' | 'blocking';
export type EvidenceMappingStatus = 'confirmed' | 'suggested' | 'needs_review';

export interface EvidenceMapping {
  source_column: string;
  concept_id: string | null;
  confidence: number;
  rationale: string;
  status: EvidenceMappingStatus;
}

export interface EvidenceLocation {
  file_name: string;
  sheet_name: string;
  column_name: string;
  row_number: number | null;
  page_number: number | null;
  table_index: number | null;
  cell_reference: string | null;
}

export interface EvidenceIssue {
  rule_id: string;
  severity: EvidenceSeverity;
  status: 'pass' | 'fail' | 'not_applicable';
  message: string;
  remediation: string;
  evidence_locations?: EvidenceLocation[];
}

export interface EvidenceManifest {
  file_name: string;
  file_hash: string;
  source_type: string;
  sheet_name: string;
  imported_at: string;
  detected_locale: string | null;
  row_count: number;
  column_count: number;
}

export interface EvidenceReviewResult {
  kind: 'financial_statement';
  manifest: EvidenceManifest;
  mappings: EvidenceMapping[];
  health: Record<EvidenceSeverity, number>;
  ready_for_analysis: boolean;
  issues: EvidenceIssue[];
}

// Document Intelligence
export interface DocumentExtractResult {
  financial_data: Record<string, number>;
  extraction_method: 'native' | 'ocr' | 'structured' | 'text_parse' | 'failed';
  confidence: number;
  fields_found: number;
  raw_text?: string;
  filename?: string;
  document_type?: string;
  quality?: {
    completeness: number;
    fields_found: number;
    critical_found: number;
    critical_missing: string[];
    warnings: string[];
    quality_score: number;
  };
}

// Benchmarking
export interface BenchmarkComparison {
  ratio_name: string;
  company_value: number;
  industry_median: number | null;
  industry_p25: number | null;
  industry_p75: number | null;
  percentile: number | null;
  rank: 'excellent' | 'above_average' | 'below_average' | 'poor' | 'no_benchmark';
  deviation_pct: number | null;
}

export interface BenchmarkResult {
  industry_id: string;
  industry_name_en: string;
  industry_name_fa: string;
  overall_percentile: number;
  overall_rank: string;
  comparisons: BenchmarkComparison[];
  ratios_benchmarked: number;
  ratios_total: number;
  recommendations: string[];
}

// Compliance
export interface ComplianceCheckResult {
  standard: string;
  standard_fa: string;
  check_id: string;
  rule: string;
  rule_fa: string;
  severity: 'blocking' | 'warning' | 'info';
  status: 'pass' | 'fail' | 'not_applicable';
  message: string;
  remediation?: string;
}

export interface ComplianceReport {
  compliance_score: number;
  total_checks: number;
  passed: number;
  failed: number;
  not_applicable: number;
  critical_issues: string[];
  warnings: string[];
  info_items: string[];
  status: 'compliant' | 'needs_attention' | 'non_compliant';
  results: ComplianceCheckResult[];
  recommendations: { priority: string; title: string; title_fa: string; description: string }[];
}

// Consolidation
export interface ConsolidatedCompany {
  company_name: string;
  ownership_pct: number;
  financial_data: Record<string, number>;
}

export interface ConsolidationResult {
  consolidated_financials: Record<string, number>;
  eliminations: Record<string, number>;
  ratios: RatioResult[];
  contributions: {
    company_name: string;
    revenue: number;
    net_income: number;
    ownership_pct: number;
    revenue_contribution: number;
  }[];
  company_count: number;
}

// TSETMC
export interface TSETMCStock {
  symbol: string;
  instrument_id: string;
  source: string;
}

export interface TSETMCStockData {
  instrument_id: string;
  available: boolean;
  data: {
    name?: string;
    last_price?: number;
    closing_price?: number;
    open_price?: number;
    high_price?: number;
    low_price?: number;
    volume?: number;
    value?: number;
    market_cap?: number;
    yesterday_price?: number;
    shares_outstanding?: number;
    eps?: number;
    pe_ratio?: number;
    sector?: string;
    change_pct?: number;
    change_value?: number;
    status?: string;
  } | null;
  error: string | null;
}

export interface TSETMCOverview {
  indices: { name: string; value: number; change: number }[];
  popular_stocks: { symbol: string; name_en: string; sector: string }[];
  status: string;
  error: string | null;
}

export interface TaxAuditFact {
  concept_id: string;
  value: number;
  period: string;
  currency: string | null;
  scale: string | null;
  locations: EvidenceLocation[];
}

export interface TaxAuditEvidenceResult {
  kind: 'tax_audit_pdf';
  manifest: EvidenceManifest;
  extraction_mode: string;
  ready_for_review: boolean;
  facts: TaxAuditFact[];
  issues: EvidenceIssue[];
}

export type EvidenceInspectionResult = EvidenceReviewResult | TaxAuditEvidenceResult;
