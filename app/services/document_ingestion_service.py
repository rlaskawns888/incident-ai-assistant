import logging
import time

from fastapi import HTTPException

from app.schemas.document_schema import(
    IncidentDocumentCreateRequest,
    IncidentDocumentCreateResponse
)
from app.services.chunker import IncidentDocumentChunker
from app.services.embedding_service import EmbeddingService
from app.services.vector_store import VectorStore

logger = logging.getLogger(__name__)

class DocumentIngestionService:
    def __init__(self):
        self.chunker = IncidentDocumentChunker()
        self.embedding_service = EmbeddingService()
        self.vector_store = VectorStore()
    
    def create_document(
        self,
        request: IncidentDocumentCreateRequest,
    ) -> IncidentDocumentCreateResponse:
        start_time = time.perf_counter()

        try:
            logger.info(
                "incident document indexing started. incident_id=%s title=%s",
                request.incident_id,
                request.title,
            )

            chunks = self.chunker.split(request.content) #과거 장애 보고서 본문을 chunk로 나눔

            if not chunks:
                raise HTTPException(
                    status_code=400,
                    detail="No chunks were created from teh incident document"
                )
            
            chunk_texts = [chunk.content for chunk in chunks]
            embeddings = self.embedding_service.embed_texts(chunk_texts)
            #chunk 본문만 뽑아서 embedding API 호출
            
            saved_count = self.vector_store.add_incident_chunks(
                incident_id=request.incident_id,
                title=request.title,
                service=request.service,
                severity=request.severity,
                chunks=chunks,
                embeddings=embeddings,
            )

            elapsed_ms = (time.perf_counter() - start_time) * 1000

            logger.info(
                "incident document indexing completed. incident_id=%s chunk_count=%s elapsed_ms=%.2f",
                request.incident_id,
                saved_count,
                elapsed_ms,
            )

            return IncidentDocumentCreateResponse(
                incident_id=request.incident_id,
                title=request.title,
                chunk_count=saved_count,
                message="Incident document indexed successfully.",
            )

        except HTTPException:
            raise

        except Exception as e:
            logger.exception(
                "incident document indexing failed. incident_id=%s",
                request.incident_id,
            )
            raise HTTPException(
                status_code=500,
                detail=f"Incident document indexing failed: {str(e)}",
            )

