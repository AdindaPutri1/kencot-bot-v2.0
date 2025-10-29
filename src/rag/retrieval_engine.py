"""
RAG Retrieval Engine Module
- Load RAG database (JSON)
- Generate embedding untuk user query
- Cari hasil paling mirip berdasarkan cosine similarity
"""

import json
import logging
import numpy as np
from typing import List, Dict, Optional
from src.rag.embeddings import get_embedding
from src.rag.similarity import cosine_similarity

logger = logging.getLogger(__name__)

def estimate_calories(protein_g: float = 0, carbs_g: float = 0, fat_g: float = 0) -> float:
    """
    Hitung kalori dari makronutrien secara manual
    1 gram protein/carbs = 4 kcal
    1 gram fat = 9 kcal
    """
    return round(protein_g*4 + carbs_g*4 + fat_g*9, 2)

class RetrievalEngine:
    """Lightweight RAG search engine untuk makanan"""

    def __init__(self, rag_db_path: str = "data/rag_database.json"):
        self.rag_db_path = rag_db_path
        self.foods = self._load_database()

    def _load_database(self) -> List[Dict]:
        """Load database makanan dari file JSON"""
        try:
            with open(self.rag_db_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Bisa format lama (dict) atau baru (list)
                if isinstance(data, list):
                    foods = data
                else:
                    foods = data.get("foods", [])

                logger.info(f"✅ Loaded {len(foods)} foods from RAG database")
                return foods
        except Exception as e:
            logger.error(f"❌ Failed to load RAG database: {e}")
            return []


    def search(
        self,
        query: str,
        top_k: int = 5,
        min_score: float = 0.3,
        context: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Cari makanan paling mirip berdasarkan embedding query user.

        Args:
            query: teks masukan user (misal: "mau makan pedas dan gurih")
            top_k: jumlah hasil teratas
            min_score: ambang batas similarity
            context: optional dict (bisa berisi 'budget' atau 'faculty')
        """
        if not self.foods:
            logger.warning("⚠️ RAG database kosong.")
            return []

        query_emb = get_embedding(query)
        if query_emb is None:
            logger.error("❌ Gagal generate embedding query.")
            return []

        results = []
        for food in self.foods:
            # pastikan embedding diubah jadi numpy array
            emb = np.array(food.get("embedding", []), dtype=float)
            if emb.size == 0:
                continue

            # ubah query embedding ke numpy array juga
            query_vec = np.array(query_emb, dtype=float)

    # hitung cosine similarity
            score = cosine_similarity(query_vec.reshape(1, -1), emb.reshape(1, -1))[0][0]

    # Optional context filter
            if context:
                budget = context.get("budget")
                faculty = context.get("faculty")

                if budget and food.get("price", 0) > budget:
                    continue
                if faculty and faculty not in food.get("faculty_proximity", []):
                    continue

            if score >= min_score:
                protein = food.get("protein_g") or 5.0
                carbs = food.get("carbohydrates_total_g") or 0
                fat = food.get("fat_total_g") or 0
                est_calories = estimate_calories(protein, carbs, fat)

            
                results.append({
                    "name": food.get("name"),
                    "canteen": food.get("canteen"),
                    "price": food.get("price"),
                    "tags": food.get("tags"),
                    "similarity_score": float(score),
                    "estimated_calories": est_calories,
                    "protein_g": protein,
                    "carbohydrates_total_g": carbs,
                    "fat_total_g": fat
                })


        # Urutkan berdasar skor tertinggi
        results.sort(key=lambda x: x["similarity_score"], reverse=True)
        return results[:top_k]
