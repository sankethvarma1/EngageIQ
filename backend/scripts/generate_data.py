import random
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import List

from faker import Faker

from app.db.base import Base
from app.db.models import (
    Budget,
    ChangeRequest,
    ChangeRequestStatus,
    Client,
    ClientFeedback,
    Employee,
    EmployeeAssignment,
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
from app.db.session import SessionLocal, engine


fake = Faker()
Faker.seed(42)
random.seed(42)


INDUSTRIES = [
    "Financial Services",
    "Healthcare",
    "Technology",
    "Manufacturing",
    "Retail",
    "Energy",
    "Telecommunications",
    "Public Sector",
]

REGIONS = ["North America", "Europe", "APAC", "LATAM", "MEA"]
ACCOUNT_TIERS = ["strategic", "major", "standard"]

ROLES = [
    ("partner", 500.00),
    ("director", 400.00),
    ("manager", 300.00),
    ("senior_consultant", 220.00),
    ("consultant", 180.00),
    ("analyst", 140.00),
]

DEPARTMENTS = ["Strategy", "Digital", "Operations", "Risk", "Technology", "Finance"]


def generate_clients(n: int = 20) -> List[Client]:
    clients = []
    for i in range(n):
        tier = random.choice(ACCOUNT_TIERS)
        if tier == "strategic":
            revenue = Decimal(random.uniform(50_000_000, 200_000_000)).quantize(Decimal("0.01"))
        elif tier == "major":
            revenue = Decimal(random.uniform(10_000_000, 50_000_000)).quantize(Decimal("0.01"))
        else:
            revenue = Decimal(random.uniform(1_000_000, 10_000_000)).quantize(Decimal("0.01"))

        client = Client(
            id=f"C{i+1:03d}",
            name=fake.company(),
            industry=random.choice(INDUSTRIES),
            region=random.choice(REGIONS),
            account_tier=tier,
            annual_revenue=revenue,
        )
        clients.append(client)
    return clients


def generate_employees(n: int = 50) -> List[Employee]:
    employees = []
    used_emails = set()
    for i in range(n):
        role, rate = random.choice(ROLES)
        first = fake.first_name()
        last = fake.last_name()
        email = f"{first.lower()}.{last.lower()}@northstar.com"
        while email in used_emails:
            email = f"{first.lower()}.{last.lower()}{random.randint(1,99)}@northstar.com"
        used_emails.add(email)

        hire_date = fake.date_between(start_date="-10y", end_date="-6m")

        emp = Employee(
            id=f"EMP{i+1:04d}",
            name=f"{first} {last}",
            email=email,
            role=role,
            department=random.choice(DEPARTMENTS),
            hire_date=hire_date,
            hourly_rate=Decimal(str(rate)),
            is_billable=role not in ["partner"],
        )
        employees.append(emp)
    return employees


def generate_engagements(clients: List[Client], employees: List[Employee], n: int = 40) -> List[Engagement]:
    engagements = []
    managers = [e for e in employees if e.role in ["partner", "director", "manager"]]
    sales_reps = [e for e in employees if e.role in ["partner", "director"]]

    for i in range(n):
        client = random.choice(clients)
        start = fake.date_between(start_date="-2y", end_date="-1m")
        duration_weeks = random.randint(12, 104)
        planned_end = start + timedelta(weeks=duration_weeks)

        # Determine engagement health pattern
        pattern = random.choices(
            ["healthy", "financial_deteriorating", "delayed", "high_change", "high_tickets", "sla_degradation", "declining_sat", "utilization_issues"],
            weights=[0.25, 0.12, 0.12, 0.1, 0.1, 0.1, 0.1, 0.11],
            k=1
        )[0]

        status = EngagementStatus.ACTIVE
        if planned_end < date.today() - timedelta(days=30):
            status = random.choice([EngagementStatus.COMPLETED, EngagementStatus.ON_HOLD])

        eng = Engagement(
            id=f"ENG{i+1:03d}",
            client_id=client.id,
            name=f"{client.name} {random.choice(['Transformation', 'Optimization', 'Migration', 'Assessment', 'Implementation', 'Advisory'])}",
            type=random.choice(list(EngagementType)),
            status=status,
            start_date=start,
            end_date=None if status == EngagementStatus.ACTIVE else planned_end + timedelta(days=random.randint(-30, 60)),
            planned_end_date=planned_end,
            engagement_manager_id=random.choice(managers).id,
            sales_rep_id=random.choice(sales_reps).id,
        )
        # Store pattern for later use in related data generation
        eng._pattern = pattern
        engagements.append(eng)
    return engagements


def generate_assignments(engagements: List[Engagement], employees: List[Employee]) -> List[EmployeeAssignment]:
    assignments = []
    billable_employees = [e for e in employees if e.is_billable]

    for eng in engagements:
        num_assigned = random.randint(3, 12)
        assigned = random.sample(billable_employees, min(num_assigned, len(billable_employees)))

        for emp in assigned:
            alloc = random.randint(25, 100)
            start = max(eng.start_date, emp.hire_date + timedelta(days=30))
            end = None
            if eng.end_date:
                end = min(eng.end_date, eng.planned_end_date + timedelta(days=60))
            elif random.random() < 0.3:
                end = eng.planned_end_date + timedelta(days=random.randint(0, 90))

            role_on_eng = "lead" if alloc > 75 else "core" if alloc > 40 else "support"

            assignment = EmployeeAssignment(
                employee_id=emp.id,
                engagement_id=eng.id,
                role_on_engagement=role_on_eng,
                allocation_pct=alloc,
                start_date=start,
                end_date=end,
            )
            assignments.append(assignment)
    return assignments


def generate_timesheets(engagements: List[Engagement], assignments: List[EmployeeAssignment]) -> List[Timesheet]:
    from app.db.models import Timesheet

    timesheets = []
    assignment_by_eng = {}
    for a in assignments:
        assignment_by_eng.setdefault(a.engagement_id, []).append(a)

    for eng in engagements:
        eng_assignments = assignment_by_eng.get(eng.id, [])
        if not eng_assignments:
            continue

        current_week = eng.start_date
        end_date = eng.end_date or min(eng.planned_end_date, date.today())

        while current_week <= end_date:
            for assignment in eng_assignments:
                if current_week < assignment.start_date:
                    continue
                if assignment.end_date and current_week > assignment.end_date:
                    continue

                alloc_pct = assignment.allocation_pct / 100.0
                base_hours = 40 * alloc_pct

                pattern = getattr(eng, "_pattern", "healthy")

                if pattern == "utilization_issues":
                    billable = base_hours * random.uniform(0.3, 0.6)
                    non_billable = base_hours * random.uniform(0.3, 0.5)
                    overtime = base_hours * random.uniform(0.1, 0.3)
                elif pattern == "delayed":
                    billable = base_hours * random.uniform(0.5, 0.8)
                    non_billable = base_hours * random.uniform(0.2, 0.4)
                    overtime = base_hours * random.uniform(0.05, 0.25)
                elif pattern == "healthy":
                    billable = base_hours * random.uniform(0.7, 0.95)
                    non_billable = base_hours * random.uniform(0.05, 0.2)
                    overtime = base_hours * random.uniform(0, 0.1)
                else:
                    billable = base_hours * random.uniform(0.6, 0.9)
                    non_billable = base_hours * random.uniform(0.1, 0.3)
                    overtime = base_hours * random.uniform(0, 0.15)

                ts = Timesheet(
                    employee_id=assignment.employee_id,
                    engagement_id=eng.id,
                    week_start=current_week,
                    billable_hours=Decimal(str(round(billable, 2))),
                    non_billable_hours=Decimal(str(round(non_billable, 2))),
                    overtime_hours=Decimal(str(round(overtime, 2))),
                )
                timesheets.append(ts)
            current_week += timedelta(weeks=1)
    return timesheets


def generate_budgets(engagements: List[Engagement]) -> List[Budget]:
    budgets = []
    categories = ["labor", "travel", "materials", "subcontractor", "other"]

    for eng in engagements:
        total_budget = Decimal(random.uniform(200_000, 5_000_000)).quantize(Decimal("0.01"))
        pattern = getattr(eng, "_pattern", "healthy")

        for cat in categories:
            if cat == "labor":
                pct = random.uniform(0.55, 0.75)
            elif cat == "subcontractor":
                pct = random.uniform(0.1, 0.25)
            elif cat == "travel":
                pct = random.uniform(0.05, 0.12)
            elif cat == "materials":
                pct = random.uniform(0.03, 0.1)
            else:
                pct = random.uniform(0.01, 0.05)

            planned = (total_budget * Decimal(str(pct))).quantize(Decimal("0.01"))

            if pattern == "financial_deteriorating":
                actual = planned * Decimal(str(random.uniform(1.15, 1.5)))
            elif pattern == "high_change":
                actual = planned * Decimal(str(random.uniform(1.1, 1.4)))
            elif pattern == "delayed":
                actual = planned * Decimal(str(random.uniform(1.05, 1.3)))
            else:
                actual = planned * Decimal(str(random.uniform(0.85, 1.1)))

            actual = actual.quantize(Decimal("0.01"))

            budget = Budget(
                engagement_id=eng.id,
                category=cat,
                planned_amount=planned,
                actual_amount=actual,
                period_start=eng.start_date,
                period_end=eng.planned_end_date,
            )
            budgets.append(budget)
    return budgets


def generate_invoices(engagements: List[Engagement]) -> List[Invoice]:
    invoices = []

    for eng in engagements:
        num_invoices = random.randint(3, 12)
        total_budget = sum(
            Decimal(str(random.uniform(200_000, 5_000_000)))
            for _ in range(5)
        ) / 5

        pattern = getattr(eng, "_pattern", "healthy")

        for i in range(num_invoices):
            inv_date = eng.start_date + timedelta(weeks=random.randint(4 * i, 4 * (i + 1)))
            if inv_date > date.today():
                inv_date = date.today() - timedelta(days=random.randint(1, 30))

            amount = (total_budget / num_invoices * Decimal(str(random.uniform(0.7, 1.3)))).quantize(Decimal("0.01"))

            if pattern == "financial_deteriorating" and i > num_invoices // 2:
                status = random.choice(["overdue", "sent"])
            elif eng.status == EngagementStatus.COMPLETED:
                status = "paid"
            else:
                status = random.choice(["paid", "sent", "overdue"])

            due = inv_date + timedelta(days=30)
            paid = None
            if status == "paid":
                paid = inv_date + timedelta(days=random.randint(5, 45))

            invoice = Invoice(
                id=f"INV{eng.id[3:]}{i+1:02d}",
                engagement_id=eng.id,
                invoice_number=f"INV-{eng.id}-{i+1:03d}",
                amount=amount,
                status=status,
                invoice_date=inv_date,
                due_date=due,
                paid_date=paid,
            )
            invoices.append(invoice)
    return invoices


def generate_milestones(engagements: List[Engagement]) -> List[Milestone]:
    milestones = []

    for eng in engagements:
        num_milestones = random.randint(5, 15)
        pattern = getattr(eng, "_pattern", "healthy")

        for i in range(num_milestones):
            planned = eng.start_date + timedelta(weeks=random.randint(i * 4, (i + 1) * 4))
            if planned > eng.planned_end_date:
                planned = eng.planned_end_date - timedelta(days=random.randint(1, 30))

            is_critical = i % 3 == 0

            if pattern == "delayed":
                delay_weeks = random.randint(2, 12)
                actual = planned + timedelta(weeks=delay_weeks)
                if actual > date.today():
                    actual = None
                    status = MilestoneStatus.DELAYED
                else:
                    status = MilestoneStatus.COMPLETED
            elif pattern == "high_change":
                if random.random() < 0.3:
                    actual = planned + timedelta(weeks=random.randint(1, 8))
                    status = MilestoneStatus.DELAYED
                else:
                    actual = planned + timedelta(days=random.randint(-5, 5))
                    status = MilestoneStatus.COMPLETED
            else:
                actual = planned + timedelta(days=random.randint(-10, 10))
                status = MilestoneStatus.COMPLETED if actual <= date.today() else MilestoneStatus.IN_PROGRESS

            ms = Milestone(
                engagement_id=eng.id,
                name=f"Milestone {i+1}: {fake.bs().title()}",
                description=fake.sentence(),
                planned_date=planned,
                actual_date=actual,
                status=status,
                is_critical_path=is_critical,
            )
            milestones.append(ms)
    return milestones


def generate_tickets(engagements: List[Engagement], employees: List[Employee]) -> List[Ticket]:
    tickets = []

    for eng in engagements:
        pattern = getattr(eng, "_pattern", "healthy")

        if pattern == "high_tickets":
            base_count = random.randint(40, 80)
        elif pattern == "sla_degradation":
            base_count = random.randint(25, 50)
        else:
            base_count = random.randint(5, 25)

        for i in range(base_count):
            reported = eng.start_date + timedelta(days=random.randint(0, max(1, (eng.planned_end_date - eng.start_date).days)))

            if pattern == "high_tickets":
                priority = random.choices(
                    [TicketPriority.LOW, TicketPriority.MEDIUM, TicketPriority.HIGH, TicketPriority.CRITICAL],
                    weights=[0.1, 0.2, 0.4, 0.3],
                    k=1
                )[0]
            else:
                priority = random.choices(
                    [TicketPriority.LOW, TicketPriority.MEDIUM, TicketPriority.HIGH, TicketPriority.CRITICAL],
                    weights=[0.3, 0.4, 0.2, 0.1],
                    k=1
                )[0]

            if priority in [TicketPriority.HIGH, TicketPriority.CRITICAL]:
                status = random.choices(
                    [TicketStatus.OPEN, TicketStatus.IN_PROGRESS, TicketStatus.RESOLVED],
                    weights=[0.2, 0.3, 0.5],
                    k=1
                )[0]
            else:
                status = random.choices(
                    [TicketStatus.OPEN, TicketStatus.IN_PROGRESS, TicketStatus.RESOLVED, TicketStatus.CLOSED],
                    weights=[0.15, 0.2, 0.3, 0.35],
                    k=1
                )[0]

            resolved = None
            sla_due = None
            if status in [TicketStatus.RESOLVED, TicketStatus.CLOSED]:
                resolved = reported + timedelta(days=random.randint(1, 30))
                sla_due = reported + timedelta(days=random.randint(2, 14))

            ticket = Ticket(
                id=f"TKT{eng.id[3:]}{i+1:04d}",
                engagement_id=eng.id,
                title=fake.sentence(nb_words=6),
                description=fake.paragraph(),
                priority=priority,
                status=status,
                assignee_id=random.choice(employees).id if random.random() > 0.1 else None,
                reported_date=reported,
                resolved_date=resolved,
                sla_due_date=sla_due,
            )
            tickets.append(ticket)
    return tickets


def generate_sla_events(engagements: List[Engagement], tickets: List[Ticket]) -> List[SLAEvent]:
    events = []
    tickets_by_eng = {}
    for t in tickets:
        tickets_by_eng.setdefault(t.engagement_id, []).append(t)

    for eng in engagements:
        eng_tickets = tickets_by_eng.get(eng.id, [])
        pattern = getattr(eng, "_pattern", "healthy")

        for ticket in eng_tickets:
            if ticket.sla_due_date and ticket.resolved_date:
                is_breach = ticket.resolved_date > ticket.sla_due_date
                if pattern == "sla_degradation":
                    is_breach = is_breach or random.random() < 0.4

                metric = (ticket.resolved_date - ticket.reported_date).days * 8
                threshold = (ticket.sla_due_date - ticket.reported_date).days * 8

                event = SLAEvent(
                    engagement_id=eng.id,
                    event_type=SLAEventType.RESOLUTION_TIME,
                    is_breach=is_breach,
                    metric_value=Decimal(str(metric)),
                    threshold_value=Decimal(str(threshold)),
                    event_date=ticket.resolved_date,
                    description=f"Ticket {ticket.id} resolution",
                )
                events.append(event)

        # Add some additional SLA events
        num_extra = random.randint(5, 20)
        for _ in range(num_extra):
            event_date = eng.start_date + timedelta(days=random.randint(0, max(1, (min(eng.end_date or date.today(), eng.planned_end_date) - eng.start_date).days)))
            event_type = random.choice(list(SLAEventType))

            if pattern == "sla_degradation":
                is_breach = random.random() < 0.35
            else:
                is_breach = random.random() < 0.08

            metric = Decimal(str(random.uniform(1, 48)))
            threshold = Decimal(str(random.uniform(4, 24)))

            event = SLAEvent(
                engagement_id=eng.id,
                event_type=event_type,
                is_breach=is_breach,
                metric_value=metric,
                threshold_value=threshold,
                event_date=event_date,
                description=fake.sentence(),
            )
            events.append(event)
    return events


def generate_change_requests(engagements: List[Engagement]) -> List[ChangeRequest]:
    changes = []

    for eng in engagements:
        pattern = getattr(eng, "_pattern", "healthy")

        if pattern == "high_change":
            count = random.randint(15, 35)
        elif pattern == "delayed":
            count = random.randint(8, 20)
        else:
            count = random.randint(0, 8)

        for i in range(count):
            requested = eng.start_date + timedelta(days=random.randint(0, max(1, (eng.planned_end_date - eng.start_date).days)))

            if pattern == "high_change":
                status = random.choices(
                    [ChangeRequestStatus.REQUESTED, ChangeRequestStatus.UNDER_REVIEW, ChangeRequestStatus.APPROVED, ChangeRequestStatus.IMPLEMENTED],
                    weights=[0.1, 0.15, 0.35, 0.4],
                    k=1
                )[0]
            else:
                status = random.choices(
                    [ChangeRequestStatus.REQUESTED, ChangeRequestStatus.UNDER_REVIEW, ChangeRequestStatus.APPROVED, ChangeRequestStatus.REJECTED, ChangeRequestStatus.IMPLEMENTED],
                    weights=[0.15, 0.1, 0.25, 0.2, 0.3],
                    k=1
                )[0]

            decided = None
            if status in [ChangeRequestStatus.APPROVED, ChangeRequestStatus.REJECTED, ChangeRequestStatus.IMPLEMENTED]:
                decided = requested + timedelta(days=random.randint(5, 30))

            cost_impact = Decimal(str(random.uniform(5000, 200000))).quantize(Decimal("0.01"))
            schedule_impact = random.randint(0, 60)

            cr = ChangeRequest(
                id=f"CR{eng.id[3:]}{i+1:03d}",
                engagement_id=eng.id,
                title=fake.sentence(nb_words=5),
                description=fake.paragraph(),
                impact_category=random.choice(["scope", "schedule", "budget", "quality"]),
                estimated_cost_impact=cost_impact,
                estimated_schedule_impact_days=schedule_impact,
                status=status,
                requested_date=requested,
                decided_date=decided,
            )
            changes.append(cr)
    return changes


def generate_client_feedback(engagements: List[Engagement]) -> List[ClientFeedback]:
    feedback = []

    for eng in engagements:
        pattern = getattr(eng, "_pattern", "healthy")

        num_surveys = random.randint(2, 6)
        for i in range(num_surveys):
            survey_date = eng.start_date + timedelta(weeks=random.randint(4 * (i + 1), 4 * (i + 2)))
            if survey_date > date.today():
                survey_date = date.today() - timedelta(days=random.randint(1, 30))

            if pattern == "declining_sat":
                base = 8 - i * 1.2
                noise = random.uniform(-1, 1)
            elif pattern == "high_tickets" or pattern == "sla_degradation":
                base = random.uniform(4, 6.5)
                noise = random.uniform(-1, 1)
            elif pattern == "financial_deteriorating":
                base = random.uniform(5, 7)
                noise = random.uniform(-1, 1)
            else:
                base = random.uniform(7, 9)
                noise = random.uniform(-1, 1)

            overall = max(1, min(10, int(base + noise)))

            fb = ClientFeedback(
                engagement_id=eng.id,
                survey_date=survey_date,
                overall_satisfaction=overall,
                delivery_quality=max(1, min(10, overall + random.randint(-2, 1))),
                communication=max(1, min(10, overall + random.randint(-1, 2))),
                responsiveness=max(1, min(10, overall + random.randint(-2, 1))),
                value_for_money=max(1, min(10, overall + random.randint(-2, 2))),
                nps_score=max(0, min(10, overall + random.randint(-3, 2))),
                comments=fake.paragraph() if random.random() > 0.5 else None,
            )
            feedback.append(fb)
    return feedback


def main():
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        print("Generating clients...")
        clients = generate_clients(20)
        db.add_all(clients)
        db.flush()
        print(f"Created {len(clients)} clients")

        print("Generating employees...")
        employees = generate_employees(50)
        db.add_all(employees)
        db.flush()
        print(f"Created {len(employees)} employees")

        print("Generating engagements...")
        engagements = generate_engagements(clients, employees, 40)
        db.add_all(engagements)
        db.flush()
        print(f"Created {len(engagements)} engagements")

        print("Generating assignments...")
        assignments = generate_assignments(engagements, employees)
        db.add_all(assignments)
        db.flush()
        print(f"Created {len(assignments)} assignments")

        print("Generating timesheets...")
        timesheets = generate_timesheets(engagements, assignments)
        db.add_all(timesheets)
        db.flush()
        print(f"Created {len(timesheets)} timesheet entries")

        print("Generating budgets...")
        budgets = generate_budgets(engagements)
        db.add_all(budgets)
        db.flush()
        print(f"Created {len(budgets)} budget entries")

        print("Generating invoices...")
        invoices = generate_invoices(engagements)
        db.add_all(invoices)
        db.flush()
        print(f"Created {len(invoices)} invoices")

        print("Generating milestones...")
        milestones = generate_milestones(engagements)
        db.add_all(milestones)
        db.flush()
        print(f"Created {len(milestones)} milestones")

        print("Generating tickets...")
        tickets = generate_tickets(engagements, employees)
        db.add_all(tickets)
        db.flush()
        print(f"Created {len(tickets)} tickets")

        print("Generating SLA events...")
        sla_events = generate_sla_events(engagements, tickets)
        db.add_all(sla_events)
        db.flush()
        print(f"Created {len(sla_events)} SLA events")

        print("Generating change requests...")
        changes = generate_change_requests(engagements)
        db.add_all(changes)
        db.flush()
        print(f"Created {len(changes)} change requests")

        print("Generating client feedback...")
        feedback = generate_client_feedback(engagements)
        db.add_all(feedback)
        db.flush()
        print(f"Created {len(feedback)} feedback entries")

        db.commit()
        print("Data generation complete!")

    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()