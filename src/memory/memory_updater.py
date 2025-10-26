"""
Memory updater - learns from user feedback
"""
import logging
from typing import Dict, List
from src.memory.long_term_memory import LongTermMemory
from src.database.models.feedback import Feedback

logger = logging.getLogger(__name__)

class MemoryUpdater:
    """Updates user preferences based on feedback"""
    
    @staticmethod
    def process_feedback(
        user_id: str,
        feedback_type: str,  # 'positive' or 'negative'
        context: Dict,
        recommended_foods: List[str]
    ):
        """
        Process user feedback and update memory
        
        Args:
            user_id: User identifier
            feedback_type: 'positive' (👍) or 'negative' (👎)
            context: Context when recommendation was made
            recommended_foods: Foods that were recommended
        """
        ltm = LongTermMemory(user_id)
        
        # Store feedback in database
        feedback_data = {
            "rating": 5 if feedback_type == "positive" else 1,
            "sentiment": feedback_type,
            "foods_recommended": recommended_foods,
            "faculty": context.get("faculty"),
            "hunger_level": context.get("hunger_level"),
            "budget": context.get("budget"),
            "time_period": context.get("time_period")
        }
        
        Feedback.create(user_id, feedback_data)
        
        # Update preferences based on feedback
        if feedback_type == "positive":
            MemoryUpdater._handle_positive_feedback(ltm, context, recommended_foods)
        else:
            MemoryUpdater._handle_negative_feedback(ltm, context, recommended_foods)
        
        logger.info(f"Processed {feedback_type} feedback for user {user_id}")
    
    @staticmethod
    def _handle_positive_feedback(
        ltm: LongTermMemory,
        context: Dict,
        foods: List[str]
    ):
        """Learn from positive feedback"""
        # Add foods to favorites
        for food in foods:
            ltm.add_favorite_food(food)
        
        budget_str = context.get("budget")
        if budget_str:
            # parse string seperti "15k" atau "20000" jadi integer
            if isinstance(budget_str, str):
                budget_str = budget_str.lower().replace("k", "")
                budget_num = int(budget_str) * 1000 if "k" in context.get("budget").lower() else int(budget_str)
            else:
                budget_num = int(budget_str)

            min_budget = budget_num
            max_budget = int(budget_num * 1.2)  # ±20% range
            ltm.update_budget_range(min_budget, max_budget)

        # Track hunger pattern
        ltm.add_hunger_pattern({
            "hunger_level": context.get("hunger_level"),
            "time_period": context.get("time_period"),
            "budget": budget_num  # <- ganti dari budget
        })

    
    @staticmethod
    def _handle_negative_feedback(
        ltm: LongTermMemory,
        context: Dict,
        foods: List[str]
    ):
        """Learn from negative feedback"""
        # Currently just log it
        # In future: could add to "disliked_foods" list
        logger.info(f"User disliked: {foods}")
        
        # Could implement:
        # - Track disliked ingredients
        # - Adjust recommendation weights
        # - Ask for specific feedback (too spicy? too expensive?)
    
    @staticmethod
    def analyze_feedback_patterns(user_id: str) -> Dict:
        """
        Analyze feedback patterns to improve recommendations
        
        Returns:
            Dict with insights
        """
        feedback_stats = Feedback.get_stats(user_id)
        positive_foods = Feedback.get_positive_foods(user_id)
        negative_foods = Feedback.get_negative_foods(user_id)
        
        insights = {
            "satisfaction_rate": feedback_stats.get("satisfaction_rate", 0),
            "liked_foods": positive_foods[:5],  # Top 5
            "disliked_foods": negative_foods[:5],
            "recommendations": []
        }
        
        # Generate recommendations for improvement
        if insights["satisfaction_rate"] < 50:
            insights["recommendations"].append(
                "Tingkat kepuasan rendah - pertimbangkan lebih banyak variasi"
            )
        
        if len(positive_foods) > 0:
            insights["recommendations"].append(
                f"User suka: {', '.join(positive_foods[:3])} - rekomendasikan yang mirip"
            )
        
        return insights
    
    @staticmethod
    def get_personalization_hints(user_id: str) -> List[str]:
        """
        Get hints for personalizing recommendations
        
        Returns:
            List of preference tags/keywords
        """
        ltm = LongTermMemory(user_id)
        positive_foods = Feedback.get_positive_foods(user_id)
        
        # Combine favorites and positive feedback
        all_liked = set(ltm.get_favorite_foods() + positive_foods)
        
        # In production, extract common tags from these foods
        # For now, return the food names as hints
        return list(all_liked)[:10]