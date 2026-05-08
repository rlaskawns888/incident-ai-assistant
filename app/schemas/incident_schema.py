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