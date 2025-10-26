"""
Long-term memory (LTM) - User profile and preferences
"""
from typing import Dict, List, Optional
from datetime import datetime
from src.database.models.user import User
from src.database.models.feedback import Feedback
import logging

logger = logging.getLogger(__name__)

class LongTermMemory:
    """
    Manages user's long-term memory:
    - Profile (faculty, preferences)
    - Food preferences (favorites, allergies)
    - Historical patterns
    """
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.profile = self._load_profile()
        
        self.hunger_patterns = []
        self.budget_patterns = []   # tambahin ini
        self.favorite_foods = []
        self.disliked_foods = []

    def get_budget_patterns(self):
        return self.budget_patterns

    
    def _load_profile(self) -> Dict:
        """Load user profile from database"""
        profile = User.get(self.user_id)
        
        if not profile:
            # Create new profile
            profile = User.create_or_update(self.user_id, {
                "faculty": None,
                "favorite_foods": [],
                "allergies": [],
                "budget_range": {},
                "hunger_patterns": [],
                "interaction_count": 0
            })
        
        return profile
    
    def get_faculty(self) -> Optional[str]:
        """Get user's faculty"""
        return self.profile.get("faculty")
    
    def update_faculty(self, faculty: str):
        """Update user's faculty"""
        User.update_preferences(self.user_id, {"faculty": faculty})
        self.profile = self._load_profile()
    
    def get_favorite_foods(self) -> List[str]:
        """Get user's favorite foods"""
        # Combine explicit favorites and positive feedback
        favorites = set(self.profile.get("favorite_foods", []))
        positive_foods = Feedback.get_positive_foods(self.user_id)
        favorites.update(positive_foods)
        return list(favorites)
    
    def add_favorite_food(self, food_name: str):
        """Add food to favorites"""
        current_favorites = self.profile.get("favorite_foods", [])
        if food_name not in current_favorites:
            current_favorites.append(food_name)
            User.update_preferences(self.user_id, {
                "favorite_foods": current_favorites
            })
            self.profile = self._load_profile()
    
    def get_allergies(self) -> List[str]:
        """Get user's food allergies"""
        return self.profile.get("allergies", [])
    
    def update_allergies(self, allergies: List[str]):
        """Update user's allergies"""
        User.update_preferences(self.user_id, {"allergies": allergies})
        self.profile = self._load_profile()
    
    def get_budget_range(self) -> Dict:
        """Get typical budget range"""
        return self.profile.get("budget_range", {})
    
    def update_budget_range(self, min_budget: int, max_budget: int):
        """Update budget preferences"""
        User.update_preferences(self.user_id, {
            "budget_range": {"min": min_budget, "max": max_budget}
        })
        self.profile = self._load_profile()
    
    def add_hunger_pattern(self, context: Dict):
        """Track hunger pattern for learning"""
        User.add_hunger_pattern(self.user_id, context)
    
    def get_hunger_patterns(self) -> List[Dict]:
        """Get historical hunger patterns"""
        return self.profile.get("hunger_patterns", [])
    
    def increment_interaction(self):
        """Increment interaction counter"""
        User.increment_interaction(self.user_id)
    
    def get_interaction_count(self) -> int:
        """Get total interactions"""
        return self.profile.get("interaction_count", 0)
    
    def is_returning_user(self) -> bool:
        """Check if user has interacted before"""
        return self.get_interaction_count() > 1
    
    def get_disliked_foods(self) -> List[str]:
        """Get foods user has disliked"""
        return Feedback.get_negative_foods(self.user_id)
    
    def get_summary(self) -> Dict:
        """Get summary of long-term memory"""
        return {
            "user_id": self.user_id,
            "faculty": self.get_faculty(),
            "favorite_foods": self.get_favorite_foods(),
            "allergies": self.get_allergies(),
            "budget_range": self.get_budget_range(),
            "interaction_count": self.get_interaction_count(),
            "disliked_foods": self.get_disliked_foods()
        }
    
    def get_preferences_summary(self):
        """Return a summary string of previous preferences"""
        summary = ""
        if self.get_hunger_patterns():
            summary += "Hunger patterns:\n"
            for i, h in enumerate(self.hunger_patterns[-5:], 1):
                summary += f"  {i}. Level: {h['hunger_level']}, Budget: {h['budget']}, Time: {h['time_period']}\n"
        if self.budget_patterns:
            summary += "Budget patterns: " + ", ".join(str(b) for b in self.budget_patterns[-5:]) + "\n"
        return summary or "Belum ada preferensi sebelumnya."