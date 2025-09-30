from ..db.database import get_client
from typing import List, Dict, Any
from bson import ObjectId

# Helper to convert ObjectId to string
def serialize_doc(doc):
    doc["_id"] = str(doc["_id"])
    return doc

async def list_database_names() -> List[str]:
    client = get_client()
    return await client.list_database_names()

async def create_collection(db_name: str, collection_name: str):
    client = get_client()
    db = client[db_name]
    await db.create_collection(collection_name)

async def create_database(db_name: str):
    client = get_client()
    db = client[db_name]
    await db.create_collection("_placeholder")

async def list_collections(db_name: str) -> List[str]:
    client = get_client()
    db = client[db_name]
    return await db.list_collection_names()

async def insert_data(db_name: str, collection_name: str, data: Dict[str, Any]) -> str:
    client = get_client()
    db = client[db_name]
    collection = db[collection_name]
    result = await collection.insert_one(data)
    return str(result.inserted_id)

async def find_data(db_name: str, collection_name: str) -> List[Dict[str, Any]]:
    client = get_client()
    db = client[db_name]
    collection = db[collection_name]
    cursor = collection.find()
    documents = []
    for doc in await cursor.to_list(length=100): # limit to 100 documents for now
        documents.append(serialize_doc(doc))
    return documents
