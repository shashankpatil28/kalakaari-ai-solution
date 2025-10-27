# Master-IP Backend Service

> A FastAPI-based backend service for managing digital CraftIDs. It provides a full REST API for creating and verifying assets, a vector-based search engine for images and metadata, and an integrated blockchain batching system to anchor assets on-chain.

This document provides all the necessary instructions to set up, run, and deploy the Master-IP backend service.

---

## Table of Contents

1. [Local Development Setup](#local-development-setup)

   * [Prerequisites](#prerequisites)
   * [Installation](#installation)
   * [1. Generate Local Keys (One-Time Setup)](#1-generate-local-keys-one-time-setup)
   * [2. Environment Variables](#2-environment-variables)
   * [3. Running the Application](#3-running-the-application)
2. [Deployment to Google Cloud Run](#deployment-to-google-cloud-run)

   * [Deployment Prerequisites](#deployment-prerequisites)
   * [Step-by-Step Deployment Guide](#step-by-step-deployment-guide)

---

## Local Development Setup

Follow these instructions to get the application running on your local machine for development and testing. All commands are run from the `master-ip/server/` directory.

### Prerequisites

Ensure you have the following software installed:

* **Python 3.10+**
* **Pip** (Python Package Installer)
* **Git**
* **OpenSSL** (for generating keys)

### Installation

1. **Clone the repository:**

   ```bash
   git clone <your-repository-url>
   cd master-ip/server
   ```

2. **Create and activate a virtual environment:**

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install the required dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

### 1. Generate Local Keys (One-Time Setup)

The `chain` module requires cryptographic keys to sign attestations.

1. **Create a directory for your keys:**

   ```bash
   mkdir -p chain/keys
   ```

2. **Generate the key files:**

   ```bash
   openssl ecparam -name prime256v1 -genkey -noout -out chain/keys/sign_priv.pem
   openssl ec -in chain/keys/sign_priv.pem -pubout -out chain/keys/sign_pub.pem
   ```

3. **Get the absolute path** to these keys. You will need this for your `.env` file.

   ```bash
   pwd
   ```

### 2. Environment Variables

The application requires several environment variables to connect to external services.

1. Create a file named `.env` in the `master-ip/server/` directory.
2. Copy the content below into the `.env` file and replace the placeholder values with your actual credentials.

```env
# .env

# --- MongoDB ---
MONGO_URI="mongodb+srv://<user>:<password>@<cluster-url>/..."
DB_NAME="masterip_db"

# --- JWT ---
SECRET_KEY="your_super_strong_random_secret_key"

# --- Pinecone ---
PINECONE_API_KEY="your_pinecone_api_key"
PINECONE_ENV="your_pinecone_environment_region"
INDEX_HOST="your_image_index_host.svc.pinecone.io"
PINECONE_TEXT_INDEX="text"

# --- Local Key Paths (REQUIRED) ---
SIGNER_KEY_PATH="/path/to/master-ip/server/chain/keys/sign_priv.pem"
PLATFORM_PUBKEY_PATH="/path/to/master-ip/server/chain/keys/sign_pub.pem"

# --- Blockchain Configuration ---
WEB3_RPC_URL="https://rpc-amoy.polygon.technology"
CHAIN_ID=80002
ANCHOR_CONTRACT_ADDRESS="0x..."
ANCHORER_PRIVATE_KEY="your_wallet_private_key"

# Queue & Batcher Settings
ANCHOR_QUEUE_COLL="anchor_queue"
QUEUE_FETCH_MAX=5
BATCH_LIMIT=5
POLL_INTERVAL=10

# --- Other (Optional) ---
GCS_BUCKET_NAME="your-gcs-bucket-name"
```

### 3. Running the Application

The service requires two separate processes to run in parallel.

#### In Terminal 1: Run the Web Server

```bash
source .venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Access the API at: [http://localhost:8000](http://localhost:8000)
Docs available at: [http://localhost:8000/docs](http://localhost:8000/docs)

#### In Terminal 2: Run the Chain Batcher

```bash
source .venv/bin/activate
python -m chain.batcher
```

---

## Deployment to Google Cloud Run

### Deployment Prerequisites

* **Google Cloud SDK (gcloud CLI)** installed and configured
* **Docker** installed and running
* Authenticate with GCP:

  ```bash
  gcloud auth login
  ```

### Step-by-Step Deployment Guide

#### Step 1: Secure Secrets (One-Time Setup)

Enable Secret Manager API:

```bash
gcloud services enable secretmanager.googleapis.com
```

Generate local keys (if not done earlier):

```bash
mkdir -p chain/keys
openssl ecparam -name prime256v1 -genkey -noout -out chain/keys/sign_priv.pem
openssl ec -in chain/keys/sign_priv.pem -pubout -out chain/keys/sign_pub.pem
```

Store secrets in GCP:

```bash
gcloud secrets create master-ip-signer-key --replication-policy="automatic" --data-file="chain/keys/sign_priv.pem"
gcloud secrets create master-ip-platform-pubkey --replication-policy="automatic" --data-file="chain/keys/sign_pub.pem"

export ANCHOR_KEY_VALUE=$(grep ANCHORER_PRIVATE_KEY .env | cut -d '=' -f2)
echo $ANCHOR_KEY_VALUE | gcloud secrets create master-ip-anchorer-key --replication-policy="automatic" --data-file=-
```

#### Step 2: Configure gcloud CLI

```bash
gcloud config set project kalakaari-ai
gcloud config set compute/region asia-southeast1
```

#### Step 3: Enable Required APIs

```bash
gcloud services enable artifactregistry.googleapis.com run.googleapis.com secretmanager.googleapis.com
```

#### Step 4: Create an Artifact Registry Repository

```bash
gcloud artifacts repositories create master-ip-containers --repository-format=docker --location=asia-southeast1 --description="Repository for master-ip-service images"
```

#### Step 5: Authenticate Docker with GCP

```bash
gcloud auth configure-docker asia-southeast1-docker.pkg.dev
```

#### Step 6: Build, Tag, and Push the Docker Image

```bash
export IMAGE_NAME="asia-southeast1-docker.pkg.dev/kalakaari-ai/master-ip-containers/backend-latest"

docker build -t $IMAGE_NAME .

docker push $IMAGE_NAME
```

#### Step 7: Grant Secret Permissions

```bash
gcloud secrets add-iam-policy-binding master-ip-signer-key --member="serviceAccount:978458840399-compute@developer.gserviceaccount.com" --role="roles/secretmanager.secretAccessor"

gcloud secrets add-iam-policy-binding master-ip-platform-pubkey --member="serviceAccount:978458840399-compute@developer.gserviceaccount.com" --role="roles/secretmanager.secretAccessor"

gcloud secrets add-iam-policy-binding master-ip-anchorer-key --member="serviceAccount:978458840399-compute@developer.gserviceaccount.com" --role="roles/secretmanager.secretAccessor"
```

#### Step 8: Deploy to Cloud Run

```bash
gcloud run deploy master-ip-service --image=$IMAGE_NAME --platform=managed --region=asia-southeast1 --port=8000 --allow-unauthenticated --memory=2Gi --cpu=2 --set-secrets="/run/secrets/signer-key/sign_priv.pem=master-ip-signer-key:latest" --set-secrets="/run/secrets/platform-pubkey/sign_pub.pem=master-ip-platform-pubkey:latest" --set-secrets="/run/secrets/anchorer-key/anchor_priv.key=master-ip-anchorer-key:latest" --set-env-vars="SIGNER_KEY_PATH=/run/secrets/signer-key/sign_priv.pem" --set-env-vars="PLATFORM_PUBKEY_PATH=/run/secrets/platform-pubkey/sign_pub.pem" --set-env-vars="ANCHORER_PRIVATE_KEY=/run/secrets/anchorer-key/anchor_priv.key" --set-env-vars="MONGO_URI=[YOUR_MONGO_URI_HERE]" --set-env-vars="PINECONE_API_KEY=[YOUR_PINECONE_API_KEY]" --set-env-vars="ANCHOR_CONTRACT_ADDRESS=[YOUR_CONTRACT_ADDRESS_HERE]" --set-env-vars="DB_NAME=masterip_db" --set-env-vars="SECRET_KEY=[YOUR_JWT_SECRET_KEY]" --set-env-vars="PINECONE_ENV=us-east1-aws" --set-env-vars="PINECONE_TEXT_INDEX=text" --set-env-vars="INDEX_HOST=https://test1-3gxkkbr.svc.aped-4627-b74a.pinecone.io" --set-env-vars="GCS_BUCKET_NAME=kalakaari-crafts" --set-env-vars="WEB3_RPC_URL=https://rpc-amoy.polygon.technology" --set-env-vars="CHAIN_ID=80002" --set-env-vars="ANCHOR_QUEUE_COLL=anchor_queue" --set-env-vars="QUEUE_FETCH_MAX=5" --set-env-vars="BATCH_LIMIT=5" --set-env-vars="POLL_INTERVAL=10"
```

After deployment, Cloud Run will return a **Service URL**, which serves as your public API endpoint.
