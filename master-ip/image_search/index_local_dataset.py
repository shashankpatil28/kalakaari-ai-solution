# verbose patched index_local_dataset.py
import os, json
from pathlib import Path
from pymongo import MongoClient
from clip_embedder import ClipEmbedder
from PIL import Image
from tqdm import tqdm

# optionally load .env
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

PINECONE_API_KEY = os.environ.get("PINECONE_API_KEY")
INDEX_HOST = os.environ.get("INDEX_HOST")
MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017")
DATA_ROOT = os.environ.get("DATA_ROOT", "./data")
BATCH = int(os.environ.get("PINECONE_BATCH", "64"))

print("CONFIG ->", {"DATA_ROOT": DATA_ROOT, "INDEX_HOST": INDEX_HOST, "MONGO_URI": MONGO_URI})

if not PINECONE_API_KEY:
    raise RuntimeError("Set PINECONE_API_KEY env var")
if not INDEX_HOST:
    raise RuntimeError("Set INDEX_HOST env var (e.g. test1-xxxx.pinecone.io)")
if not Path(DATA_ROOT).exists():
    raise RuntimeError(f"DATA_ROOT not found: {DATA_ROOT}")

# Pinecone client
from pinecone import Pinecone
pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(host=INDEX_HOST)
print("Connected to Pinecone index via host:", INDEX_HOST)

# Mongo
mongo = MongoClient(MONGO_URI)
db = mongo["master_ip"]
images_col = db["image_index"]

# Embedder
embedder = ClipEmbedder()

def load_metadata(path: Path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print("WARN: failed to load metadata:", path, e)
        return None

def map_metadata(meta):
    mapping = {}
    if isinstance(meta, dict):
        mapping.update(meta)
    elif isinstance(meta, list):
        for m in meta:
            fname = m.get("filename") or m.get("file") or m.get("name")
            if fname:
                mapping[str(fname)] = m
    return mapping

def gen_id(folder, fname, meta):
    if isinstance(meta, dict) and meta.get("id"):
        return str(meta["id"])
    return f"{folder}::{fname}"

root = Path(DATA_ROOT)
folders = [p for p in root.iterdir() if p.is_dir()]
print("Found folders:", [p.name for p in folders])

total_indexed = 0
buffer = []

for folder in folders:
    folder_name = folder.name
    meta_file = folder / "metadata.json"
    meta_map = {}
    if meta_file.exists():
        meta_map = map_metadata(load_metadata(meta_file) or {})

    # Use recursive search so nested images are found
    imgs = [p for p in folder.rglob("*") if p.suffix.lower() in [".jpg", ".jpeg", ".png", ".webp"]]
    print(f"Folder '{folder_name}' -> found {len(imgs)} image(s) (recursive)")

    if not imgs:
        continue

    for img_path in tqdm(imgs, desc=f"Indexing {folder_name}"):
        fname = img_path.name
        md = meta_map.get(fname, {})
        doc_id = gen_id(folder_name, fname, md)

        try:
            img = Image.open(img_path).convert("RGB")
        except Exception as e:
            print(f"ERROR opening image {img_path}: {e}")
            continue

        try:
            vec = embedder.embed_pil(img)
        except Exception as e:
            print(f"ERROR embedding image {img_path}: {e}")
            continue

        pine_meta = {
            "source": str(img_path.resolve()),
            "folder": folder_name,
            "filename": fname,
            "brief": (md.get("brief") if isinstance(md, dict) else "") or ""
        }

        buffer.append((doc_id, vec, pine_meta))

        # Mongo upsert (store full meta)
        try:
            doc = {"_id": doc_id, "folder": folder_name, "filename": fname, "source": str(img_path.resolve()), "meta": md}
            images_col.replace_one({"_id": doc_id}, doc, upsert=True)
        except Exception as e:
            print(f"WARN: mongo upsert failed for {doc_id}: {e}")

        total_indexed += 1

        if len(buffer) >= BATCH:
            try:
                resp = index.upsert(vectors=buffer)
            except TypeError:
                resp = index.upsert(buffer)
            print("Pinecone upsert response:", resp)
            buffer = []

# final flush
if buffer:
    try:
        resp = index.upsert(vectors=buffer)
    except TypeError:
        resp = index.upsert(buffer)
    print("Final Pinecone upsert response:", resp)

print("TOTAL indexed (attempted):", total_indexed)
print("Mongo count:", images_col.count_documents({}))
