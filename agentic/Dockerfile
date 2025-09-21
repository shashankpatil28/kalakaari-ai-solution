FROM python:3.13-slim

# keep python from writing pyc files and enable unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN python -m pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Create writable runtime dirs and non-root user
RUN mkdir -p /data /tmp \
    && chmod 777 /data /tmp \
    && adduser --disabled-password --gecos "" myuser

# Copy project files and ensure the non-root user owns them
COPY . .
RUN chown -R myuser:myuser /app /data /tmp

# Switch to non-root user
USER myuser
ENV PATH="/home/myuser/.local/bin:$PATH"

# Default session DB (absolute path in /tmp, writable)
# note: sqlite absolute URI needs four slashes: sqlite:////tmp/sessions.db
ENV SESSION_SERVICE_URI="sqlite:////tmp/sessions.db"
ENV PORT=8080

EXPOSE 8080

# Run the app
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT}"]
