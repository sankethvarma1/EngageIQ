from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.ml.risk_model import predict_risk, get_model_metrics, retrain_model
from app.api.schemas import RiskFactors, ModelMetrics
from app.core.config import get_settings
from app.db.session import get_db

router = APIRouter()


@router.get("/{engagement_id}/risk", response_model=RiskFactors)
def get_engagement_risk(engagement_id: str, db: Session = Depends(get_db)):
    from app.db.models import Engagement

    engagement = db.get(Engagement, engagement_id)
    if not engagement:
        raise HTTPException(status_code=404, detail="Engagement not found")

    risk = predict_risk(db, engagement_id)
    return risk


@router.get("/model/metrics", response_model=ModelMetrics)
def get_model_metrics_endpoint():
    metrics = get_model_metrics()
    if "error" in metrics:
        raise HTTPException(status_code=404, detail=metrics["error"])
    return metrics


@router.post("/model/retrain", response_model=ModelMetrics)
def retrain_model_endpoint():
    if not get_settings().allow_model_retrain:
        raise HTTPException(
            status_code=403,
            detail="Model retraining is disabled in this deployment.",
        )
    try:
        metrics = retrain_model()
        return metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))