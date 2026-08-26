import { useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Cell, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar } from 'recharts';
import { GitBranch, Loader2, AlertTriangle, Trophy, CheckCircle, XCircle } from 'lucide-react';
import { getFuzzyMCDMDemo } from '../lib/api';
import type { StockRankingResult } from '../../types';

export default function FuzzyMCDM() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState<StockRankingResult | null>(null);
  const [demoStocks, setDemoStocks] = useState<Record<string, any>[]>([]);

  const runDemo = async () => {
    setLoading(true); setError('');
    try {
      const data = await getFuzzyMCDMDemo();
      setDemoStocks(data.demo_stocks);
      setResult(data.analysis);
    } catch (e: any) { setError(e.message || 'Fuzzy MCDM failed'); }
    finally { setLoading(false); }
  };

  const chartColors = ['#92761f', '#4e4732', '#1a1a19', '#a8a29e', '#78716c', '#d4d4d4'];

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 bg-cascade-gold/10 rounded-xl flex items-center justify-center">
          <GitBranch className="text-cascade-gold" size={20} />
        </div>
        <div>
          <h1 className="text-xl font-bold text-cascade-charcoal">Fuzzy AHP-TOPSIS</h1>
          <p className="text-sm text-gray-500">Multi-Criteria Decision Making for Stock Ranking</p>
        </div>
      </div>

      <button onClick={runDemo} disabled={loading} className="px-4 py-2 bg-cascade-gold text-white rounded-lg hover:bg-cascade-gold/90 disabled:opacity-50 flex items-center gap-2 text-sm font-medium">
        {loading ? <Loader2 className="animate-spin" size={16} /> : <Trophy size={16} />} Rank TSE Stocks (Demo)
      </button>

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-xl flex items-start gap-3">
          <AlertTriangle className="text-red-500 shrink-0 mt-0.5" size={18} />
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}

      {result && !result.error && (
        <>
          {/* AHP Weights */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-white rounded-xl border p-4">
              <p className="text-xs text-gray-500 mb-1">Stocks Ranked</p>
              <p className="text-xl font-bold text-cascade-charcoal">{result.stocks_analyzed}</p>
            </div>
            <div className="bg-white rounded-xl border p-4">
              <p className="text-xs text-gray-500 mb-1">Criteria Used</p>
              <p className="text-xl font-bold text-cascade-charcoal">{result.criteria_used.length}</p>
            </div>
            <div className="bg-white rounded-xl border p-4">
              <p className="text-xs text-gray-500 mb-1">Best Stock</p>
              <p className="text-lg font-bold text-cascade-gold">{result.best_stock}</p>
            </div>
            <div className="bg-white rounded-xl border p-4">
              <p className="text-xs text-gray-500 mb-1">Consistency (CR)</p>
              <div className="flex items-center gap-2">
                <p className="text-xl font-bold">{result.consistency.cr}</p>
                {result.consistency.consistent ? (
                  <CheckCircle className="text-green-500" size={18} />
                ) : (
                  <XCircle className="text-red-500" size={18} />
                )}
              </div>
            </div>
          </div>

          {/* AHP Criteria Weights Chart */}
          <div className="bg-white rounded-xl border p-5">
            <h3 className="font-semibold text-cascade-charcoal mb-4">AHP Criteria Weights</h3>
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={result.ahp_ranking.map((r: any) => ({ name: r.name, weight: r.weight_pct }))} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e5e5" />
                <XAxis type="number" tick={{ fontSize: 11 }} unit="%" />
                <YAxis type="category" dataKey="name" tick={{ fontSize: 12 }} width={120} />
                <Tooltip />
                <Bar dataKey="weight" radius={[0, 6, 6, 0]}>
                  {result.ahp_ranking.map((_: any, i: number) => <Cell key={i} fill={chartColors[i % chartColors.length]} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* TOPSIS Ranking */}
          <div className="bg-white rounded-xl border p-5">
            <h3 className="font-semibold text-cascade-charcoal mb-4">TOPSIS Ranking (Closeness to Ideal)</h3>
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={result.topsis_ranking.map((r: any) => ({ name: r.name, score: r.closeness * 100 }))}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e5e5" />
                <XAxis dataKey="name" tick={{ fontSize: 10 }} angle={-20} textAnchor="end" height={60} />
                <YAxis tick={{ fontSize: 11 }} unit="%" />
                <Tooltip />
                <Bar dataKey="score" radius={[6, 6, 0, 0]}>
                  {result.topsis_ranking.map((_: any, i: number) => (
                    <Cell key={i} fill={i === 0 ? '#3c8855' : chartColors[(i + 1) % chartColors.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Criteria Radar */}
          {result.ahp_weights.length >= 3 && (
            <div className="bg-white rounded-xl border p-5">
              <h3 className="font-semibold text-cascade-charcoal mb-4">Criteria Importance Radar</h3>
              <ResponsiveContainer width="100%" height={300}>
                <RadarChart data={result.ahp_ranking.map((r: any) => ({ name: r.name, weight: r.weight_pct }))}>
                  <PolarGrid stroke="#e5e5e5" />
                  <PolarAngleAxis dataKey="name" tick={{ fontSize: 11 }} />
                  <PolarRadiusAxis tick={{ fontSize: 10 }} />
                  <Radar name="Weight %" dataKey="weight" stroke="#92761f" fill="#92761f" fillOpacity={0.3} />
                </RadarChart>
              </ResponsiveContainer>
            </div>
          )}
        </>
      )}
    </div>
  );
}