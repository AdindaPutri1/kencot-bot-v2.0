import logging
import re
import random
from typing import Dict, List
from . import utils

logger = logging.getLogger(__name__)

class KencotBot:
    def __init__(self, config):
        self.config = config
        self.conversation_states: Dict[str, Dict] = {}
        self.responses = utils.load_responses(config.RESPONSES_PATH)
        self.canteens_db = utils.load_database(config.DATABASE_PATH)

        # Regex triggers
        self.triggers = {
            'food': re.compile(r'\b(laper|lapar|hungry|kencot|makan|mam|rekomen)\b', re.IGNORECASE),
            'reset': re.compile(r'\b(ulang|reset|restart|mulai lagi|cancel|batal)\b', re.IGNORECASE)
        }

    def _reset_conversation(self, user_id: str) -> str:
        self.conversation_states[user_id] = {'phase': 'idle', 'data': {}}
        return "Siap! Udah direset nih. Kalau laper lagi tinggal bilang aja ya! 😊"

    def handle_message(self, user_id: str, message: str) -> str:
        """Main handler dengan smart check kalau semua info udah ada."""
        state = self.conversation_states.get(user_id, {'phase': 'idle', 'data': {}})

        # Reset command
        if self.triggers['reset'].search(message):
            return self._reset_conversation(user_id)

        # --- Smart check: coba ekstrak semua langsung ---
        faculty = utils.extract_faculty_from_text(message)
        hunger_level = utils.extract_hunger_level_from_text(message)
        budget = utils.extract_budget_from_text(message)

        if faculty and hunger_level and budget:
            logger.info(f"All info detected langsung: {faculty}, {hunger_level}, {budget}")
            
            # --- Tambahin check budget kecil ---
            if budget <= 1500:
                self._reset_conversation(user_id)
                return f"Aduh in this economy gada makanan harganya {budget}. Kamu puasa aja dulu yah 🥲"

            recs = utils.find_recommendations(self.canteens_db, faculty, budget, hunger_level)
            self._reset_conversation(user_id)
            if not recs:
                return random.choice(self.responses['no_result'])
            return self._format_recommendations_response(recs, {
                "faculty": faculty,
                "hunger_level": hunger_level,
                "budget": budget
            })

        # Kalau ga lengkap, jalanin state machine biasa
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
            logger.error(f"Error in phase '{phase}' for user {user_id}: {e}", exc_info=True)
            self.conversation_states[user_id] = {'phase': 'idle', 'data': {}}
            return self.responses.get("error", ["Aduh, mamang lagi error nih, coba lagi ya."])[0]

        return self._handle_idle_phase(user_id, message)

    # --- State Handlers ---
    def _handle_idle_phase(self, user_id: str, message: str) -> str:
        if self.triggers['food'].search(message):
            self.conversation_states[user_id] = {'phase': 'waiting_location', 'data': {}}
            return f"{random.choice(self.responses['greetings'])}\n\n{random.choice(self.responses['location_ask'])}"
        return "Hai! Aku Mamang UGM, siap bantu kamu cari makan. Bilang aja 'laper' buat mulai! 😉"

    def _handle_location_phase(self, user_id: str, message: str, state: Dict) -> str:
        faculty = utils.extract_faculty_from_text(message)
        if faculty:
            state['data']['faculty'] = faculty
            state['phase'] = 'waiting_hunger'
            self.conversation_states[user_id] = state
            hunger_ask_data = self.responses['hunger_level_ask']
            options = "\n".join([f"{k}. {v}" for k, v in hunger_ask_data['options'].items()])
            return f"Siap, {faculty} noted! 📍\n\n{hunger_ask_data['question']}\n{options}"
        return random.choice(self.responses['location_ask_fail'])

    def _handle_hunger_phase(self, user_id: str, message: str, state: Dict) -> str:
        hunger_level = utils.extract_hunger_level_from_text(message)
        if hunger_level:
            state['data']['hunger_level'] = hunger_level
            state['phase'] = 'waiting_budget'
            self.conversation_states[user_id] = state
            return random.choice(self.responses['budget_ask'])
        return random.choice(self.responses['hunger_ask_fail'])

    def _handle_budget_phase(self, user_id: str, message: str, state: Dict) -> str:
        budget = utils.extract_budget_from_text(message)
        if budget:
            # --- Tambahin check dulu ---
            if budget <= 1500:
                self._reset_conversation(user_id)
                return f"Aduh in this economy gada makanan harganya {budget}. Kamu puasa aja dulu yah 🥲"
            
            state['data']['budget'] = budget
            recs = utils.find_recommendations(
                self.canteens_db,
                state['data']['faculty'],
                state['data']['budget'],
                state['data']['hunger_level']
            )
            self._reset_conversation(user_id)
            if not recs:
                return random.choice(self.responses['no_result'])
            return self._format_recommendations_response(recs, state['data'])
        
        return random.choice(self.responses['budget_ask_fail'])

    def _format_recommendations_response(self, recommendations: List[Dict], user_data: Dict) -> str:
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
