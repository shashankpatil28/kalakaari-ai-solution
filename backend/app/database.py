# app/database.py
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL not set in .env")

# Ensure SSL for Supabase. Add ?sslmode=require if not present.
if "sslmode=" not in DATABASE_URL:
    sep = "&" if "?" in DATABASE_URL else "?"
    DATABASE_URL = f"{DATABASE_URL}{sep}sslmode=require"

# Create engine
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # helps avoid stale connections
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def db_ping():
    """Run a simple SELECT 1 to verify the DB connection works."""
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
        print("INFO: Database connection successful.") # Added print statement

