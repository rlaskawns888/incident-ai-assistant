import re
from typing import List

from app.schemas.chunk_schema import DocumentChunk

class IncidentDocumentChunker:
    SECTION_TITLES = [
        "장애 개요",
        "영향 범위",
        "원인 분석",
        "조치 내역",
        "재발 방지",
    ]

    def split(self, content: str) -> List[DocumentChunk]:
        nomalized_content = content.strip()

        if not nomalized_content:
            return []
        
        chunks = self._split_by_sections(nomalized_content)

        if chunks:
            return chunks

        return [
            DocumentChunk(
                chunk_index=0,
                section="전체",
                content=nomalized_content
            )
        ]
    
    def _split_by_sections(self, content: str) -> List[DocumentChunk]:
        section_pattern = "|".join(map(re.escape, self.SECTION_TITLES))

        pattern = re.compile(
            rf"(?P<section>{section_pattern})\s*[:：]\s*(?P<body>.*?)(?=\n\s*(?:{section_pattern})\s*[:：]|\Z)",
            re.DOTALL,
        )

        chunks: List[DocumentChunk] = []

        for index, match in enumerate(pattern.finditer(content)):
            section = match.group("section").strip()
            body = match.group("body").strip()

            if not body:
                continue
            
            chunks.append(
                DocumentChunk(
                    chunk_index=index,
                    section=section,
                    content=body,
                )
            )
        
        return chunks
