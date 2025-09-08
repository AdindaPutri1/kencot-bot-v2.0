import json
import random
from datetime import datetime
from typing import List, Dict, Optional
import logging
from .utils import load_responses

logger = logging.getLogger(__name__)
RESPONSES = load_responses("data/response.json")

class RuleEngine:
    def __init__(self, database_path: str = 'data/database.json'):
        """Initialize rule engine with database"""
        try:
            with open(database_path, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
            logger.info("Database loaded successfully")
        except FileNotFoundError:
            logger.error(f"Database file not found: {database_path}")
            self.data = {"ugm_canteens": []}
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing database JSON: {str(e)}")
            self.data = {"ugm_canteens": []}
    
    def get_time_category(self) -> str:
        """Determine time category based on current hour"""
        hour = datetime.now().hour
        
        if 4 <= hour <= 10:
            return "pagi"
        elif 11 <= hour <= 15:
            return "siang" 
        elif 16 <= hour <= 18:
            return "sore"
        else:
            return "malam"
    
    def get_recommendations(self, faculty: str, hunger_level: str, budget: int) -> List[Dict]:
        """Main function to get food recommendations"""
        try:
            logger.info(f"Getting recommendations for: {faculty}, {hunger_level}, {budget}")
            
            time_category = self.get_time_category()
            logger.info(f"Current time category: {time_category}")
            
            # Step 1: Filter canteens by location proximity
            nearby_canteens = self.filter_by_location(faculty)
            logger.info(f"Found {len(nearby_canteens)} nearby canteens")
            
            if not nearby_canteens:
                return []
            
            # Step 2: Filter menus by hunger level and time
            suitable_menus = self.filter_by_hunger_and_time(
                nearby_canteens, hunger_level, time_category
            )
            logger.info(f"Found {len(suitable_menus)} suitable menus")
            
            # Step 3: Filter by budget
            affordable_menus = self.filter_by_budget(suitable_menus, budget)
            logger.info(f"Found {len(affordable_menus)} affordable menus")
            
            # Step 4: Select top 2 recommendations
            final_recommendations = self.select_top_recommendations(affordable_menus)
            
            return final_recommendations
            
        except Exception as e:
            logger.error(f"Error in get_recommendations: {str(e)}")
            return []
    
    def filter_by_location(self, user_faculty: str) -> List[Dict]:
        """Filter canteens by proximity to user's faculty"""
        faculty_proximity_map = {
            "Teknik": ["Kantin Teknik", "Kantin FKKMK", "Kantin Filsafat", "Penyetan Bu Lastri"],
            "MIPA": ["Penyetan Bu Lastri", "Kantin Fakultas Geografi", "Kantin MIPA", "Warung Makan Bu Har"],
            "FKKMK": ["Kantin FKKMK", "Kantin Teknik", "Kantin Filsafat"],
            "Pertanian": ["Kantin Pertanian", "Warung Makan Bu Har", "Kantin Filsafat"],
            "Filsafat": ["Kantin Filsafat", "Kantin FKKMK", "Kantin Teknik"],
            "Pascasarjana": ["Warung Makan Bu Har", "Kantin Pertanian", "Penyetan Bu Lastri"],
            "Psikologi": ["Kantin Filsafat", "Kantin FKKMK"],
            "FEB": ["Kantin FEB", "Kantin Filsafat", "Kantin FKKMK"],
            "Hukum": ["Kantin Filsafat", "Kantin FKKMK"],
            "ISIPOL": ["Kantin Filsafat", "Kantin FKKMK"]
        }
        
        # Get priority canteen names for this faculty
        priority_canteens = faculty_proximity_map.get(user_faculty, [])
        
        # Find matching canteens from database
        nearby_canteens = []
        canteens_data = self.data.get("ugm_canteens", [])
        
        # Add canteens in order of proximity priority
        for priority_name in priority_canteens:
            for canteen in canteens_data:
                if self._canteen_name_matches(canteen.get("canteen_name", ""), priority_name):
                    nearby_canteens.append(canteen)
                    break
        
        # Add any remaining canteens if we don't have enough
        if len(nearby_canteens) < 3:
            for canteen in canteens_data:
                if canteen not in nearby_canteens:
                    nearby_canteens.append(canteen)
                    if len(nearby_canteens) >= 5:  # Limit to 5 canteens max
                        break
        
        return nearby_canteens
    
    def _canteen_name_matches(self, db_name: str, target_name: str) -> bool:
        """Check if canteen names match (fuzzy matching)"""
        db_name_clean = db_name.lower().replace(" ", "")
        target_name_clean = target_name.lower().replace(" ", "").replace("kantin", "")
        
        return target_name_clean in db_name_clean or db_name_clean in target_name_clean
    
    def filter_by_hunger_and_time(self, canteens: List[Dict], hunger_level: str, time_category: str) -> List[Dict]:
        """Filter menus based on hunger level and current time"""
        
        # Define time-appropriate food categories
        time_food_mapping = {
            "pagi": ["makanan_ringan", "minuman", "cemilan", "sarapan"],
            "siang": ["makanan_berat", "nasi", "paket_komplit"],
            "sore": ["cemilan", "jajanan", "minuman", "makanan_ringan"],
            "malam": ["makanan_berat", "makanan_hangat", "nasi"]
        }
        
        # Define hunger level food categories
        hunger_food_mapping = {
            "laper_brutal": ["makanan_berat", "nasi", "paket_komplit"],
            "laper_standar": ["makanan_berat", "nasi", "makanan_ringan"],
            "cuma_iseng": ["cemilan", "jajanan", "minuman", "makanan_ringan"]
        }
        
        # Get appropriate categories for current time and hunger level
        time_categories = time_food_mapping.get(time_category, ["makanan_berat"])
        hunger_categories = hunger_food_mapping.get(hunger_level, ["makanan_berat"])
        
        # Find intersection of both requirements
        preferred_categories = list(set(time_categories) & set(hunger_categories))
        
        # If no intersection, use hunger level as priority
        if not preferred_categories:
            preferred_categories = hunger_categories
        
        suitable_menus = []
        
        for canteen in canteens:
            for menu in canteen.get("menus", []):
                menu_category = menu.get("category", "").lower()
                menu_suitability = menu.get("suitability", [])
                
                # Check if menu matches time/hunger requirements
                if (menu_category in preferred_categories or 
                    any(cat in preferred_categories for cat in menu_suitability) or
                    time_category in menu_suitability):
                    
                    # Add canteen info to menu
                    menu_with_canteen = menu.copy()
                    menu_with_canteen['canteen'] = canteen.get("canteen_name", "")
                    menu_with_canteen['gmaps_link'] = canteen.get("gmaps_link", "")
                    menu_with_canteen['canteen_aliases'] = canteen.get("canteen_alias", [])
                    
                    suitable_menus.append(menu_with_canteen)
        
        return suitable_menus
    
    def filter_by_budget(self, menus: List[Dict], budget: int) -> List[Dict]:
        """Filter menus that fit within user's budget"""
        affordable_menus = []
        
        for menu in menus:
            menu_price = menu.get("price", 0)
            if menu_price <= budget:
                affordable_menus.append(menu)
        
        # Sort by price (ascending) and then by suitability score
        affordable_menus.sort(key=lambda x: (x.get("price", 0), -self._calculate_suitability_score(x)))
        
        return affordable_menus
    
    def _calculate_suitability_score(self, menu: Dict) -> int:
        """Calculate suitability score for menu ranking"""
        score = 0
        current_time = self.get_time_category()
        
        # Time-based scoring
        suitability = menu.get("suitability", [])
        if current_time in suitability:
            score += 10
        
        # Category-based scoring
        category = menu.get("category", "")
        if category == "makanan_berat":
            score += 5
        elif category == "cemilan":
            score += 2
        
        # Add random factor for variety
        score += random.randint(0, 3)
        
        return score
    
    def select_top_recommendations(self, menus: List[Dict]) -> List[Dict]:
        """Select and format top 2 recommendations"""
        if not menus:
            return []
        
        # Get top recommendations (max 2)
        top_menus = menus[:2]
        
        recommendations = []
        for menu in top_menus:
            # Generate description
            description = self._generate_menu_description(menu)
            
            recommendation = {
                'name': menu.get('name', 'Menu Spesial'),
                'canteen': menu.get('canteen', 'Kantin UGM'),
                'price': menu.get('price', 0),
                'category': menu.get('category', ''),
                'description': description,
                'gmaps_link': menu.get('gmaps_link', ''),
                'suitability': menu.get('suitability', [])
            }
            
            recommendations.append(recommendation)
        
        return recommendations
    
    def _generate_menu_description(self, menu: Dict) -> str:
        """Generate appealing description for menu item"""
        name = menu.get('name', '').lower()
        category = menu.get('category', '').lower()
        price = menu.get('price', 0)
        time_category = self.get_time_category()
        
        # Base descriptions by category
        descriptions = {
            'makanan_berat': [
                "Fix banget ini mah, auto kenyang sampe sore!",
                "Porsi mantul, dijamin ga bakal laper lagi!",
                "Yang ini legend sih, selalu rame antrian!",
                "Paket komplit yang bikin kenyang maksimal!"
            ],
            'nasi': [
                "Nasi pulen plus lauk mantul, perfect combo!",
                "Klasik tapi ga pernah boring, selalu enak!",
                "Nasi hangat dengan bumbu yang nampol!",
                "Comfort food yang selalu jadi andalan!"
            ],
            'cemilan': [
                "Buat ngemil-ngemil santai, cocok banget!",
                "Kriuk-kriuk gurih yang bikin nagih!",
                "Perfect buat temen ngobrol atau nunggu kelas!",
                "Cemilan legend yang ga pernah mengecewakan!"
            ],
            'minuman': [
                "Seger banget buat ngilangin dahaga!",
                "Dingin-dingin gimana gitu, mantul dah!",
                "Minuman segar yang bikin fresh lagi!",
                "Es dingin yang pas buat cuaca panas!"
            ]
        }
        
        # Time-specific descriptions
        time_descriptions = {
            'pagi': "Perfect buat sarapan pagi yang rushing!",
            'siang': "Cocok banget buat makan siang yang satisfying!",
            'sore': "Enak buat cemilan sore sambil santai!",
            'malam': "Hangat-hangat cocok buat makan malam!"
        }
        
        # Special food item descriptions
        special_descriptions = {
            'ayam': "Ayamnya juicy, bumbunya meresap banget!",
            'geprek': "Pedesnya nampol tapi nagih abis!",
            'soto': "Kuahnya bening tapi rasanya mendalam!",
            'gado': "Seger, sehat, dan mengenyangkan!",
            'bakso': "Baksonya kenyal, kuahnya gurih mantul!",
            'mie': "Mie kenyal dengan topping melimpah!",
            'nasi gudeg': "Gudeg authentic Jogja yang manis legit!",
            'pecel': "Sambal pecelnya pedas manis yang khas!"
        }
        
        # Build description
        description_parts = []
        
        # Add special food description if matches
        for food, desc in special_descriptions.items():
            if food in name:
                description_parts.append(desc)
                break
        
        # Add category description
        category_desc = random.choice(descriptions.get(category, descriptions['makanan_berat']))
        if not description_parts:
            description_parts.append(category_desc)
        
        # Add price comment
        if price <= 10000:
            description_parts.append("Harganya juga ramah di kantong!")
        elif price <= 15000:
            description_parts.append("Worth it banget sama rasanya!")
        else:
            description_parts.append("Premium tapi sebanding sama kualitasnya!")
        
        # Add time-specific comment
        if time_category in time_descriptions:
            description_parts.append(time_descriptions[time_category])
        
        return " ".join(description_parts[:2])  # Limit to 2 sentences
    
    def get_canteen_info(self, canteen_name: str) -> Optional[Dict]:
        """Get detailed canteen information"""
        canteens = self.data.get("ugm_canteens", [])
        
        for canteen in canteens:
            if self._canteen_name_matches(canteen.get("canteen_name", ""), canteen_name):
                return canteen
        
        return None
    
    def get_menu_by_category(self, category: str, limit: int = 5) -> List[Dict]:
        """Get menus by specific category"""
        menus = []
        canteens = self.data.get("ugm_canteens", [])
        
        for canteen in canteens:
            for menu in canteen.get("menus", []):
                if menu.get("category", "").lower() == category.lower():
                    menu_with_canteen = menu.copy()
                    menu_with_canteen['canteen'] = canteen.get("canteen_name", "")
                    menu_with_canteen['gmaps_link'] = canteen.get("gmaps_link", "")
                    menus.append(menu_with_canteen)
                    
                    if len(menus) >= limit:
                        return menus
        
        return menus
    
    def get_budget_range_menus(self, min_budget: int, max_budget: int) -> List[Dict]:
        """Get menus within specific budget range"""
        menus = []
        canteens = self.data.get("ugm_canteens", [])
        
        for canteen in canteens:
            for menu in canteen.get("menus", []):
                price = menu.get("price", 0)
                if min_budget <= price <= max_budget:
                    menu_with_canteen = menu.copy()
                    menu_with_canteen['canteen'] = canteen.get("canteen_name", "")
                    menu_with_canteen['gmaps_link'] = canteen.get("gmaps_link", "")
                    menus.append(menu_with_canteen)
        
        # Sort by price
        menus.sort(key=lambda x: x.get("price", 0))
        return menus