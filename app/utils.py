# app/utils.py
"""
Utility functions for Kencot Bot.
This is the core engine for data extraction, filtering, and response formatting.
"""

import re
import json
import random
import logging
from difflib import get_close_matches
from datetime import datetime
from typing import Dict, List, Optional, Any


logger = logging.getLogger(__name__)

# --- Data Loading Functions ---

def load_database(file_path: str) -> List[Dict[str, Any]]:
    """Load canteen database from JSON file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            logger.info(f"Database loaded successfully from {file_path}")
            return data.get("ugm_canteens", [])
    except FileNotFoundError:
        logger.error(f"FATAL: Database file not found at {file_path}")
        return []
    except json.JSONDecodeError as e:
        logger.error(f"FATAL: Error parsing database JSON: {str(e)}")
        return []

def load_responses(file_path: str) -> Dict[str, Any]:
    """Load response templates from a JSON file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.warning(f"Could not load responses from {file_path}. Using defaults. Error: {e}")
        return {
            "greetings": ["Halo bestie! Ada yang laper nih kayaknya 👀"],
            "location_ask": ["Posisi kamu dimana nih? Kasih tau fakultasnya ya biar ga jauh-jauh jalan."],
            "location_ask_fail": ["Hmm, fakultas mana ya? Coba sebutin yang lebih spesifik kayak 'Teknik' atau 'MIPA'."],
            "hunger_level_ask": {
                "question": "Siap! Nah sekarang tingkat kelaparanmu gimana nih?",
                "options": {
                    "A": "Laper brutal (butuh nasi porsi kuli)",
                    "B": "Laper standar (yang penting kenyang)",
                    "C": "Cuma iseng (pengen ngunyah aja)"
                }
            },
            "hunger_ask_fail": ["Pilih A, B, atau C aja ya bestie! 😊\nA. Laper brutal\nB. Laper standar\nC. Cuma iseng"],
            "budget_ask": ["Okay noted! Terakhir nih, budget kamu berapaan? Tenang, aku cariin yang paling worth it 💰"],
            "budget_ask_fail": ["Hmm, ga kedetect budgetnya. Coba bilang angkanya ya, misal: 10k, 20 ribu, atau 15000."],
            "agree_ask_fail": ["Mamang ga ngerti maksudmu 🤔. Coba jawab *iya* atau *nggak* aja ya!"],
            "no_result": ["Waduh, kayaknya kombinasi pencarianmu ga nemu apa-apa nih 😢. Coba deh ganti kriteria, mungkin budgetnya digedein dikit?"],
            "error": ["Aduh, mamang lagi error nih 😵 Coba chat lagi dalam beberapa saat ya!"]
        }

# --- Entity Extraction Functions ---

def make_flexible_pattern(word: str) -> str:
    """
    Bikin regex fleksibel:
    - Huruf bisa dobel/triple.
    - Huruf boleh hilang (kurang satu).
    """
    pattern = "".join([f"{c}+" if c.isalpha() else c for c in word])
    return r"\b" + pattern + r"\b"


FACULTY_PATTERNS = {
    "Teknik": [make_flexible_pattern("teknik"), r"\bft\b", r"\bdteti\b"],
    "MIPA": [make_flexible_pattern("mipa"), r"\bfmipa\b"],
    "FKKMK": [make_flexible_pattern("fkkmk"), make_flexible_pattern("kedokteran"), make_flexible_pattern("fk")],
    "Pertanian": [make_flexible_pattern("pertanian"), r"\bfaperta\b"],
    "Filsafat": [make_flexible_pattern("filsafat"), r"\bbonbin\b"],
    "Pascasarjana": [make_flexible_pattern("pascasarjana"), make_flexible_pattern("pasca")],
    "Psikologi": [make_flexible_pattern("psikologi"), make_flexible_pattern("psiko")],
    "Farmasi": [make_flexible_pattern("farmasi"), make_flexible_pattern("pharmasi")],
    "Kehutanan": [make_flexible_pattern("kehutanan"), r"\bfkt\b"],
    "Peternakan": [make_flexible_pattern("peternakan"), r"\bfapet\b"],
    "Geografi": [make_flexible_pattern("geografi"), make_flexible_pattern("geographi")],
    "FEB": [make_flexible_pattern("feb"), make_flexible_pattern("ekonomi"), make_flexible_pattern("ekon")],
    "Hukum": [make_flexible_pattern("hukum"), r"\bfh\b"],
    "Fisipol": [make_flexible_pattern("fisipol"), make_flexible_pattern("fisip")],
    "Ilmu Budaya": [make_flexible_pattern("budaya"), r"\bfib\b"],
    "Gelanggang Mahasiswa": [make_flexible_pattern("gelanggang")],
    "GSP": [make_flexible_pattern("gsp"), r"\bgedung\s?pusat\b"],
    "Sekolah Vokasi": [make_flexible_pattern("vokasi"), r"\bsv\b"]
}


