from sqlalchemy import Column, String, Boolean, Date, ForeignKey, Table, Numeric, Interval, Text
from sqlalchemy.dialects.postgresql import UUID, ARRAY, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
import uuid

# Declare base
Base = declarative_base()

# --- Association Table for Many-to-Many Artisan <-> Agent ---
artisan_agent_association = Table(
    "artisan_agent_association",
    Base.metadata,
    Column("artisan_id", UUID(as_uuid=True), ForeignKey("artisan.id")),
    Column("agent_id", UUID(as_uuid=True), ForeignKey("agent.id"))
)

# -------------------
# Artisan
# -------------------
class Artisan(Base):
    __tablename__ = "artisan"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)

    contact_info = Column(JSONB)   # stores {email, phone, address}
    skills = Column(ARRAY(String))

    # Relationships
    products = relationship("Product", back_populates="artisan")
    agents = relationship("Agent", secondary=artisan_agent_association, back_populates="artisans")


# -------------------
# Agent
# -------------------
class Agent(Base):
    __tablename__ = "agent"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    organization = Column(String)

    specialization = Column(ARRAY(String))
    contact_info = Column(JSONB)   # stores {email, phone}

    # Relationships
    artisans = relationship("Artisan", secondary=artisan_agent_association, back_populates="agents")


# -------------------
# Product
# -------------------
class Product(Base):
    __tablename__ = "product"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    artisan_id = Column(UUID(as_uuid=True), ForeignKey("artisan.id"))
    name = Column(String, nullable=False)
    description = Column(Text)
    category = Column(String)

    media = Column(JSONB)          # { "image": "base64...", "embedding": [...] }
    ip_status = Column(JSONB)      # { is_ip_registered, ip_type, registration_number, ... }

    authorization_id = Column(UUID(as_uuid=True), ForeignKey("authorization.id"))

    # Relationships
    artisan = relationship("Artisan", back_populates="products")
    rules = relationship("Rules", back_populates="product")


# -------------------
# Authorization
# -------------------
class Authorization(Base):
    __tablename__ = "authorization"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    artisan_id = Column(UUID(as_uuid=True), ForeignKey("artisan.id"))
    agent_id = Column(UUID(as_uuid=True), ForeignKey("agent.id"))

    consent_from_artisan = Column(Boolean)
    no_objection_certificate = Column(Boolean)
    power_of_attorney = Column(JSONB)       # { granted: bool, trademark_office: bool }
    previous_ip_rights = Column(JSONB)      # { is_derivative, right_owners: {has_rights, names: []} }

    date_granted = Column(Date)
    valid_till = Column(Date)


# -------------------
# Rules
# -------------------
class Rules(Base):
    __tablename__ = "rules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(UUID(as_uuid=True), ForeignKey("product.id"))

    allow_reproduction = Column(Boolean)
    allow_resale = Column(Boolean)
    allow_derivative = Column(Boolean)
    allow_commercial_use = Column(Boolean)
    allow_ai_training = Column(Boolean)

    license_duration = Column(Interval)
    geographical_limit = Column(String)
    royalty_percentage = Column(Numeric)

    # Relationship
    product = relationship("Product", back_populates="rules")
