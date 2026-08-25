import { useState } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid,
  LineChart, Line, Cell, PieChart, Pie,
} from 'recharts';
import { Heart, Loader2, AlertTriangle, TrendingUp, TrendingDown, Minus, Play } from 'lucide-react';
import { getSentimentDemo } from '../lib/api';
import type { SentimentDemoResult } from '../../types';

const SIGNAL_COLORS: Record<string, string> = {
  bullish: '#16a34a',
  bearish: '#dc2626',
  neutral: '#a8a29e',
};

const SIGNAL_BG: Record<string, string> = {
  bullish: 'bg-green-50 text-green-700 border-green-200',
  bearish: 'bg-red-50 text-red-700 border-red-200',
  neutral: 'bg-gray-50 text-gray-700 border-gray-200',
};

export default function Sentiment() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [data, setData] = useState<SentimentDemoResult | null>(null);

  const runDemo = async () => {
    setLoading(true); setError('');
    try { setData(await getSentimentDemo()); }
    catch (e: any) { setError(e.message || 'Sentiment demo failed'); }
    finally { setLoading(false); }
  };

  const overall = data?.market_overall;
  const dist = data?.market_distribution;
  const timeline = data?.score_timeline || [];
  const stocks = data?.per_stock || [];
  const kw = data?.market_keywords;

  const pieData = dist ? [
    { name: 'مثبت', value: dist.positive, fill: '#16a34a' },
    { name: 'منفی', value: dist.negative, fill: '#dc2626' },
    { name: 'خنثی', value: dist.neutral, fill: '#a8a29e' },
  ] : [];

  const timelineChartData = timeline.map((s, i) => ({ idx: i + 1, score: s }));

  const stockBarData = stocks.map(s => ({
    name: s.symbol,
    score: Math.round(s.score * 100),
    signal: s.signal,
  }));

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-cascade-gold/10 rounded-xl flex items-center justify-center">
            <Heart className="text-cascade-gold" size={20} />
          </div>
          <div>
            <h1 className="text-xl font-bold text-cascade-charcoal">Sentiment Analysis</h1>
            <p className="text-sm text-gray-500">NLP-based news & social media sentiment for TSE</p>
          </div>
        </div>
        <button onClick={runDemo} disabled={loading}
          className="px-5 py-2.5 bg-cascade-gold text-white rounded-lg hover:bg-cascade-gold/90 disabled:opacity-50 flex items-center gap-2 text-sm font-medium shadow-sm">
          {loading ? <Loader2 className="animate-spin" size={16} /> : <Play size={16} />}
          Run Demo (TSE News)
        </button>
      </div>

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-xl flex items-start gap-3">
          <AlertTriangle className="text-red-500 shrink-0 mt-0.5" size={18} />
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}

      {data && (
        <>
          {/* Demo Info */}
          <div className="bg-cascade-gold/5 border border-cascade-gold/20 rounded-xl p-4">
            <p className="text-sm text-cascade-dark font-medium">{data.demo_info.description}</p>
            <p className="text-xs text-gray-500 mt-1">
              {data.demo_info.news_count} news + {data.demo_info.social_count} social posts | Stocks: {data.demo_info.stocks_analyzed.join(', ')}
            </p>
          </div>

          {/* Overall Sentiment + Distribution */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Score Card */}
            <div className="bg-white rounded-xl border p-5 text-center">
              <p className="text-xs text-gray-500 mb-2">Market Sentiment Score</p>
              <p className={`text-4xl font-bold ${overall?.label === 'positive' ? 'text-green-600' : overall?.label === 'negative' ? 'text-red-600' : 'text-gray-600'}`}>
                {overall?.score !== undefined ? (overall.score > 0 ? '+' : '') + (overall.score * 100).toFixed(1) : '—'}
              </p>
              <div className={`inline-flex items-center gap-1 mt-2 px-3 py-1 rounded-full text-xs font-medium border ${SIGNAL_BG[overall?.label || 'neutral']}`}>
                {overall?.label === 'positive' ? <TrendingUp size={12} /> : overall?.label === 'negative' ? <TrendingDown size={12} /> : <Minus size={12} />}
                {overall?.label || 'neutral'}
              </div>
            </div>

            {/* Distribution Pie */}
            <div className="bg-white rounded-xl border p-5">
              <p className="text-xs text-gray-500 mb-2 font-medium">Sentiment Distribution</p>
              <ResponsiveContainer width="100%" height={140}>
                <PieChart>
                  <Pie data={pieData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={55} innerRadius={30}>
                    {pieData.map((entry, i) => <Cell key={i} fill={entry.fill} />)}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
              <div className="flex justify-center gap-4 mt-1 text-xs">
                <span className="flex items-center gap-1"><span className="w-2 h-2 bg-green-600 rounded-full" /> مثبت {overall?.positive_pct}%</span>
                <span className="flex items-center gap-1"><span className="w-2 h-2 bg-red-600 rounded-full" /> منفی {overall?.negative_pct}%</span>
                <span className="flex items-center gap-1"><span className="w-2 h-2 bg-gray-400 rounded-full" /> خنثی {overall?.neutral_pct}%</span>
              </div>
            </div>

            {/* Top Keywords */}
            <div className="bg-white rounded-xl border p-5">
              <p className="text-xs text-gray-500 mb-2 font-medium">Top Keywords</p>
              <div className="space-y-2">
                <div>
                  <p className="text-xs text-green-600 font-medium mb-1">Positive</p>
                  <div className="flex flex-wrap gap-1">
                    {kw?.positive.slice(0, 6).map((w, i) => (
                      <span key={i} className="px-2 py-0.5 bg-green-50 text-green-700 rounded text-xs">{w}</span>
                    ))}
                  </div>
                </div>
                <div>
                  <p className="text-xs text-red-600 font-medium mb-1">Negative</p>
                  <div className="flex flex-wrap gap-1">
                    {kw?.negative.slice(0, 6).map((w, i) => (
                      <span key={i} className="px-2 py-0.5 bg-red-50 text-red-700 rounded text-xs">{w}</span>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Sentiment Timeline */}
          <div className="bg-white rounded-xl border p-5">
            <h3 className="font-semibold text-cascade-charcoal mb-4">Sentiment Timeline (per news article)</h3>
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={timelineChartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e5e5" />
                <XAxis dataKey="idx" tick={{ fontSize: 11 }} label={{ value: 'Article #', position: 'insideBottom', offset: -5, fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} domain={[-1, 1]} tickFormatter={(v: number) => (v > 0 ? '+' : '') + (v * 100).toFixed(0) + '%'} />
                <Tooltip formatter={(v: number) => [(v * 100).toFixed(1) + '%', 'Sentiment']} />
                <Bar dataKey="score" radius={[4, 4, 0, 0]}>
                  {timelineChartData.map((entry, i) => (
                    <Cell key={i} fill={entry.score > 0.1 ? '#16a34a' : entry.score < -0.1 ? '#dc2626' : '#a8a29e'} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Per-Stock Sentiment */}
          <div className="bg-white rounded-xl border p-5">
            <h3 className="font-semibold text-cascade-charcoal mb-4">Per-Stock Sentiment</h3>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={stockBarData} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e5e5" />
                <XAxis type="number" tick={{ fontSize: 11 }} domain={[-100, 100]} tickFormatter={(v: number) => (v > 0 ? '+' : '') + v + '%'} />
                <YAxis type="category" dataKey="name" tick={{ fontSize: 12 }} width={80} />
                <Tooltip formatter={(v: number) => [(v > 0 ? '+' : '') + v + '%', 'Score']} />
                <Bar dataKey="score" radius={[0, 6, 6, 0]}>
                  {stockBarData.map((entry, i) => (
                    <Cell key={i} fill={SIGNAL_COLORS[entry.signal]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Stock Signal Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {stocks.map((s, i) => (
              <div key={i} className="bg-white rounded-xl border p-4">
                <div className="flex items-center justify-between mb-2">
                  <h4 className="font-bold text-cascade-charcoal">{s.symbol}</h4>
                  <span className={`px-2 py-0.5 rounded-full text-xs font-medium border ${SIGNAL_BG[s.signal]}`}>
                    {s.signal.toUpperCase()}
                  </span>
                </div>
                <p className={`text-2xl font-bold ${(s.score * 100) >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {s.score > 0 ? '+' : ''}{(s.score * 100).toFixed(1)}%
                </p>
                <p className="text-xs text-gray-500 mt-2">{s.recommendation}</p>
              </div>
            ))}
          </div>
        </>
      )}

      {/* Empty State */}
      {!data && !loading && !error && (
        <div className="text-center py-16 text-gray-400">
          <Heart size={48} className="mx-auto mb-4 opacity-30" />
          <p className="text-lg font-medium">No sentiment data yet</p>
          <p className="text-sm mt-1">Click "Run Demo" to analyze sample TSE news</p>
        </div>
      )}
    </div>
  );
}
