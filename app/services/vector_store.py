from typing import List

import chromadb

from app.core.config import settings
from app.schemas.chunk_schema import DocumentChunk
from app.schemas.incident_schema import Severity

class VectorStore:
    def __init__(self):
        self.client = chromadb.PersistentClient(
            path=settings.CHROMA_DB_PATH,
            # 로컬 디스크에 데이터를 저장하는 Chroma client 생성
        ) 

        self.collection = self.client.get_or_create_collection(
            name=settings.CHROMA_COLLECTION_NAME
            #Collection은 Chroma 안에서 데이터를 담는 단위
            #RDB로 비유하면 약간 테이블 같은 느낌
            # Chroma DB
            # └── incident_chunks collection
            #     ├── chunk 1
            #     ├── chunk 2
            #     └── chunk 3
        )
    
    def count(self) -> int:
        return self.collection.count()
    
    def get_all(self):
        return self.collection.get()
    
    def search_similar_chunks(
        self,
        query_embedding: List[float],
        top_k: int,
    ):
        return self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )

    # chunk Chroma에 저장 
    def add_incident_chunks(
        self,
        incident_id: str,
        title: str,
        service: str,
        severity: Severity,
        chunks: List[DocumentChunk], #chunker가 만든 DocumentChunk 리스트
        embeddings: List[List[float]] #각 chunk content를 embedding한 벡터 리스트
    ) -> int:
        if not chunks:
            return 0
        
        if len(chunks) != len(embeddings):
            raise ValueError("chunk and embeddings length must be same")
        
        ids = []
        documents = []
        metadatas = []

        for chunk in chunks:
            chunk_id = f"{incident_id}--{chunk.chunk_index}"

            ids.append(chunk_id)
            documents.append(chunk.content)
            metadatas.append( #metadata는 나중에 검색 결과에서 출처로 사용됨
                {
                    "incident_id": incident_id,
                    "title": title,
                    "service": service,
                    "severity": severity.value,
                    "section": chunk.section,
                    "chunk_index": chunk.chunk_index
                }
            )

        self.collection.upsert( #없으면 새로 저장, 이미 같은 id가 있으면 덮어쓰기
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas
        )

        return len(chunks)
    