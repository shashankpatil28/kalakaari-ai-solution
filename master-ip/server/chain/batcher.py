# master-ip/server/chain/batcher.py
import asyncio
import os
import sys
from pathlib import Path
from datetime import datetime, timezone
from dotenv import load_dotenv

# Load environment variables FIRST
# batcher.py is in master-ip/chain/, .env is in master-ip/server/
env_path = Path(__file__).parent.parent / "server" / ".env"
load_dotenv(env_path)

# Ensure parent dir is in path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "server"))

from chain.utils import get_logger, utc_now_iso, sleep, with_retries
from chain.queue import fetch_next_batch, mark_done, mark_failed
from chain.web3_client import anchor_hash_on_chain
from app.db.mongodb import collection, ensure_initialized
logger = get_logger("chain.batcher")

BATCH_LIMIT = int(os.getenv("BATCH_LIMIT", "5"))
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", "10"))  # seconds between empty polls

async def process_item(it: dict):
    public_id = it["public_id"]
    public_hash = it["public_hash"]
    logger.info(f"Anchoring item {public_id} on-chain...")
    try:
        # anchor hash on chain (with wait for receipt)
        tx_hash = await asyncio.to_thread(anchor_hash_on_chain, public_hash, public_id, True)
        anchored_at = utc_now_iso()

        await mark_done(public_id, tx_hash, anchored_at)
        await collection("craftids").update_one(
            {"public_id": public_id},
            {"$set": {"status": "anchored", "tx_hash": tx_hash, "anchored_at": anchored_at}}
        )
        logger.info(f"✅ Anchored {public_id} | tx: {tx_hash[:10]}...")
    except Exception as e:
        await mark_failed(public_id, str(e))
        logger.error(f"❌ Failed {public_id}: {e}")

async def process_once(limit=BATCH_LIMIT):
    items = await fetch_next_batch(limit)
    if not items:
        logger.info("Queue empty — sleeping...")
        return 0
    logger.info(f"Fetched {len(items)} queued item(s).")
    for it in items:
        await with_retries(process_item, it, retries=3, delay=5, backoff=2, logger=logger)
    return len(items)

async def run_loop():
    logger.info("Batcher started. Initializing MongoDB connection...")
    try:
        await ensure_initialized()
        logger.info("MongoDB connection initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize MongoDB: {e}")
        return
    
    logger.info("Watching queue for pending anchors...")
    while True:
        try:
            processed = await process_once()
            if processed == 0:
                await sleep(POLL_INTERVAL)
        except Exception as e:
            logger.error(f"Batcher loop error: {e}")
            await sleep(POLL_INTERVAL)

if __name__ == "__main__":
    asyncio.run(run_loop())
