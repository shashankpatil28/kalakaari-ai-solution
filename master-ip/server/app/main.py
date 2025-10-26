from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Import new routers
from .routes import craft, search

# Import DB helpers for admin endpoint
from .db.mongodb import ensure_initialized, close as mongo_close

app = FastAPI(title="Master-IP Prototype Service", version="0.1.0")

# CORS: allow your frontend (and add others here as needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Include Routers ---
# Note: We don't need to load_dotenv() here, 
# it's handled by app/constants.py when it's first imported.
app.include_router(craft.router)
app.include_router(search.router)

# --- Root and Admin Endpoints ---

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