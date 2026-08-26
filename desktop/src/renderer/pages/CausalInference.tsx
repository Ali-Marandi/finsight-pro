import { useState, useEffect, useMemo } from 'react';
import { GitBranch, AlertCircle, Loader2, Activity, BarChart3, ArrowRight } from 'lucide-react';
import { LineChart, Line, AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend, Cell } from 'recharts';
import { getCausalDemo } from '../lib/api';

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

/* ------------------------------------------------------------------ */
/*  Tab config                                                         */
/* ------------------------------------------------------------------ */
type TabId = 'granger' | 'impulse' | 'transfer_entropy' | 'mutual_information' | 'discovery';

const TABS: { id: TabId; label: string; icon: typeof GitBranch }[] = [
  { id: 'granger', label: 'Granger Causality', icon: ArrowRight },
  { id: 'impulse', label: 'Impulse Response', icon: Activity },
  { id: 'transfer_entropy', label: 'Transfer Entropy', icon: BarChart3 },
  { id: 'mutual_information', label: 'Mutual Information', icon: BarChart3 },
  { id: 'discovery', label: 'Causal Discovery', icon: GitBranch },
];

/* ------------------------------------------------------------------ */
/*  Helper: p-value → cell colour                                      */
/* ------------------------------------------------------------------ */
function pValueColor(p: number): string {
  if (p <= 0.01) return 'bg-green-500/20 text-green-800';
  if (p <= 0.05) return 'bg-yellow-400/25 text-yellow-800';
  return 'bg-gray-100 text-gray-500';
}

