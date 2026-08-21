import { useState } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import {
  LayoutDashboard, BarChart3, FileText, History, Settings,
  ChevronLeft, ChevronRight, Menu,
} from 'lucide-react';
import { useAnalysisStore } from '../hooks/useAnalysisStore';
import Header from './Header';

const navItems = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/analysis', icon: BarChart3, label: 'New Analysis' },
  { to: '/reports', icon: FileText, label: 'Reports' },
  { to: '/history', icon: History, label: 'History' },
  { to: '/settings', icon: Settings, label: 'Settings' },
];

export default function Layout({ children }: { children: React.ReactNode }) {
  const { sidebarOpen, toggleSidebar } = useAnalysisStore();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const location = useLocation();

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Sidebar */}
      <aside
        className={`
          ${sidebarOpen ? 'w-60' : 'w-16'}
          bg-cascade-charcoal text-white
          flex flex-col transition-all duration-300
          shrink-0 hidden md:flex
        `}
      >
        {/* Logo */}
        <div className="h-16 flex items-center px-4 gap-3 drag-region">
          <div className="w-8 h-8 bg-cascade-gold rounded-lg flex items-center justify-center text-white font-bold text-sm no-drag">
            F
          </div>
          {sidebarOpen && (
            <span className="font-bold text-base tracking-tight no-drag">
              FinSight <span className="text-cascade-gold">Pro</span>
            </span>
          )}
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-2 py-4 space-y-1">
          {navItems.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              className={() => {
                const isActive = to === '/' ? location.pathname === '/' : location.pathname.startsWith(to);
                return `
                  flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium
                  transition-colors duration-150 no-drag
                  ${isActive
                    ? 'text-cascade-gold bg-cascade-gold/10'
                    : 'text-white/50 hover:text-white hover:bg-white/5'
                  }
                  ${!sidebarOpen ? 'justify-center' : ''}
                `;
              }}
              title={!sidebarOpen ? label : undefined}
            >
              <Icon size={20} />
              {sidebarOpen && <span>{label}</span>}
            </NavLink>
          ))}
        </nav>

        {/* Collapse toggle */}
        <button
          onClick={toggleSidebar}
          className="mx-2 mb-4 p-2 rounded-lg text-white/40 hover:text-white hover:bg-white/5 transition-colors no-drag"
        >
          {sidebarOpen ? <ChevronLeft size={18} /> : <ChevronRight size={18} />}
        </button>
      </aside>

      {/* Mobile menu button */}
      <button
        onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
        className="md:hidden fixed top-3 left-3 z-50 p-2 rounded-lg bg-cascade-charcoal text-white"
      >
        <Menu size={20} />
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
          md:hidden fixed left-0 top-0 bottom-0 w-60 bg-cascade-charcoal text-white
          flex flex-col z-40 transition-transform duration-300
          ${mobileMenuOpen ? 'translate-x-0' : '-translate-x-full'}
        `}
      >
        <div className="h-16 flex items-center px-4 gap-3">
          <div className="w-8 h-8 bg-cascade-gold rounded-lg flex items-center justify-center text-white font-bold text-sm">F</div>
          <span className="font-bold text-base tracking-tight">FinSight <span className="text-cascade-gold">Pro</span></span>
        </div>
        <nav className="flex-1 px-2 py-4 space-y-1">
          {navItems.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              onClick={() => setMobileMenuOpen(false)}
              className={() => {
                const isActive = to === '/' ? location.pathname === '/' : location.pathname.startsWith(to);
                return `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors duration-150 ${
                  isActive ? 'text-cascade-gold bg-cascade-gold/10' : 'text-white/50 hover:text-white hover:bg-white/5'
                }`;
              }}
            >
              <Icon size={20} />
              <span>{label}</span>
            </NavLink>
          ))}
        </nav>
      </aside>

      {/* Main content */}
      <main className="flex-1 flex flex-col overflow-hidden">
        <Header />
        <div className="flex-1 overflow-y-auto p-6 scrollbar-thin">
          {children}
        </div>
      </main>
    </div>
  );
}
