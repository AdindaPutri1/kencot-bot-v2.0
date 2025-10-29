"""
Minimal Embedding Generator for JSON -> RAG database
"""
import logging
import hashlib
from typing import List, Union

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None  # fallback

from sklearn.feature_extraction.text import TfidfVectorizer

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

EMBEDDING_DIM = 192 

class EmbeddingGenerator:
    """Generate embeddings for text - with offline fallback"""

    def __init__(self, model_name: str = "all-MiniLM-L3-v2"):
        self._use_fallback = False
        self._model = None
        self._vectorizer = None
        self._initialize_model(model_name)

    def _initialize_model(self, model_name: str):
        if SentenceTransformer:
            try:
                logger.info(f"Loading embedding model: {model_name}")
                self._model = SentenceTransformer(model_name, cache_folder="./models")
                self._use_fallback = False
                logger.info("✅ Embedding model loaded successfully")
            except Exception as e:
                logger.warning(f"⚠️ Could not load transformer model: {e}")
                self._use_fallback = True
        else:
            self._use_fallback = True

        if self._use_fallback:
            logger.info("🔄 Using fallback TF-IDF based embeddings")
            self._init_fallback()

    def _init_fallback(self):
        """Initialize simple TF-IDF fallback"""
        vocab = [
            'nasi', 'ayam', 'goreng', 'mie', 'soto', 'bakso', 'geprek',
            'pedas', 'manis', 'asam', 'gurih', 'kenyang', 'berat', 'ringan',
            'sarapan', 'siang', 'malam', 'cemilan', 'minuman', 'pagi', 'sore',
            'sambal', 'sayur', 'telur', 'tempe', 'tahu', 'ikan', 'seafood',
            'steak', 'dimsum', 'batagor', 'gado', 'pecel', 'rawon', 'gulai',
            'penyet', 'bakar', 'rebus', 'kuah', 'kering', 'porsi', 'besar'
        ]
        self._vectorizer = TfidfVectorizer(
            vocabulary=vocab,
            max_features=EMBEDDING_DIM,
            ngram_range=(1, 2)
        )
        self._vectorizer.fit(vocab)

    def encode(self, text: Union[str, List[str]]) -> List[float]:
        """Generate embedding for single text"""
        if self._use_fallback:
            return self._fallback_encode(text)
        if isinstance(text, str):
            return self._model.encode(text, show_progress_bar=False).tolist()
        else:
            return self._model.encode(text, show_progress_bar=False).tolist()

    def _fallback_encode(self, text: Union[str, List[str]]) -> List[float]:
        """TF-IDF + hash fallback"""
        if isinstance(text, str):
            text = [text]
        try:
            vectors = self._vectorizer.transform(text).toarray()
            if vectors.shape[1] < EMBEDDING_DIM:
                padding = [[0.0] * (EMBEDDING_DIM - vectors.shape[1])]
                vectors = [[*row, *padding[0]] for row in vectors]
            return vectors[0] if len(text) == 1 else vectors.tolist()
        except Exception:
            return self._hash_encode(text[0] if len(text) == 1 else text)

    def _hash_encode(self, text: str) -> List[float]:
        embedding = []
        for i in range(48):  # 48 × 8 bytes = 384
            seed = f"{text}_{i}"
            hash_bytes = hashlib.sha256(seed.encode()).digest()
            for j in range(8):
                embedding.append(float(hash_bytes[j]) / 255.0)
        return embedding[:EMBEDDING_DIM]

# Global instance
embedding_generator = EmbeddingGenerator()

def get_embedding(text: str) -> List[float]:
    return embedding_generator.encode(text)
