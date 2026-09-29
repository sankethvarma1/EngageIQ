export function formatCurrency(value: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value);
}

export function formatNumber(value: number): string {
  return new Intl.NumberFormat('en-US').format(value);
}

export function formatFixed(value: number | string, digits = 1): string {
  const numeric = Number(value);
  return Number.isFinite(numeric) ? numeric.toFixed(digits) : '—';
}

export function formatPercent(value: number | string): string {
  const numeric = Number(value);
  return Number.isFinite(numeric) ? `${numeric >= 0 ? '+' : ''}${numeric.toFixed(1)}%` : '—';
}

export function getRiskBadgeClass(level: string): string {
  switch (level) {
    case 'critical':
      return 'badge-critical';
    case 'high':
      return 'badge-high';
    case 'medium':
      return 'badge-medium';
    case 'low':
      return 'badge-low';
    default:
      return 'badge';
  }
}

export function getRiskColor(level: string): string {
  switch (level) {
    case 'critical':
      return 'text-risk-critical';
    case 'high':
      return 'text-risk-high';
    case 'medium':
      return 'text-risk-medium';
    case 'low':
      return 'text-risk-low';
    default:
      return 'text-slate-600';
  }
}

export function getSeverityBadgeClass(severity: string): string {
  switch (severity) {
    case 'high':
      return 'badge-high';
    case 'medium':
      return 'badge-medium';
    case 'low':
      return 'badge-low';
    default:
      return 'badge';
  }
}

export function truncate(text: string, length: number): string {
  if (text.length <= length) return text;
  return text.slice(0, length) + '...';
}
