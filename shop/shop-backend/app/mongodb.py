# app/mongodb.py
import os
import asyncio
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ReturnDocument
from pymongo.errors import ServerSelectionTimeoutError

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME", "masterip_db")

# Global client/db objects (may be reused across warm invocations)
_client: Optional[AsyncIOMotorClient] = None
_db = None

def _make_client():
    # serverSelectionTimeoutMS ensures we fail fast if DB is unreachable
    return AsyncIOMotorClient(MONGO_URI, serverSelectionTimeoutMS=3000)

async def ensure_initialized():
    """
    Ensure global _client and _db are initialized.
    Safe to call from endpoint handlers in serverless env.
    """
    global _client, _db

    if _db is not None:
        return

    if not MONGO_URI:
        raise RuntimeError("MONGO_URI not set in environment")

    # create client (non-awaitable), then try a quick ping to verify connectivity
    try:
        if _client is None:
            _client = _make_client()
            # small delay to let client init; optional
            await asyncio.sleep(0)
        # quick ping to confirm server reachable
        await _client.admin.command("ping")
        _db = _client[DB_NAME]
    except ServerSelectionTimeoutError as e:
        # close client on failure to avoid dangling resources
        try:
            _client.close()
        except Exception:
            pass
        _client = None
        raise RuntimeError(f"Cannot connect to MongoDB (timeout). Check MONGO_URI and network. {e}") from e
    except Exception as e:
        # any other errors
        try:
            _client.close()
        except Exception:
            pass
        _client = None
        raise RuntimeError(f"MongoDB init error: {e}") from e

def collection(name: str):
    """
    Return a collection object. Must call ensure_initialized() before this in async code.
    """
    if _db is None:
        raise RuntimeError("Database not initialized")
    return _db[name]

async def next_sequence(name: str) -> int:
    """
    Atomic counter using a counters collection. Make sure init was called.
    """
    if _db is None:
        raise RuntimeError("Database not initialized")
    counters = _db["counters"]
    doc = await counters.find_one_and_update(
        {"_id": name},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=ReturnDocument.AFTER
    )
    return int(doc["seq"])

def close():
    global _client, _db
    try:
        if _client:
            _client.close()
    finally:
        _client = None
        _db = None
