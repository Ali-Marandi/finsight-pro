import axios from 'axios';
import type { AnalysisResult, AnalysisHistoryItem, UserPreferences, LicenseInfo, ApiResponse, AIConfig, EvidenceReviewResult, DocumentExtractResult, BenchmarkResult, ComplianceReport, ConsolidatedCompany, ConsolidationResult, TSETMCStockData, TSETMCOverview } from '../../types';

let apiClient: ReturnType<typeof axios.create> | null = null;

async function getApiUrl(): Promise<string> {
  if (window.electronAPI) {
    return await window.electronAPI.getApiUrl();
  }
  return 'http://127.0.0.1:8000/api/v1';
}

export async function getApiClient(): Promise<ReturnType<typeof axios.create>> {
  if (!apiClient) {
    const baseUrl = await getApiUrl();
    apiClient = axios.create({
      baseURL: baseUrl,
      timeout: 60000,
      headers: { 'Content-Type': 'application/json' },
    });
  }
  return apiClient;
}

async function buildUploadFormData(filePath: string, mappingOverrides?: Record<string, string | null>): Promise<FormData> {
  let blob: Blob;
  let fileName: string;

  if (window.electronAPI) {
    const fileInfo = await window.electronAPI.readFileBuffer(filePath);
    const buffer = Uint8Array.from(atob(fileInfo.buffer), (c) => c.charCodeAt(0));
    blob = new Blob([buffer], { type: fileInfo.mimeType });
    fileName = fileInfo.name;
  } else {
    const response = await fetch(filePath);
    blob = await response.blob();
    fileName = filePath.split(/[\\/]/).pop() || 'statement.csv';
  }

  const formData = new FormData();
  formData.append('file', blob, fileName);
  if (mappingOverrides) formData.append('mapping_overrides', JSON.stringify(mappingOverrides));
  return formData;
}

