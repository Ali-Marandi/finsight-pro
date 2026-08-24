import { useState } from 'react';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, AreaChart, Area, CartesianGrid, ReferenceLine } from 'recharts';
import { TrendingUp, Activity, BarChart3, Loader2, AlertTriangle, Info } from 'lucide-react';
import { runTimeSeriesFull } from '../lib/api';

function generateDemoPrices(): number[] {
  const prices = [100];
  for (let i = 1; i < 252; i++) {
    prices.push(prices[i - 1] * (1 + (Math.random() - 0.48) * 0.03));
  }
  return prices.map(p => Math.round(p * 100) / 100);
}

export default function TimeSeries() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState('');

  const runAnalysis = async () => {
    setLoading(true);
    setError('');
    try {
      const prices = generateDemoPrices();
      const data = await runTimeSeriesFull(prices, 30);
      setResult(data);
    } catch (e: any) {
      setError(e.message || 'Analysis failed');
    } finally {
      setLoading(false);
    }
  };

  // Prepare chart data
  const historicalData = result?.arima?.historical?.dates?.map((d: string, i: number) => ({
    date: d.slice(5),
    price: result.arima.historical.values[i],
    type: 'historical',
  })) || [];

  const forecastData = result?.arima?.forecast?.dates?.map((d: string, i: number) => ({
    date: d.slice(5),
    price: result.arima.forecast.values[i],
    lower: result.arima.forecast.lower[i],
    upper: result.arima.forecast.upper[i],
    type: 'forecast',
  })) || [];

  const volData = result?.garch?.conditional_volatility?.map((v: number, i: number) => ({
    idx: i,
    volatility: v,
  })) || [];

  const summary = result?.summary;
  const garch = result?.garch;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-cascade-gold/10 rounded-xl flex items-center justify-center">
            <TrendingUp className="text-cascade-gold" size={20} />
          </div>
          <div>
            <h1 className="text-xl font-bold text-cascade-charcoal">Time Series Analysis</h1>
            <p className="text-sm text-gray-500">ARIMA forecasting & GARCH volatility modeling</p>
          </div>
        </div>
        <button
          onClick={runAnalysis}
          disabled={loading}
          className="px-4 py-2 bg-cascade-gold text-white rounded-lg hover:bg-cascade-gold/90 disabled:opacity-50 flex items-center gap-2 text-sm font-medium"
        >
          {loading ? <Loader2 className="animate-spin" size={16} /> : <Activity size={16} />}
          {loading ? 'Analyzing...' : 'Run Analysis (Demo Data)'}
        </button>
      </div>

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-xl flex items-start gap-3">
          <AlertTriangle className="text-red-500 shrink-0 mt-0.5" size={18} />
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}

      {/* Summary Cards */}
      {summary && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <MetricCard label="Volatility (Ann.)" value={`${summary.volatility_annual}%`} />
          <MetricCard label="Total Return" value={`${summary.total_return_pct}%`} />
          <MetricCard label="Skewness" value={String(summary.skewness)} />
          <MetricCard label="Kurtosis" value={String(summary.kurtosis)} />
        </div>
      )}

      {/* GARCH Info */}
      {garch?.parameters && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-white rounded-xl border p-4">
            <p className="text-xs text-gray-500 mb-1">GARCH Persistence</p>
            <p className="text-lg font-bold text-cascade-charcoal">{garch.persistence}</p>
            {garch.persistence > 0.9 && (
              <p className="text-xs text-amber-600 mt-1 flex items-center gap-1">
                <AlertTriangle size={12} /> Strong volatility clustering
              </p>
            )}
          </div>
          <div className="bg-white rounded-xl border p-4">
            <p className="text-xs text-gray-500 mb-1">Current Ann. Volatility</p>
            <p className="text-lg font-bold text-cascade-charcoal">{garch.current_annual_volatility}%</p>
          </div>
          <div className="bg-white rounded-xl border p-4">
            <p className="text-xs text-gray-500 mb-1">Model</p>
            <p className="text-lg font-bold text-cascade-charcoal">{garch.method}</p>
            {garch.aic && <p className="text-xs text-gray-400 mt-1">AIC: {garch.aic}</p>}
          </div>
        </div>
      )}

      {/* ARIMA Chart */}
      {historicalData.length > 0 && (
        <div className="bg-white rounded-xl border p-5">
          <div className="flex items-center gap-2 mb-4">
            <BarChart3 className="text-cascade-gold" size={18} />
            <h2 className="font-semibold text-cascade-charcoal">ARIMA Price Forecast</h2>
            {result?.arima?.method && <span className="text-xs bg-gray-100 px-2 py-0.5 rounded-full text-gray-600">{result.arima.method}</span>}
          </div>
          <ResponsiveContainer width="100%" height={350}>
            <AreaChart data={[...historicalData, ...forecastData]}>
              <defs>
                <linearGradient id="confBand" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#92761f" stopOpacity={0.15} />
                  <stop offset="100%" stopColor="#92761f" stopOpacity={0.02} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e5e5" />
              <XAxis dataKey="date" tick={{ fontSize: 11 }} interval={Math.floor(historicalData.length / 6)} />
              <YAxis tick={{ fontSize: 11 }} domain={['auto', 'auto']} />
              <Tooltip />
              <Area type="monotone" dataKey="upper" stroke="none" fill="url(#confBand)" />
              <Area type="monotone" dataKey="lower" stroke="none" fill="#f5f5f4" />
              <Line type="monotone" dataKey="price" stroke="#1a1a19" strokeWidth={1.5} dot={false} />
              <ReferenceLine x={historicalData.length - 1} stroke="#92761f" strokeDasharray="4 4" />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* GARCH Volatility Chart */}
      {volData.length > 0 && (
        <div className="bg-white rounded-xl border p-5">
          <div className="flex items-center gap-2 mb-4">
            <Activity className="text-cascade-gold" size={18} />
            <h2 className="font-semibold text-cascade-charcoal">Conditional Volatility (GARCH)</h2>
          </div>
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={volData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e5e5" />
              <XAxis dataKey="idx" tick={{ fontSize: 11 }} interval={Math.floor(volData.length / 8)} />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip />
              <Line type="monotone" dataKey="volatility" stroke="#92761f" strokeWidth={1.5} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Recommendations */}
      {result?.recommendations?.length > 0 && (
        <div className="space-y-2">
          {result.recommendations.map((r: any, i: number) => (
            <div key={i} className={`p-3 rounded-lg border flex items-start gap-3 ${
              r.level === 'warning' ? 'bg-amber-50 border-amber-200' : 'bg-blue-50 border-blue-200'
            }`}>
              <Info size={16} className={r.level === 'warning' ? 'text-amber-600 shrink-0 mt-0.5' : 'text-blue-600 shrink-0 mt-0.5'} />
              <p className="text-sm">{r.text}</p>
            </div>
          ))}
        </div>
      )}

      {/* Empty state */}
      {!result && !loading && !error && (
        <div className="text-center py-20 text-gray-400">
          <TrendingUp size={48} className="mx-auto mb-4 opacity-30" />
          <p className="text-lg font-medium">Ready to analyze</p>
          <p className="text-sm mt-1">Click "Run Analysis" to generate ARIMA forecast and GARCH volatility model</p>
        </div>
      )}
    </div>
  );
}

function MetricCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-white rounded-xl border p-4">
      <p className="text-xs text-gray-500 mb-1">{label}</p>
      <p className="text-xl font-bold text-cascade-charcoal">{value}</p>
    </div>
  );
}
