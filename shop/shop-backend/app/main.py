# app/main.py
import os
from fastapi import FastAPI, HTTPException
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
import logging
from pathlib import Path 

from app.routes.products import router as products_router
from app.mongodb import connect_to_mongo, close_mongo_connection

DOTENV_PATH = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=DOTENV_PATH)

app = FastAPI(title="Shop Backend Service", version="0.1.0")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup_event():
    """
    On app startup, connect to MongoDB.
    """
    logger.info("Application startup...")
    try:
        await connect_to_mongo()
    except Exception as e:
        logger.error(f"FATAL: Could not connect to MongoDB on startup: {e}")
        pass

@app.on_event("shutdown")
def shutdown_event():
    """
    On app shutdown, close the MongoDB connection.
    """
    logger.info("Application shutdown...")
    close_mongo_connection()


# CORS: allow your frontend (and add others here as needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "*" # WARNING: Change to your frontend URL in production
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(products_router)

@app.get("/")
async def root():
    return {"message": "Shop backend is running!"}