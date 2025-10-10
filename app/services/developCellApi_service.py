import httpx
from fastapi import HTTPException
from app.config import settings
from app.models.developCellApi_model import EmbeddingRequest, ChatCompletionRequest


async def get_embedding_from_lms(request: EmbeddingRequest) -> dict:
    headers = {
        "Authorization": settings.LMS_API_AUTH_HEADER,
        "Content-Type": "application/json"
    }
    url = f"{settings.LMS_API_BASE_URL}/embeddings"

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=request.dict(), headers=headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
        except httpx.RequestError as e:
            raise HTTPException(status_code=500, detail=f"An error occurred while requesting the embedding API: {e}")


async def get_chat_completion_from_lms(request: ChatCompletionRequest) -> dict:
    headers = {
        "Authorization": settings.LMS_API_AUTH_HEADER,
        "Content-Type": "application/json"
    }
    url = f"{settings.LMS_API_BASE_URL}/chat/completions"

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=request.dict(), headers=headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
        except httpx.RequestError as e:
            raise HTTPException(status_code=500, detail=f"An error occurred while requesting the chat completion API: {e}")
