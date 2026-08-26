import { useState, useEffect, useMemo } from 'react';
import { Network, AlertCircle, Loader2, Shield, GitBranch, BarChart3 } from 'lucide-react';
import {
  AreaChart, Area, BarChart, Bar, XAxis, YAxis,
  CartesianGrid, Tooltip, ResponsiveContainer, Legend, Cell,
} from 'recharts';
import { getNetworkDemo } from '../lib/api';

/* ------------------------------------------------------------------ */
/*  Design tokens                                                      */
/* ------------------------------------------------------------------ */
const COLORS = {
  gold: '#92761f',
  blue: '#3b82f6',
  red: '#ef4444',
  green: '#10b981',
  purple: '#8b5cf6',
  orange: '#f59e0b',
};
const CHART_PALETTE = [COLORS.gold, COLORS.blue, COLORS.red, COLORS.green, COLORS.purple, COLORS.orange];

/* ------------------------------------------------------------------ */
/*  Sub-components                                                     */
/* ------------------------------------------------------------------ */
function MetricCard({ label, value, suffix = '' }: { label: string; value: string | number; suffix?: string }) {
  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4">
      <p className="text-xs text-gray-500 mb-1">{label}</p>
      <p className="text-lg font-semibold text-gray-900">
        {typeof value === 'number' ? value.toLocaleString(undefined, { maximumFractionDigits: 4 }) : value}
        {suffix}
      </p>
    </div>
  );
}

/* Downsample long arrays to at most `maxPts` entries */
function downsample<T>(arr: T[], maxPts = 120): T[] {
  if (arr.length <= maxPts) return arr;
  const step = Math.ceil(arr.length / maxPts);
  return arr.filter((_, i) => i % step === 0 || i === arr.length - 1);
}

/* ------------------------------------------------------------------ */
/*  Tab config                                                         */
/* ------------------------------------------------------------------ */
type TabId = 'correlation' | 'mst' | 'contagion' | 'systemic';

const TABS: { id: TabId; label: string; icon: typeof Network }[] = [
  { id: 'correlation', label: 'Correlation Network', icon: Network },
  { id: 'mst', label: 'MST', icon: GitBranch },
  { id: 'contagion', label: 'Contagion', icon: BarChart3 },
  { id: 'systemic', label: 'Systemic Risk', icon: Shield },
];

