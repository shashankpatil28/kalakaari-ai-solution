from fastapi import HTTPException
import os
import hashlib
import jwt
import asyncio
from datetime import datetime, timedelta
from uuid import uuid4

# Import Schemas
from app.schemas.craft import OnboardingData, VerificationResponse

# Import DB and Utils
from app.db.mongodb import ensure_initialized, collection, next_sequence, close as mongo_close
from app.utils.db_utils import ensure_db_ready_or_502
from app.utils.http_client import decode_base64_to_pil

# Import Config
from app.constant import SECRET_KEY, ALGORITHM

# Import chain modules
from chain.hashing import compute_public_hash
from chain.signer import sign_attestation
from chain.queue import enqueue_item
from chain.web3_client import is_anchored

# Import embedding and Pinecone utilities
from app.utils.embedders import ClipEmbedder, embed_text
from app.utils.pinecone import _upsert_image_index, _upsert_text_index

# Import logging
import logging
logger = logging.getLogger(__name__)


async def create_craftid(data: OnboardingData):
    # ensure DB is initialized (with recovery)
    await ensure_db_ready_or_502()

    coll = collection("craftids")

    art_name_norm = data.art.name.strip().lower()

    # check uniqueness
    try:
        existing = await asyncio.wait_for(coll.find_one({"art_name_norm": art_name_norm}), timeout=4)
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="DB read timed out")
    except Exception as e:
        # if this error occurs, try a recovery once
        try:
            mongo_close()
            await ensure_db_ready_or_502()
            coll = collection("craftids")
            existing = await asyncio.wait_for(coll.find_one({"art_name_norm": art_name_norm}), timeout=4)
        except Exception as e2:
            raise HTTPException(status_code=500, detail=f"DB read error: {e}; recovery error: {e2}")

    if existing:
        raise HTTPException(
            status_code=409,
            detail="A similar product name already exists. Please provide a more unique name."
        )

    # allocate atomic sequence
    try:
        seq = await asyncio.wait_for(next_sequence("craftid_seq"), timeout=4)
    except Exception as e:
        # try recovery once
        try:
            mongo_close()
            await ensure_db_ready_or_502()
            seq = await asyncio.wait_for(next_sequence("craftid_seq"), timeout=4)
        except Exception as e2:
            raise HTTPException(status_code=502, detail=f"Failed to allocate public id: {e}; recovery: {e2}")

    public_id = f"CID-{seq:05d}"

    # create a JWT private token (kept for backward compatibility)
    payload = {"public_id": public_id, "exp": datetime.utcnow() + timedelta(days=365)}
    private_key = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    # timestamp (ISO with Z)
    timestamp_iso = datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

    # generate a per-item salt (prevents preimage probing for PII)
    salt = os.getenv("DEFAULT_SALT", "") or uuid4().hex

    # compute deterministic public hash (exclude photo_url)
    artisan = data.artisan.dict()
    art = data.art.dict()
    # ensure we do not include photo_url in the hash inputs
    art.pop("photo_url", None)
    # compute using canonical hashing function (returns hex without 0x)
    public_hash = compute_public_hash(artisan, art, timestamp_iso, salt)

    # build attestation payload and sign it
    att_payload = {
        "public_id": public_id,
        "public_hash": public_hash,
        "timestamp": timestamp_iso,
        "salt": salt,
        "expected_anchor_by": None  # optional: you can set an ETA here
    }
    attestation = sign_attestation(att_payload)

    doc = {
        "public_id": public_id,
        "private_key": private_key,
        "public_hash": public_hash,
        "art_name_norm": art_name_norm,
        "original_onboarding_data": data.dict(),
        "timestamp": timestamp_iso,
        "salt": salt,
        "status": "queued",
        "attestation": attestation,
        "created_at": datetime.utcnow().isoformat() + "Z"
    }

    try:
        await coll.insert_one(doc)
    except Exception as e:
        # try recovery once if insert fails
        try:
            mongo_close()
            await ensure_db_ready_or_502()
            coll = collection("craftids")
            await coll.insert_one(doc)
        except Exception as e2:
            raise HTTPException(status_code=500, detail=f"DB insert error: {e}; recovery: {e2}")

    # --- NEW: Upsert image to Pinecone with the same public_id ---
    try:
        logger.info(f"[create_craftid] Upserting image to Pinecone for {public_id}")
        
        # Handle both URL and Base64 image formats
        photo_data = data.art.photo
        if photo_data.startswith('http://') or photo_data.startswith('https://'):
            # It's a URL, fetch the image
            from app.utils.http_client import _fetch_image_from_url
            pil_image = await _fetch_image_from_url(photo_data)
        else:
            # It's Base64, decode it
            pil_image = decode_base64_to_pil(photo_data)
        
        # Embed the image using ClipEmbedder (lazy-loaded singleton)
        embedder = ClipEmbedder()
        image_vector = await asyncio.to_thread(embedder.embed_pil, pil_image)
        
        # Prepare Pinecone metadata (minimal info for search results)
        pinecone_metadata = {
            "source": "craftid_creation",
            "brief": f"{data.artisan.name} - {data.art.name}",
            "artisan_name": data.artisan.name,
            "art_name": data.art.name,
            "public_id": public_id
        }
        
        # Upsert to Pinecone with the same public_id as MongoDB
        await _upsert_image_index(public_id, image_vector, pinecone_metadata)
        logger.info(f"[create_craftid] Successfully upserted image to Pinecone for {public_id}")
        
    except Exception as e:
        # Log warning but don't fail the entire request (MongoDB record is already created)
        logger.warning(f"[create_craftid] Failed to upsert image to Pinecone for {public_id}: {e}")
        # Could optionally add a flag to the response indicating partial success
    
    # --- NEW: Upsert metadata to Pinecone TEXT index with the same public_id ---
    try:
        logger.info(f"[create_craftid] Upserting metadata to Pinecone TEXT index for {public_id}")
        
        # Build metadata text string (same logic as metadata_search uses)
        meta_text_parts = [
            (data.artisan.name or "").strip(),
            (data.artisan.location or "").strip(),
            (data.art.name or "").strip(),
            (data.art.description or "").strip()
        ]
        meta_text = " ".join([p for p in meta_text_parts if p])
        
        # Embed the metadata text
        text_vector = embed_text(meta_text)  # Returns numpy array
        
        # Prepare Pinecone metadata for TEXT index (store searchable fields)
        # Note: Pinecone metadata must be flat - no nested dicts
        text_pinecone_metadata = {
            "public_id": public_id,
            "artisan_name": data.artisan.name,
            "artisan_location": data.artisan.location or "",
            "artisan_aadhaar": data.artisan.aadhaar_number or "",
            "art_name": data.art.name,
            "art_description": data.art.description or "",
            "brief": f"{data.artisan.name} - {data.art.name}"
        }
        
        # Upsert to Pinecone TEXT index with the same public_id as MongoDB
        await _upsert_text_index(public_id, text_vector.tolist(), text_pinecone_metadata)
        logger.info(f"[create_craftid] Successfully upserted metadata to Pinecone TEXT index for {public_id}")
        
    except Exception as e:
        # Log warning but don't fail the entire request (MongoDB record is already created)
        logger.warning(f"[create_craftid] Failed to upsert metadata to Pinecone TEXT index for {public_id}: {e}")
        # Could optionally add a flag to the response indicating partial success
    
    # enqueue for background anchoring (queue is a separate collection/process)
    try:
        await enqueue_item({"public_id": public_id, "public_hash": public_hash, "timestamp": timestamp_iso})
    except Exception as e:
        # if enqueue fails, keep record but inform caller
        raise HTTPException(status_code=500, detail=f"Failed to enqueue for anchoring: {e}")

    transaction_id = "tx_" + datetime.utcnow().strftime("%Y%m%d%H%M%S")

    response_data = {
        "status": "success",
        "message": f"Your CraftID for '{data.art.name}' has been created and queued for anchoring.",
        "transaction_id": transaction_id,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "verification": {
            "public_id": public_id,
            "private_key": private_key,
            "public_hash": public_hash,
            "attestation": attestation,
            "verification_url": f"/verify/{public_id}",
            "qr_code_link": f"/verify/qr/{public_id}"
        },
        "artisan_info": {
            "name": data.artisan.name,
            "location": data.artisan.location
        },
        "art_info": {
            "name": data.art.name,
            "description": data.art.description
        },
        "original_onboarding_data": data.dict(),
        "links": {
            "track_status": f"/status/{transaction_id}",
            "shop_listing": f"/shop/{public_id}"
        }
    }
    return response_data


