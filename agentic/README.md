# Agentic Service

> *AI agent orchestration microservice built on Google ADK and FastAPI.*

---

## 🧩 Project Structure

```
agentic/
├── __init__.py
├── .gitignore
├── Dockerfile
├── main.py
├── requirements.txt
├── agents/
│   ├── __init__.py
│   ├── agent.py
│   ├── prompt.py
│   └── sub_agents/
│       ├── __init__.py
│       ├── onboarding_agent/
│       │   ├── agent.py
│       │   └── prompt.py
│       └── ip_agent/
│           ├── agent.py
│           └── prompt.py
```

---

## ⚙️ Local Development Setup

### 1. Clone the repository

```bash
git clone https://github.com/<your-org>/kalakaari-ai-solution.git
cd kalakaari-ai-solution/agentic
```

### 2. Create and activate virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 3. Upgrade pip and install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Create a .env file

Create a `.env` file inside `agentic/` with the following variables:

```bash
SESSION_SERVICE_URI=<your_neon_db_url>
DATABASE_URL=<your_neon_db_url>
MODEL_NAME=gemini-2.0-flash
GOOGLE_API_KEY=<your_google_api_key>
GOOGLE_GENAI_USE_VERTEXAI=FALSE
```

**Where to get these values:**

* Neon DB URLs → from [https://neon.tech](https://neon.tech)
* Google API Key → from Google AI Studio

### 5. Run locally for development

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8080
```

Visit: [http://localhost:8080](http://localhost:8080)

---

## 🐳 Docker Setup (Local Build & Run)

### 1. Build the Docker image

```bash
docker build -t agentic-service .
```

### 2. Run the container

```bash
docker run -d \
  -p 8080:8080 \
  --env-file .env \
  agentic-service
```

Visit: [http://localhost:8080](http://localhost:8080)

---

## ⚠️ Important Prerequisites for Deployment

Before deploying to **Google Cloud Run**, update the following:

### 1. Update Dockerfile for Port 8000

Google Cloud Run sends traffic to the specified port. Modify your Dockerfile:

**Change this:**

```Dockerfile
ENV PORT=8080
EXPOSE 8080
```

**To this:**

```Dockerfile
ENV PORT=8000
EXPOSE 8000
```

`uvicorn main:app --host 0.0.0.0 --port ${PORT}` will automatically use it.

### 2. Update requirements.txt for PostgreSQL

Add the following line to ensure the Neon DB connection works:

```
psycopg2-binary
```

---

## ☁️ Deploy to Google Cloud Run

### 1. Authenticate and Configure Project

```bash
gcloud auth login
gcloud config set project kalakaari-ai
gcloud services enable \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com \
  run.googleapis.com
```

### 2. Create Artifact Registry Repository

```bash
gcloud artifacts repositories create agentic-containers \
  --repository-format=docker \
  --location=asia-southeast1 \
  --description="Container images for agentic services"
```

### 3. Build and Push Image

```bash
gcloud builds submit --tag \
  asia-southeast1-docker.pkg.dev/kalakaari-ai/agentic-containers/agentic-service:latest
```

### 4. Deploy to Cloud Run

```bash
gcloud run deploy agentic-service \
  --image "asia-southeast1-docker.pkg.dev/kalakaari-ai/agentic-containers/agentic-service:latest" \
  --platform managed \
  --region "asia-southeast1" \
  --port 8000 \
  --allow-unauthenticated \
  --set-env-vars=SESSION_SERVICE_URI=<YOUR_NEON_DB_URL>,DATABASE_URL=<YOUR_NEON_DB_URL>,MODEL_NAME=gemini-2.0-flash,GOOGLE_API_KEY=<YOUR_GOOGLE_API_KEY>,GOOGLE_GENAI_USE_VERTEXAI=FALSE
```

**Tip for complex URLs:**

If your environment variables contain special characters, use a different separator:

```bash
gcloud run deploy agentic-service \
  --image "asia-southeast1-docker.pkg.dev/kalakaari-ai/agentic-containers/agentic-service:latest" \
  --platform managed \
  --region "asia-southeast1" \
  --port 8000 \
  --allow-unauthenticated \
  --set-env-vars="^##^SESSION_SERVICE_URI=<YOUR_NEON_DB_URL>##DATABASE_URL=<YOUR_NEON_DB_URL>##MODEL_NAME=gemini-2.0-flash##GOOGLE_API_KEY=<YOUR_GOOGLE_API_KEY>##GOOGLE_GENAI_USE_VERTEXAI=FALSE"
```

### 5. Get your service URL

After deployment, Cloud Run will print a public URL:

```
Service [agentic-service] revision [agentic-service-xxxxx] has been deployed and is serving traffic at:
https://agentic-service-xxxx-as.a.run.app
```

Visit your deployed app to verify.

---

## 🧪 Testing

```bash
pytest
```

---

## 📦 Environment Recap

| Variable                  | Description                              |
| ------------------------- | ---------------------------------------- |
| SESSION_SERVICE_URI       | Neon DB or SQLite session store          |
| DATABASE_URL              | Primary Postgres database (Neon)         |
| MODEL_NAME                | Gemini model variant used                |
| GOOGLE_API_KEY            | API key from Google AI Studio            |
| GOOGLE_GENAI_USE_VERTEXAI | Set to FALSE when using API key directly |

---

✅ **Summary**

* Local dev runs with **FastAPI + Uvicorn**.
* Dockerfile configured for **port 8000** and includes **psycopg2-binary**.
* Cloud Run deployment uses **gcloud builds submit
