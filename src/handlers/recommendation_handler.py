import logging
from typing import Dict, Any, List
from .llm_handler import ask_gemini
from .context_analyzer import analyze_context
from .intent_parser import parse_intent
from .trigger_handler import handle_trigger

logger = logging.getLogger(__name__)

def handle_recommendation(message: str, nearby_menus: List[Dict]) -> str:
    """
    Tangani alur lengkap: analisis → intent → LLM rekomendasi.
    """
    context = analyze_context(message)
    intent = parse_intent(message)["intent"]
    
    # Coba trigger cepat dulu
    trigger_response = handle_trigger(intent)
    if trigger_response:
        return trigger_response

    if intent == "food_recommendation":
        logger.info("Running LLM recommendation flow...")
        return ask_gemini(context, nearby_menus)
    else:
        return "Hehe, Mamang belum paham maksudmu 😅. Coba bilang 'Mamang, aku laper dong!'"
