import motor.motor_asyncio
from typing import Optional
from qdrant_client import QdrantClient
from app.config import settings

MONGO_DETAILS = "mongodb://mongodb:27017"

client: Optional[motor.motor_asyncio.AsyncIOMotorClient] = None
qdrant_client: Optional[QdrantClient] = None


def get_client() -> motor.motor_asyncio.AsyncIOMotorClient:
    global client
    if client is None:
        client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_DETAILS)
    return client


def get_database() -> motor.motor_asyncio.AsyncIOMotorDatabase:
    return get_client().get_database("mini_dify")


def close_mongo_connection():
    global client
    if client:
        client.close()
        client = None


def get_qdrant_db() -> QdrantClient:
    global qdrant_client
    if qdrant_client is None:
        qdrant_client = QdrantClient(
            url=settings.QDRANT_URL,
            api_key=settings.QDRANT_API_KEY,
        )
    return qdrant_client
