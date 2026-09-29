import pytest
from decimal import Decimal
from datetime import date, timedelta

from app.ml.risk_model import (
    DEFAULT_RISK_WEIGHTS,
    extract_features,
    load_risk_weights,
    predict_risk,
    generate_training_labels,
    train_model,
    get_shap_explanation,
)
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
def sample_engagement(db):
    client = Client(
        id="RISK001",
        name="Risk Test Client",
        industry="Financial Services",
        region="North America",
        account_tier="strategic",
        annual_revenue=Decimal("50000000"),
    )
    db.add(client)

    emp = Employee(
        id="EMP9001",
        name="Risk Manager",
        email="risk.manager@northstar.com",
        role="manager",
        department="Risk",
        hire_date=date(2018, 1, 1),
        hourly_rate=Decimal("300.00"),
        is_billable=True,
    )
    db.add(emp)

    eng = Engagement(
        id="ENG888",
        client_id="RISK001",
        name="Risk Test Engagement",
        type=EngagementType.ADVISORY,
        status=EngagementStatus.ACTIVE,
        start_date=date.today() - timedelta(weeks=20),
        planned_end_date=date.today() + timedelta(weeks=20),
        engagement_manager_id="EMP9001",
        sales_rep_id="EMP9001",
    )
    db.add(eng)

    db.flush()

    budget = Budget(
        engagement_id="ENG888",
        category="labor",
        planned_amount=Decimal("1000000"),
        actual_amount=Decimal("1200000"),
        period_start=eng.start_date,
        period_end=eng.planned_end_date,
    )
    db.add(budget)

    invoice = Invoice(
        id="INV88801",
        engagement_id="ENG888",
        invoice_number="INV-ENG888-001",
        amount=Decimal("800000"),
        status="paid",
        invoice_date=date.today() - timedelta(weeks=10),
        due_date=date.today() - timedelta(weeks=6),
        paid_date=date.today() - timedelta(weeks=5),
    )
    db.add(invoice)

    for i in range(20):
        week = eng.start_date + timedelta(weeks=i)
        ts = Timesheet(
            employee_id="EMP9001",
            engagement_id="ENG888",
            week_start=week,
            billable_hours=Decimal("35.00"),
            non_billable_hours=Decimal("3.00"),
            overtime_hours=Decimal("2.00"),
        )
        db.add(ts)

    for i in range(8):
        ms = Milestone(
            engagement_id="ENG888",
            name=f"Milestone {i+1}",
            planned_date=eng.start_date + timedelta(weeks=(i+1)*2),
            actual_date=eng.start_date + timedelta(weeks=(i+1)*2, days=10),
            status=MilestoneStatus.COMPLETED,
            is_critical_path=i % 2 == 0,
        )
        db.add(ms)

    for i in range(15):
        ticket = Ticket(
            id=f"TKT888{i:03d}",
            engagement_id="ENG888",
            title=f"Ticket {i+1}",
            priority=TicketPriority.CRITICAL if i < 3 else TicketPriority.HIGH,
            status=TicketStatus.OPEN if i < 5 else TicketStatus.RESOLVED,
            reported_date=eng.start_date + timedelta(weeks=i),
            resolved_date=eng.start_date + timedelta(weeks=i, days=10) if i >= 5 else None,
            sla_due_date=eng.start_date + timedelta(weeks=i, days=3),
        )
        db.add(ticket)

    for i in range(15):
        sla = SLAEvent(
            engagement_id="ENG888",
            event_type=SLAEventType.RESOLUTION_TIME,
            is_breach=i < 5,
            metric_value=Decimal(str(25 + i)),
            threshold_value=Decimal("20.00"),
            event_date=eng.start_date + timedelta(weeks=i),
        )
        db.add(sla)

    for i in range(5):
        cr = ChangeRequest(
            id=f"CR888{i:02d}",
            engagement_id="ENG888",
            title=f"Change Request {i+1}",
            impact_category="budget",
            estimated_cost_impact=Decimal("50000"),
            estimated_schedule_impact_days=10,
            status=ChangeRequestStatus.APPROVED,
            requested_date=eng.start_date + timedelta(weeks=i*3),
        )
        db.add(cr)

    for i in range(4):
        fb = ClientFeedback(
            engagement_id="ENG888",
            survey_date=eng.start_date + timedelta(weeks=(i+1)*4),
            overall_satisfaction=5 - i,
            delivery_quality=5 - i,
            communication=5 - i,
            responsiveness=5 - i,
            value_for_money=5 - i,
            nps_score=4 - i,
        )
        db.add(fb)

    db.commit()
    return eng


def test_extract_features(db, sample_engagement):
    features = extract_features(db, "ENG888")
    assert "margin_pct" in features
    assert "budget_variance_pct" in features
    assert "schedule_variance_days" in features
    assert "ticket_critical" in features
    assert "sla_breach_rate_pct" in features
    assert "client_satisfaction" in features
    assert features["budget_variance_pct"] > 0
    assert features["ticket_critical"] >= 3


def test_predict_risk(db, sample_engagement):
    risk = predict_risk(db, "ENG888")
    assert 0 <= risk.composite_score <= 1
    assert risk.risk_level in ["low", "medium", "high", "critical"]
    assert hasattr(risk, "financial_risk")
    assert hasattr(risk, "delivery_risk")
    assert hasattr(risk, "operational_risk")
    assert hasattr(risk, "client_risk")
    assert hasattr(risk, "data_quality_risk")


def test_generate_training_labels(db, sample_engagement):
    X, y = generate_training_labels(db)
    assert len(X) > 0
    assert len(y) == len(X)
    assert set(y.unique()).issubset({0, 1})


def test_load_risk_weights_defaults():
    weights = load_risk_weights()
    assert set(weights) == set(DEFAULT_RISK_WEIGHTS)
    assert abs(sum(weights.values()) - 1.0) < 1e-9
    assert all(v >= 0 for v in weights.values())


def test_shap_explanation(db, sample_engagement):
    explanation = get_shap_explanation(db, "ENG888")
    if "error" not in explanation:
        assert "contributions" in explanation
        assert "base_value" in explanation
        assert len(explanation["contributions"]) > 0
        for contrib in explanation["contributions"]:
            assert "feature" in contrib
            assert "value" in contrib
            assert "shap_value" in contrib