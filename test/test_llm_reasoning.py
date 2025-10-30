from unittest.mock import MagicMock, patch
from src.bot.agent import FoodAgent

@patch("src.bot.agent.MemoryManager")   
def test_llm_reasoning_spicy_preference(MockMemoryManager):
    # Mock MemoryManager instance
    mock_memory = MagicMock()
    mock_memory.get_context.return_value = {}
    MockMemoryManager.return_value = mock_memory

    agent = FoodAgent()  
    # Mock LLM
    agent.client_gemini = MagicMock()
    agent.client_gemini.chat.completions.create.return_value = type("obj", (), {
        "choices": [type("obj", (), {
            "message": type("obj", (), {
                "content": '{"search_method":"database","recommendation":"Ayam Geprek","reasoning":"User suka pedas"}'
            })
        })]
    })

    # Mock DB
    agent.food_db = MagicMock()
    agent.food_db.get_all_menus.return_value = [
        {"menu_name":"Ayam Geprek"}
    ]

    # Run
    result = agent.process("u1", "s1", "aku suka makanan pedas")

    # Assert
    assert result["recommendation"]["menu_name"] == "Ayam Geprek"
    assert "pedas" in result["reasoning"].lower()
