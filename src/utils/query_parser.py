import re
from datetime import datetime, timedelta, timezone
from difflib import get_close_matches
from typing import Optional

def get_current_time_period() -> str:
    now = datetime.now(timezone.utc) + timedelta(hours=7)
    hour = now.hour
    if 5 <= hour < 11:
        return 'pagi'
    elif 11 <= hour < 15:
        return 'siang'
    elif 15 <= hour < 18:
        return 'sore'
    else:
        return 'malam'

def make_flexible_pattern(word: str) -> str:
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
    for faculty, patterns in FACULTY_PATTERNS.items():
        for pat in patterns:
            if re.search(pat, text_lower, re.IGNORECASE):
                return faculty
    all_keywords = list(FACULTY_PATTERNS.keys())
    match = get_close_matches(text_lower, all_keywords, n=1, cutoff=0.85)
    if match:
        return match[0]
    return None

def extract_budget_from_text(text: str) -> Optional[int]:
    text_lower = text.lower().replace(" ", "")
    match = re.search(r'(\d+)(k|rb|ribu)\b', text_lower)
    if match:
        return int(match.group(1)) * 1000
    match = re.search(r'(\d+)', text_lower)
    if match:
        num = int(match.group(1))
        return num * 1000 if num < 100 else num
    return None

def extract_hunger_level_from_text(text: str) -> Optional[str]:
    patterns = {
        "iseng": [r"\bc\b", r"\biseng\b", r"\bngunyah\b", r"\bngemil\b", r"\bringan\b"],
        "standar": [r"\bb\b", r"\bstandar\b", r"\bbiasa\b", r"\bnormal\b", r"\bkenyang\b"],
        "brutal": [r"\ba\b", r"\bbrutal\b", r"\bbanget\b", r"\bparah\b", r"\bkuli\b"]
    }
    text_lower = text.lower()
    for level, regex_list in patterns.items():
        for regex in regex_list:
            if re.search(regex, text_lower):
                return level
    return None

def parse_user_query(text: str) -> dict:
    return {
        "faculty": extract_faculty_from_text(text),
        "budget": extract_budget_from_text(text),
        "hunger": extract_hunger_level_from_text(text),
        "time_period": get_current_time_period()
    }
