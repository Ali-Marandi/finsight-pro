import { useState } from 'react';
import {
  LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid,
  BarChart, Bar, Cell, AreaChart, Area,
} from 'recharts';
import { Play, Loader2, AlertTriangle, Target, TrendingDown, Trophy, BarChart3, Activity } from 'lucide-react';
import { getBacktestDemo } from '../lib/api';
import type { BacktestDemoResult } from '../../types';

type Tab = 'strategy' | 'portfolio';

const CASCADE = {
  gold: '#92761f',
  charcoal: '#1a1a19',
  stone: '#fafaf9',
  dark: '#4e4732',
  gray: '#a8a29e',
  green: '#16a34a',
  red: '#dc2626',
  blue: '#2563eb',
  amber: '#d97706',
};

export default function Backtest() {
  const [tab, setTab] = useState<Tab>('strategy');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [demoData, setDemoData] = useState<BacktestDemoResult | null>(null);

  const runDemo = async () => {
    setLoading(true); setError('');
    try {
      setDemoData(await getBacktestDemo());
    } catch (e: any) { setError(e.message || 'Backtest demo failed'); }
    finally { setLoading(false); }
  };

  const single = demoData?.single_asset;
  const portfolio = demoData?.portfolio;

  const tabs: { id: Tab; label: string; icon: typeof Target }[] = [
    { id: 'strategy', label: 'Strategy Backtest', icon: Target },
    { id: 'portfolio', label: 'Portfolio Backtest', icon: BarChart3 },
  ];

  // Build equity chart data
  const buildEquityData = (
    equityCurve: number[],
    benchmarkCurve: number[] | null | undefined,
  ) => {
    return equityCurve.map((v, i) => ({
      day: i,
      strategy: v,
      benchmark: benchmarkCurve ? benchmarkCurve[i] : undefined,
    }));
  };

  // Build drawdown data
  const buildDrawdownData = (ddSeries: number[]) => {
    return ddSeries.map((v, i) => ({ day: i, drawdown: v }));
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-cascade-gold/10 rounded-xl flex items-center justify-center">
            <Activity className="text-cascade-gold" size={20} />
          </div>
          <div>
            <h1 className="text-xl font-bold text-cascade-charcoal">Backtesting Engine</h1>
            <p className="text-sm text-gray-500">Strategy simulation, performance metrics & risk analysis</p>
          </div>
        </div>
        <button
          onClick={runDemo}
          disabled={loading}
          className="px-5 py-2.5 bg-cascade-gold text-white rounded-lg hover:bg-cascade-gold/90 disabled:opacity-50 flex items-center gap-2 text-sm font-medium shadow-sm"
        >
          {loading ? <Loader2 className="animate-spin" size={16} /> : <Play size={16} />}
          Run Demo (5 TSE Stocks)
        </button>
      </div>

      {/* Tab Navigation */}
      <div className="flex gap-1 bg-gray-100 rounded-xl p-1">
        {tabs.map(t => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={`flex-1 flex items-center justify-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-all ${
              tab === t.id ? 'bg-white text-cascade-charcoal shadow-sm' : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            <t.icon size={15} /> {t.label}
          </button>
        ))}
      </div>

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-xl flex items-start gap-3">
          <AlertTriangle className="text-red-500 shrink-0 mt-0.5" size={18} />
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}

      {/* Demo Info Banner */}
      {demoData && (
        <div className="bg-cascade-gold/5 border border-cascade-gold/20 rounded-xl p-4">
          <p className="text-sm text-cascade-dark font-medium">{demoData.demo_info.description}</p>
          <p className="text-xs text-gray-500 mt-1">
            Assets: {demoData.demo_info.assets.join(', ')} ({demoData.demo_info.assets_fa.join(', ')})
            {' | '}{demoData.demo_info.period_days} trading days
          </p>
        </div>
      )}

      {/* ========== STRATEGY TAB ========== */}
      {tab === 'strategy' && single && !single.error && (
        <div className="space-y-5">
          {/* Performance Metrics */}
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
            <MetricCard label="Total Return" value={`${single.performance.total_return_pct}%`} color={single.performance.total_return_pct >= 0 ? 'text-green-600' : 'text-red-600'} />
            <MetricCard label="CAGR" value={`${single.performance.cagr_pct}%`} color={single.performance.cagr_pct >= 0 ? 'text-green-600' : 'text-red-600'} />
            <MetricCard label="Sharpe Ratio" value={single.risk.sharpe_ratio.toString()} color={single.risk.sharpe_ratio >= 1 ? 'text-green-600' : single.risk.sharpe_ratio >= 0 ? 'text-amber-600' : 'text-red-600'} />
            <MetricCard label="Sortino Ratio" value={single.risk.sortino_ratio.toString()} color={single.risk.sortino_ratio >= 1.5 ? 'text-green-600' : 'text-amber-600'} />
            <MetricCard label="Max Drawdown" value={`${single.risk.max_drawdown_pct}%`} color="text-red-600" />
            <MetricCard label="Calmar Ratio" value={single.risk.calmar_ratio.toString()} color={single.risk.calmar_ratio >= 1 ? 'text-green-600' : 'text-amber-600'} />
          </div>

          {/* Risk + Trade Stats Row */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
            <MetricCard label="Win Rate" value={`${single.trades.win_rate}%`} icon={<Trophy size={14} className="text-cascade-gold" />} />
            <MetricCard label="Profit Factor" value={single.trades.profit_factor.toString()} />
            <MetricCard label="Total Trades" value={single.trades.total.toString()} />
            <MetricCard label="VaR (95%)" value={`${single.risk.var_95_pct}%`} color="text-red-600" />
          </div>

          {/* Capital Info */}
          <div className="grid grid-cols-3 gap-3">
            <div className="bg-white rounded-xl border p-4">
              <p className="text-xs text-gray-500 mb-1">Initial Capital</p>
              <p className="text-lg font-bold text-cascade-charcoal">${single.capital.initial.toLocaleString()}</p>
            </div>
            <div className="bg-white rounded-xl border p-4">
              <p className="text-xs text-gray-500 mb-1">Final Value</p>
              <p className="text-lg font-bold text-cascade-charcoal">${single.capital.final.toLocaleString()}</p>
            </div>
            <div className="bg-white rounded-xl border p-4">
              <p className="text-xs text-gray-500 mb-1">Period</p>
              <p className="text-lg font-bold text-cascade-charcoal">{single.period.years} years ({single.period.days} days)</p>
            </div>
          </div>

          {/* Benchmark Comparison */}
          {single.benchmark && (
            <div className="bg-white rounded-xl border p-5">
              <h3 className="font-semibold text-cascade-charcoal mb-4 flex items-center gap-2">
                <BarChart3 size={16} className="text-cascade-gold" />
                Benchmark Comparison
              </h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                <div className="bg-gray-50 rounded-lg p-3">
                  <p className="text-xs text-gray-500">Excess Return</p>
                  <p className={`text-lg font-bold ${single.benchmark.excess_return_pct >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {single.benchmark.excess_return_pct >= 0 ? '+' : ''}{single.benchmark.excess_return_pct}%
                  </p>
                </div>
                <div className="bg-gray-50 rounded-lg p-3">
                  <p className="text-xs text-gray-500">Alpha</p>
                  <p className={`text-lg font-bold ${single.benchmark.alpha_pct >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {single.benchmark.alpha_pct >= 0 ? '+' : ''}{single.benchmark.alpha_pct}%
                  </p>
                </div>
                <div className="bg-gray-50 rounded-lg p-3">
                  <p className="text-xs text-gray-500">Beta</p>
                  <p className="text-lg font-bold text-cascade-charcoal">{single.benchmark.beta}</p>
                </div>
                <div className="bg-gray-50 rounded-lg p-3">
                  <p className="text-xs text-gray-500">Info Ratio</p>
                  <p className="text-lg font-bold text-cascade-charcoal">{single.benchmark.information_ratio}</p>
                </div>
                <div className="bg-gray-50 rounded-lg p-3">
                  <p className="text-xs text-gray-500">Benchmark Return</p>
                  <p className="text-lg font-bold text-cascade-charcoal">{single.benchmark.total_return_pct}%</p>
                </div>
                <div className="bg-gray-50 rounded-lg p-3">
                  <p className="text-xs text-gray-500">Benchmark Sharpe</p>
                  <p className="text-lg font-bold text-cascade-charcoal">{single.benchmark.sharpe}</p>
                </div>
                <div className="bg-gray-50 rounded-lg p-3">
                  <p className="text-xs text-gray-500">Tracking Error</p>
                  <p className="text-lg font-bold text-cascade-charcoal">{single.benchmark.tracking_error_pct}%</p>
                </div>
                <div className="bg-gray-50 rounded-lg p-3">
                  <p className="text-xs text-gray-500">Benchmark CAGR</p>
                  <p className="text-lg font-bold text-cascade-charcoal">{single.benchmark.cagr_pct}%</p>
                </div>
              </div>
            </div>
          )}

          {/* Equity Curve Chart */}
          <div className="bg-white rounded-xl border p-5">
            <h3 className="font-semibold text-cascade-charcoal mb-4">Equity Curve</h3>
            <ResponsiveContainer width="100%" height={320}>
              <LineChart data={buildEquityData(single.charts.equity_curve, single.charts.benchmark_curve)}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e5e5" />
                <XAxis dataKey="day" tick={{ fontSize: 11 }} interval={Math.floor(single.charts.equity_curve.length / 8)} />
                <YAxis tick={{ fontSize: 11 }} tickFormatter={(v: number) => `$${(v / 1000).toFixed(0)}k`} />
                <Tooltip formatter={(v: number) => [`$${v.toLocaleString()}`, undefined]} />
                <Line type="monotone" dataKey="benchmark" stroke={CASCADE.gray} strokeWidth={1.5} dot={false} strokeDasharray="5 3" name="Benchmark" />
                <Line type="monotone" dataKey="strategy" stroke={CASCADE.gold} strokeWidth={2} dot={false} name={single.strategy_name} />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* Drawdown Chart */}
          <div className="bg-white rounded-xl border p-5">
            <h3 className="font-semibold text-cascade-charcoal mb-4 flex items-center gap-2">
              <TrendingDown size={16} className="text-red-500" />
              Drawdown
            </h3>
            <ResponsiveContainer width="100%" height={200}>
              <AreaChart data={buildDrawdownData(single.charts.drawdown_series)}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e5e5" />
                <XAxis dataKey="day" tick={{ fontSize: 11 }} interval={Math.floor(single.charts.drawdown_series.length / 8)} />
                <YAxis tick={{ fontSize: 11 }} unit="%" />
                <Tooltip formatter={(v: number) => [`${v}%`, 'Drawdown']} />
                <defs>
                  <linearGradient id="ddGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#dc2626" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#dc2626" stopOpacity={0.02} />
                  </linearGradient>
                </defs>
                <Area type="monotone" dataKey="drawdown" stroke="#dc2626" strokeWidth={1.5} fill="url(#ddGradient)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>

          {/* Trade Log */}
          {single.trade_log.length > 0 && (
            <div className="bg-white rounded-xl border p-5">
              <h3 className="font-semibold text-cascade-charcoal mb-4">Recent Trades (Last {single.trade_log.length})</h3>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b text-gray-500 text-left">
                      <th className="py-2 pr-3 font-medium">Day</th>
                      <th className="py-2 pr-3 font-medium">Action</th>
                      <th className="py-2 pr-3 font-medium">Price</th>
                      <th className="py-2 pr-3 font-medium">Shares</th>
                      <th className="py-2 font-medium">P&L</th>
                    </tr>
                  </thead>
                  <tbody>
                    {single.trade_log.map((t, i) => (
                      <tr key={i} className="border-b last:border-0">
                        <td className="py-2 pr-3 text-gray-600">{t.day}</td>
                        <td className="py-2 pr-3">
                          <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                            t.action === 'BUY' ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'
                          }`}>
                            {t.action}
                          </span>
                        </td>
                        <td className="py-2 pr-3 text-gray-700">${t.price.toLocaleString()}</td>
                        <td className="py-2 pr-3 text-gray-700">{t.shares.toLocaleString()}</td>
                        <td className={`py-2 font-medium ${t.pnl > 0 ? 'text-green-600' : t.pnl < 0 ? 'text-red-600' : 'text-gray-500'}`}>
                          {t.pnl > 0 ? '+' : ''}{t.pnl !== 0 ? `$${t.pnl.toLocaleString()}` : '-'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}

      {/* ========== PORTFOLIO TAB ========== */}
      {tab === 'portfolio' && portfolio && !portfolio.error && (
        <div className="space-y-5">
          {/* Performance Metrics */}
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
            <MetricCard label="Total Return" value={`${portfolio.performance.total_return_pct}%`} color={portfolio.performance.total_return_pct >= 0 ? 'text-green-600' : 'text-red-600'} />
            <MetricCard label="CAGR" value={`${portfolio.performance.cagr_pct}%`} color={portfolio.performance.cagr_pct >= 0 ? 'text-green-600' : 'text-red-600'} />
            <MetricCard label="Sharpe Ratio" value={portfolio.risk.sharpe_ratio.toString()} color={portfolio.risk.sharpe_ratio >= 1 ? 'text-green-600' : 'text-amber-600'} />
            <MetricCard label="Sortino Ratio" value={portfolio.risk.sortino_ratio.toString()} />
            <MetricCard label="Max Drawdown" value={`${portfolio.risk.max_drawdown_pct}%`} color="text-red-600" />
            <MetricCard label="Calmar Ratio" value={portfolio.risk.calmar_ratio.toString()} />
          </div>

          {/* Capital + Rebalance Info */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <div className="bg-white rounded-xl border p-4">
              <p className="text-xs text-gray-500 mb-1">Initial Capital</p>
              <p className="text-lg font-bold text-cascade-charcoal">${portfolio.capital.initial.toLocaleString()}</p>
            </div>
            <div className="bg-white rounded-xl border p-4">
              <p className="text-xs text-gray-500 mb-1">Final Value</p>
              <p className="text-lg font-bold text-cascade-charcoal">${portfolio.capital.final.toLocaleString()}</p>
            </div>
            <div className="bg-white rounded-xl border p-4">
              <p className="text-xs text-gray-500 mb-1">Assets</p>
              <p className="text-lg font-bold text-cascade-charcoal">{portfolio.num_assets}</p>
            </div>
            <div className="bg-white rounded-xl border p-4">
              <p className="text-xs text-gray-500 mb-1">Rebalance</p>
              <p className="text-lg font-bold text-cascade-charcoal">Every {portfolio.rebalance_days} days</p>
            </div>
          </div>

          {/* Portfolio Weights Bar Chart */}
          <div className="bg-white rounded-xl border p-5">
            <h3 className="font-semibold text-cascade-charcoal mb-4">Portfolio Allocation</h3>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={portfolio.assets.map((a, i) => ({ name: a.name, weight: a.weight_pct, return: a.total_return_pct }))}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e5e5" />
                <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} unit="%" />
                <Tooltip />
                <Bar dataKey="weight" radius={[6, 6, 0, 0]} name="Weight %">
                  {portfolio.assets.map((_, i) => (
                    <Cell key={i} fill={[CASCADE.gold, CASCADE.dark, CASCADE.charcoal, CASCADE.gray, CASCADE.amber][i % 5]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Per-Asset Performance Table */}
          <div className="bg-white rounded-xl border p-5">
            <h3 className="font-semibold text-cascade-charcoal mb-4">Per-Asset Performance</h3>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b text-gray-500 text-left">
                    <th className="py-2 pr-3 font-medium">Asset</th>
                    <th className="py-2 pr-3 font-medium">Weight</th>
                    <th className="py-2 pr-3 font-medium">Return</th>
                    <th className="py-2 font-medium">Volatility</th>
                  </tr>
                </thead>
                <tbody>
                  {portfolio.assets.map((a, i) => (
                    <tr key={i} className="border-b last:border-0">
                      <td className="py-2.5 pr-3 font-medium text-cascade-charcoal">{a.name}</td>
                      <td className="py-2.5 pr-3 text-gray-600">{a.weight_pct}%</td>
                      <td className={`py-2.5 pr-3 font-medium ${a.total_return_pct >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                        {a.total_return_pct >= 0 ? '+' : ''}{a.total_return_pct}%
                      </td>
                      <td className="py-2.5 text-gray-600">{a.volatility_pct}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Benchmark Comparison */}
          {portfolio.benchmark && (
            <div className="grid grid-cols-2 gap-3">
              <div className="bg-white rounded-xl border p-4">
                <p className="text-xs text-gray-500 mb-1">Benchmark Return</p>
                <p className="text-lg font-bold text-cascade-charcoal">{portfolio.benchmark.total_return_pct}%</p>
              </div>
              <div className="bg-white rounded-xl border p-4">
                <p className="text-xs text-gray-500 mb-1">Excess Return</p>
                <p className={`text-lg font-bold ${portfolio.benchmark.excess_return_pct >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {portfolio.benchmark.excess_return_pct >= 0 ? '+' : ''}{portfolio.benchmark.excess_return_pct}%
                </p>
              </div>
            </div>
          )}

          {/* Equity Curve */}
          <div className="bg-white rounded-xl border p-5">
            <h3 className="font-semibold text-cascade-charcoal mb-4">Portfolio Equity Curve</h3>
            <ResponsiveContainer width="100%" height={320}>
              <LineChart data={buildEquityData(portfolio.charts.equity_curve, portfolio.charts.benchmark_curve)}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e5e5" />
                <XAxis dataKey="day" tick={{ fontSize: 11 }} interval={Math.floor(portfolio.charts.equity_curve.length / 8)} />
                <YAxis tick={{ fontSize: 11 }} tickFormatter={(v: number) => `$${(v / 1_000_000).toFixed(1)}M`} />
                <Tooltip formatter={(v: number) => [`$${v.toLocaleString()}`, undefined]} />
                <Line type="monotone" dataKey="benchmark" stroke={CASCADE.gray} strokeWidth={1.5} dot={false} strokeDasharray="5 3" name="Benchmark" />
                <Line type="monotone" dataKey="strategy" stroke={CASCADE.gold} strokeWidth={2} dot={false} name="Portfolio" />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* Drawdown */}
          <div className="bg-white rounded-xl border p-5">
            <h3 className="font-semibold text-cascade-charcoal mb-4 flex items-center gap-2">
              <TrendingDown size={16} className="text-red-500" />
              Portfolio Drawdown
            </h3>
            <ResponsiveContainer width="100%" height={200}>
              <AreaChart data={buildDrawdownData(portfolio.charts.drawdown_series)}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e5e5" />
                <XAxis dataKey="day" tick={{ fontSize: 11 }} interval={Math.floor(portfolio.charts.drawdown_series.length / 8)} />
                <YAxis tick={{ fontSize: 11 }} unit="%" />
                <Tooltip formatter={(v: number) => [`${v}%`, 'Drawdown']} />
                <defs>
                  <linearGradient id="ddGradientPort" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#dc2626" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#dc2626" stopOpacity={0.02} />
                  </linearGradient>
                </defs>
                <Area type="monotone" dataKey="drawdown" stroke="#dc2626" strokeWidth={1.5} fill="url(#ddGradientPort)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Empty State */}
      {!demoData && !loading && !error && (
        <div className="text-center py-16 text-gray-400">
          <Activity size={48} className="mx-auto mb-4 opacity-30" />
          <p className="text-lg font-medium">No backtest results yet</p>
          <p className="text-sm mt-1">Click "Run Demo" to see a sample backtest with 5 TSE stocks</p>
        </div>
      )}
    </div>
  );
}

function MetricCard({ label, value, color = 'text-cascade-charcoal', icon }: {
  label: string;
  value: string;
  color?: string;
  icon?: React.ReactNode;
}) {
  return (
    <div className="bg-white rounded-xl border p-4">
      <p className="text-xs text-gray-500 mb-1 flex items-center gap-1">
        {icon} {label}
      </p>
      <p className={`text-xl font-bold ${color}`}>{value}</p>
    </div>
  );
}
