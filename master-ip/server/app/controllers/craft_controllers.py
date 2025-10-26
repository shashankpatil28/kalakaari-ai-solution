from fastapi import HTTPException
import hashlib
# import jwt
from datetime import datetime, timedelta
import asyncio

# Import schemas
from app.schemas.craft import OnboardingData

# Import DB helpers
from app.db.mongodb import collection, next_sequence
from app.utils.db_utils import ensure_db_ready_or_502

# Import config
from app.constant import SECRET_KEY, ALGORITHM

async def create_craftid(data: OnboardingData):
    """
    Controller logic for creating a new CraftID.
    """
    # ensure DB is initialized (with recovery).
    # This single call handles connection logic.
    await ensure_db_ready_or_502()

    coll = collection("craftids")

    art_name_norm = data.art.name.strip().lower()

    # check uniqueness
    try:
        existing = await asyncio.wait_for(
            coll.find_one({"art_name_norm": art_name_norm}), 
            timeout=4
        )
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="DB read timed out")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DB read error: {e}")

    if existing:
        raise HTTPException(
            status_code=409,
            detail="A similar product name already exists. Please provide a more unique name."
        )

    # allocate atomic sequence
    try:
        seq = await asyncio.wait_for(next_sequence("craftid_seq"), timeout=4)
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Failed to allocate public id (timeout)")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to allocate public id: {e}")

    public_id = f"CID-{seq:05d}"

    payload = {"public_id": public_id, "exp": datetime.utcnow() + timedelta(days=365)}
    private_key = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    public_hash = hashlib.sha256(
        (data.art.name + data.art.description + data.art.photo).encode()
    ).hexdigest()

    doc = {
        "public_id": public_id,
        "private_key": private_key,
        "public_hash": public_hash,
        "art_name_norm": art_name_norm,
        "original_onboarding_data": data.dict(),
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

    try:
        await asyncio.wait_for(coll.insert_one(doc), timeout=4)
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="DB insert timed out")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DB insert error: {e}")

    transaction_id = "tx_" + datetime.utcnow().strftime("%Y%m%d%H%M%S")

    response_data = {
        "status": "success",
        "message": f"Your CraftID for '{data.art.name}' has been created successfully.",
        "transaction_id": transaction_id,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "verification": {
            "public_id": public_id,
            "private_key": private_key,
            "public_hash": public_hash,
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