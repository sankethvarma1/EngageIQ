'use client';

import { getRiskBadgeClass } from '@/lib/utils';

interface RiskBadgeProps {
  level: 'low' | 'medium' | 'high' | 'critical';
  score?: number;
  className?: string;
}

export function RiskBadge({ level, score, className = '' }: RiskBadgeProps) {
  const label = level.charAt(0).toUpperCase() + level.slice(1);

  return (
    <span className={`${getRiskBadgeClass(level)} ${className}`}>
      {label}
      {score !== undefined && (
        <span className="ml-1 text-xs opacity-80">({(score * 100).toFixed(0)}%)</span>
      )}
    </span>
  );
}