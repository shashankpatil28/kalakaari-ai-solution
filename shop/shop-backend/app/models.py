# app/models.py
from pydantic import BaseModel, EmailStr, Field

class Artisan(BaseModel):
    name: str
    location: str
    contact_number: str
    email: EmailStr
    aadhaar_number: str

class Art(BaseModel):
    name: str
    description: str
    photo_url: str = Field(..., alias="photo_url") # Expect 'photo_url' from the payload

class ProductPayload(BaseModel):
    public_id: str
    artisan: Artisan
    art: Art

# REMOVED old OnboardingData model