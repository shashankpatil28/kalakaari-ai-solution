import asyncio
import os
import signal # For shutdown
from datetime import datetime, timezone
import time # For timing

from chain.utils import get_logger, utc_now_iso, sleep
from chain.queue import fetch_one_and_lock, mark_done, mark_failed
from chain.web3_client import anchor_hash_on_chain, is_anchored
# --- FIX: Import connect_db and close_db ---
from app.db.mongodb import collection, connect_db, close_db
# --- END FIX ---
from app.constant import ( # Make sure to import from constants (plural)
    BATCH_LIMIT, MAX_RETRIES,
    ACTIVE_POLL_INTERVAL, IDLE_POLL_INTERVAL, IDLE_THRESHOLD_MINUTES
)

logger = get_logger("chain.batcher")

# --- Global flag for graceful shutdown ---
shutdown_requested = False
main_task = None

async def process_item(it: dict):
    """Processes a single locked queue item."""
    public_id = it["public_id"]
    public_hash = it["public_hash"]
    attempt = it.get("tries", 0) # fetch_one_and_lock already incremented
    logger.info(f"[Attempt {attempt}/{MAX_RETRIES}] Processing item {public_id}...")

    try:
        # --- 1. Idempotency Check ---
        already_anchored, anchor_ts = await asyncio.to_thread(is_anchored, public_hash)
        if already_anchored:
            logger.warning(f"Item {public_id} (hash {public_hash[:10]}...) already anchored. Marking done.")
            anchor_time_iso = datetime.fromtimestamp(anchor_ts, timezone.utc).isoformat() if anchor_ts > 0 else utc_now_iso()
            await mark_done(public_id, "N/A (already anchored)", anchor_time_iso)
            await collection("craftids").update_one(
                 {"public_id": public_id, "status": {"$ne": "anchored"}},
                 {"$set": {"status": "anchored", "tx_hash": "N/A (already anchored)", "anchored_at": anchor_time_iso}}
            )
            return

        # --- 2. Anchor Transaction ---
        logger.info(f"Anchoring hash {public_hash[:10]}... for {public_id} on-chain...")
        tx_hash = await asyncio.to_thread(anchor_hash_on_chain, public_hash, public_id, True)
        anchored_at = utc_now_iso()

        # --- 3. Mark as Done ---
        await mark_done(public_id, tx_hash, anchored_at)
        await collection("craftids").update_one(
            {"public_id": public_id},
            {"$set": {"status": "anchored", "tx_hash": tx_hash, "anchored_at": anchored_at}}
        )
        logger.info(f"✅ Anchored {public_id} | tx: {tx_hash[:10]}...")

    # --- 4. Specific Error Handling ---
    except ValueError as ve:
         logger.error(f"❌ Permanent failure for {public_id}: {ve}. Moving to 'failed' state.")
         await mark_failed(public_id, f"Permanent failure: {ve}", is_permanent=True)
         await collection("craftids").update_one(
             {"public_id": public_id},
             {"$set": {"status": "failed", "last_error": f"Permanent failure: {ve}"}}
         )
    except TimeoutError as te:
         logger.error(f"❌ Receipt timeout for {public_id}: {te}. Will retry.")
         await mark_failed(public_id, f"Receipt timeout: {te}")
    except Exception as e:
         logger.error(f"❌ Temporary failure for {public_id}: {e}. Will retry.")
         await mark_failed(public_id, str(e))


async def process_batch(limit=BATCH_LIMIT):
    """Fetches and processes items up to the limit."""
    processed_count = 0
    for _ in range(limit):
        if shutdown_requested:
             logger.info("Shutdown requested, stopping batch processing.")
             break

        item = await fetch_one_and_lock()

        if not item:
            break

        try:
             await process_item(item)
             processed_count += 1
        except Exception as e:
             public_id = item.get("public_id", "UNKNOWN")
             logger.error(f"CRITICAL: Unhandled exception during process_item for {public_id}: {e}")
             try:
                 await mark_failed(public_id, f"Unhandled exception: {e}", is_permanent=True)
             except Exception as mark_e:
                 logger.error(f"Failed to even mark {public_id} as failed: {mark_e}")

    return processed_count

async def run_loop():
    """Main batcher loop with variable polling and graceful shutdown."""
    # --- FIX: Connection handled by main() ---
    # No connection logic needed here anymore
    # --- END FIX ---

    last_processed_time = time.monotonic()
    current_poll_interval = ACTIVE_POLL_INTERVAL
    is_idle = False
    logger.info(f"Watching queue. Active poll: {ACTIVE_POLL_INTERVAL}s, Idle poll: {IDLE_POLL_INTERVAL}s after {IDLE_THRESHOLD_MINUTES}min inactivity.")

    while not shutdown_requested:
        try:
            processed = await process_batch()

            if processed > 0:
                last_processed_time = time.monotonic()
                if is_idle:
                    logger.info("Processed items, switching to active polling.")
                    is_idle = False
                current_poll_interval = ACTIVE_POLL_INTERVAL
                await sleep(1)

            else:
                time_since_last = time.monotonic() - last_processed_time
                if not is_idle and time_since_last > (IDLE_THRESHOLD_MINUTES * 60):
                    logger.info(f"No items processed for {IDLE_THRESHOLD_MINUTES} mins. Entering idle polling mode.")
                    current_poll_interval = IDLE_POLL_INTERVAL
                    is_idle = True

                logger.info(f"Queue empty. Sleeping for {current_poll_interval}s.")
                await sleep(current_poll_interval)

        except asyncio.CancelledError:
            logger.info("Main loop cancelled.")
            break
        except Exception as e:
            logger.error(f"Batcher loop error: {e}. Retrying after {ACTIVE_POLL_INTERVAL}s.")
            if not shutdown_requested:
                await sleep(ACTIVE_POLL_INTERVAL)

    logger.info("Batcher loop finished.")

def shutdown_handler(signum, frame):
    """Signal handler for SIGTERM/SIGINT."""
    global shutdown_requested, main_task
    if not shutdown_requested:
        logger.info(f"Received signal {signum}. Initiating graceful shutdown...")
        shutdown_requested = True
        if main_task:
            main_task.cancel()
    else:
        logger.warning("Shutdown already requested.")

async def main():
    """Sets up signal handlers, DB connection, and runs the main loop."""
    global main_task
    logger.info("Batcher starting...")

    # --- FIX: Connect to DB on startup ---
    try:
        await connect_db()
        logger.info("MongoDB connection initialized successfully.")
    except Exception as e:
        logger.error(f"CRITICAL: Failed to initialize MongoDB: {e}. Exiting.")
        return # Cannot run without DB
    # --- END FIX ---

    loop = asyncio.get_running_loop()
    loop.add_signal_handler(signal.SIGTERM, shutdown_handler, signal.SIGTERM, None)
    loop.add_signal_handler(signal.SIGINT, shutdown_handler, signal.SIGINT, None)

    main_task = asyncio.create_task(run_loop())
    try:
        await main_task
    except asyncio.CancelledError:
        logger.info("Main task successfully cancelled.")
    finally:
         # --- FIX: Close DB connection on shutdown ---
         logger.info("Closing MongoDB connection...")
         await close_db()
         # --- END FIX ---
         logger.info("Batcher shut down gracefully.")


if __name__ == "__main__":
    asyncio.run(main())