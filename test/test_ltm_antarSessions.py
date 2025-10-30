# test/test_long_tm.py
import pytest
from unittest.mock import MagicMock, patch
from src.memory.session_manager import SessionManager
from src.memory.memory_manager import MemoryManager

@pytest.fixture
def setup_memory_manager():
    # Patch UserMemoryModel & db_instance sebelum MemoryManager dibuat
    with patch("src.memory.memory_manager.UserMemoryModel") as MockLTM, \
         patch("src.memory.memory_manager.db_instance") as MockDB:
        MockDB.__getitem__.return_value = MagicMock()  # db_instance["user_memory"] -> mock
        mm = MemoryManager()
        mm.ltm_model = MockLTM()  # pastikan LTM dimock
        yield mm

@pytest.fixture
def setup_sessions(setup_memory_manager):
    mm = setup_memory_manager
    # Buat dua session berbeda untuk userA & userB
    mm.stm.create_session(session_id="sessA", user_id="userA")
    mm.stm.create_session(session_id="sessB", user_id="userB")
    return mm

def test_stm_ltm_isolation(setup_sessions):
    mm = setup_sessions
    
    # Simulasi userA & userB mengirim pesan berbeda
    mm.save_context("userA", "sessA", {"raw_input": "halo userA"})
    mm.save_context("userB", "sessB", {"raw_input": "hi userB"})
    
    # Cek STM per session
    stm_A = mm.stm.get_messages("sessA")
    stm_B = mm.stm.get_messages("sessB")
    
    assert stm_A == [{"role": "user", "content": "halo userA"}]
    assert stm_B == [{"role": "user", "content": "hi userB"}]
    
    # Simulasi userA & userB menambah liked_food
    mm.add_liked_food("userA", "Nasi Goreng")
    mm.add_liked_food("userB", "Ayam Geprek")
    
    # Cek LTM dipanggil sesuai user & makanan
    mm.ltm_model.add_liked_food.assert_any_call("userA", "Nasi Goreng")
    mm.ltm_model.add_liked_food.assert_any_call("userB", "Ayam Geprek")

def test_multiple_messages_and_ltm(setup_sessions):
    mm = setup_sessions
    
    # UserA kirim beberapa pesan
    messages_A = ["halo", "aku lapar", "mau makan Nasi Goreng"]
    for msg in messages_A:
        mm.save_context("userA", "sessA", {"raw_input": msg})
    
    # UserB kirim pesan berbeda
    messages_B = ["hi", "what's up?", "mau Ayam Geprek"]
    for msg in messages_B:
        mm.save_context("userB", "sessB", {"raw_input": msg})
    
    # Cek STM per session
    stm_A = [m["content"] for m in mm.stm.get_messages("sessA")]
    stm_B = [m["content"] for m in mm.stm.get_messages("sessB")]
    
    assert stm_A == messages_A
    assert stm_B == messages_B
    
    # Update LTM
    mm.add_liked_food("userA", "Nasi Goreng")
    mm.add_liked_food("userB", "Ayam Geprek")
    
    # Pastikan LTM terpanggil untuk masing-masing user
    calls = [call.args for call in mm.ltm_model.add_liked_food.call_args_list]
    assert ("userA", "Nasi Goreng") in calls
    assert ("userB", "Ayam Geprek") in calls
