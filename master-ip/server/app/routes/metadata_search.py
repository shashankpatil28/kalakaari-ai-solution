# /master-ip/server/app/routes/metadata_search.py
import os
from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from text_embedder import embed_text

load_dotenv()

# Pinecone new SDK
from pinecone import Pinecone

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENV = os.getenv("PINECONE_ENV")
INDEX_NAME = os.getenv("PINECONE_TEXT_INDEX", "text")
TOP_K_DEFAULT = 5

if not PINECONE_API_KEY:
    raise RuntimeError("PINECONE_API_KEY not set in .env")

pc = Pinecone(api_key=PINECONE_API_KEY, environment=PINECONE_ENV)
index = pc.Index(INDEX_NAME)

router = APIRouter(prefix="/metadata", tags=["metadata"])

# --- Pydantic schemas (matches your final JSON schema) ---
class Artisan(BaseModel):
    name: Optional[str] = ""
    location: Optional[str] = ""
    contact_number: Optional[str] = ""
    email: Optional[str] = ""
    aadhaar_number: Optional[str] = ""

class Art(BaseModel):
    name: Optional[str] = ""
    description: Optional[str] = ""
    photo_url: Optional[str] = ""   # ignored for embeddings

class QuerySchema(BaseModel):
    artisan: Artisan
    art: Art
    top_k: Optional[int] = TOP_K_DEFAULT

# --- helper: build meta text (ignore photo_url) ---
def build_meta_text(artisan: Artisan, art: Art) -> str:
    parts = [
        (artisan.name or "").strip(),
        (artisan.location or "").strip(),
        (art.name or "").strip(),
        (art.description or "").strip()
    ]
    return " ".join([p for p in parts if p])

# --- tiny re-rank boost function ---
def compute_boost(candidate_meta: dict, q_artisan: Artisan) -> float:
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

@router.post("/search")
def metadata_search(payload: QuerySchema):
    # 1) build meta_text for query (exclude photo_url)
    meta_text = build_meta_text(payload.artisan, payload.art)

    if not meta_text:
        raise HTTPException(status_code=400, detail="Empty metadata text for similarity search")

    # 2) embed
    q_vec = embed_text(meta_text)   # numpy normalized vector

    # 3) query Pinecone (top_k)
    try:
        res = index.query(vector=q_vec.tolist(), top_k=payload.top_k, include_metadata=True)
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
