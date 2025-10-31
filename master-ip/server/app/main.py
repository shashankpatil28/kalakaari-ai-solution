from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
import logging # For logging startup/shutdown

# Import new routers
from app.routes import craft, search

# Import DB connect/close functions
from app.db.mongodb import connect_db, close_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Lifespan Event Handler ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Code to run on startup
    logger.info("Application startup...")
    await connect_db()
    yield # Application runs here
    # Code to run on shutdown
    logger.info("Application shutdown...")
    await close_db()

# Create FastAPI app instance with lifespan manager
app = FastAPI(
    title="Master-IP Prototype Service",
    version="0.1.0",
    lifespan=lifespan # Register the lifespan handler
)

# --- CORS Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Include Routers ---
app.include_router(craft.router)
app.include_router(search.router)

# --- Root Endpoint ---
@app.get("/")
async def root():
    return {"message": "Prototype Master-IP backend is running!"}
