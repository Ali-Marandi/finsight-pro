import { AlertTriangle, CheckCircle2, FileSearch, MapPin, ShieldCheck } from 'lucide-react';
import type { EvidenceIssue, EvidenceLocation, TaxAuditEvidenceResult } from '../../types';

interface TaxAuditEvidenceReviewProps {
  evidence: TaxAuditEvidenceResult;
  onContinue: () => void;
  onStartOver: () => void;
}

const severityStyles = {
  blocking: 'border-semantic-danger/30 bg-semantic-danger/5 text-semantic-danger',
  warning: 'border-semantic-warning/30 bg-semantic-warning/5 text-semantic-warning',
  info: 'border-cascade-gold/30 bg-cascade-gold/5 text-cascade-sage',
};

function conceptLabel(concept: string): string {
  return concept.split('_').map((word) => word[0].toUpperCase() + word.slice(1)).join(' ');
}

function formatValue(value: number, currency: string | null, locale: string | null): string {
  const formatLocale = locale === 'fa' ? 'fa-IR' : 'en-US';
  if (currency && ['USD', 'IRR', 'IRT'].includes(currency)) {
    return new Intl.NumberFormat(formatLocale, { style: 'currency', currency, maximumFractionDigits: 2 }).format(value);
  }
  return new Intl.NumberFormat(formatLocale, { maximumFractionDigits: 2 }).format(value);
}

function EvidenceLocationLabel({ location }: { location: EvidenceLocation }) {
  const parts = [
    location.page_number ? `Page ${location.page_number}` : null,
    location.table_index ? `Table ${location.table_index}` : null,
    location.cell_reference || null,
  ].filter(Boolean);
  return <span className="inline-flex items-center gap-1 rounded-md bg-cascade-mist/70 px-2 py-1 text-xs text-cascade-sage"><MapPin size={12} />{parts.join(' · ') || 'Source reference'}</span>;
}

function IssueCard({ issue }: { issue: EvidenceIssue }) {
  return (
    <article className={`rounded-lg border p-4 ${severityStyles[issue.severity]}`}>
      <div className="flex flex-wrap items-center gap-2">
        <span className="rounded-full bg-white/70 px-2 py-0.5 text-xs font-semibold uppercase">{issue.severity}</span>
        <span className="text-sm font-semibold text-cascade-charcoal">{issue.message}</span>
      </div>
      <p className="mt-2 text-sm text-cascade-sage">{issue.remediation}</p>
      {!!issue.evidence_locations?.length && (
        <div className="mt-3 flex flex-wrap gap-2">
          {issue.evidence_locations.map((location, index) => <EvidenceLocationLabel key={`${location.file_name}-${location.page_number}-${index}`} location={location} />)}
        </div>
      )}
    </article>
  );
}

