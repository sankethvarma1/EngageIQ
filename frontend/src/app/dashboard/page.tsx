'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { engagementApi } from '@/lib/api';
import { enrichEngagements } from '@/lib/engagements';
import { KPICard } from '@/components/KPICard';
import { RiskBadge } from '@/components/RiskBadge';
import { formatFixed, formatPercent } from '@/lib/utils';
import { Engagement, EngagementKPIs, RiskFactors } from '@/types';

interface DashboardMetrics {
  totalEngagements: number;
  highRiskEngagements: number;
  avgMargin: number;
  avgBudgetVariance: number;
  slaBreachRate: number;
  avgClientSatisfaction: number;
  recentEngagements: (Engagement & { risk?: RiskFactors; kpis?: EngagementKPIs })[];
}

export default function DashboardPage() {
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchData() {
      try {
        const { data: engagements } = await engagementApi.list({ limit: 50 });
        const engagementData = await enrichEngagements(engagements.engagements);

        const highRisk = engagementData.filter((e): e is Engagement & { risk: RiskFactors } => 
          !!e.risk && ['high', 'critical'].includes(e.risk.risk_level)).length;
        const margins = engagementData.filter((e): e is Engagement & { kpis: EngagementKPIs } => !!e.kpis)
          .map(e => Number(e.kpis!.financial.margin_pct));
        const budgetVars = engagementData.filter((e): e is Engagement & { kpis: EngagementKPIs } => !!e.kpis)
          .map(e => Number(e.kpis!.financial.budget_variance_pct));
        const slaRates = engagementData.filter((e): e is Engagement & { kpis: EngagementKPIs } => !!e.kpis)
          .map(e => Number(e.kpis!.operational.sla_breach_rate_pct));
        const sats = engagementData.filter((e): e is Engagement & { kpis: EngagementKPIs } => !!e.kpis)
          .map(e => Number(e.kpis!.client.overall_satisfaction));

        setMetrics({
          totalEngagements: engagements.total,
          highRiskEngagements: highRisk,
          avgMargin: margins.length ? margins.reduce((a, b) => a + b, 0) / margins.length : 0,
          avgBudgetVariance: budgetVars.length ? budgetVars.reduce((a, b) => a + b, 0) / budgetVars.length : 0,
          slaBreachRate: slaRates.length ? slaRates.reduce((a, b) => a + b, 0) / slaRates.length : 0,
          avgClientSatisfaction: sats.length ? sats.reduce((a, b) => a + b, 0) / sats.length : 0,
          recentEngagements: engagementData.sort((a, b) => new Date(b.start_date).getTime() - new Date(a.start_date).getTime()).slice(0, 10),
        });
      } catch (err) {
        setError('Failed to load dashboard data');
      } finally {
        setLoading(false);
      }
    }

    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-4 border-primary-500 border-t-transparent"></div>
      </div>
    );
  }

  if (error) {
    return <div className="card p-8 text-center text-red-600">{error}</div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Dashboard</h1>
          <p className="text-slate-500 mt-1">Client Delivery Intelligence Overview</p>
        </div>
        <Link href="/engagements" className="btn-primary">
          View All Engagements
        </Link>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
        <KPICard label="Total Engagements" value={metrics!.totalEngagements} format="number" />
        <KPICard label="High Risk" value={metrics!.highRiskEngagements} format="number" trend={metrics!.highRiskEngagements > 5 ? 'up' : 'neutral'} trendLabel="needs attention" />
        <KPICard label="Avg Margin" value={metrics!.avgMargin} format="percent" trend={metrics!.avgMargin > 30 ? 'up' : metrics!.avgMargin < 20 ? 'down' : 'neutral'} />
        <KPICard label="Avg Budget Variance" value={metrics!.avgBudgetVariance} format="percent" trend={metrics!.avgBudgetVariance > 10 ? 'down' : 'neutral'} />
        <KPICard label="SLA Breach Rate" value={metrics!.slaBreachRate} format="percent" trend={metrics!.slaBreachRate > 10 ? 'down' : 'neutral'} />
        <KPICard label="Client Satisfaction" value={metrics!.avgClientSatisfaction} format="number" trend={metrics!.avgClientSatisfaction > 7.5 ? 'up' : metrics!.avgClientSatisfaction < 6 ? 'down' : 'neutral'} trendLabel="/10" />
      </div>

      <div className="card">
        <div className="card-header">
          <h2 className="font-semibold text-slate-900">Recent Engagements</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="text-left text-sm text-slate-500 border-b border-slate-200">
                <th className="pb-3 font-medium">Engagement</th>
                <th className="pb-3 font-medium">Client</th>
                <th className="pb-3 font-medium">Type</th>
                <th className="pb-3 font-medium">Status</th>
                <th className="pb-3 font-medium">Risk</th>
                <th className="pb-3 fontmedium">Margin</th>
                <th className="pb-3 font-medium">Satisfaction</th>
                <th className="pb-3 font-medium"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {metrics!.recentEngagements.map((eng) => (
                <tr key={eng.id} className="hover:bg-slate-50">
                  <td className="py-3">
                    <Link href={`/engagements/${eng.id}`} className="font-medium text-primary-600 hover:underline">
                      {eng.id}
                    </Link>
                    <p className="text-sm text-slate-500 truncate max-w-xs">{eng.name}</p>
                  </td>
                  <td className="py-3 text-sm text-slate-700">{eng.client_id}</td>
                  <td className="py-3">
                    <span className="badge bg-slate-100 text-slate-700">{eng.type}</span>
                  </td>
                  <td className="py-3">
                    <span className={`badge ${eng.status === 'active' ? 'bg-green-100 text-green-800' : eng.status === 'completed' ? 'bg-blue-100 text-blue-800' : 'bg-slate-100 text-slate-700'}`}>
                      {eng.status}
                    </span>
                  </td>
                  <td className="py-3">
                    {eng.risk && <RiskBadge level={eng.risk.risk_level} score={eng.risk.composite_score} />}
                  </td>
                  <td className="py-3 text-sm text-slate-700">
                    {eng.kpis ? formatPercent(eng.kpis.financial.margin_pct) : '—'}
                  </td>
                  <td className="py-3 text-sm text-slate-700">
                    {eng.kpis ? formatFixed(eng.kpis.client.overall_satisfaction) : '—'}
                  </td>
                  <td className="py-3 text-right">
                    <Link href={`/engagements/${eng.id}`} className="text-sm text-primary-600 hover:underline">
                      View Details
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
