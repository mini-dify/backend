from ..db.es_database import get_es_client
from typing import List, Dict, Any, Optional
from elasticsearch import NotFoundError
from ..logging_config import get_logger

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
    client = get_es_client()
    body = {}

    logger.info(f"Creating mappings: {mappings}")

    if mappings:
        body["mappings"] = mappings

    logger.info(f"Creating body    : {body}")

    response = await client.indices.create(index=index_name, body=body)
    return response


async def delete_index(index_name: str) -> Dict[str, Any]:
    """
    ElasticSearch에서 인덱스를 삭제합니다.

    Parameters:
        index_name (str): 삭제할 인덱스 이름

    Returns:
        Dict[str, Any]: ElasticSearch 응답
    """
    client = get_es_client()
    response = await client.indices.delete(index=index_name)
    return response


async def list_indices() -> List[str]:
    """
    ElasticSearch의 모든 인덱스 목록을 조회합니다.

    Returns:
        List[str]: 인덱스 이름 목록
    """
    client = get_es_client()
    response = await client.cat.indices(format="json")
    return [index["index"] for index in response]


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
    client = get_es_client()
    response = await client.index(index=index_name, body=document, id=doc_id)
    return response["_id"]


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
    client = get_es_client()
    response = await client.get(index=index_name, id=doc_id)
    return response["_source"]


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
    client = get_es_client()
    response = await client.update(
        index=index_name,
        id=doc_id,
        body={"doc": updated_fields}
    )
    return response


async def delete_document(index_name: str, doc_id: str) -> Dict[str, Any]:
    """
    ElasticSearch 인덱스에서 문서를 삭제합니다.

    Parameters:
        index_name (str): 문서가 있는 인덱스 이름
        doc_id (str): 삭제할 문서 ID

    Returns:
        Dict[str, Any]: ElasticSearch 응답
    """
    client = get_es_client()
    response = await client.delete(index=index_name, id=doc_id)
    return response


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

    return documents


async def bulk_insert_documents(index_name: str, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    ElasticSearch 인덱스에 여러 문서를 한번에 삽입합니다 (대량 삽입).

    Parameters:
        index_name (str): 문서를 삽입할 인덱스 이름
        documents (List[Dict[str, Any]]): 삽입할 문서 목록

    Returns:
        Dict[str, Any]: 대량 삽입 작업의 상세 정보가 포함된 ElasticSearch 응답
    """
    client = get_es_client()

    # Prepare bulk operations
    operations = []
    for doc in documents:
        operations.append({"index": {"_index": index_name}})
        operations.append(doc)

    response = await client.bulk(operations=operations)
    return response
