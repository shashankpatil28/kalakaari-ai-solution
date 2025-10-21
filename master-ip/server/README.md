# Master-IP Backend Service

> (A brief summary of the project will be added here.)

This document provides all the necessary instructions to set up, run, and deploy the Master-IP backend service. The service is built with FastAPI and provides endpoints for CraftID management and advanced vector-based search for images and metadata.

---

## Table of Contents

1. [Local Development Setup](#local-development-setup)

   * [Prerequisites](#prerequisites)
   * [Installation](#installation)
   * [Environment Variables](#environment-variables)
   * [Running the Application](#running-the-application)
2. [Deployment to Google Cloud Run](#deployment-to-google-cloud-run)

   * [Deployment Prerequisites](#deployment-prerequisites)
   * [Step-by-Step Deployment Guide](#step-by-step-deployment-guide)

---

## Local Development Setup

Follow these instructions to get the application running on your local machine for development and testing.

### Prerequisites

Ensure you have the following software installed:

* **Python 3.10+**
* **Pip** (Python Package Installer)
* **Git**

### Installation

1. **Clone the repository:**

   ```bash
   git clone <your-repository-url>
   cd master-ip/server
   ```

2. **Create and activate a virtual environment:**

   * **macOS / Linux:**

     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```
   * **Windows (PowerShell):**

     ```bash
     python -m venv venv
     .\venv\Scripts\Activate.ps1
     ```

3. **Install the required dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

### Environment Variables

The application requires several environment variables to connect to external services.

1. Create a file named `.env` in the `master-ip/server/` directory.
2. Copy the content below into the `.env` file and replace the placeholder values with your actual credentials.

```env
# .env

# --- MongoDB ---
# Your database connection string.
# Get from: [https://www.mongodb.com/cloud/atlas](https://www.mongodb.com/cloud/atlas)
MONGO_URI="mongodb+srv://<user>:<password>@<cluster-url>/..."
DB_NAME="masterip_db"

# --- JWT ---
# A strong, random secret key for signing tokens.
# Generate one with: python -c 'import secrets; print(secrets.token_hex(32))'
SECRET_KEY="your_super_strong_random_secret_key"

# --- Pinecone ---
# API Key and environment for your Pinecone project.
# Get from: [https://app.pinecone.io/](https://app.pinecone.io/)
PINECONE_API_KEY="your_pinecone_api_key"
PINECONE_ENV="your_pinecone_environment_region" # e.g., "gcp-starter"

# Pinecone Index Hosts (Specific to your indexes)
# Find this on the Pinecone dashboard for each index.
INDEX_HOST="your_image_index_host.svc.pinecone.io" # For image search
PINECONE_TEXT_INDEX="text" # The name of your text search index
```

### Running the Application

Once the dependencies are installed and the `.env` file is configured, run the development server:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

`--reload` enables auto-reloading, so the server will restart after you change a file.

The API will be available at [http://localhost:8000](http://localhost:8000). You can access the auto-generated documentation at [http://localhost:8000/docs](http://localhost:8000/docs).

---

## Deployment to Google Cloud Run

This guide details how to deploy the service as a containerized application on Google Cloud Run.

### Deployment Prerequisites

* **Google Cloud SDK (gcloud CLI)** installed and configured. ([Install Guide](https://cloud.google.com/sdk/docs/install))
* **Docker** installed and running on your local machine. ([Install Guide](https://docs.docker.com/get-docker/))
* You must be authenticated with GCP:

  ```bash
  gcloud auth login
  ```

### Step-by-Step Deployment Guide

All commands should be run from the `master-ip/server/` directory.

#### 1. Configure gcloud CLI: Set your project and default region.

```bash
gcloud config set project kalakaari-ai
gcloud config set compute/region asia-southeast1
```

#### 2. Enable Required APIs: This allows Cloud Run and Artifact Registry to function.

```bash
gcloud services enable artifactregistry.googleapis.com run.googleapis.com
```

#### 3. Create an Artifact Registry Repository: This private repository will store your Docker images.

```bash
gcloud artifacts repositories create master-ip-containers \
    --repository-format=docker \
    --location=asia-southeast1 \
    --description="Repository for master-ip-service images"
```

#### 4. Authenticate Docker with GCP: This command configures your local Docker client to push to your new repository.

```bash
gcloud auth configure-docker asia-southeast1-docker.pkg.dev
```

#### 5. Build, Tag, and Push the Docker Image: This sequence builds your image, tags it correctly for your repository, and pushes it.

```bash
# Define the full image name
export IMAGE_NAME="asia-southeast1-docker.pkg.dev/kalakaari-ai/master-ip-containers/backend-latest"

# Build the image
docker build -t $IMAGE_NAME .

# Push the image
docker push $IMAGE_NAME
```

#### 6. Deploy to Cloud Run: This command deploys your container image as a serverless service.

⚠️ **Important: Set Environment Variables**
You must provide all secrets from your `.env` file directly to the Cloud Run service during deployment.

```bash
gcloud run deploy master-ip-service \
    --image=$IMAGE_NAME \
    --platform=managed \
    --region=asia-southeast1 \
    --port=8000 \
    --allow-unauthenticated \
    --set-env-vars=^::^ \
MONGO_URI="YOUR_MONGO_URI_HERE":: \
DB_NAME="masterip_db":: \
SECRET_KEY="YOUR_JWT_SECRET_HERE":: \
PINECONE_API_KEY="YOUR_PINECONE_API_KEY":: \
INDEX_HOST="YOUR_PINECONE_IMAGE_INDEX_HOST":: \
PINECONE_ENV="YOUR_PINECONE_ENV_REGION":: \
PINECONE_TEXT_INDEX="text"
```

`--allow-unauthenticated` makes the service publicly accessible. Remove this flag if you intend to secure it with IAM.

After the command completes, **gcloud** will provide you with a **Service URL**. This is the public endpoint for your deployed API.
