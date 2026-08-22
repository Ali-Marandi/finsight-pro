import { useState, useEffect } from 'react';
import { Activity, AlertTriangle, CheckCircle, ShieldAlert, TrendingDown, Zap, Info } from 'lucide-react';
import { getApiClient } from '../lib/api';
import { useAnalysisStore } from '../hooks/useAnalysisStore';
import Spinner from '../components/Spinner';

interface ModelResult {
  model_name: string;
  model_year: string;
  score: number;
  zone: 'safe' | 'grey' | 'distress';
  probability: number;
  description: string;
  interpretation: string;
  components: Record<string, number | string>;
}

interface PredictionResponse {
  overall_assessment: string;
  overall_text: string;
  consensus_probability: number;
  zone_votes: { safe: number; grey: number; distress: number };
  models: ModelResult[];
  recommendations: string[];
  company_name?: string;
  period?: string;
  analysis_id?: string;
}

const ZONE_STYLES = {
  safe: {
    bg: 'bg-emerald-50',
    border: 'border-emerald-200',
    text: 'text-emerald-700',
    badge: 'bg-emerald-100 text-emerald-700',
    gauge: '#10b981',
    icon: CheckCircle,
    label: 'SAFE',
    labelFa: 'امن',
  },
  grey: {
    bg: 'bg-amber-50',
    border: 'border-amber-200',
    text: 'text-amber-700',
    badge: 'bg-amber-100 text-amber-700',
    gauge: '#f59e0b',
    icon: AlertTriangle,
    label: 'GREY ZONE',
    labelFa: 'منطقه خاکستری',
  },
  distress: {
    bg: 'bg-red-50',
    border: 'border-red-200',
    text: 'text-red-700',
    badge: 'bg-red-100 text-red-700',
    gauge: '#ef4444',
    icon: ShieldAlert,
    label: 'DISTRESS',
    labelFa: 'بحران',
  },
};

