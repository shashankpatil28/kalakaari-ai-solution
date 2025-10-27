#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Start the chain batcher in the background
echo "Starting chain batcher in background..."
python -m chain.batcher &

# Start the Uvicorn web server in the foreground
# This is the main process that will keep the container alive
echo "Starting Uvicorn web server in foreground..."
uvicorn app.main:app --host 0.0.0.0 --port 8000