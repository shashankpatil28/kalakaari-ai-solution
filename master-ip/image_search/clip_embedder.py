# /master-ip/image_search/clip_embedder.py
from PIL import Image
import torch
from transformers import CLIPProcessor, CLIPModel
import numpy as np

MODEL_NAME = "openai/clip-vit-base-patch32"  # 512-dim

class ClipEmbedder:
    def __init__(self, device=None):
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.model = CLIPModel.from_pretrained(MODEL_NAME).to(self.device)
        self.proc = CLIPProcessor.from_pretrained(MODEL_NAME)

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