function ProbabilityGauge({ probability, size = 200 }: { probability: number; size?: number }) {
  const radius = (size - 20) / 2;
  const circumference = Math.PI * radius; // half circle
  const progress = (probability / 100) * circumference;
  
  // Determine color
  let color = '#10b981'; // green
  if (probability > 50) color = '#ef4444'; // red
  else if (probability > 25) color = '#f59e0b'; // amber
  
  return (
    <div className="relative" style={{ width: size, height: size / 2 + 20 }}>
      <svg width={size} height={size / 2 + 20} className="overflow-visible">
        {/* Background arc */}
        <path
          d={`M ${10} ${size / 2 + 10} A ${radius} ${radius} 0 0 1 ${size - 10} ${size / 2 + 10}`}
          fill="none"
          stroke="#e7e5e4"
          strokeWidth="12"
          strokeLinecap="round"
        />
        {/* Progress arc */}
        <path
          d={`M ${10} ${size / 2 + 10} A ${radius} ${radius} 0 0 1 ${size - 10} ${size / 2 + 10}`}
          fill="none"
          stroke={color}
          strokeWidth="12"
          strokeLinecap="round"
          strokeDasharray={`${progress} ${circumference}`}
          style={{ transition: 'stroke-dasharray 1s ease' }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center" style={{ top: -10 }}>
        <span className="text-3xl font-bold" style={{ color }}>{probability.toFixed(1)}%</span>
        <span className="text-xs text-cascade-sage mt-1">Distress Probability</span>
      </div>
    </div>
  );
}

function ModelCard({ model, index }: { model: ModelResult; index: number }) {
  const [expanded, setExpanded] = useState(false);
  const style = ZONE_STYLES[model.zone];
  const ZoneIcon = style.icon;
  
  return (
    <div className={`rounded-xl border ${style.border} ${style.bg} p-4 transition-all hover:shadow-sm`}>
      <div className="flex items-center justify-between cursor-pointer" onClick={() => setExpanded(!expanded)}>
        <div className="flex items-center gap-3">
          <div className={`w-8 h-8 rounded-lg ${style.badge} flex items-center justify-center`}>
            <ZoneIcon size={16} />
          </div>
          <div>
            <h4 className="font-semibold text-cascade-charcoal text-sm">{model.model_name}</h4>
            <p className="text-xs text-cascade-sage">{model.model_year !== '-' ? `Published ${model.model_year}` : 'Altman-derived model'}</p>
          </div>
        </div>
        <div className="text-right">
          <div className={`text-lg font-bold ${style.text}`}>{model.score}</div>
          <span className={`text-[10px] font-medium px-2 py-0.5 rounded-full ${style.badge}`}>
            {style.label}
          </span>
        </div>
      </div>
      
      {expanded && (
        <div className="mt-3 pt-3 border-t border-black/5 space-y-3">
          <p className="text-xs text-cascade-charcoal/70 leading-relaxed">{model.description}</p>
          <p className="text-xs text-cascade-charcoal/80 leading-relaxed">{model.interpretation}</p>
          
          <div>
            <h5 className="text-[10px] font-semibold text-cascade-sage uppercase tracking-wider mb-1.5">Components</h5>
            <div className="grid grid-cols-2 gap-1">
              {Object.entries(model.components).map(([key, val]) => (
                <div key={key} className="flex justify-between text-xs">
                  <span className="text-cascade-charcoal/60 truncate mr-2" title={key}>{key.split('(')[0].trim()}</span>
                  <span className="font-mono font-medium text-cascade-charcoal">
                    {typeof val === 'string' ? val : val.toFixed(4)}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default function Prediction() {
  const { analyses, currentAnalysis } = useAnalysisStore();
  const [selectedId, setSelectedId] = useState<string>(currentAnalysis?.analysisId || '');
  const [result, setResult] = useState<PredictionResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const runPrediction = async (analysisId: string) => {
    if (!analysisId) return;
    setIsLoading(true);
    setError(null);
    setResult(null);

    try {
      const client = await getApiClient();
      const { data } = await client.post('/prediction/from-analysis', { analysis_id: analysisId });
      setResult(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Prediction failed');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-gradient-to-br from-red-500 to-orange-500 rounded-xl flex items-center justify-center">
            <Activity size={20} className="text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-cascade-charcoal">Bankruptcy Prediction</h1>
            <p className="text-xs text-cascade-sage">Multi-model financial distress analysis</p>
          </div>
        </div>
      </div>

      {/* Selector + Run */}
      <div className="bg-white rounded-xl border border-cascade-mist p-4">
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="flex-1">
            <label className="text-xs font-medium text-cascade-sage mb-1 block">Select Analysis</label>
            <select
              value={selectedId}
              onChange={(e) => setSelectedId(e.target.value)}
              className="w-full bg-cascade-stone border border-cascade-mist rounded-lg px-3 py-2.5 text-sm text-cascade-charcoal focus:outline-none focus:ring-2 focus:ring-cascade-gold/30"
            >
              <option value="">Choose a financial analysis...</option>
              {analyses.map((a) => (
                <option key={a.analysisId} value={a.analysisId}>
                  {a.companyName} — {a.period}
                </option>
              ))}
            </select>
          </div>
          <div className="flex items-end">
            <button
              onClick={() => runPrediction(selectedId)}
              disabled={!selectedId || isLoading}
              className="px-6 py-2.5 bg-cascade-charcoal text-white rounded-lg text-sm font-medium hover:bg-cascade-charcoal/90 disabled:bg-cascade-mist disabled:text-cascade-sage transition-colors flex items-center gap-2"
            >
              {isLoading ? <Spinner size={16} /> : <Zap size={16} />}
              {isLoading ? 'Running Models...' : 'Run Prediction'}
            </button>
          </div>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-4 flex items-start gap-3">
          <AlertTriangle size={18} className="text-red-500 shrink-0 mt-0.5" />
          <div>
            <h4 className="text-sm font-semibold text-red-700">Prediction Error</h4>
            <p className="text-xs text-red-600 mt-1">{error}</p>
          </div>
        </div>
      )}

      {/* Results */}
      {result && (
        <>
          {/* Overall Assessment Banner */}
          <div className={`rounded-xl border p-6 ${ZONE_STYLES[result.overall_assessment].bg} ${ZONE_STYLES[result.overall_assessment].border}`}>
            <div className="flex flex-col md:flex-row items-center gap-6">
              <ProbabilityGauge probability={result.consensus_probability} size={220} />
              <div className="flex-1 text-center md:text-left">
                <div className="flex items-center justify-center md:justify-start gap-2 mb-2">
                  {(() => {
                    const Icon = ZONE_STYLES[result.overall_assessment].icon;
                    return <Icon size={24} className={ZONE_STYLES[result.overall_assessment].text} />;
                  })()}
                  <h2 className={`text-xl font-bold ${ZONE_STYLES[result.overall_assessment].text}`}>
                    {result.overall_assessment.toUpperCase()}
                  </h2>
                </div>
                <p className="text-sm text-cascade-charcoal/70 mb-4">{result.overall_text}</p>
                <div className="flex items-center justify-center md:justify-start gap-4">
                  {Object.entries(result.zone_votes).map(([zone, count]) => {
                    const s = ZONE_STYLES[zone as keyof typeof ZONE_STYLES];
                    return (
                      <div key={zone} className={`px-3 py-1 rounded-full text-xs font-medium ${s.badge}`}>
                        {s.label}: {count}/5
                      </div>
                    );
                  })}
                </div>
                {result.company_name && (
                  <p className="text-xs text-cascade-sage mt-3">
                    {result.company_name} — {result.period}
                  </p>
                )}
              </div>
            </div>
          </div>

          {/* Model Results Grid */}
          <div>
            <h3 className="text-sm font-semibold text-cascade-charcoal mb-3 flex items-center gap-2">
              <TrendingDown size={16} className="text-cascade-sage" />
              Model Results (click to expand)
            </h3>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
              {result.models.map((model, idx) => (
                <ModelCard key={idx} model={model} index={idx} />
              ))}
            </div>
          </div>

          {/* Recommendations */}
          <div className="bg-white rounded-xl border border-cascade-mist p-5">
            <h3 className="text-sm font-semibold text-cascade-charcoal mb-3 flex items-center gap-2">
              <Info size={16} className="text-cascade-gold" />
              Recommendations
            </h3>
            <div className="space-y-2">
              {result.recommendations.map((rec, idx) => (
                <div key={idx} className="flex items-start gap-3 p-3 bg-cascade-stone rounded-lg">
                  <span className="w-6 h-6 bg-cascade-gold/10 text-cascade-gold rounded-full flex items-center justify-center text-xs font-bold shrink-0">
                    {idx + 1}
                  </span>
                  <p className="text-sm text-cascade-charcoal/80 leading-relaxed">{rec}</p>
                </div>
              ))}
            </div>
          </div>
        </>
      )}

      {/* Info when no result yet */}
      {!result && !isLoading && !error && (
        <div className="bg-white rounded-xl border border-cascade-mist p-8 text-center">
          <div className="w-16 h-16 bg-cascade-stone rounded-2xl flex items-center justify-center mx-auto mb-4">
            <Activity size={32} className="text-cascade-sage" />
          </div>
          <h3 className="text-lg font-semibold text-cascade-charcoal mb-2">Multi-Model Bankruptcy Prediction</h3>
          <p className="text-sm text-cascade-sage max-w-lg mx-auto leading-relaxed">
            Select a financial analysis to run 5 prediction models including
            <strong className="text-cascade-charcoal"> Altman Z-Score</strong>,
            <strong className="text-cascade-charcoal"> Springate</strong>,
            <strong className="text-cascade-charcoal"> Ohlson O-Score</strong>, and
            <strong className="text-cascade-charcoal"> Grover Model</strong>.
            Each model uses different statistical approaches to assess financial distress risk.
          </p>
        </div>
      )}
    </div>
  );
}
