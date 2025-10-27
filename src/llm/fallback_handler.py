"""
Fallback handler for LLM failures
"""
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class FallbackHandler:
    """Handle LLM failures with graceful fallbacks"""
    
    @staticmethod
    def generate_simple_recommendation(foods: List[Dict], context: Dict) -> str:
        """Generate simple text recommendation without LLM"""
        if not foods:
            return FallbackHandler.no_results_message(context)
        
        budget = context.get("budget", 0)
        hunger = context.get("hunger_level", "standar")
        
        intro = f"Oke, dengan budget Rp {budget:,} dan tingkat lapar {hunger}, nih Mamang kasih rekomendasi:\n\n"
        
        items = []
        for i, food in enumerate(foods[:3], 1):
            name = food.get("name", "Makanan")
            price = food.get("price", 0)
            canteen = food.get("canteen_name", "Kantin")
            
            items.append(f"{i}. {name} - Rp {price:,}\n   📍 {canteen}")
        
        return intro + "\n".join(items) + "\n\nGaskeun cobain! 😋"
    
    @staticmethod
    def no_results_message(context: Dict) -> str:
        """Message when no foods found"""
        budget = context.get("budget", 0)
        
        if budget < 5000:
            return (
                "Waduh, budget Rp {budget:,} kayaknya agak susah nih 😅\n"
                "Coba naikin dikit jadi minimal 5k ya!"
            )
        
        return (
            "Waduh, Mamang ga nemu makanan yang cocok nih 😢\n"
            "Coba ubah kriterianya dikit ya:\n"
            "- Naikin budget dikit\n"
            "- Pilih waktu lain\n"
            "- Coba fakultas terdekat"
        )
    
    @staticmethod
    def ai_error_message() -> str:
        """Message when AI fails"""
        return (
            "😅 AI-nya lagi istirahat nih.\n"
            "Tapi tenang, Mamang tetap bisa kasih rekomendasi manual!\n"
            "Coba ulangi ya 😊"
        )
    
    @staticmethod
    def format_nutrition_simple(food: Dict) -> str:
        """Simple nutrition format"""
        cal = food.get("calories", 0)
        protein = food.get("protein", 0)
        
        if cal or protein:
            return f"🔥 {cal} kkal | 💪 {protein}g protein"
        return ""


# Global instance
fallback_handler = FallbackHandler()