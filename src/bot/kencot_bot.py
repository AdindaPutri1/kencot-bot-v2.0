"""
Kencot Bot V2.0 - Main bot class with memory + RAG integration
"""
import logging
from typing import Dict, List
from src.config import Config
from src.handlers.trigger_handler import TriggerHandler
from src.memory.short_term_memory import ShortTermMemory
from src.memory.long_term_memory import LongTermMemory
from src.memory.memory_updater import MemoryUpdater
from src.rag.retrieval_engine import retrieval_engine
from src.llm.reasoner import llm_reasoner
from src.utils.time_utils import get_current_time_period, get_time_greeting
from src.utils.text_utils import (
    extract_faculty_from_text,
    extract_hunger_level_from_text,
    extract_budget_from_text,
    agree_response,
    is_full_response,
    is_thank_you
)
from src.utils.nutrition_estimator import nutrition_estimator
from src.utils.response_formatter import response_formatter
import json

logger = logging.getLogger(__name__)

class KencotBotV2:
    """Upgraded Kencot Bot with RAG + Memory"""

    def __init__(self):
        self.responses = self._load_responses()
        logger.info("Kencot Bot V2.0 initialized")

    def _load_responses(self) -> Dict:
        """Load response templates"""
        try:
            with open(Config.RESPONSES_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            logger.warning("Using default responses")
            return {
                "greetings": ["Halo bestie! Ada yang laper nih kayaknya 👀"],
                "location_ask": ["Posisi kamu dimana nih? Kasih tau fakultasnya ya!"],
                "hunger_level_ask": {
                    "question": "Siap! Tingkat lapermu gimana nih?",
                    "options": {
                        "A": "Laper brutal",
                        "B": "Laper standar",
                        "C": "Cuma iseng"
                    }
                },
                "budget_ask": ["Budget kamu berapa nih?"]
            }

    def handle_message(self, user_id: str, message: str) -> str:
        """Main message handler with RAG + Memory"""
        stm = ShortTermMemory(user_id)
        ltm = LongTermMemory(user_id)
        ltm.increment_interaction()
        stm.add_message("user", message)

        trigger = TriggerHandler.detect_trigger(message)
        if trigger == "reset":
            return self._handle_reset(user_id, stm)
        if trigger == "help":
            return TriggerHandler.get_help_response()
        if trigger == "greeting" and stm.get_phase() == "idle":
            return TriggerHandler.get_greeting_response()

        phase = stm.get_phase()
        quick_info = TriggerHandler.extract_quick_info(message)

        if self._is_complete_info(quick_info):
            return self._handle_complete_request(user_id, stm, ltm, quick_info)

        try:
            if phase == "idle":
                return self._handle_idle_phase(user_id, stm, ltm, message, trigger)
            elif phase == "waiting_location":
                return self._handle_location_phase(user_id, stm, message)
            elif phase == "waiting_hunger":
                return self._handle_hunger_phase(user_id, stm, message)
            elif phase == "waiting_budget":
                return self._handle_budget_phase(user_id, stm, ltm, message)
            elif phase == "recommendation_given":
                return self._handle_feedback_phase(user_id, stm, ltm, message)
            else:
                stm.set_phase("idle")
                return "Ada yang salah nih. Yuk mulai lagi! Bilang 'laper' ya 😊"
        except Exception as e:
            logger.error(f"Error handling message: {e}", exc_info=True)
            stm.clear()
            return "Aduh Mamang error nih 😵 Coba lagi ya!"

    def _is_complete_info(self, info: Dict) -> bool:
        return all(k in info for k in ["faculty", "hunger_level", "budget"])

    def _handle_reset(self, user_id: str, stm: ShortTermMemory) -> str:
        stm.clear()
        return "Siap! Udah direset. Kalau laper lagi tinggal bilang ya! 😊"

    def _handle_idle_phase(self, user_id: str, stm: ShortTermMemory, ltm: LongTermMemory, message: str, trigger: str) -> str:
        if trigger == "food_request":
            if ltm.is_returning_user():
                prefs = ltm.get_preferences_summary()
                greeting = (
                    f"{get_time_greeting()} Welcome back! 🎉\n\n"
                    f"Mamang inget kamu kok! Ini preferensi kamu:\n{prefs}\n\n"
                    "Sekarang mau makan di fakultas mana nih?"
                )
            else:
                greeting = (
                    f"{get_time_greeting()}\n\n"
                    f"Mamang siap bantuin cari makan! Kamu di fakultas mana nih? 📍"
                )
            stm.set_phase("waiting_location")
            return greeting
        return "Hai! Bilang 'laper' kalau mau makan ya! 😉"

    def _handle_location_phase(self, user_id: str, stm: ShortTermMemory, message: str) -> str:
        faculty = extract_faculty_from_text(message)
        if faculty:
            stm.update_context({"faculty": faculty})
            stm.set_phase("waiting_hunger")
            options = "\n".join([
                "A. Laper brutal (butuh nasi porsi kuli)",
                "B. Laper standar (yang penting kenyang)",
                "C. Cuma iseng (pengen ngunyah aja)"
            ])
            return f"Siap, {faculty} noted! 📍\n\nTingkat lapermu gimana nih?\n{options}"
        return "Hmm, fakultas mana ya? Coba sebutin yang spesifik kayak 'Teknik' atau 'MIPA' 🤔"

    def _handle_hunger_phase(self, user_id: str, stm: ShortTermMemory, message: str) -> str:
        hunger = extract_hunger_level_from_text(message)
        if hunger:
            stm.update_context({"hunger_level": hunger})
            stm.set_phase("waiting_budget")
            return "Okay noted! Budget kamu berapaan nih? 💰"
        return "Pilih A, B, atau C aja ya bestie! 😊"

    def _handle_budget_phase(self, user_id: str, stm: ShortTermMemory, ltm: LongTermMemory, message: str) -> str:
        budget = extract_budget_from_text(message)
        if not budget:
            return "Hmm, ga kedetect budgetnya. Coba angkanya ya, misal: 15k atau 20000"
        if budget < 5000:
            return f"Aduh budget {budget} itu keciiiil banget 😅\nMinimal 5 ribu ya biar ada pilihan!"

        stm.update_context({"budget": budget})
        context = stm.get_context()
        context["time_period"] = get_current_time_period()

        ltm.update_budget_range(budget, int(budget * 1.2))
        ltm.add_hunger_pattern({
            "hunger_level": context["hunger_level"],
            "time_period": context["time_period"],
            "budget": budget
        })
        return self._generate_rag_recommendation(user_id, stm, ltm, context)

    def _handle_complete_request(self, user_id: str, stm: ShortTermMemory, ltm: LongTermMemory, info: Dict) -> str:
        logger.info(f"Complete request detected: {info}")
        if info["budget"] < 5000:
            stm.set_phase("waiting_budget")
            return "Budget minimal 5 ribu ya! Coba sebutin lagi 😊"
        stm.update_context(info)
        info["time_period"] = get_current_time_period()
        ltm.update_budget_pattern(info["budget"])
        ltm.add_hunger_pattern({
            "hunger_level": info["hunger_level"],
            "time_period": info["time_period"],
            "budget": info["budget"]
        })
        return self._generate_rag_recommendation(user_id, stm, ltm, info)

    def _generate_rag_recommendation(self, user_id: str, stm: ShortTermMemory, ltm: LongTermMemory, context: Dict) -> str:
        """
        New logic:
         - retrieve candidate foods (RAG)
         - enrich with nutrition estimator
         - group by canteen, pick top-2 canteens
         - present full whatsapp-style detailed response
        """
        logger.info(f"Generating recommendation with context: {context}")
        # get candidate foods via retrieval_engine
        rag_results = retrieval_engine.search_by_context(
            user_id,
            context,
            top_k=Config.MAX_RECOMMENDATIONS * 5  # get more to allow grouping by canteen
        )

        if not rag_results:
            stm.set_phase("recommendation_given")
            return "Waduh, Mamang ga nemu makanan yang cocok nih 😢\nCoba ubah kriterianya dikit?"

        # Normalize keys to expected names and enrich nutr info
        # retrieval_engine may return different keys; ensure each item has: name, price, canteen_name, gmaps_link
        normalized = []
        for item in rag_results:
            normalized_item = {
                "name": item.get("name") or item.get("menu_name") or item.get("menu"),
                "price": item.get("price") or item.get("menu_price") or item.get("menu_price", 0) or 0,
                "canteen_name": item.get("canteen_name") or item.get("canteen") or item.get("canteen_name", "Kantin Lainnya"),
                "gmaps_link": item.get("gmaps_link") or item.get("gmaps") or item.get("gmaps_url") or "",
                # nutrition placeholders (nutrition_estimator will fill if possible)
                "calories": item.get("calories", None),
                "protein": item.get("protein", None),
                "fat": item.get("fat", None),
                "carbs": item.get("carbs", None),
                # keep original for trace/debug
                **item
            }
            normalized.append(normalized_item)

        # Enrich with nutrition estimator (should fill calories/protein/fat/carbs if missing)
        try:
            normalized = nutrition_estimator.enrich_foods(normalized)
        except Exception as e:
            logger.warning(f"nutrition_enrich failed: {e}")

        # Group by canteen preserving order
        canteen_order: List[str] = []
        canteen_map: Dict[str, List[Dict]] = {}
        for f in normalized:
            cname = f.get("canteen_name", "Kantin Lainnya")
            if cname not in canteen_map:
                canteen_map[cname] = []
                canteen_order.append(cname)
            canteen_map[cname].append(f)

        # Pick top 2 canteens (if available)
        selected_canteens = canteen_order[:2] if canteen_order else list(canteen_map.keys())[:2]

        # build flattened list that keeps only foods from selected canteens
        final_foods = []
        for cname in selected_canteens:
            final_foods.extend(canteen_map.get(cname, []))

        # store recommended food names to STM
        food_names = [f.get("name") for f in final_foods]
        stm.update_context({"recommended_foods": food_names})

        # Use llm_reasoner to generate a short opening (if exists) — tolerant to exceptions
        llm_intro = ""
        try:
            llm_intro = llm_reasoner.generate_recommendation(context, final_foods, canteen_data=None)
        except Exception as e:
            logger.debug(f"LLM reasoner failed: {e}")

        # Format final message using response_formatter
        try:
            formatted = response_formatter.format_whatsapp_style(final_foods)
            # Prefer to include llm_intro if it exists (prepend)
            if llm_intro:
                formatted = "Tunggu bentar, Mamang lagi mikir menu terbaik buat kamu... 🤔\n\n" + llm_intro + "\n\n" + formatted
        except Exception as e:
            logger.error(f"Formatting failed: {e}", exc_info=True)
            # fallback simple format
            formatted = "Nih rekomendasi (format gagal, pake fallback):\n\n" + response_formatter.format_simple_list(final_foods)

        stm.set_phase("recommendation_given")
        stm.add_message("bot", formatted)
        return formatted

    def _handle_feedback_phase(self, user_id: str, stm: ShortTermMemory, ltm: LongTermMemory, message: str) -> str:
        trigger = TriggerHandler.detect_trigger(message)
        if trigger == "feedback_positive":
            context = stm.get_context()
            foods = context.get("recommended_foods", [])
            MemoryUpdater.process_feedback(user_id, "positive", context, foods)
            stm.set_phase("idle")
            return "Yeay! Seneng deh kalau cocok! 🎉 Mamang bakal inget preferensi kamu buat next time."
        elif trigger == "feedback_negative":
            context = stm.get_context()
            foods = context.get("recommended_foods", [])
            MemoryUpdater.process_feedback(user_id, "negative", context, foods)
            stm.set_phase("waiting_location")
            return "Oops, maaf ya ga cocok 😔 Mau coba rekomendasi lain? Fakultas mana nih?"

        if is_full_response(message) or is_thank_you(message):
            stm.clear()
            return "Sip, wareg tenan! Kalau laper lagi tinggal bilang ya! 😋"

        agree = agree_response(message)
        if agree is True:
            stm.set_phase("waiting_location")
            return "Oke siap! Mau di fakultas mana kali ini? 😊"
        elif agree is False:
            stm.clear()
            return "Oke deh! Kalau laper lagi call Mamang ya! 😉"

        return "Gimana, mau rekomendasi lagi atau udah cukup? 😊"


# Global bot instance
kencot_bot = KencotBotV2()
