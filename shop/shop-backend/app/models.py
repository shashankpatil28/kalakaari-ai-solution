# app/models.py
from pydantic import BaseModel, EmailStr, Field
from typing import Optional # <-- IMPORT Optional

class Artisan(BaseModel):
    name: str
    location: str
    contact_number: str
    email: EmailStr
    aadhaar_number: str

class Art(BaseModel):
    name: str
    description: str
    photo_url: Optional[str] = Field(None, alias="photo_url") # <-- Make optional, keep alias
    photo: Optional[str] = None # <-- Add optional 'photo' field

class ProductPayload(BaseModel):
    public_id: str
    artisan: Artisan
    art: Art

# REMOVED old OnboardingData model