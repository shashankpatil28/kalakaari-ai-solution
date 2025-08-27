# ip_agent/tools.py
import os
import io
import json
import base64
import hashlib
from typing import Dict, Any

# Optional heavy deps
try:
    from PIL import Image  # Pillow
except Exception:
    Image = None

try:
    import numpy as np
except Exception:
    np = None

try:
    import faiss  # faiss-cpu or faiss-gpu
except Exception:
    faiss = None

try:
    import torch
    from transformers import CLIPProcessor, CLIPModel
except Exception:
    torch = None
    CLIPProcessor = None
    CLIPModel = None

import requests


# ---------------------------
# Config
# ---------------------------
FAISS_INDEX_FILE = os.getenv("FAISS_INDEX_FILE", "artwork_index.faiss")
EMBEDDING_DIM = 512
SIMILARITY_THRESHOLD = float(os.getenv("SIMILARITY_THRESHOLD", "0.95"))  # cosine threshold
CLIP_MODEL_NAME = os.getenv("CLIP_MODEL_NAME", "openai/clip-vit-base-patch32")

# Fallback store for exact/hash matching (if FAISS/CLIP unavailable)
HASH_STORE_FILE = os.getenv("ARTWORK_HASH_STORE", "artwork_hashes.json")


# ---------------------------
# Lazy singletons
# ---------------------------
_MODEL = None
_PROCESSOR = None
_FAISS_INDEX = None


