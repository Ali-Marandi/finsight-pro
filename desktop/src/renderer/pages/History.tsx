import { useAnalysisStore } from '../hooks/useAnalysisStore';
import { FileText, Trash2, BarChart3 } from 'lucide-react';
import { Link } from 'react-router-dom';
import { formatDate } from '../lib/utils';

export default function History() {
  const { analyses } = useAnalysisStore();

  return (
    <div className="space-y-8">
      <div className="page-header">
        <div>
          <h1 className="page-title">Analysis History</h1>
          <p className="text-cascade-sage text-sm mt-1">All your past financial analyses</p>
        </div>
        <span className="text-sm text-cascade-sage">{analyses.length} analyses</span>
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
              className="card flex items-center justify-between hover:shadow-elevated transition-shadow group"
            >
              <div className="flex items-center gap-4">
                <div className="w-10 h-10 rounded-lg bg-cascade-gold/10 flex items-center justify-center">
                  <FileText size={18} className="text-cascade-gold" />
                </div>
                <div>
                  <p className="font-medium text-sm group-hover:text-cascade-gold transition-colors">
                    {item.companyName || 'Untitled Analysis'}
                  </p>
                  <p className="text-xs text-cascade-sage">{item.period} • {item.fileName}</p>
                </div>
              </div>
              <div className="flex items-center gap-4">
                <span className="text-xs text-cascade-sage">{formatDate(item.createdAt)}</span>
                <button
                  onClick={(e) => {
                    e.preventDefault();
                    // Delete handler
                  }}
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