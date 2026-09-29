'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { engagementApi } from '@/lib/api';
import { enrichEngagements, EnrichedEngagement } from '@/lib/engagements';
import { RiskBadge } from '@/components/RiskBadge';
import { formatFixed, formatPercent } from '@/lib/utils';

export default function EngagementsPage() {
  const [engagements, setEngagements] = useState<EnrichedEngagement[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(0);
  const [filters, setFilters] = useState({ status: '', risk: '' });

  useEffect(() => {
    async function fetchData() {
      setLoading(true);
      try {
        const { data } = await engagementApi.list({ limit: 200 });

        const enriched = await enrichEngagements(data.engagements);
        setEngagements(enriched);
      } catch (err) {
        setError('Failed to load engagements');
      } finally {
        setLoading(false);
      }
    }

    fetchData();
  }, []);

  const riskOptions = ['low', 'medium', 'high', 'critical'] as const;
  const filteredEngagements = engagements.filter(eng =>
    (!filters.status || eng.status === filters.status) &&
    (!filters.risk || eng.risk?.risk_level === filters.risk)
  );
  const total = filteredEngagements.length;
  const visibleEngagements = filteredEngagements.slice(page * 20, (page + 1) * 20);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Engagements</h1>
          <p className="text-slate-500 mt-1">Monitor and manage client engagements</p>
        </div>
      </div>

      <div className="card">
        <div className="card-body">
          <div className="flex flex-wrap gap-4">
            <select
              value={filters.status}
              onChange={(e) => { setFilters({ ...filters, status: e.target.value }); setPage(0); }}
              className="px-3 py-2 border border-slate-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              <option value="">All Statuses</option>
              <option value="active">Active</option>
              <option value="completed">Completed</option>
              <option value="on_hold">On Hold</option>
              <option value="cancelled">Cancelled</option>
            </select>
            <select
              value={filters.risk}
              onChange={(e) => { setFilters({ ...filters, risk: e.target.value }); setPage(0); }}
              className="px-3 py-2 border border-slate-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              <option value="">All Risk Levels</option>
              {riskOptions.map(r => (
                <option key={r} value={r}>
                  {r.charAt(0).toUpperCase() + r.slice(1)}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-4 border-primary-500 border-t-transparent"></div>
        </div>
      ) : error ? (
        <div className="card p-8 text-center text-red-600">{error}</div>
      ) : (
        <div className="card">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="text-left text-sm text-slate-500 border-b border-slate-200">
                  <th className="pb-3 font-medium">Engagement</th>
                  <th className="pb-3 font-medium">Client</th>
                  <th className="pb-3 font-medium">Type</th>
                  <th className="pb-3 font-medium">Status</th>
                  <th className="pb-3 font-medium">Risk</th>
                  <th className="pb-3 font-medium">Margin</th>
                  <th className="pb-3 font-medium">Budget Var.</th>
                  <th className="pb-3 font-medium">SLA Breach</th>
                  <th className="pb-3 font-medium">Satisfaction</th>
                  <th className="pb-3 font-medium"></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {visibleEngagements.map((eng) => (
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
                    <td className="py-3 text-sm text-slate-700 font-medium">
                      {eng.kpis ? formatPercent(eng.kpis.financial.margin_pct) : '—'}
                    </td>
                    <td className="py-3 text-sm text-slate-700">
                      {eng.kpis ? formatPercent(eng.kpis.financial.budget_variance_pct) : '—'}
                    </td>
                    <td className="py-3 text-sm text-slate-700">
                      {eng.kpis ? formatPercent(eng.kpis.operational.sla_breach_rate_pct) : '—'}
                    </td>
                    <td className="py-3 text-sm text-slate-700">
                      {eng.kpis ? formatFixed(eng.kpis.client.overall_satisfaction) : '—'}
                    </td>
                    <td className="py-3 text-right">
                      <Link href={`/engagements/${eng.id}`} className="text-sm text-primary-600 hover:underline">
                        View
                      </Link>
                    </td>
                  </tr>
                ))}
                {total === 0 && (
                  <tr><td colSpan={10} className="py-8 text-center text-slate-500">No engagements match these filters.</td></tr>
                )}
              </tbody>
            </table>
          </div>
          {total > 20 && (
            <div className="card-header flex items-center justify-between">
              <p className="text-sm text-slate-500">
                Showing {page * 20 + 1} to {Math.min((page + 1) * 20, total)} of {total}
              </p>
              <div className="flex gap-2">
                <button
                  onClick={() => setPage(p => Math.max(0, p - 1))}
                  disabled={page === 0}
                  className="btn-secondary disabled:opacity-50"
                >
                  Previous
                </button>
                <button
                  onClick={() => setPage(p => p + 1)}
                  disabled={(page + 1) * 20 >= total}
                  className="btn-secondary disabled:opacity-50"
                >
                  Next
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
