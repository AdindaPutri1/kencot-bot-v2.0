from pymongo.collection import Collection
from pymongo import ASCENDING

class UserMemoryModel:
    """Permanent memory (LTM) storage in MongoDB"""

    def __init__(self, collection: Collection):
        self.collection = collection
        self.collection.create_index([("user_id", ASCENDING)], unique=True)

    def get_memory(self, user_id: str) -> dict:
        doc = self.collection.find_one({"user_id": user_id})
        return doc.get("memory", {}) if doc else {}

    def add_liked_food(self, user_id: str, food_name: str):
        self.collection.update_one(
            {"user_id": user_id},
            {"$addToSet": {"memory.liked_foods": food_name}},
            upsert=True
        )

    def add_disliked_food(self, user_id: str, food_name: str):
        self.collection.update_one(
            {"user_id": user_id},
            {"$addToSet": {"memory.disliked_foods": food_name}},
            upsert=True
        )

    def add_allergy(self, user_id: str, allergen: str):
        self.collection.update_one(
            {"user_id": user_id},
            {"$addToSet": {"memory.allergies": allergen}},
            upsert=True
        )

    def reset_memory(self, user_id: str):
        self.collection.update_one({"user_id": user_id}, {"$set": {"memory": {}}})