/* ------------------------------------------------------------------ */
/*  Main component                                                     */
/* ------------------------------------------------------------------ */
export default function NetworkAnalysis() {
  const [activeTab, setActiveTab] = useState<TabId>('correlation');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [data, setData] = useState<any>(null);

  const loadDemo = async () => {
    setLoading(true);
    setError('');
    try {
      const result = await getNetworkDemo();
      setData(result);
    } catch (e: any) {
      setError(e?.response?.data?.detail || e?.message || 'Failed to load network demo');
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

  const degreeData = useMemo(() => {
    const items = data?.correlation_network?.degree_centrality;
    if (!items || !Array.isArray(items)) return [];
    return items.map((d: any) => ({
      name: typeof d.asset === 'string' ? d.asset.split(' ')[0] : d.asset,
      degree: d.degree ?? d.value ?? d,
    }));
  }, [data?.correlation_network?.degree_centrality]);

  const betweennessData = useMemo(() => {
    const items = data?.correlation_network?.betweenness_centrality;
    if (!items || !Array.isArray(items)) return [];
    return items.map((d: any) => ({
      name: typeof d.asset === 'string' ? d.asset.split(' ')[0] : d.asset,
      betweenness: d.betweenness ?? d.value ?? d,
    }));
  }, [data?.correlation_network?.betweenness_centrality]);

  const mstEdgeData = useMemo(() => {
    const edges = data?.mst?.edges;
    if (!edges || !Array.isArray(edges)) return [];
    return edges.map((e: any, i: number) => ({
      name: (e.source?.split(' ')[0] ?? 'A') + '-' + (e.target?.split(' ')[0] ?? 'B'),
      weight: e.weight ?? 0,
    }));
  }, [data?.mst?.edges]);

  const contagionTimeline = useMemo(() => {
    const timeline = data?.contagion?.timeline;
    if (!timeline || !Array.isArray(timeline)) return [];
    return downsample(timeline).map((t: any) => ({
      round: t.round ?? t.step ?? 0,
      healthy: t.healthy ?? 0,
      stressed: t.stressed ?? 0,
      failed: t.failed ?? 0,
    }));
  }, [data?.contagion?.timeline]);

  const tbtfRanking = useMemo(() => {
    const ranking = data?.contagion?.too_big_to_fail;
    if (!ranking || !Array.isArray(ranking)) return [];
    return ranking;
  }, [data?.contagion?.too_big_to_fail]);

  const sriskData = useMemo(() => {
    const items = data?.systemic_risk?.srisk_scores;
    if (!items || !Array.isArray(items)) return [];
    return items.map((d: any) => ({
      name: typeof d.asset === 'string' ? d.asset.split(' ')[0] : d.asset,
      srisk: d.srisk ?? d.value ?? d,
    }));
  }, [data?.systemic_risk?.srisk_scores]);

  const mesData = useMemo(() => {
    const items = data?.systemic_risk?.mes_scores;
    if (!items || !Array.isArray(items)) return [];
    return items.map((d: any) => ({
      name: typeof d.asset === 'string' ? d.asset.split(' ')[0] : d.asset,
      mes: d.mes ?? d.value ?? d,
    }));
  }, [data?.systemic_risk?.mes_scores]);

  const tooltipStyle = { borderRadius: 8, fontSize: 12, border: '1px solid #e5e7eb' };

  /* ---------------------------------------------------------------- */
  /*  Render                                                           */
  /* ---------------------------------------------------------------- */
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-cascade-gold/10 rounded-xl flex items-center justify-center">
            <Network className="text-cascade-gold" size={20} />
          </div>
          <div>
            <h1 className="text-xl font-bold text-cascade-charcoal">Network Analysis</h1>
            <p className="text-sm text-gray-500">Correlation, MST, contagion &amp; systemic risk</p>
          </div>
        </div>
        <button
          onClick={loadDemo}
          disabled={loading}
          className="px-5 py-2.5 bg-cascade-gold text-white rounded-lg hover:bg-cascade-gold/90 disabled:opacity-50 flex items-center gap-2 text-sm font-medium shadow-sm"
        >
          {loading ? <Loader2 className="animate-spin" size={16} /> : <Network size={16} />}
          Reload Demo
        </button>
      </div>

      {/* Loading Spinner */}
      {loading && (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="animate-spin text-cascade-gold" size={32} />
          <span className="ml-3 text-gray-500 text-sm">Building network analysis…</span>
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
          {data.demo_title && (
            <div className="bg-cascade-gold/5 border border-cascade-gold/20 rounded-xl p-4">
              <h2 className="text-sm font-semibold text-cascade-charcoal mb-1">{data.demo_title}</h2>
              {data.description && <p className="text-sm text-gray-600">{data.description}</p>}
            </div>
          )}

          {/* Tab Navigation */}
          <div className="flex gap-1 bg-gray-100 rounded-xl p-1">
            {TABS.map((t) => {
              const Icon = t.icon;
              return (
                <button
                  key={t.id}
                  onClick={() => setActiveTab(t.id)}
                  className={`flex-1 flex items-center justify-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium transition-all whitespace-nowrap ${
                    activeTab === t.id
                      ? 'bg-white text-cascade-charcoal shadow-sm'
                      : 'text-gray-500 hover:text-gray-700'
                  }`}
                >
                  <Icon size={14} />
                  <span className="hidden sm:inline">{t.label}</span>
                  <span className="sm:hidden">{t.label.split(' ')[0]}</span>
                </button>
              );
            })}
          </div>

          {/* Tab 1 - Correlation Network */}
          {activeTab === 'correlation' && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                <MetricCard label="Assets (n)" value={data.correlation_network?.n_assets ?? '—'} />
                <MetricCard label="Edges" value={data.correlation_network?.n_edges ?? '—'} />
                <MetricCard label="Density" value={data.correlation_network?.density ?? '—'} />
                <MetricCard label="Avg Clustering" value={data.correlation_network?.avg_clustering ?? '—'} />
                <MetricCard label="Avg Path Length" value={data.correlation_network?.avg_path_length ?? '—'} />
              </div>

              <div className="bg-white rounded-xl border border-gray-200 p-5">
                <h3 className="font-semibold text-cascade-charcoal mb-4">Degree Centrality per Asset</h3>
                {degreeData.length > 0 ? (
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={degreeData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e5e5e5" />
                      <XAxis dataKey="name" tick={{ fontSize: 10 }} angle={-30} textAnchor="end" height={60} />
                      <YAxis tick={{ fontSize: 11 }} />
                      <Tooltip contentStyle={tooltipStyle} />
                      <Bar dataKey="degree" fill={COLORS.gold} radius={[6, 6, 0, 0]} name="Degree" />
                    </BarChart>
                  </ResponsiveContainer>
                ) : (
                  <p className="text-sm text-gray-400 py-8 text-center">No degree centrality data available</p>
                )}
              </div>

              <div className="bg-white rounded-xl border border-gray-200 p-5">
                <h3 className="font-semibold text-cascade-charcoal mb-4">Betweenness Centrality per Asset</h3>
                {betweennessData.length > 0 ? (
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={betweennessData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e5e5e5" />
                      <XAxis dataKey="name" tick={{ fontSize: 10 }} angle={-30} textAnchor="end" height={60} />
                      <YAxis tick={{ fontSize: 11 }} />
                      <Tooltip contentStyle={tooltipStyle} />
                      <Bar dataKey="betweenness" fill={COLORS.blue} radius={[6, 6, 0, 0]} name="Betweenness" />
                    </BarChart>
                  </ResponsiveContainer>
                ) : (
                  <p className="text-sm text-gray-400 py-8 text-center">No betweenness centrality data available</p>
                )}
              </div>
            </div>
          )}

          {/* Tab 2 - MST */}
          {activeTab === 'mst' && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                <MetricCard label="MST Edges" value={data.mst?.n_edges ?? '—'} />
                <MetricCard label="Total Weight" value={data.mst?.total_weight ?? '—'} />
                <MetricCard label="Max Edge Weight" value={data.mst?.max_edge_weight ?? '—'} />
                <MetricCard label="Min Edge Weight" value={data.mst?.min_edge_weight ?? '—'} />
                <MetricCard label="Diameter" value={data.mst?.diameter ?? '—'} />
              </div>

              <div className="bg-white rounded-xl border border-gray-200 p-5">
                <h3 className="font-semibold text-cascade-charcoal mb-4">MST Edge Weights</h3>
                {mstEdgeData.length > 0 ? (
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={mstEdgeData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e5e5e5" />
                      <XAxis dataKey="name" tick={{ fontSize: 10 }} angle={-30} textAnchor="end" height={60} />
                      <YAxis tick={{ fontSize: 11 }} />
                      <Tooltip contentStyle={tooltipStyle} />
                      <Bar dataKey="weight" radius={[6, 6, 0, 0]} name="Weight">
                        {mstEdgeData.map((_: any, i: number) => (
                          <Cell key={i} fill={CHART_PALETTE[i % CHART_PALETTE.length]} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                ) : (
                  <p className="text-sm text-gray-400 py-8 text-center">No MST edge data available</p>
                )}
              </div>
            </div>
          )}

          {/* Tab 3 - Contagion */}
          {activeTab === 'contagion' && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                <MetricCard label="Rounds" value={data.contagion?.n_rounds ?? '—'} />
                <MetricCard label="Initial Failed" value={data.contagion?.initial_failed ?? '—'} />
                <MetricCard label="Total Failed" value={data.contagion?.total_failed ?? '—'} />
                <MetricCard label="Total Stressed" value={data.contagion?.total_stressed ?? '—'} />
                <MetricCard label="Avg System Loss" value={data.contagion?.avg_system_loss_pct ?? '—'} suffix=" %" />
              </div>

              <div className="bg-white rounded-xl border border-gray-200 p-5">
                <h3 className="font-semibold text-cascade-charcoal mb-4">Contagion Timeline</h3>
                {contagionTimeline.length > 0 ? (
                  <ResponsiveContainer width="100%" height={320}>
                    <AreaChart data={contagionTimeline}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e5e5e5" />
                      <XAxis dataKey="round" tick={{ fontSize: 11 }} label={{ value: 'Round', position: 'insideBottom', offset: -5, fontSize: 12 }} />
                      <YAxis tick={{ fontSize: 11 }} />
                      <Tooltip contentStyle={tooltipStyle} />
                      <Legend />
                      <Area type="monotone" dataKey="healthy" stackId="1" stroke={COLORS.green} fill={COLORS.green} fillOpacity={0.5} name="Healthy" />
                      <Area type="monotone" dataKey="stressed" stackId="1" stroke={COLORS.orange} fill={COLORS.orange} fillOpacity={0.5} name="Stressed" />
                      <Area type="monotone" dataKey="failed" stackId="1" stroke={COLORS.red} fill={COLORS.red} fillOpacity={0.5} name="Failed" />
                    </AreaChart>
                  </ResponsiveContainer>
                ) : (
                  <p className="text-sm text-gray-400 py-8 text-center">No contagion timeline data available</p>
                )}
              </div>

              <div className="bg-white rounded-xl border border-gray-200 p-5">
                <h3 className="font-semibold text-cascade-charcoal mb-4">Too Big To Fail - Ranking</h3>
                {tbtfRanking.length > 0 ? (
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b border-gray-200">
                          <th className="text-left py-2 px-3 font-semibold text-gray-600">#</th>
                          <th className="text-left py-2 px-3 font-semibold text-gray-600">Asset</th>
                          <th className="text-right py-2 px-3 font-semibold text-gray-600">Cascading Failed</th>
                          <th className="text-right py-2 px-3 font-semibold text-gray-600">Impact Score</th>
                        </tr>
                      </thead>
                      <tbody>
                        {tbtfRanking.map((r: any, i: number) => (
                          <tr key={i} className="border-b border-gray-100 last:border-0">
                            <td className="py-2 px-3 text-gray-400">{i + 1}</td>
                            <td className="py-2 px-3 font-medium text-cascade-charcoal">{r.asset_name ?? r.asset ?? '—'}</td>
                            <td className={`py-2 px-3 text-right font-medium ${
                              (r.cascading_failed ?? 0) > 0 ? 'text-red-600' : 'text-gray-500'
                            }`}>
                              {r.cascading_failed ?? 0}
                            </td>
                            <td className="py-2 px-3 text-right font-semibold text-cascade-gold">
                              {typeof r.impact_score === 'number' ? r.impact_score.toFixed(4) : r.impact_score ?? '—'}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <p className="text-sm text-gray-400 py-8 text-center">No too-big-to-fail ranking data available</p>
                )}
              </div>
            </div>
          )}

          {/* Tab 4 - Systemic Risk */}
          {activeTab === 'systemic' && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                <MetricCard label="Top SRISK Asset" value={data.systemic_risk?.top_srisk_asset ?? '—'} />
                <MetricCard label="Top CoVaR Asset" value={data.systemic_risk?.top_covaR_asset ?? data.systemic_risk?.top_covar_asset ?? '—'} />
                <MetricCard label="Connectedness Index" value={data.systemic_risk?.connectedness_index ?? '—'} />
              </div>

              <div className="bg-white rounded-xl border border-gray-200 p-5">
                <h3 className="font-semibold text-cascade-charcoal mb-4">SRISK Scores per Asset</h3>
                {sriskData.length > 0 ? (
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={sriskData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e5e5e5" />
                      <XAxis dataKey="name" tick={{ fontSize: 10 }} angle={-30} textAnchor="end" height={60} />
                      <YAxis tick={{ fontSize: 11 }} />
                      <Tooltip contentStyle={tooltipStyle} />
                      <Bar dataKey="srisk" radius={[6, 6, 0, 0]} name="SRISK">
                        {sriskData.map((_: any, i: number) => (
                          <Cell key={i} fill={CHART_PALETTE[i % CHART_PALETTE.length]} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                ) : (
                  <p className="text-sm text-gray-400 py-8 text-center">No SRISK data available</p>
                )}
              </div>

              <div className="bg-white rounded-xl border border-gray-200 p-5">
                <h3 className="font-semibold text-cascade-charcoal mb-4">Marginal Expected Shortfall (MES) per Asset</h3>
                {mesData.length > 0 ? (
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={mesData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e5e5e5" />
                      <XAxis dataKey="name" tick={{ fontSize: 10 }} angle={-30} textAnchor="end" height={60} />
                      <YAxis tick={{ fontSize: 11 }} />
                      <Tooltip contentStyle={tooltipStyle} />
                      <Bar dataKey="mes" radius={[6, 6, 0, 0]} name="MES">
                        {mesData.map((_: any, i: number) => (
                          <Cell key={i} fill={CHART_PALETTE[i % CHART_PALETTE.length]} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                ) : (
                  <p className="text-sm text-gray-400 py-8 text-center">No MES data available</p>
                )}
              </div>
            </div>
          )}
        </>
      )}

      {/* Empty State */}
      {!data && !loading && !error && (
        <div className="text-center py-20 text-gray-400">
          <Network size={48} className="mx-auto mb-4 opacity-30" />
          <p className="text-lg font-medium">No network data yet</p>
          <p className="text-sm mt-1 mb-6">Click {'"'}Reload Demo{'"'} to see Network Analysis</p>
          <button
            onClick={loadDemo}
            className="px-5 py-2.5 bg-cascade-gold text-white rounded-lg hover:bg-cascade-gold/90 inline-flex items-center gap-2 text-sm font-medium shadow-sm"
          >
            <Network size={16} /> Load Demo
          </button>
        </div>
      )}
    </div>
  );
}
