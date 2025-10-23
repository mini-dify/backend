from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import Dict, Any, Optional, List
from ..services import document_service, es_service
from ..db.database import get_qdrant_db
from ..models.document import UploadDocumentRequest, UploadFileRequest
from qdrant_client import QdrantClient
from ..logging_config import get_logger
import os

logger = get_logger(__name__)
router = APIRouter()


@router.post(
    "/upload",
    status_code=status.HTTP_201_CREATED,
    summary="지식 문서 업로드",
    description="문서를 청크로 분할하여 Elasticsearch와 Qdrant에 동시 저장합니다.",
    responses={
        201: {
            "description": "문서 업로드 성공",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Document uploaded successfully",
                        "document_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                        "title": "제미니 회사 규정",
                        "total_chunks": 5,
                        "elasticsearch": {
                            "original_index": "knowledge_base_original",
                            "chunks_index": "knowledge_base",
                            "chunk_ids": ["es_id_1", "es_id_2", "es_id_3", "es_id_4", "es_id_5"]
                        },
                        "qdrant": {
                            "collection_name": "knowledge",
                            "point_ids": ["qd_id_1", "qd_id_2", "qd_id_3", "qd_id_4", "qd_id_5"]
                        }
                    }
                }
            }
        }
    }
)
async def upload_knowledge_document(
    request: UploadDocumentRequest,
    qdrant_client: QdrantClient = Depends(get_qdrant_db)
):
    try:
        logger.info(f"Received document upload request: '{request.title}'")
        result = await document_service.save_document(
            title=request.title,
            content=request.content,
            qdrant_client=qdrant_client,
            chunk_size=request.chunk_size,
            overlap=request.overlap
        )
        return {
            "message": "Document uploaded successfully",
            **result
        }
    except Exception as e:
        logger.error(f"Failed to upload document: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/upload-file",
    status_code=status.HTTP_201_CREATED,
    summary="파일로 지식 문서 업로드",
    description="파일 경로를 받아 텍스트를 읽고 Elasticsearch와 Qdrant에 저장합니다.",
    responses={
        201: {
            "description": "파일 업로드 성공",
            "content": {
                "application/json": {
                    "example": {
                        "message": "File 'file/test_script.txt' uploaded successfully",
                        "document_id": "b2c3d4e5-f6g7-8901-bcde-fg2345678901",
                        "title": "test_script.txt",
                        "total_chunks": 3,
                        "elasticsearch": {
                            "original_index": "knowledge_base_original",
                            "chunks_index": "knowledge_base",
                            "chunk_ids": ["es_id_1", "es_id_2", "es_id_3"]
                        },
                        "qdrant": {
                            "collection_name": "knowledge",
                            "point_ids": ["qd_id_1", "qd_id_2", "qd_id_3"]
                        }
                    }
                }
            }
        }
    }
)
async def upload_knowledge_from_file(
    request: UploadFileRequest,
    qdrant_client: QdrantClient = Depends(get_qdrant_db)
):
    try:
        logger.info(f"Reading file: {request.file_path}")
        content = await document_service.read_file_content(request.file_path)
        doc_title = request.title or os.path.basename(request.file_path)
        result = await document_service.save_document(
            title=doc_title,
            content=content,
            qdrant_client=qdrant_client,
            chunk_size=request.chunk_size,
            overlap=request.overlap
        )
        return {
            "message": f"File '{request.file_path}' uploaded successfully",
            **result
        }
    except FileNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"File not found: {request.file_path}")
    except Exception as e:
        logger.error(f"Failed to upload file: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/list",
    summary="저장된 문서 목록 조회",
    description="Elasticsearch와 Qdrant에 저장된 문서들을 조회합니다.",
    responses={
        200: {
            "description": "문서 목록 조회 성공",
            "content": {
                "application/json": {
                    "example": {
                        "elasticsearch": {
                            "total": 2,
                            "documents": [
                                {
                                    "_id": "es_chunk_id_1",
                                    "_source": {
                                        "document_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                                        "title": "제미니 회사 규정",
                                        "content": "제미니 회사의 근무 시간은...",
                                        "chunk_index": 0,
                                        "total_chunks": 5,
                                        "created_at": "2025-10-22T10:30:00"
                                    }
                                }
                            ]
                        },
                        "qdrant": {
                            "total": 2,
                            "points": [
                                {
                                    "id": "qd_point_id_1",
                                    "payload": {
                                        "document_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                                        "title": "제미니 회사 규정",
                                        "content": "제미니 회사의 근무 시간은...",
                                        "chunk_index": 0,
                                        "total_chunks": 5
                                    }
                                }
                            ]
                        }
                    }
                }
            }
        }
    }
)
async def list_documents(
    title: Optional[str] = Query(None, description="문서 제목으로 필터링", example="제미니 회사 규정"),
    limit: int = Query(10, description="조회할 문서 수", example=10),
    qdrant_client: QdrantClient = Depends(get_qdrant_db)
):
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
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/stats",
    summary="문서 통계",
    description="저장된 문서의 통계 정보를 조회합니다.",
    responses={
        200: {
            "description": "문서 통계 조회 성공",
            "content": {
                "application/json": {
                    "example": {
                        "elasticsearch": {
                            "index_name": "knowledge_base",
                            "total_documents": 25
                        },
                        "qdrant": {
                            "collection_name": "knowledge",
                            "points_count": 25,
                            "vector_size": 4096
                        }
                    }
                }
            }
        }
    }
)
async def get_document_stats(
    qdrant_client: QdrantClient = Depends(get_qdrant_db)
):
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
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
