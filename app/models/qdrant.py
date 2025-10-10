from pydantic import BaseModel
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
