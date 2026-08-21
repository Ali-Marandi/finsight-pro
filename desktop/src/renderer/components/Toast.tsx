import { useState, useEffect, useCallback, createContext, useContext } from 'react';
import { X, CheckCircle, AlertTriangle, XCircle, Info } from 'lucide-react';

type ToastType = 'success' | 'warning' | 'error' | 'info';

interface Toast {
  id: string;
  type: ToastType;
  message: string;
}

interface ToastContextValue {
  toast: (type: ToastType, message: string) => void;
}

const ToastContext = createContext<ToastContextValue>({ toast: () => {} });

export function useToast() {
  return useContext(ToastContext);
}

const icons = {
  success: CheckCircle,
  warning: AlertTriangle,
  error: XCircle,
  info: Info,
};

const styles = {
  success: 'bg-semantic-success/10 border-semantic-success/30 text-semantic-success',
  warning: 'bg-semantic-warning/10 border-semantic-warning/30 text-semantic-warning',
  error: 'bg-semantic-danger/10 border-semantic-danger/30 text-semantic-danger',
  info: 'bg-semantic-info/10 border-semantic-info/30 text-semantic-info',
};

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const toast = useCallback((type: ToastType, message: string) => {
    const id = Date.now().toString(36) + Math.random().toString(36).slice(2);
    setToasts((prev) => [...prev, { id, type, message }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 4000);
  }, []);

  const remove = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  return (
    <ToastContext.Provider value={{ toast }}>
      {children}
      {/* Toast container */}
      <div className="fixed bottom-4 right-4 z-[100] flex flex-col gap-2 max-w-sm">
        {toasts.map((t) => {
          const Icon = icons[t.type];
          return (
            <div
              key={t.id}
              className={`flex items-center gap-3 px-4 py-3 rounded-lg border shadow-elevated animate-slide-up ${styles[t.type]}`}
            >
              <Icon size={16} className="shrink-0" />
              <p className="text-sm font-medium flex-1">{t.message}</p>
              <button onClick={() => remove(t.id)} className="shrink-0 opacity-60 hover:opacity-100">
                <X size={14} />
              </button>
            </div>
          );
        })}
      </div>
    </ToastContext.Provider>
  );
}