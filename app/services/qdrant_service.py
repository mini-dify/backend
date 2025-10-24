from qdrant_client import QdrantClient, models
from app.models.qdrant import CollectionConfig, UpsertPoints, SearchQuery
from typing import List, Iterable, Tuple, Dict, Any, Optional
import itertools, os


async def list_collections(client: QdrantClient) -> List[str]:
    collections_response = client.get_collections()
    return [collection.name for collection in collections_response.collections]


async def create_collection(client: QdrantClient, config: CollectionConfig):
    client.recreate_collection(
        collection_name=config.name,
        vectors_config=models.VectorParams(size=config.vector_size, distance=models.Distance[config.distance.upper()]),
    )
    return {"status": "Collection created successfully"}


async def upsert_points(client: QdrantClient, points_data: UpsertPoints):
    points = [models.PointStruct(id=p.id, vector=p.vector, payload=p.payload) for p in points_data.points]
    client.upsert(
        collection_name=points_data.collection_name,
        points=points,
        wait=True
    )
    return {"status": "Points upserted successfully"}


async def search_points(client: QdrantClient, query: SearchQuery):
    hits = client.search(
        collection_name=query.collection_name,
        query_vector=query.vector,
        limit=query.limit,
        with_payload=query.with_payload
    )
    return hits



# === 보강: distance 안전 처리 (대소문자 허용) ===
def _distance_enum(distance: str):
    return models.Distance[distance.strip().upper()]

# === 추가: 간단 임베딩 선택===
def _embed(texts: List[str], model_name: str) -> List[List[float]]:
    m = (model_name or "").lower()

    if m in ("minilm", "sentence-minilm", "all-minilm-l6-v2"):
        # pip install sentence-transformers
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        return model.encode(texts, show_progress_bar=False, normalize_embeddings=True).tolist()

    if m in ("qwen-32b-emb", "qwen/qwen2.5-embedding-32b"):
        # 예시: DashScope/내부 API 연동 위치 (현재는 차원만 맞춘 더미)
        dim = 4096
        return [[0.0] * dim for _ in texts]

    if m in ("openai-1536", "text-embedding-3-small"):
        import openai
        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        resp = client.embeddings.create(model="text-embedding-3-small", input=texts)
        return [d.embedding for d in resp.data]

    raise ValueError(f"Unsupported embed_model: {model_name}")

# === 추가: 텍스트 청크/배치 유틸 ===
def _chunk_text(text: str, chunk_size: int, chunk_overlap: int) -> List[str]:
    if chunk_overlap >= chunk_size:
        chunk_overlap = max(0, chunk_size // 4)
    chunks, start, n = [], 0, len(text)
    while start < n:
        end = min(n, start + chunk_size)
        chunks.append(text[start:end])
        if end == n:
            break
        start = max(end - chunk_overlap, start + 1)
    return chunks

def _batched(iterable: Iterable, n: int):
    it = iter(iterable)
    while True:
        batch = list(itertools.islice(it, n))
        if not batch:
            return
        yield batch

# === 추가: 컬렉션 벡터 차원과 임베딩 차원 일치 검증 ===
def _verify_collection_dim(client: QdrantClient, collection_name: str, vector_len: int):
    info = client.get_collection(collection_name=collection_name)
    vecs = getattr(info, "vectors", None) or info.vectors
    size = getattr(getattr(vecs, "config", None), "size", None)
    if size is None and isinstance(vecs, dict):
        size = vecs.get("size")
    if size is not None and size != vector_len:
        raise ValueError(f"Collection dim({size}) != embedding dim({vector_len})")

# === 추가: 텍스트 대용량 임베딩 + 업서트 ===
from app.models.qdrant import EmbedTextRequest, TextItem, FileIngestRequest

async def embed_and_upsert_texts(client: QdrantClient, req: EmbedTextRequest) -> Dict[str, Any]:
    # 1) 텍스트 → 청크 확장
    expanded: List[Tuple[str, str, Dict[str, Any]]] = []
    for i, item in enumerate(req.items):
        base_id = item.id or f"doc-{i}"
        chunks = _chunk_text(item.text, req.chunk_size, req.chunk_overlap)
        for j, ch in enumerate(chunks):
            pid = f"{base_id}::chunk-{j}"
            payload = dict(item.payload or {})
            payload.update({"source_id": base_id, "chunk_index": j, "text": ch})
            expanded.append((pid, ch, payload))

    if not expanded:
        return {"status": "ok", "points": 0}

    # 2) 첫 벡터로 컬렉션 차원 검증
    preview_vec = _embed([expanded[0][1]], req.embed_model)[0]
    _verify_collection_dim(client, req.collection_name, len(preview_vec))

    # 3) 배치 임베딩 + 업서트
    total = 0
    for batch in _batched(expanded, req.batch_size):
        ids = [b[0] for b in batch]
        texts = [b[1] for b in batch]
        payloads = [b[2] for b in batch]
        vectors = _embed(texts, req.embed_model)
        points = [models.PointStruct(id=i, vector=v, payload=p) for i, v, p in zip(ids, vectors, payloads)]
        client.upsert(collection_name=req.collection_name, points=points, wait=False)  # 성능상 wait=False 권장
        total += len(points)

    return {"status": "ok", "points": total}

# === 추가: 파일(텍스트/CSV/엑셀) 인제스트 → 임베딩+업서트 ===
def _iter_records_from_file(file_path: str,
                            text_columns: Optional[List[str]],
                            sheet_name: Optional[str],
                            id_column: Optional[str]):
    import os, pandas as pd
    ext = os.path.splitext(file_path)[1].lower()

    if ext in [".txt", ".md", ".log"]:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        from app.models.qdrant import TextItem
        yield TextItem(id=None, text=content, payload={"filename": os.path.basename(file_path)})
        return

    if ext == ".csv":
        for chunk in pd.read_csv(file_path, chunksize=5000, dtype=str, keep_default_na=False):
            for _, row in chunk.iterrows():
                payload = row.to_dict()
                rid = payload.get(id_column) if id_column else None
                text = "\n".join([payload.get(c, "") for c in text_columns]) if text_columns else "\n".join(payload.values())
                from app.models.qdrant import TextItem
                yield TextItem(id=rid, text=text, payload=payload)
        return

    if ext in [".xls", ".xlsx"]:
        df = pd.read_excel(file_path, sheet_name=sheet_name, dtype=str, keep_default_na=False)
        for _, row in df.iterrows():
            payload = row.to_dict()
            rid = payload.get(id_column) if id_column else None
            text = "\n".join([payload.get(c, "") for c in text_columns]) if text_columns else "\n".join(payload.values())
            from app.models.qdrant import TextItem
            yield TextItem(id=rid, text=text, payload=payload)
        return

    raise ValueError(f"Unsupported file type: {ext}")

async def ingest_file(client: QdrantClient, req: FileIngestRequest, file_path: str) -> Dict[str, Any]:
    items = list(_iter_records_from_file(
        file_path=file_path,
        text_columns=req.text_columns,
        sheet_name=req.sheet_name,
        id_column=req.id_column,
    ))
    text_req = EmbedTextRequest(
        collection_name=req.collection_name,
        embed_model=req.embed_model,
        items=items,
        chunk_size=req.chunk_size,
        chunk_overlap=req.chunk_overlap,
        batch_size=req.batch_size,
    )
    return await embed_and_upsert_texts(client, text_req)
