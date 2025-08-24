from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from supabase import create_client, Client

# ------------------------
# Supabase Connection
# ------------------------
SUPABASE_URL = "https://lvquxorjhuomllsiuwvx.supabase.co"   # Your Supabase project URL
SUPABASE_KEY = "..."  # Your anon/public key from Supabase project settings
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)  # Create a Supabase client

# Initialize FastAPI app
app = FastAPI(title="Shop Backend")

# ------------------------
# Pydantic Models (used to validate request/response data)
# ------------------------
class ContactInfo(BaseModel):
    # Nested object for artisan contact details
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None

class Artisan(BaseModel):
    # Model for artisans
    id: Optional[str] = None                # UUID (auto-generated in DB usually)
    name: str                               # Required artisan name
    contact_info: Optional[ContactInfo] = None  # Optional nested contact info
    skills: Optional[List[str]] = []        # List of skills
    products: Optional[List[str]] = []      # List of product IDs (FK references)

class Product(BaseModel):
    # Model for products
    id: Optional[str] = None
    artisan_id: str                         # FK -> artisan.id
    name: str                               # Product name
    description: Optional[str] = None
    category: Optional[str] = None
    media: Optional[List[str]] = []         # Store base64 images or embeddings
    ip_status: Optional[dict] = None        # JSON object for IP details

class Rules(BaseModel):
    # Model for rules/permissions on products
    id: Optional[str] = None
    product_id: str                         # FK -> product.id
    allow_reproduction: bool
    allow_resale: bool
    allow_derivative: bool
    allow_commercial_use: bool
    allow_ai_training: bool
    license_duration: Optional[str] = None  # Example: "1 year"
    geographical_limit: Optional[str] = None
    royalty_percentage: Optional[float] = None


# ------------------------
# Artisan Endpoints
# ------------------------

# Add a new artisan
@app.post("/artisans")
async def add_artisan(artisan: Artisan):
    res = supabase.table("artisan").insert(artisan.dict(exclude_unset=True)).execute()
    return res.data

# Fetch all artisans
@app.get("/artisans")
async def get_artisans():
    res = supabase.table("artisan").select("*").execute()
    return res.data

# Fetch a single artisan by ID
@app.get("/artisans/{artisan_id}")
async def get_artisan(artisan_id: str):
    res = supabase.table("artisan").select("*").eq("id", artisan_id).execute()
    if not res.data:  # If no artisan found, throw 404
        raise HTTPException(status_code=404, detail="Artisan not found")
    return res.data[0]

# Delete an artisan by ID
@app.delete("/artisans/{artisan_id}")
async def delete_artisan(artisan_id: str):
    res = supabase.table("artisan").delete().eq("id", artisan_id).execute()
    return {"message": "Deleted", "count": len(res.data)}


# ------------------------
# Product Endpoints
# ------------------------

# Add a new product
@app.post("/products")
async def add_product(product: Product):
    res = supabase.table("product").insert(product.dict(exclude_unset=True)).execute()
    return res.data

# Fetch all products
@app.get("/products")
async def get_products():
    res = supabase.table("product").select("*").execute()
    return res.data

# Fetch a single product by ID
@app.get("/products/{product_id}")
async def get_product(product_id: str):
    res = supabase.table("product").select("*").eq("id", product_id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Product not found")
    return res.data[0]

# Delete a product by ID
@app.delete("/products/{product_id}")
async def delete_product(product_id: str):
    res = supabase.table("product").delete().eq("id", product_id).execute()
    return {"message": "Deleted", "count": len(res.data)}


# ------------------------
# Rules Endpoints
# ------------------------

# Add a new rule for a product
@app.post("/rules")
async def add_rule(rule: Rules):
    res = supabase.table("rules").insert(rule.dict(exclude_unset=True)).execute()
    return res.data

# Fetch all rules
@app.get("/rules")
async def get_rules():
    res = supabase.table("rules").select("*").execute()
    return res.data

# Fetch a single rule by ID
@app.get("/rules/{rule_id}")
async def get_rule(rule_id: str):
    res = supabase.table("rules").select("*").eq("id", rule_id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Rule not found")
    return res.data[0]

# Delete a rule by ID
@app.delete("/rules/{rule_id}")
async def delete_rule(rule_id: str):
    res = supabase.table("rules").delete().eq("id", rule_id).execute()
    return {"message": "Deleted", "count": len(res.data)}
