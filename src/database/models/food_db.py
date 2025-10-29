from pathlib import Path
import json
from src.utils.config import Config

class FoodDB:
    def __init__(self, canteens=None):
        self.canteens = canteens or []

    def load_from_json(self, json_path=None):
        """Load data kantin dari file JSON"""
        if json_path is None:
            json_path = Config.DATABASE_PATH

        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        self.canteens = data.get("ugm_canteens", [])
        print(f"✅ Loaded {len(self.canteens)} canteens from JSON.")

    def get_all_menus(self):
        menus = []
        for c in self.canteens:
            for m in c.get("menus", []):
                menus.append({
                    "canteen_name": c["canteen_name"],
                    "faculty_proximity": c.get("faculty_proximity", []),
                    "menu_name": m["name"],
                    "price": m.get("price"),
                    "category": m.get("category"),
                    "suitability": m.get("suitability", []),
                    "gmaps_link": c.get("gmaps_link")
                })
        return menus
    
food_db = FoodDB()
