"""
지식 문서 업로드 API

역할:
- 문서를 청크로 분할
- Elasticsearch와 Qdrant에 동시 저장
"""

from fastapi import APIRouter, HTTPException, status, Body, Depends, Query
from typing import Dict, Any, Optional, List
from ..services import document_service, es_service
from ..db.database import get_qdrant_db
from qdrant_client import QdrantClient
from ..logging_config import get_logger
import os

logger = get_logger(__name__)
router = APIRouter()


@router.post(
    "/upload",
    status_code=status.HTTP_201_CREATED,
    summary="지식 문서 업로드",
    description="문서를 청크로 분할하여 Elasticsearch와 Qdrant에 동시 저장합니다."
)
async def upload_knowledge_document(
    title: str = Body(..., description="문서 제목"),
    content: str = Body(..., description="문서 내용"),
    metadata: Optional[Dict[str, Any]] = Body(None, description="추가 메타데이터"),
    chunk_size: int = Body(500, description="청크 크기 (글자 수)"),
    overlap: int = Body(50, description="청크 간 겹침 (글자 수)"),
    qdrant_client: QdrantClient = Depends(get_qdrant_db)
):
    """
    지식 문서를 업로드하여 Elasticsearch와 Qdrant에 저장

    프로세스:
    1. 텍스트를 청크로 분할
    2. Elasticsearch에 원본 텍스트 저장 (키워드 검색용)
    3. Qdrant에 임베딩 저장 (벡터 검색용)
    """
    try:
        logger.info(f"Received document upload request: '{title}'")

        result = await document_service.save_document(
            title=title,
            content=content,
            qdrant_client=qdrant_client,
            metadata=metadata,
            chunk_size=chunk_size,
            overlap=overlap
        )

        return {
            "message": "Document uploaded successfully",
            **result
        }

    except Exception as e:
        logger.error(f"Failed to upload document: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to upload document: {str(e)}"
        )


@router.post(
    "/upload-file",
    status_code=status.HTTP_201_CREATED,
    summary="파일로 지식 문서 업로드",
    description="파일 경로를 받아 텍스트를 읽고 Elasticsearch와 Qdrant에 저장합니다."
)
async def upload_knowledge_from_file(
    file_path: str = Body(..., description="파일 경로 (예: file/test_script.txt)"),
    title: Optional[str] = Body(None, description="문서 제목 (없으면 파일명 사용)"),
    metadata: Optional[Dict[str, Any]] = Body(None, description="추가 메타데이터"),
    chunk_size: int = Body(500, description="청크 크기"),
    overlap: int = Body(50, description="청크 겹침"),
    qdrant_client: QdrantClient = Depends(get_qdrant_db)
):
    """
    파일 경로를 받아 지식 문서로 저장

    예시:
        file_path: "file/test_script.txt"
        title: "테스트 문서"
    """
    try:
        logger.info(f"Reading file: {file_path}")

        # 파일 읽기
        content = await document_service.read_file_content(file_path)

        # 제목이 없으면 파일명 사용
        doc_title = title or os.path.basename(file_path)

        # 문서 저장
        result = await document_service.save_document(
            title=doc_title,
            content=content,
            qdrant_client=qdrant_client,
            metadata=metadata,
            chunk_size=chunk_size,
            overlap=overlap
        )

        return {
            "message": f"File '{file_path}' uploaded successfully",
            **result
        }

    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File not found: {file_path}"
        )
    except Exception as e:
        logger.error(f"Failed to upload file: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to upload file: {str(e)}"
        )


@router.get(
    "/list",
    summary="저장된 문서 목록 조회",
    description="Elasticsearch와 Qdrant에 저장된 문서들을 조회합니다."
)
async def list_documents(
    title: Optional[str] = Query(None, description="문서 제목으로 필터링"),
    limit: int = Query(10, description="조회할 문서 수"),
    qdrant_client: QdrantClient = Depends(get_qdrant_db)
):
    """
    저장된 문서 목록 조회
    """
    try:
        # Elasticsearch에서 문서 조회
        if title:
            query = {"match": {"title": title}}
        else:
            query = {"match_all": {}}

        es_docs = await es_service.search_documents(
            index_name="knowledge_base",
            query=query,
            size=limit
        )

        # Qdrant에서 포인트 조회
        qdrant_points = qdrant_client.scroll(
            collection_name="knowledge",
            limit=limit,
            with_payload=True,
            with_vectors=False
        )

        return {
            "elasticsearch": {
                "total": len(es_docs),
                "documents": es_docs
            },
            "qdrant": {
                "total": len(qdrant_points[0]),
                "points": [
                    {
                        "id": point.id,
                        "payload": point.payload
                    }
                    for point in qdrant_points[0]
                ]
            }
        }

    except Exception as e:
        logger.error(f"Failed to list documents: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to list documents: {str(e)}"
        )


@router.get(
    "/stats",
    summary="문서 통계",
    description="저장된 문서의 통계 정보를 조회합니다."
)
async def get_document_stats(
    qdrant_client: QdrantClient = Depends(get_qdrant_db)
):
    """
    문서 통계 정보 조회
    """
    try:
        # Elasticsearch 통계
        es_stats = await es_service.search_documents(
            index_name="knowledge_base",
            query={"match_all": {}},
            size=0  # 카운트만
        )

        # Qdrant 통계
        qdrant_info = qdrant_client.get_collection(collection_name="knowledge")

        return {
            "elasticsearch": {
                "index_name": "knowledge_base",
                "total_documents": len(es_stats)
            },
            "qdrant": {
                "collection_name": "knowledge",
                "points_count": qdrant_info.points_count,
                "vector_size": qdrant_info.config.params.vectors.size
            }
        }

    except Exception as e:
        logger.error(f"Failed to get stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to get stats: {str(e)}"
        )
