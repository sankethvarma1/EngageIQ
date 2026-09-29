from datetime import date, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Tuple

import pandas as pd
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import (
    Budget,
    ChangeRequest,
    ChangeRequestStatus,
    ClientFeedback,
    Employee,
    Engagement,
    Invoice,
    Milestone,
    MilestoneStatus,
    SLAEvent,
    Ticket,
    TicketPriority,
    TicketStatus,
    Timesheet,
)


def get_engagement_revenue(db: Session, engagement_id: str) -> Decimal:
    result = db.execute(
        select(func.coalesce(func.sum(Invoice.amount), 0)).where(
            Invoice.engagement_id == engagement_id,
            Invoice.status.in_(["paid", "sent"]),
        )
    ).scalar()
    return Decimal(str(result or 0))


def get_engagement_cost(db: Session, engagement_id: str) -> Decimal:
    result = db.execute(
        select(
            func.coalesce(func.sum(Timesheet.billable_hours * Employee.hourly_rate), 0)
        )
        .join(Employee, Timesheet.employee_id == Employee.id)
        .where(Timesheet.engagement_id == engagement_id)
    ).scalar()
    return Decimal(str(result or 0))


def get_budget_variance(db: Session, engagement_id: str) -> Tuple[Decimal, Decimal, Decimal]:
    budgets = db.execute(
        select(Budget.planned_amount, Budget.actual_amount).where(
            Budget.engagement_id == engagement_id
        )
    ).all()

    total_planned = sum(Decimal(str(b[0] or 0)) for b in budgets)
    total_actual = sum(Decimal(str(b[1] or 0)) for b in budgets)
    variance = total_actual - total_planned
    variance_pct = (variance / total_planned * 100) if total_planned > 0 else Decimal("0")

    return total_planned, total_actual, variance_pct.quantize(Decimal("0.01"))


def get_schedule_variance(db: Session, engagement_id: str) -> Tuple[int, Decimal]:
    milestones = db.execute(
        select(Milestone.planned_date, Milestone.actual_date, Milestone.status, Milestone.is_critical_path).where(
            Milestone.engagement_id == engagement_id
        )
    ).all()

    if not milestones:
        return 0, Decimal("0")

    total_delay_days = 0
    critical_delay_days = 0
    critical_count = 0

    for planned, actual, status, is_critical in milestones:
        if actual and planned:
            delay = (actual - planned).days
            if delay > 0:
                total_delay_days += delay
                if is_critical:
                    critical_delay_days += delay
                    critical_count += 1
        elif status == MilestoneStatus.DELAYED and planned and planned < date.today():
            delay = (date.today() - planned).days
            total_delay_days += delay
            if is_critical:
                critical_delay_days += delay
                critical_count += 1

    avg_critical_delay = Decimal(str(critical_delay_days / critical_count)).quantize(Decimal("0.1")) if critical_count > 0 else Decimal("0")
    return total_delay_days, avg_critical_delay


def get_ticket_backlog(db: Session, engagement_id: str) -> Dict[str, int]:
    tickets = db.execute(
        select(Ticket.status, Ticket.priority).where(
            Ticket.engagement_id == engagement_id
        )
    ).all()

    backlog = {
        "total": len(tickets),
        "open": 0,
        "in_progress": 0,
        "resolved": 0,
        "closed": 0,
        "high_priority_open": 0,
        "critical_open": 0,
    }

    for status, priority in tickets:
        if status == TicketStatus.OPEN:
            backlog["open"] += 1
            if priority == TicketPriority.HIGH:
                backlog["high_priority_open"] += 1
            elif priority == TicketPriority.CRITICAL:
                backlog["critical_open"] += 1
        elif status == TicketStatus.IN_PROGRESS:
            backlog["in_progress"] += 1
        elif status == TicketStatus.RESOLVED:
            backlog["resolved"] += 1
        elif status == TicketStatus.CLOSED:
            backlog["closed"] += 1

    return backlog


