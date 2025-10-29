# src/utils/nutrition_estimator.py
from typing import Optional

class NutritionEstimator:
    @staticmethod
    def estimate_calories(
        protein_g: Optional[float] = 0,
        carbs_g: Optional[float] = 0,
        fat_g: Optional[float] = 0
    ) -> float:
        """
        Hitung kalori dari makronutrien:
        - Protein & Karbohidrat = 4 kcal per gram
        - Lemak = 9 kcal per gram
        """
        try:
            protein = float(protein_g)
        except (ValueError, TypeError):
            protein = 0

        try:
            carbs = float(carbs_g)
        except (ValueError, TypeError):
            carbs = 0

        try:
            fat = float(fat_g)
        except (ValueError, TypeError):
            fat = 0

        calories = protein*4 + carbs*4 + fat*9
        return round(calories, 2)
