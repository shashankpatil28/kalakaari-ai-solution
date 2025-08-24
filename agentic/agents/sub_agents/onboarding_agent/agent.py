import os
from google.adk.agents import Agent
from .prompt import ONBOARDING_PROMPT
from typing import List, Optional, Dict
from uuid import UUID
from pydantic import BaseModel, Field, EmailStr

# Import this to handle JSON serialization within the tool
import json

# --- Pydantic Models for Schema Validation ---

class ContactInfo(BaseModel):
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None

class Artisan(BaseModel):
    id: UUID = Field(..., description="Unique UUID for the artisan")
    name: str
    contact_info: ContactInfo
    skills: List[str]
    products: List[UUID]
    agents: List[UUID]

class AgentData(BaseModel):
    id: UUID
    name: str
    organization: str
    specialization: List[str]
    contact_info: ContactInfo
    artisans: List[UUID]

class IPStatus(BaseModel):
    is_ip_registered: bool = False
    ip_type: Optional[str] = None
    registration_number: Optional[str] = None
    registration_date: Optional[str] = None # Using string for easier handling with LLM
    expiry_date: Optional[str] = None # Using string for easier handling with LLM

class PowerOfAttorney(BaseModel):
    granted: bool
    trademark_office: bool

class RightOwners(BaseModel):
    has_rights: bool
    names: List[str]

class PreviousIPRights(BaseModel):
    is_derivative: bool
    right_owners: RightOwners

class Authorization(BaseModel):
    id: UUID
    artisan_id: UUID
    agent_id: UUID
    consent_from_artisan: bool
    no_objection_certificate: bool
    power_of_attorney: PowerOfAttorney
    previous_ip_rights: PreviousIPRights
    date_granted: Optional[str] = None # Using string for easier handling with LLM
    valid_till: Optional[str] = None # Using string for easier handling with LLM

class Rules(BaseModel):
    id: UUID
    product_id: UUID
    allow_reproduction: bool
    allow_resale: bool
    allow_derivative: bool
    allow_commercial_use: bool
    allow_ai_training: bool
    license_duration: str # Using text for 'interval'
    geographical_limit: str
    royalty_percentage: float

class Product(BaseModel):
    id: UUID
    artisan_id: UUID
    name: str
    description: str
    category: str
    media: List[str]
    ip_status: IPStatus
    authorization_id: UUID
    rules: List[UUID]

# Main, top-level schema
class CompleteArtisanData(BaseModel):
    artisan: List[Artisan]
    agent: List[AgentData]
    product: List[Product]
    authorization: List[Authorization]
    rules: List[Rules]

# --- Tool Definition ---

# def finalize_and_pass_data(onboarding_data: Dict) -> str:
#     """
#     Finalizes the onboarding process by validating the collected data against the
#     complete schema and returns a JSON string for the next agent.
    
#     Args:
#         onboarding_data: A dictionary containing all the collected artisan information.
    
#     Returns:
#         A JSON string of the validated data or an error message.
#     """
#     try:
#         # Pydantic validates the entire dictionary against the defined schema.
#         # This will raise a ValidationError if any required fields are missing
#         # or data types are incorrect.
#         # validated_data = CompleteArtisanData.model_validate(onboarding_data)
        
#         # If validation is successful, return the data as a clean JSON string.
#         return onboarding_data.model_dump_json(indent=2)
#     except Exception as e:
#         # Return a clear error message if validation fails.
#         return f"Error: Data validation failed. Details: {e}"

# --- Agent Definition ---

onboarding_agent = Agent(
    name="onboarding_agent",
    model=os.getenv("MODEL_NAME"),
    description="Collects artisan details and completes onboarding.",
    instruction=ONBOARDING_PROMPT,
    # tools=[finalize_and_pass_data]
)