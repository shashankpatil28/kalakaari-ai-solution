
### Create & activate virtualenv (recommended)

Run from repo root (`master-ip/server`):

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

## Start the FastAPI server (image-search routes)

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

----

