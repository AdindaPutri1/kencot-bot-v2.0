"""
Similarity calculations for RAG retrieval
"""
import numpy as np
from typing import List, Tuple, Dict
from sklearn.metrics.pairwise import cosine_similarity

def calculate_cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """
    Calculate cosine similarity between two vectors
    
    Args:
        vec1: First embedding vector
        vec2: Second embedding vector
        
    Returns:
        Similarity score (0-1)
    """
    vec1_array = np.array(vec1).reshape(1, -1)
    vec2_array = np.array(vec2).reshape(1, -1)
    
    similarity = cosine_similarity(vec1_array, vec2_array)[0][0]
    return float(similarity)

def find_most_similar(
    query_embedding: List[float],
    embeddings_db: List[Dict],
    top_k: int = 5,
    threshold: float = 0.0
) -> List[Tuple[Dict, float]]:
    """
    Find most similar items from database
    
    Args:
        query_embedding: Query vector
        embeddings_db: List of dicts with 'embedding' key
        top_k: Number of results to return
        threshold: Minimum similarity score
        
    Returns:
        List of tuples (item, similarity_score) sorted by score
    """
    results = []
    
    for item in embeddings_db:
        if "embedding" not in item:
            continue
        
        similarity = calculate_cosine_similarity(
            query_embedding,
            item["embedding"]
        )
        
        if similarity >= threshold:
            results.append((item, similarity))
    
    # Sort by similarity (descending)
    results.sort(key=lambda x: x[1], reverse=True)
    
    return results[:top_k]

def batch_similarity(
    query_embedding: List[float],
    embeddings_list: List[List[float]]
) -> List[float]:
    """
    Calculate similarity between query and multiple embeddings (faster)
    
    Args:
        query_embedding: Query vector
        embeddings_list: List of embedding vectors
        
    Returns:
        List of similarity scores
    """
    query_array = np.array(query_embedding).reshape(1, -1)
    embeddings_array = np.array(embeddings_list)
    
    similarities = cosine_similarity(query_array, embeddings_array)[0]
    
    return similarities.tolist()

def generate_embedding(text: str) -> List[float]:
    """
    Dummy embedding generator. Ganti pake model embedding asli Lo nanti.
    """
    # Contoh sederhana: representasi setiap karakter jadi float
    return [float(ord(c)) for c in text][:384] + [0.0]*(384-len(text))  # pad ke 384 dimensi

def find_similar_foods_fast(
    query_embedding: List[float],
    foods_data: List[Dict],
    top_k: int = 5,
    threshold: float = 0.5
) -> List[Dict]:
    """
    Fast similarity search optimized for food recommendations.
    Auto-generate embedding jika makanan belum punya embedding.
    """
    if not foods_data:
        return []

    embeddings = []
    valid_foods = []

    for food in foods_data:
        if "embedding" not in food or not food["embedding"] or len(food["embedding"]) != len(query_embedding):
            # generate embedding otomatis
            food["embedding"] = generate_embedding(food["name"])
        embeddings.append(food["embedding"])
        valid_foods.append(food)

    # Calculate all similarities at once
    similarities = batch_similarity(query_embedding, embeddings)

    # Pair foods with their scores
    results = []
    for i, score in enumerate(similarities):
        if score >= threshold:
            food_with_score = valid_foods[i].copy()
            food_with_score["similarity_score"] = float(score)
            results.append(food_with_score)

    # Sort by score
    results.sort(key=lambda x: x["similarity_score"], reverse=True)

    return results[:top_k]