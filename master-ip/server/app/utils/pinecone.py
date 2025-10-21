# app/utils/pinecone.py
from pinecone import Pinecone
from fastapi import HTTPException
import asyncio

# Import config from constants
from app.constants import PINECONE_API_KEY, INDEX_HOST

def _get_pinecone_index():
    """
    Return a Pinecone Index client connected to INDEX_HOST.
    Raises HTTPException(500) if env not configured or connection fails.
    """
    if not PINECONE_API_KEY or not INDEX_HOST:
        raise HTTPException(status_code=500, detail="Pinecone not configured (set PINECONE_API_KEY and INDEX_HOST)")
    try:
        pc = Pinecone(api_key=PINECONE_API_KEY)
        idx = pc.Index(host=INDEX_HOST)
        return idx
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to connect to Pinecone: {e}")


async def _query_pinecone(vec: list, top_k: int = 5) -> list:
    idx = _get_pinecone_index()

    def _q():
        try:
            # New SDK syntax
            return idx.query(vector=vec, top_k=top_k, include_metadata=True)
        except TypeError:
            # Old SDK syntax
            return idx.query(vec, top_k=top_k, include_metadata=True)

    try:
        res = await asyncio.to_thread(_q)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pinecone query failed: {e}")
    matches = res.get("matches") or getattr(res, "matches", []) or []
    return matches


async def _upsert_pinecone(doc_id: str, vec: list, pine_meta: dict):
    idx = _get_pinecone_index()

    def _upsert():
        try:
            # New SDK syntax
            return idx.upsert(vectors=[(doc_id, vec, pine_meta)])
        except TypeError:
            # Old SDK syntax
            return idx.upsert([(doc_id, vec, pine_meta)])

    try:
        resp = await asyncio.to_thread(_upsert)
        # normalize response to plain dict
        if isinstance(resp, dict):
            return resp
        upserted_count = getattr(resp, "upserted_count", None)
        if upserted_count is not None:
            return {"upserted_count": int(upserted_count)}
        # fallback: try dict-like access
        try:
            return {"upserted_count": int(resp.get("upserted_count"))}
        except Exception:
            return {"info": "upserted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pinecone upsert failed: {e}")


def _normalize_pinecone_resp(r):
    """
    Success: normalize pinecone response into a simple dict
    """
    if r is None:
        return {"upserted_count": None}
    if isinstance(r, dict):
        return r
    upserted_count = getattr(r, "upserted_count", None)
    if upserted_count is None and hasattr(r, "get"):
        try:
            upserted_count = r.get("upserted_count")
        except Exception:
            upserted_count = None
    try:
        return {"upserted_count": int(upserted_count) if upserted_count is not None else None}
    except Exception:
        return {"info": "pinecone_response_unserializable"}