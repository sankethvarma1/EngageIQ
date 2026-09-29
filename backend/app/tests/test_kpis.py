import pytest
from decimal import Decimal
from datetime import date, timedelta

from app.analytics.kpis import (
    get_engagement_revenue,
    get_engagement_cost,
    get_budget_variance,
    get_schedule_variance,
    get_ticket_backlog,
    get_sla_breach_rate,
    get_change_request_rate,
    get_employee_utilization,
    get_client_satisfaction,
    calculate_all_kpis,
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
def sample_data(db):
    client = Client(
        id="TEST001",
        name="Test Client",
        industry="Technology",
        region="North America",
        account_tier="major",
        annual_revenue=Decimal("10000000"),
    )
    db.add(client)

    emp1 = Employee(
        id="EMP0001",
        name="John Doe",
        email="john.doe@northstar.com",
        role="consultant",
        department="Technology",
        hire_date=date(2020, 1, 15),
        hourly_rate=Decimal("180.00"),
        is_billable=True,
    )
    emp2 = Employee(
        id="EMP0002",
        name="Jane Smith",
        email="jane.smith@northstar.com",
        role="senior_consultant",
        department="Technology",
        hire_date=date(2019, 6, 1),
        hourly_rate=Decimal("220.00"),
        is_billable=True,
    )
    db.add_all([emp1, emp2])

    eng = Engagement(
        id="ENG999",
        client_id="TEST001",
        name="Test Engagement",
        type=EngagementType.CONSULTING,
        status=EngagementStatus.ACTIVE,
        start_date=date.today() - timedelta(weeks=10),
        planned_end_date=date.today() + timedelta(weeks=10),
        engagement_manager_id="EMP0001",
        sales_rep_id="EMP0001",
    )
    db.add(eng)

    db.flush()

    budget = Budget(
        engagement_id="ENG999",
        category="labor",
        planned_amount=Decimal("500000"),
        actual_amount=Decimal("550000"),
        period_start=eng.start_date,
        period_end=eng.planned_end_date,
    )
    db.add(budget)

    invoice1 = Invoice(
        id="INV99901",
        engagement_id="ENG999",
        invoice_number="INV-ENG999-001",
        amount=Decimal("200000"),
        status="paid",
        invoice_date=date.today() - timedelta(weeks=8),
        due_date=date.today() - timedelta(weeks=4),
        paid_date=date.today() - timedelta(weeks=3),
    )
    invoice2 = Invoice(
        id="INV99902",
        engagement_id="ENG999",
        invoice_number="INV-ENG999-002",
        amount=Decimal("200000"),
        status="sent",
        invoice_date=date.today() - timedelta(weeks=4),
        due_date=date.today() + timedelta(weeks=2),
    )
    db.add_all([invoice1, invoice2])

    for i in range(10):
        week = eng.start_date + timedelta(weeks=i)
        ts1 = Timesheet(
            employee_id="EMP0001",
            engagement_id="ENG999",
            week_start=week,
            billable_hours=Decimal("32.00"),
            non_billable_hours=Decimal("4.00"),
            overtime_hours=Decimal("2.00"),
        )
        ts2 = Timesheet(
            employee_id="EMP0002",
            engagement_id="ENG999",
            week_start=week,
            billable_hours=Decimal("28.00"),
            non_billable_hours=Decimal("6.00"),
            overtime_hours=Decimal("1.00"),
        )
        db.add_all([ts1, ts2])

    for i in range(5):
        ms = Milestone(
            engagement_id="ENG999",
            name=f"Milestone {i+1}",
            planned_date=eng.start_date + timedelta(weeks=(i+1)*2),
            actual_date=eng.start_date + timedelta(weeks=(i+1)*2, days=3),
            status=MilestoneStatus.COMPLETED,
            is_critical_path=i % 2 == 0,
        )
        db.add(ms)

    for i in range(8):
        ticket = Ticket(
            id=f"TKT999{i:03d}",
            engagement_id="ENG999",
            title=f"Ticket {i+1}",
            priority=TicketPriority.HIGH if i < 2 else TicketPriority.MEDIUM,
            status=TicketStatus.OPEN if i < 3 else TicketStatus.RESOLVED,
            reported_date=eng.start_date + timedelta(weeks=i),
            resolved_date=eng.start_date + timedelta(weeks=i, days=5) if i >= 3 else None,
            sla_due_date=eng.start_date + timedelta(weeks=i, days=3),
        )
        db.add(ticket)

    for i in range(10):
        sla = SLAEvent(
            engagement_id="ENG999",
            event_type=SLAEventType.RESOLUTION_TIME,
            is_breach=i < 2,
            metric_value=Decimal(str(20 + i * 2)),
            threshold_value=Decimal("16.00"),
            event_date=eng.start_date + timedelta(weeks=i),
        )
        db.add(sla)

    for i in range(3):
        cr = ChangeRequest(
            id=f"CR999{i:02d}",
            engagement_id="ENG999",
            title=f"Change Request {i+1}",
            impact_category="scope",
            estimated_cost_impact=Decimal("25000"),
            estimated_schedule_impact_days=5,
            status=ChangeRequestStatus.APPROVED if i < 2 else ChangeRequestStatus.REQUESTED,
            requested_date=eng.start_date + timedelta(weeks=i*2),
        )
        db.add(cr)

    for i in range(3):
        fb = ClientFeedback(
            engagement_id="ENG999",
            survey_date=eng.start_date + timedelta(weeks=(i+1)*3),
            overall_satisfaction=8 - i,
            delivery_quality=8 - i,
            communication=8 - i,
            responsiveness=8 - i,
            value_for_money=7 - i,
            nps_score=8 - i,
        )
        db.add(fb)

    db.commit()
    return eng


def test_revenue_calculation(db, sample_data):
    revenue = get_engagement_revenue(db, "ENG999")
    assert revenue == Decimal("400000")


def test_cost_calculation(db, sample_data):
    cost = get_engagement_cost(db, "ENG999")
    expected = (Decimal("32.00") * Decimal("180.00") + Decimal("28.00") * Decimal("220.00")) * 10
    assert cost == expected


def test_budget_variance(db, sample_data):
    planned, actual, variance_pct = get_budget_variance(db, "ENG999")
    assert planned == Decimal("500000")
    assert actual == Decimal("550000")
    assert variance_pct == Decimal("10.00")


def test_schedule_variance(db, sample_data):
    total_delay, avg_critical = get_schedule_variance(db, "ENG999")
    assert total_delay == 15
    # 5 critical milestones, each delayed by 3 days = 15 total critical delay / 5 = 3.0
    assert avg_critical == Decimal("3.0")


def test_ticket_backlog(db, sample_data):
    backlog = get_ticket_backlog(db, "ENG999")
    assert backlog["total"] == 8
    assert backlog["open"] == 3
    assert backlog["high_priority_open"] == 2


def test_sla_breach_rate(db, sample_data):
    rate, breaches, total = get_sla_breach_rate(db, "ENG999")
    assert total == 10
    assert breaches == 2
    assert rate == Decimal("20.00")


def test_change_request_rate(db, sample_data):
    total, approval_rate, cost_impact, schedule_impact = get_change_request_rate(db, "ENG999")
    assert total == 3
    assert approval_rate == Decimal("66.67")
    assert cost_impact == Decimal("75000")


def test_utilization(db, sample_data):
    util = get_employee_utilization(db, "ENG999")
    assert util["total_billable"] == Decimal("600.00")
    assert util["total_non_billable"] == Decimal("100.00")
    assert util["total_overtime"] == Decimal("30.00")
    assert util["avg_utilization"] == Decimal("82.19")


def test_client_satisfaction(db, sample_data):
    sat = get_client_satisfaction(db, "ENG999")
    assert sat["overall_satisfaction"] == Decimal("7.00")
    assert sat["trend"] == "declining"


def test_all_kpis(db, sample_data):
    kpis = calculate_all_kpis(db, "ENG999")
    assert kpis["engagement_id"] == "ENG999"
    assert "financial" in kpis
    assert "delivery" in kpis
    assert "operational" in kpis
    assert "client" in kpis
    assert kpis["financial"]["margin_pct"] > 0