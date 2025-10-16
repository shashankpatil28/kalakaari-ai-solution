# app/main.py
import os
from fastapi import FastAPI, HTTPException
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware

from app.routes.craftid import router as craftid_router
from app.routes.products import router as products_router

# Import helper from your mongodb.py
from app.mongodb import ensure_initialized, close as mongo_close

load_dotenv()

app = FastAPI(title="Shop Backend Service", version="0.1.0")

# CORS: allow your frontend (and add others here as needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "*"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(products_router)


@app.get("/")
async def root():
    return {"message": "Prototype Master-IP backend is running!"}


@app.post("/init-db")
async def init_db():
    """
    Admin: Initialize DB (call once after deploy).
    If ensure_initialized fails due to old loop issues, attempt to reset client and retry.
    """
    try:
        await ensure_initialized()
    except Exception as e:
        # try reset and retry
        try:
            mongo_close()
            await ensure_initialized()
        except Exception as e2:
            raise HTTPException(status_code=502, detail=f"DB init failed: {e}; retry failed: {e2}")
    return {"status": "ok", "detail": "DB initialized or already ready."}
