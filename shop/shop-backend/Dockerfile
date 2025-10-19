# shop-backend/Dockerfile

# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set environment variables for Python
ENV PYTHONUNBUFFERED True
ENV PYTHONDONTWRITEBYTECODE True

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
# DO NOT COPY .env FILE!
COPY ./app /app/app

# Expose the port the app runs on
EXPOSE 8000

# Define the command to run the application
# Use 0.0.0.0 to listen on all interfaces
# Cloud Run sets the PORT env var, uvicorn respects it.
# We explicitly set --port 8000 so Nginx knows where to proxy internally.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

# Health check (Optional but recommended for Cloud Run)
# HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
#  CMD curl -f http://localhost:8000/ || exit 1