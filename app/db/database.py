import motor.motor_asyncio
from typing import Optional

MONGO_DETAILS = "mongodb://mongodb:27017"

client: Optional[motor.motor_asyncio.AsyncIOMotorClient] = None

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