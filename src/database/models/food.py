"""
Food model with nutrition and embedding data
Adapted to use hybrid database (MongoDB or JSON)
"""
from typing import Dict, List, Optional
from src.config import Config
from src.database.connection import db_instance
import logging

logger = logging.getLogger(__name__)

class Food:
    """Food database with nutrition and embeddings"""
    
    COLLECTION = "foods"
    
    @classmethod
    def load_from_json(cls, file_path: str = None) -> int:
        """Load foods from JSON file into database"""
        import json
        from pathlib import Path

        if file_path is None:
            file_path = Config.FOODS_PATH

        path = Path(file_path)
        if not path.exists():
            logger.warning(f"Food JSON file not found: {file_path}")
            return 0

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            foods = data.get("foods", [])
            if foods:
                # Clear existing data
                db_instance[cls.COLLECTION].delete_many({})

                # Insert new data
                for food in foods:
                    db_instance[cls.COLLECTION].insert_one(food)
                
                # Save if using JSON
                if not db_instance.use_mongo:
                    db_instance.save()
                
                logger.info(f"Loaded {len(foods)} foods from JSON")
                return len(foods)
            else:
                logger.warning("No foods found in JSON file")
                return 0
        except Exception as e:
            logger.error(f"Error loading foods: {e}", exc_info=True)
            return 0

    @classmethod
    def get_by_id(cls, food_id: str) -> Optional[Dict]:
        """Get food by ID"""
        return db_instance[cls.COLLECTION].find_one({"food_id": food_id})

    @classmethod
    def get_by_name(cls, name: str) -> Optional[Dict]:
        """Get food by name (case-insensitive)"""
        name_lower = name.lower()
        
        # For MongoDB, use regex
        if db_instance.use_mongo:
            import re
            return db_instance[cls.COLLECTION].find_one({
                "name": {"$regex": f"^{re.escape(name)}$", "$options": "i"}
            })
        
        # For JSON, manual search
        for food in db_instance[cls.COLLECTION].data:
            if food.get("name", "").lower() == name_lower:
                return food
        return None

    @classmethod
    def search_by_tags(cls, tags: List[str], limit: int = 10) -> List[Dict]:
        """Search foods by tags"""
        results = []
        
        if db_instance.use_mongo:
            # MongoDB query
            cursor = db_instance[cls.COLLECTION].find({
                "tags": {"$in": tags}
            }).limit(limit)
            results = list(cursor)
        else:
            # JSON manual search
            for food in db_instance[cls.COLLECTION].data:
                if "tags" in food and any(tag in food["tags"] for tag in tags):
                    results.append(food)
                if len(results) >= limit:
                    break
        
        return results

    @classmethod
    def get_all(cls) -> List[Dict]:
        """Get all foods"""
        if db_instance.use_mongo:
            return list(db_instance[cls.COLLECTION].find({}))
        else:
            return db_instance[cls.COLLECTION].data.copy()

    @classmethod
    def get_embeddings(cls) -> List[Dict]:
        """Get all food embeddings for similarity search"""
        embeddings = []
        
        if db_instance.use_mongo:
            cursor = db_instance[cls.COLLECTION].find({}, {
                "food_id": 1,
                "name": 1,
                "embedding": 1
            })
            for food in cursor:
                embeddings.append({
                    "food_id": food.get("food_id"),
                    "name": food.get("name"),
                    "embedding": food.get("embedding", [])
                })
        else:
            for food in db_instance[cls.COLLECTION].data:
                embeddings.append({
                    "food_id": food.get("food_id"),
                    "name": food.get("name"),
                    "embedding": food.get("embedding", [])
                })
        
        return embeddings

    @classmethod
    def calculate_total_nutrition(cls, food_ids: List[str]) -> Dict:
        """Calculate total nutrition from multiple foods"""
        total = {
            "calories": 0,
            "protein": 0,
            "fat": 0,
            "carbs": 0,
            "foods": []
        }
        for fid in food_ids:
            food = cls.get_by_id(fid)
            if food:
                total["calories"] += food.get("calories", 0)
                total["protein"] += food.get("protein", 0)
                total["fat"] += food.get("fat", 0)
                total["carbs"] += food.get("carbs", 0)
                total["foods"].append({
                    "name": food.get("name"),
                    "calories": food.get("calories", 0)
                })
        return total