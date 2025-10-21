# master-ip/server/Dockerfile

# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /code

# Copy the dependency file to the container
COPY requirements.txt .

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy your application code from the local 'app' directory
# into a directory named 'app' inside the container
# The app will be at /code/app
COPY ./app ./app

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application using Uvicorn
# We tell Uvicorn to run the 'app' object from the 'app.main' module
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]