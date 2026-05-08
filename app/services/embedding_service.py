from typing import List

from openai import OpenAI

from app.core.config import settings

# 텍스트 → 숫자 벡터
class EmbeddingService:
    def __init__(self):
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is not set")
        
        self.client = OpenAI(
            api_key=settings.OPENAI_API_KEY,
            timeout=settings.OPENAI_TIMEOUT_SECONDS,
            max_retries=settings.OPENAI_MAX_RETRIES,
        )
        self.model = settings.OPENAI_EMBEDDING_MODEL

    #단건 embedding
    def embed_text(self, text: str) -> List[float]:
        cleaned_text = text.strip()

        if not cleaned_text:
            raise ValueError("text must not be empty")
        
        response = self.client.embeddings.create( #embedding API를 호출
            model=self.model,
            input=cleaned_text,

        )

        return response.data[0].embedding
    
    #다건 embedding
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        cleaned_texts = [text.strip() for text in texts if text.strip()]

        if not cleaned_texts:
            raise ValueError("texts must not be empty")

        response = self.client.embeddings.create(
            model=self.model,
            input=cleaned_texts,
        )

        return [item.embedding for item in response.data]