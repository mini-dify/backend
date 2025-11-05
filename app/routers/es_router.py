from fastapi import APIRouter, status, HTTPException, Query, Body, Path
from typing import List, Dict, Any, Optional
from ..services import es_service
from ..models.elasticsearch import (
    CreateIndexRequest,
    DeleteIndexRequest,
    InsertDocumentRequest,
    UpdateDocumentRequest,
    SearchRequest,
    BulkInsertRequest
)
from elasticsearch import NotFoundError
from ..logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.get(
    "/indices",
    response_model=List[str],
    summary="인덱스 목록 조회",
    description="Elasticsearch에 존재하는 모든 인덱스의 이름을 조회합니다."
)
async def get_indices():
    logger.debug("Fetching Elasticsearch indices list")
    indices = await es_service.list_indices()
    logger.debug(f"Successfully fetched {len(indices)} indices")
    return indices


@router.post(
    "/indices",
    status_code=status.HTTP_201_CREATED,
    summary="인덱스 생성",
    description="새로운 Elasticsearch 인덱스를 생성합니다. 고정된 스키마(title, content, embedding)로 생성되며, 샤드와 레플리카 개수를 지정할 수 있습니다."
)
async def create_index(request: CreateIndexRequest):
    try:
        logger.info(
            f"Creating index: {request.index_name} with "
            f"shards: {request.number_of_shards}, replicas: {request.number_of_replicas}"
        )
        response = await es_service.create_index(
            index_name=request.index_name,
            number_of_shards=request.number_of_shards,
            number_of_replicas=request.number_of_replicas
        )
        logger.info(f"Successfully created index: {request.index_name}")
        return {
            "message": f"Index '{request.index_name}' created successfully with fixed schema (title, content, embedding).",
            "settings": {
                "number_of_shards": request.number_of_shards,
                "number_of_replicas": request.number_of_replicas
            },
            "schema": {
                "title": "text",
                "content": "text",
                "embedding": "dense_vector (768 dims, cosine similarity)"
            },
            "response": response
        }
    except ValueError as e:
        logger.error(f"Validation error for index {request.index_name}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create index {request.index_name}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete(
    "/indices",
    status_code=status.HTTP_200_OK,
    summary="인덱스 삭제",
    description="지정된 Elasticsearch 인덱스를 삭제합니다."
)
async def delete_index(request: DeleteIndexRequest):
    try:
        logger.info(f"Deleting index: {request.index_name}")
        response = await es_service.delete_index(request.index_name)
        logger.info(f"Successfully deleted index: {request.index_name}")
        return {"message": f"Index '{request.index_name}' deleted successfully.", "response": response}
    except NotFoundError:
        logger.warning(f"Index not found: {request.index_name}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Index '{request.index_name}' not found.")
    except Exception as e:
        logger.error(f"Failed to delete index {request.index_name}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/documents",
    status_code=status.HTTP_201_CREATED,
    summary="문서 삽입",
    description="지정된 인덱스에 새로운 문서를 삽입합니다. 문서 ID는 선택 사항이며, 미제공 시 자동 생성됩니다."
)
async def insert_document(request: InsertDocumentRequest):
    try:
        logger.info(f"Inserting document into index: {request.index_name}, doc_id: {request.doc_id}")
        inserted_id = await es_service.insert_document(request.index_name, request.document, request.doc_id)
        logger.info(f"Successfully inserted document with ID: {inserted_id}")
        return {"message": "Document inserted successfully.", "id": inserted_id}
    except Exception as e:
        logger.error(f"Failed to insert document into {request.index_name}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/documents/{index_name}/{doc_id}",
    response_model=Dict[str, Any],
    summary="문서 조회",
    description="인덱스에서 문서 ID로 특정 문서를 조회합니다."
)
async def get_document(
    index_name: str = Path(..., description="조회할 인덱스 이름", example="my_index"),
    doc_id: str = Path(..., description="문서 ID", example="doc_12345")
):
    try:
        logger.info(f"Fetching document from index: {index_name}, doc_id: {doc_id}")
        document = await es_service.get_document(index_name, doc_id)
        return document
    except Exception as e:
        logger.error(f"Failed to fetch document {doc_id} from {index_name}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put(
    "/documents/{index_name}/{doc_id}",
    status_code=status.HTTP_200_OK,
    summary="문서 수정",
    description="문서 ID로 특정 문서의 필드를 부분 수정합니다."
)
async def update_document(
    index_name: str = Path(..., description="문서가 있는 인덱스 이름", example="my_index"),
    doc_id: str = Path(..., description="수정할 문서 ID", example="doc_12345"),
    request: UpdateDocumentRequest = Body(...)
):
    try:
        logger.info(f"Updating document in index: {index_name}, doc_id: {doc_id}")
        response = await es_service.update_document(index_name, doc_id, request.updated_fields)
        return {"message": "Document updated successfully.", "response": response}
    except Exception as e:
        logger.error(f"Failed to update document {doc_id} in {index_name}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete(
    "/documents/{index_name}/{doc_id}",
    status_code=status.HTTP_200_OK,
    summary="문서 삭제",
    description="문서 ID로 특정 문서를 삭제합니다."
)
async def delete_document(
    index_name: str = Path(..., description="문서가 있는 인덱스 이름", example="my_index"),
    doc_id: str = Path(..., description="삭제할 문서 ID", example="doc_12345")
):
    try:
        logger.info(f"Deleting document from index: {index_name}, doc_id: {doc_id}")
        response = await es_service.delete_document(index_name, doc_id)
        return {"message": "Document deleted successfully.", "response": response}
    except Exception as e:
        logger.error(f"Failed to delete document {doc_id} from {index_name}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/search",
    response_model=List[Dict[str, Any]],
    summary="문서 검색",
    description="Elasticsearch Query DSL을 사용하여 인덱스에서 문서를 검색합니다. 쿼리 미제공 시 전체 문서를 조회합니다."
)
async def search_documents(request: SearchRequest):
    try:
        logger.info(f"Searching documents in index: {request.index_name}, size: {request.size}, from: {request.from_}")
        documents = await es_service.search_documents(request.index_name, request.query, request.size, request.from_)
        logger.info(f"Search completed, found {len(documents)} documents")
        return documents
    except Exception as e:
        logger.error(f"Search failed in index {request.index_name}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/bulk",
    status_code=status.HTTP_201_CREATED,
    summary="대량 문서 삽입",
    description="여러 개의 문서를 한 번에 인덱스에 삽입합니다. 대량 데이터 처리에 최적화되어 있습니다."
)
async def bulk_insert_documents(request: BulkInsertRequest):
    try:
        logger.info(f"Bulk inserting {len(request.documents)} documents into index: {request.index_name}")
        response = await es_service.bulk_insert_documents(request.index_name, request.documents)
        items_count = len(response.get("items", []))
        logger.info(f"Bulk insert completed: {items_count} items, errors: {response.get('errors')}")
        return {
            "message": f"Bulk insert completed.",
            "took": response.get("took"),
            "errors": response.get("errors"),
            "items_count": items_count
        }
    except Exception as e:
        logger.error(f"Bulk insert failed in index {request.index_name}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
