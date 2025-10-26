"""
Time utilities for time-based recommendations
"""
from datetime import datetime, timedelta

def get_current_time_period() -> str:
    """
    Get current time period in WIB (Jakarta time)
    
    Returns:
        'pagi', 'siang', 'sore', or 'malam'
    """
    # Assuming server runs in UTC, adjust to WIB (UTC+7)
    now = datetime.utcnow() + timedelta(hours=7)
    hour = now.hour
    
    if 5 <= hour < 11:
        return 'pagi'
    elif 11 <= hour < 15:
        return 'siang'
    elif 15 <= hour < 18:
        return 'sore'
    else:
        return 'malam'

def get_time_greeting() -> str:
    """Get time-appropriate greeting"""
    period = get_current_time_period()
    
    greetings = {
        'pagi': 'Selamat pagi! ☀️',
        'siang': 'Selamat siang! 🌤️',
        'sore': 'Selamat sore! 🌅',
        'malam': 'Selamat malam! 🌙'
    }
    
    return greetings.get(period, 'Halo!')

def is_meal_time() -> bool:
    """Check if it's typical meal time"""
    now = datetime.utcnow() + timedelta(hours=7)
    hour = now.hour
    
    # Breakfast: 6-9, Lunch: 11-14, Dinner: 17-20
    return (6 <= hour <= 9) or (11 <= hour <= 14) or (17 <= hour <= 20)

def get_meal_time_category() -> str:
    """Get specific meal time"""
    now = datetime.utcnow() + timedelta(hours=7)
    hour = now.hour
    
    if 6 <= hour <= 9:
        return 'sarapan'
    elif 11 <= hour <= 14:
        return 'makan_siang'
    elif 17 <= hour <= 20:
        return 'makan_malam'
    else:
        return 'cemilan'