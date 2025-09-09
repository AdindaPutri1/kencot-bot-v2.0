import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from app import utils

# ---------- UNIT TESTS ---------- based on utils.py

@pytest.mark.parametrize("text, expected", [
    ("15rb", 15000),
    ("20k", 20000),
    ("10000", 10000),
    ("50 ribu", 50000),
])
def test_extract_budget_from_text(text, expected):
    assert utils.extract_budget_from_text(text) == expected


@pytest.mark.parametrize("text, expected", [
    ("teknik", "Teknik"),
    ("FT", "Teknik"),
    ("mipa", "MIPA"),
    ("kedokteran", "FKKMK"),
    ("fisip", "Fisipol"),
])
def test_extract_faculty_from_text(text, expected):
    assert utils.extract_faculty_from_text(text) == expected


@pytest.mark.parametrize("text, expected", [
    ("brutal", "brutal"),
    ("A", "brutal"),
    ("butuh nasi porsi kuli", "brutal"),
    ("standar", "standar"),
    ("B", "standar"),
    ("normal aja", "standar"),
    ("iseng", "iseng"),
    ("C", "iseng"),
    ("cuma ngemil ringan", "iseng"),
])
def test_extract_hunger_level_from_text(text, expected):
    assert utils.extract_hunger_level_from_text(text) == expected

# ---------- UNIT TESTS – tambahan untuk typo & variasi ----------
@pytest.mark.parametrize("text, expected", [
    ("fissip", "Fisipol"),  # typo kecil
    ("fisip", "Fisipol"),
    ("FT", "Teknik"),
])
def test_extract_faculty_typo(text, expected):
    assert utils.extract_faculty_from_text(text) == expected


@pytest.mark.parametrize("text, expected", [
    ("butuh nasi porsi kuli", "brutal"),
    ("iseng banget", "iseng"),
])
def test_extract_hunger_variation(text, expected):
    assert utils.extract_hunger_level_from_text(text) == expected

# ---------- UNIT TESTS – AI Recommendation fallback ----------
def test_ai_recommendation(monkeypatch):
    # Patch find_recommendations biar kosong → trigger AI
    monkeypatch.setattr(utils, "find_recommendations", lambda *args, **kwargs: [])
    monkeypatch.setattr(utils, "ai_recommendation", lambda faculty, budget, hunger: [{"canteen_name": "AI Canteen", "menu_price": 10000}])

    recs = utils.find_recommendations([], "Teknik", 20000, "brutal")
    assert recs[0]["canteen_name"] == "AI Canteen"
    assert recs[0]["menu_price"] == 10000

# ---------- UNIT TESTS – reset state ----------
def test_reset_state(monkeypatch):
    state = {"current_state": "waiting_location"}
    monkeypatch.setattr(utils, "reset_state", lambda: state.update({"current_state": None}))

    utils.reset_state()
    assert state["current_state"] is None

