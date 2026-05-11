from fastapi import APIRouter

from app.schemas.incident_schema import(
    IncidentAnalyzeRequest, 
    IncidentAnalyzeResponse,
    SimilarIncidentSearchRequest,
    SimilarIncidentSearchResponse,
    SimilarIncidentResult,
    IncidentAnalyzeWithRagRequest,
    IncidentAnalyzeWithRagResponse,
)
from app.services.incident_analyzer import IncidentAnalyzer
from app.services.embedding_service import EmbeddingService
from app.services.vector_store import VectorStore
from app.services.rag_incident_analyzer import RagIncidentAnalyzer

router = APIRouter(
    prefix="/api/incidents"
    , tags=["Incidents"]
)

incident_analyzer = IncidentAnalyzer()
embedding_service = EmbeddingService()
vector_store = VectorStore()
rag_incident_analyzer = RagIncidentAnalyzer()

@router.get("/ping")
def ping():
    return {
        "message": "incident router is working"
    }

#기본 AI 분석용
@router.post("/analyze", response_model=IncidentAnalyzeResponse)
def analyze_incident(request: IncidentAnalyzeRequest):
    return incident_analyzer.analyze(request)

#ChromaDB 유사 장애 검색
@router.post("/search-similar", response_model=SimilarIncidentSearchResponse)
def search_similar_incidents(request: SimilarIncidentSearchRequest):
    query_text = f"{request.title}\n{request.content}"

    query_embedding = embedding_service.embed_text(query_text)

    search_result = vector_store.search_similar_chunks(
        query_embedding=query_embedding,
        top_k=request.top_k
    )

    results = []

    ids = search_result.get("ids", [[]])[0]
    documents = search_result.get("documents", [[]])[0]
    metadatas = search_result.get("metadatas", [[]])[0]
    distances = search_result.get("distances", [[]])[0]

    for item_id, document, metadata, distance in zip(
        ids,
        documents,
        metadatas,
        distances,
    ):
        results.append(
            SimilarIncidentResult(
                incident_id=metadata["incident_id"],
                title=metadata["title"],
                service=metadata["service"],
                severity=metadata["severity"],
                section=metadata["section"],
                content=document,
                distance=distance,
            )
        )

        return SimilarIncidentSearchResponse(results=results)

@router.post("/analyze-with-rag", response_model=IncidentAnalyzeWithRagResponse)
def analyze_incident_with_rag(request: IncidentAnalyzeWithRagRequest):
    return rag_incident_analyzer.analyze(request)