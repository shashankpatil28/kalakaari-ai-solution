import os
import uuid
from google.adk.agents import Agent
from .prompt import ONBOARDING_PROMPT
from typing import List, Optional
from pydantic import BaseModel, Field, EmailStr

from ..ip_agent.agent import ip_agent  # Import the IP agent

# ------------------- Pydantic Models -------------------

class ContactInfo(BaseModel):
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None

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
    license_duration: str
    geographical_limit: str
    royalty_percentage: float

class Product(BaseModel):
    id: str
    artisan_id: str
    name: str
    description: str
    category: str
    media: List[str]   # Base64 image string
    ip_status: IPStatus
    authorization_id: str
    rules: List[str]

class CompleteArtisanData(BaseModel):
    artisan: List[Artisan]
    agent: List[AgentData]
    product: List[Product]
    authorization: List[Authorization]
    rules: List[Rules]

# ------------------- Data Structuring Tool -------------------

def structure_onboarding_data(
    full_name: str, contact_info: str, address: str, artisan_type: str, nationality: str,
    artwork_name: str, description: str, category: str, materials_techniques: str, creation_date: str,
    cultural_significance: str, artwork_media: str,
    original_creator: bool, consent_ip_registration: bool, is_derivative: bool, disputes_joint_ownership: bool,
    allow_reproduction: bool, allow_resale: bool, allow_derivative: bool, allow_commercial_use: bool, allow_ai_training: bool,
    geographical_limit: str, royalty_percentage: float
) -> str:
    """Takes all collected info and structures it into the required JSON schema."""
    try:
        # Generate UUIDs
        artisan_id = str(uuid.uuid4())
        agent_id = str(uuid.uuid4())
        product_id = str(uuid.uuid4())
        auth_id = str(uuid.uuid4())
        rule_id = str(uuid.uuid4())

        complete_data = CompleteArtisanData(
            artisan=[Artisan(
                id=artisan_id,
                name=full_name,
                contact_info=ContactInfo(phone=contact_info, address=address),
                skills=[artisan_type],
                products=[product_id],
                agents=[agent_id]
            )],
            agent=[AgentData(
                id=agent_id,
                name="Kalakaari AI Agent",
                organization="Kalakaari AI",
                specialization=["IP Registration"],
                contact_info=ContactInfo(email="support@kalakaari.ai"),
                artisans=[artisan_id]
            )],
            product=[Product(
                id=product_id,
                artisan_id=artisan_id,
                name=artwork_name,
                description=description,
                category=category,
                media=[artwork_media],  # Base64 string
                ip_status=IPStatus(is_ip_registered=False, ip_type="Copyright"),
                authorization_id=auth_id,
                rules=[rule_id]
            )],
            authorization=[Authorization(
                id=auth_id,
                artisan_id=artisan_id,
                agent_id=agent_id,
                consent_from_artisan=consent_ip_registration,
                no_objection_certificate=not disputes_joint_ownership,
                power_of_attorney=PowerOfAttorney(granted=True, trademark_office=False),
                previous_ip_rights=PreviousIPRights(
                    is_derivative=is_derivative,
                    right_owners=RightOwners(has_rights=False, names=[])
                )
            )],
            rules=[Rules(
                id=rule_id,
                product_id=product_id,
                allow_reproduction=allow_reproduction,
                allow_resale=allow_resale,
                allow_derivative=allow_derivative,
                allow_commercial_use=allow_commercial_use,
                allow_ai_training=allow_ai_training,
                license_duration="Perpetual",
                geographical_limit=geographical_limit,
                royalty_percentage=royalty_percentage
            )]
        )

        return complete_data.model_dump_json(indent=2)

    except Exception as e:
        return f"Error: Failed to structure data. Details: {e}"

# ------------------- Agent Definition -------------------

onboarding_agent = Agent(
    name="onboarding_agent",
    model=os.getenv("MODEL_NAME"),
    description="Collects artisan details, structures them, then calls ip_agent.",
    instruction=ONBOARDING_PROMPT,
    tools=[structure_onboarding_data],
    sub_agents=[ip_agent]
)
