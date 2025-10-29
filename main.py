import logging
from src.database.connection import db_instance
from src.utils.config import Config
from src.bot.kencot_bot import KencotBot
from src.memory.session_manager import SessionManager

logger = logging.getLogger(__name__)

def initialize_database():
    """Initialize database and load food data"""
    logger.info("Initializing database...")
    db_instance.connect()

    if db_instance.use_mongo:
        print("[OK] Using MongoDB for storage")
    else:
        print("[OK] Using JSON file for storage")

def main():
    try:
        # --- Validasi config & inisialisasi DB ---
        Config.validate()
        initialize_database()

        # --- Setup session ---
        user_id = "user_123"
        session_id = "sess_1"
        session_mgr = SessionManager()
        session_mgr.create_session(session_id, user_id)

        # --- Inisialisasi Bot ---
        bot = KencotBot()

        # --- CLI Loop ---
        print("🤖 KENCOT BOT - CLI Mode (ketik 'exit' untuk keluar)")
        while True:
            text = input("User: ")
            if text.lower() in ["exit", "quit"]:
                break

            response = bot.handle_user_input(user_id, session_id, text)

            # Ambil context dari memori
            stm = bot.agent.memory.get_context(user_id, session_id).get("stm", {})
            ltm = bot.agent.memory.get_context(user_id, session_id).get("ltm", {})

            # Tampilkan hasil
            print("User Context (STM):", stm)
            print("User Context (LTM):", ltm)
            print("Bot Phase:", response.get("phase"))
            print("Bot Response:", response.get("response"))

            meta = response.get("metadata")
            if meta:
                print("Recommendation:", meta.get("recommendation"))
                print("Reasoning:", meta.get("nutrition"))
                print("Decision Type:", meta.get("decision_type"))
                print("Tool Used:", meta.get("tool_used"))
            print("-" * 50)

    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        print(f"Fatal error: {e}")
    finally:
        logger.info("Bot shut down.")

if __name__ == "__main__":
    main()
