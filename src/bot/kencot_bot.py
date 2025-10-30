import logging
import json
import random
from datetime import datetime, timedelta, timezone
from typing import Dict, Any

from src.bot.agent import FoodAgent
from src.memory.session_manager import SessionManager

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class KencotBot:
    def __init__(self, max_interactions: int = 3, cooldown_minutes: int = 10):
        self.agent = FoodAgent()
        self.session = SessionManager()
        self.max_interactions = max_interactions
        self.cooldown_delta = timedelta(minutes=cooldown_minutes)
        self.greetings = [
    "Halo bestie! Ada yang laper nih 👀 Mau makan apa hari ini? Kasih tau preferensi kamu ya—biar Mamang UGM racik rekomendasi yang cocok! Kamu juga bisa bilang makanan yang ga disuka atau alergi biar aman 🍽️✨",
    "Waduhhh ada yang perutnya konser ya? 😆 Tenang, Mamang UGM siap bantu cari makan terenak buat kamu!",
    "Yeay ada yang mau mam! 🍚🥗 Gaskeun kita berburu kuliner mantap bareng Mamang UGM! Mau sehat? Murah? Pedes? Tinggal bilang aja 🔥",
    "Halo, calon anak kos kenyang! 😎 Lagi bingung makan apa? Mamang bantu pilih menu yang pas buat perut dan dompet kamu 💸🍛",
    "Hoh! Ada yang kencot detected 🚨 Siap-siap, Mamang bakal rekomendasiin makanan bikin mood naik + kenyang maksimal 😋",
    "Halo! Waktunya isi bensin perut nih ⛽🍜 Kasih tau maunya apa, atau bilang aja suasana makanmu gimana. Mamang siap bantu!",
    ]


    def handle_user_input(self, user_id: str, session_id: str, text: str) -> Dict[str, Any]:
        stm = self.session.get_stm(session_id)
        if not stm:
            self.session.create_session(session_id, user_id)
            stm = self.session.get_stm(session_id)
            stm.update({
                "phase": "greetings",
                "interaction_count": 0,
                "cooldown_until": None
            })

        # === Cooldown ===
        cooldown_until = stm.get("cooldown_until")
        if cooldown_until:
            now = datetime.now(timezone.utc)
            if now < cooldown_until:
                remaining = int((cooldown_until - now).total_seconds() // 60) + 1
                return {"response": f"Token kamu habis. Coba lagi dalam {remaining} menit ya ⏳", "phase": "cooldown"}
            else:
                # Cooldown selesai reset
                stm["interaction_count"] = 0
                stm["cooldown_until"] = None
                stm["phase"] = "greetings"


        # === Reset Command ===
        text_lower = text.lower().strip()
        if any(w in text_lower for w in ["ulang", "reset", "restart", "mulai", "batal"]):
            return self._handle_reset(user_id, session_id)

        # === Handle Phase ===
        phase = stm.get("phase", "greetings")
        if phase == "greetings":
            return self._handle_greetings(user_id, session_id)
        elif phase == "recommendation":
            return self._handle_recommendation(user_id, session_id, text)
        else:
            stm["phase"] = "greetings"
            return self._handle_greetings(user_id, session_id)

    # === GREETING PHASE ===
    def _handle_greetings(self, user_id: str, session_id: str) -> Dict[str, Any]:
        stm = self.session.get_stm(session_id)
        greeting = random.choice(self.greetings)
        stm["phase"] = "recommendation"
        self.session.add_message(session_id, "bot", greeting)
        return {"response": greeting, "phase": "greetings"}

    # === RECOMMENDATION PHASE ===
    def _handle_recommendation(self, user_id: str, session_id: str, text: str) -> Dict[str, Any]:
        stm = self.session.get_stm(session_id)
        count = stm.get("interaction_count", 0)

        # Limit interaksi
        if count >= self.max_interactions:
            stm["phase"] = "cooldown"
            stm["cooldown_until"] = datetime.now(timezone.utc) + self.cooldown_delta
            msg = f"Token kamu habis. Coba lagi {int(self.cooldown_delta.total_seconds()//60)} menit lagi ya 🕒"
            return {"response": msg, "phase": "cooldown"}

        # Proses ke FoodAgent
        result = self.agent.process(user_id, session_id, text)
        stm["interaction_count"] = count + 1
        stm["phase"] = "recommendation"  # tetap di recommendation

        # Simpan context percakapan
        self.session.add_message(session_id, "user", text)
        self.session.add_message(session_id, "bot", result.get("reasoning", ""))

        return {
            "response": result.get("reasoning", ""),
            "metadata": {
                "recommendation": result.get("recommendation"),
                "nutrition": result.get("nutrition"),
                "decision_type": result.get("decision_type"),
                "tool_used": result.get("tool_used"),
                "ltm_used": result.get("ltm_used"),
            },
            "phase": "recommendation"
        }

    # === RESET PHASE ===
    def _handle_reset(self, user_id: str, session_id: str) -> Dict[str, Any]:
        self.session.clear_stm(session_id)
        self.session.create_session(session_id, user_id)
        stm = self.session.get_stm(session_id)
        stm.update({
            "phase": "greetings",
            "interaction_count": 0,
            "cooldown_until": None
        })
        msg = "Oke! Memori percakapan direset, tapi preferensi kamu tetap aman 😎"
        self.session.add_message(session_id, "bot", msg)
        return {"response": msg, "phase": "reset"}
