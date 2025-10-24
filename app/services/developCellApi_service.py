import httpx
from fastapi import HTTPException
from app.config import settings
from app.models.developCellApi_model import EmbeddingRequest, ChatCompletionRequest


async def get_embedding_from_lms(request: EmbeddingRequest, model: str = None) -> dict:
    if model is None:
        model = settings.EMBEDDING_MODEL

    headers = {
        "Authorization": settings.LMS_API_AUTHORIZATION,
        "Content-Type": "application/json"
    }
    url = settings.EMBEDDING_API_URL
    json_body = {
        "model": model,
        "input": request.input
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=json_body, headers=headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
        except httpx.RequestError as e:
            raise HTTPException(status_code=500, detail=f"An error occurred while requesting the embedding API: {e}")


async def get_chat_completion_from_lms(request: ChatCompletionRequest, model: str = None, temperature: float = None) -> dict:
    if model is None:
        model = settings.CHAT_MODEL

    headers = {
        "Authorization": settings.LMS_API_AUTHORIZATION,
        "Content-Type": "application/json"
    }
    url = settings.CHAT_COMPLETIONS_API_URL
    json_body = {
        "model": model,
        "messages": [msg.dict() for msg in request.messages]
    }

    if temperature is not None:
        json_body["temperature"] = temperature

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=json_body, headers=headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
        except httpx.RequestError as e:
            raise HTTPException(status_code=500, detail=f"An error occurred while requesting the chat completion API: {e}")
