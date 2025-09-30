from fastapi import APIRouter
from .. import schemas
from ..services import chat_service

router = APIRouter()


@router.post("/chat", response_model=schemas.ChatResponse)
def chat_endpoint(request: schemas.ChatRequest):
    return chat_service.get_chat_response(request)
