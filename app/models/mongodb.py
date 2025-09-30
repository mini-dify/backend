from pydantic import BaseModel

class CreateCollectionRequest(BaseModel):
    db_name: str
    collection_name: str

class CreateDatabaseRequest(BaseModel):
    db_name: str