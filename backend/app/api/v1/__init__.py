from fastapi import APIRouter

from app.api.v1 import engagements, kpis, risk, anomalies, explanation, ai

api_router = APIRouter()

api_router.include_router(engagements.router, prefix="/engagements", tags=["engagements"])
api_router.include_router(kpis.router, prefix="/engagements", tags=["kpis"])
api_router.include_router(risk.router, prefix="/engagements", tags=["risk"])
api_router.include_router(anomalies.router, prefix="/engagements", tags=["anomalies"])
api_router.include_router(explanation.router, prefix="/engagements", tags=["explanation"])
api_router.include_router(ai.router, prefix="/ai", tags=["ai"])