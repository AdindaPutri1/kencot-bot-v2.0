"""
Kencot Bot V2.0 - Main bot class with memory + RAG integration
"""
import logging
from typing import Dict
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
from src.utils.calorie_utils import calculate_total_calories, format_nutrition_summary
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
            with open(self.config.RESPONSES_PATH, 'r', encoding='utf-8') as f:
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
        
        # Initialize memories
        stm = ShortTermMemory(user_id)
        ltm = LongTermMemory(user_id)
        
        # Increment interaction counter
        ltm.increment_interaction()
        
        # Store message in history
        stm.add_message("user", message)
        
        # Detect trigger
        trigger = TriggerHandler.detect_trigger(message)
        
        # Handle special triggers
        if trigger == "reset":
            return self._handle_reset(user_id, stm)
        
        if trigger == "help":
            return TriggerHandler.get_help_response()
        
        if trigger == "greeting" and stm.get_phase() == "idle":
            return TriggerHandler.get_greeting_response()
        
        # Get current phase
        phase = stm.get_phase()
        
        # Try smart extraction (all info at once)
        quick_info = TriggerHandler.extract_quick_info(message)
        
        if self._is_complete_info(quick_info):
            return self._handle_complete_request(user_id, stm, ltm, quick_info)
        
        # State machine flow
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
        """Check if all required info is present"""
        return all(k in info for k in ["faculty", "hunger_level", "budget"])
    
    def _handle_reset(self, user_id: str, stm: ShortTermMemory) -> str:
        """Reset conversation"""
        stm.clear()
        return "Siap! Udah direset. Kalau laper lagi tinggal bilang ya! 😊"
    
    def _handle_idle_phase(
        self,
        user_id: str,
        stm: ShortTermMemory,
        ltm: LongTermMemory,
        message: str,
        trigger: str
    ) -> str:
        """Handle idle phase"""
        if trigger == "food_request":
            # Check if returning user
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
    
    def _handle_location_phase(
        self,
        user_id: str,
        stm: ShortTermMemory,
        message: str
    ) -> str:
        """Handle location input"""
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
    
    def _handle_hunger_phase(
        self,
        user_id: str,
        stm: ShortTermMemory,
        message: str
    ) -> str:
        """Handle hunger level input"""
        hunger = extract_hunger_level_from_text(message)
        
        if hunger:
            stm.update_context({"hunger_level": hunger})
            stm.set_phase("waiting_budget")
            return "Okay noted! Budget kamu berapaan nih? 💰"
        
        return "Pilih A, B, atau C aja ya bestie! 😊"
    
    def _handle_budget_phase(
        self,
        user_id: str,
        stm: ShortTermMemory,
        ltm: LongTermMemory,
        message: str
    ) -> str:
        """Handle budget input and generate recommendations"""
        budget = extract_budget_from_text(message)
        
        if not budget:
            return "Hmm, ga kedetect budgetnya. Coba angkanya ya, misal: 15k atau 20000"
        
        if budget < 5000:
            return (
                f"Aduh budget {budget} itu keciiiil banget 😅\n"
                "Minimal 5 ribu ya biar ada pilihan!"
            )
        
        # Save context
        stm.update_context({"budget": budget})
        context = stm.get_context()
        context["time_period"] = get_current_time_period()
        
        # Update long-term memory
        ltm.update_budget_pattern(budget)
        ltm.add_hunger_pattern({
            "hunger_level": context["hunger_level"],
            "time_period": context["time_period"],
            "budget": budget
        })
        
        # Generate recommendation using RAG
        return self._generate_rag_recommendation(user_id, stm, ltm, context)
    
    def _handle_complete_request(
        self,
        user_id: str,
        stm: ShortTermMemory,
        ltm: LongTermMemory,
        info: Dict
    ) -> str:
        """Handle request with all info at once"""
        logger.info(f"Complete request detected: {info}")
        
        if info["budget"] < 5000:
            stm.set_phase("waiting_budget")
            return "Budget minimal 5 ribu ya! Coba sebutin lagi 😊"
        
        # Save to context
        stm.update_context(info)
        info["time_period"] = get_current_time_period()
        
        # Update long-term memory
        ltm.update_budget_range(info["budget"], info["budget"])
        ltm.add_hunger_pattern({
            "hunger_level": info["hunger_level"],
            "time_period": info["time_period"],
            "budget": info["budget"]
        })
        
        return self._generate_rag_recommendation(user_id, stm, ltm, info)
    
    def _generate_rag_recommendation(
        self,
        user_id: str,
        stm: ShortTermMemory,
        ltm: LongTermMemory,
        context: Dict
    ) -> str:
        """Generate recommendation using RAG + LLM"""
        
        # Search using RAG
        rag_results = retrieval_engine.search_by_context(
            user_id,
            context,
            top_k=Config.MAX_RECOMMENDATIONS
        )
        
        if not rag_results:
            stm.set_phase("recommendation_given")
            return (
                "Waduh, Mamang ga nemu makanan yang cocok nih 😢\n"
                "Coba ubah kriterianya dikit?"
            )
        
        # Store recommended foods in context
        food_names = [f["name"] for f in rag_results]
        stm.update_context({"recommended_foods": food_names})
        
        # Generate natural language response
        response = llm_reasoner.generate_recommendation(
            context,
            rag_results,
            canteen_data=None  # Could integrate canteen data here
        )

        # ====== Fallback nutrisi manual kalau data kosong ======
        for food in rag_results:
            if not food.get("calories") or food["calories"] == 0:
                name = food.get("name", "").lower()
                if "mie" in name:
                    food.update({"calories": 550, "protein": 15, "fat": 12, "carbs": 65})
                elif "ayam" in name:
                    food.update({"calories": 700, "protein": 30, "fat": 20, "carbs": 60})
                elif "nasi" in name:
                    food.update({"calories": 600, "protein": 15, "fat": 18, "carbs": 70})
                elif "kopi" in name:
                    food.update({"calories": 50, "protein": 1, "fat": 1, "carbs": 10})
                else:
                    # default ringan
                    food.update({"calories": 300, "protein": 8, "fat": 10, "carbs": 40})

        
        # Langsung hitung total nutrisi dari hasil RAG tanpa normalisasi
        nutrition = calculate_total_calories(rag_results)


        print("\n--- DEBUG NUTRITION RAW ---")
        print(nutrition)

        nutrition_text = format_nutrition_summary(nutrition)
        
        # Update phase
        stm.set_phase("recommendation_given")
        
        # Store bot response
        full_response = (
            "Tunggu sebentar, Mamang pikirin dulu yaa... 🤔\n\n"
            f"{response}\n\n"
            f"{nutrition_text}\n\n"
            "Gimana, cocok ga? Kasih feedback dong 👍 atau 👎"
        )
        
        stm.add_message("bot", full_response)
        
        return full_response
    
    def _handle_feedback_phase(
        self,
        user_id: str,
        stm: ShortTermMemory,
        ltm: LongTermMemory,
        message: str
    ) -> str:
        """Handle user feedback after recommendation"""
        
        trigger = TriggerHandler.detect_trigger(message)
        
        # Check for feedback
        if trigger == "feedback_positive":
            context = stm.get_context()
            foods = context.get("recommended_foods", [])
            
            MemoryUpdater.process_feedback(
                user_id,
                "positive",
                context,
                foods
            )
            
            stm.set_phase("idle")
            return (
                "Yeay! Seneng deh kalau cocok! 🎉\n\n"
                "Mamang bakal inget preferensi kamu buat next time.\n"
                "Kalau laper lagi tinggal bilang ya! 😋"
            )
        
        elif trigger == "feedback_negative":
            context = stm.get_context()
            foods = context.get("recommended_foods", [])
            
            MemoryUpdater.process_feedback(
                user_id,
                "negative",
                context,
                foods
            )
            
            stm.set_phase("waiting_location")
            return (
                "Oops, maaf ya ga cocok 😔\n\n"
                "Mamang bakal belajar dari ini!\n"
                "Mau coba rekomendasi lain? Fakultas mana nih?"
            )
        
        # Check for more recommendations
        if trigger == "more_recommendations":
            stm.set_phase("waiting_location")
            return "Oke siap! Mau di fakultas mana kali ini? 😊"
        
        # Check for done
        if is_full_response(message) or is_thank_you(message):
            stm.clear()
            return "Sip, wareg tenan! Kalau laper lagi tinggal bilang ya! 😋"
        
        # Ambiguous response
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