import { useLicense } from '../hooks/useLicense';
import { Bell, Crown } from 'lucide-react';

export default function Header() {
  const { license, isPro } = useLicense();

  return (
    <header className="h-14 bg-cascade-soft-white border-b border-cascade-mist flex items-center justify-between px-6 drag-region">
      <div className="no-drag" />
      <div className="flex items-center gap-4 no-drag">
        {/* License badge */}
        <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-semibold ${
          isPro
            ? 'bg-cascade-gold/10 text-cascade-gold'
            : 'bg-cascade-mist text-cascade-sage'
        }`}>
          <Crown size={14} />
          {isPro ? license?.tier?.toUpperCase() || 'PRO' : 'FREE TIER'}
        </div>

        {/* Notifications placeholder */}
        <button className="p-2 rounded-lg text-cascade-sage hover:text-cascade-charcoal hover:bg-cascade-mist/50 transition-colors relative">
          <Bell size={18} />
        </button>

        {/* Version */}
        <span className="text-xs text-cascade-sage">v0.1.0</span>
      </div>
    </header>
  );
}