"""
Retrieval-Augmented Generation (RAG) engine.
Menyediakan retrieval berbasis embedding untuk rekomendasi makanan & konteks user.
"""

from .retrieval_engine import RetrievalEngine
from .similarity import cosine_similarity
from .embeddings import EmbeddingGenerator

__all__ = ["RetrievalEngine", "cosine_similarity", "EmbeddingGenerator"]
