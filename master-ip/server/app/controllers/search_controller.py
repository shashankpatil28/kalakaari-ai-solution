# app/controllers/search_controller.py
from fastapi import HTTPException, Request, Form
from PIL import Image
from pinecone import Pinecone
import asyncio
import json as _json
from datetime import datetime
from typing import Optional, Any

# Import schemas
from app.schemas.search import QuerySchema, QueryArtisan, QueryArt

# Import DB helpers
from app.db.mongodb import collection
from app.utils.db_utils import ensure_db_ready_or_502

# Import embedders
from app.utils.embedders import ClipEmbedder, embed_text

# Import utils
from app.utils.http_client import _fetch_image_from_url
from app.utils.pinecone import (
    _get_pinecone_index, 
    _query_pinecone, 
    _upsert_pinecone, 
    _normalize_pinecone_resp
)

# Import config
from app.constants import (
    PINECONE_API_KEY, 
    PINECONE_ENV, 
    PINECONE_TEXT_INDEX, 
    TOP_K_DEFAULT
)

# --- Image Search Controller Logic ---

# Single embedder instance (lazy)
_embedder: Optional[ClipEmbedder] = None

def _ensure_embedder():
    """Local helper to lazy-load the ClipEmbedder."""
    global _embedder
    if _embedder is None:
        _embedder = ClipEmbedder()
    return _embedder

async def _embed_image(pil_img: Image.Image) -> list:
    """Local helper to embed a PIL image asynchronously."""
    embedder = _ensure_embedder()
    try:
        vec = await asyncio.to_thread(embedder.embed_pil, pil_img)
        return vec
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Embedding error: {e}")


async def image_search_url(image_url: str, top_k: int, include_meta: bool):
    """
    Controller logic for image search.
    """
    await ensure_db_ready_or_502()
    imgs_col = collection("image_index")

    pil_img = await _fetch_image_from_url(image_url)
    vec = await _embed_image(pil_img)
    matches = await _query_pinecone(vec, top_k=top_k)

    results = []
    for m in matches:
        mid = m.get("id") if isinstance(m, dict) else getattr(m, "id", None)
        score = m.get("score") if isinstance(m, dict) else getattr(m, "score", None)
        meta = m.get("metadata") if isinstance(m, dict) else getattr(m, "metadata", {}) or {}
        full_meta = None
        if include_meta and mid:
            try:
                full_meta = await asyncio.wait_for(imgs_col.find_one({"_id": mid}), timeout=4)
            except Exception:
                full_meta = None
        results.append({
            "id": mid,
            "score": float(score) if score is not None else None,
            "source": meta.get("source", ""),
            "brief": meta.get("brief", ""),
            "full_meta": full_meta
        })
    return {"count": len(results), "results": results}


