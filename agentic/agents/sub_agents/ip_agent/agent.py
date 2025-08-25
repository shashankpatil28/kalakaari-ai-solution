import os
import json
import base64
import io

from google.adk.agents import Agent

from .prompt import IP_PROMPT
from .tools import ip_service_tool # <-- Import the new tool

from dotenv import load_dotenv

import requests
import json

# import faiss
# import numpy as np
# from PIL import Image
# from transformers import CLIPProcessor, CLIPModel
# import torch

load_dotenv()

# # --- GLOBAL VARIABLES ---
# MODEL = None
# PROCESSOR = None
# FAISS_INDEX = None
# DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
# MODEL_NAME = "openai/clip-vit-base-patch32"

# # Local FAISS index file + embedding settings
# FAISS_INDEX_FILE = "artwork_index.faiss"
# EMBEDDING_DIM = 512
# SIMILARITY_THRESHOLD = 0.95  # 95% similarity cutoff


# def load_model():
#     """Lazy load CLIP model + processor."""
#     global MODEL, PROCESSOR
#     if MODEL is None or PROCESSOR is None:
#         print(f"[IP_AGENT] Loading Hugging Face CLIP model: {MODEL_NAME}...")
#         MODEL = CLIPModel.from_pretrained(MODEL_NAME).to(DEVICE)
#         PROCESSOR = CLIPProcessor.from_pretrained(MODEL_NAME)
#         print("[IP_AGENT] Model loaded successfully.")


# def load_faiss():
#     """Lazy load or create FAISS index."""
#     global FAISS_INDEX
#     if FAISS_INDEX is None:
#         if os.path.exists(FAISS_INDEX_FILE):
#             print(f"[IP_AGENT] Loading existing FAISS index from {FAISS_INDEX_FILE}...")
#             FAISS_INDEX = faiss.read_index(FAISS_INDEX_FILE)
#         else:
#             print("[IP_AGENT] No FAISS index found. Creating a new one...")
#             FAISS_INDEX = faiss.IndexFlatIP(EMBEDDING_DIM)


# def get_image_embedding(image: Image.Image) -> np.ndarray:
#     """Generate normalized CLIP embedding for an image."""
#     load_model()  # ensure model is loaded
#     with torch.no_grad():
#         inputs = PROCESSOR(images=image, return_tensors="pt").to(DEVICE)
#         image_features = MODEL.get_image_features(**inputs)
#     embedding = image_features.cpu().numpy()
#     faiss.normalize_L2(embedding)
#     return embedding


# def check_artwork_uniqueness(artisan_data_json: str) -> str:
#     """
#     Takes artisan JSON, extracts Base64 image,
#     embeds with CLIP, and checks against FAISS for duplicates.
#     """
#     try:
#         # ensure FAISS is ready
#         load_faiss()

#         # parse artisan JSON
#         data = json.loads(artisan_data_json)
#         image_base64 = data["product"][0]["media"][0]

#         # handle "data:image/png;base64," prefix
#         if "," in image_base64:
#             _, encoded_data = image_base64.split(",", 1)
#         else:
#             encoded_data = image_base64

#         encoded_data += "=" * (-len(encoded_data) % 4)  # fix padding
#         image_bytes = base64.b64decode(encoded_data)
#         image = Image.open(io.BytesIO(image_bytes))

#         # get embedding
#         new_embedding = get_image_embedding(image)

#         # similarity search
#         if FAISS_INDEX.ntotal == 0:
#             similarity_score = 0.0
#         else:
#             distances, _ = FAISS_INDEX.search(new_embedding, 1)
#             similarity_score = distances[0][0]

#         # decision logic
#         if similarity_score > SIMILARITY_THRESHOLD:
#             result_message = (
#                 f"DUPLICATE: A very similar artwork already exists "
#                 f"({similarity_score * 100:.2f}% similarity). "
#                 "IP registration cannot proceed."
#             )
#         else:
#             FAISS_INDEX.add(new_embedding)
#             faiss.write_index(FAISS_INDEX, FAISS_INDEX_FILE)
#             result_message = (
#                 "UNIQUE: No similar artwork was found. "
#                 "The IP can be registered, and this artwork’s fingerprint has been saved."
#             )

#         print(f"[IP_AGENT] Check complete → {result_message}")
#         return result_message

#     except Exception as e:
#         error_message = f"[IP_AGENT] Error during IP check: {e}"
#         print(error_message)
#         return error_message

def call_master_ip_service(onboarding_data: str) -> dict:
    """
    Makes an API call to the master IP backend service to submit the artisan's data.

    Args:
        onboarding_data: The complete JSON data packet as a string.

    Returns:
        A dictionary with a 'status' key ('success' or 'error') and a 'message'
        key containing either a success confirmation or an error description.
    """
    try:
        # The onboarding_data is a string, so we need to parse it to a Python dictionary
        data_payload = json.loads(onboarding_data)

        # Define the API endpoint
        url = "http://localhost:8001/create"

        # Make the POST request to the backend service
        response = requests.post(url, json=data_payload, timeout=30)
        response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)

        # Check for a successful response (e.g., 200 OK, 201 Created)
        if response.status_code in [200, 201]:
            # Assuming the master service returns a success message
            return {
                "status": "success",
                "message": "Your IP data has been successfully submitted for verification. We will notify you once the process is complete.",
                "response": response,
            }
        else:
            return {
                "status": "error",
                "message": f"An unexpected error occurred with the service. Status code: {response.status_code}"
            }

    except requests.exceptions.RequestException as e:
        # Handle network-related errors (e.g., connection refused, timeout)
        return {
            "status": "error",
            "message": f"We are currently unable to connect to the IP service. Please try again later. Error: {e}"
        }
    except json.JSONDecodeError:
        # Handle cases where the input data is not valid JSON
        return {
            "status": "error",
            "message": "The data format received was invalid. Please restart the process."
        }
    except Exception as e:
        # Handle any other unexpected errors
        return {
            "status": "error",
            "message": f"An unexpected error occurred during the submission process. Error: {e}"
        }

# --- Agent Definition ---
ip_agent = Agent(
    name="ip_agent",
    model=os.getenv("MODEL_NAME"),
    description="Verifies artwork uniqueness using CLIP embeddings + FAISS similarity search.",
    instruction=IP_PROMPT,
    tools=[call_master_ip_service] # <-- Register the tool with the agent
)
