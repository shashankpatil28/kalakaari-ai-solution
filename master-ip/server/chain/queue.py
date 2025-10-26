# master-ip/server/chain/queue.py
import os
import asyncio
from datetime import datetime, timezone
from typing import List, Dict, Optional
from app.mongodb import collection  # assumes your mongodb helper at app/mongodb.py

QUEUE_COLL = os.getenv("ANCHOR_QUEUE_COLL", "anchor_queue")
MAX_FETCH = int(os.getenv("QUEUE_FETCH_MAX", "5"))

async def enqueue_item(doc: Dict) -> None:
    """
    doc must contain: public_id, public_hash, timestamp, tries (optional)
    """
    doc2 = dict(doc)
    doc2.setdefault("status", "queued")
    doc2.setdefault("tries", 0)
    doc2.setdefault("created_at", datetime.utcnow().replace(tzinfo=timezone.utc).isoformat())
    await collection(QUEUE_COLL).insert_one(doc2)

async def fetch_next_batch(limit: int = MAX_FETCH) -> List[Dict]:
    coll = collection(QUEUE_COLL)
    cursor = coll.find({"status": "queued"}).sort("created_at", 1).limit(limit)
    return await cursor.to_list(length=limit)

async def mark_done(public_id: str, tx_hash: str, anchored_at_iso: str) -> None:
    await collection(QUEUE_COLL).update_one({"public_id": public_id}, {"$set": {"status": "anchored", "tx_hash": tx_hash, "anchored_at": anchored_at_iso}})

async def mark_failed(public_id: str, reason: str) -> None:
    await collection(QUEUE_COLL).update_one({"public_id": public_id}, {"$inc": {"tries": 1}, "$set": {"last_error": reason, "last_try": datetime.utcnow().isoformat()}})
