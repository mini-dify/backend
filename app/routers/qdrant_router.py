from fastapi import APIRouter, Depends, HTTPException
from qdrant_client import QdrantClient
from app.db.database import get_qdrant_db
from app.models.qdrant import CollectionConfig, UpsertPoints, SearchQuery
from app.services import qdrant_service
from typing import List

router = APIRouter()


@router.get(
    "/qdrant/collections",
    response_model=List[str],
    summary="Qdrant 컬렉션 목록 조회",
    description="Qdrant에 존재하는 모든 컬렉션의 이름을 조회합니다."
)
async def handle_list_collections(client: QdrantClient = Depends(get_qdrant_db)):
    try:
        return await qdrant_service.list_collections(client)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/qdrant/collections",
    status_code=201,
    summary="Qdrant 컬렉션 생성",
    description="Qdrant에 새로운 벡터 컬렉션을 생성합니다.\n"
                "- **Embedding Model:** `qwen/qwen2.5-embedding-32b`- **Vector Size:** `4096`"
                "- **Distance:Cosine"
)
async def handle_create_collection(config: CollectionConfig, client: QdrantClient = Depends(get_qdrant_db)):
    try:
        return await qdrant_service.create_collection(client, config)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/qdrant/points/upsert",
    summary="Qdrant 포인트 추가/수정",
    description="지정된 컬렉션에 벡터 포인트(데이터)를 추가하거나 업데이트합니다."
)
async def handle_upsert_points(points_data: UpsertPoints, client: QdrantClient = Depends(get_qdrant_db)):
    try:
        return await qdrant_service.upsert_points(client, points_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/qdrant/points/search",
    summary="Qdrant 포인트 검색",
    description="지정된 컬렉션에서 쿼리 벡터와 유사한 벡터 포인트를 검색합니다."
)
async def handle_search_points(query: SearchQuery, client: QdrantClient = Depends(get_qdrant_db)):
    try:
        return await qdrant_service.search_points(client, query)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
