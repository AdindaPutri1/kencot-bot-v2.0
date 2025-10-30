from unittest.mock import patch, MagicMock
import pytest
from src.bot.agent import FoodAgent

def test_process_fallback():
    with patch("src.bot.agent.MemoryManager") as MockMemory:
        # Mock instance MemoryManager
        mock_memory = MagicMock()
        mock_memory.get_context.return_value = {"ltm": {}}
        MockMemory.return_value = mock_memory

        # Buat agent setelah MemoryManager dipatch
        agent = FoodAgent()

        # Patch dependency lain
        agent.nutrition_tool = MagicMock()
        agent.nutrition_tool.get_nutrition.return_value = {"calories": 200}
        agent.food_db = MagicMock()
        agent.food_db.get_all_menus.return_value = [{"menu_name": "Nasi Goreng"}]
        agent.rag_engine = MagicMock()
        agent.rag_engine.search.return_value = [{"menu_name": "Fallback Menu"}]

        # Patch LLM supaya nggak call API
        agent.call_llm = lambda prompt: {"search_method": "database", "recommendation": "Nasi Goreng", "call_nutrition": True}
        agent.call_llm_reasoning = lambda prompt: "Ini alasan kenapa makanan direkomendasikan."

        # Run test
        result = agent.process("user1", "sess1", "Rekomendasi makanan apa?")
        assert result["recommendation"]["menu_name"] == "Nasi Goreng"
        assert result["nutrition"]["calories"] > 0
        assert "Ini alasan" in result["reasoning"]
