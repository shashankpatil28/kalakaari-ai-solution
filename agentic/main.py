import os
import uvicorn
from fastapi import FastAPI
from google.adk.cli.fast_api import get_fast_api_app
from pathlib import Path

# Get the directory where main.py is located
AGENT_DIR = os.path.dirname(os.path.abspath(__file__))
# Example allowed origins for CORS
ALLOWED_ORIGINS = ["*"]
# Set web=True to serve the ADK web interface
SERVE_WEB_INTERFACE = True

# Use env var if set, otherwise default to absolute /tmp path (writable in container)
SESSION_SERVICE_URI = os.environ.get("SESSION_SERVICE_URI") or "sqlite:////tmp/sessions.db"

# If it's a sqlite URI, ensure parent dir exists
if SESSION_SERVICE_URI.startswith("sqlite:"):
    # remove the leading scheme part to get filesystem path
    # note: "sqlite:////tmp/sessions.db" -> "/tmp/sessions.db"
    file_path = SESSION_SERVICE_URI.replace("sqlite:///", "")
    Path(file_path).parent.mkdir(parents=True, exist_ok=True)

print("[INFO] Using SESSION_SERVICE_URI:", SESSION_SERVICE_URI if "@" not in SESSION_SERVICE_URI else "(hidden)")

# Call the function to get the FastAPI app instance
app: FastAPI = get_fast_api_app(
    agents_dir=AGENT_DIR,
    session_service_uri=SESSION_SERVICE_URI,
    allow_origins=ALLOWED_ORIGINS,
    web=SERVE_WEB_INTERFACE,
)

if __name__ == "__main__":
    # Use the PORT environment variable provided by Cloud Run, defaulting to 8080
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))