/* ------------------------------------------------------------------ */
/*  Main component                                                     */
/* ------------------------------------------------------------------ */
export default function CausalInference() {
  const [activeTab, setActiveTab] = useState<TabId>('granger');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [data, setData] = useState<any>(null);

  const loadDemo = async () => {
    setLoading(true);
    setError('');
    try {
      const result = await getCausalDemo();
      setData(result);
    } catch (e: any) {
      setError(e?.response?.data?.detail || e?.message || 'Failed to load causal inference demo');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDemo();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  /* ---------------------------------------------------------------- */
  /*  Derived: Granger Causality                                        */
  /* ---------------------------------------------------------------- */
  const grangerMatrix = useMemo(() => {
    const m = data?.granger_causality?.causality_matrix;
    if (!m || typeof m !== 'object') return null;
    // Expect { variables: [...], matrix: [[p00, p01, ...], ...] }
    const variables: string[] = m.variables ?? Object.keys(m).filter(k => k !== 'variables' && k !== 'matrix');
    const matrix: number[][] = m.matrix ?? [];
    return { variables, matrix };
  }, [data?.granger_causality?.causality_matrix]);

  /* ---------------------------------------------------------------- */
  /*  Derived: Impulse Response                                        */
  /* ---------------------------------------------------------------- */
  const irfData = useMemo(() => {
    const irf = data?.impulse_response;
    if (!irf) return [];
    // Expect irf_results: [{ response_var, shock_var, values: [...] }]
    const results: any[] = irf.irf_results ?? irf.results ?? [];
    if (!results.length) return [];
    const maxLen = Math.max(...results.map((r: any) => (r.values ?? []).length));
    const timeline: any[] = [];
    for (let i = 0; i < maxLen; i++) {
      const point: any = { period: i };
      for (const r of results) {
        const key = `${r.response_var ?? 'Y'}→${r.shock_var ?? 'X'}`;
        point[key] = (r.values ?? [])[i] ?? null;
      }
      timeline.push(point);
    }
    return timeline;
  }, [data?.impulse_response]);

  const irfKeys = useMemo(() => {
    const irf = data?.impulse_response;
    const results: any[] = irf?.irf_results ?? irf?.results ?? [];
    return results.map((r: any) => `${r.response_var ?? 'Y'}→${r.shock_var ?? 'X'}`);
  }, [data?.impulse_response]);

  /* ---------------------------------------------------------------- */
  /*  Derived: Transfer Entropy                                        */
  /* ---------------------------------------------------------------- */
  const teData = useMemo(() => {
    const pairs: any[] = data?.transfer_entropy?.pairs ?? data?.transfer_entropy?.results ?? [];
    if (!Array.isArray(pairs)) return [];
    return pairs.map((p: any) => ({
      name: `${p.source ?? p.from ?? '?'}→${p.target ?? p.to ?? '?'}`,
      te: p.te ?? p.value ?? p.transfer_entropy ?? 0,
      significant: (p.significant ?? (p.p_value != null && p.p_value <= 0.05)) ?? false,
    }));
  }, [data?.transfer_entropy]);

  /* ---------------------------------------------------------------- */
  /*  Derived: Mutual Information                                      */
  /* ---------------------------------------------------------------- */
  const miData = useMemo(() => {
    const pairs: any[] = data?.mutual_information?.pairs ?? data?.mutual_information?.results ?? [];
    if (!Array.isArray(pairs)) return [];
    return pairs.map((p: any, i: number) => ({
      name: `${p.var1 ?? p.source ?? '?'}–${p.var2 ?? p.target ?? '?'}`,
      mi: p.mi ?? p.value ?? p.mutual_information ?? 0,
    }));
  }, [data?.mutual_information]);

  /* ---------------------------------------------------------------- */
  /*  Derived: Causal Discovery edges                                  */
  /* ---------------------------------------------------------------- */
  const discoveryEdges = useMemo(() => {
    const edges: any[] = data?.causal_discovery?.edges ?? data?.causal_discovery?.results ?? [];
    if (!Array.isArray(edges)) return [];
    return edges.map((e: any) => ({
      source: e.source ?? e.from ?? '?',
      target: e.target ?? e.to ?? '?',
      type: e.type ?? e.orientation ?? 'unknown',
    }));
  }, [data?.causal_discovery]);

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
            <GitBranch className="text-cascade-gold" size={20} />
          </div>
          <div>
            <h1 className="text-xl font-bold text-cascade-charcoal">Causal Inference</h1>
            <p className="text-sm text-gray-500">Granger causality, impulse response, transfer entropy &amp; more</p>
          </div>
        </div>
        <button
          onClick={loadDemo}
          disabled={loading}
          className="px-5 py-2.5 bg-cascade-gold text-white rounded-lg hover:bg-cascade-gold/90 disabled:opacity-50 flex items-center gap-2 text-sm font-medium shadow-sm"
        >
          {loading ? <Loader2 className="animate-spin" size={16} /> : <GitBranch size={16} />}
          Reload Demo
        </button>
      </div>

      {/* Loading Spinner */}
      {loading && (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="animate-spin text-cascade-gold" size={32} />
          <span className="ml-3 text-gray-500 text-sm">Running causal inference…</span>
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
          <div className="flex gap-1 bg-gray-100 rounded-xl p-1 overflow-x-auto">
            {TABS.map((t) => {
              const Icon = t.icon;
              return (
                <button
                  key={t.id}
                  onClick={() => setActiveTab(t.id)}
                  className={`flex-1 flex items-center justify-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium transition-all whitespace-nowrap min-w-0 ${
                    activeTab === t.id
                      ? 'bg-white text-cascade-charcoal shadow-sm'
                      : 'text-gray-500 hover:text-gray-700'
                  }`}
                >
                  <Icon size={14} className="shrink-0" />
                  <span className="hidden lg:inline truncate">{t.label}</span>
                  <span className="lg:hidden truncate">{t.label.split(' ')[0]}</span>
                </button>
              );
            })}
          </div>

          {/* ============================================================ */}
          {/* Tab 1 – Granger Causality                                     */}
          {/* ============================================================ */}
          {activeTab === 'granger' && (
            <div className="space-y-4">
              {/* Metric cards */}
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                <MetricCard label="Variables (n)" value={data.granger_causality?.n_variables ?? '—'} />
                <MetricCard label="Optimal Lag" value={data.granger_causality?.optimal_lag ?? '—'} />
                <MetricCard label="Significant Links" value={data.granger_causality?.significant_links ?? '—'} />
              </div>

              {/* Heatmap table of p-values */}
              <div className="bg-white rounded-xl border border-gray-200 p-5">
                <h3 className="font-semibold text-cascade-charcoal mb-1">Causality Matrix (p-values)</h3>
                <p className="text-xs text-gray-500 mb-4">
                  Rows = cause, Columns = effect.{' '}
                  <span className="inline-block w-3 h-3 align-middle bg-green-500/30 rounded-sm mr-1" /> 1%{' '}
                  <span className="inline-block w-3 h-3 align-middle bg-yellow-400/40 rounded-sm mr-1" /> 5%{' '}
                  <span className="inline-block w-3 h-3 align-middle bg-gray-200 rounded-sm" /> n.s.
                </p>

                {grangerMatrix && grangerMatrix.variables.length > 0 && grangerMatrix.matrix.length > 0 ? (
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm border-collapse">
                      <thead>
                        <tr>
                          <th className="py-2 px-3 text-left text-xs font-semibold text-gray-500 border-b border-gray-200">
                            Cause ↓ / Effect →
                          </th>
                          {grangerMatrix.variables.map((v: string, j: number) => (
                            <th
                              key={j}
                              className="py-2 px-3 text-center text-xs font-semibold text-gray-600 border-b border-gray-200 whitespace-nowrap"
                            >
                              {v}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {grangerMatrix.variables.map((rowVar: string, i: number) => (
                          <tr key={i}>
                            <td className="py-2 px-3 font-medium text-cascade-charcoal border-b border-gray-100 whitespace-nowrap">
                              {rowVar}
                            </td>
                            {(grangerMatrix.matrix[i] ?? []).map((p: number, j: number) => (
                              <td
                                key={j}
                                className={`py-2 px-3 text-center text-xs font-mono font-semibold rounded-sm m-0.5 ${pValueColor(p)}`}
                                title={`p = ${typeof p === 'number' ? p.toFixed(4) : p}`}
                              >
                                {typeof p === 'number' ? p.toFixed(3) : p}
                              </td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <p className="text-sm text-gray-400 py-8 text-center">No causality matrix data available</p>
                )}
              </div>
            </div>
          )}

          {/* ============================================================ */}
          {/* Tab 2 – Impulse Response                                      */}
          {/* ============================================================ */}
          {activeTab === 'impulse' && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                <MetricCard label="Lags Used" value={data.impulse_response?.n_lags ?? '—'} />
                <MetricCard label="Forecast Horizon" value={data.impulse_response?.horizon ?? '—'} />
              </div>

              <div className="bg-white rounded-xl border border-gray-200 p-5">
                <h3 className="font-semibold text-cascade-charcoal mb-4">Impulse Response Functions</h3>
                {irfData.length > 0 ? (
                  <ResponsiveContainer width="100%" height={360}>
                    <LineChart data={irfData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e5e5e5" />
                      <XAxis dataKey="period" tick={{ fontSize: 11 }} label={{ value: 'Period', position: 'insideBottom', offset: -5, fontSize: 12 }} />
                      <YAxis tick={{ fontSize: 11 }} />
                      <Tooltip contentStyle={tooltipStyle} />
                      <Legend />
                      {irfKeys.map((key: string, i: number) => (
                        <Line
                          key={key}
                          type="monotone"
                          dataKey={key}
                          stroke={CHART_PALETTE[i % CHART_PALETTE.length]}
                          strokeWidth={2}
                          dot={false}
                          connectNulls
                        />
                      ))}
                    </LineChart>
                  </ResponsiveContainer>
                ) : (
                  <p className="text-sm text-gray-400 py-8 text-center">No impulse response data available</p>
                )}
              </div>
            </div>
          )}

          {/* ============================================================ */}
          {/* Tab 3 – Transfer Entropy                                      */}
          {/* ============================================================ */}
          {activeTab === 'transfer_entropy' && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                <MetricCard label="Pairs (n)" value={data.transfer_entropy?.n_pairs ?? '—'} />
                <MetricCard label="Max TE" value={data.transfer_entropy?.max_te ?? '—'} />
                <MetricCard label="Significant Directions" value={data.transfer_entropy?.significant_directions ?? '—'} />
              </div>

              <div className="bg-white rounded-xl border border-gray-200 p-5">
                <h3 className="font-semibold text-cascade-charcoal mb-1">Transfer Entropy by Pair (X→Y)</h3>
                <p className="text-xs text-gray-500 mb-4">
                  <span className="inline-block w-3 h-3 align-middle rounded-sm mr-1" style={{ background: COLORS.green }} /> Significant{' '}
                  <span className="inline-block w-3 h-3 align-middle bg-gray-300 rounded-sm mr-1" /> Not significant
                </p>
                {teData.length > 0 ? (
                  <ResponsiveContainer width="100%" height={Math.max(300, teData.length * 36)}>
                    <BarChart data={teData} layout="vertical" margin={{ left: 80 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e5e5e5" horizontal={false} />
                      <XAxis type="number" tick={{ fontSize: 11 }} />
                      <YAxis type="category" dataKey="name" tick={{ fontSize: 10 }} width={75} />
                      <Tooltip contentStyle={tooltipStyle} />
                      <Bar dataKey="te" radius={[0, 6, 6, 0]} name="TE" barSize={18}>
                        {teData.map((d: any, i: number) => (
                          <Cell
                            key={i}
                            fill={d.significant ? CHART_PALETTE[i % CHART_PALETTE.length] : '#d1d5db'}
                            opacity={d.significant ? 1 : 0.5}
                          />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                ) : (
                  <p className="text-sm text-gray-400 py-8 text-center">No transfer entropy data available</p>
                )}
              </div>
            </div>
          )}

          {/* ============================================================ */}
          {/* Tab 4 – Mutual Information                                    */}
          {/* ============================================================ */}
          {activeTab === 'mutual_information' && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                <MetricCard label="Variables (n)" value={data.mutual_information?.n_variables ?? '—'} />
                <MetricCard label="Max MI" value={data.mutual_information?.max_mi ?? '—'} />
                <MetricCard label="Avg MI" value={data.mutual_information?.avg_mi ?? '—'} />
              </div>

              <div className="bg-white rounded-xl border border-gray-200 p-5">
                <h3 className="font-semibold text-cascade-charcoal mb-4">Pairwise Mutual Information</h3>
                {miData.length > 0 ? (
                  <ResponsiveContainer width="100%" height={Math.max(300, miData.length * 36)}>
                    <BarChart data={miData} layout="vertical" margin={{ left: 80 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e5e5e5" horizontal={false} />
                      <XAxis type="number" tick={{ fontSize: 11 }} />
                      <YAxis type="category" dataKey="name" tick={{ fontSize: 10 }} width={75} />
                      <Tooltip contentStyle={tooltipStyle} />
                      <Bar dataKey="mi" radius={[0, 6, 6, 0]} name="MI" barSize={18}>
                        {miData.map((_: any, i: number) => (
                          <Cell key={i} fill={CHART_PALETTE[i % CHART_PALETTE.length]} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                ) : (
                  <p className="text-sm text-gray-400 py-8 text-center">No mutual information data available</p>
                )}
              </div>
            </div>
          )}

          {/* ============================================================ */}
          {/* Tab 5 – Causal Discovery                                      */}
          {/* ============================================================ */}
          {activeTab === 'discovery' && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                <MetricCard label="Nodes (n)" value={data.causal_discovery?.n_nodes ?? '—'} />
                <MetricCard label="Edges (n)" value={data.causal_discovery?.n_edges ?? '—'} />
                <MetricCard label="Communities (n)" value={data.causal_discovery?.n_communities ?? '—'} />
              </div>

              <div className="bg-white rounded-xl border border-gray-200 p-5">
                <h3 className="font-semibold text-cascade-charcoal mb-1">Discovered Edges</h3>
                <p className="text-xs text-gray-500 mb-4">
                  Edge orientation:{' '}
                  <span className="font-mono text-cascade-gold">A→B</span> directed,{' '}
                  <span className="font-mono text-blue-600">A←B</span> reverse directed,{' '}
                  <span className="font-mono text-gray-600">A—B</span> undirected
                </p>
                {discoveryEdges.length > 0 ? (
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b border-gray-200">
                          <th className="text-left py-2 px-3 font-semibold text-gray-600">#</th>
                          <th className="text-left py-2 px-3 font-semibold text-gray-600">Source</th>
                          <th className="text-center py-2 px-3 font-semibold text-gray-600">Orientation</th>
                          <th className="text-left py-2 px-3 font-semibold text-gray-600">Target</th>
                        </tr>
                      </thead>
                      <tbody>
                        {discoveryEdges.map((edge: any, i: number) => {
                          const t: string = (edge.type ?? 'unknown').toLowerCase();
                          const isForward = t.includes('->') || t === 'directed' || t === 'forward';
                          const isBackward = t.includes('<-') || t === 'reverse' || t === 'backward';
                          const isUndirected = t.includes('--') || t.includes('—') || t === 'undirected' || t === 'unknown';

                          return (
                            <tr key={i} className="border-b border-gray-100 last:border-0 hover:bg-gray-50">
                              <td className="py-2 px-3 text-gray-400">{i + 1}</td>
                              <td className="py-2 px-3 font-medium text-cascade-charcoal">{edge.source}</td>
                              <td className="py-2 px-3 text-center">
                                {isForward && (
                                  <span className="inline-flex items-center gap-1 font-mono font-semibold text-cascade-gold">
                                    <ArrowRight size={14} /> →
                                  </span>
                                )}
                                {isBackward && (
                                  <span className="inline-flex items-center gap-1 font-mono font-semibold text-blue-600">
                                    ← <ArrowRight size={14} className="rotate-180" />
                                  </span>
                                )}
                                {isUndirected && (
                                  <span className="inline-flex items-center gap-1 font-mono font-semibold text-gray-500">
                                    —
                                  </span>
                                )}
                              </td>
                              <td className="py-2 px-3 font-medium text-cascade-charcoal">{edge.target}</td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <p className="text-sm text-gray-400 py-8 text-center">No causal discovery data available</p>
                )}
              </div>
            </div>
          )}
        </>
      )}

      {/* Empty State */}
      {!data && !loading && !error && (
        <div className="text-center py-20 text-gray-400">
          <GitBranch size={48} className="mx-auto mb-4 opacity-30" />
          <p className="text-lg font-medium">No causal data yet</p>
          <p className="text-sm mt-1 mb-6">
            Click &quot;Reload Demo&quot; to run Causal Inference
          </p>
          <button
            onClick={loadDemo}
            className="px-5 py-2.5 bg-cascade-gold text-white rounded-lg hover:bg-cascade-gold/90 inline-flex items-center gap-2 text-sm font-medium shadow-sm"
          >
            <GitBranch size={16} /> Load Demo
          </button>
        </div>
      )}
    </div>
  );
}
