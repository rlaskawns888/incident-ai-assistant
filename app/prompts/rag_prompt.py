from typing import List, Dict

RAG_INCIDENT_ANALYSIS_SYSTEM_PROMPT = """
    너는 운영 장애 보고서 작성을 돕는 AI 어시스턴트다.

    너의 목표는 사용자가 입력한 현재 장애 내용과
    검색된 과거 유사 장애 사례를 참고하여
    장애 보고서 초안을 JSON 형식으로 구조화하는 것이다.

    반드시 아래 규칙을 지켜라.

    1. 현재 장애 내용과 제공된 과거 유사 장애 사례만 근거로 분석한다.
    2. 입력에 없는 수치, 시간, 서비스명, 원인, 조치 내역은 추측해서 만들지 않는다.
    3. 과거 장애 사례와 유사하더라도 현재 장애의 원인을 확정적으로 표현하지 않는다.
    4. 원인은 suspected_causes에 가능성 있는 후보로만 작성한다.
    5. 과거 장애 사례에서 효과가 있었던 조치는 recommended_actions에 참고 형태로 작성할 수 있다.
    6. 이미 현재 장애 내용에 수행한 조치가 명시되어 있으면 completed_actions에 작성한다.
    7. 확실하지 않거나 추가 확인이 필요한 내용은 needs_confirmation에 작성한다.
    8. 과거 장애 사례를 참고한 경우 sources에 해당 source 정보를 포함한다.
    9. severity는 반드시 LOW, MEDIUM, HIGH, CRITICAL 중 하나만 사용한다.
    10. 반드시 JSON만 반환한다.
    11. JSON 외의 설명 문장, 마크다운, 코드블럭은 절대 출력하지 않는다.

    응답 JSON 형식은 반드시 아래 구조를 따른다.

    {
        "summary": "현재 장애 내용을 한두 문장으로 요약",
        "impact": "현재 장애의 사용자 또는 서비스 영향 범위",
        "suspected_causes": ["가능성 있는 원인 후보"],
        "completed_actions": ["현재 장애에서 이미 수행한 조치"],
        "recommended_actions": ["과거 유사 장애 사례를 참고한 추가 권장 조치"],
        "severity": "LOW | MEDIUM | HIGH | CRITICAL",
        "needs_confirmation": ["추가 확인 필요 항목"],
        "sources": [
            {
            "incident_id": "과거 장애 식별자",
            "title": "과거 장애 제목",
            "service": "과거 장애 서비스명",
            "section": "참고한 섹션명",
            "content": "참고한 과거 장애 chunk 내용"
            }
        ]
    }
"""

def build_rag_incident_analysis_user_prompt(
    title: str,
    content: str,
    similar_chunks: List[Dict],
) -> str:
    sources_text = _format_similar_chunks(similar_chunks)

    return f"""
        아래 현재 운영 장애 내용을 분석해라.

        [현재 장애 제목]
        {title}

        [현재 장애 상세 내용]
        {content}

        [검색된 과거 유사 장애 사례]
        {sources_text}

        위 과거 유사 장애 사례는 참고 자료일 뿐이다.
        현재 장애의 원인을 확정하지 말고, 가능성 있는 원인 후보와 추가 확인 필요 항목을 분리해서 작성해라.
    """

def _format_similar_chunks(similar_chunks: List[Dict]):
    if not similar_chunks:
        return "검색된 과거 유사 장애 사례가 없습니다."

    formatted_chunks = []

    for index, chunk in enumerate(similar_chunks, start=1):
        formatted_chunks.append(
            f"""
                [Source {index}]
                incident_id: {chunk.get("incident_id")}
                title: {chunk.get("title")}
                service: {chunk.get("service")}
                severity: {chunk.get("severity")}
                section: {chunk.get("section")}
                content: {chunk.get("content")}
                distance: {chunk.get("distance")} 
                //distance: 값이 작을 수록 정확도가 높다.
                // - 값이 작을 수록, 의미적으로 가깝다고 의미하지만, 실제 장애 원인이 100%라고 보면 안됨
                // - Chroma가 embedding 벡터끼리 계산해서 만든 값
            """
        )

    return "\n".join(formatted_chunks)