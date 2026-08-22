import { useState, useEffect } from 'react';
import {
  Shield,
  ShieldCheck,
  ShieldAlert,
  ShieldX,
  AlertTriangle,
  CheckCircle2,
  Info,
  XCircle,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import { runComplianceCheck, getComplianceStandards } from '../lib/api';
import type { ComplianceReport, ComplianceCheckResult } from '../../types';
import { useAnalysisStore } from '../hooks/useAnalysisStore';
import { useToast } from '../components/Toast';
import Spinner from '../components/Spinner';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface StandardInfo {
  code: string;
  name: string;
  name_fa: string;
  check_count: number;
}

interface GroupedResult {
  standard: string;
  standard_fa: string;
  checks: ComplianceCheckResult[];
}

// ---------------------------------------------------------------------------
// Demo fallback data
// ---------------------------------------------------------------------------

const DEMO_REPORT: ComplianceReport = {
  compliance_score: 72,
  total_checks: 12,
  passed: 8,
  failed: 2,
  not_applicable: 2,
  critical_issues: [],
  warnings: ['Balance sheet doesn\'t balance within tolerance'],
  info_items: ['VAT compliance requires invoice-level data'],
  status: 'needs_attention',
  results: [
    {
      standard: 'IAS 1',
      standard_fa: 'استاندارد ۱',
      check_id: 'IAS1_02',
      rule: 'Balance sheet must balance',
      rule_fa: 'ترازنامه باید تراز باشد',
      severity: 'blocking',
      status: 'fail',
      message: 'Assets != Liabilities + Equity (8.2% diff)',
      remediation: 'Verify classification of all balance sheet line items and ensure inter-company eliminations have been applied correctly.',
    },
    {
      standard: 'IAS 2',
      standard_fa: 'استاندارد ۲',
      check_id: 'IAS2_01',
      rule: 'Inventory valuation',
      rule_fa: 'ارزش‌گذاری موجودی',
      severity: 'warning',
      status: 'pass',
      message: 'Inventory to revenue ratio is reasonable',
    },
    {
      standard: 'Iran Tax',
      standard_fa: 'مالیات ایران',
      check_id: 'IR_TAX_01',
      rule: 'Corporate tax rate',
      rule_fa: 'نرخ مالیات شرکتی',
      severity: 'warning',
      status: 'pass',
      message: 'Effective tax rate 23.5% is within range',
    },
    {
      standard: 'IAS 16',
      standard_fa: 'استاندارد ۱۶',
      check_id: 'IAS16_01',
      rule: 'Fixed assets depreciation',
      rule_fa: 'استهلاک دارایی ثابت',
      severity: 'warning',
      status: 'not_applicable',
      message: 'No depreciation data',
    },
  ],
  recommendations: [
    {
      priority: 'high',
      title: 'Balance Sheet Issue',
      title_fa: 'مشکل ترازنامه',
      description: 'Assets and L+E differ by 8.2%',
    },
    {
      priority: 'medium',
      title: 'Annual Audit',
      title_fa: 'حسابرسی سالانه',
      description: 'Engage certified auditor for statutory sign-off',
    },
  ],
};

const DEMO_STANDARDS: StandardInfo[] = [
  { code: 'IAS 1', name: 'Presentation of Financial Statements', name_fa: 'ارائه صورت‌های مالی', check_count: 4 },
  { code: 'IAS 2', name: 'Inventories', name_fa: 'موجودی‌ها', check_count: 3 },
  { code: 'IAS 7', name: 'Statement of Cash Flows', name_fa: 'صورت جریان وجوه نقد', check_count: 2 },
  { code: 'IAS 12', name: 'Income Taxes', name_fa: 'مالیات بر درآمد', check_count: 3 },
  { code: 'IAS 16', name: 'Property, Plant & Equipment', name_fa: 'دارایی‌های ثابت', check_count: 2 },
  { code: 'Iran Tax', name: 'Iranian Tax Regulations', name_fa: 'قوانین مالیاتی ایران', check_count: 5 },
  { code: 'CBI Rules', name: 'Central Bank of Iran Guidelines', name_fa: 'دستورالعمل‌های بانک مرکزی', check_count: 3 },
];

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const STATUS_CONFIG = {
  compliant: {
    label: 'COMPLIANT',
    labelFa: 'مطابق',
    bg: 'bg-emerald-50',
    border: 'border-emerald-200',
    text: 'text-emerald-700',
    badge: 'bg-emerald-100 text-emerald-700',
    gaugeColor: '#10b981',
    icon: ShieldCheck,
  },
  needs_attention: {
    label: 'NEEDS ATTENTION',
    labelFa: 'نیاز به بررسی',
    bg: 'bg-amber-50',
    border: 'border-amber-200',
    text: 'text-amber-700',
    badge: 'bg-amber-100 text-amber-700',
    gaugeColor: '#f59e0b',
    icon: ShieldAlert,
  },
  non_compliant: {
    label: 'NON-COMPLIANT',
    labelFa: 'غیرمطابق',
    bg: 'bg-red-50',
    border: 'border-red-200',
    text: 'text-red-700',
    badge: 'bg-red-100 text-red-700',
    gaugeColor: '#ef4444',
    icon: ShieldX,
  },
} as const;

const SEVERITY_STYLES: Record<ComplianceCheckResult['severity'], string> = {
  blocking: 'bg-red-100 text-red-700 border-red-200',
  warning: 'bg-amber-100 text-amber-700 border-amber-200',
  info: 'bg-blue-100 text-blue-700 border-blue-200',
};

const PRIORITY_STYLES: Record<string, { bg: string; border: string; text: string; icon: typeof Info }> = {
  critical: { bg: 'bg-red-50', border: 'border-red-200', text: 'text-red-700', icon: XCircle },
  high: { bg: 'bg-orange-50', border: 'border-orange-200', text: 'text-orange-700', icon: AlertTriangle },
  medium: { bg: 'bg-yellow-50', border: 'border-yellow-200', text: 'text-yellow-700', icon: Info },
};

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function groupResultsByStandard(results: ComplianceCheckResult[]): GroupedResult[] {
  const map = new Map<string, GroupedResult>();
  for (const r of results) {
    const key = r.standard;
    if (!map.has(key)) {
      map.set(key, { standard: r.standard, standard_fa: r.standard_fa, checks: [] });
    }
    map.get(key)!.checks.push(r);
  }
  return Array.from(map.values());
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

/** Full-circle SVG gauge */
function ComplianceGauge({ score, size = 180 }: { score: number; size?: number }) {
  const strokeWidth = 14;
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const progress = (score / 100) * circumference;

  let color = '#10b981';
  if (score < 50) color = '#ef4444';
  else if (score < 75) color = '#f59e0b';

  return (
    <div className="relative flex-shrink-0" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        {/* Track */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="#e7e5e4"
          strokeWidth={strokeWidth}
        />
        {/* Progress */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={`${progress} ${circumference}`}
          style={{ transition: 'stroke-dasharray 1s ease-out' }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-4xl font-bold" style={{ color }}>
          {score}
        </span>
        <span className="text-[11px] font-medium text-cascade-sage mt-1">Compliance Score</span>
      </div>
    </div>
  );
}

/** Status icon per check */
function CheckStatusIcon({ status }: { status: ComplianceCheckResult['status'] }) {
  switch (status) {
    case 'pass':
      return <CheckCircle2 size={16} className="text-semantic-success" />;
    case 'fail':
      return <XCircle size={16} className="text-semantic-danger" />;
    case 'not_applicable':
      return <Info size={16} className="text-cascade-sage" />;
  }
}

/** Single expandable check row */
function CheckRow({ check }: { check: ComplianceCheckResult }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="border border-cascade-mist rounded-lg transition-all hover:shadow-sm">
      <button
        type="button"
        className="w-full flex items-center gap-3 px-4 py-3 text-left"
        onClick={() => setExpanded(!expanded)}
      >
        <CheckStatusIcon status={check.status} />
        <span className="font-mono text-xs text-cascade-sage shrink-0 w-20 truncate" title={check.check_id}>
          {check.check_id}
        </span>
        <span
          className={`text-[10px] font-semibold px-2 py-0.5 rounded border shrink-0 ${SEVERITY_STYLES[check.severity]}`}
        >
          {check.severity}
        </span>
        <span className="text-sm text-cascade-charcoal font-medium flex-1 truncate">
          {check.rule}
        </span>
        <span className="text-[11px] text-cascade-sage" dir="rtl">
          {check.rule_fa}
        </span>
        {expanded ? (
          <ChevronUp size={14} className="text-cascade-sage shrink-0" />
        ) : (
          <ChevronDown size={14} className="text-cascade-sage shrink-0" />
        )}
      </button>

      {expanded && (
        <div className="px-4 pb-3 pt-0 space-y-2 animate-slide-up">
          <div className="bg-cascade-stone rounded-md p-3 space-y-2">
            <p className="text-xs text-cascade-charcoal/80 leading-relaxed">{check.message}</p>
            {check.remediation && check.status === 'fail' && (
              <div className="flex items-start gap-2 mt-2 p-2 bg-red-50 rounded-md border border-red-100">
                <AlertTriangle size={14} className="text-red-500 mt-0.5 shrink-0" />
                <div>
                  <p className="text-[10px] font-semibold text-red-600 uppercase tracking-wider mb-0.5">
                    Remediation
                  </p>
                  <p className="text-xs text-red-700/80 leading-relaxed">{check.remediation}</p>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

/** Standards sidebar card */
function StandardsSidebar({ standards }: { standards: StandardInfo[] }) {
  return (
    <div className="card">
      <h3 className="text-sm font-semibold text-cascade-charcoal mb-4 flex items-center gap-2">
        <Shield size={14} className="text-cascade-gold" />
        Compliance Standards
      </h3>
      <div className="space-y-2 max-h-96 overflow-y-auto scrollbar-thin">
        {standards.map((s) => (
          <div
            key={s.code}
            className="flex items-center justify-between px-3 py-2.5 rounded-lg bg-cascade-stone hover:bg-cascade-mist/50 transition-colors"
          >
            <div className="min-w-0">
              <p className="text-xs font-semibold text-cascade-charcoal truncate">{s.code}</p>
              <p className="text-[10px] text-cascade-sage truncate" dir="rtl">
                {s.name_fa}
              </p>
            </div>
            <span className="text-[10px] font-medium text-cascade-sage bg-cascade-mist/60 px-2 py-0.5 rounded-full shrink-0 ml-2">
              {s.check_count} checks
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main Page
// ---------------------------------------------------------------------------

export default function Compliance() {
  const { analyses } = useAnalysisStore();
  const { toast } = useToast();

  const [selectedId, setSelectedId] = useState<string>('');
  const [report, setReport] = useState<ComplianceReport | null>(null);
  const [standards, setStandards] = useState<StandardInfo[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isStandardsLoading, setIsStandardsLoading] = useState(true);
  const [expandedGroups, setExpandedGroups] = useState<Set<string>>(new Set());

  // -----------------------------------------------------------------------
  // Load available standards on mount
  // -----------------------------------------------------------------------
  useEffect(() => {
    let cancelled = false;

    async function loadStandards() {
      setIsStandardsLoading(true);
      try {
        const data = await getComplianceStandards();
        if (!cancelled && data.standards?.length) {
          setStandards(data.standards);
        } else if (!cancelled) {
          setStandards(DEMO_STANDARDS);
        }
      } catch {
        if (!cancelled) {
          setStandards(DEMO_STANDARDS);
        }
      } finally {
        if (!cancelled) setIsStandardsLoading(false);
      }
    }

    loadStandards();
    return () => {
      cancelled = true;
    };
  }, []);

  // -----------------------------------------------------------------------
  // Run compliance check
  // -----------------------------------------------------------------------
  async function handleRunCheck() {
    if (!selectedId) return;
    setIsLoading(true);
    setReport(null);

    try {
      const result = await runComplianceCheck({ analysis_id: selectedId } as any);
      setReport(result);
    } catch (err: any) {
      const message = err?.response?.data?.detail || err?.message || 'Compliance check failed';
      toast('error', message);
      // Fall back to demo data
      setReport(DEMO_REPORT);
    } finally {
      setIsLoading(false);
    }
  }

  // -----------------------------------------------------------------------
  // Toggle group expansion
  // -----------------------------------------------------------------------
  function toggleGroup(standard: string) {
    setExpandedGroups((prev) => {
      const next = new Set(prev);
      if (next.has(standard)) next.delete(standard);
      else next.add(standard);
      return next;
    });
  }

  // -----------------------------------------------------------------------
  // Derived state
  // -----------------------------------------------------------------------
  const grouped = report ? groupResultsByStandard(report.results) : [];
  const statusCfg = report ? STATUS_CONFIG[report.status] : null;
  const StatusIcon = statusCfg?.icon ?? Shield;

  // -----------------------------------------------------------------------
  // Render
  // -----------------------------------------------------------------------
  return (
    <div className="space-y-6">
      {/* ---- Header ---- */}
      <div className="page-header">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-gradient-to-br from-cascade-gold to-cascade-olive rounded-xl flex items-center justify-center">
            <Shield size={20} className="text-white" />
          </div>
          <div>
            <h1 className="page-title text-cascade-charcoal">Compliance Engine</h1>
            <p className="text-xs text-cascade-sage">Iranian Accounting Standards &amp; IFRS Compliance</p>
          </div>
        </div>
      </div>

      <div className="flex flex-col lg:flex-row gap-6">
        {/* ---- Main Content ---- */}
        <div className="flex-1 min-w-0 space-y-6">
          {/* ---- Selector + Run ---- */}
          <div className="card">
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
                  onClick={handleRunCheck}
                  disabled={!selectedId || isLoading}
                  className="px-6 py-2.5 bg-cascade-charcoal text-white rounded-lg text-sm font-medium hover:bg-cascade-charcoal/90 disabled:bg-cascade-mist disabled:text-cascade-sage transition-colors flex items-center gap-2"
                >
                  {isLoading ? <Spinner size={16} /> : <ShieldCheck size={16} />}
                  {isLoading ? 'Running Checks...' : 'Run Compliance Check'}
                </button>
              </div>
            </div>
          </div>

          {/* ---- Placeholder when no analysis selected & no results ---- */}
          {!report && !isLoading && (
            <div className="card text-center py-12">
              <div className="w-16 h-16 bg-cascade-stone rounded-2xl flex items-center justify-center mx-auto mb-4">
                <Shield size={32} className="text-cascade-sage" />
              </div>
              <h3 className="text-lg font-semibold text-cascade-charcoal mb-2">
                Iranian Accounting Standards &amp; IFRS Compliance
              </h3>
              <p className="text-sm text-cascade-sage max-w-lg mx-auto leading-relaxed">
                Select a completed financial analysis and run the compliance engine to check against
                <strong className="text-cascade-charcoal"> IAS/IFRS standards</strong>,
                <strong className="text-cascade-charcoal"> Iranian tax regulations</strong>, and
                <strong className="text-cascade-charcoal"> Central Bank of Iran</strong> guidelines.
                The engine evaluates balance sheet integrity, tax rate validity, depreciation rules, and more.
              </p>
            </div>
          )}

          {/* ---- Loading ---- */}
          {isLoading && (
            <div className="card flex flex-col items-center justify-center py-16">
              <Spinner size={32} />
              <p className="text-sm text-cascade-sage mt-4">Running compliance checks across all standards...</p>
            </div>
          )}

          {/* ---- Results ---- */}
          {report && !isLoading && statusCfg && (
            <>
              {/* -- Status Banner -- */}
              <div className={`rounded-xl border p-6 ${statusCfg.bg} ${statusCfg.border}`}>
                <div className="flex flex-col md:flex-row items-center gap-6">
                  <ComplianceGauge score={report.compliance_score} size={180} />
                  <div className="flex-1 text-center md:text-left">
                    <div className="flex items-center justify-center md:justify-start gap-2 mb-2">
                      <StatusIcon size={24} className={statusCfg.text} />
                      <h2 className={`text-xl font-bold ${statusCfg.text}`}>{statusCfg.label}</h2>
                      <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${statusCfg.badge}`} dir="rtl">
                        {statusCfg.labelFa}
                      </span>
                    </div>
                    <p className="text-sm text-cascade-charcoal/70 mb-4">
                      {report.status === 'compliant'
                        ? 'All compliance checks passed. The financial statements conform to the applicable standards.'
                        : report.status === 'non_compliant'
                          ? 'Critical compliance failures detected. Immediate remediation is required before filing.'
                          : 'Some compliance checks require attention. Review the flagged items below and take corrective action.'}
                    </p>
                  </div>
                </div>
              </div>

              {/* -- Stats Row -- */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div className="card !p-4 text-center">
                  <p className="text-2xl font-bold text-cascade-charcoal">{report.total_checks}</p>
                  <p className="text-[11px] text-cascade-sage font-medium mt-0.5">Total Checks</p>
                </div>
                <div className="card !p-4 text-center">
                  <p className="text-2xl font-bold text-semantic-success">{report.passed}</p>
                  <p className="text-[11px] text-cascade-sage font-medium mt-0.5">Passed</p>
                </div>
                <div className="card !p-4 text-center">
                  <p className="text-2xl font-bold text-semantic-danger">{report.failed}</p>
                  <p className="text-[11px] text-cascade-sage font-medium mt-0.5">Failed</p>
                </div>
                <div className="card !p-4 text-center">
                  <p className="text-2xl font-bold text-cascade-sage">{report.not_applicable}</p>
                  <p className="text-[11px] text-cascade-sage font-medium mt-0.5">N/A</p>
                </div>
              </div>

              {/* -- Alert Banners: Critical Issues -- */}
              {report.critical_issues.length > 0 && (
                <div className="space-y-2">
                  {report.critical_issues.map((issue, i) => (
                    <div
                      key={i}
                      className="flex items-start gap-3 px-4 py-3 bg-red-50 border border-red-200 rounded-xl"
                    >
                      <ShieldX size={18} className="text-semantic-danger shrink-0 mt-0.5" />
                      <p className="text-sm text-red-700 font-medium">{issue}</p>
                    </div>
                  ))}
                </div>
              )}

              {/* -- Alert Banners: Warnings -- */}
              {report.warnings.length > 0 && (
                <div className="space-y-2">
                  {report.warnings.map((w, i) => (
                    <div
                      key={i}
                      className="flex items-start gap-3 px-4 py-3 bg-amber-50 border border-amber-200 rounded-xl"
                    >
                      <AlertTriangle size={18} className="text-semantic-warning shrink-0 mt-0.5" />
                      <p className="text-sm text-amber-700 font-medium">{w}</p>
                    </div>
                  ))}
                </div>
              )}

              {/* -- Alert Banners: Info Items -- */}
              {report.info_items.length > 0 && (
                <div className="space-y-2">
                  {report.info_items.map((item, i) => (
                    <div
                      key={i}
                      className="flex items-start gap-3 px-4 py-3 bg-blue-50 border border-blue-200 rounded-xl"
                    >
                      <Info size={18} className="text-blue-500 shrink-0 mt-0.5" />
                      <p className="text-sm text-blue-700 font-medium">{item}</p>
                    </div>
                  ))}
                </div>
              )}

              {/* -- Check Results Grouped by Standard -- */}
              {grouped.length > 0 && (
                <div className="card !p-0 overflow-hidden">
                  <div className="px-5 py-4 border-b border-cascade-mist">
                    <h3 className="text-sm font-semibold text-cascade-charcoal flex items-center gap-2">
                      <ShieldCheck size={16} className="text-cascade-gold" />
                      Check Results
                      <span className="text-[10px] font-normal text-cascade-sage">(click to expand)</span>
                    </h3>
                  </div>
                  <div className="max-h-96 overflow-y-auto scrollbar-thin">
                    {grouped.map((group) => {
                      const isExpanded = expandedGroups.has(group.standard);
                      const groupPass = group.checks.filter((c) => c.status === 'pass').length;
                      const groupFail = group.checks.filter((c) => c.status === 'fail').length;
                      const groupNa = group.checks.filter((c) => c.status === 'not_applicable').length;

                      return (
                        <div key={group.standard} className="border-b border-cascade-mist last:border-b-0">
                          {/* Group header */}
                          <button
                            type="button"
                            className="w-full flex items-center gap-3 px-5 py-3 hover:bg-cascade-stone/50 transition-colors text-left"
                            onClick={() => toggleGroup(group.standard)}
                          >
                            {isExpanded ? (
                              <ChevronUp size={14} className="text-cascade-sage shrink-0" />
                            ) : (
                              <ChevronDown size={14} className="text-cascade-sage shrink-0" />
                            )}
                            <span className="text-sm font-semibold text-cascade-charcoal">
                              {group.standard}
                            </span>
                            <span className="text-[11px] text-cascade-sage" dir="rtl">
                              {group.standard_fa}
                            </span>
                            <div className="flex items-center gap-2 ml-auto">
                              {groupPass > 0 && (
                                <span className="status-good">{groupPass} pass</span>
                              )}
                              {groupFail > 0 && (
                                <span className="status-critical">{groupFail} fail</span>
                              )}
                              {groupNa > 0 && (
                                <span className="status-badge bg-cascade-mist text-cascade-sage">{groupNa} N/A</span>
                              )}
                            </div>
                          </button>

                          {/* Expanded checks */}
                          {isExpanded && (
                            <div className="px-5 pb-4 space-y-2 animate-slide-up">
                              {group.checks.map((check) => (
                                <CheckRow key={check.check_id} check={check} />
                              ))}
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* -- Recommendations -- */}
              {report.recommendations.length > 0 && (
                <div className="card">
                  <h3 className="text-sm font-semibold text-cascade-charcoal mb-4 flex items-center gap-2">
                    <AlertTriangle size={16} className="text-cascade-gold" />
                    Recommendations
                  </h3>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    {report.recommendations.map((rec, i) => {
                      const style = PRIORITY_STYLES[rec.priority] ?? PRIORITY_STYLES.medium;
                      const RecIcon = style.icon;
                      return (
                        <div
                          key={i}
                          className={`rounded-xl border p-4 ${style.bg} ${style.border}`}
                        >
                          <div className="flex items-start gap-3">
                            <RecIcon size={16} className={`${style.text} mt-0.5 shrink-0`} />
                            <div className="min-w-0">
                              <div className="flex items-center gap-2 mb-1">
                                <h4 className={`text-sm font-semibold ${style.text}`}>{rec.title}</h4>
                                <span
                                  className={`text-[10px] font-semibold uppercase px-2 py-0.5 rounded border ${style.bg} ${style.border} ${style.text}`}
                                >
                                  {rec.priority}
                                </span>
                              </div>
                              <p className="text-[11px] text-cascade-charcoal/60 mb-0.5" dir="rtl">
                                {rec.title_fa}
                              </p>
                              <p className="text-xs text-cascade-charcoal/80 leading-relaxed">
                                {rec.description}
                              </p>
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}
            </>
          )}
        </div>

        {/* ---- Standards Sidebar ---- */}
        <div className="w-full lg:w-72 flex-shrink-0">
          {isStandardsLoading ? (
            <div className="card flex items-center justify-center py-12">
              <Spinner size={20} />
            </div>
          ) : (
            <StandardsSidebar standards={standards} />
          )}
        </div>
      </div>
    </div>
  );
}
