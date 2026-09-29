import enum
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class EngagementStatus(str, enum.Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    ON_HOLD = "on_hold"
    CANCELLED = "cancelled"


class EngagementType(str, enum.Enum):
    CONSULTING = "consulting"
    IMPLEMENTATION = "implementation"
    ADVISORY = "advisory"
    MANAGED_SERVICES = "managed_services"


class TicketPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TicketStatus(str, enum.Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


class MilestoneStatus(str, enum.Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    DELAYED = "delayed"
    BLOCKED = "blocked"


class ChangeRequestStatus(str, enum.Enum):
    REQUESTED = "requested"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    IMPLEMENTED = "implemented"


class SLAEventType(str, enum.Enum):
    RESPONSE_TIME = "response_time"
    RESOLUTION_TIME = "resolution_time"
    AVAILABILITY = "availability"
    PERFORMANCE = "performance"


class Client(Base):
    __tablename__ = "clients"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    industry: Mapped[str] = mapped_column(String(100), nullable=False)
    region: Mapped[str] = mapped_column(String(50), nullable=False)
    account_tier: Mapped[str] = mapped_column(String(20), nullable=False)
    annual_revenue: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    engagements: Mapped[list["Engagement"]] = relationship(back_populates="client")


class Engagement(Base):
    __tablename__ = "engagements"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    client_id: Mapped[str] = mapped_column(String(20), ForeignKey("clients.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    type: Mapped[EngagementType] = mapped_column(Enum(EngagementType), nullable=False)
    status: Mapped[EngagementStatus] = mapped_column(Enum(EngagementStatus), nullable=False, default=EngagementStatus.ACTIVE)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    planned_end_date: Mapped[date] = mapped_column(Date, nullable=False)
    engagement_manager_id: Mapped[str] = mapped_column(String(20), ForeignKey("employees.id"), nullable=False)
    sales_rep_id: Mapped[str] = mapped_column(String(20), ForeignKey("employees.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    client: Mapped["Client"] = relationship(back_populates="engagements")
    engagement_manager: Mapped["Employee"] = relationship(foreign_keys=[engagement_manager_id], back_populates="managed_engagements")
    sales_rep: Mapped["Employee"] = relationship(foreign_keys=[sales_rep_id], back_populates="sold_engagements")
    budgets: Mapped[list["Budget"]] = relationship(back_populates="engagement")
    invoices: Mapped[list["Invoice"]] = relationship(back_populates="engagement")
    milestones: Mapped[list["Milestone"]] = relationship(back_populates="engagement")
    tickets: Mapped[list["Ticket"]] = relationship(back_populates="engagement")
    sla_events: Mapped[list["SLAEvent"]] = relationship(back_populates="engagement")
    change_requests: Mapped[list["ChangeRequest"]] = relationship(back_populates="engagement")
    client_feedback: Mapped[list["ClientFeedback"]] = relationship(back_populates="engagement")
    employee_assignments: Mapped[list["EmployeeAssignment"]] = relationship(back_populates="engagement")

    __table_args__ = (
        Index("ix_engagements_client_id", "client_id"),
        Index("ix_engagements_status", "status"),
    )


class Employee(Base):
    __tablename__ = "employees"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(150), nullable=False, unique=True)
    role: Mapped[str] = mapped_column(String(50), nullable=False)
    department: Mapped[str] = mapped_column(String(50), nullable=False)
    hire_date: Mapped[date] = mapped_column(Date, nullable=False)
    hourly_rate: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    is_billable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    managed_engagements: Mapped[list["Engagement"]] = relationship(foreign_keys="Engagement.engagement_manager_id", back_populates="engagement_manager")
    sold_engagements: Mapped[list["Engagement"]] = relationship(foreign_keys="Engagement.sales_rep_id", back_populates="sales_rep")
    assignments: Mapped[list["EmployeeAssignment"]] = relationship(back_populates="employee")
    timesheets: Mapped[list["Timesheet"]] = relationship(back_populates="employee")


class EmployeeAssignment(Base):
    __tablename__ = "employee_assignments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    employee_id: Mapped[str] = mapped_column(String(20), ForeignKey("employees.id"), nullable=False)
    engagement_id: Mapped[str] = mapped_column(String(20), ForeignKey("engagements.id"), nullable=False)
    role_on_engagement: Mapped[str] = mapped_column(String(50), nullable=False)
    allocation_pct: Mapped[int] = mapped_column(Integer, nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    employee: Mapped["Employee"] = relationship(back_populates="assignments")
    engagement: Mapped["Engagement"] = relationship(back_populates="employee_assignments")

    __table_args__ = (
        UniqueConstraint("employee_id", "engagement_id", name="uq_employee_engagement"),
        Index("ix_assignments_engagement", "engagement_id"),
    )


class Timesheet(Base):
    __tablename__ = "timesheets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    employee_id: Mapped[str] = mapped_column(String(20), ForeignKey("employees.id"), nullable=False)
    engagement_id: Mapped[str] = mapped_column(String(20), ForeignKey("engagements.id"), nullable=False)
    week_start: Mapped[date] = mapped_column(Date, nullable=False)
    billable_hours: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False, default=0)
    non_billable_hours: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False, default=0)
    overtime_hours: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    employee: Mapped["Employee"] = relationship(back_populates="timesheets")
    engagement: Mapped["Engagement"] = relationship()

    __table_args__ = (
        UniqueConstraint("employee_id", "engagement_id", "week_start", name="uq_timesheet"),
        Index("ix_timesheets_engagement_week", "engagement_id", "week_start"),
    )


class Budget(Base):
    __tablename__ = "budgets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    engagement_id: Mapped[str] = mapped_column(String(20), ForeignKey("engagements.id"), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    planned_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    actual_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, default=0)
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    engagement: Mapped["Engagement"] = relationship(back_populates="budgets")

    __table_args__ = (
        Index("ix_budgets_engagement", "engagement_id"),
    )


class Invoice(Base):
    __tablename__ = "invoices"

    id: Mapped[str] = mapped_column(String(30), primary_key=True)
    engagement_id: Mapped[str] = mapped_column(String(20), ForeignKey("engagements.id"), nullable=False)
    invoice_number: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    invoice_date: Mapped[date] = mapped_column(Date, nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    paid_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    engagement: Mapped["Engagement"] = relationship(back_populates="invoices")

    __table_args__ = (
        Index("ix_invoices_engagement", "engagement_id"),
        Index("ix_invoices_status", "status"),
    )


class Milestone(Base):
    __tablename__ = "milestones"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    engagement_id: Mapped[str] = mapped_column(String(20), ForeignKey("engagements.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    planned_date: Mapped[date] = mapped_column(Date, nullable=False)
    actual_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    status: Mapped[MilestoneStatus] = mapped_column(Enum(MilestoneStatus), nullable=False, default=MilestoneStatus.NOT_STARTED)
    is_critical_path: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    engagement: Mapped["Engagement"] = relationship(back_populates="milestones")

    __table_args__ = (
        Index("ix_milestones_engagement", "engagement_id"),
    )


class Ticket(Base):
    __tablename__ = "tickets"

    id: Mapped[str] = mapped_column(String(30), primary_key=True)
    engagement_id: Mapped[str] = mapped_column(String(20), ForeignKey("engagements.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    priority: Mapped[TicketPriority] = mapped_column(Enum(TicketPriority), nullable=False)
    status: Mapped[TicketStatus] = mapped_column(Enum(TicketStatus), nullable=False, default=TicketStatus.OPEN)
    assignee_id: Mapped[Optional[str]] = mapped_column(String(20), ForeignKey("employees.id"), nullable=True)
    reported_date: Mapped[date] = mapped_column(Date, nullable=False)
    resolved_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    sla_due_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    engagement: Mapped["Engagement"] = relationship(back_populates="tickets")
    assignee: Mapped[Optional["Employee"]] = relationship()

    __table_args__ = (
        Index("ix_tickets_engagement", "engagement_id"),
        Index("ix_tickets_status", "status"),
        Index("ix_tickets_priority", "priority"),
    )


class SLAEvent(Base):
    __tablename__ = "sla_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    engagement_id: Mapped[str] = mapped_column(String(20), ForeignKey("engagements.id"), nullable=False)
    event_type: Mapped[SLAEventType] = mapped_column(Enum(SLAEventType), nullable=False)
    is_breach: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    metric_value: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    threshold_value: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    event_date: Mapped[date] = mapped_column(Date, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    engagement: Mapped["Engagement"] = relationship(back_populates="sla_events")

    __table_args__ = (
        Index("ix_sla_events_engagement", "engagement_id"),
        Index("ix_sla_events_date", "event_date"),
    )


class ChangeRequest(Base):
    __tablename__ = "change_requests"

    id: Mapped[str] = mapped_column(String(30), primary_key=True)
    engagement_id: Mapped[str] = mapped_column(String(20), ForeignKey("engagements.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    impact_category: Mapped[str] = mapped_column(String(50), nullable=False)
    estimated_cost_impact: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, default=0)
    estimated_schedule_impact_days: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[ChangeRequestStatus] = mapped_column(Enum(ChangeRequestStatus), nullable=False, default=ChangeRequestStatus.REQUESTED)
    requested_date: Mapped[date] = mapped_column(Date, nullable=False)
    decided_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    engagement: Mapped["Engagement"] = relationship(back_populates="change_requests")

    __table_args__ = (
        Index("ix_change_requests_engagement", "engagement_id"),
        Index("ix_change_requests_status", "status"),
    )


class ClientFeedback(Base):
    __tablename__ = "client_feedback"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    engagement_id: Mapped[str] = mapped_column(String(20), ForeignKey("engagements.id"), nullable=False)
    survey_date: Mapped[date] = mapped_column(Date, nullable=False)
    overall_satisfaction: Mapped[int] = mapped_column(Integer, nullable=False)
    delivery_quality: Mapped[int] = mapped_column(Integer, nullable=False)
    communication: Mapped[int] = mapped_column(Integer, nullable=False)
    responsiveness: Mapped[int] = mapped_column(Integer, nullable=False)
    value_for_money: Mapped[int] = mapped_column(Integer, nullable=False)
    nps_score: Mapped[int] = mapped_column(Integer, nullable=False)
    comments: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    engagement: Mapped["Engagement"] = relationship(back_populates="client_feedback")

    __table_args__ = (
        Index("ix_client_feedback_engagement", "engagement_id"),
        Index("ix_client_feedback_date", "survey_date"),
    )