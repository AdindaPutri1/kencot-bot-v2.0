import logging
from typing import Dict

logger = logging.getLogger(__name__)

def parse_intent(message: str) -> Dict[str, str]:
    """
    Tentukan intent utama user dari pesan teks.
    """
    message_lower = message.lower()
    intent = "unknown"

    if any(word in message_lower for word in ["lapar", "makan", "rekomendasi", "menu", "kencot"]):
        intent = "food_recommendation"
    elif any(word in message_lower for word in ["hai", "halo", "pagi", "siang", "malam"]):
        intent = "greeting"
    elif any(word in message_lower for word in ["makasih", "thanks", "terima kasih"]):
        intent = "gratitude"
    elif "lokasi" in message_lower or "dimana" in message_lower:
        intent = "location_query"
    
    logger.info(f"Detected intent: {intent}")
    return {"intent": intent}
