'use client';

interface SHAPChartProps {
  contributions: Array<{ feature: string; shap_value: number; value: number }>;
  height?: number;
}

function formatFeatureName(feature: string): string {
  return feature.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase());
}

function formatRawValue(value: number): string {
  return Number.isInteger(value) ? value.toString() : value.toFixed(2);
}

export function SHAPChart({ contributions }: SHAPChartProps) {
  const rows = [...contributions]
    .sort((a, b) => Math.abs(b.shap_value) - Math.abs(a.shap_value))
    .slice(0, 10);
  const maxAbs = Math.max(...rows.map((c) => Math.abs(c.shap_value)), 0) || 1;

  return (
    <div className="card">
      <div className="card-header">
        <h3 className="font-semibold text-slate-900">Top Risk Drivers (SHAP)</h3>
        <p className="text-xs text-slate-500 mt-1">Red increases risk, Green decreases risk</p>
      </div>
      <div className="card-body">
        {rows.length === 0 ? (
          <p className="text-sm text-slate-500">No explanation data available.</p>
        ) : (
          <div className="space-y-2">
            {rows.map((c) => {
              const positive = c.shap_value >= 0;
              const widthPct = (Math.abs(c.shap_value) / maxAbs) * 50;
              return (
                <div key={c.feature} className="flex items-center gap-2">
                  <div
                    className="w-40 shrink-0 truncate text-xs text-slate-600"
                    title={`${formatFeatureName(c.feature)} = ${formatRawValue(c.value)}`}
                  >
                    {formatFeatureName(c.feature)}
                  </div>
                  <div className="relative flex-1 h-5 bg-slate-100 rounded overflow-hidden">
                    <div className="absolute left-1/2 top-0 bottom-0 w-px bg-slate-300" />
                    <div
                      className={`absolute top-1 bottom-1 rounded ${
                        positive ? 'left-1/2 bg-red-500' : 'right-1/2 bg-green-500'
                      }`}
                      style={{ width: `${widthPct}%` }}
                    />
                  </div>
                  <div className="w-32 shrink-0 text-right text-xs tabular-nums">
                    <span className={`font-medium ${positive ? 'text-red-600' : 'text-green-600'}`}>
                      {positive ? '+' : ''}
                      {c.shap_value.toFixed(3)}
                    </span>{' '}
                    <span className="text-slate-400">({formatRawValue(c.value)})</span>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
