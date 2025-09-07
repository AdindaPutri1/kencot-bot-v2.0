import logging
from openai import OpenAI
from .config import Config
from typing import Dict, Any


logger = logging.getLogger(__name__)

# Inisialisasi client pakai API Key dari .env
client = OpenAI(
    api_key=Config.GEMINI_API_KEY,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

def build_gemini_prompt(user_data: Dict[str, Any], nearby_menus: list = []):
    faculty = user_data.get("faculty")
    hunger = user_data.get("hunger_level")
    budget = user_data.get("budget")
    time_cat = user_data.get("time_category")

    context = f"""
Kamu adalah asisten rekomendasi makanan di UGM.
User memilih Fakultas: {faculty}, sedang {hunger}, budget sekitar Rp {budget}, dan saat ini waktu {time_cat}.
"""
    if nearby_menus:
        context += "Berikut menu yang ada di database:\n"
        for m in nearby_menus:
            context += f"- {m['menu_name']} di {m['canteen_name']} Rp {m['menu_price']}\n"

    instruction = """
Buat 2 rekomendasi menu makanan yang sesuai kondisi user.
Sertakan:
- Nama menu
- Nama kantin
- Harga
- Alasan kenapa cocok
- Link Google Maps jika ada
Tulis gaya santai, friendly.
"""
    return context + instruction

def ask_gemini(user_data, nearby_menus=[]):
    prompt = build_gemini_prompt(user_data, nearby_menus)

    try:
        response = client.chat.completions.create(
            model="gemini-2.5-flash",
            messages=[{"role": "user", "content": prompt}],
        )

        logger.info(f"Gemini response raw: {response}")

        choice = response.choices[0]
        if hasattr(choice.message, "content"):
            return choice.message.content
        elif isinstance(choice.message, dict) and "content" in choice.message:
            return choice.message["content"]
        else:
            return "⚠️ Mamang ga dapet jawaban dari Gemini."
    except Exception as e:
        logger.error("Gagal connect ke Gemini", exc_info=True)
        return "Maaf, Mamang lagi sibuk nih, coba beberapa saat lagi ya 😅"
