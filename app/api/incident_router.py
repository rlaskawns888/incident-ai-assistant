from fastapi import APIRouter

from app.schemas.incident_schema import(
    IncidentAnalyzeRequest, 
    IncidentAnalyzeResponse,
    SimilarIncidentSearchRequest,
    SimilarIncidentSearchResponse,
    SimilarIncidentResult,
)
from app.services.incident_analyzer import IncidentAnalyzer
from app.services.embedding_service import EmbeddingService
from app.services.vector_store import VectorStore

router = APIRouter(
    prefix="/api/incidents"
    , tags=["Incidents"]
)

incident_analyzer = IncidentAnalyzer()
embedding_service = EmbeddingService()
vector_store = VectorStore()

@router.get("/ping")
def ping():
    return {
        "message": "incident router is working"
    }

@router.post("/analyze", response_model=IncidentAnalyzeResponse)
def analyze_incident(request: IncidentAnalyzeRequest):
    return incident_analyzer.analyze(request)

@router.post("/search-similar", response_model=SimilarIncidentSearchResponse)
def search_similar_incidents(request: SimilarIncidentSearchRequest):
    query_text = f"{request.title}\n{request.content}"

    query_embedding = embedding_service.embed_text(query_text)