export async function inspectEvidence(
  filePath: string,
  mappingOverrides?: Record<string, string | null>,
): Promise<ApiResponse<EvidenceReviewResult>> {
  try {
    const client = await getApiClient();
    const formData = await buildUploadFormData(filePath, mappingOverrides);
    const { data } = await client.post('/evidence/inspect', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return { data };
  } catch (error: any) {
    return { error: { code: 'EVIDENCE_INSPECTION_FAILED', message: error.response?.data?.detail || error.message || 'Evidence inspection failed', details: null } };
  }
}

export async function uploadAndAnalyze(filePath: string): Promise<ApiResponse<AnalysisResult>> {
  if (window.electronAPI) {
    const fileInfo = await window.electronAPI.readFileBuffer(filePath);
    const client = await getApiClient();
    const buffer = Uint8Array.from(atob(fileInfo.buffer), (c) => c.charCodeAt(0));
    const blob = new Blob([buffer], { type: fileInfo.mimeType });
    const formData = new FormData();
    formData.append('file', blob, fileInfo.name);
    const { data } = await client.post('/analysis/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return data;
  } else {
    const client = await getApiClient();
    const response = await fetch(filePath);
    const blob = await response.blob();
    const formData = new FormData();
    const fileName = filePath.split(/[\\/]/).pop() || 'statement.csv';
    formData.append('file', blob, fileName);
    const { data } = await client.post('/analysis/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return data;
  }
}

export async function getAnalysisHistory(page = 1, perPage = 20): Promise<ApiResponse<AnalysisHistoryItem[]>> {
  const client = await getApiClient();
  const { data } = await client.get('/analysis/history', { params: { page, per_page: perPage } });
  return data;
}

export async function getAnalysisById(id: string): Promise<ApiResponse<AnalysisResult>> {
  const client = await getApiClient();
  const { data } = await client.get(`/analysis/${id}`);
  return data;
}

export async function deleteAnalysis(id: string): Promise<ApiResponse<null>> {
  const client = await getApiClient();
  const { data } = await client.delete(`/analysis/${id}`);
  return data;
}

export async function generateReport(analysisId: string, format: 'pdf' | 'xlsx' | 'html'): Promise<Blob> {
  const client = await getApiClient();
  const { data } = await client.post('/reports/generate', { analysis_id: analysisId, format }, {
    responseType: 'blob',
  });
  return data;
}

export async function saveReport(analysisId: string, format: 'pdf' | 'xlsx' | 'html', suggestedName: string): Promise<string | null> {
  const blob = await generateReport(analysisId, format);
  const filePath = await window.electronAPI?.saveFile(`${suggestedName}.${format}`);
  if (!filePath) return null;
  if (window.electronAPI) {
    // Write file via IPC would be ideal, but for now we download via blob URL
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${suggestedName}.${format}`;
    a.click();
    URL.revokeObjectURL(url);
  }
  return filePath;
}

export async function validateLicense(key: string): Promise<ApiResponse<LicenseInfo>> {
  try {
    const client = await getApiClient();
    const { data } = await client.post('/license/validate', { key });
    return data;
  } catch {
    return { error: { code: 'NETWORK_ERROR', message: 'Cannot connect to license server', details: null } };
  }
}

export async function getPreferences(): Promise<ApiResponse<UserPreferences>> {
  try {
    const client = await getApiClient();
    const { data } = await client.get('/settings/preferences');
    return data;
  } catch {
    return { data: { defaultLanguage: 'en', chartTheme: 'light', decimalPlaces: 2, autoSave: true } };
  }
}

export async function updatePreferences(prefs: Partial<UserPreferences>): Promise<ApiResponse<UserPreferences>> {
  const client = await getApiClient();
  const { data } = await client.put('/settings/preferences', prefs);
  return data;
}

export function getLocalApiUrl(): string {
  return 'http://127.0.0.1:8000/api/v1';
}

export async function getAIConfig(): Promise<AIConfig> {
  try {
    const client = await getApiClient();
    const { data } = await client.get('/ai/configure');
    return data;
  } catch {
    return { configured: false, model: '', endpoint: '' };
  }
}

export async function configureAI(apiKey: string, endpoint: string, model: string): Promise<{ status: string; model: string }> {
  const client = await getApiClient();
  const { data } = await client.post('/ai/configure', { api_key: apiKey, api_endpoint: endpoint, model });
  return data;
}

export async function runPrediction(analysisId: string): Promise<any> {
  const client = await getApiClient();
  const { data } = await client.post('/prediction/from-analysis', { analysis_id: analysisId });
  return data;
}

// Document Intelligence
export async function extractFromPDF(file: File | Blob, forceOcr = false): Promise<DocumentExtractResult> {
  const client = await getApiClient();
  const formData = new FormData();
  formData.append('file', file);
  const { data } = await client.post('/document-intelligence/extract-pdf', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    params: { force_ocr: forceOcr },
  });
  return data;
}

export async function extractFromImage(file: File | Blob): Promise<DocumentExtractResult> {
  const client = await getApiClient();
  const formData = new FormData();
  formData.append('file', file);
  const { data } = await client.post('/document-intelligence/extract-image', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return data;
}

export async function extractFromExcel(file: File | Blob): Promise<DocumentExtractResult> {
  const client = await getApiClient();
  const formData = new FormData();
  formData.append('file', file);
  const { data } = await client.post('/document-intelligence/extract-excel', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return data;
}

export async function extractFromText(text: string): Promise<DocumentExtractResult> {
  const client = await getApiClient();
  const { data } = await client.post('/document-intelligence/extract-text', { text });
  return data;
}

// Benchmarking
export async function getIndustries(): Promise<{ industries: { id: string; name_en: string; name_fa: string }[] }> {
  const client = await getApiClient();
  const { data } = await client.get('/benchmarking/industries');
  return data;
}

export async function compareBenchmark(companyName: string, ratios: { ratio_name: string; value: number; unit: string }[], industryId?: string): Promise<BenchmarkResult> {
  const client = await getApiClient();
  const { data } = await client.post('/benchmarking/compare', { company_name: companyName, ratios, industry_id: industryId });
  return data;
}

// Compliance
export async function runComplianceCheck(financialData: Record<string, number>): Promise<ComplianceReport> {
  const client = await getApiClient();
  const { data } = await client.post('/compliance/check', { financial_data: financialData });
  return data;
}

export async function getComplianceStandards(): Promise<{ standards: { code: string; name: string; name_fa: string; check_count: number }[] }> {
  const client = await getApiClient();
  const { data } = await client.get('/compliance/standards');
  return data;
}

// Consolidation
export async function consolidateCompanies(companies: ConsolidatedCompany[]): Promise<ConsolidationResult> {
  const client = await getApiClient();
  const { data } = await client.post('/consolidation/consolidate', { companies });
  return data;
}

// TSETMC
export async function searchTSETMC(query: string): Promise<{ query: string; results: { symbol: string; instrument_id: string; source: string }[] }> {
  const client = await getApiClient();
  const { data } = await client.get('/tsetmc/search', { params: { query } });
  return data;
}

export async function getTSETMCStock(instrumentId: string): Promise<TSETMCStockData> {
  const client = await getApiClient();
  const { data } = await client.get(`/tsetmc/stock/${instrumentId}`);
  return data;
}

export async function getTSETMCOverview(): Promise<TSETMCOverview> {
  const client = await getApiClient();
  const { data } = await client.get('/tsetmc/market-overview');
  return data;
}

export async function getTSETMCPopular(): Promise<{ stocks: { symbol: string; name_en: string; sector: string }[] }> {
  const client = await getApiClient();
  const { data } = await client.get('/tsetmc/popular');
  return data;
}