def get_sla_breach_rate(db: Session, engagement_id: str) -> Tuple[Decimal, int, int]:
    events = db.execute(
        select(SLAEvent.is_breach).where(
            SLAEvent.engagement_id == engagement_id
        )
    ).all()

    if not events:
        return Decimal("0"), 0, 0

    total = len(events)
    breaches = sum(1 for e in events if e[0])
    rate = Decimal(str(breaches / total * 100)).quantize(Decimal("0.01")) if total > 0 else Decimal("0")
    return rate, breaches, total


def get_change_request_rate(db: Session, engagement_id: str) -> Tuple[int, Decimal, Decimal]:
    changes = db.execute(
        select(ChangeRequest.status, ChangeRequest.estimated_cost_impact, ChangeRequest.estimated_schedule_impact_days).where(
            ChangeRequest.engagement_id == engagement_id
        )
    ).all()

    total = len(changes)
    approved = sum(1 for c in changes if c[0] in [ChangeRequestStatus.APPROVED, ChangeRequestStatus.IMPLEMENTED])
    total_cost_impact = sum(Decimal(str(c[1] or 0)) for c in changes)
    total_schedule_impact = sum(c[2] or 0 for c in changes)

    rate = Decimal(str(approved / total * 100)).quantize(Decimal("0.01")) if total > 0 else Decimal("0")
    return total, rate, total_cost_impact, total_schedule_impact


def get_employee_utilization(db: Session, engagement_id: str) -> Dict[str, Decimal]:
    timesheets = db.execute(
        select(
            Timesheet.employee_id,
            func.sum(Timesheet.billable_hours),
            func.sum(Timesheet.non_billable_hours),
            func.sum(Timesheet.overtime_hours),
        )
        .where(Timesheet.engagement_id == engagement_id)
        .group_by(Timesheet.employee_id)
    ).all()

    if not timesheets:
        return {
            "avg_utilization": Decimal("0"),
            "total_billable": Decimal("0"),
            "total_non_billable": Decimal("0"),
            "total_overtime": Decimal("0"),
            "overtime_pct": Decimal("0"),
        }

    total_billable = sum(Decimal(str(t[1] or 0)) for t in timesheets)
    total_non_billable = sum(Decimal(str(t[2] or 0)) for t in timesheets)
    total_overtime = sum(Decimal(str(t[3] or 0)) for t in timesheets)
    total_hours = total_billable + total_non_billable + total_overtime

    avg_util = Decimal(str(total_billable / total_hours * 100)).quantize(Decimal("0.01")) if total_hours > 0 else Decimal("0")
    overtime_pct = Decimal(str(total_overtime / total_hours * 100)).quantize(Decimal("0.01")) if total_hours > 0 else Decimal("0")

    return {
        "avg_utilization": avg_util,
        "total_billable": total_billable.quantize(Decimal("0.01")),
        "total_non_billable": total_non_billable.quantize(Decimal("0.01")),
        "total_overtime": total_overtime.quantize(Decimal("0.01")),
        "overtime_pct": overtime_pct,
    }


def get_client_satisfaction(db: Session, engagement_id: str) -> Dict[str, Decimal]:
    feedback = db.execute(
        select(
            ClientFeedback.overall_satisfaction,
            ClientFeedback.delivery_quality,
            ClientFeedback.communication,
            ClientFeedback.responsiveness,
            ClientFeedback.value_for_money,
            ClientFeedback.nps_score,
        ).where(ClientFeedback.engagement_id == engagement_id)
    ).all()

    if not feedback:
        return {
            "overall_satisfaction": Decimal("0"),
            "delivery_quality": Decimal("0"),
            "communication": Decimal("0"),
            "responsiveness": Decimal("0"),
            "value_for_money": Decimal("0"),
            "nps_score": Decimal("0"),
            "trend": "stable",
        }

    n = len(feedback)
    metrics = {
        "overall_satisfaction": Decimal(str(sum(f[0] for f in feedback) / n)).quantize(Decimal("0.01")),
        "delivery_quality": Decimal(str(sum(f[1] for f in feedback) / n)).quantize(Decimal("0.01")),
        "communication": Decimal(str(sum(f[2] for f in feedback) / n)).quantize(Decimal("0.01")),
        "responsiveness": Decimal(str(sum(f[3] for f in feedback) / n)).quantize(Decimal("0.01")),
        "value_for_money": Decimal(str(sum(f[4] for f in feedback) / n)).quantize(Decimal("0.01")),
        "nps_score": Decimal(str(sum(f[5] for f in feedback) / n)).quantize(Decimal("0.01")),
    }

    if n >= 2:
        recent = feedback[-1][0]
        previous = feedback[-2][0]
        if recent > previous + 0.5:
            metrics["trend"] = "improving"
        elif recent < previous - 0.5:
            metrics["trend"] = "declining"
        else:
            metrics["trend"] = "stable"
    else:
        metrics["trend"] = "stable"

    return metrics


