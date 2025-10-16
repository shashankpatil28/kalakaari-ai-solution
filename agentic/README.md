# Agentic Service

> *Short summary placeholder: explain what the Agentic service does, e.g., an AI agent orchestration microservice built on Google ADK and FastAPI.*

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

### 4. Create a `.env` file

Create a `.env` file inside `agentic/` with the following variables:

```bash
SESSION_SERVICE_URI=<your_neon_db_url>
DATABASE_URL=<your_neon_db_url>
MODEL_NAME=gemini-2.0-flash
GOOGLE_API_KEY=<your_google_api_key>
GOOGLE_GENAI_USE_VERTEXAI=FALSE
```

#### 🔑 Where to get these values:

* **Neon DB URLs** → from [https://neon.tech](https://neon.tech) (create a free Postgres instance)
* **Google API Key** → from [Google AI Studio](https://aistudio.google.com/app/apikey)

### 5. Run locally for development

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8080
```

Then visit:

```
http://localhost:8080
```

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

Verify by visiting:

```
http://localhost:8080
```

---

## ☁️ Deploy to Google Cloud Run

### 1. Authenticate and set up project

```bash
gcloud auth login
gcloud config set project <YOUR_PROJECT_ID>
```

### 2. Build and push image to Artifact Registry

```bash
gcloud builds submit --tag gcr.io/<YOUR_PROJECT_ID>/agentic-service
```

### 3. Deploy to Cloud Run

```bash
gcloud run deploy agentic-service \
  --image gcr.io/<YOUR_PROJECT_ID>/agentic-service \
  --platform managed \
  --region asia-south1 \
  --allow-unauthenticated \
  --set-env-vars SESSION_SERVICE_URI=<your_neon_db_url>,DATABASE_URL=<your_neon_db_url>,MODEL_NAME=gemini-2.0-flash,GOOGLE_API_KEY=<your_google_api_key>,GOOGLE_GENAI_USE_VERTEXAI=FALSE
```

### 4. Get your service URL

After deployment, Cloud Run will print the public URL:

```
Service [agentic-service] revision [agentic-service-xxxxx] has been deployed and is serving traffic at:
https://agentic-service-xxxx-uc.a.run.app
```

Visit that URL to verify your deployment.

---

## 🧪 Testing

Run tests (if available) using:

```bash
pytest
```

---

## 📦 Environment Recap

| Variable                    | Description                                |
| --------------------------- | ------------------------------------------ |
| `SESSION_SERVICE_URI`       | Neon DB or SQLite session store            |
| `DATABASE_URL`              | Primary Postgres database (Neon)           |
| `MODEL_NAME`                | Gemini model variant used                  |
| `GOOGLE_API_KEY`            | API key from Google AI Studio              |
| `GOOGLE_GENAI_USE_VERTEXAI` | Set to `FALSE` when using API key directly |

---

## ✅ Summary

* Local dev runs with FastAPI + uvicorn.
* Dockerfile already handles user permissions and lightweight deployment.
* Cloud Run deployment is one command after pushing the image.
