import pytest
from decimal import Decimal
from datetime import date, timedelta

from app.db.models import (
    Budget,
    ChangeRequest,
    ChangeRequestStatus,
    Client,
    ClientFeedback,
    Employee,
    Engagement,
    EngagementStatus,
    EngagementType,
    Invoice,
    Milestone,
    MilestoneStatus,
    SLAEvent,
    SLAEventType,
    Ticket,
    TicketPriority,
    TicketStatus,
    Timesheet,
)


@pytest.fixture
def setup_data(db):
    client = Client(
        id="API001",
        name="API Test Client",
        industry="Technology",
        region="Europe",
        account_tier="major",
        annual_revenue=Decimal("20000000"),
    )
    db.add(client)

    emp = Employee(
        id="EMP9901",
        name="API Manager",
        email="api.manager@northstar.com",
        role="director",
        department="Technology",
        hire_date=date(2017, 1, 1),
        hourly_rate=Decimal("400.00"),
        is_billable=True,
    )
    db.add(emp)

    eng = Engagement(
        id="ENG777",
        client_id="API001",
        name="API Test Engagement",
        type=EngagementType.IMPLEMENTATION,
        status=EngagementStatus.ACTIVE,
        start_date=date.today() - timedelta(weeks=8),
        planned_end_date=date.today() + timedelta(weeks=20),
        engagement_manager_id="EMP9901",
        sales_rep_id="EMP9901",
    )
    db.add(eng)

    db.flush()

    budget = Budget(
        engagement_id="ENG777",
        category="labor",
        planned_amount=Decimal("500000"),
        actual_amount=Decimal("480000"),
        period_start=eng.start_date,
        period_end=eng.planned_end_date,
    )
    db.add(budget)

    invoice = Invoice(
        id="INV77701",
        engagement_id="ENG777",
        invoice_number="INV-ENG777-001",
        amount=Decimal("300000"),
        status="paid",
        invoice_date=date.today() - timedelta(weeks=4),
        due_date=date.today(),
        paid_date=date.today() - timedelta(weeks=2),
    )
    db.add(invoice)

    for i in range(8):
        week = eng.start_date + timedelta(weeks=i)
        ts = Timesheet(
            employee_id="EMP9901",
            engagement_id="ENG777",
            week_start=week,
            billable_hours=Decimal("30.00"),
            non_billable_hours=Decimal("5.00"),
            overtime_hours=Decimal("1.00"),
        )
        db.add(ts)

    for i in range(4):
        ms = Milestone(
            engagement_id="ENG777",
            name=f"Milestone {i+1}",
            planned_date=eng.start_date + timedelta(weeks=(i+1)*2),
            actual_date=eng.start_date + timedelta(weeks=(i+1)*2, days=-2),
            status=MilestoneStatus.COMPLETED,
            is_critical_path=i == 0,
        )
        db.add(ms)

    for i in range(5):
        ticket = Ticket(
            id=f"TKT777{i:03d}",
            engagement_id="ENG777",
            title=f"Ticket {i+1}",
            priority=TicketPriority.MEDIUM,
            status=TicketStatus.RESOLVED,
            reported_date=eng.start_date + timedelta(weeks=i),
            resolved_date=eng.start_date + timedelta(weeks=i, days=2),
            sla_due_date=eng.start_date + timedelta(weeks=i, days=3),
        )
        db.add(ticket)

    for i in range(5):
        sla = SLAEvent(
            engagement_id="ENG777",
            event_type=SLAEventType.RESOLUTION_TIME,
            is_breach=False,
            metric_value=Decimal("12.00"),
            threshold_value=Decimal("24.00"),
            event_date=eng.start_date + timedelta(weeks=i),
        )
        db.add(sla)

    for i in range(2):
        cr = ChangeRequest(
            id=f"CR777{i:02d}",
            engagement_id="ENG777",
            title=f"Change Request {i+1}",
            impact_category="scope",
            estimated_cost_impact=Decimal("10000"),
            estimated_schedule_impact_days=3,
            status=ChangeRequestStatus.APPROVED,
            requested_date=eng.start_date + timedelta(weeks=i*3),
        )
        db.add(cr)

    for i in range(2):
        fb = ClientFeedback(
            engagement_id="ENG777",
            survey_date=eng.start_date + timedelta(weeks=(i+1)*3),
            overall_satisfaction=8,
            delivery_quality=8,
            communication=9,
            responsiveness=8,
            value_for_money=7,
            nps_score=8,
        )
        db.add(fb)

    db.commit()
    return eng


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_list_engagements(client, setup_data):
    response = client.get("/api/engagements")
    assert response.status_code == 200
    data = response.json()
    assert "engagements" in data
    assert "total" in data
    assert data["total"] >= 1


def test_get_engagement(client, setup_data):
    response = client.get("/api/engagements/ENG777")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "ENG777"
    assert data["name"] == "API Test Engagement"


def test_get_engagement_not_found(client):
    response = client.get("/api/engagements/NOTEXIST")
    assert response.status_code == 404


def test_get_kpis(client, setup_data):
    response = client.get("/api/engagements/ENG777/kpis")
    assert response.status_code == 200
    data = response.json()
    assert data["engagement_id"] == "ENG777"
    assert "financial" in data
    assert "delivery" in data
    assert "operational" in data
    assert "client" in data
    # The Next.js dashboard formats KPI values as numbers, not JSON strings.
    numeric_values = [
        *data["financial"].values(),
        data["delivery"]["avg_critical_path_delay_days"],
        *data["operational"]["utilization"].values(),
        data["operational"]["sla_breach_rate_pct"],
        data["operational"]["change_request_approval_rate_pct"],
        data["operational"]["change_request_cost_impact"],
        *(value for key, value in data["client"].items() if key != "trend"),
    ]
    assert all(isinstance(value, (int, float)) for value in numeric_values)


def test_get_risk(client, setup_data):
    response = client.get("/api/engagements/ENG777/risk")
    assert response.status_code == 200
    data = response.json()
    assert "composite_score" in data
    assert "risk_level" in data
    assert data["risk_level"] in ["low", "medium", "high", "critical"]


def test_get_anomalies(client, setup_data):
    response = client.get("/api/engagements/ENG777/anomalies")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_get_explanation(client, setup_data):
    response = client.get("/api/engagements/ENG777/explanation")
    assert response.status_code in [200, 404]
    if response.status_code == 200:
        data = response.json()
        assert "engagement_id" in data
        assert "contributions" in data


def test_ai_investigate(client, setup_data):
    response = client.post(
        "/api/ai/investigate",
        json={"question": "Why is engagement ENG777 high risk?", "engagement_id": "ENG777"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "tool_calls" in data


def test_model_metrics(client):
    response = client.get("/api/engagements/model/metrics")
    assert response.status_code in [200, 404]


def test_retrain_disabled_returns_403(client, monkeypatch):
    from app.core.config import get_settings
    monkeypatch.setattr(get_settings(), "allow_model_retrain", False)
    try:
        response = client.post("/api/engagements/model/retrain")
        assert response.status_code == 403
        assert "disabled" in response.json()["detail"]
    finally:
        monkeypatch.setattr(get_settings(), "allow_model_retrain", True)
