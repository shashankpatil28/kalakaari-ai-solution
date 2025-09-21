# app/mongodb.py
import os
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional
from pymongo import ReturnDocument

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME   = os.getenv("DB_NAME", "masterip_db")

class MongoDB:
    client: Optional[AsyncIOMotorClient] = None
    db = None

    @classmethod
    def init(cls, uri: str, db_name: str):
        # AsyncIOMotorClient is created synchronously, but you can await ops (like create_index)
        cls.client = AsyncIOMotorClient(uri)
        cls.db = cls.client[db_name]

    @classmethod
    async def create_indexes(cls):
        # craftids collection indexes:
        coll = cls.collection("craftids")
        # unique public_id
        await coll.create_index([("public_id", 1)], unique=True)
        # normalized art name for case-insensitive uniqueness check
        await coll.create_index([("art_name_norm", 1)], unique=True)
        # optional: index on public_hash for fast lookup
        await coll.create_index([("public_hash", 1)], unique=False)

    @classmethod
    def collection(cls, name: str):
        if cls.db is None:
            raise RuntimeError("Database not initialized")
        return cls.db[name]

    @classmethod
    async def next_sequence(cls, name: str) -> int:
        # atomic counter for sequential public IDs (like CID-00001)
        counters = cls.collection("counters")
        doc = await counters.find_one_and_update(
            {"_id": name},
            {"$inc": {"seq": 1}},
            upsert=True,
            return_document=ReturnDocument.AFTER
        )
        return int(doc["seq"])

    @classmethod
    def close(cls):
        if cls.client:
            cls.client.close()
