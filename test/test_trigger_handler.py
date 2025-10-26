"""
Unit tests for TriggerHandler
"""
import pytest
from src.handlers.trigger_handler import TriggerHandler

class TestTriggerHandler:
    
    def test_food_request_trigger(self):
        """Test food request detection"""
        messages = [
            "laper nih",
            "aku lapar banget",
            "kencot",
            "mau makan",
            "rekomen makanan dong"
        ]
        
        for msg in messages:
            trigger = TriggerHandler.detect_trigger(msg)
            assert trigger == "food_request", f"Failed for: {msg}"
    
    def test_greeting_trigger(self):
        """Test greeting detection"""
        messages = ["halo", "hai mamang", "selamat pagi", "assalamualaikum"]
        
        for msg in messages:
            trigger = TriggerHandler.detect_trigger(msg)
            assert trigger == "greeting", f"Failed for: {msg}"
    
    def test_reset_trigger(self):
        """Test reset command detection"""
        messages = ["reset", "ulang", "restart", "mulai lagi", "batal"]
        
        for msg in messages:
            trigger = TriggerHandler.detect_trigger(msg)
            assert trigger == "reset", f"Failed for: {msg}"
    
    def test_feedback_positive(self):
        """Test positive feedback detection"""
        messages = ["mantap", "enak banget", "cocok nih", "👍", "makasih ya"]
        
        for msg in messages:
            trigger = TriggerHandler.detect_trigger(msg)
            assert trigger == "feedback_positive", f"Failed for: {msg}"
    
    def test_feedback_negative(self):
        """Test negative feedback detection"""
        messages = ["ga enak", "mahal", "jauh banget", "👎"]
        
        for msg in messages:
            trigger = TriggerHandler.detect_trigger(msg)
            assert trigger == "feedback_negative", f"Failed for: {msg}"
    
    def test_quick_info_extraction(self):
        """Test extracting all info from one message"""
        message = "laper brutal di teknik budget 15k"
        info = TriggerHandler.extract_quick_info(message)
        
        assert info.get("faculty") == "Teknik"
        assert info.get("hunger_level") == "brutal"
        assert info.get("budget") == 15000
    
    def test_no_trigger(self):
        """Test message with no trigger"""
        message = "ini pesan random tanpa trigger"
        trigger = TriggerHandler.detect_trigger(message)
        assert trigger is None

if __name__ == "__main__":
    pytest.main([__file__, "-v"])