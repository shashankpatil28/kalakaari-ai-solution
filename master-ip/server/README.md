# Kalakaari AI - Master-IP Service (Backend)

This service is the backend server component for the Master-IP solution, designed to handle the creation and management of unique digital identifiers (`CraftID`) for artisanal products. It's built with FastAPI and uses MongoDB for data storage.

## 📝 Project Summary

(This section is intentionally left blank for you to fill in with the project's vision, goals, and high-level description.)

---

## 📁 Folder Structure

The server is organized as follows to separate concerns like routes, models, and database logic from the main application entry point.

```
master-ip/
└── server/
    ├── app/
    │   ├── routes/
    │   │   └── craftid.py
    │   ├── main.py
    │   ├── mongodb.py
    │   └── models.py
    ├── requirements.txt
    ├── .env
    ├── .gitignore
    └── README.md
```

---

## 🚀 Getting Started

You can set up the project for development either by running it directly on your local machine or by using Docker for a more isolated environment.

### Prerequisites

* Python 3.8+ and Pip
* [Docker](https://www.docker.com/get-started) and [Docker Compose](https://docs.docker.com/compose/install/) (for the Docker-based setup)
* A MongoDB instance (you can run one easily with Docker)

### 1. Local Development Setup

**Step 1: Clone the Repository**
```bash
git clone <your-repository-url>
cd kalakaari-ai-solution/master-ip/server
```

**Step 2: Create a Virtual Environment**
It's highly recommended to use a virtual environment to manage project dependencies.
```bash
# For macOS/Linux
python3 -m venv venv
source venv/bin/activate

# For Windows
python -m venv venv
.\venv\Scripts\activate
```

**Step 3: Install Dependencies**
```bash
pip install -r requirements.txt
```

**Step 4: Set Up Environment Variables**
Create a `.env` file in the `server/` directory by copying the example below. This file stores configuration details and secrets.

***File: `.env`***
```ini
# MongoDB Connection Details
MONGO_URI="mongodb://localhost:27017/"
DB_NAME="kalakaari_db"

# JWT Secret Key for signing private keys
SECRET_KEY="a_very_strong_and_secret_key_for_development"
```

**Step 5: Run a MongoDB Instance**
The easiest way to run a local MongoDB for development is with Docker:
```bash
docker run -d --name mongo-dev -p 27017:27017 mongo:latest
```

**Step 6: Run the FastAPI Application**
Use `uvicorn` to run the server. The `--reload` flag will automatically restart the server when you make changes to the code.
```bash
uvicorn app.main:app --reload
```
The server will now be running at `http://127.0.0.1:8000`.

### 2. Docker-based Setup

This method uses Docker Compose to build and run the FastAPI application and the MongoDB database in isolated containers.

**Step 1: Create the `Dockerfile`**
Create a file named `Dockerfile` (without any extension) in the `server/` directory with the content provided in the section below.

**Step 2: Create the `docker-compose.yml` file**
Create a file named `docker-compose.yml` in the `server/` directory.

```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - .:/app  # Mounts the current directory into the container for hot-reloading
    env_file:
      - ./.env
    environment:
      # Override MONGO_URI to use the Docker network service name 'mongo'
      - MONGO_URI=mongodb://mongo:27017/
    depends_on:
      - mongo

  mongo:
    image: mongo:latest
    ports:
      - "27017:27017"
    volumes:
      - mongo-data:/data/db

volumes:
  mongo-data:
```

**Step 3: Run with Docker Compose**
Make sure you have created the `.env` file as described in the local setup guide. Then, run the following command from the `server/` directory:

```bash
docker-compose up --build
```
This command will build the FastAPI image, pull the MongoDB image, and start both containers. The API will be available at `http://localhost:8000`.

---

## 🌐 API Endpoints

### Health Check

* **`GET /`**
    * **Description**: A simple endpoint to check if the service is running.
    * **Success Response (200)**:
        ```json
        { "message": "Prototype Master-IP backend is running!" }
        ```

### Admin

* **`POST /init-db`**
    * **Description**: An administrative endpoint to initialize the database. This primarily ensures the `counters` collection for the atomic sequencer is created. It's safe to call multiple times.
    * **Success Response (200)**:
        ```json
        { "status": "ok", "detail": "DB initialized or already ready." }
        ```

### CraftID Creation

* **`POST /create`**
    * **Description**: The primary endpoint for onboarding a new art piece and artisan, which generates a unique CraftID.
    * **Request Body**:
        ```json
        {
          "artisan": {
            "name": "Ramesh Kumar",
            "location": "Jaipur, Rajasthan",
            "contact_number": "9876543210",
            "email": "ramesh.k@example.com",
            "aadhaar_number": "123456789012"
          },
          "art": {
            "name": "Blue Pottery Vase - Royal Peacock",
            "description": "A handcrafted vase made with traditional blue pottery techniques, featuring a royal peacock design.",
            "photo": "data:image/jpeg;base64,..."
          }
        }
        ```
    * **Success Response (200)**: A detailed JSON object containing the newly created IDs and metadata.
    * **Error Responses**:
        * `409 Conflict`: If an art piece with a similar name already exists.
        * `502 Bad Gateway`: If the server cannot connect to the database.

---

## 🛠️ Architectural Notes

* **Asynchronous Processing**: The application uses **FastAPI** and **Motor** (an async driver for MongoDB), allowing it to handle I/O-bound operations (like database queries) efficiently without blocking.
* **Database Connection Management**: The `mongodb.py` module is designed to be resilient. The `ensure_initialized()` function lazily creates a database connection and includes retry logic to handle potential connection drops, which is particularly useful in serverless or containerized environments.
* **ID & Key Generation**:
    * **`public_id`**: A human-readable, sequential ID (`CID-00001`) generated using an atomic counter in MongoDB to prevent race conditions.
    * **`private_key`**: A **JWT (JSON Web Token)** that encodes the `public_id` and an expiration date. This acts as a portable and verifiable "private key" for the owner.
    * **`public_hash`**: A **SHA-256** hash of the core art details (name, description, photo). This creates a unique fingerprint of the art's data at the time of creation, which can be used to verify data integrity.
* **Configuration**: All sensitive data and environment-specific settings (database URI, secret keys) are managed through the `.env` file, which should not be committed to version control.