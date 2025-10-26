"""
Feedback model for storing user feedback on recommendations
"""
from datetime import datetime
from typing import Dict, List, Optional
from src.database.connection import db_instance

class Feedback:
    """User feedback storage and analysis"""
    
    COLLECTION = "feedbacks"
    
    @classmethod
    def create(cls, user_id: str, feedback_data: Dict) -> Dict:
        """Store user feedback"""
        feedback = {
            "user_id": user_id,
            "recommendation_id": feedback_data.get("recommendation_id"),
            "foods_recommended": feedback_data.get("foods_recommended", []),
            "rating": feedback_data.get("rating"),  # 1 (👎) or 5 (👍)
            "sentiment": feedback_data.get("sentiment"),  # positive/negative
            "context": {
                "faculty": feedback_data.get("faculty"),
                "hunger_level": feedback_data.get("hunger_level"),
                "budget": feedback_data.get("budget"),
                "time_period": feedback_data.get("time_period")
            },
            "comment": feedback_data.get("comment"),
            "created_at": datetime.utcnow()
        }
        
        db_instance[cls.COLLECTION].insert_one(feedback)
        
        # Save if using JSON
        if not db_instance.use_mongo:
            db_instance.save()
        
        return feedback
    
    @classmethod
    def get_user_feedbacks(cls, user_id: str, limit: int = 10) -> List[Dict]:
        """Get recent feedbacks from user"""
        if db_instance.use_mongo:
            return list(db_instance[cls.COLLECTION].find(
                {"user_id": user_id}
            ).sort("created_at", -1).limit(limit))
        else:
            # JSON manual search
            feedbacks = [f for f in db_instance[cls.COLLECTION].data 
                        if f.get("user_id") == user_id]
            # Sort by created_at descending
            feedbacks.sort(key=lambda x: x.get("created_at", datetime.min), reverse=True)
            return feedbacks[:limit]
    
    @classmethod
    def get_positive_foods(cls, user_id: str) -> List[str]:
        """Get foods that user liked (for preference learning)"""
        foods = []
        
        if db_instance.use_mongo:
            positive_feedbacks = db_instance[cls.COLLECTION].find({
                "user_id": user_id,
                "rating": {"$gte": 4}
            })
            for fb in positive_feedbacks:
                foods.extend(fb.get("foods_recommended", []))
        else:
            # JSON manual search
            for fb in db_instance[cls.COLLECTION].data:
                if fb.get("user_id") == user_id and fb.get("rating", 0) >= 4:
                    foods.extend(fb.get("foods_recommended", []))
        
        return list(set(foods))  # Remove duplicates
    
    @classmethod
    def get_negative_foods(cls, user_id: str) -> List[str]:
        """Get foods that user disliked"""
        foods = []
        
        if db_instance.use_mongo:
            negative_feedbacks = db_instance[cls.COLLECTION].find({
                "user_id": user_id,
                "rating": {"$lte": 2}
            })
            for fb in negative_feedbacks:
                foods.extend(fb.get("foods_recommended", []))
        else:
            # JSON manual search
            for fb in db_instance[cls.COLLECTION].data:
                if fb.get("user_id") == user_id and fb.get("rating", 0) <= 2:
                    foods.extend(fb.get("foods_recommended", []))
        
        return list(set(foods))
    
    @classmethod
    def get_stats(cls, user_id: str = None) -> Dict:
        """Get feedback statistics"""
        query = {"user_id": user_id} if user_id else {}
        
        total = db_instance[cls.COLLECTION].count_documents(query)
        
        # Count positive (rating >= 4)
        if db_instance.use_mongo:
            positive = db_instance[cls.COLLECTION].count_documents({**query, "rating": {"$gte": 4}})
            negative = db_instance[cls.COLLECTION].count_documents({**query, "rating": {"$lte": 2}})
        else:
            # JSON manual count
            if user_id:
                feedbacks = [f for f in db_instance[cls.COLLECTION].data if f.get("user_id") == user_id]
            else:
                feedbacks = db_instance[cls.COLLECTION].data
            
            positive = sum(1 for f in feedbacks if f.get("rating", 0) >= 4)
            negative = sum(1 for f in feedbacks if f.get("rating", 0) <= 2)
        
        return {
            "total": total,
            "positive": positive,
            "negative": negative,
            "satisfaction_rate": (positive / total * 100) if total > 0 else 0
        }