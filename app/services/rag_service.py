from typing import List, Dict, Any
from qdrant_client import QdrantClient
from ..services import search_service, assistant_service
from ..services.developCellApi_service import get_chat_completion_from_lms
from ..models.developCellApi_model import ChatCompletionRequest, ChatMessage
from ..logging_config import get_logger

logger = get_logger(__name__)

# 검색 실행
async def perform_search(query: str, search_config: Dict[str, Any], qdrant_client: QdrantClient) -> List[Dict[str, Any]]:
    """
    Assistant 설정에 따라 적절한 검색 방식 선택 및 실행
    1. 설정에서 검색 파라미터 추출 (search_type, top_k, min_score)
    2. 검색 (keyword, vector, hybrid)

    Parameters:
        query: User query
        search_config: Search configuration from assistant
        qdrant_client: Qdrant client instance

    Returns:
        List of search results
    """
    search_type = search_config.get("search_type", "hybrid")
    top_k = search_config.get("top_k", 5)
    min_score = search_config.get("min_score", 0.5)

    logger.info(f"Performing {search_type} search for query: '{query}'")

    if search_type == "keyword":
        results = await search_service.keyword_search(
            query=query,
            top_k=top_k,
            min_score=min_score
        )
    elif search_type == "vector":
        results = await search_service.vector_search(
            query=query,
            qdrant_client=qdrant_client,
            top_k=top_k,
            min_score=min_score
        )
    elif search_type == "hybrid":
        keyword_weight = search_config.get("keyword_weight", 0.3)
        vector_weight = search_config.get("vector_weight", 0.7)
        results = await search_service.hybrid_search(
            query=query,
            qdrant_client=qdrant_client,
            top_k=top_k,
            keyword_weight=keyword_weight,
            vector_weight=vector_weight,
            min_score=min_score
        )
    else:
        raise ValueError(f"Invalid search type: {search_type}")

    logger.info(f"Found {len(results)} search results")
    return results


def format_search_results_as_context(results: List[Dict[str, Any]]) -> str:
    """
    컨텍스트 포매팅
    검색 결과를 LLM 이 읽을 수 있는 자연어 텍스트로 변환 (Json -> 자연어)

    Parameters:
        results: Search results

    Returns:
        Formatted context string
    """
    if not results:
        return "검색된 관련 문서가 없습니다."

    context_parts = ["다음은 검색된 관련 문서입니다:\n"]

    for idx, result in enumerate(results, 1):
        title = result.get("title", "제목 없음")
        content = result.get("content", "")
        score = result.get("score", 0)

        context_parts.append(f"\n[문서 {idx}] (관련도: {score:.2f})")
        context_parts.append(f"제목: {title}")
        context_parts.append(f"내용: {content}\n")

    return "\n".join(context_parts)


async def chat_with_rag(
    assistant_id: str,
    user_message: str,
    qdrant_client: QdrantClient
) -> Dict[str, Any]:
    """
    RAG 메인 함수

    Parameters:
        assistant_id: Assistant ID
        user_message: User's message (사용자 질문)
        qdrant_client: Qdrant client instance (벡터 DB 클라이언트)

    Returns:
        Chat response with sources
    """
    try:
        # 1. 선택한 assistant 조회 (설정 정보를 가져온다.)
        assistant = await assistant_service.get_assistant(assistant_id)
        if not assistant:
            raise ValueError(f"Assistant not found: {assistant_id}")

        logger.info(f"Using assistant: {assistant.name} (ID: {assistant_id})")

        # 2. 조회된 assistant 설정 정보로 검색 시작
        search_results = await perform_search(
            query=user_message,
            search_config=assistant.search_config.dict(),
            qdrant_client=qdrant_client
        )

        # 3. 답변을 자연어로 변경애준다.
        context = format_search_results_as_context(search_results)

        # 4. LLM 에 넘길 message 를 만들어 준다.
        messages = [
            ChatMessage(role="system", content=assistant.system_prompt),
            ChatMessage(role="user", content=f"{context}\n\n질문: {user_message}")
        ]

        # 5. Call LLM
        logger.info(f"Calling LLM with model: {assistant.model}")
        llm_response = await get_chat_completion_from_lms(
            request=ChatCompletionRequest(messages=messages),
            model=assistant.model,
            temperature=assistant.temperature
        )

        # 6. 답변 추출
        answer = llm_response.get("choices", [{}])[0].get("message", {}).get("content", "")

        logger.info(f"RAG chat completed for assistant {assistant_id}")

        return {
            "assistant_id": assistant_id,
            "assistant_name": assistant.name,
            "user_message": user_message,
            "answer": answer,
            "sources": search_results,
            "total_sources": len(search_results)
        }

    except Exception as e:
        logger.error(f"Failed to process RAG chat: {str(e)}")
        raise
