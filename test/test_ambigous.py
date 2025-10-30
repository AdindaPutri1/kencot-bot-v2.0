import pytest
from unittest.mock import MagicMock, patch
from src.bot.agent import FoodAgent

@pytest.fixture
def agent_mocked():
    with patch("src.bot.agent.MemoryManager") as MockMemory, \
         patch("src.bot.agent.FoodDB") as MockDB, \
         patch("src.bot.agent.NutritionTool") as MockNut, \
         patch("src.bot.agent.RetrievalEngine") as MockRAG, \
         patch("src.bot.agent.OpenAI") as MockLLM:

        mem = MockMemory.return_value
        mem.get_context.return_value = {"ltm": {}}
        mem.stm.get_messages.return_value = []
        mem.add_liked_food.return_value = None

        db = MockDB.return_value
        db.get_all_menus.return_value = [{"menu_name": "Nasi Goreng"}]
        db.load_from_json.return_value = None

        nut = MockNut.return_value
        nut.get_nutrition.return_value = {"calories": 200}

        rag = MockRAG.return_value
        rag.search.return_value = [{"menu_name": "Nasi Goreng"}]

        llm = MockLLM.return_value
        llm.chat.completions.create.return_value.choices = [MagicMock(message=MagicMock(content='{"search_method":"rag","recommendation":"Nasi Goreng","call_nutrition":true}'))]

        yield FoodAgent()

def test_input_ambiguous_typo(agent_mocked):
    agent = agent_mocked

    # patch reasoning supaya nggak panggil API
    agent.call_llm_reasoning = lambda prompt: "Mamang pilih Nasi Goreng karena input typo dari user."

    result = agent.process("user3", "sess3", "nasi goyeng")

    assert result["decision_type"] == "rag"
    assert result["recommendation"]["menu_name"] == "Nasi Goreng"
    assert result["nutrition"]["calories"] > 0
    assert "Mamang pilih Nasi Goreng" in result["reasoning"]
