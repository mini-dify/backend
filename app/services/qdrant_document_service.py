"""
Qdrant 지식 문서 저장 서비스

역할:
- 청크를 임베딩으로 변환
- Qdrant에 벡터 저장 (의미적 검색용)
"""

from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct
from ..services.developCellApi_service import get_embedding_from_lms
from ..models.developCellApi_model import EmbeddingRequest
from ..logging_config import get_logger
import uuid

logger = get_logger(__name__)


async def create_embeddings_batch(texts: List[str]) -> List[List[float]]:
    """
    여러 텍스트를 임베딩으로 변환

    Parameters:
        texts: 임베딩할 텍스트 리스트

    Returns:
        임베딩 벡터 리스트 (각 벡터는 4096차원)
    """
    try:
        logger.info(f"Creating embeddings for {len(texts)} texts")

        # Qwen 임베딩 API 호출
        response = await get_embedding_from_lms(
            EmbeddingRequest(input=texts)
        )

        # 응답에서 임베딩 벡터 추출
        embeddings = [item["embedding"] for item in response["data"]]

        logger.info(f"Successfully created {len(embeddings)} embeddings")
        return embeddings

    except Exception as e:
        logger.error(f"Failed to create embeddings: {str(e)}")
        raise


async def save_chunks_to_qdrant(
    client: QdrantClient,
    collection_name: str,
    title: str,
    chunks: List[str],
    metadata: Optional[Dict[str, Any]] = None
) -> List[str]:
    """
    청크들을 Qdrant에 저장 (임베딩 생성 후)

    Parameters:
        client: QdrantClient 인스턴스
        collection_name: Qdrant 컬렉션 이름
        title: 문서 제목
        chunks: 저장할 청크 리스트
        metadata: 추가 메타데이터

    Returns:
        저장된 포인트 ID 리스트
    """
    try:
        logger.info(f"Saving {len(chunks)} chunks to Qdrant collection '{collection_name}'")

        # Step 1: 모든 청크의 임베딩 생성
        embeddings = await create_embeddings_batch(chunks)

        # Step 2: Qdrant에 저장할 포인트 생성
        points = []
        point_ids = []

        for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            point_id = str(uuid.uuid4())  # 고유 ID 생성

            point = PointStruct(
                id=point_id,
                vector=embedding,
                payload={
                    "title": title,
                    "content": chunk,
                    "chunk_index": idx,
                    "total_chunks": len(chunks),
                    "metadata": metadata or {}
                }
            )

            points.append(point)
            point_ids.append(point_id)

        # Step 3: Qdrant에 배치 저장
        client.upsert(
            collection_name=collection_name,
            points=points,
            wait=True
        )

        logger.info(f"Successfully saved {len(chunks)} chunks to Qdrant")
        return point_ids

    except Exception as e:
        logger.error(f"Failed to save chunks to Qdrant: {str(e)}")
        raise
