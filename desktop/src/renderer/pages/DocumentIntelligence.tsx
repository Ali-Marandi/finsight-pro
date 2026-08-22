import { useState, useCallback, type ReactNode } from 'react';
import {
  FileSearch,
  Upload,
  ScanText,
  AlertTriangle,
  CheckCircle2,
  FileText,
  Eye,
  X,
  Sparkles,
  Shield,
} from 'lucide-react';
import {
  extractFromPDF,
  extractFromImage,
  extractFromExcel,
  extractFromText,
} from '../lib/api';
import Spinner from '../components/Spinner';
import type { DocumentExtractResult } from '../../types';

// ──────────────────────────────────────────────
// Types
// ──────────────────────────────────────────────

type TabId = 'upload' | 'text';

interface FileWithType {
  file: File;
  detectedType: 'pdf' | 'image' | 'excel' | 'unknown';
}

// ──────────────────────────────────────────────
// Helpers
// ──────────────────────────────────────────────

const ACCEPTED_EXTENSIONS = new Set([
  'pdf', 'png', 'jpg', 'jpeg', 'tiff', 'tif', 'xlsx', 'xls',
]);

const PDF_EXTS = new Set(['pdf']);
const IMAGE_EXTS = new Set(['png', 'jpg', 'jpeg', 'tiff', 'tif']);
const EXCEL_EXTS = new Set(['xlsx', 'xls']);

function detectFileType(fileName: string): FileWithType['detectedType'] {
  const ext = fileName.split('.').pop()?.toLowerCase() ?? '';
  if (PDF_EXTS.has(ext)) return 'pdf';
  if (IMAGE_EXTS.has(ext)) return 'image';
  if (EXCEL_EXTS.has(ext)) return 'excel';
  return 'unknown';
}

function fileExtension(fileName: string): string {
  return fileName.split('.').pop()?.toUpperCase() ?? '?';
}

function formatNumber(value: number): string {
  const abs = Math.abs(value);
  const decimals = abs >= 1_000_000 ? 0 : abs >= 1_000 ? 1 : 2;
  return new Intl.NumberFormat('en-US', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(value);
}

function confidenceColor(score: number): string {
  if (score > 80) return 'bg-semantic-success';
  if (score > 50) return 'bg-semantic-warning';
  return 'bg-semantic-danger';
}

function confidenceTextColor(score: number): string {
  if (score > 80) return 'text-semantic-success';
  if (score > 50) return 'text-semantic-warning';
  return 'text-semantic-danger';
}

function methodLabel(method: DocumentExtractResult['extraction_method']): string {
  const map: Record<DocumentExtractResult['extraction_method'], string> = {
    native: 'Native PDF',
    ocr: 'OCR',
    structured: 'Structured (Excel)',
    text_parse: 'Text Parse',
    failed: 'Failed',
  };
  return map[method];
}

function methodBadgeClasses(method: DocumentExtractResult['extraction_method']): string {
  if (method === 'failed') return 'bg-semantic-danger/10 text-semantic-danger border-semantic-danger/20';
  if (method === 'ocr') return 'bg-cascade-gold/10 text-cascade-gold border-cascade-gold/20';
  if (method === 'structured') return 'bg-blue-50 text-blue-600 border-blue-200';
  return 'bg-semantic-success/10 text-semantic-success border-semantic-success/20';
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1_048_576) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1_048_576).toFixed(1)} MB`;
}

function formatFieldName(key: string): string {
  return key
    .replace(/_/g, ' ')
    .replace(/([a-z])([A-Z])/g, '$1 $2')
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

// ──────────────────────────────────────────────
// Sub-components
// ──────────────────────────────────────────────

function TabButton({
  id,
  label,
  icon,
  active,
  onClick,
}: {
  id: TabId;
  label: string;
  icon: ReactNode;
  active: boolean;
  onClick: (id: TabId) => void;
}) {
  return (
    <button
      type="button"
      onClick={() => onClick(id)}
      className={`flex items-center gap-2 px-5 py-2.5 rounded-lg text-sm font-medium transition-colors cursor-pointer ${
        active
          ? 'bg-cascade-charcoal text-white'
          : 'bg-cascade-soft-white border border-cascade-mist text-cascade-sage hover:text-cascade-charcoal'
      }`}
    >
      {icon}
      {label}
    </button>
  );
}

function ConfidenceBar({ score }: { score: number }) {
  const clamped = Math.max(0, Math.min(100, Math.round(score)));
  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium text-cascade-sage">Confidence</span>
        <span className={`text-sm font-bold ${confidenceTextColor(score)}`}>{clamped}%</span>
      </div>
      <div className="h-2.5 bg-cascade-mist rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-700 ease-out ${confidenceColor(score)}`}
          style={{ width: `${clamped}%` }}
        />
      </div>
    </div>
  );
}

