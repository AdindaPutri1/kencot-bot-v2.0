"""
Canteen model for UGM canteen data
"""
from typing import Dict, List, Optional
from src.database.connection import db_instance
import logging

logger = logging.getLogger(__name__)

class Canteen:
    """Canteen database with menus and location info"""
    
    COLLECTION = "ugm_canteens"
    
    @classmethod
    def get_all(cls) -> List[Dict]:
        """Get all canteens"""
        if db_instance.use_mongo:
            return list(db_instance[cls.COLLECTION].find({}))
        else:
            return db_instance[cls.COLLECTION].data.copy()
    
    @classmethod
    def get_by_name(cls, name: str) -> Optional[Dict]:
        """Get canteen by name (case-insensitive)"""
        name_lower = name.lower()
        
        if db_instance.use_mongo:
            import re
            return db_instance[cls.COLLECTION].find_one({
                "canteen_name": {"$regex": f"^{re.escape(name)}$", "$options": "i"}
            })
        
        # JSON manual search
        for canteen in db_instance[cls.COLLECTION].data:
            if canteen.get("canteen_name", "").lower() == name_lower:
                return canteen
        return None
    
    @classmethod
    def get_by_alias(cls, alias: str) -> Optional[Dict]:
        """Get canteen by alias"""
        alias_lower = alias.lower()
        
        if db_instance.use_mongo:
            return db_instance[cls.COLLECTION].find_one({
                "canteen_alias": {"$in": [alias]}
            })
        
        # JSON manual search
        for canteen in db_instance[cls.COLLECTION].data:
            aliases = [a.lower() for a in canteen.get("canteen_alias", [])]
            if alias_lower in aliases:
                return canteen
        return None
    
    @classmethod
    def get_by_faculty(cls, faculty: str) -> List[Dict]:
        """Get canteens near a faculty"""
        results = []
        
        if db_instance.use_mongo:
            cursor = db_instance[cls.COLLECTION].find({
                "faculty_proximity": {"$in": [faculty]}
            })
            results = list(cursor)
        else:
            # JSON manual search
            for canteen in db_instance[cls.COLLECTION].data:
                if faculty in canteen.get("faculty_proximity", []):
                    results.append(canteen)
        
        return results
    
    @classmethod
    def search_menu(cls, menu_name: str) -> List[Dict]:
        """Search for canteens that have a specific menu"""
        menu_lower = menu_name.lower()
        results = []
        
        if db_instance.use_mongo:
            cursor = db_instance[cls.COLLECTION].find({
                "menus.name": {"$regex": menu_name, "$options": "i"}
            })
            results = list(cursor)
        else:
            # JSON manual search
            for canteen in db_instance[cls.COLLECTION].data:
                for menu in canteen.get("menus", []):
                    if menu_lower in menu.get("name", "").lower():
                        results.append(canteen)
                        break
        
        return results
    
    @classmethod
    def filter_by_budget(cls, min_price: int, max_price: int) -> List[Dict]:
        """Get canteens within budget range"""
        results = []
        
        if db_instance.use_mongo:
            cursor = db_instance[cls.COLLECTION].find({
                "price_range_min": {"$lte": max_price},
                "price_range_max": {"$gte": min_price}
            })
            results = list(cursor)
        else:
            # JSON manual search
            for canteen in db_instance[cls.COLLECTION].data:
                if (canteen.get("price_range_min", 0) <= max_price and 
                    canteen.get("price_range_max", 999999) >= min_price):
                    results.append(canteen)
        
        return results
    
    @classmethod
    def get_menus_by_category(cls, category: str, faculty: str = None) -> List[Dict]:
        """Get menus by category, optionally filtered by faculty"""
        results = []
        canteens = cls.get_by_faculty(faculty) if faculty else cls.get_all()
        
        for canteen in canteens:
            for menu in canteen.get("menus", []):
                if menu.get("category") == category:
                    results.append({
                        "canteen": canteen.get("canteen_name"),
                        "menu_name": menu.get("name"),
                        "price": menu.get("price"),
                        "category": menu.get("category"),
                        "suitability": menu.get("suitability", [])
                    })
        
        return results
    
    @classmethod
    def get_menus_by_time(cls, time_period: str, faculty: str = None) -> List[Dict]:
        """Get menus suitable for a time period (pagi, siang, sore, malam)"""
        results = []
        canteens = cls.get_by_faculty(faculty) if faculty else cls.get_all()
        
        for canteen in canteens:
            for menu in canteen.get("menus", []):
                if time_period in menu.get("suitability", []):
                    results.append({
                        "canteen": canteen.get("canteen_name"),
                        "menu_name": menu.get("name"),
                        "price": menu.get("price"),
                        "category": menu.get("category"),
                        "gmaps_link": canteen.get("gmaps_link")
                    })
        
        return results
    
    @classmethod
    def recommend_by_context(cls, context: Dict) -> List[Dict]:
        """Recommend canteens based on context (faculty, budget, time)"""
        faculty = context.get("faculty")
        budget = context.get("budget", 999999)
        time_period = context.get("time_period", "siang")
        
        # Get canteens by faculty
        canteens = cls.get_by_faculty(faculty) if faculty else cls.get_all()
        
        # Filter by budget and time
        recommendations = []
        for canteen in canteens:
            if canteen.get("price_range_min", 0) <= budget:
                suitable_menus = []
                for menu in canteen.get("menus", []):
                    if (menu.get("price", 999999) <= budget and 
                        time_period in menu.get("suitability", [])):
                        suitable_menus.append(menu)
                
                if suitable_menus:
                    recommendations.append({
                        "canteen": canteen.get("canteen_name"),
                        "alias": canteen.get("canteen_alias", []),
                        "menus": suitable_menus,
                        "gmaps_link": canteen.get("gmaps_link")
                    })
        
        return recommendations