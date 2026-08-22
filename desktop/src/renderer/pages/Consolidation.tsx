import { useState } from 'react';
import { consolidateCompanies } from '../lib/api';
import type { ConsolidationResult, ConsolidatedCompany, RatioResult } from '../../types';
import { useToast } from '../components/Toast';
import Spinner from '../components/Spinner';
import { Merge, Plus, Trash2, Building2, PieChart, ArrowRight, TrendingUp, AlertTriangle, Minus } from 'lucide-react';
import { cn, formatPercent, formatRatio, getStatusColor, getStatusBg } from '../lib/utils';

// ── Helpers ──────────────────────────────────────────────────────────────────

function formatNumber(value: number): string {
  return new Intl.NumberFormat('en-US', {
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value);
}

function formatCurrency(value: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value);
}

// ── Types ────────────────────────────────────────────────────────────────────

interface FinancialField {
  key: string;
  label: string;
  step?: number;
}

const FINANCIAL_FIELDS: FinancialField[] = [
  { key: 'revenue', label: 'Revenue', step: 1000 },
  { key: 'cogs', label: 'COGS', step: 1000 },
  { key: 'net_income', label: 'Net Income', step: 1000 },
  { key: 'ebit', label: 'EBIT', step: 1000 },
  { key: 'total_assets', label: 'Total Assets', step: 1000 },
  { key: 'total_equity', label: 'Total Equity', step: 1000 },
  { key: 'total_liabilities', label: 'Total Liabilities', step: 1000 },
  { key: 'interest_expense', label: 'Interest Expense', step: 1000 },
  { key: 'current_assets', label: 'Current Assets', step: 1000 },
  { key: 'current_liabilities', label: 'Current Liabilities', step: 1000 },
  { key: 'inventory', label: 'Inventory', step: 1000 },
  { key: 'cash', label: 'Cash', step: 1000 },
  { key: 'accounts_receivable', label: 'Accounts Receivable', step: 1000 },
];

interface CompanyInput {
  id: string;
  name: string;
  ownership: number;
  financials: Record<string, number>;
  expanded: boolean;
}

const DEMO_COMPANIES: Omit<CompanyInput, 'id' | 'expanded'>[] = [
  {
    name: 'Persian Holdings',
    ownership: 100,
    financials: {
      revenue: 500000,
      cogs: 300000,
      net_income: 80000,
      ebit: 120000,
      total_assets: 800000,
      total_equity: 400000,
      total_liabilities: 400000,
      interest_expense: 20000,
      current_assets: 250000,
      current_liabilities: 150000,
      inventory: 80000,
      cash: 50000,
      accounts_receivable: 70000,
    },
  },
  {
    name: 'Pars Tech Co.',
    ownership: 60,
    financials: {
      revenue: 200000,
      cogs: 100000,
      net_income: 40000,
      ebit: 60000,
      total_assets: 300000,
      total_equity: 180000,
      total_liabilities: 120000,
      interest_expense: 5000,
      current_assets: 120000,
      current_liabilities: 60000,
      inventory: 30000,
      cash: 25000,
      accounts_receivable: 35000,
    },
  },
];

function createBlankCompany(): CompanyInput {
  const financials: Record<string, number> = {};
  FINANCIAL_FIELDS.forEach((f) => {
    financials[f.key] = 0;
  });
  return {
    id: Date.now().toString(36) + Math.random().toString(36).slice(2),
    name: '',
    ownership: 100,
    financials,
    expanded: true,
  };
}

function initDemoCompanies(): CompanyInput[] {
  return DEMO_COMPANIES.map((dc) => ({
    ...dc,
    id: Date.now().toString(36) + Math.random().toString(36).slice(2),
    expanded: false,
  }));
}

// ── Financial label display ──────────────────────────────────────────────────

const FINANCIAL_LABELS: Record<string, string> = {
  revenue: 'Revenue',
  cogs: 'Cost of Goods Sold',
  net_income: 'Net Income',
  ebit: 'EBIT',
  total_assets: 'Total Assets',
  total_equity: 'Total Equity',
  total_liabilities: 'Total Liabilities',
  interest_expense: 'Interest Expense',
  current_assets: 'Current Assets',
  current_liabilities: 'Current Liabilities',
  inventory: 'Inventory',
  cash: 'Cash',
  accounts_receivable: 'Accounts Receivable',
  minority_interest: 'Minority Interest',
  consolidated_revenue: 'Consolidated Revenue',
  consolidated_net_income: 'Consolidated Net Income',
  consolidated_ebit: 'Consolidated EBIT',
  consolidated_total_assets: 'Consolidated Total Assets',
  consolidated_total_equity: 'Consolidated Total Equity',
  consolidated_total_liabilities: 'Consolidated Total Liabilities',
};

