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

// Time Series Analysis
export interface ARIMAResult {
  method: string;
  aic: number | null;
  bic: number | null;
  historical: { dates: string[]; values: number[] };
  forecast: { dates: string[]; values: number[]; lower: number[]; upper: number[] };
  forecast_steps: number;
  error?: string;
}

export interface GARCHResult {
  method: string;
  parameters: { omega: number; alpha: number; beta: number } | null;
  persistence: number | null;
  long_run_volatility: number | null;
  current_annual_volatility: number;
  conditional_volatility: number[];
  forecast_volatility: number[] | null;
  aic: number | null;
  error?: string;
}

export interface DecompositionResult {
  method: string;
  period: number;
  trend: number[];
  seasonal: number[];
  residual: number[];
  observed: number[];
  error?: string;
}

export interface TimeSeriesSummary {
  count: number;
  first: number;
  last: number;
  min: number;
  max: number;
  mean: number;
  std: number;
  total_return_pct: number;
  volatility_annual: number;
  skewness: number;
  kurtosis: number;
}

// Financial Engineering
export interface VaRResult {
  method: string;
  confidence: number;
  position_value: number;
  var_return_pct: number;
  var_absolute: number;
  cvar_return_pct: number;
  cvar_absolute: number;
  interpretation: string;
  error?: string;
}

export interface MonteCarloResult {
  parameters: { s0: number; mu_annual: number; sigma_annual: number; days: number; simulations: number };
  statistics: {
    mean_final_price: number;
    median_final_price: number;
    prob_profit: number;
    prob_loss: number;
    var_95_pct: number;
    expected_return_pct: number;
  };
  percentiles: Record<number, number>;
  sample_paths: number[][];
}

export interface BlackScholesResult {
  option_type: string;
  inputs: { spot: number; strike: number; time: number; rate: number; volatility: number };
  price: number;
  d1: number;
  d2: number;
  greeks: { delta: number; gamma: number; vega: number; theta: number };
  error?: string;
}

// Fuzzy MCDM
export interface FuzzyAHPResult {
  method: string;
  criteria_count: number;
  weights: number[];
  criteria_names: string[];
  ranking: { rank: number; name: string; weight: number; weight_pct: number }[];
  consistency: { lambda_max: number; ci: number; ri: number; cr: number; consistent: boolean };
  is_fuzzy: boolean;
  recommendation: string;
  error?: string;
}

export interface StockRankingResult {
  method: string;
  stocks_analyzed: number;
  criteria_used: string[];
  ahp_weights: number[];
  ahp_ranking: { rank: number; name: string; weight: number; weight_pct: number }[];
  consistency: { lambda_max: number; ci: number; ri: number; cr: number; consistent: boolean };
  topsis_ranking: { rank: number; name: string; closeness: number; d_positive: number; d_negative: number }[];
  best_stock: string;
  best_score: number;
  error?: string;
}

// Black-Litterman
export interface BlackLittermanResult {
  method: string;
  num_assets: number;
  parameters: { risk_aversion: number; tau: number; risk_free_rate: number; num_views: number };
  implied_equilibrium_returns: number[];
  posterior_returns: number[];
  optimal_weights: number[];
  market_weights: number[];
  active_weights: number[];
  portfolio_metrics: {
    expected_return: number;
    volatility: number;
    sharpe_ratio: number;
    tracking_error: number;
    information_ratio: number;
  };
  return_changes: number[];
  error?: string;
}

// Factor Analysis
export interface PCAResult {
  method: string;
  observations: number;
  assets: number;
  components_analyzed: number;
  kaiser_components: number;
  total_explained_variance_pct: number;
  eigenvalues: number[];
  explained_variance_pct: number[];
  cumulative_variance_pct: number[];
  scree_plot_data: { component: number; eigenvalue: number; explained_var_pct: number; cumulative_var_pct: number }[];
  top_loadings: { component: number; explained_var_pct: number; top_assets: { name: string; loading: number }[] }[];
  mean_returns: number[];
  recommendation: string;
  error?: string;
}

export interface FamaFrenchResult {
  method: string;
  observations: number;
  assets: number;
  factor_names: string[];
  factor_statistics: { factor: string; mean_annual_pct: number; volatility_annual_pct: number; sharpe: number }[];
  factor_correlation: number[][];
  asset_loadings: { asset: string; alpha: number; beta_mkt: number; beta_smb: number; beta_hml: number; r_squared: number }[];
  avg_r_squared: number;
  mean_alpha_pct: number;
  recommendation: string;
  error?: string;
}

export interface PortfolioOptResult {
  optimal_weights: number[];
  optimal_return: number;
  optimal_volatility: number;
  sharpe_ratio: number;
  min_var_weights: number[];
  min_var_return: number;
  min_var_volatility: number;
  num_assets: number;
}

// Backtesting
export interface BacktestTrade {
  day: number;
  action: string;
  price: number;
  shares: number;
  pnl: number;
}

export interface BacktestRisk {
  sharpe_ratio: number;
  sortino_ratio: number;
  max_drawdown_pct: number;
  max_drawdown_duration_days: number;
  calmar_ratio: number;
  var_95_pct: number;
  cvar_95_pct: number;
}

export interface BacktestBenchmark {
  total_return_pct: number;
  cagr_pct: number;
  volatility_pct: number;
  sharpe: number;
  alpha_pct: number;
  beta: number;
  tracking_error_pct: number;
  information_ratio: number;
  excess_return_pct: number;
}

export interface SingleBacktestResult {
  strategy_name: string;
  period: { days: number; years: number };
  capital: { initial: number; final: number };
  performance: {
    total_return_pct: number;
    cagr_pct: number;
    annual_volatility_pct: number;
  };
  risk: BacktestRisk;
  trades: {
    total: number;
    buy_count: number;
    sell_count: number;
    win_rate: number;
    profit_factor: number;
    expectancy: number;
    avg_win: number;
    avg_loss: number;
    winning_trades: number;
    losing_trades: number;
  };
  benchmark: BacktestBenchmark | null;
  charts: {
    equity_curve: number[];
    benchmark_curve: number[] | null;
    drawdown_series: number[];
  };
  trade_log: BacktestTrade[];
  error?: string;
}

export interface PortfolioBacktestResult {
  strategy_name: string;
  num_assets: number;
  asset_names: string[];
  period: { days: number; years: number };
  capital: { initial: number; final: number };
  weights: number[];
  rebalance_days: number;
  performance: {
    total_return_pct: number;
    cagr_pct: number;
    annual_volatility_pct: number;
  };
  risk: BacktestRisk;
  assets: { name: string; weight_pct: number; total_return_pct: number; volatility_pct: number }[];
  benchmark: { total_return_pct: number; excess_return_pct: number } | null;
  charts: {
    equity_curve: number[];
    benchmark_curve: number[] | null;
    drawdown_series: number[];
  };
  error?: string;
}

export interface BacktestDemoResult {
  demo_info: {
    description: string;
    assets: string[];
    assets_fa: string[];
    period_days: number;
  };
  single_asset: SingleBacktestResult;
  portfolio: PortfolioBacktestResult;
}
