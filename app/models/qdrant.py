from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class CollectionConfig(BaseModel):
    name: str
    vector_size: int
    distance: str


class Point(BaseModel):
    id: str
    vector: List[float]
    payload: Optional[Dict[str, Any]] = None


class UpsertPoints(BaseModel):
    collection_name: str
    points: List[Point]


class SearchQuery(BaseModel):
    collection_name: str
    vector: List[float]
    limit: int = 10
    with_payload: bool = True

# === 추가: 대용량 임베딩/파일 추가용 모델 ===
class TextItem(BaseModel):
    id: Optional[str] = None
    text: str
    payload: Optional[Dict[str, Any]] = None

class EmbedTextRequest(BaseModel):
    collection_name: str
    embed_model: str = Field(..., description="예: minilm / qwen-32b-emb / openai-1536")
    items: List[TextItem]
    chunk_size: int = 800
    chunk_overlap: int = 100
    batch_size: int = 64

class FileIngestRequest(BaseModel):
    collection_name: str
    embed_model: str
    chunk_size: int = 800
    chunk_overlap: int = 100
    batch_size: int = 64
    sheet_name: Optional[str] = None
    text_columns: Optional[List[str]] = None  # ["title","content"] 같은 텍스트열 선택
    id_column: Optional[str] = None          # 행 고유 ID 컬럼명(없으면 자동생성)