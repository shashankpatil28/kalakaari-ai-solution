# app/mongodb.py
import os
import asyncio
from typing import Optional
from pathlib import Path # <-- NEW IMPORT

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ReturnDocument
from pymongo.errors import ServerSelectionTimeoutError
from dotenv import load_dotenv

DOTENV_PATH = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=DOTENV_PATH)

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME", "masterip_db")

# Global client/db objects
_client: Optional[AsyncIOMotorClient] = None
_db = None

def _make_client():
    # serverSelectionTimeoutMS ensures we fail fast if DB is unreachable
    return AsyncIOMotorClient(MONGO_URI, serverSelectionTimeoutMS=3000)

async def connect_to_mongo():
    """
    Initialize global _client and _db.
    Called once on application startup.
    """
    global _client, _db

    if not MONGO_URI:
        raise RuntimeError("MONGO_URI not set in environment")

    print("Attempting to connect to MongoDB...")
    try:
        _client = _make_client()
        # quick ping to confirm server reachable
        await _client.admin.command("ping")
        _db = _client[DB_NAME]
        print(f"Successfully connected to MongoDB, database: '{DB_NAME}'")
    except ServerSelectionTimeoutError as e:
        # close client on failure
        try:
            _client.close()
        except Exception:
            pass
        _client = None
        _db = None
        raise RuntimeError(f"Cannot connect to MongoDB (timeout). Check MONGO_URI and network. {e}") from e
    except Exception as e:
        try:
            _client.close()
        except Exception:
            pass
        _client = None
        _db = None
        raise RuntimeError(f"MongoDB init error: {e}") from e

def close_mongo_connection():
    """
    Close the global _client.
    Called once on application shutdown.
    """
    global _client, _db
    try:
        if _client:
            _client.close()
            print("MongoDB connection closed.")
    finally:
        _client = None
        _db = None

def collection(name: str):
    """
    Return a collection object. Assumes connect_to_mongo() was called.
    """
    if _db is None:
        raise RuntimeError("Database not initialized. Ensure connect_to_mongo() was called on startup.")
    return _db[name]

async def next_sequence(name: str) -> int:
    """
    Atomic counter using a counters collection.
    """
    if _db is None:
        raise RuntimeError("Database not initialized. Ensure connect_to_mongo() was called on startup.")
    counters = _db["counters"]
    doc = await counters.find_one_and_update(
        {"_id": name},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=ReturnDocument.AFTER
    )
    return int(doc["seq"])

# Removed the old 'close()' and 'ensure_initialized()' functions