import logging
from src.memory.session_manager import SessionManager
from src.database.connection import db_instance
from src.database.models.user import UserMemoryModel

logger = logging.getLogger(__name__)

class MemoryManager:
    """Bridge STM (session memory) & LTM (MongoDB)"""

    def __init__(self):
        self.stm = SessionManager()  # Short-term memory per sesi
        self.ltm_model = UserMemoryModel(db_instance["user_memory"])  # Long-term memory dari DB

    # ========================== CONTEXT ==========================
    def get_context(self, user_id: str, session_id: str):
        """Ambil data STM (session) + LTM (user)"""
        stm_data = self.stm.get_stm(session_id)
        ltm_data = self.ltm_model.get_memory(user_id)
        return {
            "stm": stm_data or {},
            "ltm": ltm_data or {},
        }
    
    def save_context(self, user_id: str, session_id: str, context: dict):
        """
        Kompatibilitas untuk agent lama yang kirim combined_context.
        Akan nyimpen history terbaru (kalau ada) ke STM.
        """
        try:
            last_user_msg = context.get("raw_input", "")
            if last_user_msg:
                self.stm.add_message(session_id, "user", last_user_msg)
            logger.debug(f"[Compat STM] Saved context for {session_id}")
        except Exception as e:
            logger.warning(f"⚠️ Gagal save_context (compat mode): {e}")


    # ========================== LTM ==========================
    def add_liked_food(self, user_id: str, food_name: str):
        """Tambahkan makanan yang disukai user ke LTM"""
        self.ltm_model.add_liked_food(user_id, food_name)
        logger.info(f"[LTM] Added liked food: {food_name}")

    def add_disliked_food(self, user_id: str, food_name: str):
        """Tambahkan makanan yang tidak disukai user ke LTM"""
        self.ltm_model.add_disliked_food(user_id, food_name)
        logger.info(f"[LTM] Added disliked food: {food_name}")

    def add_allergy(self, user_id: str, allergen: str):
        """Tambahkan alergi baru user ke LTM"""
        self.ltm_model.add_allergy(user_id, allergen)
        logger.info(f"[LTM] Added allergy: {allergen}")
