from fastapi import APIRouter

from app.schemas.incident_schema import(
    IncidentAnalyzeRequest
    , IncidentAnalyzeResponse
)
from app.services.incident_analyzer import IncidentAnalyzer

router = APIRouter(
    prefix="/api/incidents"
    , tags=["Incidents"]
)

incident_analyzer = IncidentAnalyzer()

@router.get("/ping")
def ping():
    return {
        "message": "incident router is working"
    }

@router.post("/analyze", response_model=IncidentAnalyzeResponse)
def analyze_incident(request: IncidentAnalyzeRequest):
    return incident_analyzer.analyze(request)