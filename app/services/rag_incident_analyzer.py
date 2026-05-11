import logging
import time
from typing import Dict, List

from fastapi import HTTPException
from openai import (
    APIConnectionError,
    APITimeoutError,
    AuthenticationError,
    BadRequestError,
    InternalServerError,
    OpenAI,
    RateLimitError
)

from app.core.config import settings
from app.prompts.rag_prompt import(
    RAG_INCIDENT_ANALYSIS_SYSTEM_PROMPT,
    build_rag_incident_analysis_user_prompt,
)
from app.schemas.incident_schema import(
    IncidentAnalyzeWithRagRequest,
    IncidentAnalyzeWithRagResponse,
    IncidentSource
)
from app.services.embedding_service import EmbeddingService
from app.services.vector_store import VectorStore

logger = logging.getLogger(__name__)
      
class RagIncidentAnalyzer:
    def __init__(self):
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPEN_API_KEY is not set")
    
        self.client = OpenAI(
            api_key=settings.OPENAI_API_KEY,
            timeout=settings.OPENAI_TIMEOUT_SECONDS,
            max_retries=settings.OPENAI_MAX_RETRIES
        )

        self.embedding_service = EmbeddingService()
        self.vector_store = VectorStore()

    def analyze(
        self,
        request: IncidentAnalyzeWithRagRequest,
    ) -> IncidentAnalyzeWithRagResponse:
        start_time = time.perf_counter()

        try:
            logger.info(
                "RAG incident analysis started. title=%s top_k=%s",
                request.title,
                request.top_k,
            )

            similar_chunks = self._search_similar_chunks(request)

            user_prompt = build_rag_incident_analysis_user_prompt(
                title=request.title,
                content=request.content,
                similar_chunks=similar_chunks,
            )

            response = self.client.responses.parse(
                model=settings.OPENAI_MODEL,
                input=[
                    {
                        "role": "system",
                        "content": RAG_INCIDENT_ANALYSIS_SYSTEM_PROMPT,
                    },
                    {
                        "role": "user",
                        "content": user_prompt,
                    },
                ],
                text_format=IncidentAnalyzeWithRagResponse,
            )

            parsed_response = response.output_parsed

            sources = self._build_sources(similar_chunks)
            # AI가 만든 sources 그대로 사용하지 않음
            # 이유: AI가 source를 약간 다르게 쓰거나, content를 요약하거나, 순서를 바꿀 수도 있기 대문.

            elapsed_ms = (time.perf_counter() - start_time) * 1000

            logger.info(
                "RAG incident analysis completed. title=%s source_count=%s elapsed_ms=%.2f",
                request.title,
                len(sources),
                elapsed_ms,
            )

            return IncidentAnalyzeWithRagResponse(
                summary=parsed_response.summary,
                impact=parsed_response.impact,
                suspected_causes=parsed_response.suspected_causes,
                completed_actions=parsed_response.completed_actions,
                recommended_actions=parsed_response.recommended_actions,
                severity=parsed_response.severity,
                needs_confirmation=parsed_response.needs_confirmation,
                sources=sources,
            )
        
        except AuthenticationError:
            raise HTTPException(
                status_code=401,
                detail="OpenAI authentication failed. Check your API key.",
            )

        except BadRequestError as e:
            raise HTTPException(
                status_code=400,
                detail=f"OpenAI request failed. Check model name or request format. {str(e)}",
            )

        except RateLimitError:
            raise HTTPException(
                status_code=429,
                detail="OpenAI rate limit exceeded. Please try again later.",
            )

        except APITimeoutError:
            raise HTTPException(
                status_code=504,
                detail="OpenAI request timed out. Please try again later.",
            )

        except APIConnectionError:
            raise HTTPException(
                status_code=503,
                detail="Failed to connect to OpenAI API.",
            )

        except InternalServerError:
            raise HTTPException(
                status_code=502,
                detail="OpenAI API server error. Please try again later.",
            )

        except HTTPException:
            raise

        except Exception as e:
            logger.exception(
                "RAG incident analysis failed. title=%s",
                request.title,
            )
            raise HTTPException(
                status_code=500,
                detail=f"RAG incident analysis failed: {str(e)}",
            )
        

    def _search_similar_chunks(
        self,
        request: IncidentAnalyzeWithRagRequest,
    ) -> List[Dict]:
        query_text = f"{request.title}\n{request.content}"

        query_embedding = self.embedding_service.embed_text(query_text)

        search_result = self.vector_store.search_similar_chunks(
            query_embedding=query_embedding,
            top_k=request.top_k,
        )

        ids = search_result.get("ids", [[]])[0]
        documents = search_result.get("documents", [[]])[0]
        metadatas = search_result.get("metadatas", [[]])[0]
        distances = search_result.get("distances", [[]])[0]

        similar_chunks = []

        for item_id, document, metadata, distance in zip(
            ids,
            documents,
            metadatas,
            distances,
        ):
            similar_chunks.append(
                {
                    "chunk_id": item_id,
                    "incident_id": metadata["incident_id"],
                    "title": metadata["title"],
                    "service": metadata["service"],
                    "severity": metadata["severity"],
                    "section": metadata["section"],
                    "content": document,
                    "distance": distance,
                }
            )

        return similar_chunks


    def _build_sources(
        self,
        similar_chunks: List[Dict],
    ) -> List[IncidentSource]:
        sources = []

        for chunk in similar_chunks:
            sources.append(
                IncidentSource(
                    incident_id=chunk["incident_id"],
                    title=chunk["title"],
                    service=chunk["service"],
                    section=chunk["section"],
                    content=chunk["content"],
                )
            )

        return sources