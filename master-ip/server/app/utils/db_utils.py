from fastapi import HTTPException
from app.db.mongodb import get_db # Import get_db instead of ensure_initialized

async def ensure_db_ready_or_502():
    """
    Checks if the database connection (initialized at startup) is available.
    Raises HTTPException(502) if connection was lost or failed startup.
    """
    try:
        # Simple check: try to get the DB object.
        # This will raise RuntimeError if _db is None.
        db = get_db()
        # Optionally add a quick ping if needed for extra safety,
        # but generally relies on startup success.
        # await db.command("ping")
    except RuntimeError as e:
        # This happens if the lifespan manager failed to set _db
        raise HTTPException(status_code=502, detail=f"Database connection not available: {e}")
    except Exception as e:
        # Catch potential ping errors or other unexpected issues
        raise HTTPException(status_code=502, detail=f"Database health check failed: {e}")