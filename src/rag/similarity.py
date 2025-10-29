"""
Similarity calculations for RAG retrieval
"""
import numpy as np
from typing import List, Tuple, Dict
from sklearn.metrics.pairwise import cosine_similarity
from src.rag.embeddings import get_embedding  # pakai generator resmi
import logging

logger = logging.getLogger(__name__)


def cosine_similarity_single(vec1: List[float], vec2: List[float]) -> float:
    """
    Calculate cosine similarity between two embedding vectors (0-1)
    """
    vec1_array = np.array(vec1).reshape(1, -1)
    vec2_array = np.array(vec2).reshape(1, -1)
    similarity = cosine_similarity(vec1_array, vec2_array)[0][0]
    return float(similarity)


def batch_similarity(
    query_embedding: List[float],
    embeddings_list: List[List[float]]
) -> List[float]:
    """
    Fast cosine similarity for batch embeddings
    """
    query_array = np.array(query_embedding).reshape(1, -1)
    embeddings_array = np.array(embeddings_list)
    similarities = cosine_similarity(query_array, embeddings_array)[0]
    return similarities.tolist()


def find_similar_foods_fast(
    query_embedding: List[float],
    foods_data: List[Dict],
    top_k: int = 5,
    threshold: float = 0.3
) -> List[Dict]:
    """
    Optimized similarity search for food recommendations.
    Auto-generate embedding if missing.
    """
    if not foods_data:
        logger.warning("⚠️ No food data provided to similarity search.")
        return []

    embeddings = []
    valid_foods = []

    for food in foods_data:
        if "embedding" not in food or not food["embedding"]:
            food["embedding"] = get_embedding(food["name"])
        embeddings.append(food["embedding"])
        valid_foods.append(food)

    similarities = batch_similarity(query_embedding, embeddings)

    results = []
    for i, score in enumerate(similarities):
        if score >= threshold:
            food_copy = valid_foods[i].copy()
            food_copy["similarity_score"] = float(score)
            results.append(food_copy)

    results.sort(key=lambda x: x["similarity_score"], reverse=True)

    if not results:
        logger.info("ℹ️ No similar foods found above threshold.")
    return results[:top_k]
