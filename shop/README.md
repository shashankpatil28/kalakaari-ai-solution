# 🛍️ Shop Service

## 🧩 Overview

> *(To be updated later)*

The **Shop Service** is a full-stack application consisting of two independent parts:

* **Backend:** FastAPI-based microservice for product and authentication management.
* **Frontend:** Angular-based client for user interaction and visualization.

Both can be developed locally or deployed separately on **Google Cloud Run** for scalability.

---

## ⚙️ Local Development

### 🖥️ Backend (FastAPI)

#### 1. Navigate to backend directory

```bash
cd shop-backend
```

#### 2. Create and activate a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
```

#### 3. Install dependencies

```bash
pip install -r requirements.txt
```

#### 4. Create a `.env` file

```bash
MONGO_URI=<your_mongodb_connection_string>
DB_NAME=kalaakari_shop_db
SECRET_KEY=<your_secret_key>
```

#### 5. Run the server

```bash
uvicorn app.main:app --reload --port 8000
```

Backend is now available at: **[http://localhost:8000](http://localhost:8000)**

---

### 🌐 Frontend (Angular)

#### 1. Navigate to frontend directory

```bash
cd shop-frontend
```

#### 2. Install dependencies

```bash
npm install
```

#### 3. Run development server

```bash
npm start
```

Frontend is now available at: **[http://localhost:4200](http://localhost:4200)**

---

## ☁️ Deployment (Google Cloud Run)

Both services are deployed **independently** on **GCP Cloud Run**, with images stored in **Artifact Registry**.

### 🔧 Configuration Summary

| Component | Service Name             | Artifact Repo     | Image Tag         | Region            |
| --------- | ------------------------ | ----------------- | ----------------- | ----------------- |
| Backend   | `kalakaari-shop-backend` | `shop-containers` | `backend-latest`  | `asia-southeast1` |
| Frontend  | `kalakaari-service-main` | `shop-containers` | `frontend-latest` | `asia-southeast1` |

---

### 🚀 Deploy Backend

#### Build and Push Image

```bash
PROJECT_ID="kalakaari-ai"
REGION="asia-southeast1"
REPO="shop-containers"
SERVICE_BACKEND="kalakaari-shop-backend"

# Build
docker build -t ${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO}/${SERVICE_BACKEND}:backend-latest ./shop-backend

# Push
docker push ${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO}/${SERVICE_BACKEND}:backend-latest
```

#### Deploy to Cloud Run

```bash
gcloud run deploy ${SERVICE_BACKEND} \
  --image=${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO}/${SERVICE_BACKEND}:backend-latest \
  --region=${REGION} \
  --project=${PROJECT_ID} \
  --allow-unauthenticated \
  --cpu=1 \
  --memory=512Mi \
  --port=8000 \
  --set-env-vars=MONGO_URI='<your_mongo_uri>' \
  --set-env-vars=DB_NAME='kalaakari_shop_db' \
  --set-env-vars=SECRET_KEY='<your_secret_key>'
```

Backend will be available at the generated Cloud Run URL.

---

### 🌍 Deploy Frontend

#### Build and Push Image

```bash
PROJECT_ID="kalakaari-ai"
REGION="asia-southeast1"
REPO="shop-containers"
SERVICE_FRONTEND="kalakaari-service-main"

# Build
docker build -t ${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO}/${SERVICE_FRONTEND}:frontend-latest ./shop-frontend

# Push
docker push ${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO}/${SERVICE_FRONTEND}:frontend-latest
```

#### Deploy to Cloud Run

```bash
gcloud run deploy ${SERVICE_FRONTEND} \
  --image=${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO}/${SERVICE_FRONTEND}:frontend-latest \
  --region=${REGION} \
  --project=${PROJECT_ID} \
  --allow-unauthenticated \
  --cpu=1 \
  --memory=512Mi \
  --port=4200
```

Frontend will be accessible at the generated Cloud Run URL.

---

## 📜 Notes

* Each part (backend & frontend) can be updated, built, and deployed **independently**.
* Ensure `shop-containers` Artifact Registry exists in `asia-southeast1` before pushing.
* If MongoDB access is restricted, whitelist Cloud Run egress IP or switch to a public MongoDB Atlas endpoint.
* For production, store secrets using **Secret Manager** instead of inline env vars.
