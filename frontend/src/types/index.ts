export interface Engagement {
  id: string;
  client_id: string;
  name: string;
  type: string;
  status: string;
  start_date: string;
  end_date: string | null;
  planned_end_date: string;
  engagement_manager_id: string;
}

export interface EngagementList {
  engagements: Engagement[];
  total: number;
}

export interface KPIFinancial {
  revenue: number;
  cost: number;
  gross_margin: number;
  margin_pct: number;
  planned_budget: number;
  actual_budget: number;
  budget_variance_pct: number;
}

export interface KPIDelivery {
  schedule_variance_days: number;
  avg_critical_path_delay_days: number;
  milestone_count: number;
}

export interface TicketBacklog {
  total: number;
  open: number;
  in_progress: number;
  resolved: number;
  closed: number;
  high_priority_open: number;
  critical_open: number;
}

export interface Utilization {
  avg_utilization: number;
  total_billable: number;
  total_non_billable: number;
  total_overtime: number;
  overtime_pct: number;
}

export interface KPIDOperational {
  ticket_backlog: TicketBacklog;
  sla_breach_rate_pct: number;
  sla_breaches: number;
  sla_total_events: number;
  change_request_count: number;
  change_request_approval_rate_pct: number;
  change_request_cost_impact: number;
  change_request_schedule_impact_days: number;
  utilization: Utilization;
}

export interface KPIClient {
  overall_satisfaction: number;
  delivery_quality: number;
  communication: number;
  responsiveness: number;
  value_for_money: number;
  nps_score: number;
  trend: 'improving' | 'stable' | 'declining';
}

export interface EngagementKPIs {
  engagement_id: string;
  financial: KPIFinancial;
  delivery: KPIDelivery;
  operational: KPIDOperational;
  client: KPIClient;
}

export interface RiskFactors {
  financial_risk: number;
  delivery_risk: number;
  operational_risk: number;
  client_risk: number;
  data_quality_risk: number;
  composite_score: number;
  risk_level: 'low' | 'medium' | 'high' | 'critical';
}

export interface SHAPContribution {
  feature: string;
  value: number;
  shap_value: number;
}

export interface SHAPExplanation {
  engagement_id: string;
  base_value: number;
  contributions: SHAPContribution[];
}

export interface Anomaly {
  metric: string;
  value: number;
  expected_range: [number, number];
  severity: 'low' | 'medium' | 'high';
  description: string;
  detected_at: string;
}

export interface InvestigateRequest {
  question: string;
  engagement_id?: string;
}

export interface InvestigateResponse {
  question: string;
  engagement_id: string | null;
  answer: string;
  tool_calls: ToolCall[];
  evidence: Evidence[];
}

export interface ToolCall {
  tool: string;
  args: Record<string, any>;
  result: any;
  error: string | null;
}

export interface Evidence {
  doc_id: string;
  title: string;
  section: string;
  content: string;
  source: string;
}

export interface ModelMetrics {
  auc: number;
  accuracy: number;
  precision: number;
  recall: number;
  f1: number;
  feature_importance: Record<string, number>;
  n_train: number;
  n_test: number;
}