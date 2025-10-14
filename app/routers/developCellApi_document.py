"""
지식 문서 업로드 API

역할:
- 문서를 청크로 분할
- Elasticsearch와 Qdrant에 동시 저장
"""

from fastapi import APIRouter, HTTPException, status, Body, Depends
from typing import Dict, Any, Optional
from ..services import es_document_service, qdrant_document_service
from ..db.database import get_qdrant_db
from qdrant_client import QdrantClient
from ..logging_config import get_logger
import os

logger = get_logger(__name__)
router = APIRouter()


@router.post(
    "/document/upload",
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

        # Step 1: 텍스트를 청크로 분할
        chunks = es_document_service.split_text_into_chunks(
            text=content,
            chunk_size=chunk_size,
            overlap=overlap
        )

        if not chunks:
            raise ValueError("No valid chunks created from content")

        logger.info(f"Created {len(chunks)} chunks")

        # Step 2: Elasticsearch에 저장 (원본 텍스트)
        es_chunk_ids = await es_document_service.save_chunks_to_elasticsearch(
            index_name="knowledge_base",
            title=title,
            chunks=chunks,
            metadata=metadata
        )

        # Step 3: Qdrant에 저장 (임베딩)
        qdrant_point_ids = await qdrant_document_service.save_chunks_to_qdrant(
            client=qdrant_client,
            collection_name="knowledge",
            title=title,
            chunks=chunks,
            metadata=metadata
        )

        return {
            "message": "Document uploaded successfully",
            "title": title,
            "total_chunks": len(chunks),
            "elasticsearch": {
                "index_name": "knowledge_base",
                "chunk_ids": es_chunk_ids
            },
            "qdrant": {
                "collection_name": "knowledge",
                "point_ids": qdrant_point_ids
            }
        }

    except Exception as e:
        logger.error(f"Failed to upload document: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to upload document: {str(e)}"
        )


@router.post(
    "/document/upload-file",
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
        content = await es_document_service.read_file_content(file_path)

        # 제목이 없으면 파일명 사용
        doc_title = title or os.path.basename(file_path)

        # 청크 분할
        chunks = es_document_service.split_text_into_chunks(
            text=content,
            chunk_size=chunk_size,
            overlap=overlap
        )

        if not chunks:
            raise ValueError("No valid chunks created from file content")

        # Elasticsearch 저장
        es_chunk_ids = await es_document_service.save_chunks_to_elasticsearch(
            index_name="knowledge_base",
            title=doc_title,
            chunks=chunks,
            metadata=metadata
        )

        # Qdrant 저장
        qdrant_point_ids = await qdrant_document_service.save_chunks_to_qdrant(
            client=qdrant_client,
            collection_name="knowledge",
            title=doc_title,
            chunks=chunks,
            metadata=metadata
        )

        return {
            "message": f"File '{file_path}' uploaded successfully",
            "title": doc_title,
            "total_chunks": len(chunks),
            "elasticsearch": {
                "index_name": "knowledge_base",
                "chunk_ids": es_chunk_ids
            },
            "qdrant": {
                "collection_name": "knowledge",
                "point_ids": qdrant_point_ids
            }
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
