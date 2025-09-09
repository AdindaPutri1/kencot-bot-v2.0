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