"""
LLM Reasoner for intelligent food recommendations
Supports multi-model reasoning: Groq & Gemini
Combines RAG results with contextual reasoning
"""
import logging
from typing import Dict, List, Optional
from openai import OpenAI
from src.config import Config
from src.utils.calorie_utils import calculate_total_calories, format_nutrition_summary

logger = logging.getLogger(__name__)

class LLMReasoner:
    """LLM-based reasoning layer with model switching"""

    def __init__(self):
        # Client Groq (default)
        self.client_groq = OpenAI(
            api_key=Config.GROQ_API_KEY,
            base_url="https://api.groq.com/openai/v1"
        )
        # Client Gemini (Google)
        self.client_gemini = OpenAI(
            api_key=Config.GEMINI_API_KEY,
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
        )



    def generate_recommendation(
        self,
        user_context: Dict,
        rag_results: List[Dict],
        canteen_data: Optional[List[Dict]] = None,
        model: str = "groq"
    ) -> str:
        """
        Generate natural language recommendation using Groq or Gemini
        """
        prompt = self._build_recommendation_prompt(user_context, rag_results, canteen_data)

        # Pilih model dan client utama
        if model.lower() == "gemini":
            client = self.client_gemini
            model_name = "gemini-1.5-flash"
        else:
            client = self.client_groq
            model_name = "llama-3.1-8b-instant"

        # ✅ --- Bagian try-except lengkap (dengan fallback otomatis) ---
        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": "Kamu asisten lucu dan cerdas yang bantu rekomendasi makanan kampus."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,
                max_tokens=600
            )
            return response.choices[0].message.content.strip()

        except Exception as e:
            logger.warning(f"{model} gagal, fallback ke Gemini: {e}")

            # fallback otomatis ke Gemini
            try:
                response = self.client_gemini.chat.completions.create(
                    model="gemini-1.5-flash",
                    messages=[
                        {"role": "system", "content": "Kamu asisten lucu dan cerdas yang bantu rekomendasi makanan kampus."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.8,
                    max_tokens=600
                )
                return "⚡ Fallback ke Gemini:\n\n" + response.choices[0].message.content.strip()

            except Exception as e2:
                logger.error(f"Fallback gagal: {e2}")
                return self._generate_fallback_response(rag_results)

    def _build_recommendation_prompt(
        self,
        context: Dict,
        rag_results: List[Dict],
        canteen_data: Optional[List[Dict]]
    ) -> str:
        """Bangun prompt kontekstual untuk LLM"""

        faculty = context.get("faculty", "-")
        hunger = context.get("hunger_level", "-")
        budget = context.get("budget", 0)
        time_period = context.get("time_period", "-")

        nutrition = calculate_total_calories(rag_results)

        prompt = f"""
Kamu adalah Mamang, asisten rekomendasi makanan UGM yang santai, lucu, dan cerdas 😋

KONTEKS USER:
- Fakultas: {faculty}
- Tingkat lapar: {hunger}
- Budget: Rp {budget:,}
- Waktu: {time_period}

DAFTAR MAKANAN DARI RAG:
"""
        for i, food in enumerate(rag_results[:5], 1):
            prompt += f"""
{i}. {food.get('name')}
   - Harga: Rp {food.get('price', 0):,}
   - Kalori: {food.get('calories', '?')} kkal
   - Protein: {food.get('protein', '?')}g | Lemak: {food.get('fat', '?')}g | Karbo: {food.get('carbs', '?')}g
   - Kantin: {food.get('canteen_name', 'Tidak diketahui')}
"""

        if canteen_data:
            prompt += "\nKANTIN TERDEKAT:\n"
            for c in canteen_data[:3]:
                prompt += f"- {c.get('menu_name')} di {c.get('canteen_name')} (Rp {c.get('menu_price', 0):,})\n"

        prompt += f"""

TOTAL NUTRISI:
{format_nutrition_summary(nutrition)}

INSTRUKSI UNTUK KAMU (LLM):
1. Pilih 2–3 menu terbaik yang sesuai konteks (lapar, budget, waktu, fakultas)
2. Jelaskan kenapa cocok — dengan gaya Gen-Z yang asik tapi jelas
3. Kalau bisa, tambahkan tips kecil tentang gizi atau porsi
4. Jangan pakai markdown, cukup teks biasa dengan emoji
5. Bahasa santai tapi tetap sopan, panggil user "kamu" dan sebut diri "Mamang"
"""

        return prompt.strip()

    def _generate_fallback_response(self, foods: List[Dict]) -> str:
        """Fallback kalau LLM error"""
        if not foods:
            return "Waduh, Mamang ga nemu makanan yang cocok nih 😅 Coba ubah kriterianya dikit?"

        response = "😅 AI-nya lagi istirahat, tapi nih Mamang bantu dulu manual:\n\n"
        for i, food in enumerate(foods[:3], 1):
            response += f"{i}. {food.get('name')} - Rp {food.get('price', 0):,}\n"
        nutrition = calculate_total_calories(foods)
        response += f"\nTotal kalori: {nutrition['total_calories']} kkal 🔥"
        return response

    def explain_reasoning(self, user_query: str, context: Dict, recommendation: str, model: str = "groq") -> str:
        """Menjelaskan alasan di balik rekomendasi (debugging/penjelasan opsional)"""
        prompt = f"""
User nanya: "{user_query}"
Konteks user: {context}
Rekomendasi diberikan: {recommendation}

Jelaskan secara singkat (3 kalimat) alasan logis di balik rekomendasi ini, dengan bahasa ringan.
"""

        try:
            if model == "gemini":
                client = self.client_gemini
                model_name = "gemini-1.5-flash"
            else:
                client = self.client_groq
                model_name = "llama3-8b-8192"

            response = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.6,
                max_tokens=200
            )
            return response.choices[0].message.content.strip()

        except Exception as e:
            logger.error(f"Explain reasoning failed: {e}")
            return "Mamang milih berdasarkan budget, tingkat lapar, dan waktu kamu nih 😋"

# Global instance
llm_reasoner = LLMReasoner()
