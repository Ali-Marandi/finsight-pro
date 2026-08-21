import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import Dashboard from './components/Dashboard';
import RatioTable from './components/RatioTable';
import './styles/global.css';

declare global {
  interface Window {
    electronAPI?: {
      openFile: () => Promise<string | null>;
      saveFile: (options: { defaultName: string; filters: Array<{ name: string; extensions: string[] }> }) => Promise<string | null>;
      getApiUrl: () => Promise<string>;
      getAppVersion: () => Promise<string>;
    };
  }
}

interface RatioRow {
  [key: string]: string | number | null;
}

interface AnalysisResult {
  periods: string[];
  ratios: RatioRow[];
  labels: Record<string, string>;
}

function App() {
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fileName, setFileName] = useState<string>('');

  const analyzeFile = useCallback(async (filePath: string) => {
    setLoading(true);
    setError(null);

    try {
      const formData = new FormData();
      const response = await fetch('http://127.0.0.1:8400/analyze', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Analysis failed');
      }

      const data: AnalysisResult = await response.json();
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error occurred');
    } finally {
      setLoading(false);
    }
  }, []);

  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      const file = acceptedFiles[0];
      setFileName(file.name);
      // In Electron, we pass the file path to the API
      // For dev, we simulate with file upload
      const formData = new FormData();
      formData.append('file', file);
      setLoading(true);
      setError(null);
      fetch('http://127.0.0.1:8400/analyze', {
        method: 'POST',
        body: formData,
      })
        .then(res => {
          if (!res.ok) return res.json().then(d => { throw new Error(d.detail || 'Analysis failed'); });
          return res.json();
        })
        .then((data: AnalysisResult) => setResult(data))
        .catch(err => setError(err.message))
        .finally(() => setLoading(false));
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'text/csv': ['.csv'], 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'], 'application/vnd.ms-excel.sheet.macroEnabled.12': ['.xlsm'] },
    maxFiles: 1,
  });

  return (
    <div className="app">
      <header className="app-header">
        <div className="logo">FinSight <span>Pro</span></div>
        <div className="header-actions">
          {result && (
            <button className="btn btn-secondary" onClick={() => { setResult(null); setFileName(''); }}>
              New Analysis
            </button>
          )}
        </div>
      </header>

      <main className="app-main">
        {!result && !loading && (
          <div className="upload-zone-wrapper">
            <div {...getRootProps()} className={`upload-zone ${isDragActive ? 'active' : ''}`}>
              <input {...getInputProps()} />
              <div className="upload-icon">+</div>
              <h2>Drop your financial statement here</h2>
              <p>or click to browse. Supports CSV, XLSX, XLSM</p>
              <div className="upload-hint">
                Required columns: period, revenue, gross_profit, operating_income, net_income,<br />
                total_assets, current_assets, inventory, cash, total_liabilities,<br />
                current_liabilities, equity, operating_cash_flow, interest_expense, cost_of_goods_sold, accounts_receivable
              </div>
            </div>
          </div>
        )}

        {loading && (
          <div className="loading-screen">
            <div className="spinner" />
            <p>Analyzing {fileName}...</p>
          </div>
        )}

        {error && (
          <div className="error-banner">
            <strong>Error:</strong> {error}
            <button onClick={() => setError(null)}>Dismiss</button>
          </div>
        )}

        {result && !loading && (
          <div className="results-container">
            <div className="results-header">
              <h2>Analysis Results: {fileName}</h2>
              <span className="period-count">{result.periods.length} period(s)</span>
            </div>
            <Dashboard periods={result.periods} ratios={result.ratios} labels={result.labels} />
            <RatioTable periods={result.periods} ratios={result.ratios} labels={result.labels} />
          </div>
        )}
      </main>
    </div>
  );
}

export default App;