import { useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Cell, LineChart, Line } from 'recharts';
import { Scale, Loader2, AlertTriangle } from 'lucide-react';
import { getBlackLittermanDemo } from '../lib/api';
import type { BlackLittermanResult } from '../../types';

const ASSET_NAMES = ['Asset 1', 'Asset 2', 'Asset 3', 'Asset 4', 'Asset 5'];
const chartColors = ['#92761f', '#4e4732', '#1a1a19', '#a8a29e', '#78716c'];

export default function BlackLitterman() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState<BlackLittermanResult | null>(null);

  const runDemo = async () => {
    setLoading(true); setError('');
    try {
      const data = await getBlackLittermanDemo();
      setResult(data);
    } catch (e: any) { setError(e.message || 'Black-Litterman failed'); }
    finally { setLoading(false); }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 bg-cascade-gold/10 rounded-xl flex items-center justify-center">
          <Scale className="text-cascade-gold" size={20} />
        </div>
        <div>
          <h1 className="text-xl font-bold text-cascade-charcoal">Black-Litterman Model</h1>
          <p className="text-sm text-gray-500">Posterior Returns &amp; Portfolio Allocation</p>
        </div>
      </div>

      <button onClick={runDemo} disabled={loading} className="px-4 py-2 bg-cascade-gold text-white rounded-lg hover:bg-cascade-gold/90 disabled:opacity-50 flex items-center gap-2 text-sm font-medium">
        {loading ? <Loader2 className="animate-spin" size={16} /> : <Scale size={16} />} Run 5-Asset Demo (3 Views)
      </button>

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-xl flex items-start gap-3">
          <AlertTriangle className="text-red-500 shrink-0 mt-0.5" size={18} />
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}

      {result && !result.error && (
        <>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            <div className="bg-white rounded-xl border p-4">
              <p className="text-xs text-gray-500 mb-1">Expected Return</p>
              <p className="text-xl font-bold text-green-600">{result.portfolio_metrics.expected_return}%</p>
            </div>
            <div className="bg-white rounded-xl border p-4">
              <p className="text-xs text-gray-500 mb-1">Volatility</p>
              <p className="text-xl font-bold text-cascade-charcoal">{result.portfolio_metrics.volatility}%</p>
            </div>
            <div className="bg-white rounded-xl border p-4">
              <p className="text-xs text-gray-500 mb-1">Sharpe Ratio</p>
              <p className="text-xl font-bold text-cascade-gold">{result.portfolio_metrics.sharpe_ratio}</p>
            </div>
            <div className="bg-white rounded-xl border p-4">
              <p className="text-xs text-gray-500 mb-1">Tracking Error</p>
              <p className="text-xl font-bold text-cascade-charcoal">{result.portfolio_metrics.tracking_error}%</p>
            </div>
            <div className="bg-white rounded-xl border p-4">
              <p className="text-xs text-gray-500 mb-1">Info Ratio</p>
              <p className="text-xl font-bold text-cascade-gold">{result.portfolio_metrics.information_ratio}</p>
            </div>
          </div>

          {/* Weight Comparison Chart */}
          <div className="bg-white rounded-xl border p-5">
            <h3 className="font-semibold text-cascade-charcoal mb-4">Market vs. Posterior Weights</h3>
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={ASSET_NAMES.map((name, i) => ({
                name,
                market: (result.market_weights[i] || 0) * 100,
                posterior: (result.optimal_weights[i] || 0) * 100,
              }))}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e5e5" />
                <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                <YAxis tick={{ fontSize: 11 }} unit="%" />
                <Tooltip />
                <Bar dataKey="market" fill="#a8a29e" radius={[4, 4, 0, 0]} name="Market Weight" />
                <Bar dataKey="posterior" fill="#92761f" radius={[4, 4, 0, 0]} name="Posterior Weight" />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Return Changes Chart */}
          <div className="bg-white rounded-xl border p-5">
            <h3 className="font-semibold text-cascade-charcoal mb-4">Return Adjustments (Posterior - Equilibrium %)</h3>
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={ASSET_NAMES.map((name, i) => ({
                name,
                change: result.return_changes[i] || 0,
              }))}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e5e5" />
                <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                <YAxis tick={{ fontSize: 11 }} unit="%" />
                <Tooltip />
                <Bar dataKey="change" radius={[6, 6, 0, 0]}>
                  {result.return_changes.map((v, i) => (
                    <Cell key={i} fill={v >= 0 ? '#3c8855' : '#a9534b'} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Implied vs Posterior Returns */}
          <div className="bg-white rounded-xl border p-5">
            <h3 className="font-semibold text-cascade-charcoal mb-4">Implied vs. Posterior Returns</h3>
            <ResponsiveContainer width="100%" height={250}>
              <LineChart data={ASSET_NAMES.map((name, i) => ({
                name,
                implied: ((result.implied_equilibrium_returns[i] || 0) * 100).toFixed(2),
                posterior: ((result.posterior_returns[i] || 0) * 100).toFixed(2),
              }))}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e5e5" />
                <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                <YAxis tick={{ fontSize: 11 }} unit="%" />
                <Tooltip />
                <Line type="monotone" dataKey="implied" stroke="#a8a29e" strokeWidth={2} dot={{ r: 4 }} name="Equilibrium" />
                <Line type="monotone" dataKey="posterior" stroke="#92761f" strokeWidth={2} dot={{ r: 4 }} name="Posterior" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </>
      )}
    </div>
  );
}