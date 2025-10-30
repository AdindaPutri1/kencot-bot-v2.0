# test/test_rag_engine.py
import pytest
import numpy as np
from src.rag.retrieval_engine import RetrievalEngine
from unittest.mock import patch
import json

# --- Dummy embedding function ---
def fake_get_embedding(text):
    if "pedas" in text.lower():
        return np.array([1.0, 0.0, 0.0])
    elif "manis" in text.lower():
        return np.array([0.0, 1.0, 0.0])
    return np.array([0.0, 0.0, 1.0])  # default / fallback

# --- Dummy RAG database ---
dummy_rag_data = [
    {"name": "Ayam Geprek", "embedding": [1.0, 0.0, 0.0]},
    {"name": "Pisang Goreng", "embedding": [0.0, 1.0, 0.0]},
    {"name": "Nasi Goreng", "embedding": [0.0, 0.0, 1.0]}
]

@pytest.fixture
def rag_engine(tmp_path):
    # Simpan dummy DB ke file JSON sementara
    db_file = tmp_path / "rag_db.json"
    with open(db_file, "w", encoding="utf-8") as f:
        json.dump(dummy_rag_data, f, ensure_ascii=False)
    return RetrievalEngine(str(db_file))

# --- Test semua kemungkinan input / branch ---

def test_rag_search_pedas(rag_engine):
    with patch("src.rag.retrieval_engine.get_embedding", side_effect=fake_get_embedding):
        results = rag_engine.search("aku mau makanan pedas", top_k=2)
        assert results[0]["name"] == "Ayam Geprek"
        assert results[0]["similarity_score"] > 0.9

def test_rag_search_manis(rag_engine):
    with patch("src.rag.retrieval_engine.get_embedding", side_effect=fake_get_embedding):
        results = rag_engine.search("aku mau makanan manis", top_k=2)
        assert results[0]["name"] == "Pisang Goreng"
        assert results[0]["similarity_score"] > 0.9

def test_rag_search_default(rag_engine):
    with patch("src.rag.retrieval_engine.get_embedding", side_effect=fake_get_embedding):
        results = rag_engine.search("aku mau makanan asin", top_k=2)
        # fallback branch
        assert results[0]["name"] == "Nasi Goreng"
        assert results[0]["similarity_score"] > 0.0

def test_rag_search_topk_greater_than_data(rag_engine):
    with patch("src.rag.retrieval_engine.get_embedding", side_effect=fake_get_embedding):
        results = rag_engine.search("aku mau makanan pedas", top_k=10)
        # top_k lebih besar dari jumlah DB
        assert len(results) <= 3

def test_rag_empty_database(tmp_path):
    empty_db_file = tmp_path / "empty_rag.json"
    with open(empty_db_file, "w", encoding="utf-8") as f:
        json.dump([], f)

    engine = RetrievalEngine(str(empty_db_file))
    with patch("src.rag.retrieval_engine.get_embedding", side_effect=fake_get_embedding):
        results = engine.search("pedas", top_k=2)
        # harus handle DB kosong
        assert results == []
