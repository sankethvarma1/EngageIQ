from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Any, Dict, List, Optional

from app.analytics.anomalies import detect_all_anomalies
from app.analytics.kpis import calculate_all_kpis
from app.ml.risk_model import get_shap_explanation, predict_risk
from app.rag.knowledge_base import retrieve_evidence
from app.db.session import get_db_context


@dataclass
class ToolResult:
    success: bool
    data: Any
    error: Optional[str] = None


def query_engagement(engagement_id: str) -> ToolResult:
    try:
        with get_db_context() as db:
            from app.db.models import Engagement
            eng = db.query(Engagement).filter(Engagement.id == engagement_id).first()
            if not eng:
                return ToolResult(success=False, data=None, error=f"Engagement {engagement_id} not found")

            return ToolResult(success=True, data={
                "id": eng.id,
                "client_id": eng.client_id,
                "name": eng.name,
                "type": eng.type.value,
                "status": eng.status.value,
                "start_date": str(eng.start_date),
                "end_date": str(eng.end_date) if eng.end_date else None,
                "planned_end_date": str(eng.planned_end_date),
                "engagement_manager_id": eng.engagement_manager_id,
            })
    except Exception as e:
        return ToolResult(success=False, data=None, error=str(e))


def calculate_kpis(engagement_id: str) -> ToolResult:
    try:
        with get_db_context() as db:
            kpis = calculate_all_kpis(db, engagement_id)
            # Convert Decimal to float for JSON serialization
            def convert(obj):
                if isinstance(obj, Decimal):
                    return float(obj)
                elif isinstance(obj, dict):
                    return {k: convert(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [convert(v) for v in obj]
                elif isinstance(obj, date):
                    return str(obj)
                return obj

            return ToolResult(success=True, data=convert(kpis))
    except Exception as e:
        return ToolResult(success=False, data=None, error=str(e))


def calculate_risk(engagement_id: str) -> ToolResult:
    try:
        with get_db_context() as db:
            risk = predict_risk(db, engagement_id)
            return ToolResult(success=True, data={
                "engagement_id": engagement_id,
                "composite_score": risk.composite_score,
                "risk_level": risk.risk_level,
                "financial_risk": risk.financial_risk,
                "delivery_risk": risk.delivery_risk,
                "operational_risk": risk.operational_risk,
                "client_risk": risk.client_risk,
                "data_quality_risk": risk.data_quality_risk,
            })
    except Exception as e:
        return ToolResult(success=False, data=None, error=str(e))


def get_shap_explanation_tool(engagement_id: str) -> ToolResult:
    try:
        with get_db_context() as db:
            explanation = get_shap_explanation(db, engagement_id)
            return ToolResult(success=True, data=explanation)
    except Exception as e:
        return ToolResult(success=False, data=None, error=str(e))


def detect_anomalies_tool(engagement_id: str) -> ToolResult:
    try:
        with get_db_context() as db:
            anomalies = detect_all_anomalies(engagement_id, db)
        return ToolResult(success=True, data=[{
            "metric": a.metric,
            "value": a.value,
            "expected_range": a.expected_range,
            "severity": a.severity,
            "description": a.description,
            "detected_at": str(a.detected_at),
        } for a in anomalies])
    except Exception as e:
        return ToolResult(success=False, data=None, error=str(e))


def retrieve_evidence_tool(query: str, top_k: int = 5) -> ToolResult:
    try:
        chunks = retrieve_evidence(query, top_k)
        return ToolResult(success=True, data=[{
            "doc_id": c.doc_id,
            "title": c.title,
            "section": c.section,
            "content": c.content[:500],
            "source": c.source,
        } for c in chunks])
    except Exception as e:
        return ToolResult(success=False, data=None, error=str(e))


TOOLS = {
    "query_engagement": query_engagement,
    "calculate_kpis": calculate_kpis,
    "calculate_risk": calculate_risk,
    "get_shap_explanation": get_shap_explanation_tool,
    "detect_anomalies": detect_anomalies_tool,
    "retrieve_evidence": retrieve_evidence_tool,
}


TOOL_SCHEMAS = {
    "query_engagement": {
        "name": "query_engagement",
        "description": "Get basic engagement information",
        "parameters": {
            "type": "object",
            "properties": {
                "engagement_id": {"type": "string", "description": "Engagement ID (e.g., ENG001)"}
            },
            "required": ["engagement_id"],
        },
    },
    "calculate_kpis": {
        "name": "calculate_kpis",
        "description": "Calculate all KPIs for an engagement",
        "parameters": {
            "type": "object",
            "properties": {
                "engagement_id": {"type": "string", "description": "Engagement ID"}
            },
            "required": ["engagement_id"],
        },
    },
    "calculate_risk": {
        "name": "calculate_risk",
        "description": "Calculate risk score and breakdown for an engagement",
        "parameters": {
            "type": "object",
            "properties": {
                "engagement_id": {"type": "string", "description": "Engagement ID"}
            },
            "required": ["engagement_id"],
        },
    },
    "get_shap_explanation": {
        "name": "get_shap_explanation",
        "description": "Get SHAP feature contributions for risk prediction",
        "parameters": {
            "type": "object",
            "properties": {
                "engagement_id": {"type": "string", "description": "Engagement ID"}
            },
            "required": ["engagement_id"],
        },
    },
    "detect_anomalies": {
        "name": "detect_anomalies",
        "description": "Detect anomalies in engagement metrics",
        "parameters": {
            "type": "object",
            "properties": {
                "engagement_id": {"type": "string", "description": "Engagement ID"}
            },
            "required": ["engagement_id"],
        },
    },
    "retrieve_evidence": {
        "name": "retrieve_evidence",
        "description": "Retrieve relevant knowledge base documents",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "top_k": {"type": "integer", "description": "Number of results", "default": 5}
            },
            "required": ["query"],
        },
    },
}