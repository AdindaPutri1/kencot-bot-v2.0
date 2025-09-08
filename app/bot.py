import logging
import re
import random
from typing import Any, Dict, List
from . import utils
from . import llm

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

        if faculty and not hunger_level and not budget:
        # Hanya tau fakultas → simpan dulu, minta hunger_level
            state['phase'] = 'waiting_hunger'
            state['data']['faculty'] = faculty
            self.conversation_states[user_id] = state
            return "Oke, kamu di fakultas {}. Lagi lapernya segimana nih? 🤔".format(faculty)

        elif faculty and hunger_level and not budget:
        # Tau fakultas + hunger_level → minta budget
            state['phase'] = 'waiting_budget'
            state['data']['faculty'] = faculty
            state['data']['hunger_level'] = hunger_level
            self.conversation_states[user_id] = state
            return "Noted, lapar {} di fakultas {}. Budget makanmu berapa nih? 💸".format(hunger_level, faculty)

        # jika yang diketahui fakultas, hunger_level, dan budget
        elif faculty and hunger_level and budget:
            logger.info(f"All info detected langsung: {faculty}, {hunger_level}, {budget}")
            
            # --- Tambahin check budget kecil ---
            if budget <= 1500:
                state['phase'] = "waiting_budget"
                self.conversation_states[user_id] = state
                return f"Aduh in this economy gada makanan harganya {budget}. Kamu puasa aja dulu yah 🥲\n\nBercanda, coba budget di atas 10ribu"

            state['phase'] = "recommendation_given"
            self.conversation_states[user_id] = state
            recs = utils.find_recommendations(self.canteens_db, faculty, budget, hunger_level)
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
            elif phase == 'waiting_budget_ai':  
                return self._handle_budget_phase(user_id, message, state)
            elif phase == 'recommendation_given':
                return self._handle_recommendation_phase(user_id, message, state)
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

    # === AI fallback: kalau user sudah di fase waiting_budget_ai ===
        if state.get("phase") == "waiting_budget_ai":
            agree = utils.agree_response(message)

            if agree is True:
                user_data = {
                    "faculty": state['data']['faculty'],
                    "hunger_level": state['data']['hunger_level'],
                    "budget": state['data']['budget'],
                    "time_category": utils.get_current_time_period()
                } 
                nearby_menus = utils.find_nearby_menus(self.canteens_db, user_data['faculty'])
                llm_response = llm.ask_gemini(user_data, nearby_menus)

                waiting_msg = (
                    "Sek, mamang pikirin dulu yaa... 🤔\n"
                    "Mungkin mamang mikirnya agak lama nih, tapi demi kamu apasih yang engga ❤️\n\n"
                )

                state['phase'] = "recommendation_given"
                self.conversation_states[user_id] = state
                return waiting_msg + llm_response + "\n\nMau Mamang kasih rekomendasi lagi nggak nih? 😋"

            elif agree is False:
                state['phase'] = "waiting_budget"
                self.conversation_states[user_id] = state
                return "Oke, kalau gitu Mamang nggak maksa 😅. Coba sebutin budget lain aja ya!"

            else:  # None → gagal deteksi
                return random.choice(self.responses['agree_ask_fail'])

    # === Normal flow: parsing budget ===
        budget = utils.extract_budget_from_text(message)
        if budget:
            # --- Tambahin check dulu ---
            if budget <= 1500:
                state['phase'] = "waiting_budget"
                self.conversation_states[user_id] = state
                return f"Aduh in this economy gada makanan harganya {budget}. Kamu puasa aja dulu yah 🥲\n\nBercanda, coba budget di atas 10ribu"
            
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

        agree = utils.agree_response(message)

        if agree is True:
        # Balik ke nanya lokasi lagi
            self.conversation_states[user_id] = {'phase': 'waiting_location', 'data': {}}
            return "Oke siap! Mau makan di fakultas mana kali ini? 🍽️"

        elif utils.is_full_response(message):
            self._reset_conversation(user_id)
            return "Sip, wareg tenan! Kalau laper tinggal bilang ya. 😋"

        elif utils.is_thank_you(message):
            self._reset_conversation(user_id)
            return "Sama-sama 🙌. Makasi juga udah pakai bot punya Mamang. Semoga rekomendasinya bisa buat makan bareng doimu wkwk. Kalau laper tinggal bilang, ya! 😉"

        elif agree is None:
        # kalau ga kedetect → fallback ke agree_ask_fail
            return random.choice(self.responses['agree_ask_fail'])

        else:
        # aman fallback kalau unexpected
            return "Gimana, mau rekomendasi lagi atau udah wareg? Kalau udah wareg tinggal bilang wareg atau kenyang!😋"


    def _format_recommendations_response(self, recommendations: List[Dict], user_data: Dict) -> str:
        header = f"Gini deh, karena kamu lagi di {user_data.get('faculty')} dan lagi {user_data.get('hunger_level')}, ini opsi paling mantul buat kamu: ✨\n"
        body = ""
        for i, rec in enumerate(recommendations):
            emoji = "🍽️" if i == 0 else "🍜"
            body += (
                f"\n{emoji} *{rec['menu_name']}* di *{rec['canteen_name']}*\n"
                f"   💰 Harga cuma *Rp {rec['menu_price']:,}* (pas buat budget-mu!)\n"
                f"   📍 Cus kesini: {rec['gmaps_link']}\n"
            )
            
        footer = "\nGaskeun cobain salah satunya! Butuh rekomendasi lagi ga nih? 😋"
        
        return header + body + footer
