# /master-ip/image-search/test_query.py
"""
Quick CLI tester for image→image semantic search in Pinecone.
Run from /master-ip/image-search after activating venv.

Usage:
    python test_query.py --image ./data/raw/image1.jpg --top_k 5
"""

import os
import argparse
from io import BytesIO
from PIL import Image
from clip_embedder import ClipEmbedder
from pinecone import Pinecone
from pymongo import MongoClient

# --- Configuration ---
PINECONE_API_KEY = os.environ.get("PINECONE_API_KEY")
INDEX_HOST = os.environ.get("INDEX_HOST")  # e.g. test1-xxxx.pinecone.io
MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017")

if not PINECONE_API_KEY or not INDEX_HOST:
    raise RuntimeError("Set PINECONE_API_KEY and INDEX_HOST env vars before running.")

# Initialize Pinecone + Mongo + CLIP embedder
pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(host=INDEX_HOST)
mongo = MongoClient(MONGO_URI)
images_col = mongo["master_ip"]["image_index"]
embedder = ClipEmbedder()

# --- Parse args ---
parser = argparse.ArgumentParser()
parser.add_argument("--image", required=True, help="Path to local image file to query.")
parser.add_argument("--top_k", type=int, default=5, help="Number of results to return.")
args = parser.parse_args()

# --- Load & embed ---
img_path = args.image
if not os.path.isfile(img_path):
    raise FileNotFoundError(f"Image not found: {img_path}")

img = Image.open(img_path).convert("RGB")
vec = embedder.embed_pil(img)

# --- Query Pinecone ---
print(f"\n🔍 Querying Pinecone index '{INDEX_HOST}' for similar images...")
try:
    res = index.query(vector=vec, top_k=args.top_k, include_metadata=True)
except TypeError:
    res = index.query(vec, top_k=args.top_k, include_metadata=True)

matches = res.get("matches") or getattr(res, "matches", [])
if not matches:
    print("No matches found.")
    exit(0)

print(f"\nTop {len(matches)} similar images:\n")
for i, m in enumerate(matches, start=1):
    mid = m.get("id") if isinstance(m, dict) else getattr(m, "id", None)
    score = m.get("score") if isinstance(m, dict) else getattr(m, "score", None)
    meta = m.get("metadata") if isinstance(m, dict) else getattr(m, "metadata", {})
    print(f"{i}. ID: {mid}")
    print(f"   Similarity: {score:.4f}")
    print(f"   Source: {meta.get('source', '')}")
    print(f"   Folder: {meta.get('folder', '')}")
    print(f"   Filename: {meta.get('filename', '')}")
    print(f"   Brief: {meta.get('brief', '')}")
    # optional: fetch full metadata from Mongo
    doc = images_col.find_one({"_id": mid})
    if doc:
        print(f"   Mongo Meta keys: {list(doc.get('meta', {}).keys())}")
    print("-" * 60)
