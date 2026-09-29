from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.schemas import EngagementBase, EngagementList
from app.db.models import Engagement
from app.db.session import get_db

router = APIRouter()


@router.get("", response_model=EngagementList)
def list_engagements(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    status: Optional[str] = Query(None),
    client_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    query = select(Engagement)

    if status:
        query = query.where(Engagement.status == status)
    if client_id:
        query = query.where(Engagement.client_id == client_id)

    total = db.execute(select(func.count()).select_from(query.subquery())).scalar()

    engagements = db.execute(
        query.order_by(Engagement.start_date.desc()).offset(skip).limit(limit)
    ).scalars().all()

    return EngagementList(engagements=engagements, total=total)


@router.get("/{engagement_id}", response_model=EngagementBase)
def get_engagement(engagement_id: str, db: Session = Depends(get_db)):
    engagement = db.get(Engagement, engagement_id)
    if not engagement:
        raise HTTPException(status_code=404, detail="Engagement not found")
    return engagement