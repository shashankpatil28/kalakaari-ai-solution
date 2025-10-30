from pinecone import Pinecone
from fastapi import HTTPException
import asyncio

# Import config from constants
from app.constant import (
    PINECONE_API_KEY, 
    INDEX_HOST,
    PINECONE_ENV,
    PINECONE_TEXT_INDEX
)

def _get_image_index():
    """
    Return a Pinecone Index client connected to the IMAGE index (INDEX_HOST).
    Raises HTTPException(500) if env not configured or connection fails.
    """
    if not PINECONE_API_KEY or not INDEX_HOST:
        raise HTTPException(status_code=500, detail="Pinecone (Image) not configured (set PINECONE_API_KEY and INDEX_HOST)")
    try:
        pc = Pinecone(api_key=PINECONE_API_KEY)
        idx = pc.Index(host=INDEX_HOST)
        return idx
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to connect to Pinecone (Image): {e}")


async def _query_image_index(vec: list, top_k: int = 5) -> list:
    """Async wrapper for querying the IMAGE index."""
    idx = _get_image_index()

    def _q():
        # Use new SDK syntax
        return idx.query(vector=vec, top_k=top_k, include_metadata=True)

    try:
        res = await asyncio.to_thread(_q)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pinecone (Image) query failed: {e}")
    
    matches = res.get("matches") or getattr(res, "matches", []) or []
    return matches


async def _upsert_image_index(doc_id: str, vec: list, pine_meta: dict) -> dict:
    """Async wrapper for upserting to the IMAGE index."""
    idx = _get_image_index()

    def _upsert():
        # Use new SDK syntax
        return idx.upsert(vectors=[(doc_id, vec, pine_meta)])

    try:
        resp = await asyncio.to_thread(_upsert)
        # normalize response to plain dict
        if isinstance(resp, dict):
            return resp
        upserted_count = getattr(resp, "upserted_count", None)
        if upserted_count is not None:
            return {"upserted_count": int(upserted_count)}
        return {"info": "upserted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pinecone (Image) upsert failed: {e}")


def _get_text_index():
    """
    Return a Pinecone Index client connected to the TEXT index (PINECONE_TEXT_INDEX).
    Raises HTTPException(500) if env not configured or connection fails.
    """
    if not PINECONE_API_KEY or not PINECONE_ENV or not PINECONE_TEXT_INDEX:
        raise HTTPException(status_code=500, detail="Pinecone (Text) not configured (set PINECONE_API_KEY, PINECONE_ENV, and PINECONE_TEXT_INDEX)")
    try:
        pc = Pinecone(api_key=PINECONE_API_KEY)
        idx = pc.Index(name=PINECONE_TEXT_INDEX)
        return idx
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to connect to Pinecone (Text): {e}")


async def _query_text_index(vector: list, top_k: int = 5) -> list:
    """Async wrapper for querying the TEXT index."""
    idx = _get_text_index()

    def _q():
        # This function now correctly accepts 'vector' and passes it on
        return idx.query(vector=vector, top_k=top_k, include_metadata=True)

    try:
        res = await asyncio.to_thread(_q)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pinecone (Text) query failed: {e}")

    matches = res.get("matches") or getattr(res, "matches", []) or []
    return matches


async def _upsert_text_index(doc_id: str, vec: list, pine_meta: dict) -> dict:
    """Async wrapper for upserting to the TEXT index."""
    idx = _get_text_index()

    def _upsert():
        # Use new SDK syntax
        return idx.upsert(vectors=[(doc_id, vec, pine_meta)])

    try:
        resp = await asyncio.to_thread(_upsert)
        # normalize response to plain dict
        if isinstance(resp, dict):
            return resp
        upserted_count = getattr(resp, "upserted_count", None)
        if upserted_count is not None:
            return {"upserted_count": int(upserted_count)}
        return {"info": "upserted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pinecone (Text) upsert failed: {e}")