# agentic/agents/sub_agents/ip_agent/tools.py

import os
import base64
import io
import faiss
import numpy as np
from PIL import Image

from google.adk.decorators import tool


from transformers import CLIPProcessor, CLIPModel
import torch

# --- CONFIGURATION ---
# Define the Hugging Face model we'll use for embeddings
MODEL_NAME = "openai/clip-vit-base-patch32"
# Define where the local vector database file will be stored
FAISS_INDEX_FILE = "artwork_index.faiss"
# The number of dimensions for the CLIP model's embeddings
EMBEDDING_DIM = 512
# Similarity threshold: if a new image is >95% similar to an existing one, it's a duplicate.
SIMILARITY_THRESHOLD = 0.95

# --- GLOBAL SETUP (Load model and index once) ---
# Load the pre-trained CLIP model and its processor from Hugging Face
print(f"Loading Hugging Face model: {MODEL_NAME}...")
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
MODEL = CLIPModel.from_pretrained(MODEL_NAME).to(DEVICE)
PROCESSOR = CLIPProcessor.from_pretrained(MODEL_NAME)
print("Model loaded successfully.")

# Load the FAISS index from the file if it exists, otherwise create a new one
if os.path.exists(FAISS_INDEX_FILE):
    print(f"Loading existing FAISS index from {FAISS_INDEX_FILE}...")
    faiss_index = faiss.read_index(FAISS_INDEX_FILE)
    print("FAISS index loaded.")
else:
    print("No FAISS index found, creating a new one.")
    # Using IndexFlatIP for Cosine Similarity after normalization
    faiss_index = faiss.IndexFlatIP(EMBEDDING_DIM)

def get_image_embedding(image: Image.Image) -> np.ndarray:
    """
    Generates a vector embedding from a PIL image using the loaded CLIP model.
    """
    with torch.no_grad():
        inputs = PROCESSOR(images=image, return_tensors="pt", padding=True).to(DEVICE)
        image_features = MODEL.get_image_features(**inputs)
    
    # Normalize the embedding for cosine similarity search in FAISS
    embedding = image_features.cpu().numpy()
    faiss.normalize_L2(embedding)
    return embedding

@tool
def check_artwork_uniqueness(image_base64: str) -> dict:
    """
    Checks if an artwork is unique by creating an embedding using a Hugging Face
    CLIP model and searching for similar items in a local FAISS vector index.
    If the image is unique, its embedding is added to the index.

    Args:
        image_base64: The base64 encoded string of the artwork image.
    """
    try:
        # 1. Decode the image and get its embedding
        image_bytes = base64.b64decode(image_base64)
        image = Image.open(io.BytesIO(image_bytes))
        new_embedding = get_image_embedding(image)

        # 2. Search the FAISS index for the most similar image
        if faiss_index.ntotal == 0:
            print("Index is empty. This is the first artwork.")
            is_unique = True
        else:
            # Search for the 1 nearest neighbor
            distances, indices = faiss_index.search(new_embedding, 1)
            similarity_score = distances[0][0]
            print(f"Nearest neighbor found with similarity score: {similarity_score:.4f}")

            if similarity_score > SIMILARITY_THRESHOLD:
                is_unique = False
            else:
                is_unique = True
        
        # 3. Handle the result
        if is_unique:
            # If the artwork is unique, add its embedding to the index for future checks
            print("Artwork is unique. Adding to FAISS index.")
            faiss_index.add(new_embedding)
            # Save the updated index back to the file
            faiss.write_index(faiss_index, FAISS_INDEX_FILE)
            print("FAISS index saved.")
            return {"is_unique": True}
        else:
            # If a duplicate is found, do not add it to the index
            print("Duplicate artwork found.")
            return {
                "is_unique": False,
                "message": f"A highly similar artwork was found with {similarity_score * 100:.2f}% similarity."
            }

    except Exception as e:
        print(f"An error occurred in the tool: {e}")
        return {
            "is_unique": False,
            "message": "An unexpected technical error occurred while checking the artwork."
        }