def extract_faculty_from_text(text: str) -> Optional[str]:
    text_lower = text.lower().strip()

    # Cek alias manual dulu
    if text_lower in FACULTY_PATTERNS:
        return FACULTY_PATTERNS[text_lower]

    # Cek regex dulu
    for faculty, patterns in FACULTY_PATTERNS.items():
        for pat in patterns:
            if re.search(pat, text_lower, re.IGNORECASE):
                return faculty

    # Kalau ga nemu, coba fuzzy
    all_keywords = list(FACULTY_PATTERNS.keys())
    match = get_close_matches(text_lower, all_keywords, n=1, cutoff=0.85)
    if match:
        return match[0]

    return None

def extract_budget_from_text(text: str) -> Optional[int]:
    """Extract a numerical budget from user text (e.g., '15k', '20rb', 'dibawah 20000')."""
    text_lower = text.lower().replace(" ", "")
    
    # Regex to find numbers followed by 'k', 'rb', or 'ribu'
    match = re.search(r'(\d+)(k|rb|ribu)\b', text_lower)
    if match:
        return int(match.group(1)) * 1000

    # Regex to find plain numbers
    match = re.search(r'(\d+)', text_lower)
    if match:
        num = int(match.group(1))
        # If number is small (e.g., 15), assume it's in thousands. If large (15000), use as is.
        return num * 1000 if num < 1000 else num
    
    # Format dengan kata (dua puluh ribu, sepuluh ribu)
    WORD_NUMS = {
        "sepuluh": 10000, "sebelas": 11000,
        "dua puluh": 20000, "tiga puluh": 30000,
        "seratus": 100000
    }
    for word, val in WORD_NUMS.items():
        if word in text_lower:
            return val
    return None

def extract_hunger_level_from_text(text: str) -> Optional[str]:
    """Extract hunger level dengan regex dan mapping ke brutal/standar/iseng."""
    patterns = {
        "brutal": [
            r"\ba\b", r"\bbrutal\b", r"\bbanget\b", r"\bparah\b", r"\bkuli\b"
        ],
        "standar": [
            r"\bb\b", r"\bstandar\b", r"\bbiasa\b", r"\bnormal\b", r"\bkenyang\b"
        ],
        "iseng": [
            r"\bc\b", r"\biseng\b", r"\bngunyah\b", r"\bngemil\b", r"\bringan\b"
        ]
    }

    text_lower = text.lower()

    for level, regex_list in patterns.items():
        for regex in regex_list:
            if re.search(regex, text_lower):
                return level

    return None

def agree_response(text: str) -> Optional[bool]:
    """Deteksi jawaban setuju/tidak pakai flexible pattern."""
    base_yes = ["ya", "iya", "ok", "sip", "boleh", "yoi", "lagi"]
    base_no = ["ga", "gak", "nggak", "engga", "tidak", "no"]

    patterns_yes = [make_flexible_pattern(w) for w in base_yes]
    patterns_no = [make_flexible_pattern(w) for w in base_no]

    text_lower = text.lower()

    for pat in patterns_yes:
        if re.search(pat, text_lower):
            return True
    for pat in patterns_no:
        if re.search(pat, text_lower):
            return False
    return None


def is_full_response(text: str) -> bool:
    """Deteksi kenyang/wareg dengan pola fleksibel."""
    words = ["wareg", "kenyang", "full"]
    patterns_full: List[str] = [make_flexible_pattern(w) for w in words]
    return any(re.search(p, text.lower()) for p in patterns_full)


def is_thank_you(text: str) -> bool:
    """Deteksi ucapan terima kasih dengan pola fleksibel."""
    words = ["makasi", "makasih", "terima kasih", "suwun", "thanks"]
    patterns_thanks: List[str] = [make_flexible_pattern(w) for w in words]
    return any(re.search(p, text.lower()) for p in patterns_thanks)


# --- Core Logic Functions ---

