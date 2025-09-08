import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Main configuration class for the bot."""
    
    # --- BOT SETTINGS ---
    BOT_NAME = "Kencot Bot - Mamang UGM"
    BOT_VERSION = "1.0.0"
    
    # --- FLASK SETTINGS ---
    # Used for session security, etc.
    SECRET_KEY = os.getenv('SECRET_KEY', 'a-very-secret-key-for-kencot-bot') # not used
    
    # --- WHATSAPP BUSINESS API SETTINGS ---
    # Get these from your Meta for Developers App dashboard
    WHATSAPP_TOKEN = os.getenv('WHATSAPP_TOKEN')
    PHONE_NUMBER_ID = os.getenv('PHONE_NUMBER_ID')
    WEBHOOK_VERIFY_TOKEN = os.getenv('WEBHOOK_VERIFY_TOKEN', 'kencot-bot-secret-token') # not used

    # --- LLM API SETTINGS (Optional for future use) ---
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    
    # --- FILE PATHS ---
    # These paths are relative to the project root directory
    DATABASE_PATH = 'data/database.json'
    RESPONSES_PATH = 'data/responses.json'
    
    # --- LOGGING SETTINGS ---
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = 'logs/kencot-bot.log'