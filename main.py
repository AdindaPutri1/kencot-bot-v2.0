"""
Main entry point for Kencot Bot V2.0
Supports CLI testing and WhatsApp integration via Flask API
"""
import logging
import sys
import json
from flask import Flask, request, jsonify
from src.config import Config
from src.database.connection import db_instance
from src.database.models.food import Food
from src.bot.kencot_bot import kencot_bot

# =====================================
# LOGGING SETUP
# =====================================
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Config.LOGS_DIR / 'kencot_bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# Fix Windows encoding issue
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

logger = logging.getLogger(__name__)

# =====================================
# DATABASE INIT
# =====================================
def initialize_database():
    """Initialize database and load food data"""
    logger.info("Initializing database...")
    db_instance.connect()

    if db_instance.use_mongo:
        print("[OK] Using MongoDB for storage")
    else:
        print("[OK] Using JSON file for storage")

    # Load food data
    food_count = Food.load_from_json()
    logger.info(f"Loaded {food_count} foods")

    # Count canteens
    from src.database.models.canteen import Canteen
    canteens = Canteen.get_all()
    logger.info(f"Found {len(canteens)} canteens")

    print(f"[OK] Loaded {food_count} foods and {len(canteens)} canteens")
    return food_count


# =====================================
# FLASK API (WhatsApp Integration)
# =====================================
app = Flask(__name__)

@app.route('/chat', methods=['POST'])
def chat_endpoint():
    """
    Endpoint to handle chat requests from WhatsApp (via Node.js)
    """
    try:
        data = request.get_json()
        user_id = data.get("user_id", "unknown_user")
        message = data.get("message", "").strip()

        if not message:
            return jsonify({"response": "Pesan kosong nih 😅"}), 400

        logger.info(f"[WA Chat] From {user_id}: {message}")

        # Proses lewat Kencot Bot
        response_text = kencot_bot.handle_message(user_id, message)

        logger.info(f"[Bot Reply] {response_text[:80]}...")
        return jsonify({"response": response_text})
    except Exception as e:
        logger.error(f"Error in /chat: {e}", exc_info=True)
        return jsonify({"response": "Aduh Mamang error nih 😵"}), 500


# =====================================
# CLI MODE (untuk testing manual)
# =====================================
def cli_mode():
    print("=" * 50)
    print("🤖 KENCOT BOT V2.0 - CLI MODE")
    print("=" * 50)
    print("Ketik 'quit' untuk keluar, atau 'reset' untuk ulang.")
    print("=" * 50)

    user_id = "cli_test_user"

    while True:
        try:
            msg = input("\n👤 You: ").strip()
            if msg.lower() in ["quit", "exit", "bye"]:
                print("👋 Bye! Makasih udah nyoba ya!")
                break
            elif msg.lower() == "reset":
                from src.database.models.session import Session
                Session.clear(user_id)
                print("🔄 Conversation reset!")
                continue

            reply = kencot_bot.handle_message(user_id, msg)
            print(f"\n🤖 Mamang: {reply}")

        except KeyboardInterrupt:
            print("\n👋 Interrupted. Bye!")
            break
        except Exception as e:
            logger.error(f"Error in CLI mode: {e}", exc_info=True)
            print(f"❌ Error: {e}")


# =====================================
# MAIN ENTRY POINT
# =====================================
def main():
    try:
        Config.validate()
        initialize_database()

        if len(sys.argv) > 1 and sys.argv[1] == "--cli":
            cli_mode()
        else:
            print("=" * 50)
            print("🤖 KENCOT BOT V2.0 - WHATSAPP MODE")
            print("=" * 50)
            print("API running on http://localhost:5000")
            print("Use Node.js connector to chat via WhatsApp 💬")
            print("=" * 50)

            app.run(host="0.0.0.0", port=5000)

    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        print(f"❌ Fatal error: {e}")
    finally:
        db_instance.close()
        logger.info("Bot shut down.")


if __name__ == "__main__":
    main()
