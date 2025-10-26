# app/schemas/craft.py
from pydantic import BaseModel, EmailStr
from typing import Optional

class Artisan(BaseModel):
    name: str
    location: str
    contact_number: str
    email: EmailStr
    aadhaar_number: str

class Art(BaseModel):
    name: str
    description: str
    photo: str  # base64

class OnboardingData(BaseModel):
    artisan: Artisan
    art: Art

class VerificationResponse(BaseModel):
    public_id: str
    status: str  # "pending", "anchored", "tampered"
    public_hash: str
    stored_hash: str
    computed_hash: str
    is_tampered: bool
    tx_hash: Optional[str] = None
    anchored_at: Optional[str] = None
    blockchain_timestamp: Optional[int] = None
    verification_details: dict
