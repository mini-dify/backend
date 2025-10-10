from pydantic import BaseModel
from typing import List, Dict, Any


class EmbeddingRequest(BaseModel):
    input: str


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatCompletionRequest(BaseModel):
    messages: List[ChatMessage]


class CompletionRequest(BaseModel):
    model: str
    prompt: str
    max_tokens: int = 50
