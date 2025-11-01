# app/routes/products.py
from fastapi import APIRouter, HTTPException
from typing import List
import os
import hashlib
import jwt
from datetime import datetime, timedelta
import asyncio

from app.models import ProductPayload # <-- IMPORT NEW MODEL
# We only need 'collection' now
from app.mongodb import collection

router = APIRouter()
SECRET_KEY = os.getenv("SECRET_KEY", "change_in_prod")
ALGORITHM = "HS256"

@router.post("/add-product")
async def add_product(data: ProductPayload): # <-- USE NEW MODEL
    
    craftids = collection("craftids")
    art_name_norm = data.art.name.strip().lower()

    try:
        # Check for existing product using the provided public_id
        # REMOVED asyncio.wait_for. Motor has its own timeout (serverSelectionTimeoutMS).
        existing = await craftids.find_one({"public_id": data.public_id})
    except Exception as e:
        # Catch potential ServerSelectionTimeoutError or other DB errors
        raise HTTPException(status_code=504, detail=f"DB read error on find: {e}")

    if existing:
        public_id = existing.get("public_id")
        verification_url = f"/verify/{public_id}"
        
        # Get data from the stored document
        orig_data = existing.get("original_onboarding_data", {})
        artisan_info = orig_data.get("artisan", {})
        art_info = orig_data.get("art", {})
        
        # Handle both old 'photo' and new 'photo_url' fields
        photo = art_info.get("photo_url") or art_info.get("photo", "")

        return {
            "artisan_info": {
                "name": artisan_info.get("name"),
                "location": artisan_info.get("location")
            },
            "art_info": {
                "name": art_info.get("name"),
                "description": art_info.get("description"),
                "photo": photo # Return the correct photo field
            },
            "verification": {
                "public_id": public_id,
                # "public_hash": REMOVED
                "verification_url": verification_url
            },
            "timestamp": existing.get("timestamp")
        }

    # Use the public_id from the payload
    public_id = data.public_id

    doc = {
        "public_id": public_id,
        "art_name_norm": art_name_norm,
        "original_onboarding_data": data.dict(by_alias=True), # Use by_alias to respect 'photo_url'
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

    try:
        # REMOVED asyncio.wait_for
        await craftids.insert_one(doc)
    except Exception as e:
        # Catch potential ServerSelectionTimeoutError or other DB errors
        raise HTTPException(status_code=500, detail=f"DB insert error: {e}")

    verification_url = f"/verify/{public_id}"
    return {
        "artisan_info": {"name": data.artisan.name, "location": data.artisan.location},
        "art_info": {"name": data.art.name, "description": data.art.description, "photo": data.art.photo_url}, # <-- Use photo_url
        "verification": {
            "public_id": public_id,
            # "public_hash": REMOVED
            "verification_url": verification_url
        },
        "timestamp": doc["timestamp"]
    }


@router.get("/get-products")
async def get_products():
    craftids = collection("craftids")
    try:
        # REMOVED asyncio.wait_for
        cursor = craftids.find().sort("timestamp", -1)
        docs = await cursor.to_list(length=200)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DB read error on get: {e}")

    out = []
    for d in docs:
        orig = d.get("original_onboarding_data", {})
        artisan = orig.get("artisan", {})
        art = orig.get("art", {})
        public_id = d.get("public_id")
        verification_url = f"/verify/{public_id}" if public_id else ""
        photo = art.get("photo_url") or art.get("photo", "")

        out.append({
            "artisan_info": {"name": artisan.get("name", ""), "location": artisan.get("location", "")},
            "art_info": {"name": art.get("name", ""), "description": art.get("description", ""), "photo": photo}, # <-- Use compatible photo
            "verification": {
                "public_id": public_id or "", 
                "verification_url": verification_url
            },
            "timestamp": d.get("timestamp", "")
        })

    return out