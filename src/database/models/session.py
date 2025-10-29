"""
Session model untuk ShortTermMemory
Menyimpan session per user di JSON database
"""
import sys
from pathlib import Path

# tambahkan root project ke sys.path
sys.path.append(str(Path(__file__).resolve().parents[2]))

from src.database.connection import db_instance
from src.utils.config import Config

from datetime import datetime, timedelta

class Session:
    COLLECTION = "sessions"

    @classmethod
    def create_or_update(cls, user_id: str):
        session = db_instance[cls.COLLECTION].find_one({"user_id": user_id})
        now = datetime.now()
        expires_at = now + timedelta(minutes=Config.SESSION_TIMEOUT_MINUTES)
        
        if session is None:
            session = {
                "user_id": user_id,
                "created_at": now,
                "expires_at": expires_at,
                "phase": "idle",
                "context": {},
                "history": []
            }
            db_instance[cls.COLLECTION].insert_one(session)
        else:
            session["expires_at"] = expires_at
            db_instance[cls.COLLECTION].update_one(
                {"user_id": user_id},
                {"$set": {"expires_at": expires_at}}
            )
        db_instance.save()  # <--- ganti dari save_json() ke save()
        return session

    @classmethod
    def update(cls, user_id: str, updates: dict):
        db_instance[cls.COLLECTION].update_one(
            {"user_id": user_id}, {"$set": updates}
        )
        db_instance.save()  # <--- ganti juga

    @classmethod
    def clear(cls, user_id: str):
        db_instance[cls.COLLECTION].delete_many({"user_id": user_id})
        db_instance.save()  # <--- ganti juga
        
    @classmethod
    def get_active(cls, user_id: str):
        """Ambil session yang masih aktif (belum expired)"""
        session = db_instance[cls.COLLECTION].find_one({"user_id": user_id})
        if session:
            now = datetime.now()
            # jika expired, reset session
            if session["expires_at"] < now:
                cls.clear(user_id)
                return None
            return session
        return None