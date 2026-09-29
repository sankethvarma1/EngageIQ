'use client';

import { formatCurrency, formatNumber, formatPercent } from '@/lib/utils';

interface KPICardProps {
  label: string;
  value: number | string;
  format?: 'currency' | 'number' | 'percent' | 'raw';
  trend?: 'up' | 'down' | 'neutral';
  trendLabel?: string;
  className?: string;
}

export function KPICard({ label, value, format = 'raw', trend, trendLabel, className = '' }: KPICardProps) {
  let displayValue: string;

  if (typeof value === 'number') {
    switch (format) {
      case 'currency':
        displayValue = formatCurrency(value);
        break;
      case 'number':
        displayValue = formatNumber(value);
        break;
      case 'percent':
        displayValue = formatPercent(value);
        break;
      default:
        displayValue = value.toString();
    }
  } else {
    displayValue = value;
  }

  return (
    <div className={`card ${className}`}>
      <div className="card-body">
        <p className="text-sm text-slate-500 font-medium">{label}</p>
        <div className="flex items-end gap-2 mt-1">
          <p className="text-2xl font-semibold text-slate-900">{displayValue}</p>
          {trend && trendLabel && (
            <span className={`text-sm font-medium ${trend === 'up' ? 'text-green-600' : trend === 'down' ? 'text-red-600' : 'text-slate-500'}`}>
              {trend === 'up' ? '↑' : trend === 'down' ? '↓' : '→'} {trendLabel}
            </span>
          )}
        </div>
      </div>
    </div>
  );
}