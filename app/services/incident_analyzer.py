import logging
import time

from fastapi import HTTPException
from openai import (
    OpenAI,
    AuthenticationError,
    BadRequestError,
    APIConnectionError,
    APITimeoutError,
    RateLimitError,
    APIStatusError,
)

from app.core.config import settings
from app.prompts.incident_prompt import(
    INCIDENT_ANALYSIS_SYSTEM_PROMPT
    , build_incident_analysis_user_prompt
)
from app.schemas.incident_schema import(
    IncidentAnalyzeRequest
    , IncidentAnalyzeResponse
    , Severity
)

logger = logging.getLogger(__name__)

class IncidentAnalyzer:
    def __init__(self):
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is not set")
        
        self.client = OpenAI(
            api_key=settings.OPENAI_API_KEY,
            timeout=settings.OPENAI_TIMEOUT_SECONDS,
            max_retries=settings.OPENAI_MAX_RETRIES,
        )
        self.model=settings.OPENAI_MODEL
        
    def analyze(self, request: IncidentAnalyzeRequest) -> IncidentAnalyzeResponse:
        start_time = time.perf_counter()

        user_prompt = build_incident_analysis_user_prompt(
            title = request.title
            , content = request.content
        )

        try:
            logger.info("incident analysis started. title=%s", request.title)

            response = self.client.responses.parse(
                model=self.model
                , input=[
                    {
                        "role":"system"
                        , "content":INCIDENT_ANALYSIS_SYSTEM_PROMPT
                    }
                    , {
                        "role":"user"
                        , "content":user_prompt
                    }
                ]
                , text_format = IncidentAnalyzeResponse
            )

            parsed_result = response.output_parsed

            if parsed_result is None:
                raise ValueError("OpenAI response parsing fail")
            
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            logger.info(
                "incident analysis completed. title=%s elapsed_ms=%.2f",
                request.title,
                elapsed_ms,
            )
            
            return parsed_result

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

        except APIStatusError as e:
            raise HTTPException(
                status_code=502,
                detail=f"OpenAI API returned an error. status_code={e.status_code}",
            )

        except HTTPException:
            raise

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Unexpected server error: {str(e)}",
            )

        # MOCK TEST
        # return IncidentAnalyzeResponse(
        #     summary=f"{request.title}에 대한 장애 보고서 초안입니다.",
        #     impact="일부 사용자 또는 일부 기능에 영향이 있었을 가능성이 있습니다.",
        #     suspected_causes=[
        #         "입력된 장애 내용 기준으로 원인 후보 분석이 필요합니다.",
        #         "로그, 지표, 배포 이력 확인이 필요합니다.",
        #     ],
        #     completed_actions=[
        #         "현재 단계에서는 사용자가 입력한 조치 내역을 기반으로 정리 예정입니다."
        #     ],
        #     recommended_actions=[
        #         "장애 발생 시점의 로그를 확인하세요.",
        #         "영향 범위와 고객 문의 발생 여부를 확인하세요.",
        #         "최근 배포 또는 설정 변경 여부를 확인하세요.",
        #     ],
        #     severity=Severity.MEDIUM,
        #     needs_confirmation=[
        #         "정확한 장애 영향 범위 확인 필요",
        #         "원인 후보와 실제 원인의 구분 필요",
        #     ],
        # )