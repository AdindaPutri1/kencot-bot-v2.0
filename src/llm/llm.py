import logging
from openai import OpenAI
from src.config import Config
from typing import Dict, Any, List, Optional


logger = logging.getLogger(__name__)

client = OpenAI(
    api_key=Config.GEMINI_API_KEY,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

def build_gemini_prompt(user_data: Dict[str, Any], nearby_menus: Optional[List[Dict]] = None) -> str:
    if nearby_menus is None:
        nearby_menus = []

    faculty = user_data.get("faculty")
    hunger = user_data.get("hunger_level")
    budget = user_data.get("budget")
    time_cat = user_data.get("time_category")

    # 📝 Context dasar
    context = f"""
    Kamu adalah asisten rekomendasi makanan di UGM yang biasa dipanggil Mamang.
    User memilih Fakultas: {faculty}, lagi {hunger}, budget sekitar Rp {budget}, 
    dan sekarang waktunya {time_cat}.
    """

    # 🎯 Filter menu sesuai waktu
    menus_by_time = [m for m in nearby_menus if time_cat in m.get("suitability", [])]

    if menus_by_time:
        context += "Berikut menu yang cocok sama waktunya:\n"
        for m in menus_by_time:
            context += (
                f"- {m['menu_name']} di {m['canteen_name']} Rp {m['menu_price']} "
                f"Link: {m.get('gmaps_link','-')}\n"
            )
    else:
        # Kalau gak ada yang cocok waktu → fallback
        if nearby_menus:
            # Cek apakah hasilnya bukan dari fakultas user
            first_faculty_match = any(faculty.lower() in m["canteen_name"].lower() for m in nearby_menus)
            if not first_faculty_match:
                context += (
                    f"Mamang nggak nemu menu di sekitar {faculty}, "
                    "jadi Mamang kasih rekomendasi dari kantin fakultas lain ya 😉\n"
                )
            else:
                context += (
                    f"Waduh, kayaknya jam {time_cat} ini banyak kantin yang tutup 😅\n"
                    "Tapi tenang, Mamang masih ada alternatif buat kamu:\n"
                )

            for m in nearby_menus:
                context += (
                    f"- {m['menu_name']} di {m['canteen_name']} Rp {m['menu_price']} "
                    f"Link: {m.get('gmaps_link','-')}\n"
                )
        else:
            context += "Sayang banget, Mamang nggak nemu menu terdekat buat sekarang 😭\n"

    # 📌 Instruction ke LLM
    instruction = """
    Buat 2 rekomendasi menu yang sesuai dengan kondisi user.
    Tolong sertakan:
    - Nama menu
    - Nama kantin
    - Harga
    - Alasan kenapa cocok

    Tulis gaya santai, penuh emot, ala Mamang yang friendly.
    Jangan pakai tanda baca aneh kayak # atau ***.
    Kalau kantinnya tutup karena bukan waktunya, bilang dulu,
    terus kasih alternatif lain biar user tetep dapet rekomendasi. 😋
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
