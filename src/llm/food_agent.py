"""
Food Recommendation Agent with Multi-Step Reasoning
Agentic approach: Plan → Retrieve → Reason → Format
"""
import logging
from typing import Dict, List, Optional
from openai import OpenAI
from src.config import Config
from src.utils.response_formatter import response_formatter

logger = logging.getLogger(__name__)

class FoodRecommendationAgent:
    """Agentic LLM for food recommendations with reasoning"""
    
    def __init__(self):
        # Initialize both clients
        self.client_groq = OpenAI(
            api_key=Config.GROQ_API_KEY,
            base_url="https://api.groq.com/openai/v1"
        )
        self.client_gemini = OpenAI(
            api_key=Config.GEMINI_API_KEY,
            base_url=Config.LLM_BASE_URL
        )
        logger.info("✅ Food Agent initialized with multi-model support")
    
    def generate_recommendation_with_agent(
        self,
        user_context: Dict,
        rag_results: List[Dict],
        model: str = "groq",
        show_reasoning: bool = False
    ) -> str:
        """
        Generate recommendation using agentic approach
        
        Steps:
        1. PLAN: Understand user needs
        2. RETRIEVE: Already done (rag_results)
        3. REASON: Analyze and select best options
        4. FORMAT: Create friendly response
        """
        
        # Step 1: Planning Phase
        plan = self._create_plan(user_context, model)
        
        if show_reasoning:
            logger.info(f"🧠 Agent Plan: {plan}")
        
        # Step 2 & 3: Reasoning Phase
        reasoning = self._reason_about_foods(user_context, rag_results, plan, model)
        
        if show_reasoning:
            logger.info(f"💭 Agent Reasoning: {reasoning}")
        
        # Step 4: Formatting Phase
        if rag_results:
            # 🔥 Normalize dulu biar data nutrition bener
            clean_foods = self._normalize_food_data(rag_results)

            formatted = response_formatter.format_whatsapp_style(clean_foods[:3])
            
            intro = self._generate_intro(user_context, reasoning, model)
            return f"{intro}\n\n{formatted}"
        else:
            # No results - agent suggests alternatives
            return self._generate_fallback(user_context, model)
    
    def _create_plan(self, context: Dict, model: str) -> str:
        """Step 1: Create action plan based on context"""
        prompt = f"""
Kamu adalah AI Agent yang harus membuat rencana untuk merekomendasikan makanan.

KONTEKS USER:
- Fakultas: {context.get('faculty')}
- Tingkat lapar: {context.get('hunger_level')}
- Budget: Rp {context.get('budget', 0):,}
- Waktu: {context.get('time_period')}

TUGAS: Buat rencana singkat (2-3 poin) untuk mencari makanan yang cocok.

Format:
1. Fokus pada ...
2. Prioritaskan ...
3. Hindari ...

Jawab singkat dalam Bahasa Indonesia.
"""
        
        try:
            client = self._get_client(model)
            model_name = self._get_model_name(model)
            
            response = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.5,
                max_tokens=200
            )
            
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Plan creation failed: {e}")
            return "Fokus pada budget dan tingkat lapar user."
    
    def _reason_about_foods(
        self,
        context: Dict,
        foods: List[Dict],
        plan: str,
        model: str
    ) -> str:
        """Step 3: Reason about which foods to recommend"""
        
        if not foods:
            return "Tidak ada makanan yang ditemukan."
        
        foods_summary = "\n".join([
            f"- {f['name']} (Rp {f.get('price', 0):,}, "
            f"{f.get('calories', '?')} kkal, {f.get('canteen_name', 'Kantin')})"
            for f in foods[:5]
        ])
        
        prompt = f"""
Kamu adalah AI Agent yang sedang menganalisis pilihan makanan untuk user.

RENCANA:
{plan}

KONTEKS USER:
- Budget: Rp {context.get('budget', 0):,}
- Tingkat lapar: {context.get('hunger_level')}
- Waktu: {context.get('time_period')}

PILIHAN MAKANAN:
{foods_summary}

TUGAS: Analisis dan pilih 2-3 makanan terbaik. Jelaskan singkat kenapa cocok.

Format:
Pilihan 1: [nama] - [alasan]
Pilihan 2: [nama] - [alasan]

Jawab singkat dalam Bahasa Indonesia casual.
"""
        
        try:
            client = self._get_client(model)
            model_name = self._get_model_name(model)
            
            response = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=300
            )
            
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Reasoning failed: {e}")
            return "Pilihan terbaik berdasarkan budget dan preferensi kamu."
    
    def _generate_intro(self, context: Dict, reasoning: str, model: str) -> str:
        """Generate friendly intro based on reasoning"""
        prompt = f"""
User cari makanan dengan budget Rp {context.get('budget', 0):,} di {context.get('faculty')}.

Hasil analisis AI:
{reasoning}

Buat 1 kalimat pembuka yang friendly dan natural, tanpa emoji berlebihan.
Contoh: "Oke nih, Mamang udah cariin yang paling pas buat kamu!"

Jawab HANYA 1 kalimat pembuka saja.
"""
        
        try:
            client = self._get_client(model)
            model_name = self._get_model_name(model)
            
            response = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.8,
                max_tokens=100
            )
            
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.warning(f"Intro generation failed: {e}")
            return "Oke nih, Mamang udah cariin yang paling pas buat kamu! 😋"
    
    def _generate_fallback(self, context: Dict, model: str) -> str:
        """Generate fallback when no results found"""
        prompt = f"""
User cari makanan tapi ga ada hasil yang cocok.
Budget: Rp {context.get('budget', 0):,}
Fakultas: {context.get('faculty')}

Buat pesan yang:
1. Mengakui ga ada hasil
2. Kasih saran alternatif (naikin budget/ganti waktu/fakultas lain)
3. Tetap friendly dan helpful

Maksimal 3 kalimat, gaya casual Gen-Z.
"""
        
        try:
            client = self._get_client(model)
            model_name = self._get_model_name(model)
            
            response = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.8,
                max_tokens=200
            )
            
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Fallback generation failed: {e}")
            return (
                "Waduh, Mamang ga nemu yang cocok nih 😢\n"
                "Coba naikin budget dikit atau pilih fakultas lain ya!"
            )
    
    def _get_client(self, model: str):
        """Get appropriate client"""
        return self.client_gemini if model.lower() == "gemini" else self.client_groq
    
    def _get_model_name(self, model: str) -> str:
        """Get model name"""
        if model.lower() == "gemini":
            return Config.LLM_MODEL
        return "llama-3.1-8b-instant"

# Global agent instance
food_agent = FoodRecommendationAgent()