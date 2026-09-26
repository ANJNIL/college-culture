import json
import re
from typing import List, Optional, Dict, Any
from google import genai
from fastapi import HTTPException, status
from app.config import settings
from app.models.domain import Product
from app.schemas.ai import (
    StyleRecommendationResponse,
    ProductDescriptionResponse,
    StyleChatResponse,
    ChatMessage
)

SYSTEM_STYLIST_INSTRUCTION = """You are the Premier Personal Stylist for LIHAS (Beyond Ordinary) — India's premier luxury men's accessories label.
LIHAS crafts anti-tarnish, sweatproof, and waterproof jewellery from 316L surgical-grade stainless steel, PVD titanium, and genuine natural minerals (jet onyx, zircons, 18K champagne gold dips).

CRITICAL SECURITY AND BRAND INTEGRITY RULES:
1. ONLY recommend products that exist in the PROVIDED CATALOG.
2. NEVER hallucinate or invent new products, brands, or IDs not present in the catalog.
3. Every recommendation must cite the exact product ID from the provided catalog.
4. Voice tone: Sophisticated, masculine, minimalist, editorial, confident, and refined.
"""


class GeminiAIService:
    def __init__(self):
        self._client: Optional[genai.Client] = None
        self.model_name = "gemini-3.6-flash"

    @property
    def client(self) -> genai.Client:
        if not self._client:
            if not settings.GEMINI_API_KEY:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Gemini AI API key is not configured on the server."
                )
            self._client = genai.Client(api_key=settings.GEMINI_API_KEY)
        return self._client

    def _format_catalog_prompt(self, products: List[Product]) -> str:
        items = []
        for p in products:
            items.append(
                f"- ID: {p.id}\n"
                f"  Name: {p.name}\n"
                f"  Category: {p.category}\n"
                f"  Price: ₹{p.price}\n"
                f"  Material: {p.material}\n"
                f"  Style: {p.style}\n"
                f"  Description: {p.description}\n"
            )
        return "\n".join(items)

    async def get_style_recommendations(
        self,
        occasion: Optional[str],
        style_preference: Optional[str],
        budget: Optional[int],
        current_accessory: Optional[str],
        user_prompt: Optional[str],
        catalog: List[Product],
    ) -> StyleRecommendationResponse:
        """Generate tailored accessory recommendations based on real LIHAS products."""
        catalog_text = self._format_catalog_prompt(catalog)
        catalog_ids = {p.id for p in catalog}

        prompt = f"""{SYSTEM_STYLIST_INSTRUCTION}

REAL LIHAS PRODUCT CATALOG:
{catalog_text}

CLIENT REQUEST:
- Occasion: {occasion or "Versatile Everyday / Special Event"}
- Style Preference: {style_preference or "Modern Minimalist Luxury"}
- Budget Limit: ₹{budget if budget else "Flexible"}
- Currently Owned / Wearing: {current_accessory or "None"}
- Additional Client Note: {user_prompt or "Curate an impeccable accessory combination."}

TASK:
Provide personalized styling guidance and select 1 to 3 best matching products from the REAL CATALOG above.
Respond in valid JSON format ONLY with this schema:
{{
  "styling_advice": "Detailed styling advice tailored to the occasion and preference",
  "recommended_product_ids": ["exact_id_1", "exact_id_2"],
  "suggested_outfit_pairing": "Specific outfit pairing guidance (e.g. linen shirt, charcoal blazer, sneakers)",
  "vibe_summary": "Short punchy aesthetic summary (e.g. Understated Monochromatic Precision)"
}}
"""

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            raw_text = response.text.strip() if response and response.text else "{}"

            # Strip markdown fences if present
            cleaned = re.sub(r"^```json\s*", "", raw_text, flags=re.IGNORECASE)
            cleaned = re.sub(r"^```\s*", "", cleaned)
            cleaned = re.sub(r"\s*```$", "", cleaned)
            data = json.loads(cleaned)

            rec_ids = [pid for pid in data.get("recommended_product_ids", []) if pid in catalog_ids]
            if not rec_ids and catalog:
                # Fallback to top products if LLM returned invalid IDs
                rec_ids = [catalog[0].id]

            rec_products = [p for p in catalog if p.id in rec_ids]

            return StyleRecommendationResponse(
                styling_advice=data.get("styling_advice", "Pair timeless anti-tarnish stainless steel pieces with neutral monochrome textures."),
                recommended_product_ids=rec_ids,
                recommended_products=rec_products,
                suggested_outfit_pairing=data.get("suggested_outfit_pairing", "Oversized black crewneck tee or tailored charcoal blazer with clean trousers."),
                vibe_summary=data.get("vibe_summary", "Refined Modern Masculinity")
            )
        except Exception as e:
            # Fallback for resiliency
            fallback_prods = catalog[:2] if len(catalog) >= 2 else catalog
            return StyleRecommendationResponse(
                styling_advice="Elevate your look with understated surgical steel details that complement both formal suiting and relaxed streetwear.",
                recommended_product_ids=[p.id for p in fallback_prods],
                recommended_products=fallback_prods,
                suggested_outfit_pairing="Structured overshirt or tailored suit with subtle wrist and neckline detailing.",
                vibe_summary="Modern Editorial Sophistication"
            )

    async def get_product_description(
        self,
        product_name: Optional[str],
        category: Optional[str],
        material: Optional[str],
        tone: Optional[str] = "editorial luxury",
    ) -> ProductDescriptionResponse:
        """Generate high-converting luxury editorial copy for accessories."""
        prompt = f"""You are the Creative Director and Copywriter for LIHAS, an ultra-premium men's jewellery brand.
Create rich, evocative product copy for:
- Product Name: {product_name or "Signature Accessory"}
- Category: {category or "Men's Jewellery"}
- Material: {material or "316L Surgical Stainless Steel"}
- Tone: {tone}

Respond in valid JSON ONLY with this schema:
{{
  "luxury_description": "2-3 compelling sentences highlighting tactile quality, aesthetic intention, and durability.",
  "key_highlights": ["Bullet point 1", "Bullet point 2", "Bullet point 3"],
  "craftsmanship_note": "A sentence on precision engineering and zero-tarnish performance."
}}
"""
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            raw_text = response.text.strip() if response and response.text else "{}"
            cleaned = re.sub(r"^```json\s*", "", raw_text, flags=re.IGNORECASE)
            cleaned = re.sub(r"^```\s*", "", cleaned)
            cleaned = re.sub(r"\s*```$", "", cleaned)
            data = json.loads(cleaned)

            return ProductDescriptionResponse(
                luxury_description=data.get("luxury_description", "Precision forged for daily rituals with timeless elegance."),
                key_highlights=data.get("key_highlights", ["100% Anti-Tarnish & Waterproof", "Hypoallergenic Surgical Steel", "Modern Statement Profile"]),
                craftsmanship_note=data.get("craftsmanship_note", "Finished with laser-etched precision and comfort fit ergonomics.")
            )
        except Exception:
            return ProductDescriptionResponse(
                luxury_description=f"Crafted with unyielding attention to detail in {material or 'surgical steel'}, designed to endure daily life without losing its luster.",
                key_highlights=["100% Waterproof & Sweatproof", "Hypoallergenic Skin Safe", "Hand-Polished Finish"],
                craftsmanship_note="Engineered for lifetime durability with zero discoloration."
            )

    async def chat_stylist(
        self,
        message: str,
        history: List[ChatMessage],
        catalog: List[Product]
    ) -> StyleChatResponse:
        """Interactive AI stylist chat assisting with recommendations and styling."""
        catalog_text = self._format_catalog_prompt(catalog)
        catalog_ids = {p.id: p for p in catalog}

        conversation_context = ""
        for msg in history[-6:]:
            conversation_context += f"{msg.role.capitalize()}: {msg.content}\n"

        prompt = f"""{SYSTEM_STYLIST_INSTRUCTION}

REAL LIHAS PRODUCT CATALOG:
{catalog_text}

PAST CONVERSATION:
{conversation_context}

USER MESSAGE:
{message}

INSTRUCTIONS:
1. Answer the user's styling question with expert fashion insight.
2. If relevant, mention and recommend 1 or 2 specific products from the REAL CATALOG above.
3. At the end of your response, if you mentioned any products, output a JSON block with their IDs:
```json
{{"product_ids": ["exact_id_1"]}}
```
"""
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            raw_text = response.text.strip() if response and response.text else "I am here to help you style your LIHAS pieces."

            # Parse out any trailing JSON block
            product_ids = []
            json_match = re.search(r"```json\s*(\{.*?\})\s*```", raw_text, flags=re.DOTALL)
            clean_reply = raw_text
            if json_match:
                try:
                    meta = json.loads(json_match.group(1))
                    product_ids = [pid for pid in meta.get("product_ids", []) if pid in catalog_ids]
                except Exception:
                    pass
                clean_reply = raw_text[:json_match.start()].strip()

            # Also check text for product names or IDs
            for pid, prod in catalog_ids.items():
                if pid not in product_ids:
                    if pid.lower() in raw_text.lower() or prod.name.lower() in raw_text.lower():
                        product_ids.append(pid)

            suggested = [catalog_ids[pid] for pid in product_ids[:3]]
            return StyleChatResponse(
                reply=clean_reply,
                suggested_products=suggested
            )
        except Exception:
            return StyleChatResponse(
                reply="LIHAS accessories are designed for effortless versatility. Whether you prefer the kinetic pavé spinner ring or the architectural onyx pieces, they pair seamlessly with dark neutrals and relaxed tailoring.",
                suggested_products=catalog[:2]
            )


gemini_service = GeminiAIService()
