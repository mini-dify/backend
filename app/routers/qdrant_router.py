from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
import tempfile, os, json
from qdrant_client import QdrantClient
from app.db.database import get_qdrant_db
from app.models.qdrant import CollectionConfig, UpsertPoints, SearchQuery
from app.services import qdrant_service
from typing import List

router = APIRouter()


@router.get(
    "/qdrant/collections",
    response_model=List[str],
    summary="Qdrant 컬렉션 목록 조회",
    description="Qdrant에 존재하는 모든 컬렉션의 이름을 조회합니다."
)
async def handle_list_collections(client: QdrantClient = Depends(get_qdrant_db)):
    try:
        return await qdrant_service.list_collections(client)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/qdrant/collections",
    status_code=201,
    summary="Qdrant 컬렉션 생성",
    description="Qdrant에 새로운 벡터 컬렉션을 생성합니다.\n"
                "- **Embedding Model:** `qwen/qwen2.5-embedding-32b`- **Vector Size:** `4096`"
                "- **Distance:Cosine"
)
async def handle_create_collection(config: CollectionConfig, client: QdrantClient = Depends(get_qdrant_db)):
    try:
        return await qdrant_service.create_collection(client, config)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/qdrant/points/upsert",
    summary="Qdrant 포인트 추가/수정",
    description="지정된 컬렉션에 벡터 포인트(데이터)를 추가하거나 업데이트합니다."
)
async def handle_upsert_points(points_data: UpsertPoints, client: QdrantClient = Depends(get_qdrant_db)):
    try:
        return await qdrant_service.upsert_points(client, points_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/qdrant/points/search",
    summary="Qdrant 포인트 검색",
    description="지정된 컬렉션에서 쿼리 벡터와 유사한 벡터 포인트를 검색합니다."
)
async def handle_search_points(query: SearchQuery, client: QdrantClient = Depends(get_qdrant_db)):
    try:
        return await qdrant_service.search_points(client, query)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



# === 추가: 텍스트 대용량 임베딩 업서트 ===
from app.models.qdrant import EmbedTextRequest, FileIngestRequest
from app.services import qdrant_service

@router.post(
    "/qdrant/ingest/text",
    summary="텍스트 임베딩+업서트(대용량)",
    description="문서 텍스트 목록을 청크→임베딩→Qdrant 업서트합니다. embed_model로 임베딩 모델을 선택할 수 있습니다."
)
async def handle_ingest_texts(req: EmbedTextRequest, client: QdrantClient = Depends(get_qdrant_db)):
    try:
        return await qdrant_service.embed_and_upsert_texts(client, req)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# === 추가: 파일(텍스트/CSV/엑셀) 추가 ===
@router.post(
    "/qdrant/ingest/file",
    summary="파일 임베딩+업서트(대용량)",
    description="텍스트/CSV/엑셀 파일을 업로드하여 청크→임베딩→Qdrant 업서트합니다."
)
async def handle_ingest_file(
    file: UploadFile = File(...),
    collection_name: str = Form(...),
    embed_model: str = Form(...),
    chunk_size: int = Form(800),
    chunk_overlap: int = Form(100),
    batch_size: int = Form(64),
    sheet_name: str | None = Form(None),
    text_columns: str | None = Form(None),   # 문자열 JSON: '["title","content"]'
    id_column: str | None = Form(None),
    client: QdrantClient = Depends(get_qdrant_db)
):
    try:
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name

        req = FileIngestRequest(
            collection_name=collection_name,
            embed_model=embed_model,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            batch_size=batch_size,
            sheet_name=sheet_name,
            text_columns=json.loads(text_columns) if text_columns else None,
            id_column=id_column
        )

        try:
            result = await qdrant_service.ingest_file(client, req, tmp_path)
        finally:
            os.unlink(tmp_path)

        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))