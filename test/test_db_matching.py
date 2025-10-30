from unittest.mock import MagicMock, patch
from src.bot.agent import FoodAgent

@patch("src.bot.agent.MemoryManager")  # mock MemoryManager supaya ga connect DB asli
def test_db_matching(mock_memory):
    # Mock memory object
    mock_memory.return_value = MagicMock()
    mock_memory.return_value.get_context.return_value = {}

    agent = FoodAgent()

    # Mock LLM response
    agent.client_gemini = MagicMock()
    agent.client_gemini.chat.completions.create.return_value = type("obj", (), {
        "choices": [type("obj", (), {
            "message": type("obj", (), {
                "content": '{"search_method":"database","recommendation":"Ayam Bakar"}'
            })
        })]
    })

    # DB punya Ayam Bakar
    agent.food_db = MagicMock()
    agent.food_db.get_all_menus.return_value = [
        {"menu_name": "Ayam Bakar", "price": 20000}
    ]

    result = agent.process("u1", "s1", "aku mau sesuatu yang bakar")

    assert result["recommendation"]["menu_name"] == "Ayam Bakar"
    assert result["recommendation"]["price"] == 20000
