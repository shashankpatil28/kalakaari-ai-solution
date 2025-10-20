# app/routes/craft-controllers.py
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Request
import os
import hashlib
import jwt
from datetime import datetime, timedelta
import asyncio
from typing import Optional, Any
from pathlib import Path

from app.models import OnboardingData
from app.mongodb import ensure_initialized, collection, next_sequence, close as mongo_close

# Image + embedding imports
from io import BytesIO
import requests
from PIL import Image
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]  # go up from /server/app/routes/ to /master-ip
IMAGE_SEARCH_PATH = REPO_ROOT / "image_search"
if str(IMAGE_SEARCH_PATH) not in sys.path:
    sys.path.insert(0, str(IMAGE_SEARCH_PATH))

from clip_embedder import ClipEmbedder
from pinecone import Pinecone

# networking helpers
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

router = APIRouter()
SECRET_KEY = os.getenv("SECRET_KEY", "change_in_prod")
ALGORITHM = "HS256"

# Pinecone env (used by image routes)
PINECONE_API_KEY = os.environ.get("PINECONE_API_KEY")
INDEX_HOST = os.environ.get("INDEX_HOST")  # example: test1-xxxx.pinecone.io

# Single embedder instance (lazy)
_embedder: Optional[ClipEmbedder] = None

# Browser-like headers for fetching images (helps with CDNs)
_FETCH_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0 Safari/537.36",
    "Accept": "image/*,*/*;q=0.8",
    "Referer": "https://upload.wikimedia.org/"
}


async def ensure_db_ready_or_502():
    """
    Helper: ensure db is ready. If first attempt fails, reset client and retry.
    Raises HTTPException(status_code=502) on failure.
    """
    try:
        await ensure_initialized()
    except Exception as e:
        # attempt to recover by closing client and retrying
        try:
            mongo_close()
            await ensure_initialized()
        except Exception as e2:
            raise HTTPException(status_code=502, detail=f"DB init error: {e}; retry failed: {e2}")


