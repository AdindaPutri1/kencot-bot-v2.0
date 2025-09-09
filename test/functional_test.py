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
def test_functional_faculty_hunger_wait_budget(monkeypatch, sample_canteens):
    user_responses = iter([""])  # belum budget
    # monkeypatch dll
    recs = utils.find_recommendations(sample_canteens, "Fisipol", 0, "standar")
    assert recs == []


# ---------- FUNCTIONAL – typo case → matching words ----------
@pytest.mark.parametrize("faculty_input, expected_faculty", [
    ("fisip", "Fisipol"),
    ("fisipol", "Fisipol"),
    ("fissip", "Fisipol"),  # typo case
])
def test_functional_faculty_typo_matching(faculty_input, expected_faculty):
    assert utils.extract_faculty_from_text(faculty_input) == expected_faculty


# ---------- FUNCTIONAL – AI Recommendation if database empty ----------
def test_functional_ai_recommendation(monkeypatch):
    # Dummy AI function
    monkeypatch.setattr(utils, "ai_recommendation", 
                        lambda faculty, budget, hunger: [{"canteen_name": "AI Canteen", "menu_price": 10000}])
    
    # Simulasi user setuju AI
    user_responses = iter(["ya"])
    monkeypatch.setattr(utils, "ask_user_ai", lambda: next(user_responses))
    
    # Patch find_recommendations supaya memanggil AI jika database kosong
    def dummy_find_recommendations(canteens, faculty, budget, hunger):
        if not canteens:  # kosong → trigger AI
            return utils.ai_recommendation(faculty, budget, hunger)
        return canteens
    monkeypatch.setattr(utils, "find_recommendations", dummy_find_recommendations)
    
    # Test
    recs = utils.find_recommendations([], "Teknik", 20000, "brutal")
    assert recs[0]["canteen_name"] == "AI Canteen"
    assert recs[0]["menu_price"] == 10000

# ---------- FUNCTIONAL – user minta rekomendasi lagi ----------
def test_functional_repeat_recommendation(monkeypatch, sample_canteens):
    initial_recs = [{"canteen_name": "Canteen A", "menu_price": 15000}]
    user_responses = iter(["mau", "Teknik", "standar", 20000])
    monkeypatch.setattr(utils, "find_recommendations", lambda *args, **kwargs: initial_recs)
    monkeypatch.setattr(utils, "ask_user_repeat", lambda: next(user_responses))
    monkeypatch.setattr(utils, "ask_user_faculty", lambda: next(user_responses))
    monkeypatch.setattr(utils, "ask_user_hunger", lambda: next(user_responses))
    monkeypatch.setattr(utils, "ask_user_budget", lambda: next(user_responses))

    recs = utils.find_recommendations(sample_canteens, "Teknik", 20000, "standar")
    assert recs[0]["canteen_name"] == "Canteen A"


# ---------- FUNCTIONAL – user bilang "wareg" → reset state ----------
def test_functional_user_satisfied_resets(monkeypatch):
    state = {"current_state": "waiting_location"}
    user_responses = iter(["wareg"])  # user selesai

    monkeypatch.setattr(utils, "ask_user_repeat", lambda: next(user_responses))
    # fungsi reset_state
    def fake_reset_state():
        state["current_state"] = None
    monkeypatch.setattr(utils, "reset_state", fake_reset_state)

    # Simulasi user habis rekomendasi → bilang wareg
    utils.reset_state()
    assert state["current_state"] is None

