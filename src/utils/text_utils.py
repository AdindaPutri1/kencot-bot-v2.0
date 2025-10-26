"""
Text extraction utilities (migrated from original utils.py)
"""
import re
from typing import Optional
from difflib import get_close_matches

def make_flexible_pattern(word: str) -> str:
    """Create flexible regex pattern for typo tolerance"""
    pattern = "".join([f"{c}+" if c.isalpha() else c for c in word])
    return r"\b" + pattern + r"\b"

# Faculty patterns (from original code)
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
    """Extract faculty name from text"""
    text_lower = text.lower().strip()
    
    # Check direct match
    if text_lower in FACULTY_PATTERNS:
        return FACULTY_PATTERNS[text_lower]
    
    # Check regex patterns
    for faculty, patterns in FACULTY_PATTERNS.items():
        for pat in patterns:
            if re.search(pat, text_lower, re.IGNORECASE):
                return faculty
    
    # Fuzzy matching
    all_keywords = list(FACULTY_PATTERNS.keys())
    match = get_close_matches(text_lower, all_keywords, n=1, cutoff=0.85)
    if match:
        return match[0]
    
    return None

def extract_budget_from_text(text: str) -> Optional[int]:
    """Extract budget amount from text"""
    text_lower = text.lower().replace(" ", "")
    
    # Pattern: 15k, 20rb, 20ribu
    match = re.search(r'(\d+)(k|rb|ribu)\b', text_lower)
    if match:
        return int(match.group(1)) * 1000
    
    # Plain number
    match = re.search(r'(\d+)', text_lower)
    if match:
        num = int(match.group(1))
        return num * 1000 if num < 100 else num
    
    # Word numbers
    WORD_NUMS = {
        "sepuluh": 10000,
        "sebelas": 11000,
        "dua puluh": 20000,
        "tiga puluh": 30000,
        "seratus": 100000
    }
    for word, val in WORD_NUMS.items():
        if word in text_lower:
            return val
    
    return None

def extract_hunger_level_from_text(text: str) -> Optional[str]:
    """Extract hunger level from text"""
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

def agree_response(text: str) -> Optional[bool]:
    """Detect yes/no response"""
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
    """Detect 'full/satisfied' response"""
    words = ["wareg", "kenyang", "full", "cukup"]
    patterns = [make_flexible_pattern(w) for w in words]
    return any(re.search(p, text.lower()) for p in patterns)

def is_thank_you(text: str) -> bool:
    """Detect thank you message"""
    words = ["makasi", "makasih", "terima kasih", "suwun", "thanks", "thx"]
    patterns = [make_flexible_pattern(w) for w in words]
    return any(re.search(p, text.lower()) for p in patterns)