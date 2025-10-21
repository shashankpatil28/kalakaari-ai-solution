# app/utils/db_utils.py
import asyncio
from fastapi import HTTPException
from app.db.mongodb import ensure_initialized, close as mongo_close

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