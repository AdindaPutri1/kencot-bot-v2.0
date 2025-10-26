import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

def analyze_context(message: str) -> Dict[str, Any]:
    """
    Analisis konteks percakapan user dari pesan teks.
    """
    message_lower = message.lower()
    context = {}

    # Deteksi waktu (pagi, siang, sore, malam)
    if any(word in message_lower for word in ["pagi", "breakfast", "sarapan"]):
        context["time_category"] = "pagi"
    elif any(word in message_lower for word in ["siang", "lunch", "makan siang"]):
        context["time_category"] = "siang"
    elif any(word in message_lower for word in ["sore", "malam", "dinner", "makan malam"]):
        context["time_category"] = "malam"
    else:
        context["time_category"] = "tidak diketahui"

    # Deteksi emosi user
    if any(word in message_lower for word in ["lapar", "laper", "kenyang", "ngantuk"]):
        context["hunger_level"] = "lapar"
    else:
        context["hunger_level"] = "biasa aja"

    # Deteksi fakultas
    if "fisip" in message_lower:
        context["faculty"] = "FISIPOL"
    elif "teknik" in message_lower:
        context["faculty"] = "Teknik"
    elif "fkg" in message_lower:
        context["faculty"] = "Kedokteran Gigi"
    else:
        context["faculty"] = "tidak diketahui"

    logger.info(f"Context analyzed: {context}")
    return context
