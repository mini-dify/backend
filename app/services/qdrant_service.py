from qdrant_client import QdrantClient, models
from app.models.qdrant import CollectionConfig, UpsertPoints, SearchQuery
from typing import List


async def list_collections(client: QdrantClient) -> List[str]:
    collections_response = client.get_collections()
    return [collection.name for collection in collections_response.collections]


async def create_collection(client: QdrantClient, config: CollectionConfig):
    client.recreate_collection(
        collection_name=config.name,
        vectors_config=models.VectorParams(size=config.vector_size, distance=models.Distance[config.distance.upper()]),
    )
    return {"status": "Collection created successfully"}


async def upsert_points(client: QdrantClient, points_data: UpsertPoints):
    points = [models.PointStruct(id=p.id, vector=p.vector, payload=p.payload) for p in points_data.points]
    client.upsert(
        collection_name=points_data.collection_name,
        points=points,
        wait=True
    )
    return {"status": "Points upserted successfully"}


async def search_points(client: QdrantClient, query: SearchQuery):
    hits = client.search(
        collection_name=query.collection_name,
        query_vector=query.vector,
        limit=query.limit,
        with_payload=query.with_payload
    )
    return hits
