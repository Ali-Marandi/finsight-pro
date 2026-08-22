import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { useAnalysisStore } from '../hooks/useAnalysisStore';
import FileUpload from '../components/FileUpload';
import EvidenceReview from '../components/EvidenceReview';
import TaxAuditEvidenceReview from '../components/TaxAuditEvidenceReview';
import RatioCard from '../components/RatioCard';
import RatioChart from '../components/RatioChart';
import Spinner from '../components/Spinner';
import { Download, FileText } from 'lucide-react';
import { uploadAndAnalyze, inspectEvidence, getAnalysisById, saveReport } from '../lib/api';
import { useToast } from '../components/Toast';
import type { AnalysisResult, AnalysisHistoryItem, EvidenceInspectionResult } from '../../types';

export default function Analysis() {
  const { id } = useParams();
  const { currentAnalysis, setCurrentAnalysis, isLoading, setIsLoading } = useAnalysisStore();
  const [activeCategory, setActiveCategory] = useState<string>('all');
  const [evidence, setEvidence] = useState<EvidenceInspectionResult | null>(null);
  const [selectedFilePath, setSelectedFilePath] = useState<string | null>(null);
  const [isReviewingEvidence, setIsReviewingEvidence] = useState(false);
  const { toast } = useToast();

  // Load analysis by ID if navigating from history
  useEffect(() => {
    if (id && id !== 'undefined') {
      loadAnalysis(id);
    }
  }, [id]);

  const loadAnalysis = async (analysisId: string) => {
    setIsLoading(true);
    try {
      const res = await getAnalysisById(analysisId);
      if (res.data) setCurrentAnalysis(res.data);
    } catch {
      toast('warning', 'Could not load analysis from server. Showing cached data.');
    } finally {
      setIsLoading(false);
    }
  };

  const runAnalysis = async (filePath: string) => {
    setIsLoading(true);
    try {
      const result = await uploadAndAnalyze(filePath);
      if (result.data) {
        setCurrentAnalysis(result.data);
        setEvidence(null);
        const historyItem: AnalysisHistoryItem = {
          analysisId: result.data.analysisId,
          companyName: result.data.companyName,
          period: result.data.period,
          fileName: result.data.fileName,
          createdAt: result.data.createdAt,
          summary: computeSummary(result.data.ratios),
        };
        const { analyses: current } = useAnalysisStore.getState();
        useAnalysisStore.getState().setAnalyses([historyItem, ...current]);
        toast('success', `Analysis complete: ${result.data.companyName}`);
      } else if (result.error) {
        toast('error', result.error.message);
      }
    } catch (err: any) {
      toast('error', `Analysis failed: ${err.message || 'Unknown error'}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleFileSelected = async (filePath: string) => {
    setIsLoading(true);
    try {
      const result = await inspectEvidence(filePath);
      if (result.data) {
        setSelectedFilePath(filePath);
        setEvidence(result.data);
      } else if (result.error) {
        toast('error', result.error.message);
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleConfirmMappings = async (overrides: Record<string, string | null>) => {
    if (!selectedFilePath || evidence?.kind !== 'financial_statement') return;
    setIsReviewingEvidence(true);
    const result = await inspectEvidence(selectedFilePath, overrides);
    if (result.data) {
      setEvidence(result.data);
    } else if (result.error) {
      toast('error', result.error.message);
    }
    setIsReviewingEvidence(false);
  };

  const resetEvidence = () => {
    setEvidence(null);
    setSelectedFilePath(null);
  };

  const handleExport = async (format: 'pdf' | 'xlsx' | 'html') => {
    if (!currentAnalysis) return;
    try {
      const name = `${currentAnalysis.companyName.replace(/\s+/g, '_')}_${currentAnalysis.period}`;
      const path = await saveReport(currentAnalysis.analysisId, format, name);
      if (path) {
        toast('success', `Report saved to ${path}`);
      }
    } catch {
      toast('error', 'Failed to generate report');
    }
  };

  const categories = currentAnalysis
    ? ['all', ...new Set(currentAnalysis.ratios.map((r) => r.category))]
    : ['all'];

  const filteredRatios = currentAnalysis
    ? activeCategory === 'all'
      ? currentAnalysis.ratios
      : currentAnalysis.ratios.filter((r) => r.category === activeCategory)
    : [];

  // Category score computation
  const categoryScores = currentAnalysis
    ? computeCategoryScores(currentAnalysis.ratios)
    : null;

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-24">
        <Spinner size={32} />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="page-header">
        <div>
          <h1 className="page-title">
            {currentAnalysis ? 'Analysis Details' : 'New Analysis'}
          </h1>
          <p className="text-cascade-sage text-sm mt-1">
            {currentAnalysis
              ? `${currentAnalysis.companyName} — ${currentAnalysis.period}`
              : 'Upload a financial statement to begin analysis'}
          </p>
        </div>
        {currentAnalysis && (
          <div className="flex gap-2">
            <button onClick={() => handleExport('pdf')} className="btn-secondary flex items-center gap-2">
              <Download size={16} /> PDF
            </button>
            <button onClick={() => handleExport('xlsx')} className="btn-secondary flex items-center gap-2">
              <FileText size={16} /> XLSX
            </button>
          </div>
        )}
      </div>

      {!currentAnalysis ? (
        evidence ? (
          evidence.kind === 'tax_audit_pdf' ? (
            <TaxAuditEvidenceReview
              evidence={evidence}
              onContinue={() => selectedFilePath && runAnalysis(selectedFilePath)}
              onStartOver={resetEvidence}
            />
          ) : (
            <EvidenceReview
              evidence={evidence}
              isRefreshing={isReviewingEvidence}
              onConfirmMappings={handleConfirmMappings}
              onContinue={() => selectedFilePath && runAnalysis(selectedFilePath)}
              onStartOver={resetEvidence}
            />
          )
        ) : (
          <div className="max-w-2xl mx-auto">
            <FileUpload onFileSelected={handleFileSelected} isLoading={isLoading} />
          </div>
        )
      ) : (
        <>
          {/* Score Overview */}
          {categoryScores && (
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
              {Object.entries(categoryScores).map(([cat, score]) => (
                <div key={cat} className="card py-3 px-4">
                  <p className="text-xs text-cascade-sage capitalize mb-1">{cat}</p>
                  <div className="flex items-end gap-2">
                    <span className={`text-xl font-bold ${score >= 70 ? 'text-semantic-success' : score >= 50 ? 'text-semantic-warning' : 'text-semantic-danger'}`}>
                      {score}%
                    </span>
                    <div className="flex-1 h-1.5 bg-cascade-mist rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full transition-all duration-500 ${
                          score >= 70 ? 'bg-semantic-success' : score >= 50 ? 'bg-semantic-warning' : 'bg-semantic-danger'
                        }`}
                        style={{ width: `${score}%` }}
                      />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Category Filter */}
          <div className="flex gap-2 flex-wrap">
            {categories.map((cat) => (
              <button
                key={cat}
                onClick={() => setActiveCategory(cat)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  activeCategory === cat
                    ? 'bg-cascade-charcoal text-white'
                    : 'bg-cascade-soft-white border border-cascade-mist text-cascade-sage hover:text-cascade-charcoal'
                }`}
              >
                {cat.charAt(0).toUpperCase() + cat.slice(1)}
              </button>
            ))}
          </div>

          {/* Chart */}
          {filteredRatios.length > 0 && (
            <RatioChart ratios={filteredRatios} title={`${activeCategory === 'all' ? 'All' : activeCategory.charAt(0).toUpperCase() + activeCategory.slice(1)} Ratios`} />
          )}

          {/* Ratio Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {filteredRatios.map((ratio, index) => (
              <RatioCard key={`${ratio.category}-${ratio.ratioName}-${index}`} ratio={ratio} />
            ))}
          </div>
        </>
      )}
    </div>
  );
}

function computeSummary(ratios: AnalysisResult['ratios']): AnalysisHistoryItem['summary'] {
  const byCategory = { profitability: [] as number[], liquidity: [] as number[], leverage: [] as number[], efficiency: [] as number[] };
  for (const r of ratios) {
    if (byCategory[r.category]) {
      byCategory[r.category].push(r.status === 'good' ? 100 : r.status === 'warning' ? 60 : 30);
    }
  }
  const avg = (arr: number[]) => arr.length ? Math.round(arr.reduce((a, b) => a + b, 0) / arr.length) : 0;
  return {
    profitability: avg(byCategory.profitability),
    liquidity: avg(byCategory.liquidity),
    leverage: avg(byCategory.leverage),
    efficiency: avg(byCategory.efficiency),
  };
}

function computeCategoryScores(ratios: AnalysisResult['ratios']): Record<string, number> {
  const byCategory: Record<string, number[]> = {};
  for (const r of ratios) {
    if (!byCategory[r.category]) byCategory[r.category] = [];
    byCategory[r.category].push(r.status === 'good' ? 100 : r.status === 'warning' ? 60 : 30);
  }
  const scores: Record<string, number> = {};
  for (const [cat, vals] of Object.entries(byCategory)) {
    scores[cat] = Math.round(vals.reduce((a, b) => a + b, 0) / vals.length);
  }
  return scores;
}