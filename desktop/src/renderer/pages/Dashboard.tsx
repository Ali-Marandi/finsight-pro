import { useEffect } from 'react';
import { useAnalysisStore } from '../hooks/useAnalysisStore';
import { BarChart3, FileText, TrendingUp, Clock, Shield, Zap, Globe, Sparkles, Activity, FileSearch, ShieldCheck, Merge } from 'lucide-react';
import { Link } from 'react-router-dom';
import { formatDate } from '../lib/utils';
import { getAnalysisHistory } from '../lib/api';

export default function Dashboard() {
  const { analyses, setAnalyses } = useAnalysisStore();

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
      <div className="grid grid-cols-3 lg:grid-cols-5 xl:grid-cols-10 gap-2">
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
        <Link to="/ai-copilot" className="card py-3 px-4 flex items-center gap-3 hover:shadow-elevated transition-shadow cursor-pointer bg-gradient-to-r from-cascade-gold/5 to-transparent">
          <Sparkles size={16} className="text-cascade-gold shrink-0" />
          <span className="text-xs text-cascade-gold font-medium">AI Copilot</span>
        </Link>
        <Link to="/prediction" className="card py-3 px-4 flex items-center gap-3 hover:shadow-elevated transition-shadow cursor-pointer bg-gradient-to-r from-red-50 to-transparent">
          <Activity size={16} className="text-red-400 shrink-0" />
          <span className="text-xs text-red-500 font-medium">Prediction</span>
        </Link>
        <Link to="/document-intelligence" className="card py-3 px-4 flex items-center gap-3 hover:shadow-elevated transition-shadow cursor-pointer bg-gradient-to-r from-blue-50 to-transparent">
          <FileSearch size={16} className="text-blue-500 shrink-0" />
          <span className="text-xs text-blue-600 font-medium">Doc Intel</span>
        </Link>
        <Link to="/benchmarking" className="card py-3 px-4 flex items-center gap-3 hover:shadow-elevated transition-shadow cursor-pointer bg-gradient-to-r from-emerald-50 to-transparent">
          <TrendingUp size={16} className="text-emerald-500 shrink-0" />
          <span className="text-xs text-emerald-600 font-medium">Benchmark</span>
        </Link>
        <Link to="/compliance" className="card py-3 px-4 flex items-center gap-3 hover:shadow-elevated transition-shadow cursor-pointer bg-gradient-to-r from-amber-50 to-transparent">
          <ShieldCheck size={16} className="text-amber-500 shrink-0" />
          <span className="text-xs text-amber-600 font-medium">Compliance</span>
        </Link>
        <Link to="/consolidation" className="card py-3 px-4 flex items-center gap-3 hover:shadow-elevated transition-shadow cursor-pointer bg-gradient-to-r from-violet-50 to-transparent">
          <Merge size={16} className="text-violet-500 shrink-0" />
          <span className="text-xs text-violet-600 font-medium">Consolidate</span>
        </Link>
        <Link to="/tsetmc" className="card py-3 px-4 flex items-center gap-3 hover:shadow-elevated transition-shadow cursor-pointer bg-gradient-to-r from-cyan-50 to-transparent">
          <Globe size={16} className="text-cyan-500 shrink-0" />
          <span className="text-xs text-cyan-600 font-medium">TSETMC</span>
        </Link>
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
          icon={Sparkles}
          iconBg="bg-cascade-gold/10"
          iconColor="text-cascade-gold"
          value="AI"
          label="Financial Copilot"
        />
        <StatCard
          icon={Activity}
          iconBg="bg-red-50"
          iconColor="text-red-400"
          value="5"
          label="Prediction Models"
        />
      </div>

      {/* Evidence-first entry point */}
      <div>
        <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
          <div><h2 className="text-lg font-semibold">Evidence Compiler</h2><p className="mt-1 text-sm text-cascade-sage">Inspect evidence, resolve findings, then continue to financial analysis.</p></div>
          <Link to="/analysis" className="btn-primary">Start evidence review</Link>
        </div>
        <div className="card flex flex-col gap-4 border-cascade-gold/30 bg-cascade-gold/5 p-5 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-start gap-3"><Shield size={20} className="mt-0.5 shrink-0 text-cascade-gold" /><p className="text-sm text-cascade-sage">PDF tax-audit reports now pass through cited fact extraction and evidence-health checks. CSV and Excel files pass through mapping review before ratio analysis.</p></div>
          <Link to="/analysis" className="whitespace-nowrap text-sm font-semibold text-cascade-gold hover:text-cascade-gold-hover">Open review →</Link>
        </div>
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
