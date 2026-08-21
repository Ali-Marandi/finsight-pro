import { useAnalysisStore } from '../hooks/useAnalysisStore';
import { BarChart3, FileText, TrendingUp, Clock } from 'lucide-react';
import { Link } from 'react-router-dom';
import { formatDate } from '../lib/utils';
import FileUpload from '../components/FileUpload';

export default function Dashboard() {
  const { analyses, currentAnalysis, isLoading } = useAnalysisStore();

  const handleFileSelected = async (filePath: string) => {
    // Will be connected to API in Phase 2
    console.log('File selected:', filePath);
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

      {/* Quick Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="card flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-cascade-gold/10 flex items-center justify-center">
            <BarChart3 size={22} className="text-cascade-gold" />
          </div>
          <div>
            <p className="text-2xl font-bold">{analyses.length}</p>
            <p className="text-xs text-cascade-sage">Total Analyses</p>
          </div>
        </div>
        <div className="card flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-semantic-success/10 flex items-center justify-center">
            <TrendingUp size={22} className="text-semantic-success" />
          </div>
          <div>
            <p className="text-2xl font-bold">15+</p>
            <p className="text-xs text-cascade-sage">Financial Ratios</p>
          </div>
        </div>
        <div className="card flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-semantic-info/10 flex items-center justify-center">
            <FileText size={22} className="text-semantic-info" />
          </div>
          <div>
            <p className="text-2xl font-bold">3</p>
            <p className="text-xs text-cascade-sage">Export Formats</p>
          </div>
        </div>
        <div className="card flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-semantic-warning/10 flex items-center justify-center">
            <Clock size={22} className="text-semantic-warning" />
          </div>
          <div>
            <p className="text-2xl font-bold">100%</p>
            <p className="text-xs text-cascade-sage">Offline & Private</p>
          </div>
        </div>
      </div>

      {/* Upload Section */}
      <div>
        <h2 className="text-lg font-semibold mb-4">Quick Analysis</h2>
        <FileUpload onFileSelected={handleFileSelected} isLoading={isLoading} />
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
          <div className="space-y-3">
            {analyses.slice(0, 5).map((item) => (
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
                      {item.companyName || 'Unnamed Analysis'}
                    </p>
                    <p className="text-xs text-cascade-sage">{item.period} • {item.fileName}</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-xs text-cascade-sage">{formatDate(item.createdAt)}</p>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}