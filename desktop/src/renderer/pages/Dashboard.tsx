import { useEffect } from 'react';
import { useAnalysisStore } from '../hooks/useAnalysisStore';
import { BarChart3, FileText, TrendingUp, Clock, Shield, Zap, Globe } from 'lucide-react';
import { Link } from 'react-router-dom';
import { formatDate } from '../lib/utils';
import { uploadAndAnalyze, getAnalysisHistory } from '../lib/api';
import { useToast } from '../components/Toast';
import FileUpload from '../components/FileUpload';
import Spinner from '../components/Spinner';
import type { AnalysisResult, AnalysisHistoryItem } from '../../types';

export default function Dashboard() {
  const { analyses, setAnalyses, isLoading, setIsLoading, setCurrentAnalysis } = useAnalysisStore();
  const { toast } = useToast();

  // Load history on mount
  useEffect(() => {
    loadHistory();
  }, []);

  const loadHistory = async () => {
    try {
      const res = await getAnalysisHistory();
      if (res.data && res.data.length > 0) {
        setAnalyses(res.data);
      }
    } catch {
      // Demo data already loaded by Layout
    }
  };

  const handleFileSelected = async (filePath: string) => {
    setIsLoading(true);
    try {
      const result = await uploadAndAnalyze(filePath);
      if (result.data) {
        setCurrentAnalysis(result.data);
        // Add to history
        const historyItem: AnalysisHistoryItem = {
          analysisId: result.data.analysisId,
          companyName: result.data.companyName,
          period: result.data.period,
          fileName: result.data.fileName,
          createdAt: result.data.createdAt,
          summary: computeSummary(result.data.ratios),
        };
        const { analyses: current } = useAnalysisStore.getState();
        setAnalyses([historyItem, ...current]);
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

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title">Dashboard</h1>
          <p className="text-cascade-sage text-sm mt-1">Upload a financial statement to get started</p>
        </div>
      </div>

      {/* Feature Highlights */}
      <div className="grid grid-cols-3 gap-3">
        <div className="card py-3 px-4 flex items-center gap-3">
          <Shield size={16} className="text-cascade-gold shrink-0" />
          <span className="text-xs text-cascade-sage">100% Offline & Private</span>
        </div>
        <div className="card py-3 px-4 flex items-center gap-3">
          <Zap size={16} className="text-cascade-gold shrink-0" />
          <span className="text-xs text-cascade-sage">Instant Analysis</span>
        </div>
        <div className="card py-3 px-4 flex items-center gap-3">
          <Globe size={16} className="text-cascade-gold shrink-0" />
          <span className="text-xs text-cascade-sage">Multi-Format Support</span>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          icon={BarChart3}
          iconBg="bg-cascade-gold/10"
          iconColor="text-cascade-gold"
          value={String(analyses.length)}
          label="Total Analyses"
        />
        <StatCard
          icon={TrendingUp}
          iconBg="bg-semantic-success/10"
          iconColor="text-semantic-success"
          value="17"
          label="Financial Ratios"
        />
        <StatCard
          icon={FileText}
          iconBg="bg-semantic-info/10"
          iconColor="text-semantic-info"
          value="3"
          label="Export Formats"
        />
        <StatCard
          icon={Clock}
          iconBg="bg-semantic-warning/10"
          iconColor="text-semantic-warning"
          value="<2s"
          label="Analysis Time"
        />
      </div>

      {/* Upload Section */}
      <div>
        <h2 className="text-lg font-semibold mb-4">Quick Analysis</h2>
        {isLoading ? (
          <div className="card py-16">
            <Spinner size={32} />
            <p className="text-sm text-cascade-sage mt-4">Analyzing your financial statement...</p>
          </div>
        ) : (
          <FileUpload onFileSelected={handleFileSelected} isLoading={isLoading} />
        )}
      </div>

      {/* Recent Analyses */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold">Recent Analyses</h2>
          <Link to="/history" className="text-sm text-cascade-gold hover:text-cascade-gold-hover font-medium">
            View all
          </Link>
        </div>

        {analyses.length === 0 ? (
          <div className="card text-center py-12">
            <BarChart3 size={48} className="mx-auto text-cascade-mist mb-4" />
            <h3 className="text-base font-semibold mb-2">No analyses yet</h3>
            <p className="text-sm text-cascade-sage max-w-sm mx-auto">
              Upload a CSV or Excel financial statement to see your first analysis here.
            </p>
          </div>
        ) : (
          <div className="space-y-2">
            {analyses.slice(0, 5).map((item) => (
              <Link
                key={item.analysisId}
                to={`/analysis/${item.analysisId}`}
                className="card flex items-center justify-between hover:shadow-elevated transition-shadow group py-4"
              >
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 rounded-lg bg-cascade-gold/10 flex items-center justify-center shrink-0">
                    <FileText size={16} className="text-cascade-gold" />
                  </div>
                  <div>
                    <p className="font-medium text-sm group-hover:text-cascade-gold transition-colors">
                      {item.companyName || 'Unnamed Analysis'}
                    </p>
                    <p className="text-xs text-cascade-sage">{item.period}</p>
                  </div>
                </div>
                <div className="flex items-center gap-4">
                  {item.summary && <MiniScore label="Score" value={Math.round((item.summary.profitability + item.summary.liquidity + item.summary.leverage + item.summary.efficiency) / 4)} />}
                  <span className="text-xs text-cascade-sage whitespace-nowrap">{formatDate(item.createdAt)}</span>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function StatCard({ icon: Icon, iconBg, iconColor, value, label }: {
  icon: React.ElementType; iconBg: string; iconColor: string; value: string; label: string;
}) {
  return (
    <div className="card flex items-center gap-3 py-4">
      <div className={`w-10 h-10 rounded-xl ${iconBg} flex items-center justify-center shrink-0`}>
        <Icon size={20} className={iconColor} />
      </div>
      <div>
        <p className="text-xl font-bold">{value}</p>
        <p className="text-xs text-cascade-sage">{label}</p>
      </div>
    </div>
  );
}

function MiniScore({ value }: { label: string; value: number }) {
  const color = value >= 70 ? 'text-semantic-success' : value >= 50 ? 'text-semantic-warning' : 'text-semantic-danger';
  return <span className={`text-sm font-bold ${color}`}>{value}%</span>;
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
