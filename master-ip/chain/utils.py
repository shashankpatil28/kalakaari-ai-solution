# master-ip/server/chain/utils.py
import asyncio
import logging
from datetime import datetime, timezone
import time

# ---------- Logging ----------
def get_logger(name: str = "chain") -> logging.Logger:
    """
    Returns a logger with consistent formatting.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        fmt = logging.Formatter("[%(asctime)s] [%(levelname)s] %(name)s: %(message)s")
        handler.setFormatter(fmt)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger

# ---------- Time ----------
def utc_now_iso() -> str:
    """UTC timestamp in ISO format (Z suffix)."""
    return datetime.utcnow().replace(tzinfo=timezone.utc).isoformat()

def sleep(seconds: float):
    """Async-friendly sleep helper."""
    return asyncio.sleep(seconds)

# ---------- Retry ----------
async def with_retries(coro_func, *args, retries=3, delay=3, backoff=2, logger=None, **kwargs):
    """
    Generic retry helper for async operations.
    Retries a coroutine up to N times with exponential backoff.
    """
    attempt = 0
    while attempt < retries:
        try:
            return await coro_func(*args, **kwargs)
        except Exception as e:
            attempt += 1
            if logger:
                logger.warning(f"[Retry {attempt}/{retries}] {e}")
            if attempt >= retries:
                raise
            await asyncio.sleep(delay)
            delay *= backoff
