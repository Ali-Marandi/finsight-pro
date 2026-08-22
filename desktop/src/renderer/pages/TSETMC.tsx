import { useState, useEffect, useCallback } from 'react';
import {
  TrendingUp,
  TrendingDown,
  Search,
  Globe,
  RefreshCw,
  BarChart3,
  DollarSign,
  Activity,
  Eye,
  Minus,
} from 'lucide-react';
import { searchTSETMC, getTSETMCStock, getTSETMCOverview, getTSETMCPopular } from '../lib/api';
import type { TSETMCOverview, TSETMCStockData } from '../../types';
import { useToast } from '../components/Toast';
import Spinner from '../components/Spinner';

// ---------------------------------------------------------------------------
// Demo fallback data
// ---------------------------------------------------------------------------

const DEMO_POPULAR_STOCKS = [
  { symbol: '\u062E\u067E\u0627\u0631\u0633', name_en: 'Pars Petrochemical', sector: 'Petrochemical' },
  { symbol: '\u0641\u0648\u0644\u0627\u062F', name_en: 'Mobarakeh Steel', sector: 'Metals' },
  { symbol: '\u062E\u0648\u062F\u0631\u0648', name_en: 'Iran Khodro', sector: 'Automotive' },
  { symbol: '\u0648\u0628\u0645\u0644\u062A', name_en: 'Bank Melli', sector: 'Banking' },
  { symbol: '\u062E\u0633\u0627\u067E\u0627', name_en: 'Saipa', sector: 'Automotive' },
  { symbol: '\u0648\u062A\u062C\u0627\u0631\u062A', name_en: 'Bank Tejarat', sector: 'Banking' },
  { symbol: '\u0641\u062E\u0648\u0632', name_en: 'Khuzestan Steel', sector: 'Metals' },
  { symbol: '\u06A9\u0627\u0644\u0647', name_en: 'Kalleh Dairy', sector: 'Food' },
  { symbol: '\u0641\u0646\u0627\u0648\u0631\u06CC', name_en: 'Fanaavari', sector: 'Technology' },
  { symbol: '\u06AF\u0644\u067E\u0627', name_en: 'Golpayegan', sector: 'Food' },
  { symbol: '\u0648\u0628\u0635\u0627\u062F\u0631', name_en: 'Bank Saderat', sector: 'Banking' },
  { symbol: '\u0641\u067E\u0627\u0631\u0633\u0627', name_en: 'Parsian Oil', sector: 'Oil & Gas' },
];

const DEMO_INDICES = [
  { name: '\u0634\u062E\u0635 \u06A9\u0644 (TEDPIX)', value: 2_145_320, change: 1.24 },
  { name: '\u0634\u062E\u0635 \u0627\u0648\u0644 (TEFIX)', value: 892_410, change: -0.37 },
  { name: '\u0634\u062E\u0635 \u0635\u0646\u0639\u062A\u06CC', value: 456_780, change: 0.82 },
  { name: '\u0634\u062E\u0635 \u0641\u0631\u0648\u0634\u06AF\u0627\u0647\u06CC', value: 1_032_645, change: 0.15 },
];

