from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from app.analytics.kpis import calculate_all_kpis, get_historical_kpis
from app.db.session import get_db_context


@dataclass
class Anomaly:
    engagement_id: str
    metric: str
    value: float
    expected_range: tuple
    severity: str
    description: str
    detected_at: date


def detect_utilization_anomalies(df: pd.DataFrame, engagement_id: str) -> List[Anomaly]:
    anomalies = []
    if len(df) < 4:
        return anomalies

    util_series = df["utilization_pct"].values
    mean_util = np.mean(util_series)
    std_util = np.std(util_series)

    if std_util == 0:
        return anomalies

    for i, row in df.iterrows():
        z_score = abs(row["utilization_pct"] - mean_util) / std_util
        if z_score > 2.5:
            severity = "high" if z_score > 3.5 else "medium"
            anomalies.append(Anomaly(
                engagement_id=engagement_id,
                metric="utilization",
                value=row["utilization_pct"],
                expected_range=(mean_util - 2*std_util, mean_util + 2*std_util),
                severity=severity,
                description=f"Utilization {row['utilization_pct']:.1f}% deviates significantly from average {mean_util:.1f}%",
                detected_at=row["week"],
            ))
    return anomalies


def detect_margin_deterioration(kpis: Dict, engagement_id: str, db) -> List[Anomaly]:
    anomalies = []
    margin = float(kpis["financial"]["margin_pct"])

    if margin < 10:
        anomalies.append(Anomaly(
            engagement_id=engagement_id,
            metric="margin",
            value=margin,
            expected_range=(15, 50),
            severity="high" if margin < 0 else "medium",
            description=f"Margin at {margin:.1f}% - below healthy threshold of 15%",
            detected_at=date.today(),
        ))
    elif margin < 20:
        anomalies.append(Anomaly(
            engagement_id=engagement_id,
            metric="margin",
            value=margin,
            expected_range=(20, 50),
            severity="low",
            description=f"Margin at {margin:.1f}% - approaching caution zone",
            detected_at=date.today(),
        ))

    budget_var = float(kpis["financial"]["budget_variance_pct"])
    if budget_var > 20:
        anomalies.append(Anomaly(
            engagement_id=engagement_id,
            metric="budget_variance",
            value=budget_var,
            expected_range=(-10, 10),
            severity="high" if budget_var > 35 else "medium",
            description=f"Budget variance at {budget_var:.1f}% - significant overrun",
            detected_at=date.today(),
        ))

    return anomalies


def detect_ticket_anomalies(kpis: Dict, engagement_id: str) -> List[Anomaly]:
    anomalies = []
    backlog = kpis["operational"]["ticket_backlog"]
    total_tickets = backlog["total"]
    high_priority_open = backlog["high_priority_open"]
    critical_open = backlog["critical_open"]

    if total_tickets > 50:
        severity = "high" if total_tickets > 80 else "medium"
        anomalies.append(Anomaly(
            engagement_id=engagement_id,
            metric="ticket_volume",
            value=total_tickets,
            expected_range=(0, 30),
            severity=severity,
            description=f"High ticket volume: {total_tickets} total tickets",
            detected_at=date.today(),
        ))

    if critical_open > 5:
        anomalies.append(Anomaly(
            engagement_id=engagement_id,
            metric="critical_tickets",
            value=critical_open,
            expected_range=(0, 2),
            severity="high",
            description=f"{critical_open} critical tickets open - immediate attention needed",
            detected_at=date.today(),
        ))
    elif critical_open > 2 or high_priority_open > 10:
        anomalies.append(Anomaly(
            engagement_id=engagement_id,
            metric="priority_tickets",
            value=high_priority_open + critical_open,
            expected_range=(0, 8),
            severity="medium",
            description=f"Elevated high-priority tickets: {high_priority_open} high, {critical_open} critical",
            detected_at=date.today(),
        ))

    return anomalies


