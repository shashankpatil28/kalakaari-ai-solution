# text_embedder.py
from sentence_transformers import SentenceTransformer
import numpy as np

_model = None

def get_model(name: str = "sentence-transformers/all-MiniLM-L12-v2"):  # <-- changed here
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
