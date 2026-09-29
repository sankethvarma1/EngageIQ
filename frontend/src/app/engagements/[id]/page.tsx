'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { engagementApi } from '@/lib/api';
import { RiskBadge } from '@/components/RiskBadge';
import { SHAPChart } from '@/components/SHAPChart';
import { formatCurrency, formatFixed, formatPercent, getSeverityBadgeClass } from '@/lib/utils';
import { Engagement, EngagementKPIs, RiskFactors, SHAPExplanation, Anomaly } from '@/types';

export default function EngagementDetailPage() {
  const params = useParams();
  const engagementId = params.id as string;

  const [engagement, setEngagement] = useState<Engagement | null>(null);
  const [kpis, setKpis] = useState<EngagementKPIs | null>(null);
  const [risk, setRisk] = useState<RiskFactors | null>(null);
  const [explanation, setExplanation] = useState<SHAPExplanation | null>(null);
  const [anomalies, setAnomalies] = useState<Anomaly[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchData() {
      setLoading(true);
      try {
        const [engRes, kpisRes, riskRes, explRes, anomRes] = await Promise.all([
          engagementApi.get(engagementId).catch(() => null),
          engagementApi.getKPIs(engagementId).catch(() => null),
          engagementApi.getRisk(engagementId).catch(() => null),
          engagementApi.getExplanation(engagementId).catch(() => null),
          engagementApi.getAnomalies(engagementId).catch(() => null),
        ]);

        if (!engRes?.data) {
          setError('Engagement not found');
          return;
        }

        setEngagement(engRes.data);
        setKpis(kpisRes?.data || null);
        setRisk(riskRes?.data || null);
        setExplanation(explRes?.data || null);
        setAnomalies(anomRes?.data || []);
      } catch (err) {
        setError('Failed to load engagement data');
      } finally {
        setLoading(false);
      }
    }

    fetchData();
  }, [engagementId]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-4 border-primary-500 border-t-transparent"></div>
      </div>
    );
  }

  if (error || !engagement) {
    return <div className="card p-8 text-center text-red-600">{error || 'Engagement not found'}</div>;
  }

  const riskLevel = risk?.risk_level || 'low';

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <Link href="/engagements" className="text-sm text-primary-600 hover:underline mb-2 inline-block">
            ← Back to Engagements
          </Link>
          <h1 className="text-2xl font-bold text-slate-900">{engagement.name}</h1>
          <p className="text-slate-500 mt-1">{engagement.id} • {engagement.client_id} • {engagement.type}</p>
        </div>
        <div className="flex items-center gap-4">
          <RiskBadge level={riskLevel} score={risk?.composite_score} />
          <span className={`badge ${engagement.status === 'active' ? 'bg-green-100 text-green-800' : 'bg-slate-100 text-slate-700'}`}>
            {engagement.status}
          </span>
        </div>
      </div>

      {kpis && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="card">
            <div className="card-body">
              <h3 className="text-sm font-medium text-slate-500">Financial</h3>
              <div className="space-y-2 mt-2">
                <div className="flex justify-between text-sm">
                  <span className="text-slate-500">Revenue</span>
                  <span className="font-medium">{formatCurrency(kpis.financial.revenue)}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-slate-500">Cost</span>
                  <span className="font-medium">{formatCurrency(kpis.financial.cost)}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-slate-500">Gross Margin</span>
                  <span className="font-medium">{formatCurrency(kpis.financial.gross_margin)}</span>
                </div>
                <div className="flex justify-between text-sm border-t border-slate-100 pt-2">
                  <span className="text-slate-500">Margin %</span>
                  <span className={`font-semibold ${kpis.financial.margin_pct < 20 ? 'text-red-600' : 'text-green-600'}`}>
                    {formatPercent(kpis.financial.margin_pct)}
                  </span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-slate-500">Budget Variance</span>
                  <span className={`font-medium ${kpis.financial.budget_variance_pct > 10 ? 'text-red-600' : 'text-slate-900'}`}>
                    {formatPercent(kpis.financial.budget_variance_pct)}
                  </span>
                </div>
              </div>
            </div>
          </div>

          <div className="card">
            <div className="card-body">
              <h3 className="text-sm font-medium text-slate-500">Delivery</h3>
              <div className="space-y-2 mt-2">
                <div className="flex justify-between text-sm">
                  <span className="text-slate-500">Schedule Variance</span>
                  <span className={`font-medium ${kpis.delivery.schedule_variance_days > 14 ? 'text-red-600' : 'text-slate-900'}`}>
                    {kpis.delivery.schedule_variance_days} days
                  </span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-slate-500">Avg Critical Delay</span>
                  <span className="font-medium">{formatFixed(kpis.delivery.avg_critical_path_delay_days)} days</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-slate-500">Change Requests</span>
                  <span className="font-medium">{kpis.operational.change_request_count}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-slate-500">CR Cost Impact</span>
                  <span className="font-medium">{formatCurrency(kpis.operational.change_request_cost_impact)}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-slate-500">CR Schedule Impact</span>
                  <span className="font-medium">{kpis.operational.change_request_schedule_impact_days} days</span>
                </div>
              </div>
            </div>
          </div>

          <div className="card">
            <div className="card-body">
              <h3 className="text-sm font-medium text-slate-500">Operations</h3>
              <div className="space-y-2 mt-2">
                <div className="flex justify-between text-sm">
                  <span className="text-slate-500">Total Tickets</span>
                  <span className="font-medium">{kpis.operational.ticket_backlog.total}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-slate-500">Critical Open</span>
                  <span className={`font-medium ${kpis.operational.ticket_backlog.critical_open > 0 ? 'text-red-600' : 'text-slate-900'}`}>
                    {kpis.operational.ticket_backlog.critical_open}
                  </span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-slate-500">SLA Breach Rate</span>
                  <span className={`font-medium ${kpis.operational.sla_breach_rate_pct > 10 ? 'text-red-600' : 'text-slate-900'}`}>
                    {formatPercent(kpis.operational.sla_breach_rate_pct)}
                  </span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-slate-500">Utilization</span>
                  <span className={`font-medium ${kpis.operational.utilization.avg_utilization < 60 ? 'text-red-600' : 'text-slate-900'}`}>
                    {formatPercent(kpis.operational.utilization.avg_utilization)}
                  </span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-slate-500">Overtime %</span>
                  <span className={`font-medium ${kpis.operational.utilization.overtime_pct > 15 ? 'text-red-600' : 'text-slate-900'}`}>
                    {formatPercent(kpis.operational.utilization.overtime_pct)}
                  </span>
                </div>
              </div>
            </div>
          </div>

          <div className="card">
            <div className="card-body">
              <h3 className="text-sm font-medium text-slate-500">Client</h3>
              <div className="space-y-2 mt-2">
                <div className="flex justify-between text-sm">
                  <span className="text-slate-500">Overall Satisfaction</span>
                  <span className={`font-semibold ${kpis.client.overall_satisfaction < 6 ? 'text-red-600' : kpis.client.overall_satisfaction < 7.5 ? 'text-yellow-600' : 'text-green-600'}`}>
                    {formatFixed(kpis.client.overall_satisfaction)}/10
                  </span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-slate-500">Delivery Quality</span>
                  <span className="font-medium">{formatFixed(kpis.client.delivery_quality)}/10</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-slate-500">Communication</span>
                  <span className="font-medium">{formatFixed(kpis.client.communication)}/10</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-slate-500">NPS Score</span>
                  <span className={`font-medium ${kpis.client.nps_score < 7 ? 'text-red-600' : 'text-green-600'}`}>
                    {kpis.client.nps_score}/10
                  </span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-slate-500">Trend</span>
                  <span className={`badge ${kpis.client.trend === 'improving' ? 'bg-green-100 text-green-800' : kpis.client.trend === 'declining' ? 'bg-red-100 text-red-800' : 'bg-slate-100 text-slate-800'}`}>
                    {kpis.client.trend}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {explanation && explanation.contributions.length > 0 && (
          <SHAPChart contributions={explanation.contributions} />
        )}

        <div className="card">
          <div className="card-header">
            <h3 className="font-semibold text-slate-900">Risk Breakdown</h3>
          </div>
          <div className="card-body space-y-3">
            {risk && (
              <>
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-slate-500">Financial Risk</span>
                    <span className="font-medium">{(risk.financial_risk * 100).toFixed(0)}%</span>
                  </div>
                  <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                    <div className="h-full bg-red-500" style={{ width: `${risk.financial_risk * 100}%` }}></div>
                  </div>
                </div>
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-slate-500">Delivery Risk</span>
                    <span className="font-medium">{(risk.delivery_risk * 100).toFixed(0)}%</span>
                  </div>
                  <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                    <div className="h-full bg-orange-500" style={{ width: `${risk.delivery_risk * 100}%` }}></div>
                  </div>
                </div>
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-slate-500">Operational Risk</span>
                    <span className="font-medium">{(risk.operational_risk * 100).toFixed(0)}%</span>
                  </div>
                  <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                    <div className="h-full bg-yellow-500" style={{ width: `${risk.operational_risk * 100}%` }}></div>
                  </div>
                </div>
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-slate-500">Client Risk</span>
                    <span className="font-medium">{(risk.client_risk * 100).toFixed(0)}%</span>
                  </div>
                  <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                    <div className="h-full bg-blue-500" style={{ width: `${risk.client_risk * 100}%` }}></div>
                  </div>
                </div>
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-slate-500">Utilization and Overtime Risk</span>
                    <span className="font-medium">{(risk.data_quality_risk * 100).toFixed(0)}%</span>
                  </div>
                  <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                    <div className="h-full bg-slate-500" style={{ width: `${risk.data_quality_risk * 100}%` }}></div>
                  </div>
                </div>
              </>
            )}
          </div>
        </div>
      </div>

      {anomalies.length > 0 && (
        <div className="card">
          <div className="card-header">
            <h3 className="font-semibold text-slate-900">Anomalies Detected</h3>
          </div>
          <div className="card-body">
            <div className="space-y-3">
              {anomalies.map((anom, i) => (
                <div key={i} className="flex items-start gap-3 p-3 bg-slate-50 rounded-lg">
                  <span className={getSeverityBadgeClass(anom.severity)}>{anom.severity}</span>
                  <div className="flex-1">
                    <p className="font-medium text-slate-900">{anom.description}</p>
                    <p className="text-sm text-slate-500">
                      Metric: {anom.metric} | Value: {anom.value.toFixed(1)} | Expected: {anom.expected_range[0].toFixed(1)}–{anom.expected_range[1].toFixed(1)}
                    </p>
                    <p className="text-xs text-slate-400 mt-1">Detected: {anom.detected_at}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
