# ---- Builder Stage ----
FROM python:3.10-bookworm as builder

WORKDIR /code

ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ---- Final Stage ----
FROM python:3.10-slim
RUN groupadd --gid 1001 appuser && \
    useradd --uid 1001 --gid 1001 -m -s /bin/bash appuser

WORKDIR /code

# Copy the pre-built virtual environment
COPY --from=builder /opt/venv /opt/venv

# Copy the application code
COPY --chown=appuser:appuser ./app ./app
COPY --chown=appuser:appuser ./chain ./chain

# --- NEW STEPS ---
# 1. Copy the new entrypoint script
COPY --chown=appuser:appuser ./entrypoint.sh .
# 2. Make it executable
RUN chmod +x ./entrypoint.sh
# --- END NEW STEPS ---

USER appuser
ENV PATH="/opt/venv/bin:$PATH"
EXPOSE 8000

# Use the entrypoint script as the main command
CMD ["./entrypoint.sh"]