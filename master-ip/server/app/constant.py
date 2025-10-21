# app/constants.py
import os
from dotenv import load_dotenv

load_dotenv()

# --- JWT ---
SECRET_KEY = os.getenv("SECRET_KEY", "change_in_prod")
ALGORITHM = "HS256"

# --- MongoDB ---
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME", "masterip_db")

# --- Pinecone (Image Search) ---
PINECONE_API_KEY = os.environ.get("PINECONE_API_KEY")
INDEX_HOST = os.environ.get("INDEX_HOST")  # example: test1-xxxx.pinecone.io

# --- Pinecone (Text Search) ---
PINECONE_ENV = os.getenv("PINECONE_ENV") # e.g., "gcp-starter" or "us-west1-gcp"
PINECONE_TEXT_INDEX = os.getenv("PINECONE_TEXT_INDEX", "text")

# --- Embedders ---
CLIP_MODEL_NAME = "openai/clip-vit-base-patch32"  # 512-dim
TEXT_MODEL_NAME = "sentence-transformers/all-MiniLM-L12-v2"

# --- Search ---
TOP_K_DEFAULT = 5

# --- HTTP Client ---
FETCH_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0 Safari/537.36",
    "Accept": "image/*,*/*;q=0.8",
    "Referer": "https://upload.wikimedia.org/"
}