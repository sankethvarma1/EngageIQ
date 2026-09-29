from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.analytics.anomalies import detect_all_anomalies
from app.api.schemas import Anomaly
from app.db.session import get_db

router = APIRouter()


@router.get("/{engagement_id}/anomalies", response_model=List[Anomaly])
def get_engagement_anomalies(engagement_id: str, db: Session = Depends(get_db)):
    from app.db.models import Engagement

    engagement = db.get(Engagement, engagement_id)
    if not engagement:
        raise HTTPException(status_code=404, detail="Engagement not found")

    anomalies = detect_all_anomalies(engagement_id, db)
    return anomalies