function EmptyPlaceholder() {
  return (
    <div className="card flex flex-col items-center justify-center py-16 px-8 text-center">
      <div className="w-16 h-16 rounded-2xl bg-cascade-mist flex items-center justify-center mb-4">
        <FileSearch size={28} className="text-cascade-sage" />
      </div>
      <h3 className="text-lg font-semibold text-cascade-charcoal mb-1">No results yet</h3>
      <p className="text-sm text-cascade-sage max-w-sm">
        Upload a financial document or paste text, then click extract to see structured results here.
      </p>
    </div>
  );
}

// ──────────────────────────────────────────────
// Main Component
// ──────────────────────────────────────────────

export default function DocumentIntelligence() {
  // Tab
  const [activeTab, setActiveTab] = useState<TabId>('upload');

  // File upload state
  const [selectedFile, setSelectedFile] = useState<FileWithType | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [forceOcr, setForceOcr] = useState(false);

  // Text input state
  const [inputText, setInputText] = useState('');

  // Result state
  const [result, setResult] = useState<DocumentExtractResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Ref for hidden file input
  const fileInputRef = useState<HTMLInputElement | null>(null)[0];
  const [_fileInputRef, setFileInputRef] = useState<HTMLInputElement | null>(null);

  // ──── File handling ────

  const validateAndSetFile = useCallback((file: File): boolean => {
    const ext = file.name.split('.').pop()?.toLowerCase() ?? '';
    if (!ACCEPTED_EXTENSIONS.has(ext)) {
      setError(`Unsupported file type: .${ext}. Accepted: PDF, PNG, JPG, TIFF, Excel`);
      return false;
    }
    setError(null);
    setSelectedFile({ file, detectedType: detectFileType(file.name) });
    return true;
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent<HTMLDivElement>) => {
      e.preventDefault();
      e.stopPropagation();
      setIsDragging(false);
      const droppedFile = e.dataTransfer.files[0];
      if (droppedFile) validateAndSetFile(droppedFile);
    },
    [validateAndSetFile],
  );

  const handleDragOver = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  }, []);

  const handleFileInput = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) validateAndSetFile(file);
      // Reset so same file can be selected again
      e.target.value = '';
    },
    [validateAndSetFile],
  );

  const handleClearFile = useCallback(() => {
    setSelectedFile(null);
    setError(null);
  }, []);

  // ──── Extraction ────

  const handleUploadExtract = useCallback(async () => {
    if (!selectedFile) return;
    setIsLoading(true);
    setError(null);
    setResult(null);

    try {
      let res: DocumentExtractResult;

      switch (selectedFile.detectedType) {
        case 'pdf':
          res = await extractFromPDF(selectedFile.file, forceOcr);
          break;
        case 'image':
          res = await extractFromImage(selectedFile.file);
          break;
        case 'excel':
          res = await extractFromExcel(selectedFile.file);
          break;
        default:
          throw new Error('Unable to determine extraction method for this file.');
      }

      setResult({ ...res, filename: selectedFile.file.name });
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Extraction failed';
      setError(message);
    } finally {
      setIsLoading(false);
    }
  }, [selectedFile, forceOcr]);

  const handleTextExtract = useCallback(async () => {
    const trimmed = inputText.trim();
    if (!trimmed) return;
    setIsLoading(true);
    setError(null);
    setResult(null);

    try {
      const res = await extractFromText(trimmed);
      setResult({ ...res, filename: undefined });
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Text extraction failed';
      setError(message);
    } finally {
      setIsLoading(false);
    }
  }, [inputText]);

  // ──── Derived data ────

  const extractedEntries = result
    ? Object.entries(result.financial_data).sort((a, b) => a[0].localeCompare(b[0]))
    : [];

  const quality = result?.quality ?? null;

  // ──── Render ────

  return (
    <div className="space-y-6">
      {/* ── Header ── */}
      <div className="page-header">
        <div>
          <h1 className="page-title">Document Intelligence</h1>
          <p className="text-cascade-sage text-sm mt-1">
            Extract structured financial data from PDFs, images, spreadsheets, or raw text
          </p>
        </div>
        {result && (
          <button
            type="button"
            onClick={() => {
              setResult(null);
              setError(null);
              setSelectedFile(null);
              setInputText('');
            }}
            className="btn-secondary flex items-center gap-2 text-sm"
          >
            <Eye size={14} />
            New Extraction
          </button>
        )}
      </div>

      {/* ── Tabs ── */}
      <div className="flex gap-2">
        <TabButton
          id="upload"
          label="File Upload"
          icon={<Upload size={16} />}
          active={activeTab === 'upload'}
          onClick={setActiveTab}
        />
        <TabButton
          id="text"
          label="Text Input"
          icon={<ScanText size={16} />}
          active={activeTab === 'text'}
          onClick={setActiveTab}
        />
      </div>

      {/* ── Upload Tab ── */}
      {activeTab === 'upload' && (
        <div className="card p-6 space-y-4">
          {/* Hidden file input */}
          <input
            ref={setFileInputRef}
            type="file"
            accept=".pdf,.png,.jpg,.jpeg,.tiff,.tif,.xlsx,.xls"
            onChange={handleFileInput}
            className="hidden"
            aria-hidden="true"
          />

          {/* Drop zone */}
          <div
            role="button"
            tabIndex={0}
            onDrop={handleDrop}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onClick={() => _fileInputRef?.click()}
            onKeyDown={(e) => {
              if (e.key === 'Enter' || e.key === ' ') _fileInputRef?.click();
            }}
            className={`relative flex flex-col items-center justify-center py-12 px-6 rounded-xl border-2 border-dashed transition-colors cursor-pointer ${
              isDragging
                ? 'border-cascade-gold bg-cascade-gold/5'
                : selectedFile
                  ? 'border-semantic-success/40 bg-semantic-success/5'
                  : 'border-cascade-mist hover:border-cascade-sage hover:bg-cascade-stone/50'
            }`}
          >
            {selectedFile ? (
              <div className="flex items-center gap-4 text-start">
                <div className="w-12 h-12 rounded-lg bg-semantic-success/10 flex items-center justify-center shrink-0">
                  <FileText size={22} className="text-semantic-success" />
                </div>
                <div className="min-w-0">
                  <p className="text-sm font-semibold text-cascade-charcoal truncate max-w-xs">
                    {selectedFile.file.name}
                  </p>
                  <div className="flex items-center gap-3 mt-0.5">
                    <span className="text-xs text-cascade-sage">
                      {formatFileSize(selectedFile.file.size)}
                    </span>
                    <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-medium bg-cascade-charcoal text-white">
                      {fileExtension(selectedFile.file.name)}
                    </span>
                    <span className="text-xs text-cascade-sage">
                      {methodLabel(
                        selectedFile.detectedType === 'pdf'
                          ? 'native'
                          : selectedFile.detectedType === 'image'
                            ? 'ocr'
                            : 'structured',
                      )}
                    </span>
                  </div>
                </div>
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    handleClearFile();
                  }}
                  className="p-1.5 rounded-lg hover:bg-cascade-mist transition-colors text-cascade-sage hover:text-cascade-charcoal"
                  aria-label="Remove file"
                >
                  <X size={16} />
                </button>
              </div>
            ) : (
              <>
                <div className="w-14 h-14 rounded-2xl bg-cascade-mist flex items-center justify-center mb-3">
                  <Upload size={24} className="text-cascade-sage" />
                </div>
                <p className="text-sm font-medium text-cascade-charcoal mb-1">
                  Drag & drop your file here, or click to browse
                </p>
                <p className="text-xs text-cascade-sage">
                  Supports PDF, PNG, JPG, TIFF, XLSX, XLS
                </p>
              </>
            )}
          </div>

          {/* Force OCR toggle (only for PDFs) */}
          {selectedFile?.detectedType === 'pdf' && (
            <label className="flex items-center gap-3 cursor-pointer select-none">
              <div className="relative">
                <input
                  type="checkbox"
                  checked={forceOcr}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => setForceOcr(e.target.checked)}
                  className="sr-only peer"
                />
                <div className="w-10 h-6 bg-cascade-mist rounded-full peer-checked:bg-cascade-gold transition-colors" />
                <div className="absolute top-0.5 start-0.5 w-5 h-5 bg-white rounded-full shadow-sm transition-transform peer-checked:translate-x-4" />
              </div>
              <div>
                <span className="text-sm font-medium text-cascade-charcoal">Force OCR</span>
                <span className="text-xs text-cascade-sage ms-2">
                  Use OCR even for native PDF text
                </span>
              </div>
            </label>
          )}

          {/* Extract button */}
          <button
            type="button"
            disabled={!selectedFile || isLoading}
            onClick={handleUploadExtract}
            className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg bg-cascade-charcoal text-white text-sm font-medium hover:bg-cascade-olive disabled:opacity-40 disabled:cursor-not-allowed transition-colors cursor-pointer"
          >
            {isLoading ? (
              <>
                <Spinner size={16} className="" />
                Extracting…
              </>
            ) : (
              <>
                <Sparkles size={16} />
                Extract Data
              </>
            )}
          </button>

          {/* Error */}
          {error && !isLoading && (
            <div className="flex items-start gap-2 p-3 rounded-lg bg-semantic-danger/10 text-semantic-danger text-sm">
              <AlertTriangle size={16} className="shrink-0 mt-0.5" />
              <span>{error}</span>
            </div>
          )}
        </div>
      )}

      {/* ── Text Input Tab ── */}
      {activeTab === 'text' && (
        <div className="card p-6 space-y-4">
          <div>
            <label htmlFor="doc-intel-text-input" className="block text-sm font-medium text-cascade-charcoal mb-2">
              Paste Financial Text
            </label>
            <textarea
              id="doc-intel-text-input"
              value={inputText}
              onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setInputText(e.target.value)}
              placeholder={
                'Paste financial statement text here, e.g.:\n' +
                'Total Revenue: 4,520,000\n' +
                'Cost of Goods Sold: 2,180,000\n' +
                'Net Income: 890,000\n' +
                'Total Assets: 12,350,000\n' +
                'Total Liabilities: 6,700,000'
              }
              rows={10}
              className="w-full px-4 py-3 rounded-lg border border-cascade-mist bg-cascade-soft-white text-cascade-charcoal text-sm placeholder:text-cascade-sage/60 focus:outline-none focus:ring-2 focus:ring-cascade-gold/40 focus:border-cascade-gold resize-y min-h-32"
            />
            <p className="text-xs text-cascade-sage mt-1.5">
              {inputText.trim().length > 0
                ? `${inputText.trim().split(/\s+/).length} words · ${inputText.length} characters`
                : 'Supported: income statements, balance sheets, cash flow data'}
            </p>
          </div>

          <button
            type="button"
            disabled={!inputText.trim() || isLoading}
            onClick={handleTextExtract}
            className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg bg-cascade-charcoal text-white text-sm font-medium hover:bg-cascade-olive disabled:opacity-40 disabled:cursor-not-allowed transition-colors cursor-pointer"
          >
            {isLoading ? (
              <>
                <Spinner size={16} className="" />
                Extracting…
              </>
            ) : (
              <>
                <Sparkles size={16} />
                Extract Data
              </>
            )}
          </button>

          {/* Error */}
          {error && !isLoading && (
            <div className="flex items-start gap-2 p-3 rounded-lg bg-semantic-danger/10 text-semantic-danger text-sm">
              <AlertTriangle size={16} className="shrink-0 mt-0.5" />
              <span>{error}</span>
            </div>
          )}
        </div>
      )}

      {/* ── Loading state (full-page overlay) ── */}
      {isLoading && (
        <div className="card p-8 flex flex-col items-center justify-center gap-3">
          <Spinner size={32} />
          <p className="text-sm text-cascade-sage">Processing document…</p>
        </div>
      )}

      {/* ── Results ── */}
      {!isLoading && !result && <EmptyPlaceholder />}

      {!isLoading && result && (
        <div className="space-y-6">
          {/* Result header bar */}
          <div className="card p-5 space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div className="flex items-center gap-3">
                <h2 className="text-base font-semibold text-cascade-charcoal">Extraction Results</h2>
                <span
                  className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold border ${methodBadgeClasses(
                    result.extraction_method,
                  )}`}
                >
                  {methodLabel(result.extraction_method)}
                </span>
              </div>
              {result.filename && (
                <span className="text-xs text-cascade-sage flex items-center gap-1.5">
                  <FileText size={13} />
                  {result.filename}
                </span>
              )}
            </div>

            {/* Confidence bar */}
            <ConfidenceBar score={result.confidence} />

            {/* Summary row */}
            <div className="flex flex-wrap gap-4 text-xs text-cascade-sage">
              <span>
                <span className="font-medium text-cascade-charcoal">{result.fields_found}</span> fields extracted
              </span>
              {result.document_type && (
                <span>
                  Type: <span className="font-medium text-cascade-charcoal">{result.document_type}</span>
                </span>
              )}
            </div>
          </div>

          {/* Quality score card + Critical fields + Warnings */}
          {quality && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* Quality Score */}
              <div className="card p-5 flex flex-col items-center justify-center text-center">
                <Shield size={20} className="text-cascade-sage mb-2" />
                <span className="text-xs text-cascade-sage mb-1">Quality Score</span>
                <span
                  className={`text-3xl font-bold ${
                    quality.quality_score >= 80
                      ? 'text-semantic-success'
                      : quality.quality_score >= 50
                        ? 'text-semantic-warning'
                        : 'text-semantic-danger'
                  }`}
                >
                  {quality.quality_score}<span className="text-lg">%</span>
                </span>
                <span className="text-xs text-cascade-sage mt-1">
                  {quality.completeness}% complete
                </span>
              </div>

              {/* Critical Fields Status */}
              <div className="card p-5 space-y-3">
                <h3 className="text-xs font-semibold text-cascade-sage uppercase tracking-wide">
                  Critical Fields
                </h3>
                <div className="flex items-center gap-2">
                  <CheckCircle2 size={16} className="text-semantic-success" />
                  <span className="text-sm font-medium text-cascade-charcoal">
                    {quality.critical_found} found
                  </span>
                </div>
                {quality.critical_missing.length > 0 ? (
                  <div>
                    <div className="flex items-center gap-2 mb-2">
                      <AlertTriangle size={16} className="text-semantic-warning" />
                      <span className="text-sm font-medium text-cascade-charcoal">
                        {quality.critical_missing.length} missing
                      </span>
                    </div>
                    <div className="flex flex-wrap gap-1.5">
                      {quality.critical_missing.map((field) => (
                        <span
                          key={field}
                          className="inline-flex items-center px-2 py-0.5 rounded-md text-[11px] font-medium bg-semantic-warning/10 text-semantic-warning border border-semantic-warning/20"
                        >
                          {formatFieldName(field)}
                        </span>
                      ))}
                    </div>
                  </div>
                ) : (
                  <div className="flex items-center gap-2">
                    <CheckCircle2 size={16} className="text-semantic-success" />
                    <span className="text-sm text-semantic-success">All critical fields present</span>
                  </div>
                )}
              </div>

              {/* Warnings */}
              <div className="card p-5 space-y-3">
                <h3 className="text-xs font-semibold text-cascade-sage uppercase tracking-wide">
                  Warnings
                </h3>
                {quality.warnings.length > 0 ? (
                  <ul className="space-y-2 max-h-32 overflow-y-auto">
                    {quality.warnings.map((warning, i) => (
                      <li key={i} className="flex items-start gap-2 text-sm text-cascade-charcoal">
                        <AlertTriangle size={14} className="text-semantic-warning shrink-0 mt-0.5" />
                        <span className="leading-snug">{warning}</span>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <div className="flex items-center gap-2 text-sm text-semantic-success">
                    <CheckCircle2 size={16} />
                    <span>No warnings</span>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Extracted Fields Grid */}
          <div className="card p-5 space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-base font-semibold text-cascade-charcoal">Extracted Fields</h2>
              <span className="text-xs text-cascade-sage">
                {extractedEntries.length} field{extractedEntries.length !== 1 ? 's' : ''}
              </span>
            </div>

            {extractedEntries.length === 0 ? (
              <p className="text-sm text-cascade-sage py-4 text-center">
                No structured fields were extracted from this document.
              </p>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 max-h-[28rem] overflow-y-auto">
                {extractedEntries.map(([key, value]) => (
                  <div
                    key={key}
                    className="flex flex-col gap-1 p-3 rounded-lg bg-cascade-stone border border-cascade-mist"
                  >
                    <span className="text-xs text-cascade-sage truncate" title={key}>
                      {formatFieldName(key)}
                    </span>
                    <span className="text-sm font-semibold text-cascade-charcoal tabular-nums">
                      {formatNumber(value)}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Raw text toggle (if available) */}
          {result.raw_text && (
            <details className="card">
              <summary className="p-4 text-sm font-medium text-cascade-charcoal cursor-pointer select-none hover:text-cascade-gold transition-colors">
                View Extracted Raw Text
              </summary>
              <div className="px-4 pb-4">
                <pre className="p-4 rounded-lg bg-cascade-stone text-xs text-cascade-charcoal whitespace-pre-wrap break-words max-h-64 overflow-y-auto font-mono leading-relaxed">
                  {result.raw_text}
                </pre>
              </div>
            </details>
          )}
        </div>
      )}
    </div>
  );
}
