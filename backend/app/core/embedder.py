"""Shared sentence-transformer embedder — loaded once at startup."""
from sentence_transformers import SentenceTransformer

embedder = SentenceTransformer("all-MiniLM-L6-v2")
