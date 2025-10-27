"""
Configuration settings for Kencot Bot V2.0
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Configuration class"""

    MAX_RECOMMENDATIONS = 3
    
    # Base paths
    BASE_DIR = Path(__file__).parent.parent
    DATA_DIR = BASE_DIR / "data"
    LOGS_DIR = BASE_DIR / "logs"
    
    # Create directories if they don't exist
    DATA_DIR.mkdir(exist_ok=True)
    LOGS_DIR.mkdir(exist_ok=True)
    
    # Database settings (MongoDB is optional)
    MONGO_URI = os.getenv("MONGO_URI", None)
    MONGODB_URI = os.getenv("MONGODB_URI", None) or MONGO_URI  # Support both names
    MONGO_DB = os.getenv("MONGO_DB", "kencot_bot_v2")
    MONGODB_DB = os.getenv("MONGODB_DB", None) or MONGO_DB  # Support both names
    
    # Data files
    FOODS_PATH = DATA_DIR / "foods_with_embeddings.json"
    CANTEENS_PATH = DATA_DIR / "canteens.json"
    RESPONSES_PATH = DATA_DIR / "responses.json"
    DATABASE_PATH = DATA_DIR / "database.json"
    
    # API Keys
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    
    # LLM Settings
    GEMINI_BASE_URL = os.getenv("GEMINI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta")
    LLM_MODEL = os.getenv("LLM_MODEL", "groq")  # groq, gemini, openai
    LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.groq.com/openai/v1")
    GROQ_MODEL_NAME = os.getenv("GROQ_MODEL_NAME", "llama-3.1-8b-instant")
    GEMINI_MODEL_NAME = os.getenv("GEMINI_MODEL_NAME", "gemini-2.5-flash")
    OPENAI_MODEL_NAME = os.getenv("OPENAI_MODEL_NAME", "gpt-3.5-turbo")
    
    # Embedding settings
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    EMBEDDING_DIM = int(os.getenv("EMBEDDING_DIM", "384"))
    
    # Memory settings
    SESSION_TIMEOUT_MINUTES = int(os.getenv("SESSION_TIMEOUT_MINUTES", "30"))
    MAX_CONVERSATION_HISTORY = int(os.getenv("MAX_CONVERSATION_HISTORY", "10"))
    
    # RAG settings
    TOP_K_RETRIEVAL = int(os.getenv("TOP_K_RETRIEVAL", "5"))
    SIMILARITY_THRESHOLD = float(os.getenv("SIMILARITY_THRESHOLD", "0.3"))
    
    # Bot settings
    BOT_NAME = os.getenv("BOT_NAME", "Mamang Kencot")
    BOT_PERSONALITY = os.getenv("BOT_PERSONALITY", "friendly and casual")
    
    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    # WhatsApp settings (for future use)
    WHATSAPP_NUMBER = os.getenv("WHATSAPP_NUMBER", "")
    
    @classmethod
    def validate(cls):
        """Validate critical configuration"""
        if not cls.GEMINI_API_KEY and not cls.GROQ_API_KEY:
            raise ValueError("At least one LLM API key must be configured")
        
        # Create directories if not exist
        cls.LOGS_DIR.mkdir(exist_ok=True)
        cls.DATA_DIR.mkdir(exist_ok=True)
        
        return True

# Validate on import
Config.validate()