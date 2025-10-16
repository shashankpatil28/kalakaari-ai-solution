# app/routes/products.py
from fastapi import APIRouter, HTTPException
from typing import List
import os
import hashlib
import jwt
from datetime import datetime, timedelta
import asyncio

from app.models import OnboardingData
from app.mongodb import ensure_initialized, collection, next_sequence, close as mongo_close

router = APIRouter()
SECRET_KEY = os.getenv("SECRET_KEY", "change_in_prod")
ALGORITHM = "HS256"


async def ensure_db_ready_or_502():
    try:
        await ensure_initialized()
    except Exception as e:
        try:
            mongo_close()
            await ensure_initialized()
        except Exception as e2:
            raise HTTPException(status_code=502, detail=f"DB init error: {e}; retry failed: {e2}")


@router.post("/add-product")
async def add_product(data: OnboardingData):
    # ensure DB ready
    await ensure_db_ready_or_502()

    craftids = collection("craftids")
    art_name_norm = data.art.name.strip().lower()

    try:
        existing = await asyncio.wait_for(craftids.find_one({"art_name_norm": art_name_norm}), timeout=4)
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="DB read timed out")
    except Exception as e:
        # recovery attempt
        try:
            mongo_close()
            await ensure_db_ready_or_502()
            craftids = collection("craftids")
            existing = await asyncio.wait_for(craftids.find_one({"art_name_norm": art_name_norm}), timeout=4)
        except Exception as e2:
            raise HTTPException(status_code=500, detail=f"DB read error: {e}; recovery: {e2}")

    if existing:
        public_id = existing.get("public_id")
        public_hash = existing.get("public_hash")
        verification_url = f"/verify/{public_id}"
        return {
            "artisan_info": {
                "name": existing["original_onboarding_data"]["artisan"]["name"],
                "location": existing["original_onboarding_data"]["artisan"]["location"]
            },
            "art_info": {
                "name": existing["original_onboarding_data"]["art"]["name"],
                "description": existing["original_onboarding_data"]["art"]["description"],
                "photo": existing["original_onboarding_data"]["art"].get("photo", "")
            },
            "verification": {
                "public_id": public_id,
                "public_hash": public_hash,
                "verification_url": verification_url
            },
            "timestamp": existing.get("timestamp")
        }

    # allocate seq
    try:
        seq = await asyncio.wait_for(next_sequence("craftid_seq"), timeout=4)
    except Exception as e:
        # recovery attempt
        try:
            mongo_close()
            await ensure_db_ready_or_502()
            seq = await asyncio.wait_for(next_sequence("craftid_seq"), timeout=4)
        except Exception as e2:
            raise HTTPException(status_code=502, detail=f"Failed to allocate public id: {e}; recovery: {e2}")

    public_id = f"CID-{seq:05d}"
    payload = {"public_id": public_id, "exp": datetime.utcnow() + timedelta(days=365)}
    private_key = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    public_hash = hashlib.sha256((data.art.name + data.art.description + data.art.photo).encode()).hexdigest()

    doc = {
        "public_id": public_id,
        "private_key": private_key,
        "public_hash": public_hash,
        "art_name_norm": art_name_norm,
        "original_onboarding_data": data.dict(),
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

    try:
        await craftids.insert_one(doc)
    except Exception as e:
        # recovery retry
        try:
            mongo_close()
            await ensure_db_ready_or_502()
            craftids = collection("craftids")
            await craftids.insert_one(doc)
        except Exception as e2:
            raise HTTPException(status_code=500, detail=f"DB insert error: {e}; recovery: {e2}")

    verification_url = f"/verify/{public_id}"
    return {
        "artisan_info": {"name": data.artisan.name, "location": data.artisan.location},
        "art_info": {"name": data.art.name, "description": data.art.description, "photo": data.art.photo},
        "verification": {"public_id": public_id, "public_hash": public_hash, "verification_url": verification_url},
        "timestamp": doc["timestamp"]
    }


@router.get("/get-products")
async def get_products():
    await ensure_db_ready_or_502()

    craftids = collection("craftids")
    try:
        cursor = craftids.find().sort("timestamp", -1)
        docs = await cursor.to_list(length=200)
    except Exception as e:
        # recovery attempt
        try:
            mongo_close()
            await ensure_db_ready_or_502()
            craftids = collection("craftids")
            cursor = craftids.find().sort("timestamp", -1)
            docs = await cursor.to_list(length=200)
        except Exception as e2:
            raise HTTPException(status_code=500, detail=f"DB read error: {e}; recovery: {e2}")

    out = []
    for d in docs:
        orig = d.get("original_onboarding_data", {})
        artisan = orig.get("artisan", {})
        art = orig.get("art", {})
        public_id = d.get("public_id")
        public_hash = d.get("public_hash")
        verification_url = f"/verify/{public_id}" if public_id else ""

        out.append({
            "artisan_info": {"name": artisan.get("name", ""), "location": artisan.get("location", "")},
            "art_info": {"name": art.get("name", ""), "description": art.get("description", ""), "photo": art.get("photo", "")},
            "verification": {"public_id": public_id or "", "public_hash": public_hash or "", "verification_url": verification_url},
            "timestamp": d.get("timestamp", "")
        })

    return out
