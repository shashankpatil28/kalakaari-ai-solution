# app/utils/http_client.py
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from fastapi import HTTPException
from PIL import Image
from io import BytesIO
import asyncio

# Import config from constants
from app.constant import FETCH_HEADERS

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
            r = sess.get(url, headers=FETCH_HEADERS, timeout=timeout, stream=True, allow_redirects=True)
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


def decode_base64_to_pil(base64_string: str) -> Image.Image:
    """
    Decode a Base64 string (with or without data URI prefix) to a PIL Image.
    
    Args:
        base64_string: Base64 encoded image, optionally prefixed with 
                      'data:image/...;base64,' or similar data URI format.
    
    Returns:
        PIL.Image in RGB mode
    
    Raises:
        HTTPException(400) if decoding fails
    """
    import base64
    import re
    
    try:
        # Strip data URI prefix if present (e.g., "data:image/jpeg;base64,")
        if base64_string.startswith('data:'):
            # Extract just the base64 part after the comma
            match = re.match(r'data:image/[^;]+;base64,(.+)', base64_string)
            if match:
                base64_string = match.group(1)
            else:
                # Fallback: try to split by comma
                parts = base64_string.split(',', 1)
                if len(parts) == 2:
                    base64_string = parts[1]
        
        # Decode base64 to bytes
        image_bytes = base64.b64decode(base64_string)
        
        # Convert to PIL Image
        img = Image.open(BytesIO(image_bytes)).convert("RGB")
        return img
        
    except Exception as e:
        raise HTTPException(
            status_code=400, 
            detail=f"Failed to decode Base64 image: {e}"
        )