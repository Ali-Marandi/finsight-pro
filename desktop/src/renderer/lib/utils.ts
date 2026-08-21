import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatPercent(value: number, decimals = 1): string {
  return `${(value * 100).toFixed(decimals)}%`;
}

export function formatRatio(value: number, decimals = 2): string {
  return value.toFixed(decimals);
}

export function formatCurrency(value: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value);
}

export function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
}

export function getStatusColor(status: 'good' | 'warning' | 'critical'): string {
  switch (status) {
    case 'good': return 'text-semantic-success';
    case 'warning': return 'text-semantic-warning';
    case 'critical': return 'text-semantic-danger';
  }
}

export function getStatusBg(status: 'good' | 'warning' | 'critical'): string {
  switch (status) {
    case 'good': return 'bg-semantic-success/10';
    case 'warning': return 'bg-semantic-warning/10';
    case 'critical': return 'bg-semantic-danger/10';
  }
}
