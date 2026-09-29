from datetime import date
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict


class EngagementBase(BaseModel):
    id: str
    client_id: str
    name: str
    type: str
    status: str
    start_date: date
    end_date: Optional[date]
    planned_end_date: date
    engagement_manager_id: str

    model_config = ConfigDict(from_attributes=True)


class EngagementList(BaseModel):
    engagements: List[EngagementBase]
    total: int


class KPIFinancial(BaseModel):
    revenue: float
    cost: float
    gross_margin: float
    margin_pct: float
    planned_budget: float
    actual_budget: float
    budget_variance_pct: float


class KPIDelivery(BaseModel):
    schedule_variance_days: int
    avg_critical_path_delay_days: float
    milestone_count: int


class TicketBacklog(BaseModel):
    total: int
    open: int
    in_progress: int
    resolved: int
    closed: int
    high_priority_open: int
    critical_open: int


class Utilization(BaseModel):
    avg_utilization: float
    total_billable: float
    total_non_billable: float
    total_overtime: float
    overtime_pct: float


class KPIDOperational(BaseModel):
    ticket_backlog: TicketBacklog
    sla_breach_rate_pct: float
    sla_breaches: int
    sla_total_events: int
    change_request_count: int
    change_request_approval_rate_pct: float
    change_request_cost_impact: float
    change_request_schedule_impact_days: int
    utilization: Utilization


class KPIClient(BaseModel):
    overall_satisfaction: float
    delivery_quality: float
    communication: float
    responsiveness: float
    value_for_money: float
    nps_score: float
    trend: str


class EngagementKPIs(BaseModel):
    engagement_id: str
    financial: KPIFinancial
    delivery: KPIDelivery
    operational: KPIDOperational
    client: KPIClient


class RiskFactors(BaseModel):
    financial_risk: float
    delivery_risk: float
    operational_risk: float
    client_risk: float
    data_quality_risk: float
    composite_score: float
    risk_level: str


class SHAPContribution(BaseModel):
    feature: str
    value: float
    shap_value: float


class SHAPExplanation(BaseModel):
    engagement_id: str
    base_value: float
    contributions: List[SHAPContribution]


class Anomaly(BaseModel):
    metric: str
    value: float
    expected_range: List[float]
    severity: str
    description: str
    detected_at: date


class InvestigateRequest(BaseModel):
    question: str
    engagement_id: Optional[str] = None


class InvestigateResponse(BaseModel):
    question: str
    engagement_id: Optional[str]
    answer: str
    tool_calls: List[Dict[str, Any]]
    evidence: List[Dict[str, Any]]


class ModelMetrics(BaseModel):
    auc: float
    accuracy: float
    precision: float
    recall: float
    f1: float
    feature_importance: Dict[str, float]
    n_train: int
    n_test: int


class HealthResponse(BaseModel):
    status: str
    version: str
    database: str
