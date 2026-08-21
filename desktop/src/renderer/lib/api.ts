import axios from 'axios';
import type { AnalysisResult, AnalysisHistoryItem, UserPreferences, LicenseInfo, ApiResponse } from '../types';

let apiClient: ReturnType<typeof axios.create> | null = null;

async function getApiUrl(): Promise<string> {
  if (window.electronAPI) {
    return await window.electronAPI.getApiUrl();
  }
  return 'http://127.0.0.1:8000/api/v1';
}

export async function getApiClient() {
  if (!apiClient) {
    const baseUrl = await getApiUrl();
    apiClient = axios.create({
      baseURL: baseUrl,
      timeout: 30000,
      headers: { 'Content-Type': 'application/json' },
    });
  }
  return apiClient;
}

export async function uploadAndAnalyze(filePath: string): Promise<ApiResponse<AnalysisResult>> {
  const client = await getApiClient();
  const formData = new FormData();
  formData.append('file', {
    uri: filePath,
    name: filePath.split(/[\\/]/).pop() || 'statement.csv',
    type: 'text/csv',
  } as unknown as File);
  const { data } = await client.post('/analysis/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return data;
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
  // Write blob to file via Electron
  return filePath;
}

export async function validateLicense(key: string): Promise<ApiResponse<LicenseInfo>> {
  const client = await getApiClient();
  const { data } = await client.post('/license/validate', { key });
  return data;
}

export async function getPreferences(): Promise<ApiResponse<UserPreferences>> {
  const client = await getApiClient();
  const { data } = await client.get('/settings/preferences');
  return data;
}

export async function updatePreferences(prefs: Partial<UserPreferences>): Promise<ApiResponse<UserPreferences>> {
  const client = await getApiClient();
  const { data } = await client.put('/settings/preferences', prefs);
  return data;
}

export function getLocalApiUrl(): string {
  return 'http://127.0.0.1:8000/api/v1';
}