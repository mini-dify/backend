from pydantic import BaseModel
from typing import Dict, Any, Optional, List


class CreateIndexRequest(BaseModel):
    index_name: str
    mappings: Optional[Dict[str, Any]] = None
    number_of_shards: int = 3
    number_of_replicas: int = 1


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
