from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class SearchConfig(BaseModel):
    search_type: str = Field(
        "hybrid",
        description="검색 타입 (keyword/vector/hybrid)",
        example="hybrid"
    )
    top_k: int = Field(
        5,
        description="검색할 문서 수",
        ge=1,
        le=20,
        example=5
    )
    keyword_weight: float = Field(
        0.3,
        description="키워드 검색 가중치 (hybrid 사용 시)",
        ge=0.0,
        le=1.0,
        example=0.3
    )
    vector_weight: float = Field(
        0.7,
        description="벡터 검색 가중치 (hybrid 사용 시)",
        ge=0.0,
        le=1.0,
        example=0.7
    )
    min_score: float = Field(
        0.5,
        description="최소 점수",
        ge=0.0,
        le=1.0,
        example=0.5
    )


class CreateAssistantRequest(BaseModel):
    name: str = Field(
        ...,
        description="Assistant 이름",
        example="회사 규정 도우미"
    )
    model: str = Field(
        "qwen/qwen2.5-coder-32b",
        description="사용할 LLM 모델",
        example="qwen/qwen2.5-coder-32b"
    )
    system_prompt: str = Field(
        ...,
        description="시스템 프롬프트 (Assistant의 역할/지침)",
        example="당신은 친절한 회사 규정 전문가입니다. 검색된 문서를 참고하여 정확하고 상세하게 답변해주세요."
    )
    temperature: float = Field(
        0.7,
        description="LLM temperature (창의성 조절)",
        ge=0.0,
        le=2.0,
        example=0.7
    )
    search_config: SearchConfig = Field(
        default_factory=SearchConfig,
        description="검색 설정"
    )


class UpdateAssistantRequest(BaseModel):
    name: Optional[str] = Field(
        None,
        description="Assistant 이름",
        example="회사 규정 도우미"
    )
    model: Optional[str] = Field(
        None,
        description="사용할 LLM 모델",
        example="qwen/qwen2.5-coder-32b"
    )
    system_prompt: Optional[str] = Field(
        None,
        description="시스템 프롬프트",
        example="새로운 시스템 프롬프트..."
    )
    temperature: Optional[float] = Field(
        None,
        description="LLM temperature",
        ge=0.0,
        le=2.0,
        example=0.7
    )
    search_config: Optional[SearchConfig] = Field(
        None,
        description="검색 설정"
    )


class AssistantResponse(BaseModel):
    assistant_id: str = Field(..., description="Assistant ID")
    name: str = Field(..., description="Assistant 이름")
    model: str = Field(..., description="LLM 모델")
    system_prompt: str = Field(..., description="시스템 프롬프트")
    temperature: float = Field(..., description="Temperature")
    search_config: SearchConfig = Field(..., description="검색 설정")
    created_at: str = Field(..., description="생성 시간")
    updated_at: str = Field(..., description="수정 시간")
