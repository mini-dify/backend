from ..db.es_database import get_es_client
from typing import List, Dict, Any, Optional
from elasticsearch import NotFoundError, RequestError, ConnectionError as ESConnectionError
from ..logging_config import get_logger
import traceback

logger = get_logger(__name__)


async def create_index(index_name: str, mappings: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    ElasticSearch에 새로운 인덱스를 생성합니다.

    Parameters:
        index_name (str): 생성할 인덱스 이름
        mappings (Optional[Dict[str, Any]]): 인덱스 매핑 (스키마 정의). None인 경우 동적 매핑이 사용됩니다.

    Returns:
        Dict[str, Any]: ElasticSearch 응답

    Example mappings:
        {
            "properties": {
                "title": {"type": "text"},
                "timestamp": {"type": "date"}
            }
        }
    """
    try:
        client = get_es_client()
        body = {}

        logger.info(f"Creating index '{index_name}' with mappings: {mappings}")

        if mappings:
            body["mappings"] = mappings

        logger.info(f"Creating body: {body}")

        response = await client.indices.create(index=index_name, body=body)
        logger.info(f"Successfully created index '{index_name}'")
        return response
    except RequestError as e:
        logger.error(f"RequestError while creating index '{index_name}': {e.error}")
        logger.error(f"Error details: {e.info}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise
    except ESConnectionError as e:
        logger.error(f"ConnectionError while creating index '{index_name}': {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error while creating index '{index_name}': {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise


async def delete_index(index_name: str) -> Dict[str, Any]:
    """
    ElasticSearch에서 인덱스를 삭제합니다.

    Parameters:
        index_name (str): 삭제할 인덱스 이름

    Returns:
        Dict[str, Any]: ElasticSearch 응답
    """
    try:
        logger.info(f"Deleting index '{index_name}'")
        client = get_es_client()
        response = await client.indices.delete(index=index_name)
        logger.info(f"Successfully deleted index '{index_name}'")
        return response
    except NotFoundError as e:
        logger.error(f"NotFoundError while deleting index '{index_name}': Index does not exist")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise
    except RequestError as e:
        logger.error(f"RequestError while deleting index '{index_name}': {e.error}")
        logger.error(f"Error details: {e.info}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise
    except ESConnectionError as e:
        logger.error(f"ConnectionError while deleting index '{index_name}': {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error while deleting index '{index_name}': {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise


async def list_indices() -> List[str]:
    """
    ElasticSearch의 모든 인덱스 목록을 조회합니다.

    Returns:
        List[str]: 인덱스 이름 목록
    """
    try:
        logger.info("Listing all indices")
        client = get_es_client()
        response = await client.cat.indices(format="json")
        indices = [index["index"] for index in response]
        logger.info(f"Successfully retrieved {len(indices)} indices")
        return indices
    except RequestError as e:
        logger.error(f"RequestError while listing indices: {e.error}")
        logger.error(f"Error details: {e.info}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise
    except ESConnectionError as e:
        logger.error(f"ConnectionError while listing indices: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error while listing indices: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise


async def insert_document(index_name: str, document: Dict[str, Any], doc_id: Optional[str] = None) -> str:
    """
    ElasticSearch 인덱스에 문서를 삽입합니다.

    Parameters:
        index_name (str): 문서를 삽입할 인덱스 이름
        document (Dict[str, Any]): 삽입할 문서 데이터
        doc_id (Optional[str]): 문서 ID. None인 경우 ElasticSearch가 자동으로 ID를 생성합니다.

    Returns:
        str: 삽입된 문서의 ID
    """
    try:
        logger.info(f"Inserting document into index '{index_name}' with doc_id: {doc_id}")
        client = get_es_client()
        response = await client.index(index=index_name, body=document, id=doc_id)
        inserted_id = response["_id"]
        logger.info(f"Successfully inserted document with ID '{inserted_id}' into index '{index_name}'")
        return inserted_id
    except NotFoundError as e:
        logger.error(f"NotFoundError while inserting document into index '{index_name}': Index does not exist")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise
    except RequestError as e:
        logger.error(f"RequestError while inserting document into index '{index_name}': {e.error}")
        logger.error(f"Error details: {e.info}")
        logger.error(f"Document data: {document}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise
    except ESConnectionError as e:
        logger.error(f"ConnectionError while inserting document into index '{index_name}': {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error while inserting document into index '{index_name}': {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise


async def get_document(index_name: str, doc_id: str) -> Dict[str, Any]:
    """
    ElasticSearch 인덱스에서 ID로 문서를 조회합니다.

    Parameters:
        index_name (str): 조회할 인덱스 이름
        doc_id (str): 조회할 문서 ID

    Returns:
        Dict[str, Any]: 문서 데이터

    Raises:
        NotFoundError: 문서를 찾을 수 없는 경우
    """
    try:
        logger.info(f"Getting document '{doc_id}' from index '{index_name}'")
        client = get_es_client()
        response = await client.get(index=index_name, id=doc_id)
        logger.info(f"Successfully retrieved document '{doc_id}' from index '{index_name}'")
        return response["_source"]
    except NotFoundError as e:
        logger.error(f"NotFoundError while getting document '{doc_id}' from index '{index_name}': Document or index does not exist")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise
    except RequestError as e:
        logger.error(f"RequestError while getting document '{doc_id}' from index '{index_name}': {e.error}")
        logger.error(f"Error details: {e.info}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise
    except ESConnectionError as e:
        logger.error(f"ConnectionError while getting document '{doc_id}' from index '{index_name}': {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error while getting document '{doc_id}' from index '{index_name}': {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise


async def update_document(index_name: str, doc_id: str, updated_fields: Dict[str, Any]) -> Dict[str, Any]:
    """
    ElasticSearch 인덱스의 문서를 수정합니다.

    Parameters:
        index_name (str): 문서가 있는 인덱스 이름
        doc_id (str): 수정할 문서 ID
        updated_fields (Dict[str, Any]): 수정할 필드 데이터 (부분 업데이트)

    Returns:
        Dict[str, Any]: ElasticSearch 응답
    """
    try:
        logger.info(f"Updating document '{doc_id}' in index '{index_name}' with fields: {updated_fields}")
        client = get_es_client()
        response = await client.update(
            index=index_name,
            id=doc_id,
            body={"doc": updated_fields}
        )
        logger.info(f"Successfully updated document '{doc_id}' in index '{index_name}'")
        return response
    except NotFoundError as e:
        logger.error(f"NotFoundError while updating document '{doc_id}' in index '{index_name}': Document or index does not exist")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise
    except RequestError as e:
        logger.error(f"RequestError while updating document '{doc_id}' in index '{index_name}': {e.error}")
        logger.error(f"Error details: {e.info}")
        logger.error(f"Updated fields: {updated_fields}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise
    except ESConnectionError as e:
        logger.error(f"ConnectionError while updating document '{doc_id}' in index '{index_name}': {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error while updating document '{doc_id}' in index '{index_name}': {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise


async def delete_document(index_name: str, doc_id: str) -> Dict[str, Any]:
    """
    ElasticSearch 인덱스에서 문서를 삭제합니다.

    Parameters:
        index_name (str): 문서가 있는 인덱스 이름
        doc_id (str): 삭제할 문서 ID

    Returns:
        Dict[str, Any]: ElasticSearch 응답
    """
    try:
        logger.info(f"Deleting document '{doc_id}' from index '{index_name}'")
        client = get_es_client()
        response = await client.delete(index=index_name, id=doc_id)
        logger.info(f"Successfully deleted document '{doc_id}' from index '{index_name}'")
        return response
    except NotFoundError as e:
        logger.error(f"NotFoundError while deleting document '{doc_id}' from index '{index_name}': Document or index does not exist")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise
    except RequestError as e:
        logger.error(f"RequestError while deleting document '{doc_id}' from index '{index_name}': {e.error}")
        logger.error(f"Error details: {e.info}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise
    except ESConnectionError as e:
        logger.error(f"ConnectionError while deleting document '{doc_id}' from index '{index_name}': {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error while deleting document '{doc_id}' from index '{index_name}': {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise


async def search_documents(
    index_name: str,
    query: Optional[Dict[str, Any]] = None,
    size: int = 10,
    from_: int = 0
) -> List[Dict[str, Any]]:
    """
    ElasticSearch 인덱스에서 문서를 검색합니다.

    Parameters:
        index_name (str): 검색할 인덱스 이름
        query (Optional[Dict[str, Any]]): ElasticSearch 쿼리 DSL. None인 경우 모든 문서를 조회합니다.
        size (int): 반환할 최대 문서 수 (기본값: 10)
        from_ (int): 페이지네이션 시작 오프셋 (기본값: 0)

    Returns:
        List[Dict[str, Any]]: ID와 스코어가 포함된 문서 목록

    Example query:
        {
            "match": {
                "title": "검색어"
            }
        }
    """
    try:
        logger.info(f"Searching documents in index '{index_name}' with query: {query}, size: {size}, from: {from_}")
        client = get_es_client()

        body = {
            "query": query if query else {"match_all": {}},
            "size": size,
            "from": from_
        }

        response = await client.search(index=index_name, body=body)

        # Extract documents with metadata
        documents = []
        for hit in response["hits"]["hits"]:
            doc = {
                "_id": hit["_id"],
                "_score": hit["_score"],
                **hit["_source"]
            }
            documents.append(doc)

        logger.info(f"Successfully searched index '{index_name}', found {len(documents)} documents")
        return documents
    except NotFoundError as e:
        logger.error(f"NotFoundError while searching in index '{index_name}': Index does not exist")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise
    except RequestError as e:
        logger.error(f"RequestError while searching in index '{index_name}': {e.error}")
        logger.error(f"Error details: {e.info}")
        logger.error(f"Query: {query}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise
    except ESConnectionError as e:
        logger.error(f"ConnectionError while searching in index '{index_name}': {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error while searching in index '{index_name}': {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise


async def bulk_insert_documents(index_name: str, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    ElasticSearch 인덱스에 여러 문서를 한번에 삽입합니다 (대량 삽입).

    Parameters:
        index_name (str): 문서를 삽입할 인덱스 이름
        documents (List[Dict[str, Any]]): 삽입할 문서 목록

    Returns:
        Dict[str, Any]: 대량 삽입 작업의 상세 정보가 포함된 ElasticSearch 응답
    """
    try:
        logger.info(f"Bulk inserting {len(documents)} documents into index '{index_name}'")
        client = get_es_client()

        # Prepare bulk operations
        operations = []
        for doc in documents:
            operations.append({"index": {"_index": index_name}})
            operations.append(doc)

        response = await client.bulk(operations=operations)

        # Log error details if any
        if response.get("errors"):
            error_items = [item for item in response.get("items", []) if "error" in item.get("index", {})]
            logger.warning(f"Bulk insert completed with errors. {len(error_items)} items failed")
            for idx, item in enumerate(error_items[:5]):  # Log first 5 errors
                logger.error(f"Bulk error {idx+1}: {item['index']['error']}")
        else:
            logger.info(f"Successfully bulk inserted {len(documents)} documents into index '{index_name}'")

        return response
    except NotFoundError as e:
        logger.error(f"NotFoundError while bulk inserting into index '{index_name}': Index does not exist")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise
    except RequestError as e:
        logger.error(f"RequestError while bulk inserting into index '{index_name}': {e.error}")
        logger.error(f"Error details: {e.info}")
        logger.error(f"Number of documents: {len(documents)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise
    except ESConnectionError as e:
        logger.error(f"ConnectionError while bulk inserting into index '{index_name}': {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error while bulk inserting into index '{index_name}': {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise
