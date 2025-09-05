# app/bot.py
"""
Kencot Bot - Main bot logic with conversation flow management.
This class handles the user's conversation state and calls utility functions.
"""

import logging
import re
import random  # <-- TAMBAHKAN INI
from datetime import datetime
from typing import Dict, List
from . import utils


logger = logging.getLogger(__name__)

class KencotBot:
    def __init__(self, config):
        """Initializes the bot with configuration and data."""
        self.config = config
        self.conversation_states: Dict[str, Dict] = {}
        self.responses = utils.load_responses(config.RESPONSES_PATH)
        self.canteens_db = utils.load_database(config.DATABASE_PATH)
        
        # Simple regex for initial trigger and reset
        self.triggers = {
            'food': re.compile(r'\b(laper|lapar|hungry|kencot|makan|mam|rekomen)\b', re.IGNORECASE),
            'reset': re.compile(r'\b(ulang|reset|restart|mulai lagi|cancel|batal)\b', re.IGNORECASE)
        }

    def _reset_conversation(self, user_id: str) -> str:
        """Resets the conversation state for a user."""
        self.conversation_states[user_id] = {'phase': 'idle', 'data': {}}
        return "Siap! Udah direset nih. Kalau laper lagi tinggal bilang aja ya! 😊"

    def handle_message(self, user_id: str, message: str) -> str:
        """Main message handler that routes to the correct conversation phase."""
        state = self.conversation_states.get(user_id, {'phase': 'idle', 'data': {}})
        
        # Handle reset command anytime
        if self.triggers['reset'].search(message):
            return self._reset_conversation(user_id)

        phase = state['phase']
        
        try:
            if phase == 'idle':
                return self._handle_idle_phase(user_id, message)
            elif phase == 'waiting_location':
                return self._handle_location_phase(user_id, message, state)
            elif phase == 'waiting_hunger':
                return self._handle_hunger_phase(user_id, message, state)
            elif phase == 'waiting_budget':
                return self._handle_budget_phase(user_id, message, state)
        except Exception as e:
            logger.error(f"Error in phase '{phase}' for user {user_id}: {e}")
            self.conversation_states[user_id] = {'phase': 'idle', 'data': {}} # Reset state on error
            return self.responses.get("error", ["Aduh, mamang lagi error nih, coba lagi ya."])[0]

        # Default fallback
        return self._handle_idle_phase(user_id, message)

    def _handle_idle_phase(self, user_id: str, message: str) -> str:
        """Handles the initial interaction."""
        if self.triggers['food'].search(message):
            self.conversation_states[user_id] = {'phase': 'waiting_location', 'data': {}}
            greeting = random.choice(self.responses['greetings'])
            location_ask = random.choice(self.responses['location_ask'])
            return f"{greeting}\n\n{location_ask}"
        return "Hai! Aku Mamang UGM, siap bantu kamu cari makan. Bilang aja 'laper' buat mulai! 😉"

    def _handle_location_phase(self, user_id: str, message: str, state: Dict) -> str:
        """Handles the location input phase."""
        faculty = utils.extract_faculty_from_text(message)
        if faculty:
            state['data']['faculty'] = faculty
            state['phase'] = 'waiting_hunger'
            self.conversation_states[user_id] = state

            hunger_ask_data = self.responses['hunger_level_ask']
            question = hunger_ask_data['question']
            options = "\n".join([f"{key}. {value}" for key, value in hunger_ask_data['options'].items()])
            return f"Siap, {faculty} noted! 📍\n\n{question}\n{options}"
        return random.choice(self.responses['location_ask_fail'])

    def _handle_hunger_phase(self, user_id: str, message: str, state: Dict) -> str:
        """Handles the hunger level input phase."""
        hunger_level = utils.extract_hunger_level_from_text(message)
        if hunger_level:
            state['data']['hunger_level'] = hunger_level
            state['phase'] = 'waiting_budget'
            self.conversation_states[user_id] = state
            return random.choice(self.responses['budget_ask'])
        return random.choice(self.responses['hunger_ask_fail'])

    def _handle_budget_phase(self, user_id: str, message: str, state: Dict) -> str:
        """Handles the budget input and generates the final recommendation."""
        budget = utils.extract_budget_from_text(message)
        if budget:
            state['data']['budget'] = budget
            
            # All data collected, generate recommendations!
            recommendations = utils.find_recommendations(
                self.canteens_db,
                state['data']['faculty'],
                state['data']['budget'],
                state['data']['hunger_level']
            )

            # Reset conversation for next time
            self._reset_conversation(user_id)
            
            if not recommendations:
                return random.choice(self.responses['no_result'])
            
            return self._format_recommendations_response(recommendations, state['data'])
        
        return random.choice(self.responses['budget_ask_fail'])
        
    def _format_recommendations_response(self, recommendations: List[Dict], user_data: Dict) -> str:
        """Formats the final recommendation message in Gen Z style."""
        # This is where you would call an LLM in the future.
        # For now, we use a dynamic template.
        header = f"Gini deh, karena kamu lagi di {user_data.get('faculty')} dan lagi {user_data.get('hunger_level')}, ini 2 opsi paling mantul buat kamu: ✨\n"
        
        body = ""
        for i, rec in enumerate(recommendations):
            emoji = "🍽️" if i == 0 else "🍜"
            body += (
                f"\n{emoji} *{rec['menu_name']}* di *{rec['canteen_name']}*\n"
                f"   💰 Harga cuma *Rp {rec['menu_price']:,}* (pas buat budget-mu!)\n"
                f"   📍 Cus kesini: {rec['gmaps_link']}\n"
            )
            
        footer = "\nGaskeun cobain salah satunya! Kalau butuh lagi, tinggal chat mamang aja ya! 😋"
        
        return header + body + footer