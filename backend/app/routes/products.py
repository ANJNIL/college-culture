from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query, status
from app.services.products import product_service
from app.schemas.products import ProductListResponse, ProductDetailResponse
from app.models.domain import Product

router = APIRouter(prefix="/api/products", tags=["Products"])


@router.get("", response_model=ProductListResponse)
async def list_products(
    category: Optional[str] = Query(None, description="Filter by category (Rings, Necklaces, Earrings, Ear Clips, All)"),
    min_price: Optional[int] = Query(None, ge=0, description="Minimum price filter"),
    max_price: Optional[int] = Query(None, ge=0, description="Maximum price filter"),
    sort_by: Optional[str] = Query("default", description="Sort order: default, priceLow, priceHigh, rating"),
    search: Optional[str] = Query(None, description="Search term for names or materials")
):
    """Retrieve filtered list of college  culture accessories catalog."""
    products = await product_service.get_all_products(
        category=category,
        min_price=min_price,
        max_price=max_price,
        sort_by=sort_by,
        search=search
    )

    all_products = await product_service.get_all_products()
    categories = sorted(list({p.category for p in all_products}))

    return ProductListResponse(
        total=len(products),
        categories=categories,
        products=products
    )


@router.get("/categories/list", response_model=List[str])
async def list_categories():
    """Retrieve distinct accessory categories."""
    all_products = await product_service.get_all_products()
    return sorted(list({p.category for p in all_products}))


@router.get("/{product_id}", response_model=ProductDetailResponse)
async def get_product(product_id: str):
    """Retrieve detailed product specifications and complementary accessories."""
    product = await product_service.get_product_by_id(product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID '{product_id}' was not found."
        )

    related = await product_service.get_related_products(product)
    return ProductDetailResponse(product=product, related_products=related)
