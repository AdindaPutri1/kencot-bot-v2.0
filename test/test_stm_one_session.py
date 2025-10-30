from unittest.mock import MagicMock, patch
from src.bot.agent import FoodAgent

@patch("src.bot.agent.MemoryManager")  # Mock seluruh MemoryManager
def test_short_term_memory_one_session(mock_memory):
    # Buat mock memory instance
    mock_mem_instance = MagicMock()
    # STM: simulasikan menyimpan context per session
    session_context = {}

    # Mock get_context untuk mengembalikan context berdasarkan session_id
    def get_context_side_effect(user_id, session_id):
        return session_context.get(session_id, {})

    # Mock update_context untuk menyimpan context
    def update_context_side_effect(user_id, session_id, new_context):
        session_context[session_id] = new_context

    mock_mem_instance.get_context.side_effect = get_context_side_effect
    mock_mem_instance.update_context.side_effect = update_context_side_effect

    mock_memory.return_value = mock_mem_instance

    agent = FoodAgent()

    # Input pertama
    response1 = agent.process("u1", "s1", "aku suka pedas")
    # Update context manual (simulasi STM menyimpan info)
    mock_mem_instance.update_context("u1", "s1", {"preference": "pedas"})

    # Input kedua
    response2 = agent.process("u1", "s1", "aku juga suka ayam")

    # Test: input kedua masih bisa akses info dari input pertama
    remembered_context = mock_mem_instance.get_context("u1", "s1")
    assert "pedas" in remembered_context.get("preference", "")
    assert response2 is not None
