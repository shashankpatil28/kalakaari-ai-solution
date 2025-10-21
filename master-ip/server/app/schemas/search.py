# app/schemas/search.py
from pydantic import BaseModel
from typing import Optional
from app.constants import TOP_K_DEFAULT

# --- Pydantic schemas for metadata search ---
# These are separate from craft.py as they allow optional fields for querying

class QueryArtisan(BaseModel):
    name: Optional[str] = ""
    location: Optional[str] = ""
    contact_number: Optional[str] = ""
    email: Optional[str] = ""
    aadhaar_number: Optional[str] = ""

class QueryArt(BaseModel):
    name: Optional[str] = ""
    description: Optional[str] = ""
    photo_url: Optional[str] = ""   # ignored for embeddings

class QuerySchema(BaseModel):
    artisan: QueryArtisan
    art: QueryArt
    top_k: Optional[int] = TOP_K_DEFAULT