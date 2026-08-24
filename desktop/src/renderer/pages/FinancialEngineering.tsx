import { useState } from 'react';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, BarChart, Bar, Cell } from 'recharts';
import { Calculator, Loader2, AlertTriangle, Shield, DollarSign, TrendingUp, PieChart } from 'lucide-react';
import { calculateVaR, runMonteCarlo, runBlackScholes, optimizePortfolio } from '../lib/api';
import type { VaRResult, BlackScholesResult, PortfolioOptResult } from '../../types';

type Tab = 'var' | 'montecarlo' | 'blackscholes' | 'portfolio';

function generateDemoPrices(): number[] {
  const prices = [100];
  for (let i = 1; i < 252; i++) {
    prices.push(prices[i - 1] * (1 + (Math.random() - 0.48) * 0.025));
  }
  return prices.map(p => Math.round(p * 100) / 100);
}

export default function FinancialEngineering() {
  const [tab, setTab] = useState<Tab>('var');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // VaR state
  const [varResult, setVarResult] = useState<VaRResult | null>(null);

  // Monte Carlo state
  const [mcData, setMcData] = useState<any>(null);

  // Black-Scholes state
  const [bsResult, setBsResult] = useState<BlackScholesResult | null>(null);
  const [bsInputs, setBsInputs] = useState({ spot: 100, strike: 105, time: 0.5, rate: 0.05, volatility: 0.2, type: 'call' as 'call' | 'put' });

  // Portfolio state
  const [portResult, setPortResult] = useState<PortfolioOptResult | null>(null);

  const runVaR = async () => {
    setLoading(true); setError('');
    try {
      const prices = generateDemoPrices();
      setVarResult(await calculateVaR(prices, 0.95, 'historical', 1_000_000));
    } catch (e: any) { setError(e.message || 'VaR failed'); }
    finally { setLoading(false); }
  };

  const runMC = async () => {
    setLoading(true); setError('');
    try {
      const prices = generateDemoPrices();
      const returns = prices.slice(1).map((p, i) => (p - prices[i]) / prices[i]);
      const mu = (returns.reduce((a, b) => a + b, 0) / returns.length) * 252;
      const sigma = Math.sqrt(returns.reduce((s, r) => s + (r - mu / 252) ** 2, 0) / returns.length) * Math.sqrt(252);
      setMcData(await runMonteCarlo(prices[prices.length - 1], mu, sigma, 252, 5000));
    } catch (e: any) { setError(e.message || 'Monte Carlo failed'); }
    finally { setLoading(false); }
  };

  const runBS = async () => {
    setLoading(true); setError('');
    try {
      setBsResult(await runBlackScholes(bsInputs.spot, bsInputs.strike, bsInputs.time, bsInputs.rate, bsInputs.volatility, bsInputs.type));
    } catch (e: any) { setError(e.message || 'Black-Scholes failed'); }
    finally { setLoading(false); }
  };

  const runPort = async () => {
    setLoading(true); setError('');
    try {
      const returns = [0.12, 0.08, 0.15, 0.06, 0.10];
      const n = returns.length;
      const cov: number[][] = [];
      for (let i = 0; i < n; i++) {
        cov[i] = [];
        for (let j = 0; j < n; j++) {
          cov[i][j] = i === j ? 0.04 : 0.01;
        }
      }
      setPortResult(await optimizePortfolio(returns, cov, 0.03));
    } catch (e: any) { setError(e.message || 'Optimization failed'); }
    finally { setLoading(false); }
  };

  const tabs: { id: Tab; label: string; icon: typeof Calculator }[] = [
    { id: 'var', label: 'VaR / CVaR', icon: Shield },
    { id: 'montecarlo', label: 'Monte Carlo', icon: TrendingUp },
    { id: 'blackscholes', label: 'Black-Scholes', icon: DollarSign },
    { id: 'portfolio', label: 'Portfolio', icon: PieChart },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 bg-cascade-gold/10 rounded-xl flex items-center justify-center">
          <Calculator className="text-cascade-gold" size={20} />
        </div>
        <div>
          <h1 className="text-xl font-bold text-cascade-charcoal">Financial Engineering</h1>
          <p className="text-sm text-gray-500">VaR, Monte Carlo, Black-Scholes & Portfolio Optimization</p>
        </div>
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

      {/* VaR Tab */}
      {tab === 'var' && (
        <div className="space-y-4">
          <button onClick={runVaR} disabled={loading} className="px-4 py-2 bg-cascade-gold text-white rounded-lg hover:bg-cascade-gold/90 disabled:opacity-50 flex items-center gap-2 text-sm font-medium">
            {loading ? <Loader2 className="animate-spin" size={16} /> : <Shield size={16} />} Calculate VaR (Demo)
          </button>
          {varResult && (
            <>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="bg-white rounded-xl border p-4">
                  <p className="text-xs text-gray-500 mb-1">VaR (95%)</p>
                  <p className="text-xl font-bold text-red-600">-${varResult.var_absolute.toLocaleString()}</p>
                  <p className="text-xs text-gray-400">{varResult.var_return_pct}%</p>
                </div>
                <div className="bg-white rounded-xl border p-4">
                  <p className="text-xs text-gray-500 mb-1">CVaR (Expected Shortfall)</p>
                  <p className="text-xl font-bold text-red-700">-${varResult.cvar_absolute.toLocaleString()}</p>
                  <p className="text-xs text-gray-400">{varResult.cvar_return_pct}%</p>
                </div>
                <div className="bg-white rounded-xl border p-4">
                  <p className="text-xs text-gray-500 mb-1">Method</p>
                  <p className="text-lg font-bold text-cascade-charcoal capitalize">{varResult.method}</p>
                </div>
                <div className="bg-white rounded-xl border p-4">
                  <p className="text-xs text-gray-500 mb-1">Position</p>
                  <p className="text-lg font-bold text-cascade-charcoal">${varResult.position_value.toLocaleString()}</p>
                </div>
              </div>
              <div className="bg-blue-50 border border-blue-200 rounded-xl p-4">
                <p className="text-sm text-blue-800">{varResult.interpretation}</p>
              </div>
            </>
          )}
        </div>
      )}

      {/* Monte Carlo Tab */}
      {tab === 'montecarlo' && (
        <div className="space-y-4">
          <button onClick={runMC} disabled={loading} className="px-4 py-2 bg-cascade-gold text-white rounded-lg hover:bg-cascade-gold/90 disabled:opacity-50 flex items-center gap-2 text-sm font-medium">
            {loading ? <Loader2 className="animate-spin" size={16} /> : <TrendingUp size={16} />} Run Simulation (Demo)
          </button>
          {mcData && (
            <>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="bg-white rounded-xl border p-4">
                  <p className="text-xs text-gray-500 mb-1">Mean Final Price</p>
                  <p className="text-xl font-bold text-cascade-charcoal">{mcData.statistics.mean_final_price}</p>
                </div>
                <div className="bg-white rounded-xl border p-4">
                  <p className="text-xs text-gray-500 mb-1">Prob. of Profit</p>
                  <p className="text-xl font-bold text-green-600">{mcData.statistics.prob_profit}%</p>
                </div>
                <div className="bg-white rounded-xl border p-4">
                  <p className="text-xs text-gray-500 mb-1">Prob. of Loss</p>
                  <p className="text-xl font-bold text-red-600">{mcData.statistics.prob_loss}%</p>
                </div>
                <div className="bg-white rounded-xl border p-4">
                  <p className="text-xs text-gray-500 mb-1">Simulations</p>
                  <p className="text-xl font-bold text-cascade-charcoal">{mcData.parameters.simulations.toLocaleString()}</p>
                </div>
              </div>
              <div className="bg-white rounded-xl border p-5">
                <h3 className="font-semibold text-cascade-charcoal mb-4">Sample Price Paths</h3>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={mcData.sample_paths[0]?.map((_: number, i: number) =>
                    mcData.sample_paths.reduce((acc: Record<string, number>, path: number[]) => { acc[`p${mcData.sample_paths.indexOf(path)}`] = path[i]; return acc; }, { day: i })
                  )}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e5e5e5" />
                    <XAxis dataKey="day" tick={{ fontSize: 11 }} interval={50} />
                    <YAxis tick={{ fontSize: 11 }} />
                    <Tooltip />
                    {mcData.sample_paths.map((_: number[], i: number) => (
                      <Line key={i} type="monotone" dataKey={`p${i}`} stroke={i === 0 ? '#1a1a19' : `hsl(${i * 60}, 40%, 50%)`} strokeWidth={1} dot={false} />
                    ))}
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </>
          )}
        </div>
      )}

      {/* Black-Scholes Tab */}
      {tab === 'blackscholes' && (
        <div className="space-y-4">
          <div className="grid grid-cols-3 md:grid-cols-6 gap-3">
            {[
              { key: 'spot', label: 'Spot' },
              { key: 'strike', label: 'Strike' },
              { key: 'time', label: 'Time (yr)' },
              { key: 'rate', label: 'Rate' },
              { key: 'volatility', label: 'Vol' },
            ].map(f => (
              <div key={f.key}>
                <label className="text-xs text-gray-500">{f.label}</label>
                <input
                  type="number" step="any"
                  value={(bsInputs as any)[f.key]}
                  onChange={e => setBsInputs({ ...bsInputs, [f.key]: parseFloat(e.target.value) || 0 })}
                  className="w-full mt-1 px-3 py-2 border rounded-lg text-sm"
                />
              </div>
            ))}
            <div>
              <label className="text-xs text-gray-500">Type</label>
              <select value={bsInputs.type} onChange={e => setBsInputs({ ...bsInputs, type: e.target.value as 'call' | 'put' })} className="w-full mt-1 px-3 py-2 border rounded-lg text-sm">
                <option value="call">Call</option>
                <option value="put">Put</option>
              </select>
            </div>
          </div>
          <button onClick={runBS} disabled={loading} className="px-4 py-2 bg-cascade-gold text-white rounded-lg hover:bg-cascade-gold/90 disabled:opacity-50 flex items-center gap-2 text-sm font-medium">
            {loading ? <Loader2 className="animate-spin" size={16} /> : <DollarSign size={16} />} Calculate Price
          </button>
          {bsResult && !bsResult.error && (
            <>
              <div className="bg-white rounded-xl border p-6 text-center">
                <p className="text-sm text-gray-500 mb-1">{bsResult.option_type.toUpperCase()} Option Price</p>
                <p className="text-3xl font-bold text-cascade-gold">{bsResult.price}</p>
              </div>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {Object.entries(bsResult.greeks).map(([key, val]) => (
                  <div key={key} className="bg-white rounded-xl border p-4">
                    <p className="text-xs text-gray-500 mb-1 capitalize">{key}</p>
                    <p className="text-lg font-bold text-cascade-charcoal">{val}</p>
                  </div>
                ))}
              </div>
            </>
          )}
        </div>
      )}

      {/* Portfolio Tab */}
      {tab === 'portfolio' && (
        <div className="space-y-4">
          <button onClick={runPort} disabled={loading} className="px-4 py-2 bg-cascade-gold text-white rounded-lg hover:bg-cascade-gold/90 disabled:opacity-50 flex items-center gap-2 text-sm font-medium">
            {loading ? <Loader2 className="animate-spin" size={16} /> : <PieChart size={16} />} Optimize (5-Asset Demo)
          </button>
          {portResult && (
            <>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="bg-white rounded-xl border p-4">
                  <p className="text-xs text-gray-500 mb-1">Optimal Return</p>
                  <p className="text-xl font-bold text-green-600">{portResult.optimal_return}%</p>
                </div>
                <div className="bg-white rounded-xl border p-4">
                  <p className="text-xs text-gray-500 mb-1">Optimal Volatility</p>
                  <p className="text-xl font-bold text-cascade-charcoal">{portResult.optimal_volatility}%</p>
                </div>
                <div className="bg-white rounded-xl border p-4">
                  <p className="text-xs text-gray-500 mb-1">Sharpe Ratio</p>
                  <p className="text-xl font-bold text-cascade-gold">{portResult.sharpe_ratio}</p>
                </div>
                <div className="bg-white rounded-xl border p-4">
                  <p className="text-xs text-gray-500 mb-1">Assets</p>
                  <p className="text-xl font-bold text-cascade-charcoal">{portResult.num_assets}</p>
                </div>
              </div>
              <div className="bg-white rounded-xl border p-5">
                <h3 className="font-semibold text-cascade-charcoal mb-4">Optimal Weights</h3>
                <ResponsiveContainer width="100%" height={200}>
                  <BarChart data={portResult.optimal_weights.map((w, i) => ({ asset: `Asset ${i + 1}`, weight: w * 100 }))}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e5e5e5" />
                    <XAxis dataKey="asset" tick={{ fontSize: 12 }} />
                    <YAxis tick={{ fontSize: 12 }} unit="%" />
                    <Tooltip />
                    <Bar dataKey="weight" radius={[6, 6, 0, 0]}>
                      {portResult.optimal_weights.map((_, i) => (
                        <Cell key={i} fill={['#92761f', '#4e4732', '#1a1a19', '#a8a29e', '#78716c'][i % 5]} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}