export default function TaxAuditEvidenceReview({ evidence, onContinue, onStartOver }: TaxAuditEvidenceReviewProps) {
  const blockers = evidence.issues.filter((issue) => issue.severity === 'blocking').length;
  const warnings = evidence.issues.filter((issue) => issue.severity === 'warning').length;
  const localizedFacts = [...evidence.facts].sort((left, right) => left.concept_id.localeCompare(right.concept_id));

  return (
    <section className="mx-auto max-w-6xl space-y-6">
      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-start">
        <div className="flex items-start gap-3">
          <div className="rounded-xl bg-cascade-gold/10 p-3 text-cascade-gold"><FileSearch size={22} /></div>
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.14em] text-cascade-sage">Tax Audit Evidence Review</p>
            <h1 className="mt-1 text-2xl font-bold text-cascade-charcoal">{evidence.manifest.file_name}</h1>
            <p className="mt-1 text-sm text-cascade-sage">{evidence.manifest.detected_locale || 'undetected locale'} · {evidence.extraction_mode.replace(/_/g, ' ')} · {evidence.manifest.row_count} extracted text lines</p>
          </div>
        </div>
        <button onClick={onStartOver} className="btn-secondary">Choose another file</button>
      </div>

      <div className={`flex flex-col gap-4 rounded-xl border p-5 sm:flex-row sm:items-center sm:justify-between ${evidence.ready_for_review ? 'border-semantic-success/30 bg-semantic-success/5' : 'border-semantic-danger/30 bg-semantic-danger/5'}`}>
        <div className="flex items-start gap-3">
          {evidence.ready_for_review ? <CheckCircle2 className="mt-0.5 text-semantic-success" size={22} /> : <AlertTriangle className="mt-0.5 text-semantic-danger" size={22} />}
          <div>
            <h2 className="font-semibold text-cascade-charcoal">{evidence.ready_for_review ? 'Evidence is ready for reviewer judgement' : 'Evidence requires OCR or manual review'}</h2>
            <p className="mt-1 text-sm text-cascade-sage">{localizedFacts.length} extracted facts · {blockers} blocking issue(s) · {warnings} warning(s)</p>
          </div>
        </div>
        {evidence.ready_for_review && <button onClick={onContinue} className="btn-primary">Continue to financial analysis</button>}
      </div>

      <div className="grid gap-6 lg:grid-cols-[1fr_320px]">
        <div className="card overflow-hidden p-0">
          <div className="border-b border-cascade-mist p-5">
            <h2 className="font-semibold text-cascade-charcoal">Extracted tax facts</h2>
            <p className="mt-1 text-sm text-cascade-sage">Each value remains a proposal until a professional reviewer resolves relevant warnings and signs off.</p>
          </div>
          {localizedFacts.length === 0 ? (
            <div className="p-5 text-sm text-cascade-sage">No tax facts can be safely shown for this document.</div>
          ) : (
            <div className="overflow-x-auto px-5">
              <table className="w-full min-w-[680px] text-left">
                <thead><tr className="border-b border-cascade-mist text-xs uppercase tracking-wide text-cascade-sage"><th className="py-3 pr-4">Concept</th><th className="py-3 pr-4">Value</th><th className="py-3 pr-4">Period</th><th className="py-3">Evidence citation</th></tr></thead>
                <tbody>{localizedFacts.map((fact, index) => (
                  <tr key={`${fact.concept_id}-${index}`} className="border-b border-cascade-mist last:border-0">
                    <td className="py-3 pr-4 font-medium text-cascade-charcoal">{conceptLabel(fact.concept_id)}</td>
                    <td className="py-3 pr-4 font-semibold text-cascade-charcoal">{formatValue(fact.value, fact.currency, evidence.manifest.detected_locale)}</td>
                    <td className="py-3 pr-4 text-sm text-cascade-sage">{fact.period}</td>
                    <td className="py-3"><div className="flex flex-wrap gap-2">{fact.locations.map((location, locationIndex) => <EvidenceLocationLabel key={`${fact.concept_id}-${locationIndex}`} location={location} />)}</div></td>
                  </tr>
                ))}</tbody>
              </table>
            </div>
          )}
        </div>

        <aside className="space-y-4">
          <div className="card">
            <div className="flex items-center gap-2"><ShieldCheck size={20} className="text-cascade-gold" /><h2 className="font-semibold text-cascade-charcoal">Source integrity</h2></div>
            <dl className="mt-4 space-y-3 text-sm">
              <div><dt className="text-cascade-sage">File type</dt><dd className="mt-1 font-medium text-cascade-charcoal">{evidence.manifest.source_type.toUpperCase()}</dd></div>
              <div><dt className="text-cascade-sage">Evidence hash</dt><dd className="mt-1 break-all font-mono text-xs text-cascade-charcoal">{evidence.manifest.file_hash}</dd></div>
              <div><dt className="text-cascade-sage">Review principle</dt><dd className="mt-1 text-cascade-charcoal">No AI-generated conclusion is treated as a final tax position.</dd></div>
            </dl>
          </div>
          <div className="card">
            <h2 className="font-semibold text-cascade-charcoal">Reviewer checklist</h2>
            <ol className="mt-3 space-y-2 text-sm text-cascade-sage list-decimal pl-5"><li>Open every cited source for material findings.</li><li>Resolve conflicting figures and missing evidence.</li><li>Confirm jurisdiction and period before any filing decision.</li></ol>
          </div>
        </aside>
      </div>

      <div className="card">
        <div className="flex items-center gap-2"><AlertTriangle size={20} className="text-cascade-gold" /><h2 className="font-semibold text-cascade-charcoal">Evidence Health</h2></div>
        {evidence.issues.length === 0 ? <p className="mt-4 text-sm text-cascade-sage">No extraction or reconciliation issues were found.</p> : <div className="mt-4 space-y-3">{evidence.issues.map((issue) => <IssueCard key={`${issue.rule_id}-${issue.message}`} issue={issue} />)}</div>}
      </div>
    </section>
  );
}