def get_current_time_period() -> str:
    """Determine if it's 'pagi', 'siang', 'sore', or 'malam' based on WIB."""
    # Assuming the server runs in UTC, we adjust to WIB (UTC+7)
    # now = datetime.utcnow() + timedelta(hours=7)
    now = datetime.now() # Use this if your server is already in WIB
    hour = now.hour
    
    if 7 <= hour < 11: return 'pagi'
    if 11 <= hour < 15: return 'siang'
    if 15 <= hour < 18: return 'sore'
    return 'malam'

def find_recommendations(all_canteens: List[Dict], faculty: str, budget: int, hunger_level: str) -> List[Dict]:
    """
    The core filtering engine to find food recommendations.
    Returns a list of up to 2 matching menus, each with its parent canteen info.
    """
    time_period = get_current_time_period()
    logger.info(f"Filtering for: faculty='{faculty}', budget<={budget}, hunger='{hunger_level}', time='{time_period}'")

    hunger_to_category_map = {
        'brutal': ['makanan_berat'],
        'standar': ['makanan_berat', 'makanan_ringan'],
        'iseng': ['cemilan', 'makanan_ringan']
    }
    allowed_categories = hunger_to_category_map.get(hunger_level, [])

    nearby_canteens = [
        canteen for canteen in all_canteens 
        if faculty in canteen.get('faculty_proximity', [])
    ]
    
    if not nearby_canteens:
        logger.warning(f"No canteens found with proximity to faculty: {faculty}")
        return []

    matching_menus = []
    for canteen in nearby_canteens:
        for menu in canteen.get('menus', []):
            is_budget_ok = menu.get('price', float('inf')) <= budget
            is_category_ok = menu.get('category') in allowed_categories
            is_time_ok = time_period in menu.get('suitability', [])
            
            if is_budget_ok and is_category_ok and is_time_ok:
                result_item = {
                    'canteen_name': canteen.get('canteen_name'),
                    'gmaps_link': canteen.get('gmaps_link'),
                    'menu_name': menu.get('name'),
                    'menu_price': menu.get('price')
                }
                matching_menus.append(result_item)
    
    random.shuffle(matching_menus)
    logger.info(f"Found {len(matching_menus)} matching items. Returning up to 2.")
    return matching_menus[:2]

def find_nearby_menus(
    canteens_db: List[Dict], faculty: str, limit: int = 5, allow_fallback: bool = True
) -> List[Dict]:
    """Ambil beberapa menu dari kantin dekat fakultas tertentu. 
       Kalau tidak ada, ambil dari fakultas lain kalau allow_fallback=True.
    """
    menus = []
    faculty_lower = faculty.lower()

    #  Cari berdasarkan fakultas dulu
    for canteen in canteens_db:
        if (faculty_lower in canteen.get("canteen_name", "").lower() or
            any(faculty_lower in alias.lower() for alias in canteen.get("canteen_alias", []))):
            
            for menu in canteen.get("menus", []):
                if isinstance(menu, dict):
                    menu_with_info = {
                        "canteen_name": canteen.get("canteen_name", "Unknown"),
                        "menu_name": menu.get("menu_name") or menu.get("name", "Unknown"),
                        "menu_price": menu.get("menu_price") or menu.get("price", 0),
                        "suitability": menu.get("suitability", []),
                        "gmaps_link": canteen.get("gmaps_link", None)
                    }
                    menus.append(menu_with_info)
                    if len(menus) >= limit:
                        return menus

    #  Kalau kosong & fallback diizinkan → ambil menu umum dari kantin lain
    if not menus and allow_fallback:
        for canteen in canteens_db:
            for menu in canteen.get("menus", []):
                if isinstance(menu, dict):
                    menu_with_info = {
                        "canteen_name": canteen.get("canteen_name", "Unknown"),
                        "menu_name": menu.get("menu_name") or menu.get("name", "Unknown"),
                        "menu_price": menu.get("menu_price") or menu.get("price", 0),
                        "suitability": menu.get("suitability", []),
                        "gmaps_link": canteen.get("gmaps_link", None)
                    }
                    menus.append(menu_with_info)
                    if len(menus) >= limit:
                        return menus

    return menus

# untuk testing functional flow
def ask_user_budget():
    return input("Budgetnya berapa?")

def ask_user_ai():
    return input("Mau dicari pake AI? (ya/tidak)")

def ask_user_repeat():
    return input("Mau rekomendasi lagi? (ya/tidak)")

def reset_state():
    return None

# untuk functional test
def ask_user_budget():
    pass

def ask_user_ai():
    pass

def ask_user_repeat():
    pass

def ask_user_faculty():
    pass

def ask_user_hunger():
    pass

def ai_recommendation(faculty, budget, hunger):
    pass







