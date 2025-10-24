from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Literal
from enum import Enum


class NodeType(str, Enum):
    """노드 타입"""
    START = "start"                    # 시작 노드
    KNOWLEDGE_RETRIEVAL = "knowledge_retrieval"  # 지식 검색
    LLM = "llm"                        # LLM 호출
    CODE = "code"                      # Python 코드 실행
    CONDITION = "condition"            # 조건 분기
    HTTP_REQUEST = "http_request"      # HTTP 요청
    VARIABLE = "variable"              # 변수 설정
    END = "end"                        # 종료 노드


class NodeConfig(BaseModel):
    """노드별 설정"""
    # Knowledge Retrieval 설정
    search_type: Optional[str] = None
    top_k: Optional[int] = None

    # LLM 설정
    model: Optional[str] = None
    system_prompt: Optional[str] = None
    temperature: Optional[float] = None

    # Code 설정
    code: Optional[str] = None

    # Condition 설정
    condition: Optional[str] = None

    # HTTP 설정
    url: Optional[str] = None
    method: Optional[str] = None
    headers: Optional[Dict[str, str]] = None

    # 기타
    variables: Optional[Dict[str, Any]] = None


class WorkflowNode(BaseModel):
    """워크플로우 노드"""
    id: str = Field(..., description="노드 ID", example="node_1")
    type: NodeType = Field(..., description="노드 타입")
    name: str = Field(..., description="노드 이름", example="지식 검색")
    config: NodeConfig = Field(default_factory=NodeConfig, description="노드 설정")
    next_nodes: List[str] = Field(
        default_factory=list,
        description="다음 노드 ID 목록",
        example=["node_2"]
    )


class WorkflowDefinition(BaseModel):
    """워크플로우 정의"""
    workflow_id: str = Field(..., description="워크플로우 ID")
    name: str = Field(..., description="워크플로우 이름", example="RAG 파이프라인")
    description: Optional[str] = Field(None, description="설명")
    nodes: List[WorkflowNode] = Field(..., description="노드 목록")
    start_node_id: str = Field(..., description="시작 노드 ID", example="node_1")


class CreateWorkflowRequest(BaseModel):
    """워크플로우 생성 요청"""
    name: str = Field(..., description="워크플로우 이름", example="기본 RAG 파이프라인")
    description: Optional[str] = Field(None, description="설명")
    nodes: List[WorkflowNode] = Field(..., description="노드 목록")
    start_node_id: str = Field(..., description="시작 노드 ID")


class WorkflowExecutionRequest(BaseModel):
    """워크플로우 실행 요청"""
    workflow_id: str = Field(..., description="워크플로우 ID")
    input_data: Dict[str, Any] = Field(
        ...,
        description="입력 데이터",
        example={"user_message": "회사 근무 시간은?"}
    )


class NodeExecutionResult(BaseModel):
    """노드 실행 결과"""
    node_id: str
    node_name: str
    node_type: NodeType
    output: Dict[str, Any]
    execution_time_ms: float
    success: bool
    error: Optional[str] = None


class WorkflowExecutionResponse(BaseModel):
    """워크플로우 실행 결과"""
    workflow_id: str
    workflow_name: str
    execution_id: str
    input_data: Dict[str, Any]
    output_data: Dict[str, Any]
    nodes_executed: List[NodeExecutionResult]
    total_execution_time_ms: float
    success: bool
