# Incident AI Assistant

운영 장애 보고서 자동 요약 및 유사 장애 기반 RAG 분석 서비스입니다.

현재 장애 내용을 입력하면 LLM이 장애 보고서 초안을 생성하고,  
과거 장애 문서를 Vector DB에 저장한 뒤 현재 장애와 유사한 과거 장애 사례를 검색하여  
근거 기반 장애 분석을 수행할 수 있습니다.

---

## 1. 프로젝트 목적

운영 장애 대응 과정에서는 장애 내용 정리, 원인 후보 도출, 조치 내역 정리, 재발 방지 항목 작성이 반복적으로 발생합니다.

이 프로젝트는 이러한 반복 업무를 줄이기 위해 다음 기능을 제공합니다.

- 현재 장애 내용을 기반으로 장애 보고서 초안 자동 생성
- 과거 장애 문서를 chunk 단위로 분리
- chunk를 embedding하여 Vector DB에 저장
- 현재 장애와 유사한 과거 장애 사례 검색
- 검색된 과거 장애 사례를 참고한 RAG 기반 장애 분석

---

## 2. 문제 정의

운영 장애 보고서는 다음과 같은 문제가 있습니다.

1. 장애 발생 직후에는 정보가 흩어져 있어 보고서 작성이 어렵다.
2. 과거에 비슷한 장애가 있었더라도 빠르게 찾기 어렵다.
3. 장애 원인과 조치 내역을 매번 수동으로 정리해야 한다.
4. LLM만 사용하면 과거 장애 이력을 알 수 없어 일반적인 답변에 그칠 수 있다.

이 프로젝트는 LLM과 Vector DB 기반 RAG 구조를 사용하여  
현재 장애 분석에 과거 장애 사례를 참고할 수 있도록 설계했습니다.

---

## 3. 주요 기능

### 3.1 현재 장애 분석

현재 장애 제목과 상세 내용을 입력하면 LLM이 장애 보고서 초안을 생성합니다.

API:

```http
POST /api/incidents/analyze
```

주요 응답 항목:

- summary
- impact
- suspected_causes
- completed_actions
- recommended_actions
- severity
- needs_confirmation

처리 흐름:

```text
현재 장애 내용 입력
↓
System Prompt + User Prompt 생성
↓
OpenAI Responses API 호출
↓
Structured Output 기반 JSON 응답 반환
```

---

### 3.2 과거 장애 문서 등록

과거 장애 보고서를 등록하면 문서를 섹션 단위로 chunking하고,  
각 chunk를 embedding하여 ChromaDB에 저장합니다.

API:

```http
POST /api/incident-documents
```

요청 예시:

```json
{
  "incident_id": "INC-2026-001",
  "title": "결제 API timeout 장애",
  "service": "payment-service",
  "severity": "HIGH",
  "content": "장애 개요: 2026년 01월 12일 결제 API timeout 증가\n영향 범위: 일부 사용자의 주문 생성 실패\n원인 분석: DB connection pool 부족과 slow query 증가\n조치 내역: connection pool size 증가, index 추가\n재발 방지: connection pool 모니터링 기준 강화"
}
```

처리 흐름:

```text
과거 장애 문서 입력
↓
section 기반 chunking
↓
OpenAI Embedding API 호출
↓
chunk + embedding + metadata 생성
↓
ChromaDB 저장
```

저장되는 metadata:

- incident_id
- title
- service
- severity
- section
- chunk_index

---

### 3.3 유사 장애 검색

현재 장애 내용을 embedding한 뒤,  
ChromaDB에 저장된 과거 장애 chunk 중 의미적으로 유사한 chunk를 검색합니다.

API:

```http
POST /api/incidents/search-similar
```

요청 예시:

```json
{
  "title": "결제 API timeout 증가",
  "content": "오늘 오전부터 결제 API timeout이 증가했고 DB connection pool 사용률이 급격히 올라갔습니다.",
  "top_k": 3
}
```

응답 예시:

