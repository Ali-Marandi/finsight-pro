import { useEffect, useState } from 'react';
import { AlertTriangle, CheckCircle2, FileSearch, ShieldCheck } from 'lucide-react';
import type { EvidenceMapping, EvidenceReviewResult } from '../../types';

interface EvidenceReviewProps {
  evidence: EvidenceReviewResult;
  isRefreshing?: boolean;
  onConfirmMappings: (overrides: Record<string, string | null>) => void;
  onContinue: () => void;
  onStartOver: () => void;
}

const CANONICAL_CONCEPTS = [
  'period', 'revenue', 'gross_profit', 'operating_income', 'net_income',
  'total_assets', 'current_assets', 'inventory', 'cash', 'total_liabilities',
  'current_liabilities', 'equity', 'operating_cash_flow', 'interest_expense',
  'cost_of_goods_sold', 'accounts_receivable',
];

const severityStyles = {
  blocking: 'border-semantic-danger/30 bg-semantic-danger/5 text-semantic-danger',
  warning: 'border-semantic-warning/30 bg-semantic-warning/5 text-semantic-warning',
  info: 'border-cascade-gold/30 bg-cascade-gold/5 text-cascade-sage',
};

function MappingRow({ mapping, decision, onChange }: {
  mapping: EvidenceMapping;
  decision: string | null | undefined;
  onChange: (value: string | null) => void;
}) {
  return (
    <tr className="border-b border-cascade-mist last:border-0">
      <td className="py-3 pr-4">
        <p className="font-medium text-cascade-charcoal">{mapping.source_column}</p>
        <p className="mt-1 text-xs text-cascade-sage">{mapping.rationale}</p>
      </td>
      <td className="py-3 pr-4">
        <select
          value={decision ?? ''}
          onChange={(event) => onChange(event.target.value || null)}
          className="w-full rounded-lg border border-cascade-mist bg-white px-3 py-2 text-sm text-cascade-charcoal outline-none focus:border-cascade-gold"
        >
          <option value="">Exclude from current model</option>
          {CANONICAL_CONCEPTS.map((concept) => <option key={concept} value={concept}>{concept}</option>)}
        </select>
      </td>
      <td className="py-3 pr-4 text-sm font-medium text-cascade-charcoal">{Math.round(mapping.confidence * 100)}%</td>
      <td className="py-3"><span className="rounded-full bg-cascade-gold/10 px-2 py-1 text-xs font-semibold text-cascade-gold">Suggested</span></td>
    </tr>
  );
}

export default function EvidenceReview({ evidence, isRefreshing = false, onConfirmMappings, onContinue, onStartOver }: EvidenceReviewProps) {
  const suggestedMappings = evidence.mappings.filter((mapping) => mapping.status === 'suggested');
  const [decisions, setDecisions] = useState<Record<string, string | null>>({});

  useEffect(() => {
    setDecisions(Object.fromEntries(suggestedMappings.map((mapping) => [mapping.source_column, mapping.concept_id])));
  }, [evidence]);

  return (
    <section className="mx-auto max-w-5xl space-y-6">
      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-start">
        <div className="flex items-start gap-3">
          <div className="rounded-xl bg-cascade-gold/10 p-3 text-cascade-gold"><FileSearch size={22} /></div>
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.14em] text-cascade-sage">Evidence Review</p>
            <h1 className="mt-1 text-2xl font-bold text-cascade-charcoal">{evidence.manifest.file_name}</h1>
            <p className="mt-1 text-sm text-cascade-sage">{evidence.manifest.row_count} rows · {evidence.manifest.column_count} columns · {evidence.manifest.detected_locale || 'undetected locale'}</p>
          </div>
        </div>
        <button onClick={onStartOver} className="btn-secondary">Choose another file</button>
      </div>

      <div className={`flex flex-col gap-4 rounded-xl border p-5 sm:flex-row sm:items-center sm:justify-between ${evidence.ready_for_analysis ? 'border-semantic-success/30 bg-semantic-success/5' : 'border-semantic-danger/30 bg-semantic-danger/5'}`}>
        <div className="flex items-start gap-3">
          {evidence.ready_for_analysis ? <CheckCircle2 className="mt-0.5 text-semantic-success" size={22} /> : <AlertTriangle className="mt-0.5 text-semantic-danger" size={22} />}
          <div>
            <h2 className="font-semibold text-cascade-charcoal">{evidence.ready_for_analysis ? 'Evidence is ready for analysis' : 'Analysis is blocked until evidence is resolved'}</h2>
            <p className="mt-1 text-sm text-cascade-sage">{evidence.health.blocking} blocking issue(s) · {evidence.health.warning} warning(s)</p>
          </div>
        </div>
        {evidence.ready_for_analysis && <button onClick={onContinue} className="btn-primary">Continue to analysis</button>}
      </div>

      {suggestedMappings.length > 0 && (
        <div className="card overflow-hidden p-0">
          <div className="flex flex-col gap-4 border-b border-cascade-mist p-5 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h2 className="font-semibold text-cascade-charcoal">Review proposed mappings</h2>
              <p className="mt-1 text-sm text-cascade-sage">Confirm detected aliases before the statement can be analyzed.</p>
            </div>
            <button onClick={() => onConfirmMappings(decisions)} disabled={isRefreshing} className="btn-primary whitespace-nowrap disabled:cursor-not-allowed disabled:opacity-50">
              {isRefreshing ? 'Rechecking evidence…' : 'Confirm and recheck'}
            </button>
          </div>
          <div className="overflow-x-auto px-5">
            <table className="w-full min-w-[700px] text-left">
              <thead><tr className="text-xs uppercase tracking-wide text-cascade-sage"><th className="py-3 pr-4">Source column</th><th className="py-3 pr-4">Canonical concept</th><th className="py-3 pr-4">Confidence</th><th className="py-3">Status</th></tr></thead>
              <tbody>{suggestedMappings.map((mapping) => (
                <MappingRow
                  key={mapping.source_column}
                  mapping={mapping}
                  decision={decisions[mapping.source_column]}
                  onChange={(value) => setDecisions((current) => ({ ...current, [mapping.source_column]: value }))}
                />
              ))}</tbody>
            </table>
          </div>
        </div>
      )}

      <div className="card">
        <div className="flex items-center gap-2"><ShieldCheck size={20} className="text-cascade-gold" /><h2 className="font-semibold text-cascade-charcoal">Evidence Health</h2></div>
        {evidence.issues.length === 0 ? (
          <p className="mt-4 text-sm text-cascade-sage">No evidence-health issues were found.</p>
        ) : (
          <div className="mt-4 space-y-3">
            {evidence.issues.map((issue) => (
              <article key={`${issue.rule_id}-${issue.message}`} className={`rounded-lg border p-4 ${severityStyles[issue.severity]}`}>
                <div className="flex flex-wrap items-center gap-2"><span className="rounded-full bg-white/70 px-2 py-0.5 text-xs font-semibold uppercase">{issue.severity}</span><span className="text-sm font-semibold text-cascade-charcoal">{issue.message}</span></div>
                <p className="mt-2 text-sm text-cascade-sage">{issue.remediation}</p>
              </article>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}
