# app/main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr
import uvicorn
from datetime import datetime, timedelta
import hashlib
import jwt
import json
import os

# ==============================================================================
# 1. Pydantic Models for Prototype Schema
# ==============================================================================
class Artisan(BaseModel):
    name: str
    location: str
    contact_number: str
    email: EmailStr
    aadhaar_number: str

class Art(BaseModel):
    name: str
    description: str
    photo: str  # Base64 encoded image string

class OnboardingData(BaseModel):
    artisan: Artisan
    art: Art

# ==============================================================================
# 2. DB 
# ==============================================================================
DATABASE_FILE = "craftid_db.json"
SECRET_KEY = "shashankpatil2811"  # Use env variable in production
ALGORITHM = "HS256"

def get_db():
    if not os.path.exists(DATABASE_FILE):
        with open(DATABASE_FILE, "w") as f:
            json.dump([], f)
    with open(DATABASE_FILE, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

def save_db(data):
    with open(DATABASE_FILE, "w") as f:
        json.dump(data, f, indent=4)

# ==============================================================================
# 3. FastAPI Application
# ==============================================================================
app = FastAPI(title="Master-IP Prototype Service", version="0.1.0")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/")
def root():
    return {"message": "Prototype Master-IP backend is running!"}

# ==============================================================================
# 4. POST Endpoint (/create)
# ==============================================================================
@app.post("/create")
def create_craftid(data: OnboardingData):
    db = get_db()

    # Step 1: Check for uniqueness
    for entry in db:
        try:
            existing_art_name = entry["original_onboarding_data"]["art"]["name"]
            if existing_art_name.lower() == data.art.name.lower():
                raise HTTPException(
                    status_code=409,
                    detail="A similar product name already exists. Please provide a more unique name."
                )
        except KeyError:
            # If old entries don’t follow the new structure, skip them
            continue

    # Step 2: Generate IDs and Hashes
    public_id = f"CID-{len(db) + 1:05d}"

    # Create a JWT token as the private key
    payload = {"public_id": public_id, "exp": datetime.utcnow() + timedelta(days=365)}
    private_key = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    # Generate a public hash
    public_hash = hashlib.sha256(
        (data.art.name + data.art.description + data.art.photo).encode()
    ).hexdigest()

    # Step 3: Prepare and Store the new CraftID
    new_craftid = {
        "public_id": public_id,
        "private_key": private_key,
        "public_hash": public_hash,
        "original_onboarding_data": data.dict(),
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    db.append(new_craftid)
    save_db(db)

    # Step 4: Construct the response
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
            "verification_url": f"http://localhost:8001/verify/{public_id}",
            "qr_code_link": f"http://localhost:8001/verify/qr/{public_id}"
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
            "track_status": f"http://localhost:8001/status/{transaction_id}",
            "shop_listing": f"http://localhost:8001/shop/{public_id}"
        }
    }
    return response_data

# ==============================================================================
# 5. Entry Point
# ==============================================================================
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
