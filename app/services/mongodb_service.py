from ..db.database import get_client
from typing import List, Dict, Any, Optional
from bson import ObjectId

# Helper to convert ObjectId to string
def serialize_doc(doc):
    if "_id" in doc and isinstance(doc["_id"], ObjectId):
        doc["_id"] = str(doc["_id"])
    return doc

def convert_id_to_objectid(query_filter: Dict[str, Any]) -> Dict[str, Any]:
    if "_id" in query_filter and isinstance(query_filter["_id"], str):
        try:
            query_filter["_id"] = ObjectId(query_filter["_id"])
        except Exception:
            pass # Handle invalid ObjectId string if necessary
    return query_filter

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
    for doc in await cursor.to_list(length=100):
        documents.append(serialize_doc(doc))
    return documents

async def find_data_with_filter(db_name: str, collection_name: str, query_filter: Dict[str, Any]) -> List[Dict[str, Any]]:
    client = get_client()
    db = client[db_name]
    collection = db[collection_name]
    query_filter = convert_id_to_objectid(query_filter)
    cursor = collection.find(query_filter)
    documents = []
    for doc in await cursor.to_list(length=100):
        documents.append(serialize_doc(doc))
    return documents

async def find_data_by_id(db_name: str, collection_name: str, doc_id: str) -> Optional[Dict[str, Any]]:
    client = get_client()
    db = client[db_name]
    collection = db[collection_name]
    try:
        document = await collection.find_one({"_id": ObjectId(doc_id)})
        if document:
            return serialize_doc(document)
        return None
    except Exception:
        return None

async def update_data(db_name: str, collection_name: str, query_filter: Dict[str, Any], update_data: Dict[str, Any], upsert: bool = False, multi: bool = False) -> int:
    client = get_client()
    db = client[db_name]
    collection = db[collection_name]
    query_filter = convert_id_to_objectid(query_filter)
    if multi:
        result = await collection.update_many(query_filter, {"$set": update_data}, upsert=upsert)
    else:
        result = await collection.update_one(query_filter, {"$set": update_data}, upsert=upsert)
    return result.modified_count

async def delete_data_with_filter(db_name: str, collection_name: str, query_filter: Dict[str, Any]) -> int:
    client = get_client()
    db = client[db_name]
    collection = db[collection_name]
    query_filter = convert_id_to_objectid(query_filter)
    result = await collection.delete_many(query_filter)
    return result.deleted_count

async def delete_database(db_name: str):
    client = get_client()
    await client.drop_database(db_name)

async def delete_collection(db_name: str, collection_name: str):
    client = get_client()
    db = client[db_name]
    await db.drop_collection(collection_name)