from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List


class CreateIndexRequest(BaseModel):
    index_name: str = Field(
        ...,
        description="생성할 인덱스 이름",
        example="my_index"
    )
    number_of_shards: int = Field(
        3,
        description="Primary Shard 개수 (기본값: 3, 최소값: 1)",
        example=3
    )
    number_of_replicas: int = Field(
        1,
        description="Replica Shard 개수 (기본값: 1, 최소값: 0, 권장 최대값: 2)",
        example=1
    )


class InsertDocumentRequest(BaseModel):
    index_name: str
    document: Dict[str, Any]
    doc_id: Optional[str] = None


class UpdateDocumentRequest(BaseModel):
    updated_fields: Dict[str, Any]


class SearchRequest(BaseModel):
    index_name: str
    query: Optional[Dict[str, Any]] = None
    size: int = 10
    from_: int = 0


class BulkInsertRequest(BaseModel):
    index_name: str
    documents: List[Dict[str, Any]]
