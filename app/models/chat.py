from pydantic import BaseModel, Field
from typing import List, Dict, Any


class ChatRequest(BaseModel):
    assistant_id: str = Field(
        ...,
        description="사용할 Assistant ID",
        example="asst_1a2b3c4d5e6f"
    )
    message: str = Field(
        ...,
        description="사용자 질문",
        example="회사 근무 시간이 어떻게 되나요?"
    )


class ChatResponse(BaseModel):
    assistant_id: str = Field(..., description="Assistant ID")
    assistant_name: str = Field(..., description="Assistant 이름")
    user_message: str = Field(..., description="사용자 질문")
    answer: str = Field(..., description="AI 답변")
    sources: List[Dict[str, Any]] = Field(..., description="참고한 문서 소스")
    total_sources: int = Field(..., description="참고한 문서 개수")
