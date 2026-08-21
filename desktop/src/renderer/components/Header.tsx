import { useState, useEffect } from 'react';
import { useLicense } from '../hooks/useLicense';
import { Bell, Crown, RefreshCw } from 'lucide-react';

export default function Header() {
  const { license, isPro } = useLicense();
  const [version, setVersion] = useState('0.1.0');

  useEffect(() => {
    if (window.electronAPI) {
      window.electronAPI.getAppVersion().then(setVersion);
    }
  }, []);

  return (
    <header className="h-12 bg-cascade-soft-white border-b border-cascade-mist flex items-center justify-between px-4 no-drag">
      <div />
      <div className="flex items-center gap-3">
        {/* License badge */}
        <div className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-semibold ${
          isPro
            ? 'bg-cascade-gold/10 text-cascade-gold'
            : 'bg-cascade-mist text-cascade-sage'
        }`}>
          <Crown size={12} />
          {isPro ? license?.tier?.toUpperCase() || 'PRO' : 'FREE TIER'}
        </div>

        {/* API Status indicator */}
        <ApiStatusIndicator />

        {/* Notifications placeholder */}
        <button className="p-1.5 rounded-lg text-cascade-sage hover:text-cascade-charcoal hover:bg-cascade-mist/50 transition-colors relative">
          <Bell size={16} />
        </button>

        {/* Version */}
        <span className="text-[11px] text-cascade-sage/60">v{version}</span>
      </div>
    </header>
  );
}

function ApiStatusIndicator() {
  const [status, setStatus] = useState<'checking' | 'online' | 'offline'>('checking');

  useEffect(() => {
    const check = async () => {
      try {
        const apiUrl = window.electronAPI
          ? await window.electronAPI.getApiUrl()
          : 'http://127.0.0.1:8000/api/v1';
        const res = await fetch(`${apiUrl.replace('/api/v1', '')}/health`, {
          signal: AbortSignal.timeout(3000),
        });
        setStatus(res.ok ? 'online' : 'offline');
      } catch {
        setStatus('offline');
      }
    };
    check();
    const interval = setInterval(check, 15000);
    return () => clearInterval(interval);
  }, []);

  if (status === 'checking') {
    return (
      <div className="flex items-center gap-1.5 text-[11px] text-cascade-sage">
        <RefreshCw size={12} className="animate-spin" />
        <span className="hidden sm:inline">Connecting...</span>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-1.5 text-[11px]">
      <span className={`w-2 h-2 rounded-full ${status === 'online' ? 'bg-semantic-success' : 'bg-semantic-danger'} animate-pulse`} />
      <span className={`hidden sm:inline ${status === 'online' ? 'text-semantic-success' : 'text-semantic-danger'}`}>
        {status === 'online' ? 'API Ready' : 'Offline Mode'}
      </span>
    </div>
  );
}