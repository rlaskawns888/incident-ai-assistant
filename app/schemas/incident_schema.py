from enum import Enum
from typing import List

from pydantic import BaseModel, Field

class Severity(str, Enum):
    LOW="LOW"
    MEDIUM="MEDIUM"
    HIGH="HIGH"
    CRITICAL="CRITICAL"


class IncidentAnalyzeRequest(BaseModel):
    title: str = Field(
        ...
        , min_length=1
        , max_length=200
        , description="장애 제목"
        , examples=["결제 API timeout 장애"]
    )
    content: str = Field(
        ...
        , min_length=10
        , description="장애 상세 내용"
        , examples=[
            "2026-04-30 10:12부터 결제 API timeout이 증가했습니다. "
            "주문 생성 요청 중 일부가 실패했고, DB connection pool 사용률이 급증했습니다."
        ]
    )


class IncidentAnalyzeResponse(BaseModel):
    summary: str = Field(..., description="장애 요약")
    impact: str = Field(..., description="장애 영향 범위")
    suspected_causes: List[str] = Field(..., description="가능성 있는 원인 후보")
    completed_actions: List[str] = Field(..., description="이미 수행한 조치")
    recommended_actions: List[str] = Field(..., description="추가 권장 조치")
    severity: Severity = Field(..., description="장애 심각도")
    needs_confirmation: List[str] = Field(..., description="추가 확인 필요 항목")


class SimilarIncidentSearchRequest(BaseModel):
    title: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="현재 장애 제목",
        examples=["결제 API timeout 증가"],
    )
    content: str = Field(
        ...,
        min_length=10,
        description="현재 장애 상세 내용",
        examples=[
            "오늘 오전부터 결제 API timeout이 증가했고 "
            "DB connection pool 사용률이 급증했습니다."
        ],
    )
    top_k: int = Field(
        3,
        ge=1,
        le=10,
        description="검색할 유사 장애 chunk 개수",
        examples=[3],
    )


class SimilarIncidentResult(BaseModel):
    incident_id: str = Field(..., description="과거 장애 식별자")
    title: str = Field(..., description="과거 장애 제목")
    service: str = Field(..., description="장애 발생 서비스")
    severity: Severity = Field(..., description="장애 심각도")
    section: str = Field(..., description="검색된 chunk 섹션")
    content: str = Field(..., description="검색된 chunk 본문")
    distance: float = Field(..., description="Chroma vector distance. 값이 작을수록 유사함")


class SimilarIncidentSearchResponse(BaseModel):
    results: List[SimilarIncidentResult] = Field(
        ...,
        description="유사 장애 검색 결과",
    )


# 과거 장애 chunk
class IncidentSource(BaseModel): 
    incident_id: str = Field(..., description="참고한 과거 장애 식별자")
    title: str = Field(..., description="참고한 과저 장애 제목")
    service: str = Field(..., description="참고한 과거 장애 서비스명")
    section: str = Field(..., description="참고한 과거 장애 chunk 섹션")
    content: str = Field(..., description="참고한 과거 장애 chunk 본문")


class IncidentAnalyzeWithRagRequest(BaseModel):
    title: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="현재 장애 제목",
        examples=["결제 API timeout 증가"],
    )
    content: str = Field(
        ...,
        min_length=10,
        description="현재 장애 상세 내용",
        examples=[
            "오늘 오전부터 결제 API timeout이 증가했고 "
            "DB connection pool 사용률이 급격히 올라갔습니다."
        ],
    )
    top_k: int = Field(
        3,
        ge=1,
        le=10,
        description="RAG 분석에 사용할 유사 장애 chunk 개수",
        examples=[3],
    )


class IncidentAnalyzeWithRagResponse(BaseModel):
    summary: str = Field(..., description="현재 장애 요약")
    impact: str = Field(..., description="현재 장애 영향 범위")
    suspected_causes: List[str] = Field(..., description="가능성 있는 원인 후보")
    completed_actions: List[str] = Field(..., description="현재 장애에서 이미 수행한 조치")
    recommended_actions: List[str] = Field(..., description="추가 권장 조치")
    severity: Severity = Field(..., description="장애 심각도")
    needs_confirmation: List[str] = Field(..., description="추가 확인 필요 항목")
    sources: List[IncidentSource] = Field(..., description="분석에 참고한 과거 장애 source")