from typing import Dict, Any, List, Optional
from datetime import datetime
from qdrant_client import QdrantClient
import time
import uuid

from ..models.workflow import (
    WorkflowDefinition,
    WorkflowNode,
    NodeType,
    NodeExecutionResult,
    CreateWorkflowRequest
)
from ..services import mongodb_service, search_service
from ..services.developCellApi_service import get_chat_completion_from_lms
from ..models.developCellApi_model import ChatCompletionRequest, ChatMessage
from ..logging_config import get_logger

logger = get_logger(__name__)

DB_NAME = "mini_dify"
COLLECTION_NAME = "workflows"


# ============================================
# 노드 Executor 함수들
# ============================================

async def execute_knowledge_retrieval_node(
    node: WorkflowNode,
    context: Dict[str, Any],
    qdrant_client: QdrantClient
) -> Dict[str, Any]:
    """지식 검색 노드 실행"""
    user_message = context.get("user_message", "")

    search_type = node.config.search_type or "hybrid"
    top_k = node.config.top_k or 5

    logger.info(f"Executing Knowledge Retrieval: {search_type}")

    if search_type == "keyword":
        results = await search_service.keyword_search(
            query=user_message,
            top_k=top_k,
            min_score=0.0
        )
    elif search_type == "vector":
        results = await search_service.vector_search(
            query=user_message,
            qdrant_client=qdrant_client,
            top_k=top_k,
            min_score=0.0
        )
    else:  # hybrid
        results = await search_service.hybrid_search(
            query=user_message,
            qdrant_client=qdrant_client,
            top_k=top_k,
            keyword_weight=0.3,
            vector_weight=0.7,
            min_score=0.0
        )

    # 검색 결과를 텍스트로 포맷팅
    if results:
        context_text = "\n\n".join([
            f"[문서 {i+1}]\n제목: {r.get('title')}\n내용: {r.get('content')}"
            for i, r in enumerate(results)
        ])
    else:
        context_text = "검색된 관련 문서가 없습니다."

    return {
        "search_results": results,
        "search_context": context_text,
        "total_results": len(results)
    }


async def execute_llm_node(
    node: WorkflowNode,
    context: Dict[str, Any],
    qdrant_client: QdrantClient
) -> Dict[str, Any]:
    """LLM 노드 실행"""
    user_message = context.get("user_message", "")
    search_context = context.get("search_context", "")

    model = node.config.model or "qwen/qwen2.5-coder-32b"
    system_prompt = node.config.system_prompt or "당신은 유용한 AI 어시스턴트입니다."
    temperature = node.config.temperature or 0.7

    logger.info(f"Executing LLM: {model}")

    # 메시지 구성
    user_content = f"{search_context}\n\n질문: {user_message}" if search_context else user_message

    messages = [
        ChatMessage(role="system", content=system_prompt),
        ChatMessage(role="user", content=user_content)
    ]

    # LLM 호출
    llm_response = await get_chat_completion_from_lms(
        request=ChatCompletionRequest(messages=messages),
        model=model,
        temperature=temperature
    )

    answer = llm_response.get("choices", [{}])[0].get("message", {}).get("content", "")

    return {
        "llm_answer": answer,
        "llm_model": model,
        "llm_response": llm_response
    }


async def execute_code_node(
    node: WorkflowNode,
    context: Dict[str, Any],
    qdrant_client: QdrantClient
) -> Dict[str, Any]:
    """코드 실행 노드"""
    code = node.config.code or ""

    logger.info(f"Executing Code Node")

    # 안전한 코드 실행 환경
    local_vars = {"context": context, "result": {}}

    try:
        exec(code, {"__builtins__": {}}, local_vars)
        return local_vars.get("result", {})
    except Exception as e:
        logger.error(f"Code execution error: {str(e)}")
        return {"error": str(e)}


async def execute_variable_node(
    node: WorkflowNode,
    context: Dict[str, Any],
    qdrant_client: QdrantClient
) -> Dict[str, Any]:
    """변수 설정 노드"""
    variables = node.config.variables or {}

    logger.info(f"Setting variables: {list(variables.keys())}")

    return variables


# ============================================
# 워크플로우 실행 엔진
# ============================================

