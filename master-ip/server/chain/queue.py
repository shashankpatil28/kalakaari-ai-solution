import os
import asyncio
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional
from pymongo import ReturnDocument # Import needed
from app.db.mongodb import collection
# Make sure to import from constants.py (plural)
from app.constant import VISIBILITY_TIMEOUT_SECONDS, MAX_RETRIES

QUEUE_COLL = os.getenv("ANCHOR_QUEUE_COLL", "anchor_queue")

async def enqueue_item(doc: Dict) -> None:
    """
    doc must contain: public_id, public_hash, timestamp
    """
    doc2 = dict(doc)
    doc2.setdefault("status", "queued")
    doc2.setdefault("tries", 0)
    doc2.setdefault("created_at", datetime.now(timezone.utc).isoformat())
    doc2.setdefault("locked_until", None) # For visibility timeout
    doc2.setdefault("last_error", None)
    doc2.setdefault("last_try", None)
    await collection(QUEUE_COLL).insert_one(doc2)

async def fetch_one_and_lock() -> Optional[Dict]:
    """
    Atomically fetches one item, marks it as processing, and sets a visibility timeout.
    Returns the item or None if queue is empty or items are locked.
    """
    coll = collection(QUEUE_COLL)
    now = datetime.now(timezone.utc)
    lock_until_time = now + timedelta(seconds=VISIBILITY_TIMEOUT_SECONDS)

    # Query for items that are queued OR processing but timed out
    query = {
        "status": {"$in": ["queued", "requeued"]}, # Or just "queued" if you don't use "requeued" status
        "$or": [
            {"locked_until": {"$lt": now}},
            {"locked_until": None}
        ]
    }
    
    # Correct query: Find items that are "queued" OR "processing" but timed out
    query_robust = {
        "$or": [
            {"status": "queued"},
            {"status": "processing", "locked_until": {"$lt": now}}
        ]
    }

    # Atomically find one matching item and update it
    updated_doc = await coll.find_one_and_update(
        query_robust,
        {
            "$set": {
                "status": "processing",
                "locked_until": lock_until_time,
                "last_try": now.isoformat()
            },
            "$inc": {"tries": 1} # Increment tries on every attempt
        },
        sort=[("created_at", 1)], # Process oldest first
        return_document=ReturnDocument.AFTER # Return the updated document
    )
    return updated_doc # Returns None if no document matched the query

async def mark_done(public_id: str, tx_hash: str, anchored_at_iso: str) -> None:
    """Marks an item as done if it was in processing state."""
    await collection(QUEUE_COLL).update_one(
        {"public_id": public_id, "status": "processing"}, # Ensure we only update items we locked
        {"$set": {"status": "anchored", "tx_hash": tx_hash, "anchored_at": anchored_at_iso, "locked_until": None}}
    )

async def mark_failed(public_id: str, reason: str, is_permanent: bool = False) -> None:
    """Increments tries and marks as failed if max retries reached or if permanent."""
    coll = collection(QUEUE_COLL)
    now_iso = datetime.now(timezone.utc).isoformat()

    # Find the item to get current tries count
    item = await coll.find_one({"public_id": public_id, "status": "processing"})
    if not item:
        print(f"Warning: Could not find item {public_id} in processing state to mark as failed.")
        return

    current_tries = item.get("tries", 0) # Tries was already incremented by fetch_one_and_lock
    
    update_doc = {
        "$set": {
            "last_error": reason,
            "last_try": now_iso,
             # Unlock immediately on failure to allow retry
            "locked_until": None 
        }
    }

    if is_permanent or current_tries >= MAX_RETRIES:
        # Max retries reached or permanent error, mark as permanently failed (DLQ)
        update_doc["$set"]["status"] = "failed"
        print(f"Item {public_id} reached max retries ({current_tries}/{MAX_RETRIES}) or had permanent error. Moving to 'failed' state.")
    else:
        # Still retryable, set back to queued
        update_doc["$set"]["status"] = "queued"
        print(f"Item {public_id} failed, attempt {current_tries}/{MAX_RETRIES}. Re-queueing.")


    await coll.update_one(
        {"public_id": public_id, "status": "processing"}, # Only update if still processing
        update_doc
    )

async def fetch_failed_items(limit: int = 10) -> List[Dict]:
     """Optional Helper for DLQ Inspection."""
     coll = collection(QUEUE_COLL)
     cursor = coll.find({"status": "failed"}).sort("last_try", -1).limit(limit)
     return await cursor.to_list(length=limit)