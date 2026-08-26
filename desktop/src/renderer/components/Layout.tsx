import { useState, useEffect } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import {
  LayoutDashboard, BarChart3, FileText, History, Settings,
  ChevronLeft, ChevronRight, Menu, Sparkles, Activity,
  FileSearch, ShieldCheck, Merge, Globe, TrendingUp, Calculator, Target,
  BrainCircuit, Network, GitBranch, MessageSquareHeart, Layers, Scale,
  Waves, Brain, ArrowRightLeft, Sliders, Atom,
} from 'lucide-react';
import { useAnalysisStore } from '../hooks/useAnalysisStore';
import Header from './Header';
import Titlebar from './Titlebar';
import { getAnalysisHistory } from '../lib/api';

const navItems = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/analysis', icon: BarChart3, label: 'New Analysis' },
  { to: '/ai-copilot', icon: Sparkles, label: 'AI Copilot' },
  { to: '/prediction', icon: Activity, label: 'Prediction' },
  { to: '/document-intelligence', icon: FileSearch, label: 'Doc Intelligence' },
  { to: '/benchmarking', icon: BarChart3, label: 'Benchmarking' },
  { to: '/compliance', icon: ShieldCheck, label: 'Compliance' },
  { to: '/consolidation', icon: Merge, label: 'Consolidation' },
  { to: '/tsetmc', icon: Globe, label: 'TSETMC Live' },
  { to: '/time-series', icon: TrendingUp, label: 'Time Series' },
  { to: '/financial-engineering', icon: Calculator, label: 'Fin. Engineering' },
  { to: '/backtest', icon: Target, label: 'Backtesting' },
  { to: '/fuzzy-mcdm', icon: BrainCircuit, label: 'Fuzzy MCDM' },
  { to: '/factor-analysis', icon: Layers, label: 'Factor Analysis' },
  { to: '/black-litterman', icon: Scale, label: 'Black-Litterman' },
  { to: '/sentiment', icon: MessageSquareHeart, label: 'Sentiment' },
  { to: '/stochastic-calculus', icon: Waves, label: 'Stochastic' },
  { to: '/network-analysis', icon: Network, label: 'Network' },
  { to: '/causal-inference', icon: ArrowRightLeft, label: 'Causal' },
  { to: '/reinforcement-learning', icon: Brain, label: 'RL Engine' },
  { to: '/fuzzy-neural', icon: Atom, label: 'Fuzzy Neural' },
  { to: '/advanced-optimization', icon: Sliders, label: 'Adv. Optim.' },
  { to: '/reports', icon: FileText, label: 'Reports' },
  { to: '/history', icon: History, label: 'History' },
  { to: '/settings', icon: Settings, label: 'Settings' },
];

export default function Layout({ children }: { children: React.ReactNode }) {
  const { sidebarOpen, toggleSidebar, setAnalyses } = useAnalysisStore();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const location = useLocation();

  // Load analysis history on mount
  useEffect(() => {
    getAnalysisHistory().then((res) => {
      if (res.data) setAnalyses(res.data);
    }).catch(() => {
      // API not available - that's ok
    });
  }, [setAnalyses]);

  // Load demo data if no analyses
  useEffect(() => {
    const { analyses } = useAnalysisStore.getState();
    if (analyses.length === 0) {
      loadDemoData();
    }
  }, []);

  return (
    <div className="flex h-screen overflow-hidden flex-col">
      <Titlebar />
      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar */}
        <aside
          className={`
            ${sidebarOpen ? 'w-56' : 'w-14'}
            bg-cascade-charcoal text-white
            flex flex-col transition-all duration-300
            shrink-0 hidden md:flex
          `}
        >
          {/* Logo */}
          <div className="h-12 flex items-center px-3 gap-2.5">
            <div className="w-7 h-7 bg-cascade-gold rounded-md flex items-center justify-center text-white font-bold text-xs shrink-0">
              F
            </div>
            {sidebarOpen && (
              <span className="font-bold text-sm tracking-tight whitespace-nowrap">
                FinSight <span className="text-cascade-gold">Pro</span>
              </span>
            )}
          </div>

          {/* Navigation */}
          <nav className="flex-1 px-2 py-3 space-y-0.5">
            {navItems.map(({ to, icon: Icon, label }) => (
              <NavLink
                key={to}
                to={to}
                className={() => {
                  const isActive = to === '/' ? location.pathname === '/' : location.pathname.startsWith(to);
                  return `
                    flex items-center gap-2.5 px-2.5 py-2 rounded-lg text-[13px] font-medium
                    transition-colors duration-150
                    ${isActive
                      ? 'text-cascade-gold bg-cascade-gold/10'
                      : 'text-white/40 hover:text-white hover:bg-white/5'
                    }
                    ${!sidebarOpen ? 'justify-center' : ''}
                  `;
                }}
                title={!sidebarOpen ? label : undefined}
              >
                <Icon size={18} />
                {sidebarOpen && <span className="whitespace-nowrap">{label}</span>}
              </NavLink>
            ))}
          </nav>

          {/* Collapse toggle */}
          <div className="px-2 pb-3">
            <button
              onClick={toggleSidebar}
              className="w-full p-2 rounded-lg text-white/30 hover:text-white hover:bg-white/5 transition-colors"
            >
              {sidebarOpen ? <ChevronLeft size={16} /> : <ChevronRight size={16} />}
            </button>
          </div>
        </aside>

        {/* Mobile menu button */}
        <button
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          className="md:hidden fixed top-10 left-3 z-50 p-2 rounded-lg bg-cascade-charcoal text-white"
        >
          <Menu size={18} />
        </button>

        {/* Mobile overlay */}
        {mobileMenuOpen && (
          <div
            className="md:hidden fixed inset-0 bg-black/50 z-40"
            onClick={() => setMobileMenuOpen(false)}
          />
        )}

        {/* Mobile sidebar */}
        <aside
          className={`
            md:hidden fixed left-0 top-9 bottom-0 w-56 bg-cascade-charcoal text-white
            flex flex-col z-40 transition-transform duration-300
            ${mobileMenuOpen ? 'translate-x-0' : '-translate-x-full'}
          `}
        >
          <div className="h-12 flex items-center px-3 gap-2.5">
            <div className="w-7 h-7 bg-cascade-gold rounded-md flex items-center justify-center text-white font-bold text-xs">F</div>
            <span className="font-bold text-sm tracking-tight">FinSight <span className="text-cascade-gold">Pro</span></span>
          </div>
          <nav className="flex-1 px-2 py-3 space-y-0.5">
            {navItems.map(({ to, icon: Icon, label }) => (
              <NavLink
                key={to}
                to={to}
                onClick={() => setMobileMenuOpen(false)}
                className={() => {
                  const isActive = to === '/' ? location.pathname === '/' : location.pathname.startsWith(to);
                  return `flex items-center gap-2.5 px-2.5 py-2 rounded-lg text-[13px] font-medium transition-colors duration-150 ${
                    isActive ? 'text-cascade-gold bg-cascade-gold/10' : 'text-white/40 hover:text-white hover:bg-white/5'
                  }`;
                }}
              >
                <Icon size={18} />
                <span>{label}</span>
              </NavLink>
            ))}
          </nav>
        </aside>

        {/* Main content */}
        <main className="flex-1 flex flex-col overflow-hidden">
          <Header />
          <div className="flex-1 overflow-y-auto p-6 scrollbar-thin bg-cascade-stone">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}

