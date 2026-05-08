from fastapi import APIRouter

from app.schemas.document_schema import(
    IncidentDocumentCreateRequest,
    IncidentDocumentCreateResponse,
)
from app.services.document_ingestion_service import DocumentIngestionService

router = APIRouter(
    prefix="/api/incident-documents",
    tags=["Incident Documents"],
)

document_ingestion_service = DocumentIngestionService()

@router.post("", response_model=IncidentDocumentCreateResponse)
def create_incident_document(request: IncidentDocumentCreateRequest):
    return document_ingestion_service.create_document(request)