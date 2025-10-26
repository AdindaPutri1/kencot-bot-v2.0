"""
User model for long-term memory storage
"""
from datetime import datetime
from typing import Dict, List, Optional
from src.database.connection import db_instance

class User:
    """User profile and preferences (long-term memory)"""
    
    COLLECTION = "users"
    
    @classmethod
    def create_or_update(cls, user_id: str, data: Dict) -> Dict:
        """Create or update user profile"""
        user_data = {
            "user_id": user_id,
            "faculty": data.get("faculty"),
            "favorite_foods": data.get("favorite_foods", []),
            "allergies": data.get("allergies", []),
            "budget_range": data.get("budget_range", {}),
            "hunger_patterns": data.get("hunger_patterns", []),
            "interaction_count": data.get("interaction_count", 0),
            "last_interaction": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        db_instance[cls.COLLECTION].update_one(
            {"user_id": user_id},
            {"$set": user_data, "$setOnInsert": {"created_at": datetime.utcnow()}},
            upsert=True
        )
        
        # Save if using JSON
        if not db_instance.use_mongo:
            db_instance.save()
        
        return cls.get(user_id)
    
    @classmethod
    def get(cls, user_id: str) -> Optional[Dict]:
        """Get user profile"""
        return db_instance[cls.COLLECTION].find_one({"user_id": user_id})
    
    @classmethod
    def update_preferences(cls, user_id: str, preferences: Dict) -> Dict:
        """Update user preferences incrementally"""
        update_data = {"updated_at": datetime.utcnow()}
        update_ops = {"$set": update_data}
        
        if "favorite_foods" in preferences:
            update_ops["$addToSet"] = {
                "favorite_foods": {"$each": preferences["favorite_foods"]}
            }
        
        if "allergies" in preferences:
            update_data["allergies"] = preferences["allergies"]
        
        if "budget_range" in preferences:
            update_data["budget_range"] = preferences["budget_range"]
        
        db_instance[cls.COLLECTION].update_one(
            {"user_id": user_id},
            update_ops
        )
        
        # Save if using JSON
        if not db_instance.use_mongo:
            db_instance.save()
        
        return cls.get(user_id)
    
    @classmethod
    def increment_interaction(cls, user_id: str):
        """Increment interaction counter"""
        db_instance[cls.COLLECTION].update_one(
            {"user_id": user_id},
            {
                "$inc": {"interaction_count": 1},
                "$set": {"last_interaction": datetime.utcnow()}
            }
        )
        
        # Save if using JSON
        if not db_instance.use_mongo:
            db_instance.save()
    
    @classmethod
    def add_hunger_pattern(cls, user_id: str, pattern: Dict):
        """Track hunger patterns for personalization"""
        pattern_data = {
            "hunger_level": pattern.get("hunger_level"),
            "time_period": pattern.get("time_period"),
            "budget": pattern.get("budget"),
            "timestamp": datetime.utcnow()
        }
        
        db_instance[cls.COLLECTION].update_one(
            {"user_id": user_id},
            {"$push": {
                "hunger_patterns": {
                    "$each": [pattern_data],
                    "$slice": -20  # Keep only last 20 patterns
                }
            }}
        )
        
        # Save if using JSON
        if not db_instance.use_mongo:
            db_instance.save()