```json
{
  "results": [
    {
      "incident_id": "INC-2026-001",
      "title": "결제 API timeout 장애",
      "service": "payment-service",
      "severity": "HIGH",
      "section": "원인 분석",
      "content": "DB connection pool 부족과 slow query 증가",
      "distance": 0.23
    }
  ]
}
```

처리 흐름:

```text
현재 장애 내용 입력
↓
OpenAI Embedding API 호출
↓
현재 장애 내용을 query embedding으로 변환
↓
ChromaDB vector search
↓
유사 과거 장애 chunk 반환
```

`distance`는 벡터 거리값입니다.  
값이 낮을수록 현재 장애 내용과 과거 장애 chunk가 의미적으로 더 가깝다고 볼 수 있습니다.

---

### 3.4 RAG 기반 장애 분석

현재 장애 내용으로 유사 과거 장애를 검색하고,  
검색된 과거 장애 chunk를 LLM prompt에 포함하여 근거 기반 장애 분석을 생성합니다.

API:

```http
POST /api/incidents/analyze-with-rag
```

요청 예시:

```json
{
  "title": "결제 API timeout 증가",
  "content": "오늘 오전부터 결제 API timeout이 증가했고 DB connection pool 사용률이 급격히 올라갔습니다.",
  "top_k": 3
}
```

응답 예시:

```json
{
  "summary": "결제 API timeout이 증가했고 DB connection pool 사용률이 급격히 상승한 장애입니다.",
  "impact": "일부 결제 또는 주문 생성 요청에 지연이나 실패가 발생했을 가능성이 있습니다.",
  "suspected_causes": [
    "DB connection pool 부족 가능성",
    "slow query 증가 가능성"
  ],
  "completed_actions": [],
  "recommended_actions": [
    "DB connection pool 사용률 추이를 확인합니다.",
    "slow query 발생 여부와 실행 계획을 확인합니다.",
    "과거 유사 장애에서 수행했던 connection pool size 조정과 index 추가 필요성을 검토합니다."
  ],
  "severity": "HIGH",
  "needs_confirmation": [
    "DB connection pool 부족이 timeout의 직접 원인인지 확인 필요",
    "slow query 발생 여부 확인 필요",
    "실제 사용자 영향 범위 확인 필요"
  ],
  "sources": [
    {
      "incident_id": "INC-2026-001",
      "title": "결제 API timeout 장애",
      "service": "payment-service",
      "section": "원인 분석",
      "content": "DB connection pool 부족과 slow query 증가"
    }
  ]
}
```

처리 흐름:

```text
현재 장애 내용 입력
↓
현재 장애 내용 embedding
↓
ChromaDB에서 유사 과거 장애 chunk 검색
↓
검색된 chunk를 RAG prompt에 포함
↓
OpenAI Responses API 호출
↓
sources 포함 장애 분석 응답 반환
```

---

## 4. 기술 스택

- Python
- FastAPI
- Pydantic
- OpenAI API
- OpenAI Embedding API
- ChromaDB
- Uvicorn
- python-dotenv

---

## 5. 시스템 구조

```text
app/
├── api/
│   ├── incident_router.py
│   └── document_router.py
├── core/
│   └── config.py
├── prompts/
│   ├── incident_prompt.py
│   └── rag_prompt.py
├── schemas/
│   ├── incident_schema.py
│   ├── document_schema.py
│   └── chunk_schema.py
└── services/
    ├── incident_analyzer.py
    ├── rag_incident_analyzer.py
    ├── document_ingestion_service.py
    ├── chunker.py
    ├── embedding_service.py
    └── vector_store.py
```

---

## 6. RAG 처리 흐름

### 6.1 과거 장애 저장 흐름

```text
POST /api/incident-documents
↓
DocumentIngestionService
↓
IncidentDocumentChunker
↓
EmbeddingService
↓
VectorStore
↓
ChromaDB
```

### 6.2 현재 장애 RAG 분석 흐름

