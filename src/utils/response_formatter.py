"""
Response formatter for food recommendations
"""
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

class ResponseFormatter:
    """Format food recommendations into user-friendly messages"""

    @staticmethod
    def _format_price(p: int) -> str:
        try:
            return f"Rp {int(p):,}"
        except Exception:
            return f"Rp {p}"

    @staticmethod
    def format_recommendation(
        foods: List[Dict],
        llm_response: str = None,
        show_nutrition: bool = True
    ) -> str:
        """
        Format food recommendations with canteen info

        Args:
            foods: List of recommended food items (each item must contain at least:
                   name, price, canteen_name/gmaps_link and optionally calories, protein, fat, carbs)
            llm_response: Optional LLM-generated explanation
            show_nutrition: Whether to show nutrition info

        Returns:
            Formatted message string
        """
        if not foods:
            return "Waduh, Mamang ga nemu makanan yang cocok nih 😢\nCoba ubah kriterianya dikit?"

        # Use whatsapp-style formatter as main output
        return ResponseFormatter.format_whatsapp_style(foods)

    @staticmethod
    def format_simple_list(foods: List[Dict]) -> str:
        """Simple list format (for fallback)"""
        if not foods:
            return "Waduh, Mamang ga nemu makanan yang cocok nih 😢"

        lines = ["Nih Mamang kasih rekomendasi:", ""]

        for idx, food in enumerate(foods, 1):
            name = food.get("name", "Makanan")
            price = food.get("price", 0)
            canteen = food.get("canteen_name", food.get("canteen", "Kantin Lainnya"))

            lines.append(f"{idx}. **{name}** ({ResponseFormatter._format_price(price)})")
            lines.append(f"   📍 {canteen}")

        return "\n".join(lines)

    @staticmethod
    def format_whatsapp_style(foods: List[Dict]) -> str:
        """
        WhatsApp-friendly format (like your demo) with nutrition details
        Groups by canteen, prints top-2 canteens (if foods include more),
        shows totals and per-menu nutrition breakdown.
        """
        if not foods:
            return "Waduh, Mamang ga nemu makanan yang cocok nih 😢\nCoba ubah kriterianya dikit?"

        # Group foods by canteen_name (robust to key names)
        canteen_groups = {}
        for f in foods:
            canteen = f.get("canteen_name") or f.get("canteen") or "Kantin Lainnya"
            gmaps = f.get("gmaps_link") or f.get("gmaps") or f.get("gmaps_url") or ""
            if canteen not in canteen_groups:
                canteen_groups[canteen] = {"foods": [], "gmaps": gmaps}
            canteen_groups[canteen]["foods"].append(f)

        # Choose up to 2 canteens (preserve insertion order)
        selected_canteens = list(canteen_groups.items())[:2]

        lines = []
        lines.append("Tunggu sebentar, Mamang pikirin dulu yaa... 🤔\n")

        # If user likely in a faculty/canteen context, try to be contextual
        first_canteen_name = selected_canteens[0][0] if selected_canteens else "Kantin"
        lines.append(f"Gini deh, karena kamu lagi di *{first_canteen_name.split()[0] if ' ' in first_canteen_name else first_canteen_name}*, ini opsi paling mantul buat kamu: ✨\n")

        # Totals
        total_calories = total_protein = total_fat = total_carbs = total_price = 0

        # Build canteen blocks
        for idx, (canteen_name, data) in enumerate(selected_canteens, start=1):
            foods_list = data["foods"]
            gmaps = data.get("gmaps", "")

            lines.append(f"*{idx}. {canteen_name}*")
            for food in foods_list:
                name = food.get("name", "Makanan")
                price = food.get("price", 0)
                calories = food.get("calories", 0)
                protein = food.get("protein", 0)
                fat = food.get("fat", 0)
                carbs = food.get("carbs", 0)

                total_price += price or 0
                total_calories += calories or 0
                total_protein += protein or 0
                total_fat += fat or 0
                total_carbs += carbs or 0

                # category -> badge (optional cosmetic)
                category = food.get("category", "")
                badge = "🍽️"
                if category == "makanan_berat":
                    badge = "🍛"
                elif category == "makanan_ringan":
                    badge = "🥙"
                elif category == "cemilan":
                    badge = "🍪"
                elif category == "minuman":
                    badge = "🥤"

                lines.append(f"   {badge} *{name}* - {ResponseFormatter._format_price(price)}")
                # Nutrition line (show only if there is any nutrition info)
                if any([calories, protein, fat, carbs]):
                    lines.append(f"      _{calories} kkal | P: {protein}g | F: {fat}g | C: {carbs}g_")
                else:
                    lines.append(f"      _info nutrisi tidak tersedia_")

            if gmaps:
                lines.append(f"   📍 Cus kesini: {gmaps}")

            lines.append("")  # spacing

        # Summary block
        lines.append("━━━━━━━━━━━━━━━━━━━━━")
        lines.append("📊 *Ringkasan Total:*")
        lines.append(f"💰 Estimasi biaya: {ResponseFormatter._format_price(total_price)}")
        lines.append(f"🔥 Total kalori: {int(total_calories)} kkal")
        lines.append(f"💪 Protein: {int(total_protein)}g | 🧈 Lemak: {int(total_fat)}g | 🍚 Karbo: {int(total_carbs)}g")
        lines.append("━━━━━━━━━━━━━━━━━━━━━\n")

        # Nutrient breakdown per menu (from all returned foods)
        lines.append("📋 *Detail Nutrisi per Menu:*")
        for f in foods:
            name = f.get("name", "Makanan")
            calories = f.get("calories", 0)
            protein = f.get("protein", 0)
            fat = f.get("fat", 0)
            carbs = f.get("carbs", 0)
            if any([calories, protein, fat, carbs]):
                lines.append(f"- {name}: {calories} kkal (P: {protein}g, F: {fat}g, C: {carbs}g)")
            else:
                lines.append(f"- {name}: info nutrisi tidak tersedia")

        lines.append("\nGaskeun cobain salah satunya! Butuh rekomendasi lagi ga nih? 😊")

        return "\n".join(lines)


# Global instance
response_formatter = ResponseFormatter()
