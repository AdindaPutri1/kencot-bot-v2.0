"""
Embedding generation with offline fallback
"""
import logging
import hashlib
from typing import List, Union
from src.config import Config

logger = logging.getLogger(__name__)

class EmbeddingGenerator:
    """Generate embeddings for text - with offline fallback"""
    
    _instance = None
    _model = None
    _use_fallback = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._model is None:
            self._initialize_model()
    
    def _initialize_model(self):
        """Try to load SentenceTransformer, fallback to simple embeddings"""
        try:
            from sentence_transformers import SentenceTransformer
            logger.info(f"Loading embedding model: {Config.EMBEDDING_MODEL}")
            
            # Try with timeout
            self._model = SentenceTransformer(
                Config.EMBEDDING_MODEL,
                cache_folder="./models"  # Local cache
            )
            self._use_fallback = False
            logger.info("✅ Embedding model loaded successfully")
            
        except Exception as e:
            logger.warning(f"⚠️ Could not load transformer model: {e}")
            logger.info("🔄 Using fallback TF-IDF based embeddings")
            self._use_fallback = True
            self._init_fallback()
    
    def _init_fallback(self):
        """Initialize simple TF-IDF based fallback"""
        from sklearn.feature_extraction.text import TfidfVectorizer
        
        # Pre-trained on Indonesian food vocabulary
        self._fallback_vocab = [
            'nasi', 'ayam', 'goreng', 'mie', 'soto', 'bakso', 'geprek',
            'pedas', 'manis', 'asam', 'gurih', 'kenyang', 'berat', 'ringan',
            'sarapan', 'siang', 'malam', 'cemilan', 'minuman', 'pagi', 'sore',
            'sambal', 'sayur', 'telur', 'tempe', 'tahu', 'ikan', 'seafood',
            'steak', 'dimsum', 'batagor', 'gado', 'pecel', 'rawon', 'gulai',
            'penyet', 'bakar', 'rebus', 'kuah', 'kering', 'porsi', 'besar'
        ]
        
        self._vectorizer = TfidfVectorizer(
            vocabulary=self._fallback_vocab,
            max_features=384,  # Match dimension with all-MiniLM-L6-v2
            ngram_range=(1, 2)
        )
        
        # Fit with dummy corpus
        self._vectorizer.fit(self._fallback_vocab)
    
    def encode(self, text: Union[str, List[str]]) -> List[float]:
        """
        Generate embedding for text
        
        Args:
            text: Single string or list of strings
            
        Returns:
            List of floats (embedding vector)
        """
        if self._use_fallback:
            return self._fallback_encode(text)
        
        if isinstance(text, str):
            return self._model.encode(text, show_progress_bar=False).tolist()
        else:
            return self._model.encode(text, show_progress_bar=False).tolist()
    
    def _fallback_encode(self, text: Union[str, List[str]]) -> List[float]:
        """Fallback encoding using TF-IDF + hashing"""
        if isinstance(text, str):
            text = [text]
        
        try:
            # TF-IDF encoding
            vectors = self._vectorizer.transform(text).toarray()
            
            # Pad to 384 dimensions if needed
            if vectors.shape[1] < 384:
                padding = [[0.0] * (384 - vectors.shape[1])]
                vectors = [[*row, *padding[0]] for row in vectors]
            
            return vectors[0] if len(text) == 1 else vectors.tolist()
            
        except Exception as e:
            logger.error(f"Fallback encoding failed: {e}")
            # Ultimate fallback: character-based hash embedding
            return self._hash_encode(text[0] if isinstance(text, list) else text)
    
    def _hash_encode(self, text: str) -> List[float]:
        """Emergency fallback: deterministic hash-based embedding"""
        # Use multiple hash functions for 384 dimensions
        embedding = []
        for i in range(48):  # 48 hash seeds × 8 bytes = 384 floats
            seed = f"{text}_{i}"
            hash_obj = hashlib.sha256(seed.encode())
            hash_bytes = hash_obj.digest()
            
            # Convert first 8 bytes to floats
            for j in range(0, 8):
                embedding.append(float(hash_bytes[j]) / 255.0)
        
        return embedding[:384]
    
    def encode_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts
        
        Args:
            texts: List of strings
            
        Returns:
            List of embedding vectors
        """
        if self._use_fallback:
            return [self._fallback_encode(text) for text in texts]
        
        return self._model.encode(texts, show_progress_bar=False).tolist()

# Global instance
embedding_generator = EmbeddingGenerator()

def get_embedding(text: str) -> List[float]:
    """Helper function to get embedding"""
    return embedding_generator.encode(text)

def get_embeddings_batch(texts: List[str]) -> List[List[float]]:
    """Helper function to get multiple embeddings"""
    return embedding_generator.encode_batch(texts)