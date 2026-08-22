import { useState, useEffect, useMemo } from 'react';
import {
  BarChart3,
  Target,
  Trophy,
  AlertTriangle,
  ChevronDown,
  ArrowRightLeft,
  Lightbulb,
  TrendingUp,
  TrendingDown,
  Minus,
  Info,
  RefreshCw,
  ChevronRight,
  ArrowUpRight,
  ArrowDownRight,
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
  ReferenceLine,
} from 'recharts';
import { useAnalysisStore } from '../hooks/useAnalysisStore';
import { compareBenchmark, getIndustries } from '../lib/api';
import { useToast } from '../components/Toast';
import Spinner from '../components/Spinner';
import { cn } from '../lib/utils';
import type { BenchmarkResult, BenchmarkComparison } from '../../types';

// ────────────────────────────────────────────────────────────────────────────
// Constants & helpers
// ────────────────────────────────────────────────────────────────────────────

const rankConfig: Record<
  BenchmarkComparison['rank'],
  { label: string; color: string; bg: string; icon: React.ElementType }
> = {
  excellent: {
    label: 'Excellent',
    color: 'text-semantic-success',
    bg: 'bg-semantic-success/10',
    icon: Trophy,
  },
  above_average: {
    label: 'Above Average',
    color: 'text-cascade-gold',
    bg: 'bg-cascade-gold/10',
    icon: TrendingUp,
  },
  below_average: {
    label: 'Below Average',
    color: 'text-semantic-warning',
    bg: 'bg-semantic-warning/10',
    icon: Minus,
  },
  poor: {
    label: 'Poor',
    color: 'text-semantic-danger',
    bg: 'bg-semantic-danger/10',
    icon: TrendingDown,
  },
  no_benchmark: {
    label: 'N/A',
    color: 'text-cascade-sage',
    bg: 'bg-cascade-mist',
    icon: Info,
  },
};

function getRankBadge(rank: BenchmarkComparison['rank']) {
  const cfg = rankConfig[rank];
  const Icon = cfg.icon;
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold',
        cfg.bg,
        cfg.color,
      )}
    >
      <Icon size={12} />
      {cfg.label}
    </span>
  );
}

// ────────────────────────────────────────────────────────────────────────────
// Main Page
// ────────────────────────────────────────────────────────────────────────────