```text
POST /api/incidents/analyze-with-rag
↓
RagIncidentAnalyzer
↓
EmbeddingService
↓
VectorStore.search_similar_chunks()
↓
RAG Prompt 생성
↓
OpenAI Responses API
↓
IncidentAnalyzeWithRagResponse
```

---

## 7. API 목록

| Method | Path | Description |
|---|---|---|
| GET | / | Health Check |
| GET | /api/incidents/ping | Incident Router Check |
| POST | /api/incidents/analyze | 현재 장애 기본 분석 |
| POST | /api/incident-documents | 과거 장애 문서 등록 |
| POST | /api/incidents/search-similar | 유사 과거 장애 검색 |
| POST | /api/incidents/analyze-with-rag | RAG 기반 장애 분석 |

---

## 8. 실행 방법

### 8.1 가상환경 생성

```bash
python -m venv venv
```

### 8.2 가상환경 활성화

Windows:

```bash
venv\Scripts\activate
```

Mac / Linux:

```bash
source venv/bin/activate
```

### 8.3 패키지 설치

```bash
pip install -r requirements.txt
```

### 8.4 환경변수 설정

프로젝트 루트에 `.env` 파일을 생성합니다.

```env
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-5.5
OPENAI_TIMEOUT_SECONDS=30
OPENAI_MAX_RETRIES=1

OPENAI_EMBEDDING_MODEL=text-embedding-3-small

CHROMA_DB_PATH=./chroma_db
CHROMA_COLLECTION_NAME=incident_chunks
```

### 8.5 서버 실행

```bash
python -m uvicorn app.main:app --reload
```

Swagger:

```text
http://127.0.0.1:8000/docs
```

---

## 9. 테스트 시나리오

### 9.1 과거 장애 문서 등록

API:

```http
POST /api/incident-documents
```

요청:

```json
{
  "incident_id": "INC-2026-001",
  "title": "결제 API timeout 장애",
  "service": "payment-service",
  "severity": "HIGH",
  "content": "장애 개요: 2026년 01월 12일 결제 API timeout 증가\n영향 범위: 일부 사용자의 주문 생성 실패\n원인 분석: DB connection pool 부족과 slow query 증가\n조치 내역: connection pool size 증가, index 추가\n재발 방지: connection pool 모니터링 기준 강화"
}
```

예상 응답:

```json
{
  "incident_id": "INC-2026-001",
  "title": "결제 API timeout 장애",
  "chunk_count": 5,
  "message": "Incident document indexed successfully."
}
```

---

### 9.2 ChromaDB 저장 확인

```bash
python -c "from app.services.vector_store import VectorStore; store=VectorStore(); data=store.get_all(); print(data['ids']); print(data['metadatas']); print(data['documents'])"
```

예상 확인 항목:

- ids에 chunk id가 저장되어 있는지 확인
- metadatas에 incident_id, title, service, severity, section, chunk_index가 저장되어 있는지 확인
- documents에 chunk 본문이 저장되어 있는지 확인

---

### 9.3 유사 장애 검색

API:

```http
POST /api/incidents/search-similar
```

요청:

```json
{
  "title": "결제 API timeout 증가",
  "content": "오늘 오전부터 결제 API timeout이 증가했고 DB connection pool 사용률이 급격히 올라갔습니다.",
  "top_k": 3
}
```

확인 항목:

- results가 비어 있지 않은지 확인
- 관련 있는 과거 장애 chunk가 상위에 나오는지 확인
- distance가 반환되는지 확인

---

### 9.4 기본 AI 분석

API:

```http
POST /api/incidents/analyze
```

요청:

```json
{
  "title": "결제 API timeout 증가",
  "content": "오늘 오전부터 결제 API timeout이 증가했고 DB connection pool 사용률이 급격히 올라갔습니다."
}
```

확인 항목:

- 현재 장애 내용만 기반으로 분석되는지 확인
- sources 필드가 없는지 확인

---

### 9.5 RAG 기반 장애 분석

API:

```http
POST /api/incidents/analyze-with-rag
```

요청:

