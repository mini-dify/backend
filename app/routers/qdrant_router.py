from fastapi import APIRouter, Depends, HTTPException
from qdrant_client import QdrantClient
from app.db.database import get_qdrant_db
from app.models.qdrant import CollectionConfig, UpsertPoints, SearchQuery
from app.services import qdrant_service

router = APIRouter()


@router.post("/qdrant/collections", status_code=201)
async def handle_create_collection(config: CollectionConfig, client: QdrantClient = Depends(get_qdrant_db)):
    try:
        return await qdrant_service.create_collection(client, config)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/qdrant/points/upsert")
async def handle_upsert_points(points_data: UpsertPoints, client: QdrantClient = Depends(get_qdrant_db)):
    try:
        return await qdrant_service.upsert_points(client, points_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/qdrant/points/search")
async def handle_search_points(query: SearchQuery, client: QdrantClient = Depends(get_qdrant_db)):
    try:
        return await qdrant_service.search_points(client, query)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
