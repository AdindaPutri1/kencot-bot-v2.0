"""
Short-term memory (STM) - Session-based conversation context
"""
from typing import Dict, List, Optional
from datetime import datetime
from src.database.models.session import Session
import logging

logger = logging.getLogger(__name__)

class ShortTermMemory:
    """
    Manages short-term conversation memory:
    - Current session context
    - Conversation phase
    - Recent messages
    """
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.session = self._ensure_session()

    def _ensure_session(self):
        """Pastikan session ada, kalau belum ada dibuat baru"""
        return Session.create_or_update(self.user_id)

    def get_phase(self) -> str:
        return self.session.get("phase", "idle")
    
    def set_phase(self, phase: str):
        Session.update(self.user_id, {"phase": phase})
        self.session = self._ensure_session()
    
    def get_context(self) -> Dict:
        return self.session.get("context", {})
    
    def update_context(self, updates: Dict):
        current_context = self.get_context()
        current_context.update(updates)
        Session.update(self.user_id, {"context": current_context})
        self.session = self._ensure_session()
    
    def set_context(self, context: Dict):
        Session.update(self.user_id, {"context": context})
        self.session = self._ensure_session()
    
    def add_message(self, role: str, message: str):
        """Tambahkan pesan ke history"""
        history = self.session.get("history", [])
        history.append({"role": role, "content": message, "timestamp": datetime.now()})
        Session.update(self.user_id, {"history": history})
        self.session = self._ensure_session()
    
    def get_conversation_history(self, limit: int = None) -> List[Dict]:
        history = self.session.get("history", [])
        if limit:
            return history[-limit:]
        return history
    
    def clear(self):
        """Reset short-term memory"""
        self.context = {}
        self.phase = "idle"
        self.history = []
    
    def reset_session(self):
        Session.clear(self.user_id)
        self.session = self._ensure_session()
    
    def get_last_user_message(self) -> Optional[str]:
        history = self.get_conversation_history()
        for msg in reversed(history):
            if msg.get("role") == "user":
                return msg.get("content")
        return None
    
    def get_last_bot_message(self) -> Optional[str]:
        history = self.get_conversation_history()
        for msg in reversed(history):
            if msg.get("role") == "bot":
                return msg.get("content")
        return None
    
    def has_context_key(self, key: str) -> bool:
        return key in self.get_context()
    
    def get_context_value(self, key: str, default=None):
        return self.get_context().get(key, default)
    
    def get_summary(self) -> Dict:
        return {
            "user_id": self.user_id,
            "phase": self.get_phase(),
            "context": self.get_context(),
            "message_count": len(self.get_conversation_history()),
            "last_user_message": self.get_last_user_message(),
            "last_bot_message": self.get_last_bot_message(),
            "session_created": self.session.get("created_at"),
            "session_expires": self.session.get("expires_at")
        }
