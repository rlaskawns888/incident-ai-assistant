from pydantic import BaseModel, Field

class DocumentChunk(BaseModel):
    chunk_index: int = Field(..., description="문서 내 chunk 순서")
    section: str = Field(..., description="chunk가 속한 섹션명")
    content: str = Field(..., description="chunk 본문")