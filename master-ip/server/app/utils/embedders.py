# app/utils/embedders.py
from PIL import Image
import torch
from transformers import CLIPProcessor, CLIPModel
import numpy as np
from sentence_transformers import SentenceTransformer

# Import config from constants
from app.constants import CLIP_MODEL_NAME, TEXT_MODEL_NAME

# --- CLIP Image Embedder ---

class ClipEmbedder:
    def __init__(self, device=None):
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.model = CLIPModel.from_pretrained(CLIP_MODEL_NAME).to(self.device)
        self.proc = CLIPProcessor.from_pretrained(CLIP_MODEL_NAME)

    def embed_pil(self, pil_image):
        inputs = self.proc(images=pil_image, return_tensors="pt").to(self.device)
        with torch.no_grad():
            feats = self.model.get_image_features(**inputs)    # (1, dim)
        feats = feats / feats.norm(p=2, dim=-1, keepdim=True)
        vec = feats.cpu().numpy()[0]
        # ensure python list for Pinecone
        return vec.astype(float).tolist()

    def embed_paths(self, pil_paths):
        # pil_paths: list of PIL.Image instances or file paths; returns list of vectors
        vecs = []
        for p in pil_paths:
            if isinstance(p, str):
                img = Image.open(p).convert("RGB")
            else:
                img = p
            vecs.append(self.embed_pil(img))
        return vecs

# --- SentenceTransformer Text Embedder ---

_model = None

def get_model(name: str = TEXT_MODEL_NAME):
    global _model
    if _model is None:
        _model = SentenceTransformer(name)
    return _model

def embed_text(text: str):
    m = get_model()
    vec = m.encode([text], show_progress_bar=False)[0]
    norm = np.linalg.norm(vec)
    if norm == 0:
        return vec.astype("float32")
    return (vec / norm).astype("float32")