"""
Core utilities for Kencot Bot.
Handles data loading, fallback, and food recommendation logic.
"""

import json
import random
import logging
from typing import Dict, List, Any

from src.utils.text_utils import extract_faculty_from_text, extract_budget_from_text, extract_hunger_level_from_text
from .time_utils import get_current_time_period
from src.llm.llm import ask_gemini


logger = logging.getLogger(__name__)


def load_database(file_path: str) -> List[Dict[str, Any]]:
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("ugm_canteens", [])
    except Exception as e:
        logger.error(f"Error loading database: {e}")
        return []

def find_recommendations(all_canteens: List[Dict], faculty: str, budget: int, hunger_level: str) -> List[Dict]:
    time_period = get_current_time_period()
    hunger_map = {
        "brutal": ["makanan_berat"],
        "standar": ["makanan_berat", "makanan_ringan"],
        "iseng": ["cemilan", "makanan_ringan", "minuman"]
    }
    allowed = hunger_map.get(hunger_level, [])

    nearby = [c for c in all_canteens if faculty in c.get("faculty_proximity", [])]
    if not nearby:
        logger.warning(f"No nearby canteens found for faculty {faculty}")
        return []

    matches = []
    for c in nearby:
        for m in c.get("menus", []):
            
            # --- START PERBAIKAN LOGIKA WAKTU ---
            menu_suitability = m.get("suitability", [])
            
            # is_time_ok: True jika suitability list kosong (selalu tersedia) 
            # ATAU jika waktu saat ini (time_period) ada di dalam list.
            is_time_ok = (not menu_suitability) or (time_period in menu_suitability)
            # --- END PERBAIKAN LOGIKA WAKTU ---
            
            is_budget_ok = m.get("price", 999999) <= budget
            is_category_ok = m.get("category") in allowed
            
            # Menggunakan is_time_ok yang sudah diperbaiki
            if is_budget_ok and is_category_ok and is_time_ok: 
                matches.append({
                    "canteen_name": c.get("canteen_name"),
                    "menu_name": m.get("name"),
                    "menu_price": m.get("price"),
                    "gmaps_link": c.get("gmaps_link")
                })

    random.shuffle(matches)

    if not matches:
        try:
            user_data = {"faculty": faculty, "budget": budget, "hunger_level": hunger_level, "time_category": time_period}
            # Fallback ke AI (Gemini)
            ai_result = ask_gemini(user_data, nearby)
            if ai_result:
                return [{"canteen_name": "AI Mamang 🤖", "menu_name": ai_result, "menu_price": "-", "gmaps_link": None}]
        except Exception as e:
            logger.error(f"AI fallback failed: {e}")

    return matches[:2]
