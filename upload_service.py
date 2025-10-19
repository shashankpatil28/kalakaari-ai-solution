import os
import cloudinary
import cloudinary.uploader
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# --- START OF THE FINAL FIX ---
# Hardcode the configuration values directly and separately.
# This is the most reliable method.
CLOUDINARY_CLOUD_NAME = "dq3x9vmgs"
CLOUDINARY_API_KEY = "567627968886437"
CLOUDINARY_API_SECRET = "VGQUcX3WZIRehE6yPIqV0ao2neY"
# --- END OF THE FINAL FIX ---

# Create the FastAPI app instance
app = FastAPI()

print(f"--- UPLOAD SERVICE: API Key loaded: {CLOUDINARY_API_KEY is not None} ---")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure the Cloudinary client using the individual, explicit values
cloudinary.config(
  cloud_name = CLOUDINARY_CLOUD_NAME,
  api_key = CLOUDINARY_API_KEY,
  api_secret = CLOUDINARY_API_SECRET,
  secure = True
)

@app.post("/upload-image/")
async def create_upload_file(file: UploadFile = File(...)):
    """
    This endpoint receives an image, uploads it to Cloudinary,
    and returns the secure URL.
    """
    try:
        print(f"--- UPLOAD SERVICE: Received file: {file.filename} ---")
        contents = await file.read()
        
        upload_result = cloudinary.uploader.upload(
            contents,
            folder="craft_id_artworks"
        )
        
        secure_url = upload_result.get("secure_url")
        if not secure_url:
            raise HTTPException(status_code=500, detail="Cloudinary did not return a URL")

        print(f"--- UPLOAD SERVICE: Success! URL: {secure_url} ---")
        return {"file_url": secure_url}

    except Exception as e:
        print(f"--- UPLOAD SERVICE: Error: {e} ---")
        raise HTTPException(status_code=500, detail=f"Image upload failed: {str(e)}")