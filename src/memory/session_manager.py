from typing import Dict
from datetime import datetime, timedelta, timezone

class SessionManager:
    """Short-Term Memory per session"""

    def __init__(self):
        self.short_term_memory = {}

    def create_session(self, session_id: str, user_id: str, duration_minutes: int = 30):
        now = datetime.now(timezone.utc)
        self.short_term_memory[session_id] = {
            "user_id": user_id,
            "phase": "greetings",
            "interaction_count": 0,
            "conversation_history": [],
            "created_at": now,
            "expires_at": now + timedelta(minutes=duration_minutes),
            "cooldown_until": None
        }

    def get_stm(self, session_id: str) -> dict:
        return self.short_term_memory.get(session_id)

    def add_message(self, session_id: str, role: str, message: str):
        session = self.short_term_memory.setdefault(session_id, {})
        session.setdefault("conversation_history", []).append({
            "role": role,
            "message": message,
            "timestamp": datetime.now(timezone.utc)
        })
    
    def get_messages(self, session_id: str):
        """Ambil daftar percakapan (role + content)"""
        session = self.short_term_memory.get(session_id, {})
        history = session.get("conversation_history", [])
        return [{"role": h["role"], "content": h["message"]} for h in history]


    def clear_stm(self, session_id: str):
        self.short_term_memory.pop(session_id, None)

    
