from pydantic import BaseModel, Field
from typing import Optional


class UploadDocumentRequest(BaseModel):
    title: str = Field(
        ...,
        description="문서 제목",
        example="제미니 회사 규정"
    )
    content: str = Field(
        ...,
        description="문서 내용",
        example="제미니 회사의 근무 시간은 평일 오전 9시부터 오후 6시까지입니다..."
    )
    embedding_model: str = Field(
        "qwen/qwen2.5-embedding-32b",
        description="임베딩 모델",
        example="qwen/qwen2.5-embedding-32b"
    )
    chunk_size: int = Field(
        500,
        description="청크 크기 (글자 수)",
        example=500
    )
    overlap: int = Field(
        50,
        description="청크 간 겹침 (글자 수)",
        example=50
    )


class UploadFileRequest(BaseModel):
    file_path: str = Field(
        ...,
        description="파일 경로",
        example="file/test_script.txt"
    )
    title: Optional[str] = Field(
        None,
        description="문서 제목 (없으면 파일명 사용)",
        example="테스트 문서"
    )
    embedding_model: str = Field(
        "qwen/qwen2.5-embedding-32b",
        description="임베딩 모델",
        example="qwen/qwen2.5-embedding-32b"
    )
    chunk_size: int = Field(
        500,
        description="청크 크기",
        example=500
    )
    overlap: int = Field(
        50,
        description="청크 겹침",
        example=50
    )
