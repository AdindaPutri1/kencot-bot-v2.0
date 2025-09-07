# app/utils.py
"""
Utility functions for Kencot Bot.
This is the core engine for data extraction, filtering, and response formatting.
"""

import re
import json
import random
import logging
from .config import Config # Jika kamu butuh config di sini
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
            "no_result": ["Waduh, kayaknya kombinasi pencarianmu ga nemu apa-apa nih 😢. Coba deh ganti kriteria, mungkin budgetnya digedein dikit?"],
            "error": ["Aduh, mamang lagi error nih 😵 Coba chat lagi dalam beberapa saat ya!"]
        }

# --- Entity Extraction Functions ---

def extract_faculty_from_text(text: str) -> Optional[str]:
    """Extract and normalize faculty name from user input."""
    faculty_mapping = {
        'teknik': 'Teknik', 'ft': 'Teknik',
        'mipa': 'MIPA', 'fmipa': 'MIPA',
        'fkkmk': 'FKKMK', 'kedokteran': 'FKKMK', 'fk': 'FKKMK',
        'pertanian': 'Pertanian', 'faperta': 'Pertanian',
        'filsafat': 'Filsafat', 'bonbin': 'Filsafat',
        'pascasarjana': 'Pascasarjana', 'pasca': 'Pascasarjana',
        'psikologi': 'Psikologi', 'psiko': 'Psikologi',
        'farmasi': 'Farmasi',
        'kehutanan': 'Kehutanan', 'fkt': 'Kehutanan',
        'peternakan': 'Peternakan', 'fapet': 'Peternakan',
        'geografi': 'Geografi',
        'feb': 'FEB', 'ekonomi': 'FEB',
        'hukum': 'Hukum', 'fh': 'Hukum',
        'isipol': 'Fisipol', 'fisipol': 'Fisipol',
        'budaya': 'Ilmu Budaya', 'fib': 'Ilmu Budaya',
        'gelanggang': 'Gelanggang Mahasiswa',
        'gsp': 'GSP',
        'vokasi': 'Sekolah Vokasi', 'sv': 'Sekolah Vokasi'
    }
    text_lower = text.lower()
    for keyword, faculty in faculty_mapping.items():
        if keyword in text_lower:
            return faculty
    return None

def extract_budget_from_text(text: str) -> Optional[int]:
    """Extract a numerical budget from user text (e.g., '15k', '20rb', 'dibawah 20000')."""
    text_lower = text.lower().replace(" ", "")
    
    # Regex to find numbers followed by 'k', 'rb', or 'ribu'
    match = re.search(r'(\d+)(k|rb|ribu)', text_lower)
    if match:
        return int(match.group(1)) * 1000

    # Regex to find plain numbers
    match = re.search(r'(\d+)', text_lower)
    if match:
        num = int(match.group(1))
        # If number is small (e.g., 15), assume it's in thousands. If large (15000), use as is.
        return num * 1000 if num < 1000 else num
        
    return None

def extract_hunger_level_from_text(text: str) -> Optional[str]:
    """Extract hunger level and map it to a standard category: 'brutal', 'standar', 'iseng'."""
    text_lower = text.lower()
    if any(x in text_lower for x in ['a', 'brutal', 'banget', 'parah', 'kuli']):
        return 'brutal'
    if any(x in text_lower for x in ['b', 'standar', 'biasa', 'normal', 'kenyang']):
        return 'standar'
    if any(x in text_lower for x in ['c', 'iseng', 'ngunyah', 'ngemil', 'ringan']):
        return 'iseng'
    return None

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

def find_nearby_menus(canteens_db: List[Dict], faculty: str, limit: int = 5) -> List[Dict]:
    """Mengambil beberapa menu dari kantin yang namanya mengandung nama fakultas."""
    menus = []
    faculty_lower = faculty.lower()

    for canteen in canteens_db:
        if (faculty_lower in str(canteen.get("canteen_name", "")).lower() or
            any(faculty_lower in str(alias).lower() for alias in canteen.get("canteen_alias", []))):
            
            for menu in canteen.get("menus", []):
                if isinstance(menu, dict):
                    menu_with_info = menu.copy()
                    menu_with_info['canteen_name'] = canteen.get("canteen_name", "Unknown")
                    menu_with_info['menu_name'] = menu.get("name", "Unknown")  # ✅ pastikan key ada
                    menu_with_info['menu_price'] = menu.get("price", 0)
                    menus.append(menu_with_info)

                    if len(menus) >= limit:
                        return menus

    return menus



