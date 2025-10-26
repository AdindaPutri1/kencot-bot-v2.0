"""
Calorie calculation and nutrition utilities
"""
from typing import List, Dict

def calculate_total_calories(foods: List[Dict]) -> Dict:
    """
    Calculate total calories and macros from multiple foods
    
    Args:
        foods: List of food items with nutrition data
        
    Returns:
        Dict with totals and breakdown
    """
    total = {
        "total_calories": 0,
        "total_protein": 0,
        "total_fat": 0,
        "total_carbs": 0,
        "foods": []
    }
    
    for food in foods:
        calories = food.get("calories", 0)
        protein = food.get("protein", 0)
        fat = food.get("fat", 0)
        carbs = food.get("carbs", 0)
        
        total["total_calories"] += calories
        total["total_protein"] += protein
        total["total_fat"] += fat
        total["total_carbs"] += carbs
        
        total["foods"].append({
            "name": food.get("name", "Unknown"),
            "calories": calories,
            "protein": protein,
            "fat": fat,
            "carbs": carbs
        })
    
    return total

def format_nutrition_summary(nutrition: Dict) -> str:
    """
    Format nutrition data into friendly text
    
    Args:
        nutrition: Dict from calculate_total_calories
        
    Returns:
        Formatted string
    """
    lines = ["📊 *Total Nutrisi:*"]
    lines.append(f"🔥 Kalori: {nutrition['total_calories']} kkal")
    lines.append(f"💪 Protein: {nutrition['total_protein']}g")
    lines.append(f"🧈 Lemak: {nutrition['total_fat']}g")
    lines.append(f"🍚 Karbohidrat: {nutrition['total_carbs']}g")
    
    lines.append("\n📋 *Detail per Menu:*")
    for food in nutrition["foods"]:
        lines.append(
            f"• {food['name']}: {food['calories']} kkal "
            f"(P: {food['protein']}g, F: {food['fat']}g, C: {food['carbs']}g)"
        )
    
    return "\n".join(lines)

def estimate_calories_needed(hunger_level: str) -> Dict:
    """
    Estimate calorie needs based on hunger level
    
    Args:
        hunger_level: 'brutal', 'standar', or 'iseng'
        
    Returns:
        Dict with min/max calorie range
    """
    ranges = {
        "brutal": {"min": 600, "max": 1000, "description": "Makan berat porsi besar"},
        "standar": {"min": 400, "max": 700, "description": "Makan standar kenyang"},
        "iseng": {"min": 100, "max": 400, "description": "Cemilan ringan"}
    }
    
    return ranges.get(hunger_level, ranges["standar"])

def check_nutrition_balance(nutrition: Dict) -> List[str]:
    """
    Check if nutrition is balanced and provide tips
    
    Args:
        nutrition: Dict from calculate_total_calories
        
    Returns:
        List of tips/warnings
    """
    tips = []
    
    total_calories = nutrition.get("total_calories", 0)
    protein = nutrition.get("total_protein", 0)
    fat = nutrition.get("total_fat", 0)
    carbs = nutrition.get("total_carbs", 0)
    
    # Protein check (should be 15-30% of calories)
    protein_calories = protein * 4
    protein_percentage = (protein_calories / total_calories * 100) if total_calories > 0 else 0
    
    if protein_percentage < 15:
        tips.append("⚠️ Proteinnya kurang nih, coba tambah lauk protein!")
    elif protein_percentage > 30:
        tips.append("💪 Wah, protein tinggi banget! Cocok buat yang lagi workout.")
    
    # Fat check (should be 20-35% of calories)
    fat_calories = fat * 9
    fat_percentage = (fat_calories / total_calories * 100) if total_calories > 0 else 0
    
    if fat_percentage > 40:
        tips.append("🧈 Lemaknya agak tinggi nih, hati-hati ya!")
    
    # Calorie check
    if total_calories > 1000:
        tips.append("🔥 Kalorinya lumayan tinggi, cocok buat yang lagi butuh energi banyak!")
    elif total_calories < 300:
        tips.append("😋 Porsi ringan nih, cocok buat cemilan!")
    
    if not tips:
        tips.append("✅ Nutrisinya seimbang! Mantap pilihannya!")
    
    return tips