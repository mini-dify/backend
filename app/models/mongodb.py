from pydantic import BaseModel
from typing import Dict, Any, Optional

class CreateCollectionRequest(BaseModel):
    db_name: str
    collection_name: str

class CreateDatabaseRequest(BaseModel):
    db_name: str

class UpdateDataRequest(BaseModel):
    query_filter: Dict[str, Any]
    update_data: Dict[str, Any]
    upsert: bool = False
    multi: bool = False

class DeleteDataWithFilterRequest(BaseModel):
    query_filter: Dict[str, Any]
