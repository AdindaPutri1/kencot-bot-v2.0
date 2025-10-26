"""
Fallback handler for LLM failures or incomplete responses.
Handles graceful degradation when reasoning or generation fails.
"""

import logging
from typing import List, Dict, Optional
from src.utils.calorie_utils import calculate_total_calories, format_nutrition_summary

logger = logging.getLogger(__name__)


class FallbackHandler:
    """
    Fallback layer for LLM or API errors.
    Designed to keep user experience smooth with humor & contextual awareness.
    """

    def __init__(self):
        self.default_responses = [
            "Waduh, Mamang lagi ngantuk nih, coba lagi bentar ya 😴",
            "Server lagi laper juga nih, sabar bentar ya 🍜",
            "Hmm, kayaknya jaringan lagi lemot... tapi Mamang tetep usahain buat bantuin 💪",
        ]

    def handle_reasoning_failure(
        self,
        user_context: Dict,
        rag_results: Optional[List[Dict]] = None
    ) -> str:
        """
        Generate a fallback recommendation if reasoning fails.
        """

        faculty = user_context.get("faculty", "fakultas kamu")
        hunger = user_context.get("hunger_level", "lapar")
        budget = user_context.get("budget", 0)

        if not rag_results:
            msg = (
                f"😅 Mamang belum nemu makanan yang cocok buat kamu di sekitar {faculty}. "
                f"Coba naikin dikit budget-nya (Rp {budget:,}) atau pilih fakultas lain deh 😉"
            )
            logger.warning("Fallback triggered: no RAG results.")
            return msg

        # Ambil top 3 hasil
        selected_foods = rag_results[:3]
        nutrition = calculate_total_calories(selected_foods)

        msg = f"Tenang, Mamang tetep punya rekomendasi buat kamu nih 😋\n\n"

        for i, food in enumerate(selected_foods, 1):
            msg += f"{i}. {food.get('name')} - {food.get('calories', 0)} kkal\n"

        msg += f"\nTotal kalori: {nutrition['total_calories']} kkal 🔥"
        msg += f"\nCocok buat kamu yang lagi {hunger} dan punya budget sekitar Rp {budget:,} 💸"

        return msg

    def handle_connection_error(self, error: Exception) -> str:
        """
        Fallback for API/connection errors (e.g., Gemini down, network issues).
        """
        logger.error(f"LLM connection error: {error}", exc_info=True)
        return (
            "⚠️ Mamang lagi susah connect ke server nih 😭 "
            "Mungkin jaringannya ngambek. Coba lagi bentar ya!"
        )

    def handle_unexpected_response(self, raw_response: Optional[Dict] = None) -> str:
        """
        Fallback for weird or incomplete model responses.
        """
        logger.warning(f"Unexpected LLM response: {raw_response}")
        return (
            "Heh, Mamang dikasih jawaban aneh sama AI 😅 "
            "Coba ulang lagi, nanti Mamang pastiin hasilnya lebih mantap!"
        )

    def random_idle_message(self) -> str:
        """
        Random playful message to keep bot personality alive during idle or wait time.
        """
        import random
        return random.choice(self.default_responses)


# Global instance
fallback_handler = FallbackHandler()
