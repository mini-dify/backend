"""
Unified document storage service

Functions:
- Text chunking
- Save to Elasticsearch (keyword search)
- Save to Qdrant (vector search)
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct
from ..db.es_database import get_es_client
from ..services.developCellApi_service import get_embedding_from_lms
from ..models.developCellApi_model import EmbeddingRequest
from ..logging_config import get_logger
import uuid

logger = get_logger(__name__)


# ============================================
# Text Processing
# ============================================

def split_text_into_chunks(
    text: str,
    chunk_size: int = 500,
    overlap: int = 50
) -> List[str]:
    """
    Split text into chunks

    Parameters:
        text: Original text to split
        chunk_size: Maximum characters per chunk
        overlap: Overlapping characters between chunks

    Returns:
        List of chunk strings
    """
    if not text or len(text) == 0:
        return []

    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        start = end - overlap

        if end >= len(text):
            break

    logger.info(f"Split text into {len(chunks)} chunks (size={chunk_size}, overlap={overlap})")
    return chunks


async def read_file_content(file_path: str) -> str:
    """
    Read text from file

    Parameters:
        file_path: File path

    Returns:
        File content
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        logger.info(f"Read file: {file_path} ({len(content)} characters)")
        return content

    except Exception as e:
        logger.error(f"Failed to read file {file_path}: {str(e)}")
        raise


# ============================================
# Elasticsearch Operations
# ============================================

async def save_original_document(
    index_name: str,
    document_id: str,
    title: str,
    content: str
) -> str:
    """
    Save original document to Elasticsearch

    Parameters:
        index_name: Elasticsearch index name (knowledge_base_original)
        document_id: Unique document ID
        title: Document title
        content: Full document content

    Returns:
        Document ID
    """
    try:
        client = get_es_client()

        document = {
            "document_id": document_id,
            "title": title,
            "full_content": content,
            "created_at": datetime.now().isoformat()
        }

        response = await client.index(
            index=index_name,
            id=document_id,
            body=document
        )

        logger.info(f"Saved original document to Elasticsearch with ID: {document_id}")
        return response["_id"]

    except Exception as e:
        logger.error(f"Failed to save original document to Elasticsearch: {str(e)}")
        raise


async def save_chunks_to_elasticsearch(
    index_name: str,
    document_id: str,
    title: str,
    chunks: List[str]
) -> List[str]:
    """
    Save chunks to Elasticsearch

    Parameters:
        index_name: Elasticsearch index name
        document_id: Original document ID
        title: Document title
        chunks: List of chunks to save

    Returns:
        List of saved document IDs
    """
    try:
        client = get_es_client()
        chunk_ids = []

        for idx, chunk in enumerate(chunks):
            document = {
                "document_id": document_id,
                "title": title,
                "content": chunk,
                "chunk_index": idx,
                "total_chunks": len(chunks),
                "created_at": datetime.now().isoformat()
            }

            response = await client.index(
                index=index_name,
                body=document
            )

            chunk_ids.append(response["_id"])
            logger.info(f"Saved chunk {idx+1}/{len(chunks)} to Elasticsearch with ID: {response['_id']}")

        logger.info(f"Successfully saved {len(chunks)} chunks to Elasticsearch")
        return chunk_ids

    except Exception as e:
        logger.error(f"Failed to save chunks to Elasticsearch: {str(e)}")
        raise


# ============================================
# Qdrant Operations
# ============================================

async def create_embeddings_for_chunks(chunks: List[str]) -> List[List[float]]:
    """
    Create embeddings for multiple chunks

    Parameters:
        chunks: List of text chunks

    Returns:
        List of embedding vectors (each 4096 dimensions)
    """
    try:
        logger.info(f"Creating embeddings for {len(chunks)} chunks")

        embeddings = []

        for idx, chunk in enumerate(chunks):
            logger.info(f"Creating embedding {idx+1}/{len(chunks)}")

            response = await get_embedding_from_lms(
                EmbeddingRequest(input=chunk)
            )

            embedding = response["data"][0]["embedding"]
            embeddings.append(embedding)

        logger.info(f"Successfully created {len(embeddings)} embeddings")
        return embeddings

    except Exception as e:
        logger.error(f"Failed to create embeddings: {str(e)}")
        raise


async def save_chunks_to_qdrant(
    client: QdrantClient,
    collection_name: str,
    document_id: str,
    title: str,
    chunks: List[str]
) -> List[str]:
    """
    Save chunks to Qdrant with embeddings

    Parameters:
        client: QdrantClient instance
        collection_name: Qdrant collection name
        document_id: Original document ID
        title: Document title
        chunks: List of chunks to save

    Returns:
        List of saved point IDs
    """
    try:
        logger.info(f"Saving {len(chunks)} chunks to Qdrant collection '{collection_name}'")

        # Create embeddings
        embeddings = await create_embeddings_for_chunks(chunks)

        # Create points
        points = []
        point_ids = []

        for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            point_id = str(uuid.uuid4())

            point = PointStruct(
                id=point_id,
                vector=embedding,
                payload={
                    "document_id": document_id,
                    "title": title,
                    "content": chunk,
                    "chunk_index": idx,
                    "total_chunks": len(chunks)
                }
            )

            points.append(point)
            point_ids.append(point_id)

        # Batch insert
        client.upsert(
            collection_name=collection_name,
            points=points,
            wait=True
        )

        logger.info(f"Successfully saved {len(chunks)} chunks to Qdrant")
        return point_ids

    except Exception as e:
        logger.error(f"Failed to save chunks to Qdrant: {str(e)}")
        raise


# ============================================
# Unified Save Function
# ============================================

async def save_document(
    title: str,
    content: str,
    qdrant_client: QdrantClient,
    chunk_size: int = 500,
    overlap: int = 50
) -> Dict[str, Any]:
    """
    Save document to both Elasticsearch and Qdrant

    Parameters:
        title: Document title
        content: Document content
        qdrant_client: QdrantClient instance
        chunk_size: Chunk size
        overlap: Chunk overlap

    Returns:
        Save result with both ES and Qdrant info
    """
    try:
        # Generate unique document ID
        document_id = str(uuid.uuid4())
        logger.info(f"Generated document ID: {document_id}")

        # Save original document to knowledge_base_original
        await save_original_document(
            index_name="knowledge_base_original",
            document_id=document_id,
            title=title,
            content=content
        )

        # Split into chunks
        chunks = split_text_into_chunks(content, chunk_size, overlap)

        if not chunks:
            raise ValueError("No valid chunks created")

        # Save to Elasticsearch
        es_chunk_ids = await save_chunks_to_elasticsearch(
            index_name="knowledge_base",
            document_id=document_id,
            title=title,
            chunks=chunks
        )

        # Save to Qdrant
        qdrant_point_ids = await save_chunks_to_qdrant(
            client=qdrant_client,
            collection_name="knowledge",
            document_id=document_id,
            title=title,
            chunks=chunks
        )

        return {
            "document_id": document_id,
            "title": title,
            "total_chunks": len(chunks),
            "elasticsearch": {
                "original_index": "knowledge_base_original",
                "chunks_index": "knowledge_base",
                "chunk_ids": es_chunk_ids
            },
            "qdrant": {
                "collection_name": "knowledge",
                "point_ids": qdrant_point_ids
            }
        }

    except Exception as e:
        logger.error(f"Failed to save document: {str(e)}")
        raise
