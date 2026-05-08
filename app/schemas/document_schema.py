from pydantic import BaseModel, Field

from app.schemas.incident_schema import Severity

class IncidentDocumentCreateRequest(BaseModel):
    incident_id: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="장애식별자ID",
        examples=["INC-2026-001"]
    )
    title: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="장애 제목",
        examples=["결제 API timeout 장애"],
    )
    service: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="장애가 발생한 서비스명",
        examples=["payment-service"],
    )
    severity: Severity = Field(
        ...,
        description="장애 심각도",
        examples=["HIGH"],
    )
    content: str = Field(
        ...,
        min_length=20,
        description="과거 장애 보고서 전체 내용",
        examples=[
            "장애 개요: 2026년 01월 12일 결제 API timeout 증가\n"
            "영향 범위: 일부 사용자의 주문 생성 실패\n"
            "원인 분석: DB connection pool 부족과 slow query 증가\n"
            "조치 내역: connection pool size 증가, index 추가\n"
            "재발 방지: connection pool 모니터링 기준 강화"
        ],
    )

class IncidentDocumentCreateResponse(BaseModel):
    incident_id: str = Field(..., description="장애 식별자")
    title: str = Field(..., description="장애 제목")
    chunk_count: int = Field(..., description="생성된 chunk 개수")
    message: str = Field(..., description="처리 결과 메시지")