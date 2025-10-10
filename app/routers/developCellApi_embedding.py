from fastapi import APIRouter, Depends
from app.models.developCellApi_model import EmbeddingRequest
from app.services import developCellApi_service

router = APIRouter()


@router.post("/embeddings",
             summary="텍스트 임베딩"
             )
async def get_embedding(request: EmbeddingRequest):
    return await developCellApi_service.get_embedding_from_lms(request)
