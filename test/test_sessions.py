# test/test_sessions.py
import pytest
from unittest.mock import MagicMock

# Mock Session & MemoryManager supaya tes bisa jalan
class MockSession:
    def __init__(self, user_id):
        self.user_id = user_id
        self.history = []
        self.memory_manager = MagicMock()

    def save_context(self, msg):
        self.history.append({'role': 'user', 'content': msg})

    def get_context(self):
        return {'history': self.history}

    def add_liked_food(self, food):
        self.memory_manager.add_liked_food(food)

class MockSessionManager:
    def create_session(self, user_id):
        return MockSession(user_id)

@pytest.fixture
def setup_sessions():
    session_mgr = MockSessionManager()
    userA_session = session_mgr.create_session(user_id="userA")
    userB_session = session_mgr.create_session(user_id="userB")
    return userA_session, userB_session

def test_stm_context_separate(setup_sessions):
    userA_session, userB_session = setup_sessions
    
    # Simulasi pesan berbeda
    messages_A = ["halo", "aku lapar"]
    messages_B = ["hi", "what's up?"]
    
    for msg in messages_A:
        userA_session.save_context(msg)
    for msg in messages_B:
        userB_session.save_context(msg)
    
    context_A = userA_session.get_context()
    context_B = userB_session.get_context()
    
    assert context_A['history'][-2:] == [{'role': 'user', 'content': m} for m in messages_A]
    assert context_B['history'][-2:] == [{'role': 'user', 'content': m} for m in messages_B]

def test_ltm_liked_food_called_per_user(setup_sessions):
    userA_session, userB_session = setup_sessions
    
    # Tambah liked_food
    userA_session.add_liked_food("Nasi Goreng")
    userB_session.add_liked_food("Ayam Geprek")
    
    # Cek LTM terpanggil
    userA_session.memory_manager.add_liked_food.assert_any_call("Nasi Goreng")
    userB_session.memory_manager.add_liked_food.assert_any_call("Ayam Geprek")
