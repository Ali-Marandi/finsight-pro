import { useState, useEffect, useMemo } from 'react';
import { Brain, AlertCircle, Loader2, Activity, BarChart3, Target } from 'lucide-react';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend, Cell } from 'recharts';
import { getRLDemo } from '../lib/api';

const COLORS = ['#92761f', '#3b82f6', '#ef4444', '#10b981', '#8b5cf6', '#f59e0b'];

function MetricCard({ label, value, suffix = '' }: { label: string; value: string | number | null | undefined; suffix?: string }) {
  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4">
      <p className="text-xs text-gray-500 mb-1">{label}</p>
      <p className="text-lg font-semibold text-gray-900">{value ?? '—'}{suffix}</p>
    </div>
  );
}

function downsample(arr: number[], maxLen = 120): number[] {
  if (arr.length <= maxLen) return arr;
  const step = arr.length / maxLen;
  const result: number[] = [];
  for (let i = 0; i < maxLen; i++) result.push(arr[Math.floor(i * step)]);
  return result;
}

export default function ReinforcementLearning() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState(0);
  const tabs = ['Q-Learning Execution', 'TWAP / VWAP', 'Portfolio RL'];

  useEffect(() => { loadDemo(); }, []);

  async function loadDemo() {
    setLoading(true); setError(null);
    try {
      const r = await getRLDemo();
      setData(r); } catch (e: any) { setError(e.message || 'Failed to load RL demo'); }
    finally { setLoading(false); }
  }

  const ql = data?.q_learning_execution;
  const tv = data?.twap_vwap_strategy;
  const pr = data?.portfolio_rl_allocation;

  const executionChartData = useMemo(() => {
    if (!ql?.optimal_execution_schedule || !tv?.twap_schedule || !tv?.vwap_schedule) return [];
    const maxLen = Math.min(ql.optimal_execution_schedule.length || 0, tv.twap_schedule.length || 0, tv.vwap_schedule.length || 0, 120);
    const chartData: any[] = [];
    for (let i = 0; i < maxLen; i++) {
      chartData.push({
        step: i,
        rl: ql.optimal_execution_schedule[i]?.cumulative_executed ?? 0,
        twap: tv.twap_schedule[i]?.cumulative_executed ?? 0,
        vwap: tv.vwap_schedule[i]?.cumulative_executed ?? 0,
      });
    }
    return chartData;
  }, [ql, tv]);

  const sharpeData = useMemo(() => {
    if (!pr?.sharpe_comparison) return [];
    return [
      { name: 'Q-Learning RL', value: pr.sharpe_comparison.rl ?? pr.rl_performance?.sharpe_ratio ?? 0 },
      { name: 'Equal Weight', value: pr.sharpe_comparison.equal_weight ?? pr.equal_weight_performance?.sharpe_ratio ?? 0 },
      { name: 'Buy & Hold', value: pr.sharpe_comparison.buy_and_hold ?? pr.buy_and_hold_performance?.sharpe_ratio ?? 0 },
    ];
  }, [pr]);

  const returnData = useMemo(() => {
    if (!pr) return [];
    return [
      { name: 'Q-Learning RL', value: pr.rl_performance?.cumulative_return_pct ?? 0 },
      { name: 'Equal Weight', value: pr.equal_weight_performance?.cumulative_return_pct ?? 0 },
      { name: 'Buy & Hold', value: pr.buy_and_hold_performance?.cumulative_return_pct ?? 0 },
    ];
  }, [pr]);

  if (loading) return (
    <div className="flex items-center justify-center h-64"><Loader2 className="animate-spin text-cascade-gold" size={32} /></div>
  );

  if (error) return (
    <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start gap-3"><AlertCircle className="text-red-500 mt-0.5 shrink-0" size={20} /><div><p className="text-red-800 font-medium">Error</p><p className="text-red-600 text-sm">{error}</p></div></div>
  );

  return (
    <div className="space-y-6">
      {data?.demo_title && (
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
          <h3 className="text-sm font-semibold text-amber-900">{data.demo_title}</h3>
          <p className="text-xs text-amber-700 mt-1">{data.description}</p>
        </div>
      )}

      {/* Tab Switcher */}
      <div className="bg-gray-100 rounded-xl p-1 flex gap-1">
        {tabs.map((tab, i) => (
          <button key={tab} onClick={() => setActiveTab(i)} className={`flex-1 py-2 px-3 rounded-lg text-sm font-medium transition-colors ${activeTab === i ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500 hover:text-gray-700'}`}>{tab}</button>
        ))}
      </div>

      {/* Tab 0: Q-Learning Execution */}
      {activeTab === 0 && ql && (
        <div className="space-y-4">
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-3">
            <MetricCard label="Total Shares" value={data?.intraday_execution_summary?.base_price ? '100,000' : ql?.total_shares} />
            <MetricCard label="Steps" value={data?.intraday_execution_summary?.n_steps ?? ql?.n_steps} />
            <MetricCard label="Episodes" value={ql?.q_table_summary?.total_entries ? '500' : '—'} />
            <MetricCard label="RL Avg Price" value={ql?.slippage_comparison?.rl_avg_price ?? '—'} />
            <MetricCard label="TWAP Avg" value={ql?.slippage_comparison?.twap_avg_price ?? tv?.twap_avg_price} />
            <MetricCard label="VWAP Avg" value={ql?.slippage_comparison?.vwap_avg_price ?? tv?.vwap_avg_price} />
            <MetricCard label="RL Slippage" value={ql?.slippage_comparison?.rl_slippage_vs_vwap_pct ?? '—'} suffix=" %" />
          </div>
          {executionChartData.length > 0 && (
            <div className="bg-white rounded-lg border border-gray-200 p-4">
              <h4 className="text-sm font-medium text-gray-700 mb-3">Cumulative Execution Comparison</h4>
              <ResponsiveContainer width="100%" height={320}><LineChart data={executionChartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" /><XAxis dataKey="step" tick={{ fontSize: 11 }} /><YAxis tick={{ fontSize: 11 }} /><Tooltip />
                <Legend /><Line type="monotone" dataKey="rl" name="Q-Learning" stroke="#92761f" dot={false} strokeWidth={2} />
                <Line type="monotone" dataKey="twap" name="TWAP" stroke="#3b82f6" dot={false} strokeWidth={2} />
                <Line type="monotone" dataKey="vwap" name="VWAP" stroke="#10b981" dot={false} strokeWidth={2} />
              </LineChart></ResponsiveContainer>
            </div>
          )}
          {ql?.q_table_summary && (
            <div className="bg-white rounded-lg border border-gray-200 p-4">
              <h4 className="text-sm font-medium text-gray-700 mb-3">Q-Table Summary</h4>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                <MetricCard label="Non-Zero Entries" value={ql.q_table_summary.non_zero_entries} />
                <MetricCard label="Total Entries" value={ql.q_table_summary.total_entries} />
                <MetricCard label="Mean Q-Value" value={ql.q_table_summary.mean_q_value} />
                <MetricCard label="Max Q-Value" value={ql.q_table_summary.max_q_value} />
              </div>
            </div>
          )}
        </div>
      )}

      {/* Tab 1: TWAP/VWAP */}
      {activeTab === 1 && tv && (
        <div className="space-y-4">
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
            <MetricCard label="Total Shares" value="100,000" />
            <MetricCard label="Steps" value={tv?.n_steps ?? data?.intraday_execution_summary?.n_steps} />
            <MetricCard label="TWAP Avg Price" value={tv?.twap_avg_price} />
            <MetricCard label="VWAP Avg Price" value={tv?.vwap_avg_price} />
            <MetricCard label="TWAP Slippage" value={tv?.twap_slippage_vs_ideal_pct} suffix=" %" />
            <MetricCard label="VWAP Slippage" value={tv?.vwap_slippage_vs_ideal_pct} suffix=" %" />
          </div>
          <div className="bg-white rounded-lg border border-gray-200 p-4">
            <h4 className="text-sm font-medium text-gray-700 mb-3">Slippage Comparison</h4>
            <ResponsiveContainer width="100%" height={280}><BarChart data={[
              { name: 'TWAP', slippage: tv?.twap_slippage_vs_ideal_pct ?? 0 },
              { name: 'VWAP', slippage: tv?.vwap_slippage_vs_ideal_pct ?? 0 },
            ]}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" /><XAxis dataKey="name" tick={{ fontSize: 12 }} /><YAxis tick={{ fontSize: 11 }} /><Tooltip />
              <Bar dataKey="slippage" name="Slippage %" radius={[4, 4, 0, 0]}>
                <Cell fill="#3b82f6" /><Cell fill="#10b981" />
              </Bar>
            </BarChart></ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Tab 2: Portfolio RL */}
      {activeTab === 2 && pr && (
        <div className="space-y-4">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <MetricCard label="Assets" value={data?.asset_names?.length ?? pr?.parameters?.n_assets} />
            <MetricCard label="Episodes" value={pr?.parameters?.episodes} />
            <MetricCard label="RL Sharpe" value={pr?.rl_performance?.sharpe_ratio} />
            <MetricCard label="EW Sharpe" value={pr?.equal_weight_performance?.sharpe_ratio} />
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-white rounded-lg border border-gray-200 p-4">
              <h4 className="text-sm font-medium text-gray-700 mb-3">Sharpe Ratio Comparison</h4>
              <ResponsiveContainer width="100%" height={260}><BarChart data={sharpeData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" /><XAxis dataKey="name" tick={{ fontSize: 11 }} /><YAxis tick={{ fontSize: 11 }} /><Tooltip />
                <Bar dataKey="value" name="Sharpe Ratio" radius={[4, 4, 0, 0]}>
                  {sharpeData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                </Bar>
              </BarChart></ResponsiveContainer>
            </div>
            <div className="bg-white rounded-lg border border-gray-200 p-4">
              <h4 className="text-sm font-medium text-gray-700 mb-3">Cumulative Return %</h4>
              <ResponsiveContainer width="100%" height={260}><BarChart data={returnData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" /><XAxis dataKey="name" tick={{ fontSize: 11 }} /><YAxis tick={{ fontSize: 11 }} /><Tooltip />
                <Bar dataKey="value" name="Return %" radius={[4, 4, 0, 0]}>
                  {returnData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                </Bar>
              </BarChart></ResponsiveContainer>
            </div>
          </div>
          {pr?.rl_performance && (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <MetricCard label="RL Return" value={pr.rl_performance.cumulative_return_pct} suffix=" %" />
              <MetricCard label="RL Max DD" value={pr.rl_performance.max_drawdown_pct} suffix=" %" />
              <MetricCard label="RL Volatility" value={pr.rl_performance.annualized_volatility_pct} suffix=" %" />
              <MetricCard label="RL Calmar" value={pr.rl_performance.calmar_ratio} />
            </div>
          )}
        </div>
      )}

      {/* Empty State */}
      {!data && !loading && !error && (
        <div className="flex flex-col items-center justify-center h-64 text-gray-400">
          <Brain size={48} className="mb-3" /><p className="text-sm">Click below to load Reinforcement Learning demo</p>
          <button onClick={loadDemo} className="mt-3 px-4 py-2 bg-cascade-gold text-white rounded-lg text-sm hover:bg-cascade-gold/90">Load Demo</button>
        </div>
      )}
    </div>
  );
}