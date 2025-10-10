from fastapi import APIRouter
from app.models.developCellApi_model import ChatCompletionRequest
from app.services import developCellApi_service

router = APIRouter()


@router.post("/chat/completions",
             summary="llm 질의응답"
             )
async def get_chat_completion(request: ChatCompletionRequest):
    return await developCellApi_service.get_chat_completion_from_lms(request)
