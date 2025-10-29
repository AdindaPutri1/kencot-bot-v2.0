import logging
import json
from typing import Dict, List
from openai import OpenAI

from src.utils.query_parser import parse_user_query
from src.memory.memory_manager import MemoryManager
from src.utils.nutrition_api import NutritionTool
from src.utils.config import Config
from src.database.models.food_db import FoodDB
from src.rag.retrieval_engine import RetrievalEngine
from src.utils.nutrition_estimator import NutritionEstimator


logger = logging.getLogger(__name__)

class FoodAgent:
    def __init__(self):
        self.memory = MemoryManager()
        self.nutrition_tool = NutritionTool()
        self.food_db = FoodDB()
        self.food_db.load_from_json(Config.DATABASE_PATH)

        self.rag_engine = RetrievalEngine()
        self.client_gemini = OpenAI(
            api_key=Config.GEMINI_API_KEY,
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
        )
        self.model = "gemini-2.5-flash"

    # ========================== MAIN ==========================
    def process(self, user_id: str, session_id: str, user_input: str) -> dict:
        logger.info(f"[PROCESS] User {user_id} | Session {session_id} | Input: {user_input}")

        # --- Parsing query ---
        parsed = parse_user_query(user_input)
        context = self.memory.get_context(user_id, session_id)

        # --- Tambahkan konteks STM (riwayat percakapan aktif) ---
        stm_history = self.memory.stm.get_messages(session_id) if hasattr(self.memory, "stm") else []
        combined_context = {
            "stm": stm_history,
            "ltm": context.get("ltm", {}),
            "parsed": parsed,
            "raw_input": user_input
        }

        # --- 1️⃣ Update memory (deteksi alergi/dislike) ---
        memory_update_prompt = self.build_memory_update_prompt(user_input, combined_context)
        memory_update = self.call_llm(memory_update_prompt)
        self.apply_memory_update(user_id, memory_update)

        # --- 2️⃣ Decision phase ---
        menus = self.food_db.get_all_menus()
        decision_prompt = self.build_decision_prompt(user_input, menus, combined_context)
        llm_decision = self.call_llm(decision_prompt)

        decision_type = llm_decision.get("search_method", "")
        recommended_food_name = llm_decision.get("recommendation", "Tidak ada rekomendasi")
        call_nutrition = llm_decision.get("call_nutrition", False)

        logger.debug(f"[DECISION] Type: {decision_type}, Food: {recommended_food_name}")

        # --- 3️⃣ Get final recommendation ---
        final_recommendation = None
        rag_used = False

        if decision_type == "database":
            for item in menus:
                if item["menu_name"].lower() == recommended_food_name.lower():
                    final_recommendation = item
                    break

        elif decision_type == "rag":
            rag_used = True
            rag_results = self.rag_engine.search(recommended_food_name, top_k=3)
            final_recommendation = rag_results[0] if rag_results else {"name": "Tidak ada rekomendasi"}

        if not final_recommendation:
            final_recommendation = {"name": "Tidak ada rekomendasi"}

        # --- 4️⃣ Tambahkan ke LTM liked_foods otomatis ---
        if final_recommendation.get("menu_name") not in ["Tidak ada rekomendasi", None]:
            food_name = final_recommendation.get("menu_name") 
            if food_name:
                self.memory.add_liked_food(user_id, food_name)
                logger.info(f"[LTM] Added to liked_foods: {food_name}")

        # --- 5️⃣ Nutrisi ---
        nutrition = {}
        if call_nutrition and final_recommendation.get("menu_name") != "Tidak ada rekomendasi":
            nutrition = self.nutrition_tool.get_nutrition(final_recommendation.get("menu_name"))

        # hitung kalori fallback
        nutrition["calories"] = self.compute_calories(nutrition)


        # --- 6️⃣ Reasoning ke user ---
        reasoning_prompt = self.build_reasoning_prompt(
            user_input, llm_decision, final_recommendation, nutrition, rag_used, combined_context
        )
        reasoning = self.call_llm_reasoning(reasoning_prompt)

        # --- 7️⃣ Update STM (conversation context) ---
        self.memory.stm.add_message(session_id, "user", user_input)
        self.memory.stm.add_message(session_id, "bot", reasoning)

        # --- Simpan konteks ke memory ---
        self.memory.save_context(user_id, session_id, combined_context)

        # --- Return hasil ---
        return {
            "recommendation": final_recommendation,
            "nutrition": nutrition,
            "reasoning": reasoning,
            "decision_type": decision_type,
            "tool_used": "FoodDB" if not rag_used else "RAG",
            "ltm_used": bool(context.get("ltm")),
        }
    
    def compute_calories(self, nutrition: dict) -> float:
        """
        Hitung kalori makanan menggunakan NutritionEstimator.
        Fallback kalau data protein/carb/fat tidak tersedia.
        """
        protein = nutrition.get("protein_g")
        carbs = nutrition.get("carbohydrates_total_g")
        fat = nutrition.get("fat_total_g")

        # fallback default
        if protein is None or protein == "Only available for premium subscribers":
            protein = 5.0
        if carbs is None:
            carbs = 32.4
        if fat is None:
            fat = 2.9

        try:
            protein = float(protein)
        except (ValueError, TypeError):
            protein = 5.0
        try:
            carbs = float(carbs)
        except (ValueError, TypeError):
            carbs = 32.4
        try:
            fat = float(fat)
        except (ValueError, TypeError):
            fat = 2.9

        return NutritionEstimator.estimate_calories(protein_g=protein, carbs_g=carbs, fat_g=fat)


    # ========================== MEMORY UPDATE ==========================
    def build_memory_update_prompt(self, user_input: str, context: Dict) -> str:
        return f"""
Kamu adalah sistem deteksi preferensi makanan user.

User input: "{user_input}"
Context: {json.dumps(context, ensure_ascii=False, default=str)}

Tugasmu:
1. Jika user menyebut makanan yang tidak disukai → masukkan ke "disliked_foods".
2. Jika user menyebut alergi terhadap makanan/bahan tertentu → masukkan ke "allergies".
3. Jika tidak ada, kosongkan array-nya.
4. Jawab hanya dalam format JSON seperti ini:
{{
  "disliked_foods": ["<nama makanan>"],
  "allergies": ["<alergen>"]
}}
        """

    def apply_memory_update(self, user_id: str, update: dict):
        """Tambahkan hasil deteksi LLM ke LTM dengan log debugging."""
        if not isinstance(update, dict):
            logger.warning(f"[MEMORY] Invalid memory update: {update}")
            return

        allergies = update.get("allergies", [])
        disliked = update.get("disliked_foods", [])

        if allergies:
            logger.info(f"[LTM] Adding allergies for {user_id}: {allergies}")
            for item in allergies:
                self.memory.add_allergy(user_id, item)

        if disliked:
            logger.info(f"[LTM] Adding disliked foods for {user_id}: {disliked}")
            for food in disliked:
                self.memory.add_disliked_food(user_id, food)

    # ========================== DECISION & REASONING ==========================
    def build_decision_prompt(self, user_input: str, menus: List[Dict], context: Dict) -> str:
        stm_text = "\n".join([f"{m['role']}: {m.get('content', m.get('message', ''))}" for m in context.get("stm", [])])
        menus_text = "\n".join([f"- {m['menu_name']}" for m in menus])
        return f"""
Kamu adalah asisten makanan cerdas di UGM.

Percakapan sebelumnya:
{stm_text if stm_text else "(belum ada percakapan sebelumnya)"}

User query: "{user_input}"
Context (LTM & parsed query): {json.dumps(context, ensure_ascii=False, default=str)}

Daftar menu dari database:
{menus_text}

Tugasmu:
1. Gunakan konteks percakapan sebelumnya (STM) dan preferensi user (LTM).
2. Jika makanan yang diminta user ada di daftar menu, gunakan:
   "search_method": "database"
3. Jika tidak ada → gunakan:
   "search_method": "rag" dan berikan nama makanan yang paling mirip.
4. Jika makanan mengandung bahan yang ada di daftar alergi dan disliked_foods user → jangan rekomendasikan.
5. Jika kamu memilih menu valid (bukan "Tidak ada rekomendasi"), tuliskan **selalu** "call_nutrition": true.
6. Output dalam JSON valid:
{{
  "search_method": "database" atau "rag",
  "recommendation": "<nama makanan>",
  "call_nutrition": true
}}
        """

    def build_reasoning_prompt(self, user_input: str, decision: Dict, food: Dict, nutrition: Dict, rag_used: bool, context: Dict) -> str:
        food_name = food.get("name") or food.get("menu_name") or "Tidak ada rekomendasi"
        canteen = food.get("canteen") or food.get("canteen_name", "Tidak diketahui")
        price = food.get("price", "Tidak diketahui")
        suitability = ", ".join(food.get("suitability", [])) or "Tidak diketahui"
        maps_link = food.get("gmaps_link") or "Tidak tersedia"
        method = "RAG retrieval" if rag_used else "database.json"

        stm_text = "\n".join([f"{m['role']}: {m.get('content', m.get('message', ''))}" for m in context.get("stm", [])])
        liked_foods = context.get("ltm", {}).get("liked_foods", [])
        allergies = context.get("ltm", {}).get("allergies", [])
        disliked_foods = context.get("ltm", {}).get("disliked_foods", [])

        return f"""
User query: "{user_input}"
LLM Decision: {json.dumps(decision, ensure_ascii=False, default=str)}
Source: {method}

Makanan direkomendasikan:
- Nama: {food_name}
- Kantin: {canteen}
- Harga: Rp{price}
- Ketersediaan: {suitability}
- Lokasi Maps: {maps_link}

Nutrition info: {nutrition if nutrition else 'Tidak ada data nutrisi'}

Dari percakapan sebelumnya:
{stm_text if stm_text else "(belum ada percakapan sebelumnya)"}

Liked foods user: {liked_foods}
Allergies user: {allergies}
Disliked foods user: {disliked_foods}

Tugas:
1. Jelaskan kenapa makanan itu cocok direkomendasikan berdasarkan konteks dan preferensi user misal ada di makanan kesukaannya.
2. Jika hasil dari RAG, beri tahu user bahwa itu hasil pencarian mirip.
3. Jika user bertanya "ingat ga tadi aku dapet rekomendasi makanan apa aja", sebutkan semua makanan yang sudah direkomendasikan sebelumnya dari STM.
4. Sertakan alasan kenapa makanan itu cocok berdasarkan liked_foods, allergies, dan disliked_foods.
5. Gunakan gaya ramah dan natural tanpa format JSON.
        """

    # ========================== LLM CALLS ==========================
    def call_llm(self, prompt: str) -> dict:
        try:
            response = self.client_gemini.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7
            )

            raw = response.choices[0].message.content
            if not raw:
                return {}

            raw = raw.strip()
            if raw.startswith("```json"):
                raw = raw[7:-3].strip()
            elif raw.startswith("```"):
                raw = raw[3:-3].strip()

            return json.loads(raw)
        except Exception as e:
            logger.error(f"[LLM] Call error: {e}", exc_info=True)
            return {}

    def call_llm_reasoning(self, prompt: str) -> str:
        try:
            response = self.client_gemini.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"[LLM Reasoning] Error: {e}", exc_info=True)
            return "Maaf, reasoning gagal dihasilkan."
        

