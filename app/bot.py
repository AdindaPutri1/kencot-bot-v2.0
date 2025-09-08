import logging
import re
import random  # <-- TAMBAHKAN INI
from datetime import datetime
from typing import Any, Dict, List
from . import utils
from . import llm


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

    def extract_slots(self, message: str) -> Dict[str, str]:
        slots = {}
        if (faculty := utils.extract_faculty_from_text(message)):
            slots['faculty'] = faculty
        if (hunger := utils.extract_hunger_level_from_text(message)):
            slots['hunger_level'] = hunger
        if (budget := utils.extract_budget_from_text(message)):
            slots['budget'] = budget
        return slots

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
            elif phase == 'waiting_budget_ai':  
                return self._handle_budget_phase(user_id, message, state)
            elif phase == 'recommendation_given':
                return self._handle_recommendation_phase(user_id, message, state)
        except Exception as e:  
            logger.error(f"Error in phase '{phase}' for user {user_id}: {e}")
            self.conversation_states[user_id] = {'phase': 'idle', 'data': {}} # Reset state on error
            return self.responses.get("error", ["Aduh, mamang lagi error nih, coba lagi ya."])[0]

        # Default fallback
        return self._handle_idle_phase(user_id, message)

    def _handle_idle_phase(self, user_id: str, message: str) -> str:
        """Handles the initial interaction when user is idle"""
        
        state: Dict[str, Dict[str, str]] = self.conversation_states.get(
            user_id, {'phase': 'idle', 'data': {}}
        )

        if self.triggers['food'].search(message):

           # === Extract semua slot dulu ===
            slots = self.extract_slots(message)
            state['data'].update(slots)

            # === Kalau user cuma trigger doang (laper, kencot, dll) ===
            if state['phase'] == 'idle' and not state['data']:
                self.conversation_states[user_id] = {'phase': 'waiting_location', 'data': {}}
                greeting = random.choice(self.responses['greetings'])
                location_ask = random.choice(self.responses['location_ask'])
                return f"{greeting}\n\n{location_ask}"

            # === Cek apakah slot udah lengkap / masih kurang ===
            return self._check_and_recommend(user_id, state)
        return "Hai! Aku Mamang UGM, siap bantu kamu cari makan. Bilang aja 'laper' buat mulai! 😉"

    def _check_and_recommend(self, user_id: str, state: Dict) -> str:
        """Helper untuk cek slot mana yang udah lengkap dan tentuin phase selanjutnya."""

        data = state['data']

        # Kalau lengkap semua → kasih rekomendasi
        if all(k in data for k in ['faculty', 'hunger_level', 'budget']):
            recommendations = utils.find_recommendations(
                self.canteens_db,
                data['faculty'],
                data['budget'],
                data['hunger_level']
            )
            if recommendations:
                state['phase'] = "recommendation_given"
                self.conversation_states[user_id] = state
                return self._format_recommendations_response(recommendations, data)
            else:
                state['phase'] = "waiting_budget_ai"
                self.conversation_states[user_id] = state
                return "Yah, ga ada yang cocok euy. Mau aku cariin aja nih pake AI Mamang? (Ya/Tidak)"

        # Kalau baru faculty aja → nanya hunger
        if "faculty" in data and "hunger_level" not in data:
            state['phase'] = "waiting_hunger"
            self.conversation_states[user_id] = state
            hunger_ask_data: Dict[str, Any] = self.responses['hunger_level_ask']
            question = hunger_ask_data['question']
            options_dict: Dict[str, str] = hunger_ask_data['options']
            options = "\n".join([f"{k}. {v}" for k, v in options_dict.items()])
            return f"Siap, {data['faculty']} noted! 📍\n\n{question}\n{options}"

        # Kalau faculty + hunger udah ada tapi budget belum
        if "faculty" in data and "hunger_level" in data and "budget" not in data:
            state['phase'] = "waiting_budget"
            self.conversation_states[user_id] = state
            return random.choice(self.responses['budget_ask'])

        # Kalau belum ada apa-apa → fallback
        state['phase'] = "waiting_location"
        self.conversation_states[user_id] = state
        return random.choice(self.responses['location_ask'])
    
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

    # === AI fallback: kalau user sudah di fase waiting_budget_ai ===
        if state.get("phase") == "waiting_budget_ai":
            if message.lower() in ["ya", "ok", "boleh"]:
                user_data = {
                    "faculty": state['data']['faculty'],
                    "hunger_level": state['data']['hunger_level'],
                    "budget": state['data']['budget'],
                    "time_category": utils.get_current_time_period()
            }
                nearby_menus = utils.find_nearby_menus(self.canteens_db, user_data['faculty'])
                llm_response = llm.ask_gemini(user_data, nearby_menus)

                 # selesai kasih rekomendasi → balik ke recommendation phase
                state['phase'] = "recommendation_given"
                self.conversation_states[user_id] = state
                return llm_response + "\n\nMau Mamang kasih rekomendasi lagi nggak nih? 😋"
            
            state['phase'] = "waiting_budget"
            self.conversation_states[user_id] = state
            # Kalau jawabannya bukan "ya"
            return "Oke, kalau gitu Mamang nggak maksa 😅. Coba sebutin budget lain aja ya!"

    # === Normal flow: parsing budget ===
        budget = utils.extract_budget_from_text(message)
        if budget:
            state['data']['budget'] = budget

        # Cari rekomendasi dari DB
            recommendations = utils.find_recommendations(
                self.canteens_db,
                state['data']['faculty'],
                state['data']['budget'],
                state['data']['hunger_level']
            )

            if recommendations:
                state['phase'] = "recommendation_given"
                self.conversation_states[user_id] = state
                return self._format_recommendations_response(recommendations, state['data'])

        # Kalau nggak ada rekomendasi → minta izin AI
            state['phase'] = "waiting_budget_ai"
            self.conversation_states[user_id] = state
            return "Yah, ga ada yang cocok euy. Mau aku cariin aja nih pake AI Mamang? (Ya/Tidak)"

        return random.choice(self.responses['budget_ask_fail'])
    
    def _handle_recommendation_phase(self, user_id: str, message: str, state: Dict) -> str:
        """Handles setelah kasih rekomendasi"""
        if any(word in message.lower() for word in ["ya", "lagi", "boleh"]):
        # Balik ke nanya lokasi lagi
            self.conversation_states[user_id] = {'phase': 'waiting_location', 'data': {}}
            return "Oke siap! Mau makan di fakultas mana kali ini? 🍽️"
        elif "wareg" in message.lower() or "kenyang" in message.lower():
            self._reset_conversation(user_id)
            return "Sip, wareg tenan! Kalau laper tinggal bilang ya."
        else:
            return "Gimana, mau rekomendasi lagi atau udah wareg? 😋"

        
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
            
        footer = "\nGaskeun cobain salah satunya! Butuh rekomendasi Mamang lagi, nggak nih? 😋"
        
        return header + body + footer