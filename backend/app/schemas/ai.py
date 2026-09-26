from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from app.models.domain import Product


class StyleRecommendationRequest(BaseModel):
    occasion: Optional[str] = Field(None, description="e.g. Black tie dinner, Date night, Streetwear, Everyday office")
    style_preference: Optional[str] = Field(None, description="e.g. Minimalist, Bold cybernetic, Classic gold, Dark luxury")
    budget: Optional[int] = Field(None, ge=100, le=50000, description="Max budget in INR")
    current_accessory: Optional[str] = Field(None, description="Accessories already owned or interested in")
    user_prompt: Optional[str] = Field(None, description="Free-form user styling question or prompt")


class StyleRecommendationResponse(BaseModel):
    styling_advice: str
    recommended_product_ids: List[str]
    recommended_products: List[Product]
    suggested_outfit_pairing: str
    vibe_summary: str


class ProductDescriptionRequest(BaseModel):
    product_id: Optional[str] = None
    product_name: Optional[str] = None
    category: Optional[str] = None
    material: Optional[str] = None
    tone: Optional[str] = "editorial luxury"


class ProductDescriptionResponse(BaseModel):
    luxury_description: str
    key_highlights: List[str]
    craftsmanship_note: str


class ChatMessage(BaseModel):
    role: str = Field(..., pattern="^(user|assistant|model)$")
    content: str


class StyleChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    history: Optional[List[ChatMessage]] = Field(default_factory=list)


class StyleChatResponse(BaseModel):
    reply: str
    suggested_products: List[Product] = Field(default_factory=list)
