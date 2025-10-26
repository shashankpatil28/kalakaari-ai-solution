# ---- Builder Stage ----
# Use the full "bookworm" image to ensure all build dependencies 
# (like C++ compilers for torch) are present.
FROM python:3.10-bookworm as builder

# Set working directory
WORKDIR /code

# Create a virtual environment
ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Copy and install requirements into the venv
# This layer is cached as long as requirements.txt doesn't change
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


# ---- Final Stage ----
# Use the slim image for the final, small container
FROM python:3.10-slim

# Create a non-root user for security
RUN groupadd --gid 1001 appuser && \
    useradd --uid 1001 --gid 1001 -m -s /bin/bash appuser

# Set working directory
WORKDIR /code

# Copy the pre-built virtual environment from the builder stage
COPY --from=builder /opt/venv /opt/venv

# Copy the application code
# CRITICAL: We copy BOTH 'app' and 'chain' folders
COPY --chown=appuser:appuser ./app ./app
COPY --chown=appuser:appuser ./chain ./chain

# Set the non-root user
USER appuser

# Set the PATH to use the venv
ENV PATH="/opt/venv/bin:$PATH"

# Expose the port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]