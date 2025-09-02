# app/main.py
from fastapi import FastAPI
from pydantic import BaseModel, EmailStr
from typing import Optional
import uvicorn
from datetime import datetime

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
# 2. FastAPI Application
# ==============================================================================

app = FastAPI(title="Master-IP Prototype Service", version="0.1.0")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/")
def root():
    return {"message": "Prototype Master-IP backend is running!"}

# ==============================================================================
# 3. POST Endpoint (/create)
# ==============================================================================

@app.post("/create")
async def create_ip_record(onboarding_data: OnboardingData):
    """
    Receives simplified onboarding JSON (artisan + art details),
    prints it for verification, and returns a dummy structured response.
    """
    # Log received data (for developer visibility)
    print("\n=========================================================")
    print("✅ Received onboarding data from IP agent:")
    print(onboarding_data.model_dump_json(indent=2))
    print("=========================================================\n")

    # Dummy structured response
    response_data = {
        "status": "success",
        "message": "Your CraftID submission has been received and queued for IP verification.",
        "transaction_id": "tx_" + datetime.utcnow().strftime("%Y%m%d%H%M%S"),
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "verification": {
            "estimated_completion": "24-48 hours",
            "next_steps": [
                "An IP specialist will review your submission.",
                "You will receive a confirmation email after verification is complete."
            ]
        },
        "links": {
            "track_status": "http://localhost:8001/status/"
        }
    }
    return response_data

# ==============================================================================
# 4. Entry Point
# ==============================================================================

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
