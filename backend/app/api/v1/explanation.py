from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.ml.risk_model import get_shap_explanation
from app.api.schemas import SHAPExplanation
from app.db.session import get_db

router = APIRouter()


@router.get("/{engagement_id}/explanation", response_model=SHAPExplanation)
def get_engagement_explanation(engagement_id: str, db: Session = Depends(get_db)):
    from app.db.models import Engagement

    engagement = db.get(Engagement, engagement_id)
    if not engagement:
        raise HTTPException(status_code=404, detail="Engagement not found")

    explanation = get_shap_explanation(db, engagement_id)
    if "error" in explanation:
        raise HTTPException(status_code=404, detail=explanation["error"])

    return explanation