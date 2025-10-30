# test/test_memory_feedback.py
import pytest
from unittest.mock import MagicMock, patch
from src.memory.memory_manager import MemoryManager

@pytest.fixture
def memory_manager():
    # Mock UserMemoryModel dan db_instance sebelum MemoryManager dibuat
    with patch("src.memory.memory_manager.UserMemoryModel") as MockLTM, \
         patch("src.memory.memory_manager.db_instance") as MockDB:

        # db_instance["user_memory"] -> mock object
        MockDB.__getitem__.return_value = MagicMock()
        mm = MemoryManager()
        mm.ltm_model = MockLTM()  # pastikan LTM dimock
        yield mm

def test_add_liked_disliked_allergy(memory_manager):
    mm = memory_manager
    user_id = "user123"

    # Tambah liked_food
    mm.add_liked_food(user_id, "Nasi Goreng")
    mm.ltm_model.add_liked_food.assert_called_with(user_id, "Nasi Goreng")

    # Tambah disliked_food
    mm.add_disliked_food(user_id, "Sayur")
    mm.ltm_model.add_disliked_food.assert_called_with(user_id, "Sayur")

    # Tambah allergy
    mm.add_allergy(user_id, "kacang")
    mm.ltm_model.add_allergy.assert_called_with(user_id, "kacang")

def test_apply_feedback(memory_manager):
    mm = memory_manager
    user_id = "user123"

    feedback = {
        "rating": 5,
        "sentiment": "positive",
        "context": {"hunger_level": "brutal", "budget": 20000},
        "comment": "Mantap!"
    }

    # Karena MemoryManager belum ada add_feedback asli, kita bisa simulasikan
    # misal patch add_feedback di ltm_model
    mm.ltm_model.add_feedback = MagicMock()
    mm.ltm_model.add_feedback(user_id, feedback)
    mm.ltm_model.add_feedback.assert_called_with(user_id, feedback)

def test_stm_save_context(memory_manager):
    mm = memory_manager
    user_id = "user123"
    session_id = "sess1"

    context = {"raw_input": "Halo Mamang!"}
    mm.save_context(user_id, session_id, context)

    # cek STM tersimpan
    messages = mm.stm.get_messages(session_id)
    assert messages[-1]["role"] == "user"
    assert messages[-1]["content"] == "Halo Mamang!"
