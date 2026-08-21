import { cn, formatPercent, formatRatio, getStatusColor, getStatusBg } from '../lib/utils';
import type { RatioResult } from '../../types';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

interface RatioCardProps {
  ratio: RatioResult;
}

const statusIcons = {
  good: TrendingUp,
  warning: Minus,
  critical: TrendingDown,
};

export default function RatioCard({ ratio }: RatioCardProps) {
  const StatusIcon = statusIcons[ratio.status];
  const displayValue = ratio.unit === '%'
    ? formatPercent(ratio.value)
    : formatRatio(ratio.value);

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