def detect_sla_anomalies(kpis: Dict, engagement_id: str) -> List[Anomaly]:
    anomalies = []
    breach_rate = float(kpis["operational"]["sla_breach_rate_pct"])

    if breach_rate > 20:
        anomalies.append(Anomaly(
            engagement_id=engagement_id,
            metric="sla_breach_rate",
            value=breach_rate,
            expected_range=(0, 10),
            severity="high" if breach_rate > 35 else "medium",
            description=f"SLA breach rate at {breach_rate:.1f}% - well above acceptable threshold",
            detected_at=date.today(),
        ))
    elif breach_rate > 10:
        anomalies.append(Anomaly(
            engagement_id=engagement_id,
            metric="sla_breach_rate",
            value=breach_rate,
            expected_range=(0, 10),
            severity="low",
            description=f"SLA breach rate at {breach_rate:.1f}% - trending upward",
            detected_at=date.today(),
        ))

    return anomalies


def detect_change_request_anomalies(kpis: Dict, engagement_id: str) -> List[Anomaly]:
    anomalies = []
    cr_count = kpis["operational"]["change_request_count"]
    cr_cost = float(kpis["operational"]["change_request_cost_impact"])
    cr_schedule = kpis["operational"]["change_request_schedule_impact_days"]

    if cr_count > 15:
        anomalies.append(Anomaly(
            engagement_id=engagement_id,
            metric="change_request_volume",
            value=cr_count,
            expected_range=(0, 10),
            severity="medium",
            description=f"High change request volume: {cr_count} requests",
            detected_at=date.today(),
        ))

    if cr_cost > 100000:
        anomalies.append(Anomaly(
            engagement_id=engagement_id,
            metric="change_request_cost",
            value=cr_cost,
            expected_range=(0, 50000),
            severity="medium",
            description=f"Change requests adding ${cr_cost:,.0f} in estimated cost impact",
            detected_at=date.today(),
        ))

    if cr_schedule > 30:
        anomalies.append(Anomaly(
            engagement_id=engagement_id,
            metric="change_request_schedule",
            value=cr_schedule,
            expected_range=(0, 15),
            severity="medium" if cr_schedule < 60 else "high",
            description=f"Change requests adding {cr_schedule} days to schedule",
            detected_at=date.today(),
        ))

    return anomalies


def detect_satisfaction_anomalies(kpis: Dict, engagement_id: str) -> List[Anomaly]:
    anomalies = []
    sat = kpis["client"]
    overall = float(sat["overall_satisfaction"])
    trend = sat.get("trend", "stable")

    if overall < 5:
        anomalies.append(Anomaly(
            engagement_id=engagement_id,
            metric="client_satisfaction",
            value=overall,
            expected_range=(6, 10),
            severity="high",
            description=f"Client satisfaction critically low at {overall:.1f}/10",
            detected_at=date.today(),
        ))
    elif overall < 6.5:
        anomalies.append(Anomaly(
            engagement_id=engagement_id,
            metric="client_satisfaction",
            value=overall,
            expected_range=(7, 10),
            severity="medium",
            description=f"Client satisfaction below target at {overall:.1f}/10",
            detected_at=date.today(),
        ))

    if trend == "declining":
        anomalies.append(Anomaly(
            engagement_id=engagement_id,
            metric="satisfaction_trend",
            value=overall,
            expected_range=(0, 10),
            severity="medium",
            description="Client satisfaction declining over recent surveys",
            detected_at=date.today(),
        ))

    return anomalies


def detect_all_anomalies(engagement_id: str, db) -> List[Anomaly]:
    kpis = calculate_all_kpis(db, engagement_id)
    hist_df = get_historical_kpis(db, engagement_id, weeks=12)

    all_anomalies = []
    all_anomalies.extend(detect_margin_deterioration(kpis, engagement_id, db))
    all_anomalies.extend(detect_ticket_anomalies(kpis, engagement_id))
    all_anomalies.extend(detect_sla_anomalies(kpis, engagement_id))
    all_anomalies.extend(detect_change_request_anomalies(kpis, engagement_id))
    all_anomalies.extend(detect_satisfaction_anomalies(kpis, engagement_id))
    all_anomalies.extend(detect_utilization_anomalies(hist_df, engagement_id))

    return sorted(all_anomalies, key=lambda x: {"high": 0, "medium": 1, "low": 2}[x.severity])