```json
{
  "title": "결제 API timeout 증가",
  "content": "오늘 오전부터 결제 API timeout이 증가했고 DB connection pool 사용률이 급격히 올라갔습니다.",
  "top_k": 3
}
```

확인 항목:

- 현재 장애 내용과 유사 과거 장애가 함께 반영되는지 확인
- sources가 포함되는지 확인
- recommended_actions에 과거 조치 내역이 참고되는지 확인
- needs_confirmation에 확정되지 않은 항목이 분리되는지 확인

---

## 10. 구현 포인트

### 10.1 Structured Output

LLM 응답을 자유 텍스트가 아니라 Pydantic schema 기반 JSON으로 받도록 구현했습니다.

이를 통해 API 응답 구조를 안정적으로 유지할 수 있습니다.

---

### 10.2 Chunking

과거 장애 문서를 다음 섹션 기준으로 나눕니다.

- 장애 개요
- 영향 범위
- 원인 분석
- 조치 내역
- 재발 방지

문서를 chunk 단위로 나누면 전체 문서를 하나의 embedding으로 저장하는 것보다  
검색 결과가 더 세밀해집니다.

---

### 10.3 Embedding

각 chunk를 OpenAI Embedding API를 사용해 숫자 벡터로 변환합니다.

사용 모델:

```text
text-embedding-3-small
```

Embedding은 텍스트의 의미를 숫자 벡터로 표현합니다.

예:

```text
"DB connection pool 부족과 slow query 증가"
↓
[0.012, -0.043, 0.331, ...]
```

---

### 10.4 Vector DB

ChromaDB를 사용해 chunk, embedding, metadata를 저장합니다.

저장 항목:

- id
- document
- embedding
- metadata

metadata에는 다음 정보가 포함됩니다.

- incident_id
- title
- service
- severity
- section
- chunk_index

---

### 10.5 Semantic Search

현재 장애 내용을 embedding한 뒤,  
ChromaDB에 저장된 과거 장애 chunk embedding과 거리 계산을 수행합니다.

`distance`는 낮을수록 현재 장애 내용과 과거 장애 chunk가 의미적으로 가깝다는 뜻입니다.

다만 distance는 정답률이 아니라 벡터 공간에서의 유사도 참고값입니다.

---

### 10.6 RAG

현재 장애 내용을 embedding한 뒤 ChromaDB에서 유사한 과거 장애 chunk를 검색합니다.

검색된 chunk를 RAG prompt에 포함하여 LLM이 현재 장애를 분석하도록 구성했습니다.

응답에는 sources를 포함하여 어떤 과거 장애 chunk를 참고했는지 확인할 수 있습니다.

---

### 10.7 Source 추적

RAG 분석 응답에는 sources를 포함합니다.

이를 통해 LLM이 어떤 과거 장애 사례를 참고했는지 확인할 수 있습니다.

예:

```json
{
  "sources": [
    {
      "incident_id": "INC-2026-001",
      "title": "결제 API timeout 장애",
      "service": "payment-service",
      "section": "원인 분석",
      "content": "DB connection pool 부족과 slow query 증가"
    }
  ]
}
```

---

## 11. 일반 LLM 분석과 RAG 분석의 차이

### 11.1 일반 분석

API:

```http
POST /api/incidents/analyze
```

흐름:

```text
현재 장애 내용
↓
LLM
↓
장애 분석 JSON
```

특징:

- 현재 입력만 보고 분석
- 과거 장애 이력은 참고하지 않음
- sources 없음

---

### 11.2 RAG 분석

API:

```http
POST /api/incidents/analyze-with-rag
```

흐름:

```text
현재 장애 내용
↓
embedding
↓
ChromaDB 유사 장애 검색
↓
검색된 과거 장애 chunk를 prompt에 포함
↓
LLM
↓
sources 포함 장애 분석 JSON
```

특징:

- 과거 유사 장애를 참고함
- 과거 조치 내역을 recommended_actions에 반영 가능
- sources를 통해 근거 추적 가능

---