"""
Unified search service

Functions:
- Keyword search (Elasticsearch BM25)
- Vector search (Qdrant cosine similarity)
- Hybrid search (BM25 + cosine combined)
"""

from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from ..db.es_database import get_es_client
from ..services.developCellApi_service import get_embedding_from_lms
from ..models.developCellApi_model import EmbeddingRequest
from ..logging_config import get_logger

logger = get_logger(__name__)


# ============================================
# Keyword Search (Elasticsearch BM25)
# ============================================

async def keyword_search(
    query: str,
    top_k: int = 5,
    min_score: float = 0.0,
    index_name: str = "knowledge_base"
) -> List[Dict[str, Any]]:
    """
    Keyword-based search using Elasticsearch BM25

    Parameters:
        query: Search query
        top_k: Number of results to return
        min_score: Minimum BM25 score threshold
        index_name: Elasticsearch index name

    Returns:
        List of search results with BM25 scores
    """
    try:
        logger.info(f"Keyword search: '{query}' (top_k={top_k}, min_score={min_score})")

        client = get_es_client()

        response = await client.search(
            index=index_name,
            body={
                "query": {
                    "match": {
                        "content": query
                    }
                },
                "size": top_k,
                "min_score": min_score
            }
        )

        results = []
        max_score = response["hits"]["max_score"] or 1.0

        for hit in response["hits"]["hits"]:
            results.append({
                "doc_id": hit["_id"],
                "title": hit["_source"].get("title", ""),
                "content": hit["_source"]["content"],
                "chunk_index": hit["_source"].get("chunk_index", 0),
                "total_chunks": hit["_source"].get("total_chunks", 1),
                "bm25_score": hit["_score"],
                "normalized_bm25": hit["_score"] / max_score
            })

        logger.info(f"Keyword search returned {len(results)} results")
        return results

    except Exception as e:
        logger.error(f"Keyword search failed: {str(e)}")
        raise


# ============================================
# Vector Search (Qdrant Cosine Similarity)
# ============================================

async def vector_search(
    query: str,
    qdrant_client: QdrantClient,
    top_k: int = 5,
    min_score: float = 0.7,
    collection_name: str = "knowledge"
) -> List[Dict[str, Any]]:
    """
    Vector-based search using Qdrant cosine similarity

    Parameters:
        query: Search query
        qdrant_client: QdrantClient instance
        top_k: Number of results to return
        min_score: Minimum cosine similarity threshold (0~1)
        collection_name: Qdrant collection name

    Returns:
        List of search results with cosine similarity scores
    """
    try:
        logger.info(f"Vector search: '{query}' (top_k={top_k}, min_score={min_score})")

        # Step 1: Create query embedding
        embedding_response = await get_embedding_from_lms(
            EmbeddingRequest(input=query)
        )
        query_vector = embedding_response["data"][0]["embedding"]

        # Step 2: Search in Qdrant
        search_results = qdrant_client.search(
            collection_name=collection_name,
            query_vector=query_vector,
            limit=top_k,
            score_threshold=min_score
        )

        # Step 3: Format results
        results = []
        for hit in search_results:
            results.append({
                "doc_id": hit.id,
                "title": hit.payload.get("title", ""),
                "content": hit.payload["content"],
                "chunk_index": hit.payload.get("chunk_index", 0),
                "total_chunks": hit.payload.get("total_chunks", 1),
                "cosine_score": hit.score
            })

        logger.info(f"Vector search returned {len(results)} results")
        return results

    except Exception as e:
        logger.error(f"Vector search failed: {str(e)}")
        raise


# ============================================
# Hybrid Search (BM25 + Cosine)
# ============================================

async def hybrid_search(
    query: str,
    qdrant_client: QdrantClient,
    top_k: int = 5,
    keyword_weight: float = 0.3,
    vector_weight: float = 0.7,
    min_score: float = 0.5,
    index_name: str = "knowledge_base",
    collection_name: str = "knowledge"
) -> List[Dict[str, Any]]:
    """
    Hybrid search combining BM25 and cosine similarity

    Parameters:
        query: Search query
        qdrant_client: QdrantClient instance
        top_k: Number of results to return
        keyword_weight: Weight for BM25 score (0~1)
        vector_weight: Weight for cosine score (0~1)
        min_score: Minimum final score threshold
        index_name: Elasticsearch index name
        collection_name: Qdrant collection name

    Returns:
        List of search results with combined scores
    """
    try:
        logger.info(f"Hybrid search: '{query}' (top_k={top_k}, weights: BM25={keyword_weight}, Vector={vector_weight})")

        # Step 1: Get results from both sources
        keyword_results = await keyword_search(
            query=query,
            top_k=top_k * 2,  # Get more candidates
            min_score=0.0,
            index_name=index_name
        )

        vector_results = await vector_search(
            query=query,
            qdrant_client=qdrant_client,
            top_k=top_k * 2,
            min_score=0.0,  # No threshold here, filter later
            collection_name=collection_name
        )

        # Step 2: Combine scores
        combined_scores = {}

        # Process Elasticsearch results
        for result in keyword_results:
            doc_id = result["doc_id"]
            combined_scores[doc_id] = {
                "title": result["title"],
                "content": result["content"],
                "chunk_index": result["chunk_index"],
                "total_chunks": result["total_chunks"],
                "bm25_score": result["normalized_bm25"],
                "cosine_score": 0.0,
                "final_score": 0.0
            }

        # Process Qdrant results
        for result in vector_results:
            doc_id = result["doc_id"]

            if doc_id in combined_scores:
                # Document found in both
                combined_scores[doc_id]["cosine_score"] = result["cosine_score"]
            else:
                # Document only in Qdrant
                combined_scores[doc_id] = {
                    "title": result["title"],
                    "content": result["content"],
                    "chunk_index": result["chunk_index"],
                    "total_chunks": result["total_chunks"],
                    "bm25_score": 0.0,
                    "cosine_score": result["cosine_score"],
                    "final_score": 0.0
                }

        # Step 3: Calculate final scores
        for doc_id in combined_scores:
            doc = combined_scores[doc_id]
            doc["final_score"] = (
                doc["bm25_score"] * keyword_weight +
                doc["cosine_score"] * vector_weight
            )

        # Step 4: Sort and filter
        ranked_results = sorted(
            combined_scores.items(),
            key=lambda x: x[1]["final_score"],
            reverse=True
        )

        filtered_results = [
            {
                "doc_id": doc_id,
                "title": data["title"],
                "content": data["content"],
                "chunk_index": data["chunk_index"],
                "total_chunks": data["total_chunks"],
                "bm25_score": data["bm25_score"],
                "cosine_score": data["cosine_score"],
                "final_score": data["final_score"]
            }
            for doc_id, data in ranked_results
            if data["final_score"] >= min_score
        ]

        results = filtered_results[:top_k]

        logger.info(f"Hybrid search returned {len(results)} results")
        return results

    except Exception as e:
        logger.error(f"Hybrid search failed: {str(e)}")
        raise
