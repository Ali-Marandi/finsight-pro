import { useState, useEffect, useMemo } from 'react';
import { Activity, AlertCircle, TrendingUp, Zap, BarChart3, Loader2, Play } from 'lucide-react';
import {
  LineChart, Line, AreaChart, Area, BarChart, Bar, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
} from 'recharts';
import { getStochasticDemo } from '../lib/api';

/* ------------------------------------------------------------------ */
/*  Design tokens                                                      */
/* ------------------------------------------------------------------ */
const COLORS = ['#92761f', '#3b82f6', '#ef4444', '#10b981', '#8b5cf6'];
const PATH_COLORS = [COLORS[0], COLORS[1], COLORS[2], COLORS[3], COLORS[4]];

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
function downsample(arr: number[], maxPts = 120): number[] {
  if (arr.length <= maxPts) return arr;
  const step = Math.ceil(arr.length / maxPts);
  return arr.filter((_, i) => i % step === 0 || i === arr.length - 1);
}

/* Build chart-ready data from parallel arrays (e.g. spot_prices + delta) */
function zipToData(keys: string[], ...arrays: number[][]): Record<string, number>[] {
  const ds = arrays.map(a => downsample(a));
  const dLen = Math.min(...ds.map(a => a.length));
  return Array.from({ length: dLen }, (_, i) => {
    const row: Record<string, number> = {} as any;
    keys.forEach((k, ki) => { row[k] = ds[ki][i]; });
    return row;
  });
}

/* Build chart data from multiple paths (for LineChart) */
function pathsToData(...paths: number[][]): Record<string, number>[] {
  const ds = paths.map((p: any) => downsample(p));
  const dLen = Math.min(...ds.map((d: any) => d.length));
  return Array.from({ length: dLen }, (_, i) => {
    const row: Record<string, number> = { day: i } as any;
    ds.forEach((d, pi) => { row[`path${pi}`] = d[i]; });
    return row;
  });
}

/* ------------------------------------------------------------------ */
/*  Tab config                                                         */
/* ------------------------------------------------------------------ */
const tabs = ['GBM / Itô', 'Heston', 'Greeks', 'Barrier', 'Jump-Diffusion'] as const;
type TabId = (typeof tabs)[number];
const TAB_ICONS: Record<TabId, typeof Activity> = {
  'GBM / Itô': TrendingUp,
  'Heston': Zap,
  'Greeks': BarChart3,
  'Barrier': AlertCircle,
  'Jump-Diffusion': Activity,
};