function loadDemoData() {
  const { setAnalyses, setCurrentAnalysis } = useAnalysisStore.getState();

  const demoAnalyses: import('../../types').AnalysisHistoryItem[] = [
    {
      analysisId: 'demo-001',
      companyName: 'Acme Corporation',
      period: 'FY 2024',
      fileName: 'acme_income_2024.xlsx',
      createdAt: '2024-12-15T10:30:00Z',
      summary: { profitability: 78, liquidity: 85, leverage: 62, efficiency: 71 },
    },
    {
      analysisId: 'demo-002',
      companyName: 'GlobalTech Industries',
      period: 'Q3 2024',
      fileName: 'globaltech_q3_2024.csv',
      createdAt: '2024-11-28T14:20:00Z',
      summary: { profitability: 65, liquidity: 72, leverage: 45, efficiency: 88 },
    },
    {
      analysisId: 'demo-003',
      companyName: 'Pinnacle Holdings',
      period: 'FY 2023',
      fileName: 'pinnacle_annual_2023.xlsx',
      createdAt: '2024-10-05T09:15:00Z',
      summary: { profitability: 42, liquidity: 58, leverage: 80, efficiency: 55 },
    },
  ];

  const demoAnalysis: import('../../types').AnalysisResult = {
    analysisId: 'demo-001',
    companyName: 'Acme Corporation',
    period: 'FY 2024',
    fileName: 'acme_income_2024.xlsx',
    createdAt: '2024-12-15T10:30:00Z',
    ratios: [
      { category: 'profitability', ratioName: 'Gross Profit Margin', value: 0.42, unit: '%', benchmark: 0.38, status: 'good' },
      { category: 'profitability', ratioName: 'Net Profit Margin', value: 0.18, unit: '%', benchmark: 0.12, status: 'good' },
      { category: 'profitability', ratioName: 'Return on Assets', value: 0.14, unit: '%', benchmark: 0.10, status: 'good' },
      { category: 'profitability', ratioName: 'Return on Equity', value: 0.22, unit: '%', benchmark: 0.18, status: 'good' },
      { category: 'liquidity', ratioName: 'Current Ratio', value: 2.4, unit: 'x', benchmark: 2.0, status: 'good' },
      { category: 'liquidity', ratioName: 'Quick Ratio', value: 1.8, unit: 'x', benchmark: 1.5, status: 'good' },
      { category: 'liquidity', ratioName: 'Cash Ratio', value: 0.6, unit: 'x', benchmark: 0.5, status: 'good' },
      { category: 'leverage', ratioName: 'Debt to Equity', value: 1.8, unit: 'x', benchmark: 1.5, status: 'warning' },
      { category: 'leverage', ratioName: 'Debt to Assets', value: 0.65, unit: '%', benchmark: 0.50, status: 'critical' },
      { category: 'leverage', ratioName: 'Interest Coverage', value: 4.2, unit: 'x', benchmark: 3.0, status: 'good' },
      { category: 'efficiency', ratioName: 'Asset Turnover', value: 0.85, unit: 'x', benchmark: 0.80, status: 'good' },
      { category: 'efficiency', ratioName: 'Inventory Turnover', value: 6.3, unit: 'x', benchmark: 5.5, status: 'good' },
    ],
  };

  setAnalyses(demoAnalyses);
  setCurrentAnalysis(demoAnalysis);
}
