import os
import logging
from flask import Flask, request, jsonify
from app.bot import KencotBot
from app.config import Config

# --- Logging Setup ---
logging.basicConfig(
    level=Config.LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Config.LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# --- Flask App and Bot Initialization ---
app = Flask(__name__)
app.config.from_object(Config)

# Variabel 'kencot_bot' dibuat di sini agar bisa diakses oleh fungsi di bawahnya
try:
    kencot_bot = KencotBot(Config)
    logger.info(f"{Config.BOT_NAME} v{Config.BOT_VERSION} initialized successfully for API mode.")
except Exception as e:
    logger.critical(f"Failed to initialize KencotBot: {e}", exc_info=True)
    exit()

# --- API Endpoints ---

@app.route('/')
def home():
    """Health check endpoint to confirm the API is running."""
    return jsonify({
        "status": "ok",
        "bot_name": Config.BOT_NAME,
        "mode": "api_server"
    })

@app.route('/chat', methods=['POST'])
def chat_handler():
    """
    API endpoint to interact with the bot.
    Receives a message and returns the bot's response.
    """
    data = request.get_json()
    if not data or 'user_id' not in data or 'message' not in data:
        return jsonify({"error": "Missing user_id or message in request body"}), 400
    
    user_id = data['user_id']
    message = data['message']
    
    logger.info(f"API received message from {user_id}: '{message}'")
    
    try:
        # Menggunakan variabel kencot_bot yang sudah dibuat di atas
        response_text = kencot_bot.handle_message(user_id, message)
        return jsonify({"response": response_text})
    except Exception as e:
        logger.error(f"Error processing chat request for {user_id}: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

# --- Main Execution ---

if __name__ == '__main__':
    # Port for the API server, e.g., 5000
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port)