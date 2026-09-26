from typing import List, Optional, Tuple, Dict, Any
from fastapi import HTTPException, status
from app.database.supabase import db
from app.models.domain import Product, OrderItem
from app.schemas.orders import OrderItemRequest

FREE_SHIPPING_THRESHOLD = 799
STANDARD_SHIPPING_FEE = 70


class ProductService:
    async def get_all_products(
        self,
        category: Optional[str] = None,
        min_price: Optional[int] = None,
        max_price: Optional[int] = None,
        sort_by: Optional[str] = "default",
        search: Optional[str] = None,
    ) -> List[Product]:
        """Fetch and filter products according to user criteria."""
        all_products = await db.get_all_products()

        filtered = []
        for p in all_products:
            # Category filter
            if category and category.lower() != "all" and p.category.lower() != category.lower():
                continue
            # Price filters
            if min_price is not None and p.price < min_price:
                continue
            if max_price is not None and p.price > max_price:
                continue
            # Search query
            if search:
                q = search.lower().strip()
                in_name = q in p.name.lower()
                in_cat = q in p.category.lower()
                in_desc = q in p.description.lower()
                in_mat = q in p.material.lower()
                if not (in_name or in_cat or in_desc or in_mat):
                    continue
            filtered.append(p)

        # Sorting
        if sort_by == "priceLow":
            filtered.sort(key=lambda x: x.price)
        elif sort_by == "priceHigh":
            filtered.sort(key=lambda x: x.price, reverse=True)
        elif sort_by == "rating":
            filtered.sort(key=lambda x: x.rating, reverse=True)

        return filtered

    async def get_product_by_id(self, product_id: str) -> Optional[Product]:
        """Retrieve single product by id."""
        return await db.get_product_by_id(product_id)

    async def get_related_products(self, product: Product, limit: int = 3) -> List[Product]:
        """Get related accessories in similar or complementary categories."""
        all_products = await db.get_all_products()
        related = [p for p in all_products if p.id != product.id]
        # prioritize complementary categories
        related.sort(key=lambda p: 0 if p.category != product.category else 1)
        return related[:limit]

    async def calculate_and_validate_order_totals(
        self,
        items: List[OrderItemRequest]
    ) -> Tuple[int, int, int, List[OrderItem]]:
        """
        CRITICAL SECURITY REQUIREMENT:
        Calculate order totals strictly using backend database product prices.
        Never trust price sent by the client.
        Returns: (subtotal, shipping_amount, grand_total, validated_order_items)
        """
        if not items:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Order must contain at least one item."
            )

        subtotal = 0
        validated_items: List[OrderItem] = []

        for item_req in items:
            product = await db.get_product_by_id(item_req.product_id)
            if not product:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Product with ID '{item_req.product_id}' was not found in catalog."
                )
            if not product.is_active:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Product '{product.name}' is currently unavailable."
                )
            if product.stock < item_req.quantity:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Insufficient stock for '{product.name}'. Available: {product.stock}."
                )

            item_total = product.price * item_req.quantity
            subtotal += item_total

            validated_items.append(
                OrderItem(
                    product_id=product.id,
                    product_name=product.name,
                    price=product.price,
                    quantity=item_req.quantity,
                    selected_size=item_req.selected_size,
                    image_url=product.image_url,
                )
            )

        shipping_amount = 0 if (subtotal >= FREE_SHIPPING_THRESHOLD or subtotal == 0) else STANDARD_SHIPPING_FEE
        grand_total = subtotal + shipping_amount

        return subtotal, shipping_amount, grand_total, validated_items


product_service = ProductService()
