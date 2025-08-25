# app/main.py
from fastapi import FastAPI

from .models.model import Base

from .db.db import engine
from .db.db import db_ping

# Create all tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Master-IP Service", version="0.1.0")

@app.on_event("startup")
def _startup():
    # Verify DB connection when the server starts
    db_ping()

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/")
def root():
    return {"message": "Backend is working!"}
