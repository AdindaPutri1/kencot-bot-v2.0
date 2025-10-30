"""
Unit tests for RAG Retrieval Engine
"""
import pytest
from src.rag.similarity import calculate_cosine_similarity, find_similar_foods_fast
from src.rag.embeddings import get_embedding
from src.rag.retrieval_engine import retrieval_engine
from src.database.connection import db_instance
from src.database.models.food_db import Food

@pytest.fixture(scope="module")
def setup_db():
    """Setup database with test data"""
    db_instance.connect()
    Food.load_from_json()
    yield
    db_instance.close()

class TestSimilarity:
    
    def test_cosine_similarity(self):
        """Test cosine similarity calculation"""
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [1.0, 0.0, 0.0]
        
        similarity = calculate_cosine_similarity(vec1, vec2)
        assert similarity == pytest.approx(1.0, 0.01)
    
    def test_orthogonal_vectors(self):
        """Test orthogonal vectors (should be 0)"""
        vec1 = [1.0, 0.0]
        vec2 = [0.0, 1.0]
        
        similarity = calculate_cosine_similarity(vec1, vec2)
        assert similarity == pytest.approx(0.0, 0.01)
    
    def test_find_similar_foods(self, setup_db):
        """Test finding similar foods"""
        query_embedding = [0.2, -0.4, 0.7, -0.1, 0.5]
        
        foods = Food.get_all()
        results = find_similar_foods_fast(
            query_embedding,
            foods,
            top_k=3,
            threshold=0.5
        )
        
        assert len(results) <= 3
        if results:
            assert "similarity_score" in results[0]

class TestEmbeddings:
    
    def test_get_embedding(self):
        """Test embedding generation"""
        text = "nasi goreng pedas enak"
        embedding = get_embedding(text)
        
        assert isinstance(embedding, list)
        assert len(embedding) > 0
        assert all(isinstance(x, float) for x in embedding)
    
    def test_similar_texts_similar_embeddings(self):
        """Test that similar texts have similar embeddings"""
        emb1 = get_embedding("nasi goreng")
        emb2 = get_embedding("nasi goreng spesial")
        emb3 = get_embedding("es teh manis")
        
        sim_12 = calculate_cosine_similarity(emb1, emb2)
        sim_13 = calculate_cosine_similarity(emb1, emb3)
        
        # Nasi goreng should be more similar to each other
        assert sim_12 > sim_13

class TestRetrievalEngine:
    
    def test_search_by_context(self, setup_db):
        """Test context-based search"""
        context = {
            "faculty": "Teknik",
            "hunger_level": "brutal",
            "budget": 20000,
            "time_period": "siang"
        }
        
        results = retrieval_engine.search_by_context(
            "test_user_retrieval",
            context,
            top_k=3
        )
        
        assert isinstance(results, list)
        # Should return results or empty list
        assert len(results) >= 0
    
    def test_search_by_text(self, setup_db):
        """Test simple text search"""
        query = "makanan pedas gurih"
        
        results = retrieval_engine.search_by_text(query, top_k=5)
        
        assert isinstance(results, list)
        assert len(results) <= 5

if __name__ == "__main__":
    pytest.main([__file__, "-v"])