# -----------------------
# Existing create route (unchanged)
# -----------------------
@router.post("/create")
async def create_craftid(data: OnboardingData):
    # ensure DB is initialized (with recovery)
    await ensure_db_ready_or_502()

    coll = collection("craftids")

    art_name_norm = data.art.name.strip().lower()

    # check uniqueness
    try:
        existing = await asyncio.wait_for(coll.find_one({"art_name_norm": art_name_norm}), timeout=4)
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="DB read timed out")
    except Exception as e:
        # if this error occurs, try a recovery once
        try:
            mongo_close()
            await ensure_db_ready_or_502()
            coll = collection("craftids")
            existing = await asyncio.wait_for(coll.find_one({"art_name_norm": art_name_norm}), timeout=4)
        except Exception as e2:
            raise HTTPException(status_code=500, detail=f"DB read error: {e}; recovery error: {e2}")

    if existing:
        raise HTTPException(
            status_code=409,
            detail="A similar product name already exists. Please provide a more unique name."
        )

    # allocate atomic sequence
    try:
        seq = await asyncio.wait_for(next_sequence("craftid_seq"), timeout=4)
    except Exception as e:
        # try recovery once
        try:
            mongo_close()
            await ensure_db_ready_or_502()
            seq = await asyncio.wait_for(next_sequence("craftid_seq"), timeout=4)
        except Exception as e2:
            raise HTTPException(status_code=502, detail=f"Failed to allocate public id: {e}; recovery: {e2}")

    public_id = f"CID-{seq:05d}"

    payload = {"public_id": public_id, "exp": datetime.utcnow() + timedelta(days=365)}
    private_key = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    public_hash = hashlib.sha256(
        (data.art.name + data.art.description + data.art.photo).encode()
    ).hexdigest()

    doc = {
        "public_id": public_id,
        "private_key": private_key,
        "public_hash": public_hash,
        "art_name_norm": art_name_norm,
        "original_onboarding_data": data.dict(),
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

    try:
        await coll.insert_one(doc)
    except Exception as e:
        # try recovery once if insert fails
        try:
            mongo_close()
            await ensure_db_ready_or_502()
            coll = collection("craftids")
            await coll.insert_one(doc)
        except Exception as e2:
            raise HTTPException(status_code=500, detail=f"DB insert error: {e}; recovery: {e2}")

    transaction_id = "tx_" + datetime.utcnow().strftime("%Y%m%d%H%M%S")

    response_data = {
        "status": "success",
        "message": f"Your CraftID for '{data.art.name}' has been created successfully.",
        "transaction_id": transaction_id,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "verification": {
            "public_id": public_id,
            "private_key": private_key,
            "public_hash": public_hash,
            "verification_url": f"/verify/{public_id}",
            "qr_code_link": f"/verify/qr/{public_id}"
        },
        "artisan_info": {
            "name": data.artisan.name,
            "location": data.artisan.location
        },
        "art_info": {
            "name": data.art.name,
            "description": data.art.description
        },
        "original_onboarding_data": data.dict(),
        "links": {
            "track_status": f"/status/{transaction_id}",
            "shop_listing": f"/shop/{public_id}"
        }
    }
    return response_data


# -----------------------
# Image-search helpers (URL-only flow)
# -----------------------
def _ensure_embedder():
    global _embedder
    if _embedder is None:
        _embedder = ClipEmbedder()
    return _embedder


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


def _requests_session_with_retries(total_retries: int = 2, backoff_factor: float = 0.3):
    s = requests.Session()
    retries = Retry(
        total=total_retries,
        backoff_factor=backoff_factor,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET", "POST")
    )
    adapter = HTTPAdapter(max_retries=retries)
    s.mount("https://", adapter)
    s.mount("http://", adapter)
    return s


async def _fetch_image_from_url(url: str, timeout: int = 10) -> Image.Image:
    """
    Fetch image bytes from the given URL and return a PIL.Image (RGB).
    Uses browser-like headers + retries and checks content-type.
    Raises HTTPException(400) on bad URLs or non-image responses.
    """
    def _fetch():
        sess = _requests_session_with_retries(total_retries=2, backoff_factor=0.5)
        try:
            r = sess.get(url, headers=_FETCH_HEADERS, timeout=timeout, stream=True, allow_redirects=True)
            r.raise_for_status()
        except Exception as e:
            raise RuntimeError(f"HTTP fetch failed: {e}")

        ct = r.headers.get("content-type", "")
        if not ct or not ct.startswith("image/"):
            raise RuntimeError(f"URL did not return an image (content-type={ct})")

        MAX_BYTES = 15 * 1024 * 1024
        data = b""
        try:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    data += chunk
                    if len(data) > MAX_BYTES:
                        raise RuntimeError("Image too large")
        finally:
            r.close()

        from io import BytesIO
        try:
            img = Image.open(BytesIO(data)).convert("RGB")
        except Exception as e:
            raise RuntimeError(f"Failed to parse image bytes: {e}")
        return img

    try:
        pil_img = await asyncio.to_thread(_fetch)
        return pil_img
    except RuntimeError as re:
        raise HTTPException(status_code=400, detail=f"Failed to fetch image: {re}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch image: {e}")


async def _embed_image(pil_img: Image.Image) -> list:
    embedder = _ensure_embedder()
    try:
        vec = await asyncio.to_thread(embedder.embed_pil, pil_img)
        return vec
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Embedding error: {e}")


async def _query_pinecone(vec: list, top_k: int = 5) -> list:
    idx = _get_pinecone_index()

    def _q():
        try:
            return idx.query(vector=vec, top_k=top_k, include_metadata=True)
        except TypeError:
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
            return idx.upsert(vectors=[(doc_id, vec, pine_meta)])
        except TypeError:
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


# -----------------------
# Image-search routes (URL-only)
# -----------------------

@router.post("/image-search/url")
async def image_search_url(image_url: str = Form(...), top_k: int = Form(5), include_meta: bool = Form(True)):
    """
    Provide an image_url (public or signed) and get top-k similar items.
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


@router.post("/image-search/upsert")
async def image_search_upsert(
    request: Request,
    craft_id: Optional[str] = Form(None),
    image_url: Optional[str] = Form(None),
    metadata: Optional[str] = Form(None)  # accept JSON string in form
):
    """
    Upsert a new image vector + metadata from an image URL and metadata JSON.
    metadata: JSON string or can be omitted.
    Returns the doc_id and upsert response.
    """
    await ensure_db_ready_or_502()
    imgs_col = collection("image_index")

    if not image_url:
        raise HTTPException(status_code=400, detail="image_url is required")

    # parse metadata if provided as JSON string
    meta_obj: Any = {}
    if metadata:
        try:
            import json as _json
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

    # Success: normalize pinecone response into a simple dict
    def _normalize_pinecone_resp(r):
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

    pinecone_safe = _normalize_pinecone_resp(upsert_resp)

    return {"status": "ok", "pinecone": pinecone_safe, "doc_id": doc_id}