/* ------------------------------------------------------------------ */
/*  Main component                                                     */
/* ------------------------------------------------------------------ */
export default function StochasticCalculus() {
  const [activeTab, setActiveTab] = useState<TabId>('GBM / Itô');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [data, setData] = useState<any>(null);

  const loadDemo = async () => {
    setLoading(true);
    setError('');
    try {
      const result = await getStochasticDemo();
      setData(result);
    } catch (e: any) {
      setError(e?.response?.data?.detail || e?.message || 'Failed to load stochastic demo');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDemo();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  /* ---------------------------------------------------------------- */
  /*  Derived data for each tab                                        */
  /* ---------------------------------------------------------------- */

  // GBM chart data
  const gbmChartData = useMemo(() => {
    if (!data?.gbm?.sample_paths?.length) return [];
    return pathsToData(...data.gbm.sample_paths.slice(0, 3));
  }, [data?.gbm?.sample_paths]);

  // Heston chart data
  const hestonChartData = useMemo(() => {
    const ap = data?.heston?.asset_paths;
    const vp = data?.heston?.vol_paths;
    if (!ap?.length || !vp?.length) return [];
    const aLen = Math.min(ap.length, 2);
    const vLen = Math.min(vp.length, 2);
    const dsA = ap.slice(0, aLen).map((p: any) => downsample(p));
    const dsV = vp.slice(0, vLen).map((p: any) => downsample(p));
    const dLen = Math.min(
      ...dsA.map((d: any) => d.length),
      ...dsV.map((d: any) => d.length),
    );
    return Array.from({ length: dLen }, (_, i) => {
      const row: Record<string, number> = { day: i } as any;
      dsA.forEach((d: any, j: number) => { row[`asset${j}`] = d[i]; });
      dsV.forEach((d: any, j: number) => { row[`vol${j}`] = d[i]; });
      return row;
    });
  }, [data?.heston]);

  // Greeks chart data
  const greeksBarData = useMemo(() => {
    const g = data?.greeks_summary;
    if (!g) return [];
    return [
      { name: 'Delta', value: g.delta },
      { name: 'Gamma', value: g.gamma },
      { name: 'Theta', value: g.theta },
      { name: 'Vega', value: g.vega },
      { name: 'Rho', value: g.rho },
    ];
  }, [data?.greeks_summary]);

  const deltaSurfaceData = useMemo(() => {
    const ds = data?.delta_surface;
    if (!ds?.spot_prices || !ds?.delta) return [];
    return zipToData(['spot', 'delta'], ds.spot_prices, ds.delta);
  }, [data?.delta_surface]);

  // Jump-Diffusion chart data
  const jumpDiffChartData = useMemo(() => {
    const jd = data?.jump_diffusion;
    if (!jd?.jump_diffusion_avg_path || !jd?.gbm_avg_path) return [];
    return zipToData(['day', 'jump', 'gbm'],
      Array.from({ length: jd.jump_diffusion_avg_path.length }, (_, i) => i),
      jd.jump_diffusion_avg_path,
      jd.gbm_avg_path,
    );
  }, [data?.jump_diffusion]);

  /* ---------------------------------------------------------------- */
  /*  Render                                                           */
  /* ---------------------------------------------------------------- */
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-cascade-gold/10 rounded-xl flex items-center justify-center">
            <Activity className="text-cascade-gold" size={20} />
          </div>
          <div>
            <h1 className="text-xl font-bold text-cascade-charcoal">Stochastic Calculus</h1>
            <p className="text-sm text-gray-500">GBM, Heston, Greeks, Barrier & Jump-Diffusion models</p>
          </div>
        </div>
        <button
          onClick={loadDemo}
          disabled={loading}
          className="px-5 py-2.5 bg-cascade-gold text-white rounded-lg hover:bg-cascade-gold/90 disabled:opacity-50 flex items-center gap-2 text-sm font-medium shadow-sm"
        >
          {loading ? <Loader2 className="animate-spin" size={16} /> : <Play size={16} />}
          Load Demo
        </button>
      </div>

      {/* Loading */}
      {loading && (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="animate-spin text-cascade-gold" size={32} />
          <span className="ml-3 text-gray-500 text-sm">Running stochastic simulations…</span>
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

          {/* ============== Tab 1 – GBM / Itô ============== */}
          {activeTab === 'GBM / Itô' && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <MetricCard label="Simulated Paths" value={data.gbm?.n_paths ?? '—'} />
                <MetricCard label="Trading Days" value={data.gbm?.days ?? '—'} />
                <MetricCard label="Mean Final Price" value={data.gbm?.mean_final_price ?? '—'} />
                <MetricCard label="Theoretical Mean" value={data.gbm?.theoretical_mean ?? '—'} />
              </div>

              <div className="bg-white rounded-xl border border-gray-200 p-5">
                <h3 className="font-semibold text-cascade-charcoal mb-4">Sample Paths (first 3)</h3>
                {gbmChartData.length > 0 ? (
                  <ResponsiveContainer width="100%" height={340}>
                    <LineChart data={gbmChartData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e5e5e5" />
                      <XAxis dataKey="day" tick={{ fontSize: 11 }} interval={Math.floor(gbmChartData.length / 8)} />
                      <YAxis tick={{ fontSize: 11 }} domain={['auto', 'auto']} />
                      <Tooltip
                        contentStyle={{ borderRadius: 8, fontSize: 12, border: '1px solid #e5e7eb' }}
                        formatter={(v: number, name: string) => [v.toFixed(2), `Path ${parseInt(name.replace('path', '')) + 1}`]}
                      />
                      <Legend formatter={(v: string) => `Path ${parseInt(v.replace('path', '')) + 1}`} />
                      {[0, 1, 2].map((i) => (
                        <Line
                          key={i}
                          type="monotone"
                          dataKey={`path${i}`}
                          stroke={PATH_COLORS[i]}
                          strokeWidth={1.5}
                          dot={false}
                        />
                      ))}
                    </LineChart>
                  </ResponsiveContainer>
                ) : (
                  <p className="text-sm text-gray-400 py-8 text-center">No path data available</p>
                )}
              </div>
            </div>
          )}

          {/* ============== Tab 2 – Heston ============== */}
          {activeTab === 'Heston' && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
                <MetricCard label="Simulated Paths" value={data.heston?.n_paths ?? '—'} />
                <MetricCard label="Trading Days" value={data.heston?.days ?? '—'} />
                <MetricCard label="Initial Vol (v₀)" value={data.heston?.v0 ?? '—'} />
                <MetricCard label="Long-Run Vol (θ)" value={data.heston?.theta ?? '—'} />
                <MetricCard label="Reversion Speed (κ)" value={data.heston?.kappa ?? '—'} />
                <MetricCard label="Vol of Vol (ξ)" value={data.heston?.xi ?? '—'} />
              </div>

              <div className="bg-white rounded-xl border border-gray-200 p-5">
                <h3 className="font-semibold text-cascade-charcoal mb-4">Asset Paths & Volatility (first 2 each)</h3>
                {hestonChartData.length > 0 ? (
                  <ResponsiveContainer width="100%" height={340}>
                    <LineChart data={hestonChartData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e5e5e5" />
                      <XAxis dataKey="day" tick={{ fontSize: 11 }} interval={Math.floor(hestonChartData.length / 8)} />
                      <YAxis yAxisId="price" tick={{ fontSize: 11 }} domain={['auto', 'auto']} />
                      <YAxis yAxisId="vol" orientation="right" tick={{ fontSize: 11 }} domain={['auto', 'auto']} />
                      <Tooltip
                        contentStyle={{ borderRadius: 8, fontSize: 12, border: '1px solid #e5e7eb' }}
                      />
                      <Legend />
                      <Line yAxisId="price" type="monotone" dataKey="asset0" stroke={COLORS[0]} strokeWidth={1.5} dot={false} name="Asset 1" />
                      <Line yAxisId="price" type="monotone" dataKey="asset1" stroke={COLORS[1]} strokeWidth={1.5} dot={false} name="Asset 2" />
                      <Line yAxisId="vol" type="monotone" dataKey="vol0" stroke={COLORS[2]} strokeWidth={1.5} dot={false} strokeDasharray="6 3" name="Vol 1" />
                      <Line yAxisId="vol" type="monotone" dataKey="vol1" stroke={COLORS[3]} strokeWidth={1.5} dot={false} strokeDasharray="6 3" name="Vol 2" />
                    </LineChart>
                  </ResponsiveContainer>
                ) : (
                  <p className="text-sm text-gray-400 py-8 text-center">No Heston data available</p>
                )}
              </div>
            </div>
          )}

          {/* ============== Tab 3 – Greeks ============== */}
          {activeTab === 'Greeks' && (
            <div className="space-y-4">
              <div className="bg-white rounded-xl border border-gray-200 p-5">
                <h3 className="font-semibold text-cascade-charcoal mb-4">Greeks Summary (ATM Call)</h3>
                {greeksBarData.length > 0 ? (
                  <ResponsiveContainer width="100%" height={240}>
                    <BarChart data={greeksBarData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e5e5e5" />
                      <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                      <YAxis tick={{ fontSize: 11 }} />
                      <Tooltip
                        contentStyle={{ borderRadius: 8, fontSize: 12, border: '1px solid #e5e7eb' }}
                        formatter={(v: number) => [v.toFixed(4), 'Value']}
                      />
                      <Bar dataKey="value" radius={[6, 6, 0, 0]}>
                        {greeksBarData.map((_, i) => (
                          <Cell key={i} fill={COLORS[i % COLORS.length]} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                ) : (
                  <p className="text-sm text-gray-400 py-8 text-center">No Greeks data available</p>
                )}
              </div>

              <div className="bg-white rounded-xl border border-gray-200 p-5">
                <h3 className="font-semibold text-cascade-charcoal mb-4">Delta Surface (Spot vs Delta)</h3>
                {deltaSurfaceData.length > 0 ? (
                  <ResponsiveContainer width="100%" height={280}>
                    <AreaChart data={deltaSurfaceData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e5e5e5" />
                      <XAxis
                        dataKey="spot"
                        tick={{ fontSize: 11 }}
                        tickFormatter={(v: number) => v.toFixed(0)}
                        interval={Math.floor(deltaSurfaceData.length / 8)}
                      />
                      <YAxis tick={{ fontSize: 11 }} domain={[0, 1]} />
                      <Tooltip
                        contentStyle={{ borderRadius: 8, fontSize: 12, border: '1px solid #e5e7eb' }}
                        formatter={(v: number, name: string) => [v.toFixed(4), name === 'delta' ? 'Delta' : name]}
                        labelFormatter={(l: number) => `Spot: ${l.toFixed(2)}`}
                      />
                      <Area
                        type="monotone"
                        dataKey="delta"
                        stroke={COLORS[0]}
                        fill={COLORS[0]}
                        fillOpacity={0.15}
                        strokeWidth={2}
                        name="Delta"
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                ) : (
                  <p className="text-sm text-gray-400 py-8 text-center">No delta surface data available</p>
                )}
              </div>
            </div>
          )}

          {/* ============== Tab 4 – Barrier ============== */}
          {activeTab === 'Barrier' && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
                <MetricCard label="Option Type" value={data.barrier?.option_type ?? '—'} />
                <MetricCard label="Barrier Level" value={data.barrier?.barrier_level ?? '—'} />
                <MetricCard label="Barrier Price" value={data.barrier?.price ?? '—'} />
                <MetricCard label="Vanilla Price" value={data.barrier?.vanilla_price ?? '—'} />
                <MetricCard label="Prob. Barrier Hit" value={data.barrier?.probability_hit ?? '—'} suffix="" />
                <MetricCard label="Std. Error" value={data.barrier?.std_error ?? '—'} />
              </div>

              {data.barrier && (
                <div className="bg-white rounded-xl border border-gray-200 p-5">
                  <h3 className="font-semibold text-cascade-charcoal mb-3">Barrier Option Summary</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="bg-gray-50 rounded-lg p-4">
                      <p className="text-xs text-gray-500 mb-1">Price Discount vs Vanilla</p>
                      {data.barrier.vanilla_price && data.barrier.price ? (
                        <p className="text-lg font-semibold text-cascade-gold">
                          {((1 - data.barrier.price / data.barrier.vanilla_price) * 100).toFixed(2)}%
                          <span className="text-xs text-gray-400 ml-1">cheaper</span>
                        </p>
                      ) : (
                        <p className="text-lg font-semibold text-gray-400">—</p>
                      )}
                    </div>
                    <div className="bg-gray-50 rounded-lg p-4">
                      <p className="text-xs text-gray-500 mb-1">Knock-Out Probability</p>
                      <p className="text-lg font-semibold text-red-600">
                        {typeof data.barrier.probability_hit === 'number'
                          ? (data.barrier.probability_hit * 100).toFixed(2) + '%'
                          : data.barrier.probability_hit ?? '—'}
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* ============== Tab 5 – Jump-Diffusion ============== */}
          {activeTab === 'Jump-Diffusion' && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
                <MetricCard label="Simulated Paths" value={data.jump_diffusion?.n_paths ?? '—'} />
                <MetricCard label="Trading Days" value={data.jump_diffusion?.days ?? '—'} />
                <MetricCard label="Jump Intensity (λ)" value={data.jump_diffusion?.jump_intensity ?? '—'} />
                <MetricCard label="Jump Mean (μⱼ)" value={data.jump_diffusion?.jump_mean ?? '—'} />
                <MetricCard label="Jump Std (σⱼ)" value={data.jump_diffusion?.jump_std ?? '—'} />
              </div>

              <div className="bg-white rounded-xl border border-gray-200 p-5">
                <h3 className="font-semibold text-cascade-charcoal mb-4">Jump-Diffusion vs Pure GBM (Average Paths)</h3>
                {jumpDiffChartData.length > 0 ? (
                  <ResponsiveContainer width="100%" height={340}>
                    <LineChart data={jumpDiffChartData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e5e5e5" />
                      <XAxis
                        dataKey="day"
                        tick={{ fontSize: 11 }}
                        interval={Math.floor(jumpDiffChartData.length / 8)}
                      />
                      <YAxis tick={{ fontSize: 11 }} domain={['auto', 'auto']} />
                      <Tooltip
                        contentStyle={{ borderRadius: 8, fontSize: 12, border: '1px solid #e5e7eb' }}
                        formatter={(v: number, name: string) => [v.toFixed(2), name === 'jump' ? 'Merton JD' : 'Pure GBM']}
                      />
                      <Legend formatter={(v: string) => (v === 'jump' ? 'Merton Jump-Diffusion' : 'Pure GBM')} />
                      <Line type="monotone" dataKey="jump" stroke={COLORS[0]} strokeWidth={2} dot={false} name="jump" />
                      <Line type="monotone" dataKey="gbm" stroke={COLORS[1]} strokeWidth={2} dot={false} strokeDasharray="6 3" name="gbm" />
                    </LineChart>
                  </ResponsiveContainer>
                ) : (
                  <p className="text-sm text-gray-400 py-8 text-center">No jump-diffusion data available</p>
                )}
              </div>
            </div>
          )}
        </>
      )}

      {/* Empty State */}
      {!data && !loading && !error && (
        <div className="text-center py-20 text-gray-400">
          <Activity size={48} className="mx-auto mb-4 opacity-30" />
          <p className="text-lg font-medium">No stochastic data yet</p>
          <p className="text-sm mt-1 mb-6">Click &quot;Load Demo&quot; to see Stochastic Calculus analysis</p>
          <button
            onClick={loadDemo}
            className="px-5 py-2.5 bg-cascade-gold text-white rounded-lg hover:bg-cascade-gold/90 inline-flex items-center gap-2 text-sm font-medium shadow-sm"
          >
            <Play size={16} /> Load Demo
          </button>
        </div>
      )}
    </div>
  );
}
