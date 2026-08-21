import { useEffect } from 'react';
import { useAnalysisStore } from '../hooks/useAnalysisStore';
import { FileText, Trash2, BarChart3 } from 'lucide-react';
import { Link } from 'react-router-dom';
import { formatDate } from '../lib/utils';
import { getAnalysisHistory, deleteAnalysis } from '../lib/api';
import { useToast } from '../components/Toast';

export default function History() {
  const { analyses, setAnalyses } = useAnalysisStore();
  const { toast } = useToast();

  useEffect(() => {
    loadHistory();
  }, []);

  const loadHistory = async () => {
    try {
      const res = await getAnalysisHistory(1, 100);
      if (res.data && res.data.length > 0) {
        setAnalyses(res.data);
      }
    } catch {
      // Keep demo data
    }
  };

  const handleDelete = async (e: React.MouseEvent, id: string) => {
    e.preventDefault();
    e.stopPropagation();

    try {
      await deleteAnalysis(id);
      setAnalyses(analyses.filter((a) => a.analysisId !== id));
      toast('success', 'Analysis deleted');
    } catch {
      // Remove locally even if API fails
      setAnalyses(analyses.filter((a) => a.analysisId !== id));
      toast('success', 'Analysis removed');
    }
  };

  return (
    <div className="space-y-8">
      <div className="page-header">
        <div>
          <h1 className="page-title">Analysis History</h1>
          <p className="text-cascade-sage text-sm mt-1">All your past financial analyses</p>
        </div>
        <span className="text-sm text-cascade-sage bg-cascade-mist/50 px-3 py-1 rounded-full">{analyses.length} analyses</span>
      </div>

      {analyses.length === 0 ? (
        <div className="card text-center py-16">
          <BarChart3 size={48} className="mx-auto text-cascade-mist mb-4" />
          <h3 className="text-base font-semibold mb-2">No history yet</h3>
          <p className="text-sm text-cascade-sage max-w-sm mx-auto">
            Your completed analyses will appear here.
          </p>
        </div>
      ) : (
        <div className="space-y-2">
          {analyses.map((item) => (
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
                    {item.companyName || 'Untitled Analysis'}
                  </p>
                  <p className="text-xs text-cascade-sage">{item.period} · {item.fileName}</p>
                </div>
              </div>
              <div className="flex items-center gap-4">
                {item.summary && (
                  <div className="hidden sm:flex gap-2">
                    {(['profitability', 'liquidity', 'leverage', 'efficiency'] as const).map((key) => {
                      const score = item.summary![key];
                      return (
                        <div key={key} className="flex items-center gap-1">
                          <div className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: score >= 70 ? '#16a34a' : score >= 50 ? '#d97706' : '#dc2626' }} />
                          <span className="text-[11px] text-cascade-sage capitalize">{key.slice(0, 4)}</span>
                        </div>
                      );
                    })}
                  </div>
                )}
                <span className="text-xs text-cascade-sage whitespace-nowrap">{formatDate(item.createdAt)}</span>
                <button
                  onClick={(e) => handleDelete(e, item.analysisId)}
                  className="p-1.5 rounded-lg text-cascade-sage hover:text-semantic-danger hover:bg-semantic-danger/10 transition-colors"
                >
                  <Trash2 size={14} />
                </button>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}