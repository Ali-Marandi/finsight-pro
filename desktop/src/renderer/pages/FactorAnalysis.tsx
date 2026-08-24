import { useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Cell, LineChart, Line, Legend } from 'recharts';
import { ScatterChart, Scatter, ZAxis } from 'recharts';
import { Layers, Loader2, AlertTriangle } from 'lucide-react';
import { getFactorAnalysisDemo } from '../lib/api';
import type { PCAResult, FamaFrenchResult } from '../../types';

const chartColors = ['#92761f', '#4e4732', '#1a1a19', '#a8a29e', '#78716c', '#517181'];

type Tab = 'pca' | 'famafrench';

export default function FactorAnalysis() {
  const [tab, setTab] = useState<Tab>('pca');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [pcaResult, setPcaResult] = useState<PCAResult | null>(null);
  const [ffResult, setFfResult] = useState<FamaFrenchResult | null>(null);

  const runDemo = async () => {
    setLoading(true); setError('');
    try {
      const data = await getFactorAnalysisDemo();
      setPcaResult(data.pca);
      setFfResult(data.fama_french);
    } catch (e: any) { setError(e.message || 'Factor analysis failed'); }
    finally { setLoading(false); }
  };

  const tabs: { id: Tab; label: string }[] = [
    { id: 'pca', label: 'PCA' },
    { id: 'famafrench', label: 'Fama-French' },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 bg-cascade-gold/10 rounded-xl flex items-center justify-center">
          <Layers className="text-cascade-gold" size={20} />
        </div>
        <div>
          <h1 className="text-xl font-bold text-cascade-charcoal">Factor Analysis</h1>
          <p className="text-sm text-gray-500">PCA &amp; Fama-French 3-Factor Model</p>
        </div>
      </div>

      <div className="flex gap-3">
        <div className="flex gap-1 bg-gray-100 rounded-xl p-1">
          {tabs.map(t => (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                tab === t.id ? 'bg-white text-cascade-charcoal shadow-sm' : 'text-gray-500 hover:text-gray-700'
              }`}
            >{t.label}</button>
          ))}
        </div>
        <button onClick={runDemo} disabled={loading} className="px-4 py-2 bg-cascade-gold text-white rounded-lg hover:bg-cascade-gold/90 disabled:opacity-50 flex items-center gap-2 text-sm font-medium">
          {loading ? <Loader2 className="animate-spin" size={16} /> : <Layers size={16} />} 10-Asset Demo
        </button>
      </div>

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-xl flex items-start gap-3">
          <AlertTriangle className="text-red-500 shrink-0 mt-0.5" size={18} />
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}

      {tab === 'pca' && pcaResult && !pcaResult.error && (
        <>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-white rounded-xl border p-4">
              <p className="text-xs text-gray-500 mb-1">Assets Analyzed</p>
              <p className="text-xl font-bold text-cascade-charcoal">{pcaResult.assets}</p>
            </div>
            <div className="bg-white rounded-xl border p-4">
              <p className="text-xs text-gray-500 mb-1">Kaiser Components</p>
              <p className="text-xl font-bold text-cascade-gold">{pcaResult.kaiser_components}</p>
            </div>
            <div className="bg-white rounded-xl border p-4">
              <p className="text-xs text-gray-500 mb-1">Total Variance Explained</p>
              <p className="text-xl font-bold text-cascade-charcoal">{pcaResult.total_explained_variance_pct}%</p>
            </div>
            <div className="bg-white rounded-xl border p-4">
              <p className="text-xs text-gray-500 mb-1">Observations</p>
              <p className="text-xl font-bold text-cascade-charcoal">{pcaResult.observations}</p>
            </div>
          </div>

          {/* Scree Plot */}
          <div className="bg-white rounded-xl border p-5">
            <h3 className="font-semibold text-cascade-charcoal mb-4">Scree Plot (Eigenvalues)</h3>
            <ResponsiveContainer width="100%" height={250}>
              <LineChart data={pcaResult.scree_plot_data}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e5e5" />
                <XAxis dataKey="component" tick={{ fontSize: 11 }} label={{ value: 'Component', position: 'insideBottom', offset: -5, fontSize: 12 }} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip />
                <Line type="monotone" dataKey="eigenvalue" stroke="#92761f" strokeWidth={2} dot={{ r: 4, fill: '#92761f' }} name="Eigenvalue" />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* Cumulative Variance */}
          <div className="bg-white rounded-xl border p-5">
            <h3 className="font-semibold text-cascade-charcoal mb-4">Cumulative Variance Explained</h3>
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={pcaResult.scree_plot_data}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e5e5" />
                <XAxis dataKey="component" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} unit="%" />
                <Tooltip />
                <Bar dataKey="cumulative_var_pct" radius={[6, 6, 0, 0]} name="Cumulative %">
                  {pcaResult.scree_plot_data.map((_, i) => <Cell key={i} fill={chartColors[i % chartColors.length]} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          {pcaResult.recommendation && (
            <div className="bg-blue-50 border border-blue-200 rounded-xl p-4">
              <p className="text-sm text-blue-800">{pcaResult.recommendation}</p>
            </div>
          )}
        </>
      )}

      {tab === 'famafrench' && ffResult && !ffResult.error && (
        <>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-white rounded-xl border p-4">
              <p className="text-xs text-gray-500 mb-1">Assets</p>
              <p className="text-xl font-bold text-cascade-charcoal">{ffResult.assets}</p>
            </div>
            <div className="bg-white rounded-xl border p-4">
              <p className="text-xs text-gray-500 mb-1">Avg R-squared</p>
              <p className="text-xl font-bold text-cascade-gold">{ffResult.avg_r_squared}</p>
            </div>
            <div className="bg-white rounded-xl border p-4">
              <p className="text-xs text-gray-500 mb-1">Mean Alpha (ann.)</p>
              <p className="text-xl font-bold text-cascade-charcoal">{ffResult.mean_alpha_pct}%</p>
            </div>
            <div className="bg-white rounded-xl border p-4">
              <p className="text-xs text-gray-500 mb-1">Periods</p>
              <p className="text-xl font-bold text-cascade-charcoal">{ffResult.observations}</p>
            </div>
          </div>

          {/* Factor Statistics */}
          <div className="bg-white rounded-xl border p-5">
            <h3 className="font-semibold text-cascade-charcoal mb-4">Factor Statistics</h3>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b">
                    <th className="text-right py-2 px-3 font-semibold text-gray-600">Factor</th>
                    <th className="text-right py-2 px-3 font-semibold text-gray-600">Mean (ann. %)</th>
                    <th className="text-right py-2 px-3 font-semibold text-gray-600">Vol (ann. %)</th>
                    <th className="text-right py-2 px-3 font-semibold text-gray-600">Sharpe</th>
                  </tr>
                </thead>
                <tbody>
                  {ffResult.factor_statistics.map((f, i) => (
                    <tr key={i} className="border-b last:border-0">
                      <td className="py-2 px-3 font-medium">{f.factor}</td>
                      <td className={`py-2 px-3 ${f.mean_annual_pct >= 0 ? 'text-green-600' : 'text-red-600'}`}>{f.mean_annual_pct}%</td>
                      <td className="py-2 px-3">{f.volatility_annual_pct}%</td>
                      <td className="py-2 px-3 font-bold text-cascade-gold">{f.sharpe}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Factor Loadings Chart */}
          <div className="bg-white rounded-xl border p-5">
            <h3 className="font-semibold text-cascade-charcoal mb-4">Factor Loadings (Market Beta by Asset)</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={ffResult.asset_loadings.map(a => ({ name: a.asset.split(' ')[0], mkt: a.beta_mkt, smb: a.beta_smb, hml: a.beta_hml }))}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e5e5" />
                <XAxis dataKey="name" tick={{ fontSize: 10 }} angle={-25} textAnchor="end" height={60} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip />
                <Legend />
                <Bar dataKey="mkt" fill="#92761f" radius={[4, 4, 0, 0]} name="Market Beta" />
                <Bar dataKey="smb" fill="#4e4732" radius={[4, 4, 0, 0]} name="SMB" />
                <Bar dataKey="hml" fill="#a8a29e" radius={[4, 4, 0, 0]} name="HML" />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* R-squared Chart */}
          <div className="bg-white rounded-xl border p-5">
            <h3 className="font-semibold text-cascade-charcoal mb-4">Model Fit (R-squared per Asset)</h3>
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={ffResult.asset_loadings.map(a => ({ name: a.asset.split(' ')[0], r2: a.r_squared * 100 }))}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e5e5" />
                <XAxis dataKey="name" tick={{ fontSize: 10 }} angle={-25} textAnchor="end" height={60} />
                <YAxis tick={{ fontSize: 11 }} unit="%" />
                <Tooltip />
                <Bar dataKey="r2" radius={[6, 6, 0, 0]} name="R-squared %">
                  {ffResult.asset_loadings.map((a, i) => (
                    <Cell key={i} fill={a.r_squared > 0.7 ? '#3c8855' : a.r_squared > 0.4 ? '#92761f' : '#a9534b'} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          {ffResult.recommendation && (
            <div className="bg-blue-50 border border-blue-200 rounded-xl p-4">
              <p className="text-sm text-blue-800">{ffResult.recommendation}</p>
            </div>
          )}
        </>
      )}
    </div>
  );
}