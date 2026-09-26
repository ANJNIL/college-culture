from fastapi import APIRouter, HTTPException, status, Request
from app.schemas.ai import (
    StyleRecommendationRequest,
    StyleRecommendationResponse,
    ProductDescriptionRequest,
    ProductDescriptionResponse,
    StyleChatRequest,
    StyleChatResponse,
)
from app.services.gemini import gemini_service
from app.services.products import product_service
from app.security.rate_limiter import limiter

router = APIRouter(prefix="/api/ai", tags=["AI Stylist"])


@router.post("/style-recommendation", response_model=StyleRecommendationResponse)
@limiter.limit("20/minute")
async def get_style_recommendation(request: Request, body: StyleRecommendationRequest):
    """
    Generate personalized men's accessory and outfit recommendations.
    Strictly restricted to REAL accessories in the LIHAS database.
    """
    catalog = await product_service.get_all_products()
    recommendation = await gemini_service.get_style_recommendations(
        occasion=body.occasion,
        style_preference=body.style_preference,
        budget=body.budget,
        current_accessory=body.current_accessory,
        user_prompt=body.user_prompt,
        catalog=catalog
    )
    return recommendation


@router.post("/product-description", response_model=ProductDescriptionResponse)
@limiter.limit("20/minute")
async def generate_product_description(request: Request, body: ProductDescriptionRequest):
    """
    Generate luxury editorial description and craftsmanship highlights.
    If product_id is provided, automatically fetches product details from database.
    """
    name = body.product_name
    category = body.category
    material = body.material

    if body.product_id:
        prod = await product_service.get_product_by_id(body.product_id)
        if prod:
            name = prod.name
            category = prod.category
            material = prod.material

    description = await gemini_service.get_product_description(
        product_name=name,
        category=category,
        material=material,
        tone=body.tone or "editorial luxury"
    )
    return description


@router.post("/style-chat", response_model=StyleChatResponse)
@limiter.limit("25/minute")
async def style_chat(request: Request, body: StyleChatRequest):
    """
    Interactive AI stylist conversation with real product recommendations.
    """
    catalog = await product_service.get_all_products()
    chat_result = await gemini_service.chat_stylist(
        message=body.message,
        history=body.history or [],
        catalog=catalog
    )
    return chat_result
