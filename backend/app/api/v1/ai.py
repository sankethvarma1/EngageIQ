from fastapi import APIRouter, HTTPException

from app.agents.orchestrator import investigate
from app.api.schemas import InvestigateRequest, InvestigateResponse

router = APIRouter()


@router.post("/investigate", response_model=InvestigateResponse)
async def ai_investigate(request: InvestigateRequest):
    try:
        result = await investigate(request.question, request.engagement_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))