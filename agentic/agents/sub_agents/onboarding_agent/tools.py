import os
import cloudinary
import cloudinary.uploader
from dotenv import load_dotenv

# This is the single, correct, and verified way to import the ADK library
# to access its services like 'files'.
import google.adk as adk

# Load environment variables
load_dotenv()

# Configure the Cloudinary client
cloudinary.config(cloud_url=os.getenv("CLOUDINARY_URL"))

def upload_image_to_cloudinary(image_uri: str) -> str:
    """
    This tool takes an image's file URI (a string provided by the system when a
    user uploads a file), retrieves the image data using the ADK file service,
    uploads it to Cloudinary, and returns its secure, downloadable URL.

    Args:
        image_uri (str): The file URI of the uploaded image (e.g., 'file://_p0_...')

    Returns:
        str: The secure URL of the uploaded image, or an error message if it fails.
    """
    if not os.getenv("CLOUDINARY_URL"):
        return "Error: CLOUDINARY_URL environment variable is not set."
    
    try:
        print(f"--- TOOL: Received image URI: {image_uri} ---")
        
        # Access the files service through the 'adk' module to get the content.
        # This is the correct and working method.
        image_data = adk.files.get_content(image_uri)

        print("--- TOOL: Attempting to upload image to Cloudinary... ---")
        
        # Upload the image bytes to a specific folder
        upload_result = cloudinary.uploader.upload(
            image_data,
            folder="craft_id_artworks"
        )
        
        # Safely get the secure URL from the response
        secure_url = upload_result.get("secure_url")
        
        if secure_url:
            print(f"--- TOOL: Upload successful. URL: {secure_url} ---")
            return secure_url
        else:
            print("--- TOOL: Upload failed. No secure_url in response. ---")
            return "Error: Could not retrieve URL from Cloudinary response."

    except Exception as e:
        print(f"--- TOOL: Cloudinary upload failed: {e} ---")
        return f"Error: Image upload failed. Details: {str(e)}"