async def execute_node(
    node: WorkflowNode,
    context: Dict[str, Any],
    qdrant_client: QdrantClient
) -> NodeExecutionResult:
    """단일 노드 실행"""
    start_time = time.time()

    try:
        logger.info(f"Executing node: {node.name} (type: {node.type})")

        # 노드 타입별 실행
        if node.type == NodeType.KNOWLEDGE_RETRIEVAL:
            output = await execute_knowledge_retrieval_node(node, context, qdrant_client)
        elif node.type == NodeType.LLM:
            output = await execute_llm_node(node, context, qdrant_client)
        elif node.type == NodeType.CODE:
            output = await execute_code_node(node, context, qdrant_client)
        elif node.type == NodeType.VARIABLE:
            output = await execute_variable_node(node, context, qdrant_client)
        elif node.type == NodeType.START or node.type == NodeType.END:
            output = {}
        else:
            output = {"error": f"Unsupported node type: {node.type}"}

        execution_time = (time.time() - start_time) * 1000

        return NodeExecutionResult(
            node_id=node.id,
            node_name=node.name,
            node_type=node.type,
            output=output,
            execution_time_ms=execution_time,
            success=True
        )

    except Exception as e:
        execution_time = (time.time() - start_time) * 1000
        logger.error(f"Node execution failed: {str(e)}")

        return NodeExecutionResult(
            node_id=node.id,
            node_name=node.name,
            node_type=node.type,
            output={},
            execution_time_ms=execution_time,
            success=False,
            error=str(e)
        )


async def execute_workflow(
    workflow: WorkflowDefinition,
    input_data: Dict[str, Any],
    qdrant_client: QdrantClient
) -> Dict[str, Any]:
    """워크플로우 전체 실행"""
    start_time = time.time()
    execution_id = str(uuid.uuid4())

    logger.info(f"Starting workflow execution: {workflow.name} (ID: {execution_id})")

    # 실행 컨텍스트 초기화
    context = {**input_data}

    # 노드 맵 생성 (빠른 조회용)
    node_map = {node.id: node for node in workflow.nodes}

    # 실행 결과 저장
    execution_results: List[NodeExecutionResult] = []

    # 시작 노드부터 실행
    current_node_id = workflow.start_node_id

    # 무한 루프 방지 (최대 50개 노드)
    max_iterations = 50
    iteration = 0

    while current_node_id and iteration < max_iterations:
        iteration += 1

        # 현재 노드 가져오기
        current_node = node_map.get(current_node_id)
        if not current_node:
            logger.error(f"Node not found: {current_node_id}")
            break

        # 노드 실행
        result = await execute_node(current_node, context, qdrant_client)
        execution_results.append(result)

        # 실행 결과를 컨텍스트에 병합
        if result.success:
            context.update(result.output)
        else:
            logger.error(f"Node failed: {current_node.name}")
            break

        # 종료 노드면 중단
        if current_node.type == NodeType.END:
            break

        # 다음 노드로 이동
        if current_node.next_nodes:
            current_node_id = current_node.next_nodes[0]  # 첫 번째 다음 노드
        else:
            break

    total_time = (time.time() - start_time) * 1000

    logger.info(f"Workflow execution completed: {execution_id} ({total_time:.2f}ms)")

    return {
        "workflow_id": workflow.workflow_id,
        "workflow_name": workflow.name,
        "execution_id": execution_id,
        "input_data": input_data,
        "output_data": context,
        "nodes_executed": [r.dict() for r in execution_results],
        "total_execution_time_ms": total_time,
        "success": all(r.success for r in execution_results)
    }


# ============================================
# 워크플로우 CRUD
# ============================================

async def create_workflow(request: CreateWorkflowRequest) -> WorkflowDefinition:
    """워크플로우 생성"""
    workflow_id = f"wf_{uuid.uuid4().hex[:12]}"

    workflow_data = {
        "workflow_id": workflow_id,
        "name": request.name,
        "description": request.description,
        "nodes": [node.dict() for node in request.nodes],
        "start_node_id": request.start_node_id,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }

    await mongodb_service.insert_data(DB_NAME, COLLECTION_NAME, workflow_data)

    logger.info(f"Created workflow: {workflow_id}")

    return WorkflowDefinition(**workflow_data)


async def get_workflow(workflow_id: str) -> Optional[WorkflowDefinition]:
    """워크플로우 조회"""
    results = await mongodb_service.find_data_with_filter(
        DB_NAME,
        COLLECTION_NAME,
        {"workflow_id": workflow_id}
    )

    if not results:
        return None

    workflow_data = results[0]
    workflow_data.pop("_id", None)

    return WorkflowDefinition(**workflow_data)


async def list_workflows() -> List[WorkflowDefinition]:
    """워크플로우 목록 조회"""
    results = await mongodb_service.find_data(DB_NAME, COLLECTION_NAME)

    workflows = []
    for doc in results:
        doc.pop("_id", None)
        workflows.append(WorkflowDefinition(**doc))

    return workflows
