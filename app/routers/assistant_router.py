from fastapi import APIRouter, HTTPException, status, Path
from typing import List
from ..models.assistant import CreateAssistantRequest, UpdateAssistantRequest, AssistantResponse
from ..services import assistant_service
from ..logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Assistant 생성",
    description="새로운 Assistant를 생성합니다. Assistant는 LLM 모델, 시스템 프롬프트, 검색 설정을 포함합니다.",
    response_model=AssistantResponse,
    responses={
        201: {
            "description": "Assistant 생성 성공",
            "content": {
                "application/json": {
                    "example": {
                        "assistant_id": "asst_1a2b3c4d5e6f",
                        "name": "회사 규정 도우미",
                        "model": "qwen/qwen2.5-coder-32b",
                        "system_prompt": "당신은 친절한 회사 규정 전문가입니다.",
                        "temperature": 0.7,
                        "search_config": {
                            "search_type": "hybrid",
                            "top_k": 5,
                            "keyword_weight": 0.3,
                            "vector_weight": 0.7,
                            "min_score": 0.5
                        },
                        "created_at": "2025-10-23T10:30:00",
                        "updated_at": "2025-10-23T10:30:00"
                    }
                }
            }
        }
    }
)
async def create_assistant(request: CreateAssistantRequest):
    try:
        logger.info(f"Creating assistant: '{request.name}'")
        result = await assistant_service.create_assistant(request)
        return result
    except Exception as e:
        logger.error(f"Failed to create assistant: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "",
    summary="Assistant 목록 조회",
    description="저장된 모든 Assistant를 조회합니다.",
    response_model=List[AssistantResponse],
    responses={
        200: {
            "description": "Assistant 목록 조회 성공",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "assistant_id": "asst_1a2b3c4d5e6f",
                            "name": "회사 규정 도우미",
                            "model": "qwen/qwen2.5-coder-32b",
                            "system_prompt": "당신은 친절한 회사 규정 전문가입니다.",
                            "temperature": 0.7,
                            "search_config": {
                                "search_type": "hybrid",
                                "top_k": 5,
                                "keyword_weight": 0.3,
                                "vector_weight": 0.7,
                                "min_score": 0.5
                            },
                            "created_at": "2025-10-23T10:30:00",
                            "updated_at": "2025-10-23T10:30:00"
                        }
                    ]
                }
            }
        }
    }
)
async def list_assistants():
    try:
        logger.info("Listing all assistants")
        results = await assistant_service.list_assistants()
        return results
    except Exception as e:
        logger.error(f"Failed to list assistants: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/{assistant_id}",
    summary="Assistant 조회",
    description="특정 Assistant의 상세 정보를 조회합니다.",
    response_model=AssistantResponse,
    responses={
        200: {
            "description": "Assistant 조회 성공"
        },
        404: {
            "description": "Assistant를 찾을 수 없음"
        }
    }
)
async def get_assistant(
    assistant_id: str = Path(..., description="Assistant ID", example="asst_1a2b3c4d5e6f")
):
    try:
        logger.info(f"Getting assistant: {assistant_id}")
        result = await assistant_service.get_assistant(assistant_id)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Assistant not found: {assistant_id}"
            )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get assistant {assistant_id}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put(
    "/{assistant_id}",
    summary="Assistant 수정",
    description="Assistant의 설정을 수정합니다. 프롬프트 수정 시 다음 대화부터 새 설정이 적용됩니다.",
    response_model=AssistantResponse,
    responses={
        200: {
            "description": "Assistant 수정 성공"
        },
        404: {
            "description": "Assistant를 찾을 수 없음"
        }
    }
)
async def update_assistant(
    request: UpdateAssistantRequest,
    assistant_id: str = Path(..., description="Assistant ID", example="asst_1a2b3c4d5e6f")
):
    try:
        logger.info(f"Updating assistant: {assistant_id}")
        result = await assistant_service.update_assistant(assistant_id, request)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Assistant not found: {assistant_id}"
            )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update assistant {assistant_id}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete(
    "/{assistant_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Assistant 삭제",
    description="Assistant를 삭제합니다.",
    responses={
        204: {
            "description": "Assistant 삭제 성공"
        },
        404: {
            "description": "Assistant를 찾을 수 없음"
        }
    }
)
async def delete_assistant(
    assistant_id: str = Path(..., description="Assistant ID", example="asst_1a2b3c4d5e6f")
):
    try:
        logger.info(f"Deleting assistant: {assistant_id}")
        deleted = await assistant_service.delete_assistant(assistant_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Assistant not found: {assistant_id}"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete assistant {assistant_id}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