async def image_search_upsert(
    craft_id: Optional[str],
    image_url: Optional[str],
    metadata: Optional[str]
):
    """
    Controller logic for upserting an image.
    """
    await ensure_db_ready_or_502()
    imgs_col = collection("image_index")

    if not image_url:
        raise HTTPException(status_code=400, detail="image_url is required")

    # parse metadata if provided as JSON string
    meta_obj: Any = {}
    if metadata:
        try:
            meta_obj = _json.loads(metadata)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid metadata JSON")

    # fetch & embed
    pil_img = await _fetch_image_from_url(image_url)
    vec = await _embed_image(pil_img)

    # determine doc id
    doc_id = craft_id or f"url::{hash(image_url)}"

    # prepare pinecone metadata and upsert
    pine_meta = {
        "source": image_url,
        "brief": meta_obj.get("title", "") if isinstance(meta_obj, dict) else ""
    }
    upsert_resp = await _upsert_pinecone(doc_id, vec, pine_meta)

    # store full metadata into Mongo (async)
    doc = {
        "_id": doc_id,
        "source": image_url,
        "meta": meta_obj,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    try:
        await imgs_col.replace_one({"_id": doc_id}, doc, upsert=True)
    except Exception as e:
        # non-fatal: return response but alert user that mongo write failed
        safe_pine = {}
        try:
            if isinstance(upsert_resp, dict):
                safe_pine = upsert_resp
            else:
                upserted_count = getattr(upsert_resp, "upserted_count", None) or (upsert_resp.get("upserted_count") if hasattr(upsert_resp, "get") else None)
                safe_pine = {"upserted_count": int(upserted_count) if upserted_count is not None else None}
        except Exception:
            safe_pine = {"info": "pinecone response (unserializable)"}

        return {
            "status": "partial",
            "detail": f"pinecone_upsert: {safe_pine}, mongo_error: {str(e)}",
            "doc_id": doc_id
        }

    pinecone_safe = _normalize_pinecone_resp(upsert_resp)

    return {"status": "ok", "pinecone": pinecone_safe, "doc_id": doc_id}


# --- Metadata Search Controller Logic ---

# Initialize Pinecone client for text search
if not PINECONE_API_KEY:
    raise RuntimeError("PINECONE_API_KEY not set in .env")

pc_text = Pinecone(api_key=PINECONE_API_KEY, environment=PINECONE_ENV)
text_index = pc_text.Index(PINECONE_TEXT_INDEX)

def build_meta_text(artisan: QueryArtisan, art: QueryArt) -> str:
    """Local helper to build metadata string."""
    parts = [
        (artisan.name or "").strip(),
        (artisan.location or "").strip(),
        (art.name or "").strip(),
        (art.description or "").strip()
    ]
    return " ".join([p for p in parts if p])

def compute_boost(candidate_meta: dict, q_artisan: QueryArtisan) -> float:
    """Local helper to compute re-rank boost."""
    boost = 0.0
    # exact aadhaar match (strong)
    if q_artisan.aadhaar_number and candidate_meta.get("artisan", {}).get("aadhaar_number") == q_artisan.aadhaar_number:
        boost += 0.30
    # exact artisan name (small)
    if q_artisan.name and candidate_meta.get("artisan", {}).get("name", "").lower() == q_artisan.name.lower():
        boost += 0.07
    # exact location (small)
    if q_artisan.location and candidate_meta.get("artisan", {}).get("location", "").lower() == q_artisan.location.lower():
        boost += 0.05
    return boost

def metadata_search(payload: QuerySchema):
    """
    Controller logic for metadata search.
    Note: This is synchronous as embed_text is synchronous.
    """
    # 1) build meta_text for query (exclude photo_url)
    meta_text = build_meta_text(payload.artisan, payload.art)

    if not meta_text:
        raise HTTPException(status_code=400, detail="Empty metadata text for similarity search")

    # 2) embed
    q_vec = embed_text(meta_text)   # numpy normalized vector

    # 3) query Pinecone (top_k)
    try:
        res = text_index.query(vector=q_vec.tolist(), top_k=payload.top_k, include_metadata=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pinecone query failed: {e}")

    # 4) normalize results structure across SDK versions
    matches = []
    if isinstance(res, dict) and "matches" in res:
        matches = res["matches"]
    elif hasattr(res, "matches"):
        matches = res.matches
    else:
        matches = res

    # 5) compute composite score: use returned score (cosine) + small field boosts
    out = []
    for m in matches:
        # normalized access
        mid = m["id"] if isinstance(m, dict) else getattr(m, "id", None)
        score = m.get("score") if isinstance(m, dict) else getattr(m, "score", 0.0)
        meta = m.get("metadata") if isinstance(m, dict) else getattr(m, "metadata", {}) or {}

        # apply tiny boosts from exact fields in the query
        boost = compute_boost(meta, payload.artisan)
        final_score = float(score) + boost

        out.append({
            "id": mid,
            "score": round(float(score), 4),
            "final_score": round(final_score, 4),
            "metadata": meta
        })

    # 6) sort by final_score desc and return top_k
    out_sorted = sorted(out, key=lambda x: x["final_score"], reverse=True)[:payload.top_k]

    return {"query_meta_text": meta_text, "results": out_sorted}