"""
RAG Retrieval Engine for food recommendations - CLEAN FIXED VERSION
"""
import logging
from typing import List, Dict, Optional
from src.rag.embeddings import get_embedding
from src.rag.similarity import find_similar_foods_fast
from src.database.connection import db_instance
from src.database.models.user import User
from src.config import Config

logger = logging.getLogger(__name__)

class RetrievalEngine:
    """RAG-based food retrieval system"""
    
    def __init__(self):
        self.foods_cache = None
    
    def _load_foods(self) -> List[Dict]:
        """
        Load ALL menu items from UGM canteens database
        Converts canteen structure to flat food list
        """
        if self.foods_cache is None:
            foods = []
            
            # Ensure database is connected
            if db_instance.json_db is None and db_instance.db is None:
                db_instance.connect()
            
            # Load canteens from database
            try:
                if db_instance.use_mongo:
                    # MongoDB access
                    canteens = list(db_instance.db['ugm_canteens'].find({}))
                else:
                    # JSON database access
                    canteens_obj = db_instance.json_db['ugm_canteens']
                    canteens = canteens_obj.data  # Direct access to list
                
                logger.info(f"Loaded {len(canteens)} canteens from database")
                
            except Exception as e:
                logger.error(f"Error loading canteens: {e}")
                canteens = []
            
            # Flatten canteen menus into food list
            for canteen in canteens:
                canteen_name = canteen.get("canteen_name", "")
                faculty = canteen.get("faculty_proximity", [])
                gmaps = canteen.get("gmaps_link", "")
                
                for menu in canteen.get("menus", []):
                    # Create food entry with all relevant info
                    food = {
                        "id": f"{canteen_name}_{menu['name']}".replace(" ", "_"),
                        "name": menu["name"],
                        "price": menu.get("price", 0),
                        "category": menu.get("category", ""),
                        "suitability": menu.get("suitability", []),
                        "canteen_name": canteen_name,
                        "faculty_proximity": faculty,
                        "gmaps_link": gmaps,
                        # Generate tags for better matching
                        "tags": self._generate_tags(menu, canteen)
                    }
                    foods.append(food)
            
            self.foods_cache = foods
            logger.info(f"Processed {len(self.foods_cache)} food items from {len(canteens)} canteens")
        
        return self.foods_cache
    
    def _generate_tags(self, menu: Dict, canteen: Dict) -> List[str]:
        """Generate searchable tags from menu and canteen info"""
        tags = []
        
        # Category tags
        category = menu.get("category", "")
        if category == "makanan_berat":
            tags.extend(["berat", "kenyang", "nasi", "porsi besar"])
        elif category == "makanan_ringan":
            tags.extend(["ringan", "snack", "cepat"])
        elif category == "cemilan":
            tags.extend(["cemilan", "snack", "jajan"])
        elif category == "minuman":
            tags.extend(["minum", "segar"])
        
        # Suitability tags
        tags.extend(menu.get("suitability", []))
        
        # Name-based tags
        name_lower = menu["name"].lower()
        if "ayam" in name_lower:
            tags.append("ayam")
        if "nasi" in name_lower:
            tags.append("nasi")
        if "mie" in name_lower or "mee" in name_lower:
            tags.append("mie")
        if "geprek" in name_lower or "penyet" in name_lower:
            tags.extend(["pedas", "sambal"])
        if "goreng" in name_lower:
            tags.append("goreng")
        if "soto" in name_lower:
            tags.append("berkuah")
        if "gado" in name_lower or "pecel" in name_lower:
            tags.extend(["sayur", "sehat"])
        
        return tags
    
    def refresh_cache(self):
        """Refresh foods cache"""
        self.foods_cache = None
        logger.info("Foods cache cleared")
    
    def search_by_context(
        self,
        user_id: str,
        context: Dict,
        top_k: int = None
    ) -> List[Dict]:
        """
        Search foods using context filtering + RAG
        
        Args:
            user_id: User identifier
            context: Context dict with faculty, hunger_level, budget, time_period
            top_k: Number of results (default from config)
            
        Returns:
            List of recommended foods with scores
        """
        if "similar_to" in context:
            query_text = f"menu mirip dengan {', '.join(context['similar_to'])}"
        else:
            query_text = self._build_query_text(context)


        if top_k is None:
            top_k = Config.MAX_RECOMMENDATIONS
        
        # Load all foods
        all_foods = self._load_foods()
        
        if not all_foods:
            logger.error("No foods available in database!")
            return []
        
        # STEP 1: Hard filtering (budget, faculty, time)
        filtered_foods = self._apply_hard_filters(all_foods, context)
        
        logger.info(f"After hard filters: {len(filtered_foods)}/{len(all_foods)} foods remaining")
        
        if not filtered_foods:
            logger.warning("No foods passed hard filters!")
            # Relax filters and try again
            filtered_foods = self._apply_hard_filters(all_foods, context, strict=False)
            logger.info(f"After relaxed filters: {len(filtered_foods)} foods")
        
        if not filtered_foods:
            return []
        
        # STEP 2: RAG semantic search
        logger.info(f"Search query: '{query_text}'")
        query_embedding = get_embedding(query_text)

        
        query_embedding = get_embedding(query_text)
        
        similar_foods = find_similar_foods_fast(
            query_embedding,
            filtered_foods,
            top_k=min(top_k * 2, len(filtered_foods)),  # Get more candidates
            threshold=0.3  # Lower threshold for better recall
        )
        
        logger.info(f"Found {len(similar_foods)} similar foods after RAG")
        
        # If still no results, lower threshold further
        if not similar_foods and filtered_foods:
            logger.warning("No results with threshold 0.3, trying 0.0...")
            similar_foods = find_similar_foods_fast(
                query_embedding,
                filtered_foods,
                top_k=min(top_k * 2, len(filtered_foods)),
                threshold=0.0  # Accept all
            )
            logger.info(f"Found {len(similar_foods)} foods with no threshold")
        
        # STEP 3: Apply personalization
        personalized = self._apply_personalization(user_id, similar_foods)
        
        return personalized[:top_k]
    
    def _apply_hard_filters(self, foods: List[Dict], context: Dict, strict: bool = True) -> List[Dict]:
        """Apply mandatory filters (budget, faculty, time period)"""
        filtered = foods
        
        # Budget filter (always apply)
        budget = context.get("budget")
        if budget:
            filtered = [f for f in filtered if f["price"] <= budget]
            logger.info(f"After budget filter (≤{budget}): {len(filtered)} foods")
        
        # Faculty filter (strict mode only)
        faculty = context.get("faculty")
        if faculty and strict:
            filtered = [
                f for f in filtered
                if not f["faculty_proximity"] or faculty in f["faculty_proximity"]
            ]
            logger.info(f"After faculty filter ({faculty}): {len(filtered)} foods")
        
        # Time period filter (strict mode only)
        time_period = context.get("time_period")
        if time_period and strict:
            filtered = [
                f for f in filtered
                if not f["suitability"] or time_period in f["suitability"]
            ]
            logger.info(f"After time filter ({time_period}): {len(filtered)} foods")
        
        return filtered
    
    def _build_query_text(self, context: Dict) -> str:
        """Build natural language query from context"""
        parts = []
        
        hunger_level = context.get("hunger_level", "")
        if hunger_level == "brutal":
            parts.append("makanan berat porsi besar mengenyangkan nasi")
        elif hunger_level == "standar":
            parts.append("makanan enak kenyang standar")
        elif hunger_level == "iseng":
            parts.append("cemilan ringan snack jajan")
        
        time_period = context.get("time_period", "")
        if time_period == "pagi":
            parts.append("sarapan pagi")
        elif time_period == "siang":
            parts.append("makan siang")
        elif time_period == "sore":
            parts.append("makan sore")
        elif time_period == "malam":
            parts.append("makan malam")
        
        # Add preferences
        preferences = context.get("preferences", [])
        if preferences:
            parts.extend(preferences)
        
        query = " ".join(parts)
        return query if query else "makanan enak"  # Default query
    
    def _apply_personalization(
        self,
        user_id: str,
        candidates: List[Dict]
    ) -> List[Dict]:
        """Apply user preferences to boost/filter results"""
        user = User.get(user_id)
        if not user:
            return candidates
        
        favorite_foods = user.get("favorite_foods", [])
        allergies = user.get("allergies", [])
        
        # Filter out allergies
        if allergies:
            candidates = [
                food for food in candidates
                if not any(allergy in food.get("tags", []) for allergy in allergies)
            ]
        
        # Boost favorites
        for food in candidates:
            food_name = food.get("name", "")
            if food_name in favorite_foods:
                food["similarity_score"] = min(1.0, food.get("similarity_score", 0) + 0.2)
        
        # Re-sort after boosting
        candidates.sort(key=lambda x: x.get("similarity_score", 0), reverse=True)
        
        return candidates
    
    def search_by_text(self, query: str, top_k: int = 5) -> List[Dict]:
        """Simple text-based search"""
        query_embedding = get_embedding(query)
        foods = self._load_foods()
        
        return find_similar_foods_fast(
            query_embedding,
            foods,
            top_k=top_k,
            threshold=0.5
        )

# Global instance
retrieval_engine = RetrievalEngine()