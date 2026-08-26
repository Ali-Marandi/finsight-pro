import { useState, useEffect, useMemo } from 'react';
import { Sliders, AlertCircle, Loader2, BarChart3, TrendingUp, Shield, GitBranch, Target } from 'lucide-react';
import {
  LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Legend, Cell, ReferenceLine, ReferenceDot,
} from 'recharts';
import { getAdvOptDemo } from '../lib/api';

/* ------------------------------------------------------------------ */
/*  Color palette                                                       */
/* ------------------------------------------------------------------ */
const SECTOR_COLORS: Record<string, string> = {
  Technology: '#3b82f6',
  Healthcare: '#10b981',
  Finance: '#92761f',
  Energy: '#f59e0b',
  Consumer: '#8b5cf6',
  Industrial: '#ef4444',
  RealEstate: '#06b6d4',
  Utilities: '#ec4899',
  Materials: '#78716c',
  Telecom: '#6366f1',
};
const FALLBACK_SECTOR_COLORS = ['#92761f', '#3b82f6', '#ef4444', '#10b981', '#8b5cf6', '#f59e0b', '#06b6d4', '#ec4899'];

/* ------------------------------------------------------------------ */
/*  Sub-components                                                      */
/* ------------------------------------------------------------------ */
function MetricCard({ label, value, suffix = '', color }: { label: string; value: string | number; suffix?: string; color?: string }) {
  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4">
      <p className="text-xs text-gray-500 mb-1">{label}</p>
      <p className={`text-lg font-semibold ${color || 'text-gray-900'}`}>
        {typeof value === 'number' ? value.toLocaleString(undefined, { maximumFractionDigits: 4 }) : value}
        {suffix}
      </p>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Tab config                                                         */
/* ------------------------------------------------------------------ */
const tabs = ['SOCP Portfolio', 'Robust Optimization', 'HRP', 'Pareto Frontier'] as const;
type TabId = (typeof tabs)[number];
const TAB_ICONS: Record<TabId, typeof Sliders> = {
  'SOCP Portfolio': BarChart3,
  'Robust Optimization': Shield,
  'HRP': GitBranch,
  'Pareto Frontier': Target,
};

/* ------------------------------------------------------------------ */
/*  Helpers                                                            */
/* ------------------------------------------------------------------ */
function getSectorColor(sector: string | undefined, index: number): string {
  if (sector && SECTOR_COLORS[sector]) return SECTOR_COLORS[sector];
  return FALLBACK_SECTOR_COLORS[index % FALLBACK_SECTOR_COLORS.length];
}

const tooltipStyle = { borderRadius: 8, fontSize: 12, border: '1px solid #e5e7eb' };

/* ------------------------------------------------------------------ */
/*  Main component                                                     */
/* ------------------------------------------------------------------ */
export default function AdvancedOptimization() {
  const [activeTab, setActiveTab] = useState<TabId>('SOCP Portfolio');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [data, setData] = useState<any>(null);

  const loadDemo = async () => {
    setLoading(true);
    setError('');
    try {
      const result = await getAdvOptDemo();
      setData(result);
    } catch (e: any) {
      setError(e?.response?.data?.detail || e?.message || 'Failed to load Advanced Optimization demo');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDemo();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  /* ---------------------------------------------------------------- */
  /*  Derived data                                                     */
  /* ---------------------------------------------------------------- */

  // SOCP weights bar data
  const socpBarData = useMemo(() => {
    const assets = data?.assets;
    const weights = data?.socp_optimization?.weights;
    if (!assets?.length || !weights?.length) return [];
    return assets.map((a: any, i: number) => ({
      name: a.name || a.ticker || `Asset ${i + 1}`,
      weight: (weights[i] ?? 0) * 100,
      sector: a.sector,
    }));
  }, [data?.assets, data?.socp_optimization?.weights]);

  // Robust grouped bar data
  const robustBarData = useMemo(() => {
    const assets = data?.assets;
    const nw = data?.robust_optimization?.nominal_weights;
    const rw = data?.robust_optimization?.robust_weights;
    if (!assets?.length || !nw?.length || !rw?.length) return [];
    return assets.map((a: any, i: number) => ({
      name: a.name || a.ticker || `Asset ${i + 1}`,
      nominal: (nw[i] ?? 0) * 100,
      robust: (rw[i] ?? 0) * 100,
    }));
  }, [data?.assets, data?.robust_optimization?.nominal_weights, data?.robust_optimization?.robust_weights]);

  // HRP comparison bar data
  const hrpBarData = useMemo(() => {
    const assets = data?.assets;
    const hrpW = data?.hrp?.weights;
    const eqW = data?.hrp?.equal_weights;
    const ivW = data?.hrp?.inverse_variance_weights;
    if (!assets?.length || !hrpW?.length) return [];
    const n = assets.length;
    return assets.map((a: any, i: number) => ({
      name: a.name || a.ticker || `Asset ${i + 1}`,
      hrp: (hrpW[i] ?? 0) * 100,
      equal: (eqW?.[i] ?? 1 / n) * 100,
      invVar: (ivW?.[i] ?? 1 / n) * 100,
    }));
  }, [data?.assets, data?.hrp]);

  // Pareto frontier data
  const paretoData = useMemo(() => {
    const frontier = data?.pareto_frontier?.frontier;
    if (!Array.isArray(frontier)) return [];
    return frontier.map((p: any, i: number) => ({
      index: i,
      risk: p.risk ?? p.volatility ?? p.x,
      return: p.return ?? p.expected_return ?? p.y,
    }));
  }, [data?.pareto_frontier?.frontier]);

  const tangencyPoint = useMemo(() => {
    const tp = data?.pareto_frontier?.tangency_portfolio;
    if (!tp) return null;
    return { risk: tp.risk ?? tp.volatility, return: tp.return ?? tp.expected_return };
  }, [data?.pareto_frontier?.tangency_portfolio]);

  const minVarPoint = useMemo(() => {
    const mv = data?.pareto_frontier?.min_variance_portfolio;
    if (!mv) return null;
    return { risk: mv.risk ?? mv.volatility, return: mv.return ?? mv.expected_return };
  }, [data?.pareto_frontier?.min_variance_portfolio]);

  /* ---------------------------------------------------------------- */
  /*  Render                                                           */
  /* ---------------------------------------------------------------- */
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-cascade-gold/10 rounded-xl flex items-center justify-center">
            <Sliders className="text-cascade-gold" size={20} />
          </div>
          <div>
            <h1 className="text-xl font-bold text-cascade-charcoal">Advanced Optimization</h1>
            <p className="text-sm text-gray-500">SOCP, Robust Optimization, HRP & Pareto Frontier</p>
          </div>
        </div>
        <button
          onClick={loadDemo}
          disabled={loading}
          className="px-5 py-2.5 bg-cascade-gold text-white rounded-lg hover:bg-cascade-gold/90 disabled:opacity-50 flex items-center gap-2 text-sm font-medium shadow-sm"
        >
          {loading ? <Loader2 className="animate-spin" size={16} /> : <TrendingUp size={16} />}
          Load Demo
        </button>
      </div>

      {/* Loading */}
      {loading && (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="animate-spin text-cascade-gold" size={32} />
          <span className="ml-3 text-gray-500 text-sm">Running optimization models…</span>
        </div>
      )}

      {/* Error Banner */}
      {error && !loading && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-xl flex items-start gap-3">
          <AlertCircle className="text-red-500 shrink-0 mt-0.5" size={18} />
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}

      {/* Data loaded */}
      {data && !loading && (
        <>
          {/* Info Banner */}
          {(data.demo_title || data.description) && (
            <div className="bg-cascade-gold/5 border border-cascade-gold/20 rounded-xl p-4">
              <h2 className="text-sm font-semibold text-cascade-charcoal mb-1">{data.demo_title || 'Advanced Optimization'}</h2>
              {data.description && <p className="text-sm text-gray-600">{data.description}</p>}
            </div>
          )}

          {/* Tab Navigation */}
          <div className="flex gap-1 bg-gray-100 rounded-xl p-1">
            {tabs.map((t) => {
              const Icon = TAB_ICONS[t];
              return (
                <button
                  key={t}
                  onClick={() => setActiveTab(t)}
                  className={`flex-1 flex items-center justify-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium transition-all whitespace-nowrap ${
                    activeTab === t
                      ? 'bg-white text-cascade-charcoal shadow-sm'
                      : 'text-gray-500 hover:text-gray-700'
                  }`}
                >
                  <Icon size={14} />
                  <span className="hidden sm:inline">{t}</span>
                  <span className="sm:hidden">{t.split(' ')[0]}</span>
                </button>
              );
            })}
          </div>

          {/* ============== Tab 1 – SOCP Portfolio ============== */}
          {activeTab === 'SOCP Portfolio' && (
            <div className="space-y-4">
              {/* Metric Cards */}
              <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                <MetricCard
                  label="Expected Return"
                  value={data.socp_optimization?.expected_return ?? '—'}
                  suffix="%"
                  color="text-green-600"
                />
                <MetricCard
                  label="Expected Risk"
                  value={data.socp_optimization?.expected_risk ?? '—'}
                  suffix="%"
                />
                <MetricCard
                  label="Sharpe Ratio"
                  value={data.socp_optimization?.sharpe_ratio ?? '—'}
                  color="text-cascade-gold"
                />
                <MetricCard
                  label="Converged"
                  value={data.socp_optimization?.converged != null ? (data.socp_optimization.converged ? 'Yes' : 'No') : '—'}
                  color={data.socp_optimization?.converged ? 'text-green-600' : 'text-red-500'}
                />
                <MetricCard
                  label="Constraint Violations"
                  value={data.socp_optimization?.constraint_violations ?? '—'}
                  color={Number(data.socp_optimization?.constraint_violations) > 0 ? 'text-red-500' : 'text-green-600'}
                />
              </div>

              {/* Optimal Weights Bar Chart */}
              <div className="bg-white rounded-xl border border-gray-200 p-5">
                <h3 className="font-semibold text-cascade-charcoal mb-4">SOCP Optimal Weights by Asset</h3>
                {socpBarData.length > 0 ? (
                  <ResponsiveContainer width="100%" height={340}>
                    <BarChart data={socpBarData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e5e5e5" />
                      <XAxis dataKey="name" tick={{ fontSize: 11 }} interval={0} angle={-30} textAnchor="end" height={60} />
                      <YAxis tick={{ fontSize: 11 }} unit="%" />
                      <Tooltip
                        contentStyle={tooltipStyle}
                        formatter={(v: number) => [v.toFixed(2) + '%', 'Weight']}
                      />
                      <Bar dataKey="weight" radius={[4, 4, 0, 0]} name="Optimal Weight">
                        {socpBarData.map((entry: any, i: number) => (
                          <Cell key={i} fill={getSectorColor(entry.sector, i)} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                ) : (
                  <p className="text-sm text-gray-400 py-8 text-center">No SOCP weight data available</p>
                )}
              </div>

              {/* Sector Legend */}
              {socpBarData.length > 0 && (
                <div className="bg-white rounded-xl border border-gray-200 p-5">
                  <h3 className="font-semibold text-cascade-charcoal mb-3">Sector Color Key</h3>
                  <div className="flex flex-wrap gap-3">
                    {Array.from(new Set(socpBarData.map((d: any) => d.sector).filter(Boolean))).map((sector: any) => (
                      <div key={String(sector)} className="flex items-center gap-1.5">
                        <span
                          className="w-3 h-3 rounded-sm inline-block"
                          style={{ backgroundColor: SECTOR_COLORS[String(sector)] || '#92761f' }}
                        />
                        <span className="text-xs text-gray-600">{String(sector)}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* ============== Tab 2 – Robust Optimization ============== */}
          {activeTab === 'Robust Optimization' && (
            <div className="space-y-4">
              {/* Metric Cards */}
              <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                <MetricCard
                  label="Nominal Sharpe"
                  value={data.robust_optimization?.nominal_sharpe ?? '—'}
                  color="text-cascade-gold"
                />
                <MetricCard
                  label="Robust Sharpe"
                  value={data.robust_optimization?.robust_sharpe ?? '—'}
                  color="text-blue-600"
                />
                <MetricCard
                  label="Robust Return"
                  value={data.robust_optimization?.robust_return ?? '—'}
                  suffix="%"
                  color="text-green-600"
                />
                <MetricCard
                  label="Worst-Case Return"
                  value={data.robust_optimization?.worst_case_return ?? '—'}
                  suffix="%"
                  color="text-red-500"
                />
                <MetricCard
                  label="Shrinkage %"
                  value={data.robust_optimization?.shrinkage_pct ?? '—'}
                  suffix="%"
                  color="text-purple-600"
                />
              </div>

              {/* Nominal vs Robust Weights Grouped Bar Chart */}
              <div className="bg-white rounded-xl border border-gray-200 p-5">
                <h3 className="font-semibold text-cascade-charcoal mb-4">Nominal vs. Robust Weights</h3>
                {robustBarData.length > 0 ? (
                  <ResponsiveContainer width="100%" height={340}>
                    <BarChart data={robustBarData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e5e5e5" />
                      <XAxis dataKey="name" tick={{ fontSize: 11 }} interval={0} angle={-30} textAnchor="end" height={60} />
                      <YAxis tick={{ fontSize: 11 }} unit="%" />
                      <Tooltip
                        contentStyle={tooltipStyle}
                        formatter={(v: number, name: string) => [v.toFixed(2) + '%', name === 'nominal' ? 'Nominal Weight' : 'Robust Weight']}
                      />
                      <Legend formatter={(v: string) => (v === 'nominal' ? 'Nominal Weight' : 'Robust Weight')} />
                      <Bar dataKey="nominal" fill="#92761f" radius={[4, 4, 0, 0]} name="nominal" />
                      <Bar dataKey="robust" fill="#3b82f6" radius={[4, 4, 0, 0]} name="robust" />
                    </BarChart>
                  </ResponsiveContainer>
                ) : (
                  <p className="text-sm text-gray-400 py-8 text-center">No robust optimization data available</p>
                )}
              </div>
            </div>
          )}

          {/* ============== Tab 3 – HRP ============== */}
          {activeTab === 'HRP' && (
            <div className="space-y-4">
              {/* Metric Cards */}
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                <MetricCard
                  label="Number of Clusters"
                  value={data.hrp?.n_clusters ?? '—'}
                  color="text-blue-600"
                />
                <MetricCard
                  label="Linkage Method"
                  value={data.hrp?.linkage_method ?? '—'}
                />
              </div>

              {/* HRP vs Equal-Weight vs Inverse-Variance */}
              <div className="bg-white rounded-xl border border-gray-200 p-5">
                <h3 className="font-semibold text-cascade-charcoal mb-4">HRP vs. Equal-Weight vs. Inverse-Variance</h3>
                {hrpBarData.length > 0 ? (
                  <ResponsiveContainer width="100%" height={340}>
                    <BarChart data={hrpBarData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e5e5e5" />
                      <XAxis dataKey="name" tick={{ fontSize: 11 }} interval={0} angle={-30} textAnchor="end" height={60} />
                      <YAxis tick={{ fontSize: 11 }} unit="%" />
                      <Tooltip
                        contentStyle={tooltipStyle}
                        formatter={(v: number, name: string) => [
                          v.toFixed(2) + '%',
                          name === 'hrp' ? 'HRP Weight' : name === 'equal' ? 'Equal Weight' : 'Inverse-Variance Weight',
                        ]}
                      />
                      <Legend formatter={(v: string) => {
                        if (v === 'hrp') return 'HRP Weight';
                        if (v === 'equal') return 'Equal Weight';
                        return 'Inverse-Variance Weight';
                      }} />
                      <Bar dataKey="hrp" fill="#92761f" radius={[4, 4, 0, 0]} name="hrp" />
                      <Bar dataKey="equal" fill="#3b82f6" radius={[4, 4, 0, 0]} name="equal" />
                      <Bar dataKey="invVar" fill="#10b981" radius={[4, 4, 0, 0]} name="invVar" />
                    </BarChart>
                  </ResponsiveContainer>
                ) : (
                  <p className="text-sm text-gray-400 py-8 text-center">No HRP data available</p>
                )}
              </div>
            </div>
          )}

          {/* ============== Tab 4 – Pareto Frontier ============== */}
          {activeTab === 'Pareto Frontier' && (
            <div className="space-y-4">
              {/* Metric Cards */}
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                <MetricCard
                  label="Frontier Points"
                  value={data.pareto_frontier?.n_points ?? '—'}
                  color="text-purple-600"
                />
                <MetricCard
                  label="Max Sharpe Portfolio Return"
                  value={data.pareto_frontier?.max_sharpe_portfolio_return ?? '—'}
                  suffix="%"
                  color="text-green-600"
                />
                <MetricCard
                  label="Min Variance Portfolio Risk"
                  value={data.pareto_frontier?.min_var_portfolio_risk ?? '—'}
                  suffix="%"
                  color="text-red-500"
                />
              </div>

              {/* Pareto Frontier Chart */}
              <div className="bg-white rounded-xl border border-gray-200 p-5">
                <h3 className="font-semibold text-cascade-charcoal mb-4">Efficient Frontier (Risk vs. Return)</h3>
                {paretoData.length > 0 ? (
                  <ResponsiveContainer width="100%" height={400}>
                    <LineChart data={paretoData} margin={{ bottom: 20, left: 10, right: 20, top: 10 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e5e5e5" />
                      <XAxis
                        dataKey="risk"
                        tick={{ fontSize: 11 }}
                        type="number"
                        domain={['auto', 'auto']}
                        label={{ value: 'Risk (Volatility %)', position: 'insideBottom', offset: -8, style: { fontSize: 12, fill: '#6b7280' } }}
                        tickFormatter={(v: number) => v.toFixed(1)}
                      />
                      <YAxis
                        tick={{ fontSize: 11 }}
                        domain={['auto', 'auto']}
                        label={{ value: 'Return %', angle: -90, position: 'insideLeft', style: { fontSize: 12, fill: '#6b7280' } }}
                        tickFormatter={(v: number) => v.toFixed(1)}
                      />
                      <Tooltip
                        contentStyle={tooltipStyle}
                        formatter={(v: number, name: string) => [v.toFixed(2) + '%', name === 'return' ? 'Return' : 'Risk']}
                        labelFormatter={(l: number) => `Risk: ${l.toFixed(2)}%`}
                      />
                      <Legend />
                      <Line
                        type="monotone"
                        dataKey="return"
                        stroke="#92761f"
                        strokeWidth={2.5}
                        dot={{ r: 4, fill: '#92761f', stroke: '#fff', strokeWidth: 2 }}
                        name="Efficient Frontier"
                        connectNulls
                      />

                      {/* Tangency Portfolio Reference Lines */}
                      {tangencyPoint && (
                        <>
                          <ReferenceLine
                            x={tangencyPoint.risk}
                            stroke="#ef4444"
                            strokeDasharray="4 4"
                            strokeWidth={1.5}
                            label={{ value: 'Tangency', position: 'top', fill: '#ef4444', fontSize: 11, fontWeight: 600 }}
                          />
                          <ReferenceLine
                            y={tangencyPoint.return}
                            stroke="#ef4444"
                            strokeDasharray="4 4"
                            strokeWidth={1}
                          />
                          <ReferenceDot
                            x={tangencyPoint.risk}
                            y={tangencyPoint.return}
                            r={7}
                            fill="#ef4444"
                            stroke="#fff"
                            strokeWidth={2}
                            label={{ value: 'Tangency Portfolio', position: 'top', fill: '#ef4444', fontSize: 10, fontWeight: 600 }}
                          />
                        </>
                      )}

                      {/* Min Variance Portfolio Reference Lines */}
                      {minVarPoint && (
                        <>
                          <ReferenceLine
                            x={minVarPoint.risk}
                            stroke="#3b82f6"
                            strokeDasharray="4 4"
                            strokeWidth={1.5}
                            label={{ value: 'Min Var', position: 'bottom', fill: '#3b82f6', fontSize: 11, fontWeight: 600 }}
                          />
                          <ReferenceLine
                            y={minVarPoint.return}
                            stroke="#3b82f6"
                            strokeDasharray="4 4"
                            strokeWidth={1}
                          />
                          <ReferenceDot
                            x={minVarPoint.risk}
                            y={minVarPoint.return}
                            r={7}
                            fill="#3b82f6"
                            stroke="#fff"
                            strokeWidth={2}
                            label={{ value: 'Min Variance Portfolio', position: 'bottom', fill: '#3b82f6', fontSize: 10, fontWeight: 600 }}
                          />
                        </>
                      )}
                    </LineChart>
                  </ResponsiveContainer>
                ) : (
                  <p className="text-sm text-gray-400 py-8 text-center">No Pareto frontier data available</p>
                )}
              </div>

              {/* Frontier Legend */}
              <div className="bg-white rounded-xl border border-gray-200 p-4">
                <div className="flex flex-wrap gap-6 items-center">
                  <div className="flex items-center gap-2">
                    <span className="w-3 h-3 rounded-full bg-[#92761f] inline-block" />
                    <span className="text-xs text-gray-600">Efficient Frontier</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="w-3 h-3 rounded-full bg-[#ef4444] inline-block" />
                    <span className="text-xs text-gray-600">Tangency (Max Sharpe) Portfolio</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="w-3 h-3 rounded-full bg-[#3b82f6] inline-block" />
                    <span className="text-xs text-gray-600">Minimum Variance Portfolio</span>
                  </div>
                </div>
              </div>
            </div>
          )}
        </>
      )}

      {/* Empty State */}
      {!data && !loading && !error && (
        <div className="text-center py-20 text-gray-400">
          <Sliders size={48} className="mx-auto mb-4 opacity-30" />
          <p className="text-lg font-medium">No optimization data yet</p>
          <p className="text-sm mt-1 mb-6">Click &quot;Load Demo&quot; to run Advanced Optimization models</p>
          <button
            onClick={loadDemo}
            className="px-5 py-2.5 bg-cascade-gold text-white rounded-lg hover:bg-cascade-gold/90 inline-flex items-center gap-2 text-sm font-medium shadow-sm"
          >
            <TrendingUp size={16} /> Load Demo
          </button>
        </div>
      )}
    </div>
  );
}
