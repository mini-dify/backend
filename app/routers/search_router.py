from fastapi import APIRouter, HTTPException, status, Depends
from typing import Dict, Any, Optional
from ..services import search_service
from ..db.database import get_qdrant_db
from ..models.search import (
    KeywordSearchRequest,
    VectorSearchRequest,
    HybridSearchRequest,
    CompareSearchRequest
)
from qdrant_client import QdrantClient
from ..logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.post(
    "/keyword",
    summary="키워드 검색 (BM25)",
    description="Elasticsearch BM25 알고리즘을 사용한 키워드 기반 검색입니다."
)
async def search_by_keyword(request: KeywordSearchRequest):
    try:
        logger.info(f"Keyword search request: '{request.query}'")
        results = await search_service.keyword_search(
            query=request.query,
            top_k=request.top_k,
            min_score=request.min_score
        )
        return {
            "search_type": "keyword",
            "query": request.query,
            "total_results": len(results),
            "results": results
        }
    except Exception as e:
        logger.error(f"Keyword search failed: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/vector",
    summary="벡터 검색 (코사인 유사도)",
    description="Qdrant를 사용한 벡터 기반 의미적 검색입니다."
)
async def search_by_vector(
    request: VectorSearchRequest,
    qdrant_client: QdrantClient = Depends(get_qdrant_db)
):
    try:
        logger.info(f"Vector search request: '{request.query}'")
        results = await search_service.vector_search(
            query=request.query,
            qdrant_client=qdrant_client,
            top_k=request.top_k,
            min_score=request.min_score
        )
        return {
            "search_type": "vector",
            "query": request.query,
            "total_results": len(results),
            "results": results
        }
    except Exception as e:
        logger.error(f"Vector search failed: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/hybrid",
    summary="하이브리드 검색 (BM25 + 코사인)",
    description="키워드 검색과 벡터 검색을 결합한 하이브리드 검색입니다."
)
async def search_by_hybrid(
    request: HybridSearchRequest,
    qdrant_client: QdrantClient = Depends(get_qdrant_db)
):
    try:
        if abs(request.keyword_weight + request.vector_weight - 1.0) > 0.01:
            raise ValueError("keyword_weight + vector_weight must equal 1.0")

        logger.info(f"Hybrid search request: '{request.query}' (weights: BM25={request.keyword_weight}, Vector={request.vector_weight})")
        results = await search_service.hybrid_search(
            query=request.query,
            qdrant_client=qdrant_client,
            top_k=request.top_k,
            keyword_weight=request.keyword_weight,
            vector_weight=request.vector_weight,
            min_score=request.min_score
        )
        return {
            "search_type": "hybrid",
            "query": request.query,
            "weights": {
                "keyword": request.keyword_weight,
                "vector": request.vector_weight
            },
            "total_results": len(results),
            "results": results
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Hybrid search failed: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/compare",
    summary="검색 방법 비교",
    description="키워드, 벡터, 하이브리드 검색 결과를 한 번에 비교합니다."
)
async def compare_search_methods(
    request: CompareSearchRequest,
    qdrant_client: QdrantClient = Depends(get_qdrant_db)
):
    try:
        logger.info(f"Compare search request: '{request.query}'")
        keyword_results = await search_service.keyword_search(
            query=request.query,
            top_k=request.top_k,
            min_score=0.0
        )
        vector_results = await search_service.vector_search(
            query=request.query,
            qdrant_client=qdrant_client,
            top_k=request.top_k,
            min_score=0.0
        )
        hybrid_results = await search_service.hybrid_search(
            query=request.query,
            qdrant_client=qdrant_client,
            top_k=request.top_k,
            keyword_weight=0.3,
            vector_weight=0.7,
            min_score=0.0
        )
        return {
            "query": request.query,
            "keyword": {
                "total_results": len(keyword_results),
                "results": keyword_results
            },
            "vector": {
                "total_results": len(vector_results),
                "results": vector_results
            },
            "hybrid": {
                "total_results": len(hybrid_results),
                "results": hybrid_results
            }
        }
    except Exception as e:
        logger.error(f"Compare search failed: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
