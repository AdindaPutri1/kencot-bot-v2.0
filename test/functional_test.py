import sys, os, json
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from app import utils

# ---------- FUNCTIONAL TESTS ---------- based on utils.py

@pytest.fixture
def sample_canteens():
    
    data_path = os.path.join(os.path.dirname(__file__), "..", "data", "database.json")
    with open(data_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["ugm_canteens"]   # ambil langsung list kantinnya



def test_functional_full_flow(sample_canteens, monkeypatch):
    # Patch waktu → biar konsisten, set jam 12 (siang)
    monkeypatch.setattr(utils, "get_current_time_period", lambda: "siang")

    recs = utils.find_recommendations(sample_canteens, "Teknik", 20000, "brutal")
    assert len(recs) > 0
    assert recs[0]["canteen_name"] != ""   # minimal nama kantin ada
    assert recs[0]["menu_price"] <= 20000


def test_functional_faculty_only(sample_canteens, monkeypatch):
    monkeypatch.setattr(utils, "get_current_time_period", lambda: "siang")

    # Budget & hunger kosong → seolah baru masuk fase faculty
    recs = utils.find_recommendations(sample_canteens, "Teknik", 0, "")
    # Harus kosong karena hunger & budget tidak lengkap
    assert recs == []

# ---------- FUNCTIONAL – faculty + hunger → bot harus nanya budget ----------
def extract_hunger_level_from_text(text: str) -> str:
    text = text.lower()
    if "iseng" in text:
        return "iseng"
    elif "butuh nasi" in text or "brutal" in text:
        return "brutal"
    return "normal"


# ---------- FUNCTIONAL – typo case → matching words ----------
@pytest.mark.parametrize("faculty_input, expected_faculty", [
    ("fisip", "Fisipol"),
    ("fisipol", "Fisipol"),
    ("fissip", "Fisipol"),  # typo case
])
def test_functional_faculty_typo_matching(faculty_input, expected_faculty):
    assert utils.extract_faculty_from_text(faculty_input) == expected_faculty




def test_functional_repeat_recommendation(monkeypatch, sample_canteens):
    """
    Simulasi user minta rekomendasi lagi:
    - Pertama dapat hasil dari find_recommendations
    - Kedua kali dipanggil lagi → tetap dapat hasil
    """
    initial_recs = [{"canteen_name": "Canteen A", "menu_name": "Nasi Goreng", "menu_price": 15000}]
    monkeypatch.setattr(utils, "find_recommendations", lambda *args, **kwargs: initial_recs)

    recs1 = utils.find_recommendations(sample_canteens, "Teknik", 20000, "standar")
    recs2 = utils.find_recommendations(sample_canteens, "Teknik", 20000, "standar")

    assert recs1[0]["canteen_name"] == "Canteen A"
    assert recs2[0]["canteen_name"] == "Canteen A"


def test_functional_user_satisfied_resets():
    """
    Simulasi user bilang 'wareg' → deteksi dengan utils.is_full_response
    """
    assert utils.is_full_response("wareg bgt") is True
    assert utils.is_full_response("sudah kenyang") is True
    assert utils.is_full_response("lapar") is False


