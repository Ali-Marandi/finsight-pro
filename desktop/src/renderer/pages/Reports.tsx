import { useAnalysisStore } from '../hooks/useAnalysisStore';
import { FileText, Download, Plus } from 'lucide-react';
import { Link } from 'react-router-dom';

export default function Reports() {
  const { analyses } = useAnalysisStore();

  return (
    <div className="space-y-8">
      <div className="page-header">
        <div>
          <h1 className="page-title">Reports</h1>
          <p className="text-cascade-sage text-sm mt-1">Generate and download professional reports</p>
        </div>
        <Link to="/analysis" className="btn-primary flex items-center gap-2">
          <Plus size={16} /> New Analysis
        </Link>
      </div>

      {analyses.length === 0 ? (
        <div className="card text-center py-16">
          <FileText size={48} className="mx-auto text-cascade-mist mb-4" />
          <h3 className="text-base font-semibold mb-2">No reports available</h3>
          <p className="text-sm text-cascade-sage max-w-sm mx-auto mb-6">
            Complete a financial analysis first, then generate professional reports in PDF, Excel, or HTML format.
          </p>
          <Link to="/analysis" className="btn-primary inline-flex items-center gap-2">
            <Plus size={16} /> Start Analysis
          </Link>
        </div>
      ) : (
        <div className="space-y-3">
          {analyses.map((item) => (
            <div key={item.analysisId} className="card flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="w-10 h-10 rounded-lg bg-cascade-gold/10 flex items-center justify-center">
                  <FileText size={18} className="text-cascade-gold" />
                </div>
                <div>
                  <p className="font-medium text-sm">{item.companyName || 'Untitled Report'}</p>
                  <p className="text-xs text-cascade-sage">{item.period} • {item.fileName}</p>
                </div>
              </div>
              <div className="flex gap-2">
                <button className="btn-secondary text-xs px-3 py-1.5 flex items-center gap-1.5">
                  <Download size={14} /> PDF
                </button>
                <button className="btn-secondary text-xs px-3 py-1.5 flex items-center gap-1.5">
                  <Download size={14} /> XLSX
                </button>
                <button className="btn-secondary text-xs px-3 py-1.5 flex items-center gap-1.5">
                  <Download size={14} /> HTML
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}