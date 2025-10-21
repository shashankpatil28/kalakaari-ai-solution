# app/schemas/craft.py
from pydantic import BaseModel, EmailStr

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