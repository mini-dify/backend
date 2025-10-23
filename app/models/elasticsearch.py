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


class DeleteIndexRequest(BaseModel):
    index_name: str = Field(
        ...,
        description="삭제할 인덱스 이름",
        example="my_index"
    )


class InsertDocumentRequest(BaseModel):
    index_name: str = Field(
        ...,
        description="문서를 삽입할 인덱스 이름",
        example="my_index"
    )
    document: Dict[str, Any] = Field(
        ...,
        description="삽입할 문서 데이터",
        example={
            "title": "FastAPI Tutorial",
            "content": "This is a tutorial about FastAPI...",
            "embedding": [0.1, 0.2, 0.3]
        }
    )
    doc_id: Optional[str] = Field(
        None,
        description="문서 ID (미제공 시 자동 생성)",
        example="doc_12345"
    )


class UpdateDocumentRequest(BaseModel):
    updated_fields: Dict[str, Any] = Field(
        ...,
        description="수정할 필드 데이터",
        example={
            "title": "Updated Title",
            "content": "Updated content..."
        }
    )


class SearchRequest(BaseModel):
    index_name: str = Field(
        ...,
        description="검색할 인덱스 이름",
        example="my_index"
    )
    query: Optional[Dict[str, Any]] = Field(
        None,
        description="ElasticSearch 쿼리 DSL (미제공 시 전체 조회)",
        example={
            "match": {
                "title": "FastAPI"
            }
        }
    )
    size: int = Field(
        10,
        description="반환할 최대 결과 수",
        example=10
    )
    from_: int = Field(
        0,
        alias="from",
        description="페이지네이션 시작 오프셋",
        example=0
    )


class BulkInsertRequest(BaseModel):
    index_name: str = Field(
        ...,
        description="문서를 삽입할 인덱스 이름",
        example="my_index"
    )
    documents: List[Dict[str, Any]] = Field(
        ...,
        description="삽입할 문서 목록",
        example=[
            {
                "title": "Document 1",
                "content": "Content 1...",
                "embedding": [0.1, 0.2, 0.3]
            },
            {
                "title": "Document 2",
                "content": "Content 2...",
                "embedding": [0.4, 0.5, 0.6]
            }
        ]
    )
