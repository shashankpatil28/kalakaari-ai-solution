# app/main.py
from fastapi import FastAPI, HTTPException
import uvicorn
from pydantic import BaseModel, Field, EmailStr
from typing import List, Dict, Optional
import json

from .models.model import Base

from .db.db import engine
from .db.db import db_ping

# Create all tables
# Base.metadata.create_all(bind=engine)

app = FastAPI(title="Master-IP Service", version="0.1.0")

# @app.on_event("startup")
# def _startup():
#     # Verify DB connection when the server starts
#     db_ping()

# Inner models for nested objects
class ContactInfo(BaseModel):
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None

class IPStatus(BaseModel):
    is_ip_registered: bool = False
    ip_type: Optional[str] = None
    registration_number: Optional[str] = None
    registration_date: Optional[str] = None
    expiry_date: Optional[str] = None

class PowerOfAttorney(BaseModel):
    granted: bool
    trademark_office: bool

class RightOwners(BaseModel):
    has_rights: bool
    names: List[str]

class PreviousIPRights(BaseModel):
    is_derivative: bool
    right_owners: RightOwners

# Main models for each data entity
class Artisan(BaseModel):
    id: str
    name: str
    contact_info: ContactInfo
    skills: List[str]
    products: List[str]
    agents: List[str]

class AgentData(BaseModel):
    id: str
    name: str
    organization: str
    specialization: List[str]
    contact_info: ContactInfo
    artisans: List[str]

class Product(BaseModel):
    id: str
    artisan_id: str
    name: str
    description: str
    category: str
    media: List[str]
    ip_status: IPStatus
    authorization_id: str
    rules: List[str]

class Authorization(BaseModel):
    id: str
    artisan_id: str
    agent_id: str
    consent_from_artisan: bool
    no_objection_certificate: bool
    power_of_attorney: PowerOfAttorney
    previous_ip_rights: PreviousIPRights
    date_granted: Optional[str] = None
    valid_till: Optional[str] = None

class Rules(BaseModel):
    id: str
    product_id: str
    allow_reproduction: bool
    allow_resale: bool
    allow_derivative: bool
    allow_commercial_use: bool
    allow_ai_training: bool
    license_duration: Optional[str] = None
    geographical_limit: Optional[str] = None
    royalty_percentage: Optional[float] = None

# The complete payload model that the endpoint will receive
class CompleteArtisanData(BaseModel):
    artisan: List[Artisan]
    agent: List[AgentData]
    product: List[Product]
    authorization: List[Authorization]
    rules: List[Rules]

# ==============================================================================
# 2. FastAPI Application
# ==============================================================================
@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/")
def root():
    return {"message": "Backend is working!"}

# Define a POST endpoint at /create
@app.post("/create")
async def create_ip_record(complete_data: CompleteArtisanData):
    """
    Receives the JSON data from the IP agent, prints it for verification,
    and returns a dummy JSON response.
    """
    # --------------------------------------------------------------------------
    # For developer verification: print the received data to the console
    # --------------------------------------------------------------------------
    print("\n=========================================================")
    print("Received JSON data from IP agent:")
    # Use .dict() or .json() to convert the Pydantic model to a dictionary/JSON string
    # We use .model_dump_json(indent=2) for a pretty-printed output
    print(complete_data.model_dump_json(indent=2))
    print("=========================================================\n")

    # --------------------------------------------------------------------------
    # 3. Dummy Response
    #    This is a dummy response simulating a successful backend process.
    #    It contains 10+ lines as requested.
    # --------------------------------------------------------------------------
    response_data = {
        "status": "success",
        "message": "Data submitted successfully. IP verification process has been initiated.",
        "transaction_id": "tx_20250825_123456789",
        "timestamp": "2025-08-25T11:10:00Z",
        "details": {
            "product_id": complete_data.product[0].id,
            "artisan_id": complete_data.artisan[0].id,
            "verification_eta": "48 hours",
            "next_steps": [
                "A dedicated IP specialist will review your submission.",
                "You will receive a notification via email once the initial review is complete."
            ]
        },
        "links": {
            "view_status": "http://localhost:8001/status/tx_20250825_123456789"
        }
    }
    return response_data

# ==============================================================================
# 4. Entry point for running the application
# ==============================================================================
if __name__ == "__main__":
    # To run, execute this script and navigate to http://localhost:8001
    # You can access the FastAPI documentation at http://localhost:8001/docs
    uvicorn.run(app, host="0.0.0.0", port=8001)
