bash
~~~
master-ip/
└── server/
    ├── .env                        # local dev env (DO NOT commit)
    ├── Dockerfile                  # container for FastAPI + optional batcher entry
    ├── docker-compose.yml          # local dev (optional)
    ├── requirements.txt
    ├── README.md
    ├── app/
    │   ├── main.py                 # FastAPI app entry (uvicorn)
    │   ├── mongodb.py              # mongo helpers / collection()
    │   ├── models.py               # pydantic models
    │   └── routes/
    │       ├── craftid.py          # POST /create -> compute hash, attestation, store queued
    │       ├── verify.py           # GET /verify/{public_id} -> pending/anchored/tampered
    │       ├── metadata_search.py
    │       └── craft_controllers.py
    │
    ├── chain/                      # single package for chain logic (like image_search)
    │   ├── __init__.py
    │   ├── README.md
    │   ├── requirements.txt        # web3, cryptography (can be merged with top-level)
    │   ├── hashing.py              # deterministic JSON hashing (exclude photo_url)
    │   ├── signer.py               # attestation sign/verify (ECDSA; dev-friendly)
    │   ├── web3_client.py          # web3.py anchor_hash_on_chain(), is_anchored()
    │   ├── queue.py                # enqueue_item(), dequeue_for_worker()
    │   ├── batcher.py              # batcher/worker to process queued items (per-item anchor)
    │   └── utils.py                # small helpers: hex, time, logging
    │
    ├── scripts/
       ├── start-batcher.sh        # wrapper to run `python -m chain.batcher`
       └── anchor-now.sh           # optional: one-off anchor helper

## To Create keys (inside master-ip/chain/keys)
~~~

openssl ecparam -name prime256v1 -genkey -noout -out sign_priv.pem
openssl ec -in sign_priv.pem -pubout -out sign_pub.pem

~~~

## To Create

~~~
curl -sS -X POST "http://localhost:8000/create" \
  -H "Content-Type: application/json" \
  -d '{"artisan":{"name":"Ravi Verma","location":"Mithila, Bihar","contact_number":"9876543210","email":"ravi@example.com","aadhaar_number":"1234-5678-9101"},"art":{"name":"Madhubani Painting","description":"Traditional artwork depicting rural folklore","photo_url":"https://cdn.example.com/img123.jpg"}}' | jq
~~~


## To Anchor

~~~
python -m batcher.py. (from master-ip/)
~~~


## To Verify

~~~
curl -s http://localhost:8000/verify/CID-00020 | python3 -m json.tool
~~~

## To verify on internet 

~~~
https://amoy.polygonscan.com/tx/0x<TX_HASH>
~~~

