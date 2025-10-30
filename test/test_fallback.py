import pytest
from src import FoodAgent

class DummyMemoryManager:
    def __init__(self):
        self.stm = self
        self.context = {}
        self.liked = []
    def get_context(self, user_id, session_id):
        return {"ltm": {}}
    def stm(self):
        return self
    def get_messages(self, session_id):
        return []
    def add_liked_food(self, user_id, food_name):
        self.liked.append(food_name)
    def save_context(self, user_id, session_id, context):
        pass
    def add_message(self, session_id, role, content):
        pass

class DummyNutritionTool:
    def get_nutrition(self, food_name):
        # kembalikan dict kosong supaya fallback kalori jalan
        return {}

class DummyFoodDB:
    def load_from_json(self, path):
        pass
    def get_all_menus(self):
        return [{"menu_name": "Nasi Goreng"}]

class DummyRetrievalEngine:
    def search(self, text, top_k=3):
        return [{"menu_name": "Fallback Menu"}]

def test_process_fallback(monkeypatch):
    agent = FoodAgent()

    # patch semua dependency
    agent.memory = DummyMemoryManager()
    agent.nutrition_tool = DummyNutritionTool()
    agent.food_db = DummyFoodDB()
    agent.rag_engine = DummyRetrievalEngine()

    # patch LLM supaya nggak call API
    agent.call_llm = lambda prompt: {"search_method": "database", "recommendation": "Nasi Goreng", "call_nutrition": True}
    agent.call_llm_reasoning = lambda prompt: "Ini alasan kenapa makanan direkomendasikan."

    result = agent.process("user1", "sess1", "Rekomendasi makanan apa?")

    assert result["recommendation"]["menu_name"] == "Nasi Goreng"
    assert result["nutrition"]["calories"] > 0
    assert "Ini alasan" in result["reasoning"]
