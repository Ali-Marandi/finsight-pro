import { useState, useEffect } from 'react';
import { Brain, AlertCircle, Loader2, BarChart3, Info } from 'lucide-react';
import { LineChart, Line, AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend, Cell } from 'recharts';
import { getFuzzyNeuralDemo } from '../lib/api';

const COLORS = ['#92761f', '#3b82f6', '#ef4444', '#10b981', '#8b5cf6', '#f59e0b'];

function MetricCard({ label, value, suffix = '', color }: { label: string; value: string | number | null | undefined; suffix?: string; color?: string }) {
  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4">
      <p className="text-xs text-gray-500 mb-1">{label}</p>
      <p className={`text-lg font-semibold ${color ?? 'text-gray-900'}`}>{value ?? '—'}{suffix}</p>
    </div>
  );
}

export default function FuzzyNeural() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState(0);
  const tabs = ['Credit Scoring', 'Bankruptcy Prediction', 'Rule Extraction'];

  useEffect(() => { loadDemo(); }, []);

   async function loadDemo() {
    setLoading(true); setError(null);
    try {
      const r = await getFuzzyNeuralDemo();
      setData(r);
    } catch (e: any) {
      setError(e.message || 'Failed to load Fuzzy Neural demo');
    } finally {
      setLoading(false);
    }
  }

  const creditScoring = data?.credit_scoring;
  const bankruptcy = data?.bankruptcy_prediction;
  const ruleExtraction = data?.rule_extraction;

  /* ---------- Loading / Error / Empty states ---------- */

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center h-64 gap-3">
        <Loader2 className="animate-spin text-cascade-gold" size={32} />
        <p className="text-sm text-gray-500">Loading Fuzzy Neural Network demo...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-cascade-gold/10 rounded-xl flex items-center justify-center">
            <Brain className="text-cascade-gold" size={20} />
          </div>
          <div>
            <h1 className="text-xl font-bold text-cascade-charcoal">Fuzzy Neural Networks</h1>
            <p className="text-sm text-gray-500">ANFIS-based Credit & Bankruptcy Analysis</p>
          </div>
        </div>
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start gap-3">
          <AlertCircle className="text-red-500 mt-0.5 shrink-0" size={20} />
          <div>
            <p className="text-red-800 font-medium">Error</p>
            <p className="text-red-600 text-sm">{error}</p>
          </div>
        </div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="flex flex-col items-center justify-center h-64 text-gray-400">
        <Brain size={48} className="mb-3" />
        <p className="text-sm">No data available</p>
        <button onClick={loadDemo} className="mt-3 px-4 py-2 bg-cascade-gold text-white rounded-lg text-sm hover:bg-cascade-gold/90">
          Load Demo
        </button>
      </div>
    );
  }

  /* ---------- Helper: membership chart data ---------- */

  const membershipChartData = (() => {
    if (!creditScoring?.membership_degrees) return [];
    const md = creditScoring.membership_degrees;
    const features = ['income', 'debt_ratio', 'employment_years', 'credit_history', 'age'];
    return features.map(f => ({
      feature: f.replace(/_/g, ' ').replace(/\b\w/g, c: any => (c as string).toUpperCase()),
      low: md[f]?.low ?? 0,
      medium: md[f]?.medium ?? 0,
      high: md[f]?.high ?? 0,
    }));
  })();

  /* ---------- Helper: accuracy comparison data ---------- */

  const accuracyChartData = bankruptcy ? [
    { name: 'Train', accuracy: bankruptcy.train_accuracy ?? 0 },
    { name: 'Test', accuracy: bankruptcy.test_accuracy ?? 0 },
  ] : [];

  /* ---------- Helper: confusion matrix ---------- */

  const confusionMatrix = bankruptcy?.confusion_matrix;

  /* ---------- Helper: ROC curve data ---------- */

  const rocData = bankruptcy?.roc_curve_points ?? [];

  /* ---------- Helper: rules table ---------- */

  const extractedRules = ruleExtraction?.rules ?? [];

  /* ================================================================ */
  /*  RENDER                                                          */
  /* ================================================================ */

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 bg-cascade-gold/10 rounded-xl flex items-center justify-center">
          <Brain className="text-cascade-gold" size={20} />
        </div>
        <div>
          <h1 className="text-xl font-bold text-cascade-charcoal">Fuzzy Neural Networks</h1>
          <p className="text-sm text-gray-500">ANFIS-based Credit Scoring & Bankruptcy Analysis</p>
        </div>
      </div>

      {/* Info Banner */}
      {data?.demo_title && (
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 flex items-start gap-3">
          <Info className="text-amber-600 shrink-0 mt-0.5" size={18} />
          <div>
            <h3 className="text-sm font-semibold text-amber-900">{data.demo_title}</h3>
            <p className="text-xs text-amber-700 mt-1">{data.description}</p>
          </div>
        </div>
      )}

      {/* Tab Switcher */}
      <div className="bg-gray-100 rounded-xl p-1 flex gap-1">
        {tabs.map((tab, i) => (
          <button
            key={tab}
            onClick={() => setActiveTab(i)}
            className={`flex-1 py-2 px-3 rounded-lg text-sm font-medium transition-colors ${
              activeTab === i
                ? 'bg-white text-gray-900 shadow-sm'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* Tab 0: Credit Scoring */}
      {activeTab === 0 && (
        <div className="space-y-4">
          {/* Metric Cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <MetricCard
              label="Credit Score"
              value={creditScoring?.score}
              color="text-cascade-gold"
            />
            <MetricCard
              label="Risk Category"
              value={creditScoring?.risk_category}
              color={
                creditScoring?.risk_category === 'Low'
                  ? 'text-green-600'
                  : creditScoring?.risk_category === 'High'
                  ? 'text-red-600'
                  : 'text-amber-600'
              }
            />
            <MetricCard
              label="Activated Rules"
              value={creditScoring?.activated_rules}
            />
            <MetricCard
              label="Top Sensitive Feature"
              value={creditScoring?.top_sensitive_feature
                ?.replace(/_/g, ' ')
                ?.replace(/\b\w/g, c: any => (c as string).toUpperCase())}
            />
          </div>

          {/* Membership Degrees Bar Chart */}
          {membershipChartData.length > 0 && (
            <div className="bg-white rounded-lg border border-gray-200 p-4">
              <h4 className="text-sm font-medium text-gray-700 mb-3 flex items-center gap-2">
                <BarChart3 size={16} className="text-gray-400" />
                Fuzzy Membership Degrees per Feature
              </h4>
              <ResponsiveContainer width="100%" height={320}>
                <BarChart data={membershipChartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                  <XAxis dataKey="feature" tick={{ fontSize: 11 }} />
                  <YAxis tick={{ fontSize: 11 }} domain={[0, 1]} />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="low" name="Low" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="medium" name="Medium" fill="#f59e0b" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="high" name="High" fill="#ef4444" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Empty state for tab content */}
          {!creditScoring && (
            <div className="flex flex-col items-center justify-center h-48 text-gray-400">
              <BarChart3 size={36} className="mb-2" />
              <p className="text-sm">No credit scoring data available</p>
            </div>
          )}
        </div>
      )}

      {/* Tab 1: Bankruptcy Prediction */}
      {activeTab === 1 && (
        <div className="space-y-4">
          {/* Metric Cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <MetricCard
              label="Train Accuracy"
              value={bankruptcy?.train_accuracy}
              suffix="%"
              color="text-cascade-gold"
            />
            <MetricCard
              label="Test Accuracy"
              value={bankruptcy?.test_accuracy}
              suffix="%"
              color="text-blue-600"
            />
            <MetricCard
              label="AUC"
              value={bankruptcy?.auc}
              color="text-green-600"
            />
            <MetricCard
              label="ANFIS vs Logistic Δ"
              value={bankruptcy?.anfis_vs_logistic_improvement}
              suffix="%"
              color="text-purple-600"
            />
          </div>

          {/* Accuracy Comparison Chart */}
          {accuracyChartData.length > 0 && (
            <div className="bg-white rounded-lg border border-gray-200 p-4">
              <h4 className="text-sm font-medium text-gray-700 mb-3 flex items-center gap-2">
                <BarChart3 size={16} className="text-gray-400" />
                Train vs Test Accuracy
              </h4>
              <ResponsiveContainer width="100%" height={260}>
                <BarChart data={accuracyChartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                  <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                  <YAxis tick={{ fontSize: 11 }} domain={[0, 100]} unit="%" />
                  <Tooltip />
                  <Bar dataKey="accuracy" name="Accuracy" radius={[4, 4, 0, 0]}>
                    <Cell fill="#92761f" />
                    <Cell fill="#3b82f6" />
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Confusion Matrix & ROC Curve side-by-side */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {/* Confusion Matrix */}
            {confusionMatrix && (
              <div className="bg-white rounded-lg border border-gray-200 p-4">
                <h4 className="text-sm font-medium text-gray-700 mb-3">Confusion Matrix</h4>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr>
                        <th className="text-left text-xs text-gray-500 font-medium pb-2 pr-4"></th>
                        <th colSpan={2} className="text-center text-xs text-gray-500 font-medium pb-2">
                          Predicted
                        </th>
                      </tr>
                      <tr>
                        <th className="text-left text-xs text-gray-400 font-medium pb-2 pr-4">
                          Actual
                        </th>
                        <th className="text-center text-xs text-gray-400 font-medium pb-2 px-4">
                          Non-Bankrupt
                        </th>
                        <th className="text-center text-xs text-gray-400 font-medium pb-2 px-4">
                          Bankrupt
                        </th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                      <tr>
                        <td className="py-2 pr-4 text-xs text-gray-600 font-medium">Non-Bankrupt</td>
                        <td className="py-2 px-4 text-center">
                          <span className="inline-flex items-center justify-center w-12 h-8 rounded bg-green-50 text-green-700 font-semibold text-sm">
                            {confusionMatrix.true_negative ?? '—'}
                          </span>
                        </td>
                        <td className="py-2 px-4 text-center">
                          <span className="inline-flex items-center justify-center w-12 h-8 rounded bg-red-50 text-red-700 font-semibold text-sm">
                            {confusionMatrix.false_positive ?? '—'}
                          </span>
                        </td>
                      </tr>
                      <tr>
                        <td className="py-2 pr-4 text-xs text-gray-600 font-medium">Bankrupt</td>
                        <td className="py-2 px-4 text-center">
                          <span className="inline-flex items-center justify-center w-12 h-8 rounded bg-red-50 text-red-700 font-semibold text-sm">
                            {confusionMatrix.false_negative ?? '—'}
                          </span>
                        </td>
                        <td className="py-2 px-4 text-center">
                          <span className="inline-flex items-center justify-center w-12 h-8 rounded bg-green-50 text-green-700 font-semibold text-sm">
                            {confusionMatrix.true_positive ?? '—'}
                          </span>
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* ROC Curve */}
            {rocData.length > 0 && (
              <div className="bg-white rounded-lg border border-gray-200 p-4">
                <h4 className="text-sm font-medium text-gray-700 mb-3">ROC Curve</h4>
                <ResponsiveContainer width="100%" height={240}>
                  <AreaChart data={rocData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                    <XAxis
                      dataKey="fpr"
                      type="number"
                      tick={{ fontSize: 11 }}
                      domain={[0, 1]}
                      label={{ value: 'False Positive Rate', position: 'insideBottom', offset: -5, fontSize: 11, fill: '#9ca3af' }}
                    />
                    <YAxis
                      type="number"
                      tick={{ fontSize: 11 }}
                      domain={[0, 1]}
                      label={{ value: 'True Positive Rate', angle: -90, position: 'insideLeft', offset: 10, fontSize: 11, fill: '#9ca3af' }}
                    />
                    <Tooltip
                      formatter={(value: number, name: string) => [value?.toFixed(4), name]}
                      labelFormatter={(label: number) => `FPR: ${label?.toFixed(4)}`}
                    />
                    <Area
                      type="monotone"
                      dataKey="tpr"
                      name="TPR"
                      stroke="#92761f"
                      fill="#92761f"
                      fillOpacity={0.15}
                      strokeWidth={2}
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            )}
          </div>

          {/* Empty state */}
          {!bankruptcy && (
            <div className="flex flex-col items-center justify-center h-48 text-gray-400">
              <BarChart3 size={36} className="mb-2" />
              <p className="text-sm">No bankruptcy prediction data available</p>
            </div>
          )}
        </div>
      )}

      {/* Tab 2: Rule Extraction */}
      {activeTab === 2 && (
        <div className="space-y-4">
          {/* Metric Cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <MetricCard
              label="Total Rules"
              value={ruleExtraction?.n_rules}
              color="text-cascade-gold"
            />
            <MetricCard
              label="Features Used"
              value={ruleExtraction?.n_features}
              color="text-blue-600"
            />
            <MetricCard
              label="Avg Rule Strength"
              value={ruleExtraction?.avg_rule_strength}
              color="text-purple-600"
            />
            <MetricCard
              label="Coverage"
              value={ruleExtraction?.coverage}
              suffix="%"
              color="text-green-600"
            />
          </div>

          {/* Rules Table */}
          {extractedRules.length > 0 && (
            <div className="bg-white rounded-lg border border-gray-200 p-4">
              <h4 className="text-sm font-medium text-gray-700 mb-3">Extracted Fuzzy Rules</h4>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-gray-200">
                      <th className="text-left text-xs text-gray-500 font-medium pb-2 pr-4">#</th>
                      <th className="text-left text-xs text-gray-500 font-medium pb-2 pr-4">Rule</th>
                      <th className="text-right text-xs text-gray-500 font-medium pb-2 px-4">Strength</th>
                      <th className="text-right text-xs text-gray-500 font-medium pb-2 px-4">Confidence</th>
                      <th className="text-right text-xs text-gray-500 font-medium pb-2 pl-4">Support</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {extractedRules.map((rule: any, idx: number) => (
                      <tr key={idx} className="hover:bg-gray-50 transition-colors">
                        <td className="py-2.5 pr-4 text-xs text-gray-400 font-mono">{idx + 1}</td>
                        <td className="py-2.5 pr-4 text-xs text-gray-700 max-w-xs">
                          <span className="font-mono leading-relaxed">{rule.rule_text ?? rule.rule ?? '—'}</span>
                        </td>
                        <td className="py-2.5 px-4 text-right">
                          <span
                            className="inline-flex items-center justify-center min-w-[3rem] px-2 py-0.5 rounded-full text-xs font-semibold"
                            style={{
                              backgroundColor: `${COLORS[idx % COLORS.length]}18`,
                              color: COLORS[idx % COLORS.length],
                            }}
                          >
                            {(rule.strength ?? 0).toFixed(3)}
                          </span>
                        </td>
                        <td className="py-2.5 px-4 text-right text-xs text-gray-700 font-medium">
                          {(rule.confidence ?? 0).toFixed(3)}
                        </td>
                        <td className="py-2.5 pl-4 text-right text-xs text-gray-700 font-medium">
                          {(rule.support ?? 0).toFixed(3)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Empty state */}
          {extractedRules.length === 0 && !ruleExtraction && (
            <div className="flex flex-col items-center justify-center h-48 text-gray-400">
              <BarChart3 size={36} className="mb-2" />
              <p className="text-sm">No rule extraction data available</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
