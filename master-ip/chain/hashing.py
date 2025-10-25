# master-ip/server/chain/hashing.py
import json
import hashlib
from typing import Dict, Optional

def canonical_obj(artisan: Dict, art: Dict, timestamp_iso: str, salt: Optional[str] = "") -> Dict:
    return {
        "artisan": {
            "name": (artisan.get("name") or "").strip(),
            "location": (artisan.get("location") or "").strip(),
            "contact_number": (artisan.get("contact_number") or "").strip(),
            "email": (artisan.get("email") or "").strip(),
            "aadhaar_number": (artisan.get("aadhaar_number") or "").strip(),
        },
        "art": {
            "name": (art.get("name") or "").strip(),
            "description": (art.get("description") or "").strip()
        },
        "timestamp": timestamp_iso,
        "salt": (salt or "").strip()
    }

def compute_public_hash(artisan: Dict, art: Dict, timestamp_iso: str, salt: Optional[str] = "") -> str:
    """
    Deterministic SHA-256 hex hash of canonical JSON.
    Returns lowercase hex string (without 0x).
    """
    obj = canonical_obj(artisan, art, timestamp_iso, salt)
    s = json.dumps(obj, separators=(",", ":"), sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(s.encode("utf-8")).hexdigest()
