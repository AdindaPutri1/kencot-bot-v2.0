import logging
from flask import Flask, request, jsonify
from src.database.connection import db_instance
from src.utils.config import Config
from src.bot.kencot_bot import KencotBot
from src.memory.session_manager import SessionManager

# --- Logging setup ---
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# --- Flask setup ---
app = Flask(__name__)

# --- Global bot instance ---
bot = None
session_mgr = None

def initialize_database():
    """Initialize database and load food data"""
    logger.info("Initializing database...")
    db_instance.connect()
    if db_instance.use_mongo:
        print("[OK] Using MongoDB for storage")
    else:
        print("[OK] Using JSON file for storage")

def initialize_bot():
    """Init config, DB, and bot (once only)"""
    global bot, session_mgr
    Config.validate()
    initialize_database()
    session_mgr = SessionManager()
    bot = KencotBot()
    print("🤖 KENCOT BOT - WhatsApp API Mode aktif!")

# === ROUTES ===

@app.route("/handle", methods=["POST"])
def handle_message():
    """Handle message from WhatsApp connector"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Missing JSON body"}), 400

        user_id = data.get("user_id", "unknown_user")
        session_id = data.get("session_id", f"sess_{user_id}")
        text = data.get("text", "").strip()

        if not text:
            return jsonify({"response": "⚠️ Pesan kosong nih, coba ketik lagi ya!"}), 400

        # --- Proses dengan bot ---
        response = bot.handle_user_input(user_id, session_id, text)
        return jsonify({
            "status": "success",
            "user_id": user_id,
            "session_id": session_id,
            "bot_response": response.get("response", ""),
            "metadata": response.get("metadata", {}),
            "phase": response.get("phase", "")
        })
    except Exception as e:
        logger.error(f"Error processing message: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route("/ping", methods=["GET"])
def ping():
    """Simple health check"""
    return jsonify({"status": "ok", "message": "Kencot Bot API is running 🚀"})


if __name__ == "__main__":
    initialize_bot()
    app.run(host="0.0.0.0", port=5000)