function getFinancialLabel(key: string): string {
  return FINANCIAL_LABELS[key] || key.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
}

// ── Component ────────────────────────────────────────────────────────────────

export default function Consolidation() {
  const [companies, setCompanies] = useState<CompanyInput[]>(initDemoCompanies);
  const [result, setResult] = useState<ConsolidationResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const { toast } = useToast();

  // ── Company management ───────────────────────────────────────────────────

  const addCompany = () => {
    setCompanies((prev) => [...prev, createBlankCompany()]);
  };

  const removeCompany = (id: string) => {
    if (companies.length <= 1) {
      toast('warning', 'At least one company is required');
      return;
    }
    setCompanies((prev) => prev.filter((c) => c.id !== id));
    setResult(null);
  };

  const updateCompany = (id: string, field: string, value: string | number) => {
    setCompanies((prev) =>
      prev.map((c) => {
        if (c.id !== id) return c;
        if (field === 'name') return { ...c, name: value as string };
        if (field === 'ownership') return { ...c, ownership: Number(value) || 0 };
        if (field === 'expanded') return { ...c, expanded: Boolean(value) };
        return { ...c, financials: { ...c.financials, [field]: Number(value) || 0 } };
      }),
    );
  };

  // ── Consolidation ───────────────────────────────────────────────────────

  const handleConsolidate = async () => {
    const validCompanies = companies.filter((c) => c.name.trim() !== '');
    if (validCompanies.length < 2) {
      toast('warning', 'At least 2 named companies are required for consolidation');
      return;
    }

    setIsLoading(true);
    setResult(null);

    try {
      const payload: ConsolidatedCompany[] = validCompanies.map((c) => ({
        company_name: c.name.trim(),
        ownership_pct: Math.min(100, Math.max(0, c.ownership)),
        financial_data: { ...c.financials },
      }));

      const res = await consolidateCompanies(payload);
      setResult(res);
      toast('success', `Consolidation complete: ${res.company_count} companies merged`);
    } catch (err: any) {
      toast('error', `Consolidation failed: ${err.message || 'Unknown error'}`);
    } finally {
      setIsLoading(false);
    }
  };

  // ── Compute minority interest locally for stats ─────────────────────────

  const minorityInterest = result
    ? Object.entries(result.eliminations).reduce((sum, [, v]) => sum + Math.abs(v), 0)
    : 0;

  const consolidatedRevenue = result?.consolidated_financials?.revenue ?? 0;
  const consolidatedNetIncome = result?.consolidated_financials?.net_income ?? 0;

  // ── Ratio categories ────────────────────────────────────────────────────

  const ratioCategories = result
    ? (['profitability', 'liquidity', 'leverage', 'efficiency'] as const).filter((cat) =>
        result.ratios.some((r) => r.category === cat),
      )
    : [];

  const BAR_COLORS = [
    'bg-cascade-gold',
    'bg-cascade-olive',
    'bg-cascade-sage',
    'bg-cascade-charcoal/70',
    'bg-semantic-success',
    'bg-semantic-warning',
  ];

  // ── Render ──────────────────────────────────────────────────────────────

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title">Consolidation Engine</h1>
          <p className="text-cascade-sage text-sm mt-1">
            Combine financial statements from multiple companies
          </p>
        </div>
      </div>

      {/* Company List Builder */}
      <section>
        <div className="flex items-center gap-2 mb-4">
          <Building2 size={18} className="text-cascade-gold" />
          <h2 className="text-lg font-semibold">Company List</h2>
          <span className="text-xs text-cascade-sage bg-cascade-mist rounded-full px-2.5 py-0.5">
            {companies.length} {companies.length === 1 ? 'company' : 'companies'}
          </span>
        </div>

        <div className="space-y-3">
          {companies.map((company, idx) => (
            <div key={company.id} className="card !p-0 overflow-hidden">
              {/* Collapsed row — always visible */}
              <div className="flex items-center gap-3 px-4 py-3">
                <span className="flex items-center justify-center w-7 h-7 rounded-full bg-cascade-gold/10 text-cascade-gold text-xs font-bold shrink-0">
                  {idx + 1}
                </span>

                <input
                  type="text"
                  value={company.name}
                  onChange={(e) => updateCompany(company.id, 'name', e.target.value)}
                  placeholder="Company name"
                  className="input-field !py-2 flex-1 min-w-0"
                />

                <div className="flex items-center gap-1.5 shrink-0">
                  <label className="text-xs text-cascade-sage whitespace-nowrap">Ownership</label>
                  <div className="relative w-20">
                    <input
                      type="number"
                      min={0}
                      max={100}
                      step={1}
                      value={company.ownership}
                      onChange={(e) => updateCompany(company.id, 'ownership', e.target.value)}
                      className="input-field !py-2 !pr-7 text-right"
                    />
                    <span className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-cascade-sage pointer-events-none">
                      %
                    </span>
                  </div>
                </div>

                <button
                  onClick={() => setCompanies((prev) => prev.map((c) => c.id === company.id ? { ...c, expanded: !c.expanded } : c))}
                  className={cn(
                    'p-2 rounded-lg transition-colors shrink-0',
                    company.expanded
                      ? 'bg-cascade-gold/10 text-cascade-gold'
                      : 'text-cascade-sage hover:text-cascade-charcoal hover:bg-cascade-mist/50',
                  )}
                  title={company.expanded ? 'Collapse financials' : 'Expand financials'}
                >
                  <ArrowRight
                    size={16}
                    className={cn('transition-transform duration-200', company.expanded && 'rotate-90')}
                  />
                </button>

                <button
                  onClick={() => removeCompany(company.id)}
                  className="p-2 rounded-lg text-cascade-sage hover:text-semantic-danger hover:bg-semantic-danger/10 transition-colors shrink-0"
                  title="Remove company"
                >
                  <Trash2 size={16} />
                </button>
              </div>

              {/* Expanded financial fields */}
              {company.expanded && (
                <div className="px-4 pb-4 pt-1 border-t border-cascade-mist">
                  <p className="text-xs text-cascade-sage mb-3 font-medium uppercase tracking-wider">
                    Financial Data
                  </p>
                  <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
                    {FINANCIAL_FIELDS.map((field) => (
                      <div key={field.key}>
                        <label className="block text-xs text-cascade-sage mb-1">
                          {field.label}
                        </label>
                        <input
                          type="number"
                          min={0}
                          step={field.step ?? 1000}
                          value={company.financials[field.key] || ''}
                          onChange={(e) =>
                            updateCompany(company.id, field.key, e.target.value)
                          }
                          placeholder="0"
                          className="input-field !py-2 text-right"
                        />
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>

        {/* Add Company Button */}
        <button
          onClick={addCompany}
          className="mt-3 flex items-center gap-2 px-4 py-2.5 rounded-lg border border-dashed border-cascade-mist text-cascade-sage hover:text-cascade-gold hover:border-cascade-gold transition-colors text-sm font-medium"
        >
          <Plus size={16} />
          Add Company
        </button>
      </section>

      {/* Consolidate Button */}
      <div className="flex items-center gap-3">
        <button
          onClick={handleConsolidate}
          disabled={companies.filter((c) => c.name.trim() !== '').length < 2 || isLoading}
          className={cn(
            'btn-primary flex items-center gap-2',
            (companies.filter((c) => c.name.trim() !== '').length < 2 || isLoading) &&
              'opacity-50 cursor-not-allowed',
          )}
        >
          {isLoading ? <Spinner size={16} className="!p-0" /> : <Merge size={16} />}
          {isLoading ? 'Consolidating…' : 'Consolidate'}
        </button>
        {companies.filter((c) => c.name.trim() !== '').length < 2 && (
          <p className="text-xs text-cascade-sage flex items-center gap-1">
            <AlertTriangle size={14} className="text-semantic-warning" />
            At least 2 named companies are required
          </p>
        )}
      </div>

      {/* Loading State */}
      {isLoading && (
        <div className="card flex flex-col items-center justify-center py-16 gap-3">
          <Spinner size={32} />
          <p className="text-sm text-cascade-sage">Processing consolidation entries…</p>
        </div>
      )}

      {/* Results Section */}
      {result && !isLoading && (
        <div className="space-y-6 animate-slide-up">
          {/* ── Stats Cards ──────────────────────────────────────────────── */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
            <div className="card !p-4">
              <div className="flex items-center gap-2 mb-2">
                <div className="p-1.5 rounded-lg bg-cascade-gold/10">
                  <Building2 size={14} className="text-cascade-gold" />
                </div>
                <span className="text-xs text-cascade-sage font-medium">Total Companies</span>
              </div>
              <p className="text-2xl font-bold tracking-tight">{result.company_count}</p>
            </div>

            <div className="card !p-4">
              <div className="flex items-center gap-2 mb-2">
                <div className="p-1.5 rounded-lg bg-semantic-success/10">
                  <TrendingUp size={14} className="text-semantic-success" />
                </div>
                <span className="text-xs text-cascade-sage font-medium">Consolidated Revenue</span>
              </div>
              <p className="text-2xl font-bold tracking-tight text-semantic-success">
                {formatCurrency(consolidatedRevenue)}
              </p>
            </div>

            <div className="card !p-4">
              <div className="flex items-center gap-2 mb-2">
                <div className="p-1.5 rounded-lg bg-cascade-olive/10">
                  <TrendingUp size={14} className="text-cascade-olive" />
                </div>
                <span className="text-xs text-cascade-sage font-medium">Consolidated Net Income</span>
              </div>
              <p className="text-2xl font-bold tracking-tight">
                {formatCurrency(consolidatedNetIncome)}
              </p>
            </div>

            <div className="card !p-4">
              <div className="flex items-center gap-2 mb-2">
                <div className="p-1.5 rounded-lg bg-semantic-warning/10">
                  <PieChart size={14} className="text-semantic-warning" />
                </div>
                <span className="text-xs text-cascade-sage font-medium">Minority Interest</span>
              </div>
              <p className="text-2xl font-bold tracking-tight text-semantic-warning">
                {formatCurrency(minorityInterest)}
              </p>
            </div>
          </div>

          {/* ── Revenue Contribution Breakdown ───────────────────────────── */}
          {result.contributions.length > 0 && (
            <div className="card">
              <div className="flex items-center gap-2 mb-5">
                <PieChart size={16} className="text-cascade-gold" />
                <h3 className="text-sm font-semibold">Revenue Contribution Breakdown</h3>
              </div>

              <div className="space-y-3">
                {result.contributions.map((contrib, idx) => {
                  const widthPct = Math.max(2, contrib.revenue_contribution * 100);
                  return (
                    <div key={contrib.company_name}>
                      <div className="flex items-center justify-between mb-1">
                        <div className="flex items-center gap-2 min-w-0">
                          <span
                            className="w-2.5 h-2.5 rounded-full shrink-0"
                            style={{
                              backgroundColor:
                                idx === 0
                                  ? 'var(--color-cascade-gold, #b8860b)'
                                  : idx === 1
                                    ? 'var(--color-cascade-olive, #6b7c3f)'
                                    : idx === 2
                                      ? 'var(--color-cascade-sage, #7a8b6f)'
                                      : idx === 3
                                        ? '#4a4a4a'
                                        : idx === 4
                                          ? 'var(--color-semantic-success, #22c55e)'
                                          : 'var(--color-semantic-warning, #f59e0b)',
                            }}
                          />\n                          <span className="text-sm font-medium truncate">
                            {contrib.company_name}
                          </span>
                          <span className="text-xs text-cascade-sage">
                            ({contrib.ownership_pct}% owned)
                          </span>
                        </div>
                        <div className="flex items-center gap-3 shrink-0">
                          <span className="text-sm text-cascade-sage">
                            {formatCurrency(contrib.revenue)}
                          </span>
                          <span className="text-sm font-semibold w-14 text-right">
                            {(contrib.revenue_contribution * 100).toFixed(1)}%
                          </span>
                        </div>
                      </div>
                      <div className="h-3 bg-cascade-mist/60 rounded-full overflow-hidden">
                        <div
                          className={cn(
                            'h-full rounded-full transition-all duration-700 ease-out',
                            BAR_COLORS[idx % BAR_COLORS.length],
                          )}
                          style={{ width: `${widthPct}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* ── Elimination Entries ───────────────────────────────────────── */}
          {Object.keys(result.eliminations).length > 0 && (
            <div className="card">
              <div className="flex items-center gap-2 mb-4">
                <AlertTriangle size={16} className="text-semantic-warning" />
                <h3 className="text-sm font-semibold">Elimination Entries</h3>
                <span className="text-xs text-cascade-sage bg-semantic-warning/10 px-2 py-0.5 rounded-full">
                  {Object.keys(result.eliminations).length} entries
                </span>
              </div>

              <div className="divide-y divide-cascade-mist">
                {Object.entries(result.eliminations).map(([key, value]) => (
                  <div
                    key={key}
                    className="flex items-center justify-between py-2.5 first:pt-0 last:pb-0"
                  >
                    <span className="text-sm text-cascade-charcoal">{getFinancialLabel(key)}</span>
                    <span
                      className={cn(
                        'text-sm font-semibold font-mono',
                        value < 0 ? 'text-semantic-danger' : 'text-semantic-success',
                      )}
                    >
                      {value < 0 ? '(' : ''}
                      {formatCurrency(Math.abs(value))}
                      {value < 0 ? ')' : ''}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* ── Consolidated Financials Table ─────────────────────────────── */}
          <div className="card">
            <div className="flex items-center gap-2 mb-4">
              <Merge size={16} className="text-cascade-gold" />
              <h3 className="text-sm font-semibold">Consolidated Financials</h3>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-x-8 gap-y-1">
              {Object.entries(result.consolidated_financials).map(([key, value]) => (
                <div
                  key={key}
                  className="flex items-center justify-between py-2.5 border-b border-cascade-mist/60"
                >
                  <span className="text-sm text-cascade-sage">{getFinancialLabel(key)}</span>
                  <span className="text-sm font-semibold font-mono">
                    {formatCurrency(value)}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* ── Consolidated Ratios ───────────────────────────────────────── */}
          {result.ratios.length > 0 && (
            <div className="space-y-5">
              <div className="flex items-center gap-2">
                <TrendingUp size={16} className="text-cascade-gold" />
                <h3 className="text-sm font-semibold">Consolidated Ratios</h3>
              </div>

              {ratioCategories.map((category) => {
                const categoryRatios = result.ratios.filter((r) => r.category === category);
                return (
                  <div key={category}>
                    <h4 className="text-xs font-semibold text-cascade-sage uppercase tracking-wider mb-3">
                      {category}
                    </h4>
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                      {categoryRatios.map((ratio, idx) => (
                        <ConsolidationRatioCard key={`${category}-${idx}`} ratio={ratio} />
                      ))}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ── Consolidation Ratio Card ─────────────────────────────────────────────────

function ConsolidationRatioCard({ ratio }: { ratio: RatioResult }) {
  const StatusIcon =
    ratio.status === 'good' ? TrendingUp : ratio.status === 'warning' ? Minus : AlertTriangle;

  const displayValue =
    ratio.unit === '%' ? formatPercent(ratio.value) : formatRatio(ratio.value);

  return (
    <div className="card hover:shadow-elevated transition-shadow">
      <div className="flex items-start justify-between mb-3">
        <span className="text-xs font-semibold text-cascade-sage uppercase tracking-wider">
          {ratio.ratioName.replace(/_/g, ' ')}
        </span>
        <div className={cn('p-1.5 rounded-lg', getStatusBg(ratio.status))}>
          <StatusIcon size={14} className={cn(getStatusColor(ratio.status))} />
        </div>
      </div>
      <div className="flex items-end gap-2">
        <span className={cn('text-2xl font-bold tracking-tight', getStatusColor(ratio.status))}>
          {displayValue}
        </span>
        {ratio.unit && ratio.unit !== '%' && (
          <span className="text-sm text-cascade-sage mb-0.5">{ratio.unit}</span>
        )}
      </div>
      {ratio.benchmark !== null && (
        <div className="mt-3 pt-3 border-t border-cascade-mist">
          <div className="flex justify-between text-xs">
            <span className="text-cascade-sage">Industry Benchmark</span>
            <span className="font-medium">
              {ratio.unit === '%' ? formatPercent(ratio.benchmark) : formatRatio(ratio.benchmark)}
            </span>
          </div>
        </div>
      )}
    </div>
  );
}
