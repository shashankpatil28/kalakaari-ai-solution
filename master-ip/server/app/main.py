from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Import new routers
from app.routes import craft, search

# Import DB helpers for admin endpoint
from app.db.mongodb import ensure_initialized, close as mongo_close

app = FastAPI(title="Master-IP Prototype Service", version="0.1.0")

# CORS
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

# --- Root and Admin Endpoints ---

@app.get("/")
async def root():
    return {"message": "Prototype Master-IP backend is running!"}


@app.post("/init-db")
async def init_db():
    """
    Admin: Initialize DB (call once after deploy).
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