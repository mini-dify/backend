from pydantic import BaseModel, Field
from typing import Optional


class KeywordSearchRequest(BaseModel):
    query: str = Field(
        ...,
        description="검색 질문",
        example="제미니 회사 근무 시간"
    )
    top_k: int = Field(
        5,
        description="반환할 문서 수",
        ge=1,
        le=20,
        example=5
    )
    min_score: float = Field(
        0.0,
        description="최소 BM25 점수",
        ge=0.0,
        example=0.0
    )


class VectorSearchRequest(BaseModel):
    query: str = Field(
        ...,
        description="검색 질문",
        example="제미니 회사 근무 시간"
    )
    top_k: int = Field(
        5,
        description="반환할 문서 수",
        ge=1,
        le=20,
        example=5
    )
    min_score: float = Field(
        0.7,
        description="최소 코사인 유사도 (0~1)",
        ge=0.0,
        le=1.0,
        example=0.7
    )


class HybridSearchRequest(BaseModel):
    query: str = Field(
        ...,
        description="검색 질문",
        example="제미니 회사 근무 시간"
    )
    top_k: int = Field(
        5,
        description="반환할 문서 수",
        ge=1,
        le=20,
        example=5
    )
    keyword_weight: float = Field(
        0.3,
        description="키워드 검색 가중치 (0~1)",
        ge=0.0,
        le=1.0,
        example=0.3
    )
    vector_weight: float = Field(
        0.7,
        description="벡터 검색 가중치 (0~1)",
        ge=0.0,
        le=1.0,
        example=0.7
    )
    min_score: float = Field(
        0.5,
        description="최소 최종 점수 (0~1)",
        ge=0.0,
        le=1.0,
        example=0.5
    )


class CompareSearchRequest(BaseModel):
    query: str = Field(
        ...,
        description="검색 질문",
        example="제미니 회사 근무 시간"
    )
    top_k: int = Field(
        5,
        description="각 방법별 반환할 문서 수",
        ge=1,
        le=20,
        example=5
    )
