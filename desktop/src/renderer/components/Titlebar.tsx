import { useState, useEffect } from 'react';
import { Minus, Square, X, Copy } from 'lucide-react';

export default function Titlebar() {
  const [isMaximized, setIsMaximized] = useState(false);

  useEffect(() => {
    const checkMaximized = async () => {
      if (window.electronAPI) {
        const max = await window.electronAPI.windowIsMaximized();
        setIsMaximized(max);
      }
    };
    checkMaximized();

    // Poll for maximize state changes
    const interval = setInterval(checkMaximized, 500);
    return () => clearInterval(interval);
  }, []);

  const handleMinimize = () => window.electronAPI?.windowMinimize();
  const handleMaximize = () => {
    window.electronAPI?.windowMaximize();
    setIsMaximized(!isMaximized);
  };
  const handleClose = () => window.electronAPI?.windowClose();

  // Only show custom titlebar in Electron
  if (!window.electronAPI) return null;

  return (
    <div className="h-9 bg-cascade-charcoal flex items-center justify-between select-none shrink-0 drag-region">
      {/* Left: App title */}
      <div className="flex items-center gap-2 pl-3 no-drag">
        <div className="w-4 h-4 bg-cascade-gold rounded flex items-center justify-center">
          <span className="text-white font-bold text-[9px]">F</span>
        </div>
        <span className="text-white/70 text-xs font-medium">FinSight Pro</span>
      </div>

      {/* Center: Spacer for drag region */}
      <div className="flex-1" />

      {/* Right: Window controls */}
      <div className="flex items-center no-drag">
        <button
          onClick={handleMinimize}
          className="w-11 h-9 flex items-center justify-center text-white/60 hover:text-white hover:bg-white/10 transition-colors"
        >
          <Minus size={14} />
        </button>
        <button
          onClick={handleMaximize}
          className="w-11 h-9 flex items-center justify-center text-white/60 hover:text-white hover:bg-white/10 transition-colors"
        >
          {isMaximized ? <Copy size={12} /> : <Square size={12} />}
        </button>
        <button
          onClick={handleClose}
          className="w-11 h-9 flex items-center justify-center text-white/60 hover:text-white hover:bg-red-600 transition-colors rounded-tr"
        >
          <X size={14} />
        </button>
      </div>
    </div>
  );
}