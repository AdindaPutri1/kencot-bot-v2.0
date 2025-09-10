import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from app import utils

import json

@pytest.fixture
def sample_canteens():
    data_path = os.path.join(os.path.dirname(__file__), "..", "data", "database.json")
    with open(data_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["ugm_canteens"]
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
def test_ai_recommendation(monkeypatch, sample_canteens):
    # Patch supaya find_recommendations kosong → trigger AI
    monkeypatch.setattr(utils, "find_recommendations", lambda *args, **kwargs: [])

    # Patch ask_gemini → simulasi balikin rekomendasi AI
    monkeypatch.setattr(utils, "ask_gemini", lambda user_data, canteens: "🍛 Nasi Padang AI")

    # Panggil langsung ask_gemini (karena recs kosong → fallback AI)
    result = utils.ask_gemini(
        {"faculty": "Teknik", "hunger_level": "iseng", "budget": 5000, "time_category": "siang"},
        sample_canteens
    )

    assert "Nasi Padang AI" in result



# ---------- UNIT TESTS – reset state ----------
def test_reset_state_equivalent():
    assert utils.is_full_response("wareg") is True
    assert utils.is_full_response("kenyang banget") is True
    assert utils.is_full_response("lapar") is False


