from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.analytics.kpis import calculate_all_kpis
from app.api.schemas import EngagementKPIs
from app.db.session import get_db

router = APIRouter()


@router.get("/{engagement_id}/kpis", response_model=EngagementKPIs)
def get_engagement_kpis(engagement_id: str, db: Session = Depends(get_db)):
    from app.db.models import Engagement

    engagement = db.get(Engagement, engagement_id)
    if not engagement:
        raise HTTPException(status_code=404, detail="Engagement not found")

    kpis = calculate_all_kpis(db, engagement_id)
    return kpis