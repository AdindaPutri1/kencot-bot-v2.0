"""
Configuration settings for Kencot Bot
"""

import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Main configuration class"""
    
    # Bot settings
    BOT_NAME = "Kencot Bot - Mamang UGM"
    BOT_VERSION = "1.0.0"
    BOT_DESCRIPTION = "Chatbot rekomendasi makanan UGM dengan gaya Gen Z"
    
    # Flask settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'kencot-bot-secret-key-2024')
    DEBUG = os.getenv('FLASK_ENV') == 'development'
    
    # WhatsApp Business API settings
    WHATSAPP_TOKEN = os.getenv('WHATSAPP_TOKEN')
    PHONE_NUMBER_ID = os.getenv('PHONE_NUMBER_ID')
    WEBHOOK_VERIFY_TOKEN = os.getenv('WEBHOOK_VERIFY_TOKEN', 'kencot-webhook-token')
    
    # OpenAI/Gemini API settings (for future LLM integration)
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    
    # Database settings
    DATABASE_PATH = 'data/database.json'
    RESPONSES_PATH = 'data/responses.json'
    
    # Logging settings
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = 'bot.log'
    LOG_MAX_BYTES = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT = 5
    
    # Session settings
    SESSION_TIMEOUT_MINUTES = 30
    MAX_CONVERSATION_HISTORY = 100
    
    # Faculty proximity mapping (ordered by distance)
    FACULTY_PROXIMITY = {
        "Teknik": [
            "Kantin Teknik", 
            "Kantin FKKMK", 
            "Kantin Filsafat", 
            "Penyetan Bu Lastri",
            "Warung Makan Bu Har"
        ],
        "MIPA": [
            "Penyetan Bu Lastri",
            "Kantin MIPA", 
            "Kantin Teknik", 
            "Warung Makan Bu Har",
            "Kantin FKKMK"
        ],
        "FKKMK": [
            "Kantin FKKMK",
            "Kantin Teknik", 
            "Kantin Filsafat",
            "Penyetan Bu Lastri"
        ],
        "Pertanian": [
            "Kantin Pertanian",
            "Warung Makan Bu Har", 
            "Kantin Filsafat",
            "Penyetan Bu Lastri"
        ],
        "Filsafat": [
            "Kantin Filsafat",
            "Kantin FKKMK", 
            "Kantin Teknik",
            "Penyetan Bu Lastri"
        ],
        "Pascasarjana": [
            "Warung Makan Bu Har",
            "Kantin Pertanian", 
            "Penyetan Bu Lastri",
            "Kantin Filsafat"
        ],
        "Psikologi": [
            "Kantin Filsafat",
            "Kantin FKKMK",
            "Kantin Teknik"
        ],
        "FEB": [
            "Kantin FEB",
            "Kantin Filsafat", 
            "Kantin FKKMK"
        ],
        "Hukum": [
            "Kantin Filsafat",
            "Kantin FKKMK",
            "Kantin FEB"
        ],
        "ISIPOL": [
            "Kantin Filsafat",
            "Kantin FKKMK",
            "Kantin FEB"
        ],
        "Farmasi": [
            "Kantin FKKMK",
            "Kantin Teknik",
            "Kantin Filsafat"
        ],
        "Kehutanan": [
            "Kantin Pertanian",
            "Warung Makan Bu Har",
            "Kantin Filsafat"
        ],
        "Peternakan": [
            "Kantin Pertanian",
            "Warung Makan Bu Har",
            "Penyetan Bu Lastri"
        ]
    }
    
    # Time-based food category mapping
    TIME_FOOD_MAPPING = {
        "pagi": {
            "primary": ["makanan_ringan", "minuman", "sarapan"],
            "secondary": ["cemilan", "roti"]
        },
        "siang": {
            "primary": ["makanan_berat", "nasi", "paket_komplit"],
            "secondary": ["makanan_ringan", "minuman"]
        },
        "sore": {
            "primary": ["cemilan", "jajanan", "minuman"],
            "secondary": ["makanan_ringan"]
        },
        "malam": {
            "primary": ["makanan_berat", "makanan_hangat", "nasi"],
            "secondary": ["cemilan", "minuman"]
        }
    }
    
    # Hunger level to food category mapping
    HUNGER_MAPPING = {
        "laper_brutal": {
            "categories": ["makanan_berat", "nasi", "paket_komplit"],
            "min_price": 8000,
            "portion_preference": "besar"
        },
        "laper_standar": {
            "categories": ["makanan_berat", "nasi", "makanan_ringan"],
            "min_price": 5000,
            "portion_preference": "sedang"
        },
        "cuma_iseng": {
            "categories": ["cemilan", "jajanan", "minuman", "makanan_ringan"],
            "min_price": 2000,
            "portion_preference": "kecil"
        }
    }
    
    # Budget categories for better recommendations
    BUDGET_CATEGORIES = {
        "hemat": {"min": 0, "max": 10000, "label": "hemat banget"},
        "ekonomis": {"min": 10001, "max": 20000, "label": "ekonomis"},
        "standar": {"min": 20001, "max": 30000, "label": "standar"},
        "premium": {"min": 30001, "max": 50000, "label": "premium"},
        "sultan": {"min": 50001, "max": 100000, "label": "sultan mode"}
    }
    
    # Regex patterns for message processing
    REGEX_PATTERNS = {
        "food_triggers": [
            r'\b(laper|lapar|hungry|kencot|makan|mam|maksi|enak)\b',
            r'\b(ngemil|cemil|kenyang|kuliner|jajan|rekomen|recommend)\b',
            r'\b(food|breakfast|lunch|dinner|sarapan|siang|malam|sore|pagi)\b'
        ],
        "location_patterns": [
            r'\b(teknik|mipa|fkkmk|kedokteran|pertanian|filsafat)\b',
            r'\b(pascasarjana|psikologi|farmasi|kehutanan|peternakan)\b',
            r'\b(geografi|biologi|kimia|fisika|matematika|isipol)\b',
            r'\b(hukum|ekonomi|feb|ugm|bulaksumur)\b'
        ],
        "budget_patterns": [
            r'(\d+)(?:\s*(?:k|rb|ribu|rp|rupiah|000))?',
            r'(lima|sepuluh|limabelas|duapuluh|tigapuluh)(?:\s*(?:ribu|rb))?',
            r'\b(murah|mahal|hemat|ekonomis|budget|duit)\b'
        ],
        "hunger_patterns": [
            r'\b([abc])\b',
            r'\b(brutal|banget|parah|standar|biasa|iseng|ngunyah|ngemil)\b'
        ]
    }
    
    # Gen Z vocabulary and expressions
    GENZ_EXPRESSIONS = {
        "positive": [
            "mantul", "gaskeun", "fix", "auto", "legend", "epic", 
            "vibes", "no cap", "periodt", "slay", "fire", "bussin"
        ],
        "negative": [
            "waduh", "yah", "duh", "aduh", "alamak", "astaga"
        ],
        "filler": [
            "gini deh", "btw", "kayaknya", "gimana gitu", "kira-kira",
            "trus", "eh", "nah", "nih", "yah kan"
        ],
        "food_descriptors": [
            "nampol", "nagih", "juicy", "crispy", "gurih", "pedas mantul",
            "kenyang maksimal", "porsi kuli", "rasa mendalam", "comfort food"
        ]
    }
    
    # Response templates categories
    RESPONSE_CATEGORIES = {
        "greetings": "Greeting responses",
        "location_ask": "Asking for location",
        "hunger_ask": "Asking about hunger level", 
        "budget_ask": "Asking about budget",
        "recommendations": "Food recommendations",
        "no_results": "No recommendations found",
        "errors": "Error handling",
        "confirmations": "Confirmation responses",
        "goodbyes": "Goodbye responses"
    }
    
    # Feature flags for development
    FEATURES = {
        "enable_llm_integration": False,
        "enable_voice_notes": False,
        "enable_image_recognition": False,
        "enable_location_services": False,
        "enable_user_preferences": True,
        "enable_conversation_memory": True,
        "debug_mode": DEBUG
    }
    
    # Rate limiting settings
    RATE_LIMITS = {
        "messages_per_user_per_minute": 10,
        "messages_per_user_per_hour": 100,
        "global_messages_per_minute": 1000
    }
    
    # Health check settings
    HEALTH_CHECK = {
        "database_check": True,
        "api_check": True,
        "memory_check": True,
        "response_time_threshold": 2.0  # seconds
    }

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    LOG_LEVEL = 'DEBUG'

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    LOG_LEVEL = 'INFO'
    
class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    DATABASE_PATH = 'tests/test_database.json'
    RESPONSES_PATH = 'tests/test_responses.json'