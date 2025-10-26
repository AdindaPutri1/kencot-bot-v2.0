"""
LLM Reasoner for intelligent food recommendations
Combines RAG results with contextual reasoning
"""
import logging
from typing import Dict, List, Optional
from openai import OpenAI
from src.config import Config
from src.utils.calorie_utils import calculate_total_calories, format_nutrition_summary

logger = logging.getLogger(__name__)

class LLMReasoner:
    """LLM-based reasoning layer for recommendations"""
    
    def __init__(self):
        self.client = OpenAI(
            api_key=Config.GEMINI_API_KEY,
            base_url=Config.LLM_BASE_URL
        )
    
    def generate_recommendation(
        self,
        user_context: Dict,
        rag_results: List[Dict],
        canteen_data: Optional[List[Dict]] = None
    ) -> str:
        """
        Generate natural language recommendation
        
        Args:
            user_context: User info (faculty, hunger, budget, etc.)
            rag_results: Foods from RAG retrieval
            canteen_data: Optional canteen menu data
            
        Returns:
            Natural language recommendation text
        """
        prompt = self._build_recommendation_prompt(
            user_context,
            rag_results,
            canteen_data
        )
        
        try:
            response = self.client.chat.completions.create(
                model=Config.LLM_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.8,
                max_tokens=800
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"LLM reasoning failed: {e}", exc_info=True)
            return self._generate_fallback_response(rag_results)
    
    def _build_recommendation_prompt(
        self,
        context: Dict,
        rag_results: List[Dict],
        canteen_data: Optional[List[Dict]]
    ) -> str:
        """Build prompt for LLM"""
        
        faculty = context.get("faculty", "")
        hunger = context.get("hunger_level", "")
        budget = context.get("budget", 0)
        time_period = context.get("time_period", "")
        
        # Calculate nutrition
        nutrition = calculate_total_calories(rag_results)
        
        prompt = f"""
Kamu adalah Mamang, asisten rekomendasi makanan UGM yang ramah dan santai.

KONTEKS USER:
- Fakultas: {faculty}
- Tingkat lapar: {hunger}
- Budget: Rp {budget:,}
- Waktu: {time_period}

REKOMENDASI DARI AI (RAG):
"""
        
        for i, food in enumerate(rag_results, 1):
            prompt += f"""
{i}. {food.get('name')}
   - Kalori: {food.get('calories')} kkal
   - Protein: {food.get('protein')}g | Fat: {food.get('fat')}g | Carbs: {food.get('carbs')}g
   - Tags: {', '.join(food.get('tags', []))}
   - Similarity Score: {food.get('similarity_score', 0):.2f}
"""
        
        if canteen_data:
            prompt += "\n\nDATA KANTIN TERDEKAT:\n"
            for canteen in canteen_data[:3]:
                prompt += f"- {canteen.get('menu_name')} di {canteen.get('canteen_name')} (Rp {canteen.get('menu_price', 0):,})\n"
        
        prompt += f"""

TOTAL NUTRISI:
{format_nutrition_summary(nutrition)}

INSTRUKSI:
1. Pilih 2-3 menu terbaik dari rekomendasi di atas
2. Jelaskan kenapa cocok dengan kondisi user (lapar {hunger}, budget {budget}, waktu {time_period})
3. Kalau ada data kantin, sebutin lokasinya
4. Sebutin total kalori dan nutrisi dari pilihan kamu
5. Kasih tips nutrition yang relevan

GAYA BAHASA:
- Santai, friendly, penuh emoji 😋
- Jangan pakai markdown atau formatting aneh
- Panggil user "kamu" dan diri sendiri "Mamang"
- Bahasa gaul anak muda tapi tetap sopan

Tulis rekomendasinya sekarang!
"""
        
        return prompt
    
    def _generate_fallback_response(self, foods: List[Dict]) -> str:
        """Simple fallback if LLM fails"""
        if not foods:
            return "Waduh, Mamang ga nemu makanan yang cocok nih 😅 Coba ubah kriterianya dikit?"
        
        response = "Nih Mamang kasih rekomendasi:\n\n"
        
        for i, food in enumerate(foods[:3], 1):
            response += f"{i}. {food.get('name')} ({food.get('calories')} kkal)\n"
        
        nutrition = calculate_total_calories(foods)
        response += f"\nTotal kalori: {nutrition['total_calories']} kkal 🔥"
        
        return response
    
    def explain_reasoning(
        self,
        user_query: str,
        context: Dict,
        recommendation: str
    ) -> str:
        """
        Explain why certain recommendations were made
        (Untuk debugging atau user yang penasaran)
        """
        prompt = f"""
User nanya: "{user_query}"

Konteks user: {context}

Rekomendasi yang diberikan: {recommendation}

Jelaskan secara singkat (3-4 kalimat) logika di balik rekomendasi ini.
Gunakan bahasa yang mudah dipahami.
"""
        
        try:
            response = self.client.chat.completions.create(
                model=Config.LLM_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=200
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Reasoning explanation failed: {e}")
            return "Mamang milih berdasarkan budget, tingkat lapar, dan waktu kamu nih! 😊"

# Global instance
llm_reasoner = LLMReasoner()