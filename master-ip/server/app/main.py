# app/main.py
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from dotenv import load_dotenv
from app.mongodb import MongoDB
from app.routes.craftid import router as craftid_router

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME   = os.getenv("DB_NAME", "masterip_db")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # init client (synchronous creation)
    MongoDB.init(MONGO_URI, DB_NAME)
    # ensure indexes (awaitable)
    await MongoDB.create_indexes()
    try:
        yield
    finally:
        MongoDB.close()

app = FastAPI(title="Master-IP Prototype Service", version="0.1.0", lifespan=lifespan)

app.include_router(craftid_router)
@app.get("/")
async def root():   
    return {
        "hi"
    }
