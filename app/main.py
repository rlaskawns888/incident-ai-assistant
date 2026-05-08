import logging

from fastapi import FastAPI

from app.api.incident_router import router as incident_router
from app.api.document_router import router as document_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)

app = FastAPI (
    title="Incident AI Assistant"
    , description="AI 운영 장애 보고서 자동 요약 서비스"
    , version="0.1.0"
)

app.include_router(incident_router)
app.include_router(document_router)

@app.get("/")
def health_check():
    return {
        "status": "ok"
        , "message": "Incident AI Assistant API is running"
    }