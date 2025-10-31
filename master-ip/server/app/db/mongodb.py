import asyncio
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ReturnDocument
from pymongo.errors import ServerSelectionTimeoutError
import logging # For logging startup/shutdown

# Import config from constants
from app.constant import MONGO_URI, DB_NAME

logger = logging.getLogger(__name__)

# Global client/db objects - managed by lifespan events
_client: Optional[AsyncIOMotorClient] = None
_db = None

async def connect_db():
    """Connects to MongoDB on application startup."""
    global _client, _db
    logger.info("Connecting to MongoDB...")
    if not MONGO_URI:
        # Fail fast during startup if URI is missing
        raise RuntimeError("MONGO_URI not set in environment")

    try:
        _client = AsyncIOMotorClient(
            MONGO_URI,
            serverSelectionTimeoutMS=5000 # Increased timeout for initial connection
        )
        # Verify connection by pinging
        await _client.admin.command("ping")
        _db = _client[DB_NAME]
        logger.info(f"Successfully connected to MongoDB database: {DB_NAME}")
    except ServerSelectionTimeoutError as e:
        logger.error(f"MongoDB connection failed (timeout). Check MONGO_URI and network. Error: {e}")
        # Reraise to prevent app startup if connection fails
        raise RuntimeError(f"Cannot connect to MongoDB (timeout): {e}") from e
    except Exception as e:
        logger.error(f"An unexpected error occurred during MongoDB connection: {e}")
        # Reraise to prevent app startup
        raise RuntimeError(f"MongoDB init error: {e}") from e

async def close_db():
    """Closes the MongoDB connection on application shutdown."""
    global _client, _db
    if _client:
        logger.info("Closing MongoDB connection...")
        _client.close()
        _client = None
        _db = None
        logger.info("MongoDB connection closed.")

def get_db():
    """Returns the database instance. Assumes connect_db was called."""
    if _db is None:
        # This should ideally not happen if lifespan events are used correctly
        raise RuntimeError("Database connection not initialized. Ensure connect_db() was called.")
    return _db

def collection(name: str):
    """Returns a collection object from the initialized database."""
    db = get_db() # Get the initialized DB object
    return db[name]

async def next_sequence(name: str) -> int:
    """Atomic counter using a counters collection."""
    # Uses get_db() indirectly via collection()
    counters = collection("counters")
    doc = await counters.find_one_and_update(
        {"_id": name},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=ReturnDocument.AFTER
    )
    # Ensure doc is not None before accessing 'seq'
    if doc is None:
        # This might happen on the very first call if upsert takes time
        # Retry once or handle as appropriate
        logger.warning(f"Upsert for sequence '{name}' did not return document immediately, retrying find.")
        doc = await counters.find_one({"_id": name})
        if doc is None:
             raise RuntimeError(f"Failed to create or find sequence counter '{name}'")

    return int(doc.get("seq", 0)) # Added .get with default

# Keep the close() function for potential manual reset if needed,
# though lifespan manager handles normal shutdown.
def close():
    """Manual close function (less used with lifespan)."""
    close_db() # Call the async version wrapper if needed, or just reuse logic