function generateDemoStockData(symbol: string, nameEn: string, sector: string): TSETMCStockData {
  const last = Math.round(1000 + Math.random() * 49000);
  const changePct = parseFloat((Math.random() * 10 - 5).toFixed(2));
  const changeValue = Math.round(last * (changePct / 100));
  const high = Math.round(last * 1.03);
  const low = Math.round(last * 0.97);
  const open = Math.round(low + Math.random() * (high - low));
  const close = last;
  const volume = Math.round(1_000_000 + Math.random() * 49_000_000);
  const shares = Math.round(1_000_000_000 + Math.random() * 19_000_000_000);
  const marketCap = last * shares;
  const value = Math.round(volume * last);
  const eps = Math.round(100 + Math.random() * 2900);
  const pe = parseFloat((last / eps).toFixed(2));
  const status = changePct > 0.01 ? 'positive' : changePct < -0.01 ? 'negative' : 'unchanged';

  return {
    instrument_id: `demo-${symbol}`,
    available: true,
    data: {
      name: symbol,
      last_price: last,
      closing_price: close,
      open_price: open,
      high_price: high,
      low_price: low,
      volume,
      value,
      market_cap: marketCap,
      yesterday_price: last - changeValue,
      shares_outstanding: shares,
      eps,
      pe_ratio: pe,
      sector,
      change_pct: changePct,
      change_value: changeValue,
      status,
    },
    error: null,
  };
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function formatRial(n: number | undefined | null): string {
  if (n == null) return '—';
  return `${n.toLocaleString('en-US')} IRR`;
}

function formatNumber(n: number | undefined | null): string {
  if (n == null) return '—';
  return n.toLocaleString('en-US');
}

function formatPercent(n: number | undefined | null): string {
  if (n == null) return '—';
  const sign = n >= 0 ? '+' : '';
  return `${sign}${n.toFixed(2)}%`;
}

function formatCompact(n: number | undefined | null): string {
  if (n == null) return '—';
  if (n >= 1_000_000_000_000) return `${(n / 1_000_000_000_000).toFixed(1)}T`;
  if (n >= 1_000_000_000) return `${(n / 1_000_000_000).toFixed(1)}B`;
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
  return n.toLocaleString('en-US');
}

function sectorColor(sector: string): string {
  const map: Record<string, string> = {
    Petrochemical: 'bg-amber-100 text-amber-700',
    Metals: 'bg-slate-100 text-slate-700',
    Automotive: 'bg-blue-100 text-blue-700',
    Banking: 'bg-emerald-100 text-emerald-700',
    Food: 'bg-orange-100 text-orange-700',
    Technology: 'bg-violet-100 text-violet-700',
    'Oil & Gas': 'bg-red-100 text-red-700',
  };
  return map[sector] || 'bg-cascade-mist/50 text-cascade-sage';
}

// ---------------------------------------------------------------------------
// Types for internal state
// ---------------------------------------------------------------------------

interface PopularStock {
  symbol: string;
  name_en: string;
  sector: string;
}

interface SearchResult {
  symbol: string;
  instrument_id: string;
  source: string;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export default function TSETMC() {
  const { toast } = useToast();

  // Search state
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [searchOpen, setSearchOpen] = useState(false);
  const [searchLoading, setSearchLoading] = useState(false);

  // Popular stocks
  const [popularStocks, setPopularStocks] = useState<PopularStock[]>(DEMO_POPULAR_STOCKS);
  const [popularLoading, setPopularLoading] = useState(false);

  // Market overview
  const [overview, setOverview] = useState<TSETMCOverview | null>(null);
  const [overviewLoading, setOverviewLoading] = useState(false);

  // Selected stock
  const [selectedStock, setSelectedStock] = useState<TSETMCStockData | null>(null);
  const [stockLoading, setStockLoading] = useState(false);

  // Refresh
  const [refreshing, setRefreshing] = useState(false);

  // -----------------------------------------------------------------------
  // Load market overview on mount
  // -----------------------------------------------------------------------
  const loadOverview = useCallback(async () => {
    setOverviewLoading(true);
    try {
      const res = await getTSETMCOverview();
      if (res && res.indices && res.indices.length > 0) {
        setOverview(res);
      } else {
        // Fallback demo data
        setOverview({
          indices: DEMO_INDICES,
          popular_stocks: DEMO_POPULAR_STOCKS,
          status: 'demo',
          error: null,
        });
      }
    } catch {
      setOverview({
        indices: DEMO_INDICES,
        popular_stocks: DEMO_POPULAR_STOCKS,
        status: 'demo',
        error: null,
      });
    } finally {
      setOverviewLoading(false);
    }
  }, []);

  // -----------------------------------------------------------------------
  // Load popular stocks
  // -----------------------------------------------------------------------
  const loadPopularStocks = useCallback(async () => {
    setPopularLoading(true);
    try {
      const res = await getTSETMCPopular();
      if (res && res.stocks && res.stocks.length > 0) {
        setPopularStocks(res.stocks);
      }
      // If empty or error, keep demo data already in state
    } catch {
      // Keep demo data
    } finally {
      setPopularLoading(false);
    }
  }, []);

  useEffect(() => {
    loadOverview();
    loadPopularStocks();
  }, [loadOverview, loadPopularStocks]);

  // -----------------------------------------------------------------------
  // Search
  // -----------------------------------------------------------------------
  const handleSearch = useCallback(async () => {
    const q = searchQuery.trim();
    if (!q) return;
    setSearchLoading(true);
    setSearchOpen(true);
    try {
      const res = await searchTSETMC(q);
      if (res && res.results && res.results.length > 0) {
        setSearchResults(res.results);
      } else {
        setSearchResults([]);
        toast('info', 'No results found for your search');
      }
    } catch {
      toast('warning', 'Search service unavailable — try a popular stock below');
      setSearchResults([]);
    } finally {
      setSearchLoading(false);
    }
  }, [searchQuery, toast]);

  const handleSearchKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === 'Enter') handleSearch();
      if (e.key === 'Escape') setSearchOpen(false);
    },
    [handleSearch],
  );

  // -----------------------------------------------------------------------
  // Select / load a stock
  // -----------------------------------------------------------------------
  const loadStock = useCallback(
    async (instrumentId: string, fallbackSymbol?: string, fallbackName?: string, fallbackSector?: string) => {
      setStockLoading(true);
      setSelectedStock(null);
      setSearchOpen(false);
      try {
        const res = await getTSETMCStock(instrumentId);
        if (res && res.available && res.data) {
          setSelectedStock(res);
        } else {
          // Fallback to demo data
          const demo = generateDemoStockData(
            fallbackSymbol || 'Unknown',
            fallbackName || 'Unknown',
            fallbackSector || 'General',
          );
          demo.instrument_id = instrumentId;
          setSelectedStock(demo);
          toast('info', 'Live data unavailable — showing simulated data');
        }
      } catch {
        const demo = generateDemoStockData(
          fallbackSymbol || 'Unknown',
          fallbackName || 'Unknown',
          fallbackSector || 'General',
        );
        demo.instrument_id = instrumentId;
        setSelectedStock(demo);
        toast('info', 'Live data unavailable — showing simulated data');
      } finally {
        setStockLoading(false);
      }
    },
    [toast],
  );

  const handleSelectSearchResult = useCallback(
    (r: SearchResult) => {
      setSearchQuery(r.symbol);
      setSearchOpen(false);
      loadStock(r.instrument_id, r.symbol);
    },
    [loadStock],
  );

  const handlePopularClick = useCallback(
    (stock: PopularStock) => {
      // Use the symbol as a mock instrument_id for demo purposes
      const instrumentId = stock.symbol;
      loadStock(instrumentId, stock.symbol, stock.name_en, stock.sector);
    },
    [loadStock],
  );

  // -----------------------------------------------------------------------
  // Refresh all
  // -----------------------------------------------------------------------
  const handleRefresh = useCallback(async () => {
    setRefreshing(true);
    try {
      await Promise.all([loadOverview(), loadPopularStocks()]);
      if (selectedStock) {
        await loadStock(selectedStock.instrument_id);
      }
      toast('success', 'Market data refreshed');
    } catch {
      toast('error', 'Failed to refresh market data');
    } finally {
      setRefreshing(false);
    }
  }, [loadOverview, loadPopularStocks, loadStock, selectedStock, toast]);

  // -----------------------------------------------------------------------
  // Derived values
  // -----------------------------------------------------------------------
  const stockData = selectedStock?.data ?? null;
  const isPositive = (stockData?.change_pct ?? 0) > 0.01;
  const isNegative = (stockData?.change_pct ?? 0) < -0.01;
  const isUnchanged = !isPositive && !isNegative;

  const changeColor = isPositive
    ? 'text-semantic-success'
    : isNegative
      ? 'text-semantic-danger'
      : 'text-cascade-sage';

  const statusBg = isPositive
    ? 'bg-semantic-success/10 text-semantic-success'
    : isNegative
      ? 'bg-semantic-danger/10 text-semantic-danger'
      : 'bg-cascade-mist/50 text-cascade-sage';

  const statusLabel = isPositive ? 'Positive' : isNegative ? 'Negative' : 'Unchanged';
  const StatusIcon = isPositive ? TrendingUp : isNegative ? TrendingDown : Minus;

  const indices = overview?.indices ?? (overviewLoading ? [] : DEMO_INDICES);

  // -----------------------------------------------------------------------
  // Render
  // -----------------------------------------------------------------------
  return (
    <div className="space-y-8">
      {/* ---- Header ---- */}
      <div className="page-header">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-cascade-gold/10 flex items-center justify-center shrink-0">
            <Globe size={20} className="text-cascade-gold" />
          </div>
          <div>
            <h1 className="page-title">TSETMC Live Market</h1>
            <p className="text-cascade-sage text-sm mt-1">Tehran Stock Exchange real-time data</p>
          </div>
        </div>
        <button
          onClick={handleRefresh}
          disabled={refreshing}
          className="btn-secondary flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <RefreshCw size={14} className={refreshing ? 'animate-spin' : ''} />
          <span className="hidden sm:inline">Refresh</span>
        </button>
      </div>

      {/* ---- Search Bar ---- */}
      <div className="relative">
        <div className="flex gap-2">
          <div className="relative flex-1">
            <Search
              size={18}
              className="absolute left-3.5 top-1/2 -translate-y-1/2 text-cascade-sage pointer-events-none"
            />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onFocus={() => {
                if (searchResults.length > 0) setSearchOpen(true);
              }}
              onKeyDown={handleSearchKeyDown}
              placeholder="Search stock by symbol or name (Persian / English)..."
              className="input-field pl-11 pr-4 py-3 text-base"
            />
          </div>
          <button
            onClick={handleSearch}
            disabled={searchLoading || !searchQuery.trim()}
            className="btn-primary px-6 flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {searchLoading ? <Spinner size={14} /> : <Search size={14} />}
            <span>Search</span>
          </button>
        </div>

        {/* Search results dropdown */}
        {searchOpen && searchResults.length > 0 && (
          <div className="absolute z-50 mt-1 w-full card p-2 max-h-80 overflow-y-auto scrollbar-thin shadow-elevated">
            {searchResults.map((r) => (
              <button
                key={`${r.instrument_id}-${r.symbol}`}
                onClick={() => handleSelectSearchResult(r)}
                className="w-full text-left px-3 py-2.5 rounded-lg hover:bg-cascade-mist/50 transition-colors flex items-center justify-between group"
              >
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-lg bg-cascade-gold/10 flex items-center justify-center shrink-0">
                    <Eye size={14} className="text-cascade-gold" />
                  </div>
                  <div>
                    <p className="font-medium text-sm group-hover:text-cascade-gold transition-colors">
                      {r.symbol}
                    </p>
                    <p className="text-xs text-cascade-sage">{r.source}</p>
                  </div>
                </div>
                <BarChart3 size={14} className="text-cascade-mist group-hover:text-cascade-gold transition-colors" />
              </button>
            ))}
          </div>
        )}
        {searchOpen && !searchLoading && searchResults.length === 0 && searchQuery.trim() && (
          <div className="absolute z-50 mt-1 w-full card p-4 text-center">
            <p className="text-sm text-cascade-sage">No stocks found for &ldquo;{searchQuery}&rdquo;</p>
          </div>
        )}
      </div>

      {/* ---- Close dropdown on outside click ---- */}
      {searchOpen && (
        <div
          className="fixed inset-0 z-40"
          onClick={() => setSearchOpen(false)}
          onKeyDown={(e) => e.key === 'Escape' && setSearchOpen(false)}
          role="button"
          tabIndex={-1}
          aria-label="Close search results"
        />
      )}

      {/* ---- Market Overview ---- */}
      <section>
        <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <Activity size={18} className="text-cascade-gold" />
          Market Indices
        </h2>

        {overviewLoading && !overview ? (
          <div className="card py-10">
            <Spinner size={28} />
            <p className="text-sm text-cascade-sage mt-3">Loading market overview...</p>
          </div>
        ) : (
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            {indices.map((idx, i) => {
              const pos = idx.change > 0;
              const neg = idx.change < 0;
              return (
                <div key={i} className="card p-4">
                  <p className="text-xs text-cascade-sage mb-2 truncate">{idx.name}</p>
                  <p className="text-lg font-bold">{formatNumber(idx.value)}</p>
                  <p
                    className={`text-sm font-semibold mt-1 flex items-center gap-1 ${
                      pos ? 'text-semantic-success' : neg ? 'text-semantic-danger' : 'text-cascade-sage'
                    }`}
                  >
                    {pos ? <TrendingUp size={14} /> : neg ? <TrendingDown size={14} /> : <Minus size={14} />}
                    {formatPercent(idx.change)}
                  </p>
                </div>
              );
            })}
          </div>
        )}
      </section>

      {/* ---- Popular Stocks Grid ---- */}
      <section>
        <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <BarChart3 size={18} className="text-cascade-gold" />
          Popular Stocks
        </h2>

        {popularLoading && !popularStocks.length ? (
          <div className="card py-10">
            <Spinner size={28} />
            <p className="text-sm text-cascade-sage mt-3">Loading popular stocks...</p>
          </div>
        ) : (
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            {popularStocks.map((stock) => (
              <button
                key={stock.symbol}
                onClick={() => handlePopularClick(stock)}
                disabled={stockLoading}
                className="card text-left p-4 hover:shadow-elevated hover:border-cascade-gold/30 transition-all cursor-pointer group disabled:opacity-60"
              >
                <div className="flex items-start justify-between mb-2">
                  <div>
                    <p className="font-bold text-base group-hover:text-cascade-gold transition-colors">
                      {stock.symbol}
                    </p>
                    <p className="text-xs text-cascade-sage mt-0.5">{stock.name_en}</p>
                  </div>
                  <Eye size={14} className="text-cascade-mist group-hover:text-cascade-gold transition-colors mt-1" />
                </div>
                <span className={`status-badge ${sectorColor(stock.sector)}`}>
                  {stock.sector}
                </span>
              </button>
            ))}
          </div>
        )}
      </section>

      {/* ---- Selected Stock Detail ---- */}
      {stockLoading && (
        <section>
          <div className="card py-12">
            <Spinner size={32} />
            <p className="text-sm text-cascade-sage mt-4">Loading stock data...</p>
          </div>
        </section>
      )}

      {selectedStock && !stockLoading && stockData && (
        <section className="animate-slide-up">
          <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <DollarSign size={18} className="text-cascade-gold" />
            Stock Detail
          </h2>

          <div className="card space-y-6">
            {/* Header row: name + price + change */}
            <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
              <div>
                <div className="flex items-center gap-3">
                  <h3 className="text-xl font-bold">{stockData.name}</h3>
                  <span className={`status-badge ${statusBg}`}>
                    <StatusIcon size={12} />
                    {statusLabel}
                  </span>
                </div>
                {stockData.sector && (
                  <span className={`status-badge ${sectorColor(stockData.sector)} mt-2`}>
                    {stockData.sector}
                  </span>
                )}
              </div>

              <div className="flex items-end gap-6">
                <div className="text-right">
                  <p className="text-xs text-cascade-sage mb-1">Last Price</p>
                  <p className="text-3xl font-bold">{formatRial(stockData.last_price)}</p>
                </div>
                <div className="text-right min-w-[110px]">
                  <p className={`text-2xl font-bold ${changeColor}`}>
                    {formatPercent(stockData.change_pct)}
                  </p>
                  <p className={`text-sm font-medium ${changeColor}`}>
                    {stockData.change_value != null && (
                      <>
                        {stockData.change_value >= 0 ? '+' : ''}
                        {formatNumber(stockData.change_value)} IRR
                      </>
                    )}
                  </p>
                </div>
              </div>
            </div>

            {/* Divider */}
            <div className="border-t border-cascade-mist" />

            {/* Info grid */}
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-x-6 gap-y-4">
              <InfoItem label="Open" value={formatRial(stockData.open_price)} />
              <InfoItem label="High" value={formatRial(stockData.high_price)} />
              <InfoItem label="Low" value={formatRial(stockData.low_price)} />
              <InfoItem label="Close" value={formatRial(stockData.closing_price)} />
              <InfoItem label="Volume" value={formatNumber(stockData.volume)} />
              <InfoItem label="Trade Value" value={formatRial(stockData.value)} />
              <InfoItem label="Market Cap" value={formatCompact(stockData.market_cap)} />
              <InfoItem label="EPS" value={formatNumber(stockData.eps)} />
              <InfoItem label="P/E Ratio" value={stockData.pe_ratio != null ? String(stockData.pe_ratio) : '—'} />
              <InfoItem label="Shares Outstanding" value={formatCompact(stockData.shares_outstanding)} />
              <InfoItem label="Sector" value={stockData.sector || '—'} />
              <InfoItem
                label="Yesterday"
                value={formatRial(stockData.yesterday_price)}
              />
            </div>
          </div>
        </section>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function InfoItem({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-xs text-cascade-sage mb-0.5">{label}</p>
      <p className="text-sm font-medium text-cascade-charcoal truncate" title={value}>
        {value}
      </p>
    </div>
  );
}