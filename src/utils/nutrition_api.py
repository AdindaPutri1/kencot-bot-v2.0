import requests
from deep_translator import GoogleTranslator
from typing import Dict
from src.utils.config import Config

class NutritionTool:
    """Translate makanan ke Inggris dan ambil data nutrisi dari API Ninjas"""

    API_KEY = Config.NUTRITION_API_KEY
    BASE_URL = "https://api.api-ninjas.com/v1/nutrition"

    def __init__(self):
        self.headers = {"X-Api-Key": self.API_KEY}
        # ganti googletrans dengan deep-translator
        self.translator = GoogleTranslator(source='id', target='en')

    def translate_to_english(self, food_name: str) -> str:
        """Translate food name ke bahasa Inggris"""
        try:
            translated = self.translator.translate(food_name)
            return translated
        except Exception:
            return food_name

    def get_nutrition(self, food_name: str) -> Dict:
        """Ambil info nutrisi makanan, setelah diterjemahkan ke Inggris"""
        english_name = self.translate_to_english(food_name)
        params = {"query": english_name}
        try:
            response = requests.get(self.BASE_URL, headers=self.headers, params=params, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list) and len(data) > 0:
                    return data[0]
                return {"error": "No data found"}
            else:
                return {"error": f"API error: {response.status_code}"}
        except requests.RequestException as e:
            return {"error": str(e)}