export default function Benchmarking() {
  const { analyses, currentAnalysis } = useAnalysisStore();
  const { toast } = useToast();

  // UI state
  const [selectedAnalysisId, setSelectedAnalysisId] = useState<string | null>(null);
  const [selectedIndustryId, setSelectedIndustryId] = useState<string | null>(null);
  const [industries, setIndustries] = useState<
    { id: string; name_en: string; name_fa: string }[]
  >([]);
  const [industryDropdownOpen, setIndustryDropdownOpen] = useState(false);
  const [analysisDropdownOpen, setAnalysisDropdownOpen] = useState(false);

  // Results
  const [benchmarkResult, setBenchmarkResult] = useState<BenchmarkResult | null>(null);
  const [isComparing, setIsComparing] = useState(false);
  const [isLoadingIndustries, setIsLoadingIndustries] = useState(false);

  // Active comparison category filter
  const [activeCategory, setActiveCategory] = useState<string>('all');

  // Pre-select the current analysis when available
  useEffect(() => {
    if (currentAnalysis && !selectedAnalysisId) {
      setSelectedAnalysisId(currentAnalysis.analysisId);
    }
  }, [currentAnalysis]);

  // Load industries on mount
  useEffect(() => {
    loadIndustries();
  }, []);

  const loadIndustries = async () => {
    setIsLoadingIndustries(true);
    try {
      const res = await getIndustries();
      if (res.industries && res.industries.length > 0) {
        setIndustries(res.industries);
      }
    } catch {
      toast('warning', 'Could not load industries. Using demo data.');
      setIndustries(demoIndustries);
    } finally {
      setIsLoadingIndustries(false);
    }
  };

  const selectedAnalysis = useMemo(
    () =>
      selectedAnalysisId
        ? analyses.find((a) => a.analysisId === selectedAnalysisId) ??
          (currentAnalysis?.analysisId === selectedAnalysisId
            ? currentAnalysis
            : null)
        : null,
    [selectedAnalysisId, analyses, currentAnalysis],
  );

  const handleCompare = async () => {
    if (!selectedAnalysis) {
      toast('error', 'Please select an analysis to benchmark.');
      return;
    }
    if (!selectedIndustryId) {
      toast('error', 'Please select an industry for comparison.');
      return;
    }

    setIsComparing(true);
    setBenchmarkResult(null);

    try {
      // Build ratios payload from the selected analysis
      const analysisToUse =
        currentAnalysis?.analysisId === selectedAnalysisId
          ? currentAnalysis
          : null;

      let ratioPayload: { ratio_name: string; value: number; unit: string }[];

      if (analysisToUse && analysisToUse.ratios) {
        ratioPayload = analysisToUse.ratios.map((r) => ({
          ratio_name: r.ratioName,
          value: r.value,
          unit: r.unit,
        }));
      } else {
        // Use demo ratios if we don't have the full analysis
        ratioPayload = demoRatios;
      }

      const result = await compareBenchmark(
        selectedAnalysis.companyName,
        ratioPayload,
        selectedIndustryId,
      );
      setBenchmarkResult(result);
      toast('success', 'Benchmark comparison complete.');
    } catch (err: any) {
      toast('error', `Benchmark failed: ${err.message || 'Unknown error'}`);
      // Load demo data on failure so user still sees something useful
      setBenchmarkResult(demoBenchmarkResult);
    } finally {
      setIsComparing(false);
    }
  };

  // Filtered comparisons based on category
  const filteredComparisons = useMemo(() => {
    if (!benchmarkResult) return [];
    return benchmarkResult.comparisons;
  }, [benchmarkResult]);

  const selectedIndustry = industries.find(
    (i) => i.id === selectedIndustryId,
  );

  // ──────────────────────────────────────────────────────────────────────────
  // Render
  // ──────────────────────────────────────────────────────────────────────────
  return (
    <div className="space-y-8">
      {/* ─── Header ─── */}
      <div className="page-header">
        <div>
          <h1 className="page-title">Industry Benchmarking</h1>
          <p className="text-cascade-sage text-sm mt-1">
            Compare your financial ratios against industry medians and peer
            percentiles
          </p>
        </div>
        {benchmarkResult && (
          <button
            onClick={() => {
              setBenchmarkResult(null);
              setSelectedIndustryId(null);
              setActiveCategory('all');
            }}
            className="btn-secondary flex items-center gap-2"
          >
            <RefreshCw size={14} />
            New Comparison
          </button>
        )}
      </div>

      {/* ─── Setup Panel ─── */}
      {!benchmarkResult && (
        <div className="card">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 rounded-xl bg-cascade-gold/10 flex items-center justify-center shrink-0">
              <ArrowRightLeft size={20} className="text-cascade-gold" />
            </div>
            <div>
              <h2 className="font-semibold text-base">
                Configure Comparison
              </h2>
              <p className="text-xs text-cascade-sage">
                Select a saved analysis and an industry to benchmark against
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
            {/* Analysis Selector */}
            <div>
              <label className="block text-xs font-semibold text-cascade-sage uppercase tracking-wider mb-2">
                Analysis
              </label>
              <div className="relative">
                <button
                  onClick={() => {
                    setAnalysisDropdownOpen(!analysisDropdownOpen);
                    setIndustryDropdownOpen(false);
                  }}
                  className="w-full flex items-center justify-between px-4 py-3 rounded-lg border border-cascade-mist bg-cascade-soft-white text-sm hover:border-cascade-stone transition-colors"
                >
                  <span
                    className={
                      selectedAnalysis
                        ? 'text-cascade-charcoal font-medium'
                        : 'text-cascade-sage'
                    }
                  >
                    {selectedAnalysis
                      ? `${selectedAnalysis.companyName} — ${selectedAnalysis.period}`
                      : 'Select an analysis…'}
                  </span>
                  <ChevronDown
                    size={16}
                    className={cn(
                      'text-cascade-sage transition-transform',
                      analysisDropdownOpen && 'rotate-180',
                    )}
                  />
                </button>

                {analysisDropdownOpen && (
                  <div className="absolute z-20 top-full left-0 right-0 mt-1 bg-white border border-cascade-mist rounded-lg shadow-elevated max-h-64 overflow-y-auto">
                    {analyses.length === 0 && !currentAnalysis ? (
                      <div className="px-4 py-6 text-center">
                        <BarChart3
                          size={24}
                          className="mx-auto text-cascade-mist mb-2"
                        />
                        <p className="text-sm text-cascade-sage">
                          No analyses available. Run an analysis first.
                        </p>
                      </div>
                    ) : (
                      <>
                        {currentAnalysis && (
                          <DropdownItem
                            label={`${currentAnalysis.companyName} — ${currentAnalysis.period}`}
                            sublabel="Current analysis"
                            active={
                              selectedAnalysisId ===
                              currentAnalysis.analysisId
                            }
                            onClick={() => {
                              setSelectedAnalysisId(
                                currentAnalysis.analysisId,
                              );
                              setAnalysisDropdownOpen(false);
                            }}
                          />
                        )}
                        {analyses
                          .filter(
                            (a) =>
                              a.analysisId !==
                              currentAnalysis?.analysisId,
                          )
                          .map((item) => (
                            <DropdownItem
                              key={item.analysisId}
                              label={`${item.companyName} — ${item.period}`}
                              sublabel={item.fileName}
                              active={
                                selectedAnalysisId ===
                                item.analysisId
                              }
                              onClick={() => {
                                setSelectedAnalysisId(
                                  item.analysisId,
                                );
                                setAnalysisDropdownOpen(false);
                              }}
                            />
                          ))}
                      </>
                    )}
                  </div>
                )}
              </div>
            </div>

            {/* Industry Selector */}
            <div>
              <label className="block text-xs font-semibold text-cascade-sage uppercase tracking-wider mb-2">
                Industry
              </label>
              <div className="relative">
                <button
                  onClick={() => {
                    setIndustryDropdownOpen(!industryDropdownOpen);
                    setAnalysisDropdownOpen(false);
                  }}
                  className="w-full flex items-center justify-between px-4 py-3 rounded-lg border border-cascade-mist bg-cascade-soft-white text-sm hover:border-cascade-stone transition-colors"
                  disabled={isLoadingIndustries}
                >
                  <span
                    className={
                      selectedIndustry
                        ? 'text-cascade-charcoal font-medium'
                        : 'text-cascade-sage'
                    }
                  >
                    {isLoadingIndustries
                      ? 'Loading industries…'
                      : selectedIndustry
                        ? selectedIndustry.name_en
                        : 'Select an industry…'}
                  </span>
                  <ChevronDown
                    size={16}
                    className={cn(
                      'text-cascade-sage transition-transform',
                      industryDropdownOpen && 'rotate-180',
                    )}
                  />
                </button>

                {industryDropdownOpen && (
                  <div className="absolute z-20 top-full left-0 right-0 mt-1 bg-white border border-cascade-mist rounded-lg shadow-elevated max-h-64 overflow-y-auto">
                    {industries.length === 0 ? (
                      <div className="px-4 py-6 text-center">
                        <Target
                          size={24}
                          className="mx-auto text-cascade-mist mb-2"
                        />
                        <p className="text-sm text-cascade-sage">
                          No industries available.
                        </p>
                      </div>
                    ) : (
                      industries.map((ind) => (
                        <DropdownItem
                          key={ind.id}
                          label={ind.name_en}
                          sublabel={ind.name_fa}
                          active={selectedIndustryId === ind.id}
                          onClick={() => {
                            setSelectedIndustryId(ind.id);
                            setIndustryDropdownOpen(false);
                          }}
                        />
                      ))
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>

          <button
            onClick={handleCompare}
            disabled={isComparing || !selectedAnalysisId || !selectedIndustryId}
            className="w-full md:w-auto px-6 py-3 rounded-lg bg-cascade-charcoal text-white font-medium text-sm hover:bg-cascade-charcoal/90 transition-colors disabled:opacity-40 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            {isComparing ? (
              <>
                <Spinner size={16} />
                Comparing…
              </>
            ) : (
              <>
                <Target size={16} />
                Run Benchmark Comparison
              </>
            )}
          </button>
        </div>
      )}

      {/* ─── Loading State ─── */}
      {isComparing && (
        <div className="card py-16">
          <Spinner size={32} />
          <p className="text-sm text-cascade-sage mt-4">
            Running industry benchmark comparison…
          </p>
        </div>
      )}

      {/* ─── Benchmark Results ─── */}
      {benchmarkResult && !isComparing && (
        <>
          {/* Overall Score & Stats */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
            {/* Overall Percentile */}
            <div className="card py-4 px-4">
              <p className="text-xs text-cascade-sage uppercase tracking-wider mb-1">
                Overall Percentile
              </p>
              <div className="flex items-end gap-2">
                <span
                  className={cn(
                    'text-3xl font-bold tracking-tight',
                    benchmarkResult.overall_percentile >= 75
                      ? 'text-semantic-success'
                      : benchmarkResult.overall_percentile >= 50
                        ? 'text-cascade-gold'
                        : benchmarkResult.overall_percentile >= 25
                          ? 'text-semantic-warning'
                          : 'text-semantic-danger',
                  )}
                >
                  {benchmarkResult.overall_percentile}
                  <span className="text-base font-medium">th</span>
                </span>
              </div>
              <p className="text-xs text-cascade-sage mt-1">of industry peers</p>
            </div>

            {/* Overall Rank */}
            <div className="card py-4 px-4">
              <p className="text-xs text-cascade-sage uppercase tracking-wider mb-2">
                Overall Rank
              </p>
              {getRankBadge(
                benchmarkResult.overall_rank as BenchmarkComparison['rank'],
              )}
            </div>

            {/* Ratios Benchmarked */}
            <div className="card py-4 px-4">
              <p className="text-xs text-cascade-sage uppercase tracking-wider mb-1">
                Ratios Benchmarked
              </p>
              <div className="flex items-end gap-1">
                <span className="text-3xl font-bold text-cascade-charcoal">
                  {benchmarkResult.ratios_benchmarked}
                </span>
                <span className="text-sm text-cascade-sage mb-1">
                  / {benchmarkResult.ratios_total}
                </span>
              </div>
              <div className="mt-2 h-1.5 bg-cascade-mist rounded-full overflow-hidden">
                <div
                  className="h-full rounded-full bg-cascade-gold transition-all duration-500"
                  style={{
                    width: `${
                      (benchmarkResult.ratios_benchmarked /
                        benchmarkResult.ratios_total) *
                      100
                    }%`,
                  }}
                />
              </div>
            </div>

            {/* Industry */}
            <div className="card py-4 px-4">
              <p className="text-xs text-cascade-sage uppercase tracking-wider mb-1">
                Industry
              </p>
              <p className="text-lg font-bold text-cascade-charcoal">
                {benchmarkResult.industry_name_en}
              </p>
              <p className="text-xs text-cascade-sage mt-0.5">
                {benchmarkResult.industry_name_fa}
              </p>
            </div>
          </div>

          {/* Category Summary Cards */}
          <CategorySummaryCards comparisons={filteredComparisons} />

          {/* Comparison Chart */}
          <BenchmarkChart comparisons={filteredComparisons} />

          {/* Comparison Table */}
          <ComparisonTable comparisons={filteredComparisons} />

          {/* Recommendations */}
          {benchmarkResult.recommendations.length > 0 && (
            <div className="card">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-9 h-9 rounded-lg bg-cascade-gold/10 flex items-center justify-center shrink-0">
                  <Lightbulb size={18} className="text-cascade-gold" />
                </div>
                <div>
                  <h2 className="font-semibold text-base">
                    Recommendations
                  </h2>
                  <p className="text-xs text-cascade-sage">
                    AI-generated insights to improve performance
                  </p>
                </div>
              </div>
              <div className="space-y-3">
                {benchmarkResult.recommendations.map((rec, idx) => (
                  <div
                    key={idx}
                    className="flex items-start gap-3 p-3 rounded-lg bg-cascade-soft-white border border-cascade-mist"
                  >
                    <div className="w-6 h-6 rounded-full bg-cascade-gold/10 flex items-center justify-center shrink-0 mt-0.5">
                      <span className="text-xs font-bold text-cascade-gold">
                        {idx + 1}
                      </span>
                    </div>
                    <p className="text-sm text-cascade-charcoal leading-relaxed">
                      {rec}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}

      {/* ─── Empty State (no analysis available) ─── */}
      {!benchmarkResult &&
        !isComparing &&
        analyses.length === 0 &&
        !currentAnalysis && (
          <div className="card text-center py-16">
            <BarChart3 size={48} className="mx-auto text-cascade-mist mb-4" />
            <h3 className="text-base font-semibold mb-2">
              No analyses to benchmark
            </h3>
            <p className="text-sm text-cascade-sage max-w-md mx-auto">
              Upload and analyze a financial statement first, then return here
              to compare your results against industry benchmarks.
            </p>
          </div>
        )}
    </div>
  );
}

// ────────────────────────────────────────────────────────────────────────────
// Sub-components
// ────────────────────────────────────────────────────────────────────────────

function DropdownItem({
  label,
  sublabel,
  active,
  onClick,
}: {
  label: string;
  sublabel?: string;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className={cn(
        'w-full text-left px-4 py-3 text-sm border-b border-cascade-mist last:border-b-0 transition-colors',
        active
          ? 'bg-cascade-gold/5 text-cascade-charcoal font-medium'
          : 'text-cascade-charcoal hover:bg-cascade-stone/30',
      )}
    >
      <div className="flex items-center justify-between">
        <span>{label}</span>
        {active && (
          <ChevronRight size={14} className="text-cascade-gold" />
        )}
      </div>
      {sublabel && (
        <p className="text-xs text-cascade-sage mt-0.5">{sublabel}</p>
      )}
    </button>
  );
}

// ────────────────────────────────────────────────────────────────────────────
// Category Summary Cards
// ────────────────────────────────────────────────────────────────────────────

const categoryLabels: Record<string, string> = {
  profitability: 'Profitability',
  liquidity: 'Liquidity',
  leverage: 'Leverage',
  efficiency: 'Efficiency',
};

const categoryIcons: Record<string, React.ElementType> = {
  profitability: TrendingUp,
  liquidity: BarChart3,
  leverage: AlertTriangle,
  efficiency: Target,
};

const categoryColors: Record<string, string> = {
  profitability: 'text-cascade-gold',
  liquidity: 'text-semantic-success',
  leverage: 'text-semantic-warning',
  efficiency: 'text-cascade-olive',
};

const categoryBgColors: Record<string, string> = {
  profitability: 'bg-cascade-gold/10',
  liquidity: 'bg-semantic-success/10',
  leverage: 'bg-semantic-warning/10',
  efficiency: 'bg-cascade-olive/10',
};

function CategorySummaryCards({
  comparisons,
}: {
  comparisons: BenchmarkComparison[];
}) {
  // Group by inferred category
  const categories = useMemo(() => {
    const groups: Record<
      string,
      { comparisons: BenchmarkComparison[]; avgPercentile: number }
    > = {};
    for (const c of comparisons) {
      const cat = inferCategory(c.ratio_name);
      if (!groups[cat])
        groups[cat] = { comparisons: [], avgPercentile: 0 };
      groups[cat].comparisons.push(c);
    }
    for (const g of Object.values(groups)) {
      const withPct = g.comparisons.filter(
        (c) => c.percentile !== null,
      );
      g.avgPercentile =
        withPct.length > 0
          ? Math.round(
              withPct.reduce((a, b) => a + (b.percentile ?? 0), 0) /
                withPct.length,
            )
          : 0;
    }
    return groups;
  }, [comparisons]);

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
      {Object.entries(categories).map(([cat, data]) => {
        const Icon = categoryIcons[cat] || BarChart3;
        const excellent = data.comparisons.filter(
          (c) => c.rank === 'excellent',
        ).length;
        const poor = data.comparisons.filter(
          (c) => c.rank === 'poor' || c.rank === 'below_average',
        ).length;

        return (
          <div key={cat} className="card py-3 px-4">
            <div className="flex items-center gap-2 mb-2">
              <div
                className={cn(
                  'w-7 h-7 rounded-lg flex items-center justify-center',
                  categoryBgColors[cat] || 'bg-cascade-mist',
                )}
              >
                <Icon
                  size={14}
                  className={categoryColors[cat] || 'text-cascade-sage'}
                />
              </div>
              <span className="text-xs font-semibold text-cascade-sage uppercase tracking-wider">
                {categoryLabels[cat] || cat}
              </span>
            </div>
            <div className="flex items-end gap-2">
              <span
                className={cn(
                  'text-xl font-bold',
                  data.avgPercentile >= 70
                    ? 'text-semantic-success'
                    : data.avgPercentile >= 50
                      ? 'text-cascade-gold'
                      : data.avgPercentile >= 30
                        ? 'text-semantic-warning'
                        : 'text-semantic-danger',
                )}
              >
                {data.avgPercentile}
                <span className="text-xs font-medium">th</span>
              </span>
              <span className="text-xs text-cascade-sage mb-0.5">
                avg percentile
              </span>
            </div>
            <div className="flex gap-3 mt-2 text-xs text-cascade-sage">
              <span className="text-semantic-success">
                {excellent} excellent
              </span>
              <span className="text-semantic-danger">{poor} below avg</span>
            </div>
          </div>
        );
      })}
    </div>
  );
}

function inferCategory(ratioName: string): string {
  const name = ratioName.toLowerCase();
  if (
    name.includes('profit') ||
    name.includes('margin') ||
    name.includes('roa') ||
    name.includes('roe') ||
    name.includes('return')
  )
    return 'profitability';
  if (
    name.includes('current') ||
    name.includes('quick') ||
    name.includes('cash') ||
    name.includes('liquidity')
  )
    return 'liquidity';
  if (
    name.includes('debt') ||
    name.includes('leverage') ||
    name.includes('equity') ||
    name.includes('d/e') ||
    name.includes('interest')
  )
    return 'leverage';
  return 'efficiency';
}

// ────────────────────────────────────────────────────────────────────────────
// Benchmark Chart
// ────────────────────────────────────────────────────────────────────────────

function BenchmarkChart({
  comparisons,
}: {
  comparisons: BenchmarkComparison[];
}) {
  // Build normalized chart data (percentile-based for cross-ratio comparability)
  const chartData = comparisons
    .filter((c) => c.percentile !== null)
    .slice(0, 12) // Show max 12 for readability
    .map((c) => ({
      name: c.ratio_name.replace(/_/g, ' '),
      company: c.percentile!,
      median: 50, // By definition median = 50th percentile
      rank: c.rank,
      deviation: c.deviation_pct,
    }));

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="font-semibold text-base">Percentile Ranking</h3>
          <p className="text-xs text-cascade-sage mt-0.5">
            Your position relative to industry peers (higher is better)
          </p>
        </div>
        <div className="flex items-center gap-4 text-xs text-cascade-sage">
          <span className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded-sm bg-cascade-gold" />
            Your Company
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded-sm bg-cascade-mist" />
            Industry Median
          </span>
        </div>
      </div>

      <div className="h-72">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={chartData}
            margin={{ top: 5, right: 20, left: 0, bottom: 5 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#e7e5e4" vertical={false} />
            <XAxis
              dataKey="name"
              tick={{ fontSize: 10, fill: '#78716c' }}
              angle={-30}
              textAnchor="end"
              height={65}
            />
            <YAxis
              tick={{ fontSize: 11, fill: '#78716c' }}
              domain={[0, 100]}
              tickFormatter={(v: number) => `${v}th`}
            />
            <Tooltip
              contentStyle={{
                background: '#1a1a19',
                border: 'none',
                borderRadius: '8px',
                color: '#fff',
                fontSize: '12px',
              }}
              formatter={(value: number, name: string) => {
                if (name === 'company') return [`${value}th percentile`, 'Your Company'];
                return [`${value}th percentile`, 'Industry Median'];
              }}
            />
            <ReferenceLine
              y={50}
              stroke="#a8a29e"
              strokeDasharray="6 3"
              label={{
                value: 'Median',
                position: 'right',
                fontSize: 10,
                fill: '#a8a29e',
              }}
            />
            <Bar dataKey="company" radius={[4, 4, 0, 0]} maxBarSize={40}>
              {chartData.map((entry, index) => {
                const cfg = rankConfig[entry.rank];
                const color =
                  entry.company >= 75
                    ? '#16a34a'
                    : entry.company >= 50
                      ? '#92761f'
                      : entry.company >= 25
                        ? '#d97706'
                        : '#dc2626';
                return <Cell key={index} fill={color} />;
              })}
            </Bar>
            <Bar
              dataKey="median"
              fill="#d6d3d1"
              radius={[4, 4, 0, 0]}
              maxBarSize={20}
              opacity={0.6}
            />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

// ────────────────────────────────────────────────────────────────────────────
// Comparison Table
// ────────────────────────────────────────────────────────────────────────────

function ComparisonTable({
  comparisons,
}: {
  comparisons: BenchmarkComparison[];
}) {
  const [sortField, setSortField] = useState<
    'ratio_name' | 'percentile' | 'deviation_pct'
  >('percentile');
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc');

  const sorted = useMemo(() => {
    return [...comparisons].sort((a, b) => {
      const aVal = a[sortField] ?? 0;
      const bVal = b[sortField] ?? 0;
      return sortDir === 'asc' ? (aVal as number) - (bVal as number) : (bVal as number) - (aVal as number);
    });
  }, [comparisons, sortField, sortDir]);

  const toggleSort = (field: typeof sortField) => {
    if (sortField === field) {
      setSortDir(sortDir === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDir('desc');
    }
  };

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-semibold text-base">Detailed Comparison</h3>
        <span className="text-xs text-cascade-sage">
          {comparisons.length} ratios
        </span>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-cascade-mist">
              <th
                className="text-left py-3 px-3 text-xs font-semibold text-cascade-sage uppercase tracking-wider cursor-pointer hover:text-cascade-charcoal transition-colors"
                onClick={() => toggleSort('ratio_name')}
              >
                <span className="flex items-center gap-1">
                  Ratio
                  <SortIcon
                    active={sortField === 'ratio_name'}
                    dir={sortDir}
                  />
                </span>
              </th>
              <th className="text-right py-3 px-3 text-xs font-semibold text-cascade-sage uppercase tracking-wider">
                Your Value
              </th>
              <th className="text-right py-3 px-3 text-xs font-semibold text-cascade-sage uppercase tracking-wider">
                P25
              </th>
              <th className="text-right py-3 px-3 text-xs font-semibold text-cascade-sage uppercase tracking-wider">
                Median
              </th>
              <th className="text-right py-3 px-3 text-xs font-semibold text-cascade-sage uppercase tracking-wider">
                P75
              </th>
              <th
                className="text-right py-3 px-3 text-xs font-semibold text-cascade-sage uppercase tracking-wider cursor-pointer hover:text-cascade-charcoal transition-colors"
                onClick={() => toggleSort('percentile')}
              >
                <span className="flex items-center gap-1 justify-end">
                  Percentile
                  <SortIcon
                    active={sortField === 'percentile'}
                    dir={sortDir}
                  />
                </span>
              </th>
              <th
                className="text-right py-3 px-3 text-xs font-semibold text-cascade-sage uppercase tracking-wider cursor-pointer hover:text-cascade-charcoal transition-colors"
                onClick={() => toggleSort('deviation_pct')}
              >
                <span className="flex items-center gap-1 justify-end">
                  Deviation
                  <SortIcon
                    active={sortField === 'deviation_pct'}
                    dir={sortDir}
                  />
                </span>
              </th>
              <th className="text-center py-3 px-3 text-xs font-semibold text-cascade-sage uppercase tracking-wider">
                Rank
              </th>
            </tr>
          </thead>
          <tbody>
            {sorted.map((c, idx) => (
              <tr
                key={`${c.ratio_name}-${idx}`}
                className="border-b border-cascade-mist/50 last:border-b-0 hover:bg-cascade-stone/20 transition-colors"
              >
                <td className="py-3 px-3 font-medium text-cascade-charcoal">
                  {c.ratio_name.replace(/_/g, ' ')}
                </td>
                <td className="py-3 px-3 text-right font-mono text-cascade-charcoal">
                  {formatNumber(c.company_value)}
                </td>
                <td className="py-3 px-3 text-right font-mono text-cascade-sage">
                  {c.industry_p25 !== null
                    ? formatNumber(c.industry_p25)
                    : '—'}
                </td>
                <td className="py-3 px-3 text-right font-mono font-medium text-cascade-charcoal">
                  {c.industry_median !== null
                    ? formatNumber(c.industry_median)
                    : '—'}
                </td>
                <td className="py-3 px-3 text-right font-mono text-cascade-sage">
                  {c.industry_p75 !== null
                    ? formatNumber(c.industry_p75)
                    : '—'}
                </td>
                <td className="py-3 px-3 text-right">
                  {c.percentile !== null ? (
                    <span
                      className={cn(
                        'font-mono font-semibold',
                        c.percentile >= 75
                          ? 'text-semantic-success'
                          : c.percentile >= 50
                            ? 'text-cascade-gold'
                            : c.percentile >= 25
                              ? 'text-semantic-warning'
                              : 'text-semantic-danger',
                      )}
                    >
                      {c.percentile}th
                    </span>
                  ) : (
                    <span className="text-cascade-sage">—</span>
                  )}
                </td>
                <td className="py-3 px-3 text-right">
                  {c.deviation_pct !== null ? (
                    <span
                      className={cn(
                        'inline-flex items-center gap-0.5 font-mono text-xs font-medium',
                        c.deviation_pct > 0
                          ? 'text-semantic-success'
                          : c.deviation_pct < 0
                            ? 'text-semantic-danger'
                            : 'text-cascade-sage',
                      )}
                    >
                      {c.deviation_pct > 0 ? (
                        <ArrowUpRight size={12} />
                      ) : c.deviation_pct < 0 ? (
                        <ArrowDownRight size={12} />
                      ) : null}
                      {Math.abs(c.deviation_pct).toFixed(1)}%
                    </span>
                  ) : (
                    <span className="text-cascade-sage">—</span>
                  )}
                </td>
                <td className="py-3 px-3 text-center">
                  {getRankBadge(c.rank)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function SortIcon({
  active,
  dir,
}: {
  active: boolean;
  dir: 'asc' | 'desc';
}) {
  return (
    <span
      className={cn(
        'inline-flex flex-col leading-none gap-0',
        active ? 'text-cascade-charcoal' : 'text-cascade-mist',
      )}
    >
      <span
        className={cn(
          'text-[8px]',
          dir === 'asc' && active ? 'text-cascade-gold' : '',
        )}
      >
        ▲
      </span>
      <span
        className={cn(
          'text-[8px] -mt-0.5',
          dir === 'desc' && active ? 'text-cascade-gold' : '',
        )}
      >
        ▼
      </span>
    </span>
  );
}

// ────────────────────────────────────────────────────────────────────────────
// Utility
// ────────────────────────────────────────────────────────────────────────────

function formatNumber(value: number): string {
  if (Math.abs(value) < 1) return (value * 100).toFixed(1) + '%';
  if (Math.abs(value) >= 1000) return value.toLocaleString('en-US', { maximumFractionDigits: 1 });
  return value.toFixed(2);
}

// ────────────────────────────────────────────────────────────────────────────
// Demo data (fallback when API is unavailable)
// ────────────────────────────────────────────────────────────────────────────

const demoIndustries = [
  { id: 'manufacturing', name_en: 'Manufacturing', name_fa: 'تولید' },
  { id: 'technology', name_en: 'Technology', name_fa: 'فناوری' },
  { id: 'healthcare', name_en: 'Healthcare', name_fa: 'بهداشت و درمان' },
  { id: 'finance', name_en: 'Finance & Banking', name_fa: 'مالی و بانکی' },
  { id: 'retail', name_en: 'Retail & Commerce', name_fa: 'خرده‌فروشی' },
  { id: 'energy', name_en: 'Energy & Utilities', name_fa: 'انرژی و آب' },
  { id: 'construction', name_en: 'Construction', name_fa: 'ساختمان' },
  { id: 'agriculture', name_en: 'Agriculture', name_fa: 'کشاورزی' },
];

const demoRatios = [
  { ratio_name: 'net_profit_margin', value: 0.12, unit: '%' },
  { ratio_name: 'gross_profit_margin', value: 0.35, unit: '%' },
  { ratio_name: 'return_on_assets', value: 0.08, unit: '%' },
  { ratio_name: 'return_on_equity', value: 0.15, unit: '%' },
  { ratio_name: 'current_ratio', value: 1.8, unit: 'x' },
  { ratio_name: 'quick_ratio', value: 1.2, unit: 'x' },
  { ratio_name: 'debt_to_equity', value: 0.65, unit: 'x' },
  { ratio_name: 'interest_coverage', value: 4.2, unit: 'x' },
  { ratio_name: 'asset_turnover', value: 1.1, unit: 'x' },
  { ratio_name: 'inventory_turnover', value: 6.5, unit: 'x' },
];

const demoBenchmarkResult: BenchmarkResult = {
  industry_id: 'manufacturing',
  industry_name_en: 'Manufacturing',
  industry_name_fa: 'تولید',
  overall_percentile: 62,
  overall_rank: 'above_average',
  ratios_benchmarked: 9,
  ratios_total: 10,
  comparisons: [
    {
      ratio_name: 'net_profit_margin',
      company_value: 0.12,
      industry_median: 0.08,
      industry_p25: 0.04,
      industry_p75: 0.14,
      percentile: 68,
      rank: 'above_average',
      deviation_pct: 50.0,
    },
    {
      ratio_name: 'gross_profit_margin',
      company_value: 0.35,
      industry_median: 0.30,
      industry_p25: 0.22,
      industry_p75: 0.38,
      percentile: 60,
      rank: 'above_average',
      deviation_pct: 16.7,
    },
    {
      ratio_name: 'return_on_assets',
      company_value: 0.08,
      industry_median: 0.06,
      industry_p25: 0.03,
      industry_p75: 0.09,
      percentile: 65,
      rank: 'above_average',
      deviation_pct: 33.3,
    },
    {
      ratio_name: 'return_on_equity',
      company_value: 0.15,
      industry_median: 0.12,
      industry_p25: 0.07,
      industry_p75: 0.18,
      percentile: 58,
      rank: 'above_average',
      deviation_pct: 25.0,
    },
    {
      ratio_name: 'current_ratio',
      company_value: 1.8,
      industry_median: 1.5,
      industry_p25: 1.1,
      industry_p75: 2.0,
      percentile: 62,
      rank: 'above_average',
      deviation_pct: 20.0,
    },
    {
      ratio_name: 'quick_ratio',
      company_value: 1.2,
      industry_median: 1.0,
      industry_p25: 0.7,
      industry_p75: 1.4,
      percentile: 60,
      rank: 'above_average',
      deviation_pct: 20.0,
    },
    {
      ratio_name: 'debt_to_equity',
      company_value: 0.65,
      industry_median: 0.80,
      industry_p25: 0.50,
      industry_p75: 1.10,
      percentile: 55,
      rank: 'above_average',
      deviation_pct: -18.75,
    },
    {
      ratio_name: 'interest_coverage',
      company_value: 4.2,
      industry_median: 3.5,
      industry_p25: 2.0,
      industry_p75: 5.5,
      percentile: 57,
      rank: 'above_average',
      deviation_pct: 20.0,
    },
    {
      ratio_name: 'asset_turnover',
      company_value: 1.1,
      industry_median: 1.3,
      industry_p25: 0.9,
      industry_p75: 1.6,
      percentile: 40,
      rank: 'below_average',
      deviation_pct: -15.4,
    },
  ],
  recommendations: [
    'Improve asset turnover by optimizing inventory management and increasing revenue per asset — your 1.1x is below the industry median of 1.3x.',
    'Your debt-to-equity ratio of 0.65 is better than the median (0.80), but consider maintaining this advantage as you scale operations.',
    'Net profit margin at 12% outperforms 68% of peers — sustain this through cost discipline and pricing strategy.',
    'Quick ratio of 1.2 is healthy; however, monitor working capital to ensure short-term obligations are comfortably met during expansion.',
  ],
};
