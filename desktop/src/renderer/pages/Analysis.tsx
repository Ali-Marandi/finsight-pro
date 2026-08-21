import { useState } from 'react';
import { useParams } from 'react-router-dom';
import { useAnalysisStore } from '../hooks/useAnalysisStore';
import FileUpload from '../components/FileUpload';
import RatioCard from '../components/RatioCard';
import RatioChart from '../components/RatioChart';
import { Download, FileText } from 'lucide-react';

export default function Analysis() {
  const { id } = useParams();
  const { currentAnalysis, isLoading, setIsLoading, setCurrentAnalysis } = useAnalysisStore();
  const [activeCategory, setActiveCategory] = useState<string>('all');

  const handleFileSelected = async (filePath: string) => {
    setIsLoading(true);
    try {
      // Will be connected to API:
      // const result = await uploadAndAnalyze(filePath);
      // if (result.data) setCurrentAnalysis(result.data);
      console.log('Analyzing:', filePath);
    } finally {
      setIsLoading(false);
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

  return (
    <div className="space-y-8">
      <div className="page-header">
        <div>
          <h1 className="page-title">
            {id ? 'Analysis Details' : 'New Analysis'}
          </h1>
          <p className="text-cascade-sage text-sm mt-1">
            {currentAnalysis
              ? `${currentAnalysis.companyName} — ${currentAnalysis.period}`
              : 'Upload a financial statement to begin analysis'}
          </p>
        </div>
        {currentAnalysis && (
          <div className="flex gap-2">
            <button className="btn-secondary flex items-center gap-2">
              <Download size={16} /> Export PDF
            </button>
            <button className="btn-secondary flex items-center gap-2">
              <FileText size={16} /> Export XLSX
            </button>
          </div>
        )}
      </div>

      {!currentAnalysis ? (
        <div className="max-w-2xl mx-auto">
          <FileUpload onFileSelected={handleFileSelected} isLoading={isLoading} />
        </div>
      ) : (
        <>
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
          <RatioChart ratios={filteredRatios} title={`${activeCategory === 'all' ? 'All' : activeCategory.charAt(0).toUpperCase() + activeCategory.slice(1)} Ratios`} />

          {/* Ratio Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredRatios.map((ratio, index) => (
              <RatioCard key={`${ratio.category}-${ratio.ratioName}-${index}`} ratio={ratio} />
            ))}
          </div>
        </>
      )}
    </div>
  );
}