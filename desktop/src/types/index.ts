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
