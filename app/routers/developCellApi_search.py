"""
Search API endpoints

Provides:
- Keyword search (Elasticsearch BM25)
- Vector search (Qdrant cosine similarity)
- Hybrid search (BM25 + cosine combined)
"""

from fastapi import APIRouter, HTTPException, status, Body, Depends
from typing import Dict, Any, Optional
from ..services import search_service
from ..db.database import get_qdrant_db
from qdrant_client import QdrantClient
from ..logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.post(
    "/search/keyword",
    summary="키워드 검색 (BM25)",
    description="Elasticsearch BM25 알고리즘을 사용한 키워드 기반 검색입니다."
)
async def search_by_keyword(
    query: str = Body(..., description="검색 질문"),
    top_k: int = Body(5, description="반환할 문서 수", ge=1, le=20),
    min_score: float = Body(0.0, description="최소 BM25 점수", ge=0.0)
):
    """
    Keyword-based search using BM25

    Example:
        {
            "query": "제미니 회사 근무 시간",
            "top_k": 5,
            "min_score": 0.0
        }
    """
    try:
        logger.info(f"Keyword search request: '{query}'")

        results = await search_service.keyword_search(
            query=query,
            top_k=top_k,
            min_score=min_score
        )

        return {
            "search_type": "keyword",
            "query": query,
            "total_results": len(results),
            "results": results
        }

    except Exception as e:
        logger.error(f"Keyword search failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Keyword search failed: {str(e)}"
        )


@router.post(
    "/search/vector",
    summary="벡터 검색 (코사인 유사도)",
    description="Qdrant를 사용한 벡터 기반 의미적 검색입니다."
)
async def search_by_vector(
    query: str = Body(..., description="검색 질문"),
    top_k: int = Body(5, description="반환할 문서 수", ge=1, le=20),
    min_score: float = Body(0.7, description="최소 코사인 유사도 (0~1)", ge=0.0, le=1.0),
    qdrant_client: QdrantClient = Depends(get_qdrant_db)
):
    """
    Vector-based search using cosine similarity

    Example:
        {
            "query": "제미니 회사 근무 시간",
            "top_k": 5,
            "min_score": 0.7
        }
    """
    try:
        logger.info(f"Vector search request: '{query}'")

        results = await search_service.vector_search(
            query=query,
            qdrant_client=qdrant_client,
            top_k=top_k,
            min_score=min_score
        )

        return {
            "search_type": "vector",
            "query": query,
            "total_results": len(results),
            "results": results
        }

    except Exception as e:
        logger.error(f"Vector search failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Vector search failed: {str(e)}"
        )


@router.post(
    "/search/hybrid",
    summary="하이브리드 검색 (BM25 + 코사인)",
    description="키워드 검색과 벡터 검색을 결합한 하이브리드 검색입니다."
)
async def search_by_hybrid(
    query: str = Body(..., description="검색 질문"),
    top_k: int = Body(5, description="반환할 문서 수", ge=1, le=20),
    keyword_weight: float = Body(0.3, description="키워드 검색 가중치 (0~1)", ge=0.0, le=1.0),
    vector_weight: float = Body(0.7, description="벡터 검색 가중치 (0~1)", ge=0.0, le=1.0),
    min_score: float = Body(0.5, description="최소 최종 점수 (0~1)", ge=0.0, le=1.0),
    qdrant_client: QdrantClient = Depends(get_qdrant_db)
):
    """
    Hybrid search combining BM25 and cosine similarity

    Example:
        {
            "query": "제미니 회사 근무 시간",
            "top_k": 5,
            "keyword_weight": 0.3,
            "vector_weight": 0.7,
            "min_score": 0.5
        }
    """
    try:
        # Validate weights
        if abs(keyword_weight + vector_weight - 1.0) > 0.01:
            raise ValueError("keyword_weight + vector_weight must equal 1.0")

        logger.info(f"Hybrid search request: '{query}' (weights: BM25={keyword_weight}, Vector={vector_weight})")

        results = await search_service.hybrid_search(
            query=query,
            qdrant_client=qdrant_client,
            top_k=top_k,
            keyword_weight=keyword_weight,
            vector_weight=vector_weight,
            min_score=min_score
        )

        return {
            "search_type": "hybrid",
            "query": query,
            "weights": {
                "keyword": keyword_weight,
                "vector": vector_weight
            },
            "total_results": len(results),
            "results": results
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Hybrid search failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Hybrid search failed: {str(e)}"
        )


@router.post(
    "/search/compare",
    summary="검색 방법 비교",
    description="키워드, 벡터, 하이브리드 검색 결과를 한 번에 비교합니다."
)
async def compare_search_methods(
    query: str = Body(..., description="검색 질문"),
    top_k: int = Body(5, description="각 방법별 반환할 문서 수", ge=1, le=20),
    qdrant_client: QdrantClient = Depends(get_qdrant_db)
):
    """
    Compare all three search methods

    Example:
        {
            "query": "제미니 회사 근무 시간",
            "top_k": 5
        }
    """
    try:
        logger.info(f"Compare search request: '{query}'")

        # Run all three searches
        keyword_results = await search_service.keyword_search(
            query=query,
            top_k=top_k,
            min_score=0.0
        )

        vector_results = await search_service.vector_search(
            query=query,
            qdrant_client=qdrant_client,
            top_k=top_k,
            min_score=0.0
        )

        hybrid_results = await search_service.hybrid_search(
            query=query,
            qdrant_client=qdrant_client,
            top_k=top_k,
            keyword_weight=0.3,
            vector_weight=0.7,
            min_score=0.0
        )

        return {
            "query": query,
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
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Compare search failed: {str(e)}"
        )
