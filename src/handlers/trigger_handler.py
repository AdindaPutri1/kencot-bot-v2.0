"""
Trigger detection for initiating conversations
"""
import re
from typing import Optional, Dict

class TriggerHandler:
    """Detects conversation triggers and intents"""
    
    # Trigger patterns
    TRIGGERS = {
        'food_request': re.compile(
            r'\b(laper|lapar|hungry|kencot|makan|mam|rekomen|haus)\b',
            re.IGNORECASE
        ),
        'greeting': re.compile(
            r'\b(halo|hai|hi|hey|pagi|siang|sore|malam|assalam)\b',
            re.IGNORECASE
        ),
        'reset': re.compile(
            r'\b(ulang|reset|restart|mulai lagi|cancel|batal)\b',
            re.IGNORECASE
        ),
        'help': re.compile(
            r'\b(help|bantuan|gimana|cara|tutorial)\b',
            re.IGNORECASE
        ),
        'feedback_positive': re.compile(
            r'(👍|👏|mantap|enak|cocok|bagus|suka|makasih|thanks|good)',
            re.IGNORECASE
        ),
        'feedback_negative': re.compile(
            r'(👎|jelek|ga enak|ga cocok|mahal|jauh)',
            re.IGNORECASE
        ),
        'more_recommendations': re.compile(
            r'\b(lagi|more|tambah|lain)\b',
            re.IGNORECASE
        ),
        'done': re.compile(
            r'\b(wareg|kenyang|cukup|selesai|udah|done|finish)\b',
            re.IGNORECASE
        )
    }
    
    @classmethod
    def detect_trigger(cls, message: str) -> Optional[str]:
        """
        Detect primary trigger in message
        
        Args:
            message: User message
            
        Returns:
            Trigger name or None
        """
        message = message.strip()
        
        # Check each trigger pattern
        for trigger_name, pattern in cls.TRIGGERS.items():
            if pattern.search(message):
                return trigger_name
        
        return None
    
    @classmethod
    def detect_all_triggers(cls, message: str) -> list:
        """
        Detect all triggers in message
        
        Returns:
            List of trigger names
        """
        triggers = []
        
        for trigger_name, pattern in cls.TRIGGERS.items():
            if pattern.search(message):
                triggers.append(trigger_name)
        
        return triggers
    
    @classmethod
    def is_question(cls, message: str) -> bool:
        """Check if message is a question"""
        return message.strip().endswith('?')
    
    @classmethod
    def extract_quick_info(cls, message: str) -> Dict:
        """
        Try to extract all info from single message
        Useful for smart context detection
        
        Returns:
            Dict with extracted information
        """
        from src.utils.text_utils import (
            extract_faculty_from_text,
            extract_hunger_level_from_text,
            extract_budget_from_text
        )
        
        info = {}
        
        faculty = extract_faculty_from_text(message)
        if faculty:
            info['faculty'] = faculty
        
        hunger = extract_hunger_level_from_text(message)
        if hunger:
            info['hunger_level'] = hunger
        
        budget = extract_budget_from_text(message)
        if budget:
            info['budget'] = budget
        
        return info
    
    @classmethod
    def get_greeting_response(cls) -> str:
        """Get friendly greeting"""
        return (
            "Halo bestie! 👋 Aku Mamang, asisten makanan UGM.\n\n"
            "Lagi laper? Tinggal bilang aja 'laper' atau 'kencot', "
            "nanti aku bantuin cariin makanan yang pas buat kamu! 😋"
        )
    
    @classmethod
    def get_help_response(cls) -> str:
        """Get help message"""
        return (
            "📖 *Cara pakai Mamang:*\n\n"
            "1️⃣ Bilang 'laper' atau 'kencot' buat mulai\n"
            "2️⃣ Kasih tau fakultas kamu\n"
            "3️⃣ Pilih tingkat lapar (brutal/standar/iseng)\n"
            "4️⃣ Sebutin budget\n"
            "5️⃣ Mamang akan kasih rekomendasi terbaik!\n\n"
            "Kamu juga bisa kasih feedback 👍 👎 biar Mamang makin pinter! 🧠"
        )
    
def handle_trigger(intent: str) -> str | None:
    """
    Handle trigger intent dan kembalikan respon cepat (jika ada)
    """
    if intent == "greeting":
        return TriggerHandler.get_greeting_response()
    elif intent == "help":
        return TriggerHandler.get_help_response()
    elif intent == "reset":
        return "Oke bestie, aku reset dulu ya 🔄"
    elif intent in ["feedback_positive", "feedback_negative"]:
        return "Makasih feedback-nya bestie! Mamang makin semangat 😋"
    else:
        return None