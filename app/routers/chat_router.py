from fastapi import APIRouter, HTTPException, status, Depends
from ..models.chat import ChatRequest, ChatResponse
from ..services import rag_service
from ..db.database import get_qdrant_db
from qdrant_client import QdrantClient
from ..logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.post(
    "",
    summary="RAG 기반 채팅",
    description="Assistant를 사용하여 지식 베이스 기반 대화를 진행합니다. 자동으로 검색 후 LLM이 답변을 생성합니다.",
    response_model=ChatResponse,
    responses={
        200: {
            "description": "채팅 성공",
            "content": {
                "application/json": {
                    "example": {
                        "assistant_id": "asst_1a2b3c4d5e6f",
                        "assistant_name": "회사 규정 도우미",
                        "user_message": "회사 근무 시간이 어떻게 되나요?",
                        "answer": "회사 규정에 따르면, 근무 시간은 평일 오전 9시부터 오후 6시까지입니다. 점심 시간은 12시부터 1시까지 1시간입니다.",
                        "sources": [
                            {
                                "title": "제미니 회사 규정",
                                "content": "제미니 회사의 근무 시간은 평일 오전 9시부터 오후 6시까지입니다...",
                                "score": 0.85
                            }
                        ],
                        "total_sources": 1
                    }
                }
            }
        },
        404: {
            "description": "Assistant를 찾을 수 없음"
        }
    }
)
async def chat(
    request: ChatRequest,
    qdrant_client: QdrantClient = Depends(get_qdrant_db)
):
    try:
        logger.info(f"Chat request for assistant {request.assistant_id}: '{request.message}'")

        result = await rag_service.chat_with_rag(
            assistant_id=request.assistant_id,
            user_message=request.message,
            qdrant_client=qdrant_client
        )

        return ChatResponse(**result)

    except ValueError as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Chat failed: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