def calculate_all_kpis(db: Session, engagement_id: str) -> Dict:
    revenue = get_engagement_revenue(db, engagement_id)
    cost = get_engagement_cost(db, engagement_id)
    gross_margin = revenue - cost
    margin_pct = (gross_margin / revenue * 100).quantize(Decimal("0.01")) if revenue > 0 else Decimal("0")

    planned_budget, actual_budget, budget_variance_pct = get_budget_variance(db, engagement_id)
    schedule_variance_days, avg_critical_delay = get_schedule_variance(db, engagement_id)
    ticket_backlog = get_ticket_backlog(db, engagement_id)
    sla_breach_rate, sla_breaches, sla_total = get_sla_breach_rate(db, engagement_id)
    cr_total, cr_approval_rate, cr_cost_impact, cr_schedule_impact = get_change_request_rate(db, engagement_id)
    utilization = get_employee_utilization(db, engagement_id)
    satisfaction = get_client_satisfaction(db, engagement_id)

    return {
        "engagement_id": engagement_id,
        "financial": {
            "revenue": revenue,
            "cost": cost,
            "gross_margin": gross_margin,
            "margin_pct": margin_pct,
            "planned_budget": planned_budget,
            "actual_budget": actual_budget,
            "budget_variance_pct": budget_variance_pct,
        },
        "delivery": {
            "schedule_variance_days": schedule_variance_days,
            "avg_critical_path_delay_days": avg_critical_delay,
            "milestone_count": 0,
        },
        "operational": {
            "ticket_backlog": ticket_backlog,
            "sla_breach_rate_pct": sla_breach_rate,
            "sla_breaches": sla_breaches,
            "sla_total_events": sla_total,
            "change_request_count": cr_total,
            "change_request_approval_rate_pct": cr_approval_rate,
            "change_request_cost_impact": cr_cost_impact,
            "change_request_schedule_impact_days": cr_schedule_impact,
            "utilization": utilization,
        },
        "client": satisfaction,
    }


def get_historical_kpis(db: Session, engagement_id: str, weeks: int = 12) -> pd.DataFrame:
    end_date = date.today()
    start_date = end_date - timedelta(weeks=weeks)

    timesheets = db.execute(
        select(
            Timesheet.week_start,
            func.sum(Timesheet.billable_hours),
            func.sum(Timesheet.non_billable_hours),
            func.sum(Timesheet.overtime_hours),
        )
        .where(
            Timesheet.engagement_id == engagement_id,
            Timesheet.week_start >= start_date,
            Timesheet.week_start <= end_date,
        )
        .group_by(Timesheet.week_start)
        .order_by(Timesheet.week_start)
    ).all()

    data = []
    for week, billable, non_billable, overtime in timesheets:
        b = float(billable or 0)
        nb = float(non_billable or 0)
        ot = float(overtime or 0)
        total = b + nb + ot
        util = (b / total * 100) if total > 0 else 0
        data.append({
            "week": week,
            "billable_hours": b,
            "non_billable_hours": nb,
            "overtime_hours": ot,
            "utilization_pct": util,
        })

    return pd.DataFrame(data)