from fastapi import APIRouter, Depends
from . import schemas, services

router = APIRouter()


@router.post("/chat", response_model=schemas.ChatResponse)
def chat_endpoint(request: schemas.ChatRequest):
    return services.get_chat_response(request)
