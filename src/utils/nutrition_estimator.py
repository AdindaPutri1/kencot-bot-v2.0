"""
Nutrition estimator for Indonesian foods
"""
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class NutritionEstimator:
    """Estimate nutrition values for Indonesian foods"""
    
    # Nutrition database (per 100g or per serving)
    NUTRITION_DB = {
        # Nasi-based dishes
        "nasi goreng": {"calories": 250, "protein": 8, "fat": 10, "carbs": 35},
        "nasi rames": {"calories": 450, "protein": 18, "fat": 15, "carbs": 60},
        "nasi campur": {"calories": 450, "protein": 18, "fat": 15, "carbs": 60},
        "nasi putih": {"calories": 180, "protein": 4, "fat": 0.5, "carbs": 40},
        "nasi sayur": {"calories": 200, "protein": 5, "fat": 3, "carbs": 38},
        "nasi pecel": {"calories": 350, "protein": 12, "fat": 8, "carbs": 55},
        
        # Ayam dishes
        "ayam geprek": {"calories": 400, "protein": 25, "fat": 18, "carbs": 35},
        "ayam goreng": {"calories": 380, "protein": 28, "fat": 20, "carbs": 25},
        "ayam bakar": {"calories": 320, "protein": 30, "fat": 12, "carbs": 25},
        "ayam penyet": {"calories": 400, "protein": 25, "fat": 18, "carbs": 35},
        "chicken katsu": {"calories": 420, "protein": 26, "fat": 20, "carbs": 35},
        "chicken steak": {"calories": 380, "protein": 28, "fat": 18, "carbs": 30},
        
        # Mie dishes
        "mie ayam": {"calories": 350, "protein": 15, "fat": 12, "carbs": 45},
        "mie goreng": {"calories": 400, "protein": 12, "fat": 15, "carbs": 55},
        "indomie": {"calories": 380, "protein": 10, "fat": 16, "carbs": 52},
        "mama mie": {"calories": 380, "protein": 10, "fat": 16, "carbs": 52},
        "mie dok-dok": {"calories": 420, "protein": 14, "fat": 18, "carbs": 50},
        
        # Soup dishes
        "soto ayam": {"calories": 250, "protein": 18, "fat": 8, "carbs": 25},
        "soto": {"calories": 250, "protein": 18, "fat": 8, "carbs": 25},
        "bakso": {"calories": 280, "protein": 15, "fat": 10, "carbs": 30},
        "rawon": {"calories": 320, "protein": 22, "fat": 12, "carbs": 28},
        
        # Vegetable dishes
        "gado-gado": {"calories": 280, "protein": 10, "fat": 12, "carbs": 35},
        "pecel": {"calories": 250, "protein": 9, "fat": 10, "carbs": 32},
        "lotek": {"calories": 240, "protein": 8, "fat": 10, "carbs": 30},
        "sayur lodeh": {"calories": 180, "protein": 5, "fat": 8, "carbs": 22},
        
        # Other dishes
        "steak": {"calories": 450, "protein": 30, "fat": 25, "carbs": 30},
        "batagor": {"calories": 320, "protein": 12, "fat": 18, "carbs": 28},
        "dimsum": {"calories": 200, "protein": 8, "fat": 10, "carbs": 18},
        "magelangan": {"calories": 380, "protein": 14, "fat": 16, "carbs": 45},
        
        # Snacks
        "gorengan": {"calories": 150, "protein": 3, "fat": 8, "carbs": 18},
        "waffle": {"calories": 280, "protein": 5, "fat": 12, "carbs": 38},
        
        # Drinks
        "jus": {"calories": 80, "protein": 1, "fat": 0, "carbs": 18},
        "kopi": {"calories": 20, "protein": 1, "fat": 0, "carbs": 3},
        
        # Telur dishes
        "telur": {"calories": 155, "protein": 13, "fat": 11, "carbs": 1},
        "telur penyet": {"calories": 200, "protein": 14, "fat": 14, "carbs": 8},
    }
    
    # Category defaults
    CATEGORY_DEFAULTS = {
        "makanan_berat": {"calories": 400, "protein": 18, "fat": 15, "carbs": 50},
        "makanan_ringan": {"calories": 250, "protein": 8, "fat": 10, "carbs": 30},
        "cemilan": {"calories": 150, "protein": 3, "fat": 8, "carbs": 18},
        "minuman": {"calories": 80, "protein": 1, "fat": 0, "carbs": 18},
    }
    
    def estimate_nutrition(self, food: Dict) -> Dict:
        """
        Estimate nutrition for a food item
        
        Args:
            food: Food dict with name and category
            
        Returns:
            Food dict with added nutrition fields
        """
        name_lower = food.get("name", "").lower()
        category = food.get("category", "")
        
        # Try exact match first
        for key, nutrition in self.NUTRITION_DB.items():
            if key in name_lower:
                food["calories"] = nutrition["calories"]
                food["protein"] = nutrition["protein"]
                food["fat"] = nutrition["fat"]
                food["carbs"] = nutrition["carbs"]
                logger.debug(f"Matched '{name_lower}' with '{key}'")
                return food
        
        # Fallback to category default
        if category in self.CATEGORY_DEFAULTS:
            default = self.CATEGORY_DEFAULTS[category]
            food["calories"] = default["calories"]
            food["protein"] = default["protein"]
            food["fat"] = default["fat"]
            food["carbs"] = default["carbs"]
            logger.debug(f"Using category default for '{name_lower}': {category}")
        else:
            # Ultimate fallback
            food["calories"] = 300
            food["protein"] = 10
            food["fat"] = 10
            food["carbs"] = 40
            logger.warning(f"No nutrition data for '{name_lower}', using generic values")
        
        return food
    
    def enrich_foods(self, foods: list) -> list:
        """Add nutrition estimates to list of foods"""
        return [self.estimate_nutrition(food.copy()) for food in foods]

# Global instance
nutrition_estimator = NutritionEstimator()