async def verify_craftid(public_id: str):
    """
    Verify the integrity and anchoring status of a CraftID.
    """
    await ensure_db_ready_or_502()
    
    coll = collection("craftids")
    
    # Fetch the craftid record
    try:
        doc = await asyncio.wait_for(coll.find_one({"public_id": public_id}), timeout=4)
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="DB read timed out")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DB read error: {e}")
    
    if not doc:
        raise HTTPException(status_code=404, detail=f"CraftID {public_id} not found")
    
    # Extract stored data
    stored_hash = doc.get("public_hash")
    timestamp = doc.get("timestamp")
    salt = doc.get("salt")
    status = doc.get("status", "pending")
    tx_hash = doc.get("tx_hash")
    anchored_at = doc.get("anchored_at")
    original_data = doc.get("original_onboarding_data", {})
    
    # Recompute hash from current stored metadata
    artisan = original_data.get("artisan", {})
    art = original_data.get("art", {})
    
    # Exclude photo_url if present (same as creation)
    art_copy = dict(art)
    art_copy.pop("photo_url", None)
    
    # Recompute the hash
    computed_hash = compute_public_hash(artisan, art_copy, timestamp, salt)
    
    # Check if metadata has been tampered with
    metadata_tampered = (stored_hash != computed_hash)
    
    # Check blockchain status
    blockchain_anchored = False
    blockchain_timestamp = None
    blockchain_hash_match = False
    
    if status == "anchored" and tx_hash:
        # Query blockchain to verify
        try:
            anchored, ts = await asyncio.to_thread(is_anchored, stored_hash)
            blockchain_anchored = anchored
            blockchain_timestamp = ts
            blockchain_hash_match = anchored
        except Exception as e:
            blockchain_anchored = False
            blockchain_timestamp = None
    
    # Determine final status and tamper detection
    if metadata_tampered:
        final_status = "tampered"
        is_tampered = True
        verification_details = {
            "metadata_tampered": True,
            "reason": "Stored hash does not match recomputed hash from current metadata",
            "blockchain_verified": blockchain_anchored
        }
    elif status == "anchored" and blockchain_anchored:
        final_status = "anchored"
        is_tampered = False
        verification_details = {
            "metadata_tampered": False,
            "blockchain_verified": True,
            "blockchain_timestamp": blockchain_timestamp
        }
    elif status == "queued" or status == "pending":
        final_status = "pending"
        is_tampered = False
        verification_details = {
            "metadata_tampered": False,
            "blockchain_verified": False,
            "reason": "Anchoring is pending (not yet on blockchain)"
        }
    else:
        # Status is anchored but blockchain verification failed
        final_status = "pending"
        is_tampered = False
        verification_details = {
            "metadata_tampered": False,
            "blockchain_verified": False,
            "reason": "Blockchain verification failed or pending confirmation"
        }
    
    return VerificationResponse(
        public_id=public_id,
        status=final_status,
        public_hash=stored_hash,
        stored_hash=stored_hash,
        computed_hash=computed_hash,
        is_tampered=is_tampered,
        tx_hash=tx_hash,
        anchored_at=anchored_at,
        blockchain_timestamp=blockchain_timestamp,
        verification_details=verification_details
    )