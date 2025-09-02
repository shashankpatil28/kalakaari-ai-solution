# app/main.py
import json
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl
from typing import List
from fastapi.encoders import jsonable_encoder  # ✅ Fix for serialization

# Import CORSMiddleware
from fastapi.middleware.cors import CORSMiddleware

# --- Pydantic Models ---
class VerificationData(BaseModel):
    public_id: str
    public_hash: str
    verification_url: HttpUrl

class ArtisanInfo(BaseModel):
    name: str
    location: str

class ArtInfo(BaseModel):
    name: str
    description: str
    photo: str

class AddProductRequest(BaseModel):
    artisan_info: ArtisanInfo
    art_info: ArtInfo
    verification: VerificationData

class Product(BaseModel):
    artisan_info: ArtisanInfo
    art_info: ArtInfo
    verification: VerificationData

# --- Mock Database Functions ---
DATABASE_FILE = "shop_db.json"

def get_shop_db() -> List[dict]:
    if not os.path.exists(DATABASE_FILE):
        with open(DATABASE_FILE, "w") as f:
            json.dump([], f)
    with open(DATABASE_FILE, "r") as f:
        return json.load(f)

def save_shop_db(data: List[dict]):
    with open(DATABASE_FILE, "w") as f:
        json.dump(data, f, indent=4)

# --- FastAPI Application ---
app = FastAPI()

# Add the CORS middleware here
origins = [
    "http://localhost:4200",  # Your Angular frontend's origin
    "http://127.0.0.1:4200",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allows all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)

@app.post("/add-product", response_model=dict)
def add_product(product_data: AddProductRequest):
    """
    Receives a new product listing from the agentic service and stores it in the shop database.
    """
    db = get_shop_db()
    
    # Prevent duplicate entries
    for product in db:
        if product["verification"]["public_id"] == product_data.verification.public_id:
            raise HTTPException(status_code=409, detail="Product with this CraftID already exists.")
    
    # ✅ Convert to JSON-serializable dict
    serialized_product = jsonable_encoder(product_data)
    db.append(serialized_product)
    save_shop_db(db)
    
    return {"status": "success", "message": "Product added to the shop successfully."}

@app.get("/get-products", response_model=List[Product])
def get_products():
    """
    Returns a list of all products in the shop database.
    """
    db = get_shop_db()
    return db
