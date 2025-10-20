# Use a slim, recent Python
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Minimal system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
  && rm -rf /var/lib/apt/lists/*

# Install Python deps first for caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code (must include the 'app' package folder)
COPY . .

# Default to 8000; Cloud Run will override with PORT=8000 when we deploy with --port=8000
ENV PORT=8000

# Expose for local runs (Cloud Run ignores EXPOSE)
EXPOSE 8000

# IMPORTANT: your app is app.main:app (NOT main:app)
CMD exec uvicorn app.main:app --host 0.0.0.0 --port $PORT