def _safe_load_hash_store() -> Dict[str, bool]:
    try:
        if os.path.exists(HASH_STORE_FILE):
            with open(HASH_STORE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {}


def _safe_save_hash_store(store: Dict[str, bool]) -> None:
    try:
        with open(HASH_STORE_FILE, "w", encoding="utf-8") as f:
            json.dump(store, f)
    except Exception:
        pass


def _load_clip() -> None:
    """Load CLIP model & processor once (if available)."""
    global _MODEL, _PROCESSOR
    if _MODEL is None or _PROCESSOR is None:
        if CLIPModel is None or CLIPProcessor is None or torch is None:
            raise RuntimeError("CLIP/torch not available for embedding.")
        device = "cuda" if torch.cuda.is_available() else "cpu"
        _MODEL = CLIPModel.from_pretrained(CLIP_MODEL_NAME).to(device)
        _MODEL.eval()
        _PROCESSOR = CLIPProcessor.from_pretrained(CLIP_MODEL_NAME)


def _load_faiss() -> None:
    """Load or create FAISS index (if available)."""
    global _FAISS_INDEX
    if faiss is None:
        raise RuntimeError("FAISS not available for similarity search.")
    if _FAISS_INDEX is None:
        if os.path.exists(FAISS_INDEX_FILE):
            _FAISS_INDEX = faiss.read_index(FAISS_INDEX_FILE)
        else:
            _FAISS_INDEX = faiss.IndexFlatIP(EMBEDDING_DIM)  # Cosine via normalized dot product


# --- replace in ip_agent/tools.py ---

import re
from typing import Any

_B64_STD_ALPHABET = re.compile(r"[A-Za-z0-9+/=]+")
_B64_STD_STRICT   = re.compile(r"^[A-Za-z0-9+/]+={0,2}$")
_B64_URL_ALPHABET = re.compile(r"[A-Za-z0-9_\-=]+")
_B64_URL_STRICT   = re.compile(r"^[A-Za-z0-9_\-]+={0,2}$")

def _clean_b64(s: str) -> str:
    """Normalize whitespace and strip quotes and BOM-ish junk."""
    # common whitespace/newlines/tabs
    s = s.strip().replace("\n", "").replace("\r", "").replace("\t", "").replace(" ", "")
    # remove accidental surrounding quotes/backticks
    if len(s) >= 2 and ((s[0] == s[-1]) and s[0] in ("'", '"', "`")):
        s = s[1:-1]
    return s

def _pad_b64(s: str) -> str:
    """Right-pad '=' to make length a multiple of 4."""
    return s + ("=" * (-len(s) % 4))

def _is_urlsafe_b64(s: str) -> bool:
    # Heuristic: contains urlsafe chars and no '+' or '/'
    return ("-" in s or "_" in s) and ("+" not in s and "/" not in s)

def _decode_any_b64(s: str) -> bytes:
    """Try strict std b64, strict urlsafe, then forgiving fallbacks."""
    s = _clean_b64(s)

    # Data URL prefix?
    if ";base64," in s[:128]:
        s = s.split(",", 1)[1]
        s = _clean_b64(s)

    # Keep only characters from the relevant alphabet to drop junk
    if _is_urlsafe_b64(s):
        # filter to urlsafe alphabet
        s = "".join(_B64_URL_ALPHABET.findall(s))
        s = _pad_b64(s)
        try:
            return base64.urlsafe_b64decode(s)
        except Exception:
            pass  # try forgiving std decoder as a last resort
        s = "".join(_B64_STD_ALPHABET.findall(s))
        s = _pad_b64(s)
        return base64.b64decode(s, validate=False)
    else:
        # filter to standard alphabet
        s = "".join(_B64_STD_ALPHABET.findall(s))
        s = _pad_b64(s)
        try:
            return base64.b64decode(s, validate=True)
        except Exception:
            # last resort: non-strict (ignores non-alphabet chars)
            return base64.b64decode(s, validate=False)

def _find_first_base64_string(obj: Any) -> str | None:
    """
    Deep-scan JSON structure for the first plausible base64 string.
    Prioritize data URLs or long base64-looking chunks.
    """
    # Prefer standard structure if present and valid
    try:
        media = obj.get("product", [])[0].get("media", [])
        for item in media:
            if isinstance(item, str) and len(item) >= 32:
                return item
    except Exception:
        pass

    # Generic deep traversal
    stack = [obj]
    best_candidate = None
    while stack:
        cur = stack.pop()
        if isinstance(cur, dict):
            stack.extend(cur.values())
        elif isinstance(cur, list):
            stack.extend(cur)
        elif isinstance(cur, str):
            s = cur.strip()
            if "data:image" in s and ";base64," in s:
                return s
            # long-ish strings with mostly base64 alphabet
            if len(s) >= 64:
                # score by fraction of base64-ish chars
                no_ws = re.sub(r"\s", "", s)
                base_chars = len(_B64_STD_ALPHABET.findall(no_ws.replace("=", "")))
                # Very rough heuristic; prefer longer strings
                if base_chars >= 48:
                    if best_candidate is None or len(s) > len(best_candidate):
                        best_candidate = s
    return best_candidate

def _extract_base64_from_json(onboarding_data: str | dict) -> bytes:
    """
    Parse onboarding_data (JSON string or dict) and return decoded image bytes.
    Tries product[0].media first; if invalid/short, deep-scans entire object.
    """
    # Accept dicts too (in case caller passes an object by mistake)
    if isinstance(onboarding_data, (dict, list)):
        data = onboarding_data
    else:
        data = json.loads(onboarding_data)

    # 1) Try the canonical path
    candidate = None
    try:
        m0 = data["product"][0]["media"][0]
        if isinstance(m0, str):
            candidate = m0
    except Exception:
        candidate = None

    # 2) Validate candidate length; ignore suspiciously short strings
    if not candidate or len(candidate.strip()) < 32:
        candidate = _find_first_base64_string(data)

    if not candidate:
        raise ValueError("No plausible base64 image string found in onboarding_data.")

    # 3) Decode with robust strategy
    try:
        img_bytes = _decode_any_b64(candidate)
    except Exception as e:
        raise ValueError(f"Invalid base64 image data (after robust cleanup): {e}")

    # 4) Extra sanity: tiny outputs are likely bad inputs
    if len(img_bytes) < 256:  # ~0.25 KB — far too small for an image
        raise ValueError("Decoded image is unexpectedly small; input may not be a real base64 image.")

    return img_bytes



def _get_image_embedding(image_bytes: bytes) -> "np.ndarray":
    """Convert bytes -> PIL image -> CLIP embedding (L2-normalized)."""
    if Image is None:
        raise RuntimeError("Pillow (PIL) not available.")
    if np is None:
        raise RuntimeError("NumPy not available.")
    _load_clip()

    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    device = "cuda" if (torch is not None and torch.cuda.is_available()) else "cpu"

    with torch.no_grad():
        inputs = _PROCESSOR(images=image, return_tensors="pt").to(device)
        image_features = _MODEL.get_image_features(**inputs)
    embedding = image_features.cpu().numpy().astype("float32")
    # Normalize to use inner product as cosine similarity
    if faiss is not None:
        faiss.normalize_L2(embedding)
    else:
        # Manual L2 normalize (fallback)
        norm = np.linalg.norm(embedding, axis=1, keepdims=True) + 1e-12
        embedding = embedding / norm
    return embedding


def verify_artwork_uniqueness(onboarding_data: str) -> Dict[str, Any]:
    """
    Tool: checks whether the uploaded artwork already exists in the vector DB.
    Returns a dict like:
    {
      "status": "ok",
      "duplicate": False,
      "similarity": 0.87,
      "message": "UNIQUE: ...",
    }
    or on duplicate:
    {
      "status": "ok",
      "duplicate": True,
      "similarity": 0.98,
      "message": "DUPLICATE: ...",
    }
    or on failure:
    {
      "status": "error",
      "message": "reason"
    }
    """
    try:
        image_bytes = _extract_base64_from_json(onboarding_data)

        # Preferred path: CLIP + FAISS cosine similarity
        if (faiss is not None) and (CLIPModel is not None) and (CLIPProcessor is not None) and (torch is not None) and (np is not None) and (Image is not None):
            _load_faiss()
            embedding = _get_image_embedding(image_bytes)

            if _FAISS_INDEX.ntotal > 0:
                distances, _ = _FAISS_INDEX.search(embedding, 1)
                similarity = float(distances[0][0])  # cosine (since normalized)
            else:
                similarity = 0.0

            if similarity >= SIMILARITY_THRESHOLD:
                return {
                    "status": "ok",
                    "duplicate": True,
                    "similarity": similarity,
                    "message": f"An artwork with very high visual similarity already exists ({similarity*100:.2f}% match). We cannot proceed with IP creation for duplicates."
                }

            # Unique -> add to index and persist
            _FAISS_INDEX.add(embedding)
            faiss.write_index(_FAISS_INDEX, FAISS_INDEX_FILE)
            return {
                "status": "ok",
                "duplicate": False,
                "similarity": similarity,
                "message": "No sufficiently similar artwork found in our database. Proceeding with IP submission."
            }

        # Fallback path: exact-match via hash (keeps things errorless even without heavy deps)
        # NOTE: This is not cosine similarity, but ensures the tool never crashes.
        img_hash = hashlib.sha256(image_bytes).hexdigest()
        store = _safe_load_hash_store()
        if img_hash in store:
            return {
                "status": "ok",
                "duplicate": True,
                "similarity": 1.0,
                "message": "An identical image already exists in our records. We cannot proceed with duplicate IP creation."
            }
        store[img_hash] = True
        _safe_save_hash_store(store)
        return {
            "status": "ok",
            "duplicate": False,
            "similarity": 0.0,
            "message": "No identical artwork found (fallback check). Proceeding with IP submission."
        }

    except Exception as e:
        return {"status": "error", "message": f"Verification failed: {e}"}


def call_master_ip_service(onboarding_data: str) -> dict:
    """
    Existing tool (moved here): POSTs the onboarding_data JSON to the backend.
    """
    try:
        data_payload = json.loads(onboarding_data)
        url = os.getenv("MASTER_IP_ENDPOINT", "http://localhost:8001/create")
        response = requests.post(url, json=data_payload, timeout=30)
        response.raise_for_status()

        if response.status_code in [200, 201]:
            return {
                "status": "success",
                "message": "Your IP data has been successfully submitted for verification. We will notify you once the process is complete.",
                "response": response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text,
            }
        else:
            return {
                "status": "error",
                "message": f"An unexpected error occurred with the service. Status code: {response.status_code}"
            }

    except requests.exceptions.RequestException as e:
        return {"status": "error", "message": f"We are currently unable to connect to the IP service. Please try again later. Error: {e}"}
    except json.JSONDecodeError:
        return {"status": "error", "message": "The data format received was invalid. Please restart the process."}
    except Exception as e:
        return {"status": "error", "message": f"An unexpected error occurred during the submission process. Error: {e}"}
