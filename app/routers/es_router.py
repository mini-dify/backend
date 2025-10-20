from fastapi import APIRouter, status, HTTPException, Query, Body
from typing import List, Dict, Any, Optional
from ..services import es_service
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
    """
    ElasticSearch의 모든 인덱스 목록을 조회합니다.

    Returns:
        List[str]: 인덱스 이름 목록
    """
    logger.info("Fetching Elasticsearch indices list")
    indices = await es_service.list_indices()
    logger.info(f"Successfully fetched {len(indices)} indices")
    return indices


@router.post(
    "/indices",
    status_code=status.HTTP_201_CREATED,
    summary="인덱스 생성",
    description="새로운 Elasticsearch 인덱스를 생성합니다. 선택적으로 매핑(스키마), 샤드, 레플리카 개수를 지정할 수 있습니다."
)
async def create_index(
    index_name: str = Query(..., description="생성할 인덱스 이름", example="my_index"),
    mappings: Optional[Dict[str, Any]] = Body(
        None,
        description="인덱스 매핑 (스키마 정의)",
        example={
            "properties": {
                "title": {"type": "text"},
                "content": {"type": "text"},
                "embedding": {
                    "type": "dense_vector",
                    "dims": 768,
                    "index": True,
                    "similarity": "cosine"
                }
            }
        }
    ),
    number_of_shards: int = Body(3, description="Primary Shard 개수 (기본값: 3, 최소값: 1)", example=3),
    number_of_replicas: int = Body(1, description="Replica Shard 개수 (기본값: 1, 최소값: 0, 권장 최대값: 2)", example=1)
):
    """
    새로운 인덱스를 생성합니다.

    Parameters:
        index_name (str): 생성할 인덱스 이름
        mappings (Optional[Dict[str, Any]]): 인덱스 매핑 정보 (선택사항)
        number_of_shards (int): Primary Shard 개수 (기본값: 3)
        number_of_replicas (int): Replica Shard 개수 (기본값: 1)

    Returns:
        Dict: 생성 결과 메시지 및 응답

    Example:
        {
            "index_name": "my_index",
            "mappings": {
                "properties": {
                    "title": {"type": "text"},
                    "content": {"type": "text"}
                }
            },
            "number_of_shards": 3,
            "number_of_replicas": 1
        }
    """
    try:
        logger.info(
            f"Creating index: {index_name} with "
            f"shards: {number_of_shards}, replicas: {number_of_replicas}"
        )
        response = await es_service.create_index(
            index_name=index_name,
            mappings=mappings,
            number_of_shards=number_of_shards,
            number_of_replicas=number_of_replicas
        )
        logger.info(f"Successfully created index: {index_name}")
        return {
            "message": f"Index '{index_name}' created successfully.",
            "settings": {
                "number_of_shards": number_of_shards,
                "number_of_replicas": number_of_replicas
            },
            "response": response
        }
    except ValueError as e:
        logger.error(f"Validation error for index {index_name}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create index {index_name}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete(
    "/indices/{index_name}",
    status_code=status.HTTP_200_OK,
    summary="인덱스 삭제",
    description="지정된 Elasticsearch 인덱스를 삭제합니다."
)
async def delete_index(index_name: str):
    """
    인덱스를 삭제합니다.

    Parameters:
        index_name (str): 삭제할 인덱스 이름

    Returns:
        Dict: 삭제 결과 메시지 및 응답
    """
    try:
        logger.info(f"Deleting index: {index_name}")
        response = await es_service.delete_index(index_name)
        logger.info(f"Successfully deleted index: {index_name}")
        return {"message": f"Index '{index_name}' deleted successfully.", "response": response}
    except NotFoundError:
        logger.warning(f"Index not found: {index_name}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Index '{index_name}' not found.")
    except Exception as e:
        logger.error(f"Failed to delete index {index_name}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/documents",
    status_code=status.HTTP_201_CREATED,
    summary="문서 삽입",
    description="지정된 인덱스에 새로운 문서를 삽입합니다. 문서 ID는 선택 사항이며, 미제공 시 자동 생성됩니다."
)
async def insert_document(
    index_name: str = Query(..., description="문서를 삽입할 인덱스 이름"),
    document: Dict[str, Any] = Body(..., description="삽입할 문서 데이터"),
    doc_id: Optional[str] = Query(None, description="문서 ID (미제공시 자동 생성)")
):
    """
    인덱스에 문서를 삽입합니다.

    Parameters:
        index_name (str): 문서를 삽입할 인덱스 이름
        document (Dict[str, Any]): 삽입할 문서 데이터
        doc_id (Optional[str]): 문서 ID (선택사항)

    Returns:
        Dict: 삽입 결과 메시지 및 문서 ID
    """
    try:
        logger.info(f"Inserting document into index: {index_name}, doc_id: {doc_id}")
        inserted_id = await es_service.insert_document(index_name, document, doc_id)
        logger.info(f"Successfully inserted document with ID: {inserted_id}")
        return {"message": "Document inserted successfully.", "id": inserted_id}
    except Exception as e:
        logger.error(f"Failed to insert document into {index_name}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/documents/{index_name}/{doc_id}",
    response_model=Dict[str, Any],
    summary="문서 조회",
    description="인덱스에서 문서 ID로 특정 문서를 조회합니다."
)
async def get_document(index_name: str, doc_id: str):
    """
    ID로 문서를 조회합니다.

    Parameters:
        index_name (str): 조회할 인덱스 이름
        doc_id (str): 조회할 문서 ID

    Returns:
        Dict[str, Any]: 문서 데이터
    """
    try:
        logger.info(f"Fetching document from index: {index_name}, doc_id: {doc_id}")
        document = await es_service.get_document(index_name, doc_id)
        logger.info(f"Successfully fetched document: {doc_id}")
        return document
    except NotFoundError:
        logger.warning(f"Document not found: {doc_id} in index {index_name}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID '{doc_id}' not found in index '{index_name}'."
        )
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
    index_name: str,
    doc_id: str,
    updated_fields: Dict[str, Any] = Body(..., description="수정할 필드 데이터")
):
    """
    ID로 문서를 수정합니다.

    Parameters:
        index_name (str): 문서가 있는 인덱스 이름
        doc_id (str): 수정할 문서 ID
        updated_fields (Dict[str, Any]): 수정할 필드 데이터

    Returns:
        Dict: 수정 결과 메시지 및 응답
    """
    try:
        logger.info(f"Updating document in index: {index_name}, doc_id: {doc_id}")
        response = await es_service.update_document(index_name, doc_id, updated_fields)
        logger.info(f"Successfully updated document: {doc_id}")
        return {"message": "Document updated successfully.", "response": response}
    except NotFoundError:
        logger.warning(f"Document not found for update: {doc_id} in index {index_name}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID '{doc_id}' not found in index '{index_name}'."
        )
    except Exception as e:
        logger.error(f"Failed to update document {doc_id} in {index_name}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete(
    "/documents/{index_name}/{doc_id}",
    status_code=status.HTTP_200_OK,
    summary="문서 삭제",
    description="문서 ID로 특정 문서를 삭제합니다."
)
async def delete_document(index_name: str, doc_id: str):
    """
    ID로 문서를 삭제합니다.

    Parameters:
        index_name (str): 문서가 있는 인덱스 이름
        doc_id (str): 삭제할 문서 ID

    Returns:
        Dict: 삭제 결과 메시지 및 응답
    """
    try:
        logger.info(f"Deleting document from index: {index_name}, doc_id: {doc_id}")
        response = await es_service.delete_document(index_name, doc_id)
        logger.info(f"Successfully deleted document: {doc_id}")
        return {"message": "Document deleted successfully.", "response": response}
    except NotFoundError:
        logger.warning(f"Document not found for deletion: {doc_id} in index {index_name}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID '{doc_id}' not found in index '{index_name}'."
        )
    except Exception as e:
        logger.error(f"Failed to delete document {doc_id} from {index_name}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/search",
    response_model=List[Dict[str, Any]],
    summary="문서 검색",
    description="Elasticsearch Query DSL을 사용하여 인덱스에서 문서를 검색합니다. 쿼리 미제공 시 전체 문서를 조회합니다."
)
async def search_documents(
    index_name: str = Query(..., description="검색할 인덱스 이름"),
    query: Optional[Dict[str, Any]] = Body(None, description="ElasticSearch 쿼리 DSL (미제공시 전체 조회)"),
    size: int = Query(10, description="반환할 최대 결과 수"),
    from_: int = Query(0, alias="from", description="페이지네이션 시작 오프셋")
):
    """
    인덱스에서 문서를 검색합니다.

    Parameters:
        index_name (str): 검색할 인덱스 이름
        query (Optional[Dict[str, Any]]): ElasticSearch 쿼리 DSL (선택사항)
        size (int): 반환할 최대 결과 수 (기본값: 10)
        from_ (int): 페이지네이션 시작 오프셋 (기본값: 0)

    Returns:
        List[Dict[str, Any]]: 검색된 문서 목록
    """
    try:
        logger.info(f"Searching documents in index: {index_name}, size: {size}, from: {from_}")
        documents = await es_service.search_documents(index_name, query, size, from_)
        logger.info(f"Search completed, found {len(documents)} documents")
        return documents
    except Exception as e:
        logger.error(f"Search failed in index {index_name}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/bulk",
    status_code=status.HTTP_201_CREATED,
    summary="대량 문서 삽입",
    description="여러 개의 문서를 한 번에 인덱스에 삽입합니다. 대량 데이터 처리에 최적화되어 있습니다."
)
async def bulk_insert_documents(
    index_name: str = Query(..., description="문서를 삽입할 인덱스 이름"),
    documents: List[Dict[str, Any]] = Body(..., description="삽입할 문서 목록")
):
    """
    여러 문서를 한번에 삽입합니다 (대량 삽입).

    Parameters:
        index_name (str): 문서를 삽입할 인덱스 이름
        documents (List[Dict[str, Any]]): 삽입할 문서 목록

    Returns:
        Dict: 대량 삽입 결과 (소요 시간, 에러 여부, 삽입된 문서 수)
    """
    try:
        logger.info(f"Bulk inserting {len(documents)} documents into index: {index_name}")
        response = await es_service.bulk_insert_documents(index_name, documents)
        items_count = len(response.get("items", []))
        logger.info(f"Bulk insert completed: {items_count} items, errors: {response.get('errors')}")
        return {
            "message": f"Bulk insert completed.",
            "took": response.get("took"),
            "errors": response.get("errors"),
            "items_count": items_count
        }
    except Exception as e:
        logger.error(f"Bulk insert failed in index {index_name}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
