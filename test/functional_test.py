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
