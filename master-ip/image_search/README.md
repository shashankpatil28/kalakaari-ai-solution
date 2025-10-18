
### Create & activate virtualenv (recommended)

Run from repo root (`master-ip`):

```bash
# create venv if not present (run once)
python -m venv .venv

# activate
# macOS / Linux
source .venv/bin/activate

# Windows (PowerShell)
# .venv\Scripts\Activate.ps1
```

### Install Python deps (server & image-search)

From repo root (`master-ip`):

```bash
# ensure pip up-to-date
python -m pip install --upgrade pip

# Install main server deps (fastapi, uvicorn, pymongo, pinecone, pillow, transformers, torch, etc.)
# If requirements.txt exists, prefer:
pip install -r server/requirements.txt
# otherwise install minimal packages:
pip install fastapi uvicorn pymongo requests pillow python-dotenv python-jose transformers torch pinecone[grpc]
```

> NOTE: The Pinecone SDK must be the modern `pinecone` package. If you get an error about `pinecone-client`, run:
>
> ```bash
> python -m pip uninstall -y pinecone-client
> python -m pip install "pinecone[grpc]"
> ```

---

## 3) Make `image-search` importable (editable install)

To allow the FastAPI code to `from image_search.clip_embedder import ClipEmbedder`:

From repo root `master-ip`:

```bash

# install it into the same venv used by server
python -m pip install -e ./image_search
```

Verify imports:

```bash
python - <<'PY'
try:
    from image_search.clip_embedder import ClipEmbedder
    print("✅ image_search.clip_embedder import OK")
except Exception as e:
    print("❌ import failed:", e)
PY
```

If this fails, ensure you are using the same `python`/`.venv` where the server will run (see troubleshooting).

---

## 5) Start the FastAPI server (image-search routes)

Set env vars (do **not** commit secrets):

```bash
# inside .venv
export PINECONE_API_KEY="YOUR_PINECONE_KEY"
export INDEX_HOST=""   # your host or just host w/o https
export MONGO_URI="mongodb+srv://<user>:<pw>@cluster.mongodb.net/?retryWrites=true&w=majority"
export SECRET_KEY="change_in_prod"   # for existing craft routes
```

Start Uvicorn from `/master-ip/server`:

```bash
cd server
uvicorn app.main:app --reload --port 8000
```

Server URL: `http://127.0.0.1:8000`

---

## 6) Test endpoints — `curl` commands

> Replace file paths, image URLs, and craft IDs as needed. Use direct raw image URLs (not HTML page links).



### 6.1 `/image-search/url` — query by remote image URL

```bash
curl -X POST "http://127.0.0.1:8000/image-search/url" \
  -F "image_url=<image-url>" \
  -F "top_k=5"
```

If remote hosts block requests (403), the server fetch uses a browser-like `User-Agent` and retries; ensure `_fetch_image_from_url` in `craft_controllers.py` contains the headers snippet. For testing from CLI, you can also include a UA in curl:

```bash
curl -A "Mozilla/5.0 (X11; Linux x86_64) ..." \
  -X POST "http://127.0.0.1:8000/image-search/url" \
  -F "image_url=<raw_image_url>" -F "top_k=3"
```

### 6.3 `/image-search/upsert` — upsert new craft + metadata

Example Ajrak artifact:

```bash
curl -X POST "http://127.0.0.1:8000/image-search/upsert" \
  -F "craft_id=CRAFT_000022" \
  -F "image_url=https://upload.wikimedia.org/wikipedia/commons/f/f3/Ajrak_print_from_Sindh.jpg" \
  -F 'metadata={"title":"Ajrak Block Printed Textile","artisan":"Sindhi Craftsmen","category":"Hand Block Printing","region":"Kutch, Gujarat","description":"Traditional Ajrak fabric."}'
```

**Expected success response**:

```json
{"status":"ok","pinecone":{"upserted_count":1},"doc_id":"CRAFT_000022"}
```

### 6.4 Verify inserted metadata in Mongo

If you use mongo shell or `mongosh`, run:

```bash
mongosh "<your-atlas-uri>" --eval 'db.getSiblingDB("master_ip").image_index.findOne({"_id":"CRAFT_000022"})'
```

---

## 7) What each route does (short)


* `POST /image-search/url`

  * Accepts `image_url` (form), `top_k`, `include_meta`.
  * Fetches remote image (with UA & retry), embeds, queries Pinecone, returns results.

* `POST /image-search/upsert`

  * Accepts `craft_id` (optional), `image_url` (required), `metadata` (JSON string form).
  * Fetches image, embeds, upserts single vector to Pinecone and stores full metadata in Mongo under `_id == craft_id` (or auto-generated `url::<hash>` if not provided).
  * Returns safe JSON (normalized `upserted_count`) to avoid FastAPI encoder errors.

---

## 8) Common troubleshooting & tips

### 8.1 `ModuleNotFoundError: No module named 'clip_embedder'` or `image_search`

* Ensure `image_search` package is importable. Install editable with the `python -m pip install -e ./image_search` command while using the same `.venv` used to run uvicorn.
* If Uvicorn runs in a different working directory, either:

  * set `PYTHONPATH` before launching Uvicorn:

    ```bash
    export PYTHONPATH="/path/to/master-ip:${PYTHONPATH:-}"
    uvicorn app.main:app --reload --port 8000
    ```
  * or add a small `sys.path` insert at top of `server/app/main.py` (not preferred for prod).

### 8.2 Pinecone `403 Forbidden` / Wrong API key

* Re-check `PINECONE_API_KEY` environment variable: copy directly from Pinecone console (no leading/trailing spaces).
* Ensure key belongs to the project where `test1` index exists, and `INDEX_HOST` points to your index host.

### 8.3 Remote fetch 403 errors for Wikimedia / CDNs

* Make sure `_fetch_image_from_url` uses browser-like headers:

  ```py
  headers = {"User-Agent": "Mozilla/5.0 ...", "Accept": "image/*,*/*;q=0.8", "Referer": "..."}
  ```
* For private images, provide signed URLs or POST the image bytes instead of a URL.

### 8.4 FastAPI JSON encoding RecursionError

* Do not return raw SDK objects (Pinecone response or PyMongo Cursor) directly. The code normalizes Pinecone results to `{"upserted_count": N}` before returning.

### 8.5 If index returns results but they’re poor

* Ensure normalization of embeddings (L2 normalized) and Pinecone metric is `cosine`. The `ClipEmbedder` provided already normalizes outputs.
* Try increasing dataset or re-check model version.

---


## Appendix — Useful commands (copy-paste)

```bash
# activate venv
cd /Users/<you>/.../master-ip
source .venv/bin/activate

# install server deps (if no requirements.txt)
python -m pip install fastapi uvicorn pymongo requests pillow python-dotenv transformers torch "pinecone[grpc]"

# install image_search editable
python -m pip install -e ./image_search

# index local data
export PINECONE_API_KEY="..."
export INDEX_HOST="test1-xxxx.pinecone.io"
export MONGO_URI="mongodb+srv://..."
export DATA_ROOT="./image_search/data"
python image_search/index_local_dataset.py

# run server
cd server
export PINECONE_API_KEY="..."
export INDEX_HOST="..."
export MONGO_URI="..."
uvicorn app.main:app --reload --port 8000

# test endpoints — example upsert
curl -X POST "http://127.0.0.1:8000/image-search/upsert" \
  -F "craft_id=CRAFT_000022" \
  -F "image_url=<image-url" \
  -F 'metadata={"title":"Ajrak","artisan":"Sindhi Craftsmen"}'
```

