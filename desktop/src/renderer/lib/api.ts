import axios from 'axios';
import type { AnalysisResult, AnalysisHistoryItem, UserPreferences, LicenseInfo, ApiResponse } from '../../types';

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
