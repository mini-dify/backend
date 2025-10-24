from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
from ..models.workflow import (
    CreateWorkflowRequest,
    WorkflowDefinition,
    WorkflowExecutionRequest,
    WorkflowExecutionResponse
)
from ..services import workflow_service
from ..db.database import get_qdrant_db
from qdrant_client import QdrantClient
from ..logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="워크플로우 생성",
    description="노드 기반 워크플로우를 생성합니다. Dify처럼 노드를 연결하여 파이프라인을 구성할 수 있습니다.",
    response_model=WorkflowDefinition
)
async def create_workflow(request: CreateWorkflowRequest):
    try:
        logger.info(f"Creating workflow: '{request.name}'")
        result = await workflow_service.create_workflow(request)
        return result
    except Exception as e:
        logger.error(f"Failed to create workflow: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "",
    summary="워크플로우 목록 조회",
    description="저장된 모든 워크플로우를 조회합니다.",
    response_model=List[WorkflowDefinition]
)
async def list_workflows():
    try:
        logger.info("Listing all workflows")
        results = await workflow_service.list_workflows()
        return results
    except Exception as e:
        logger.error(f"Failed to list workflows: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/{workflow_id}",
    summary="워크플로우 조회",
    description="특정 워크플로우의 상세 정보를 조회합니다.",
    response_model=WorkflowDefinition
)
async def get_workflow(workflow_id: str):
    try:
        logger.info(f"Getting workflow: {workflow_id}")
        result = await workflow_service.get_workflow(workflow_id)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workflow not found: {workflow_id}"
            )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get workflow {workflow_id}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/execute",
    summary="워크플로우 실행",
    description="저장된 워크플로우를 실행합니다. 각 노드가 순차적으로 실행되며 결과를 반환합니다.",
    response_model=WorkflowExecutionResponse
)
async def execute_workflow(
    request: WorkflowExecutionRequest,
    qdrant_client: QdrantClient = Depends(get_qdrant_db)
):
    try:
        logger.info(f"Executing workflow: {request.workflow_id}")

        # 워크플로우 조회
        workflow = await workflow_service.get_workflow(request.workflow_id)
        if not workflow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workflow not found: {request.workflow_id}"
            )

        # 워크플로우 실행
        result = await workflow_service.execute_workflow(
            workflow=workflow,
            input_data=request.input_data,
            qdrant_client=qdrant_client
        )

        return WorkflowExecutionResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Workflow execution failed: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
