import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
import httpx
from app.config import settings
from app.database.seed_data import SEED_PRODUCTS
from app.models.domain import Product, CartItem, Order, OrderItem

# In-memory fallback stores for development resilience
_IN_MEMORY_PRODUCTS: Dict[str, Dict[str, Any]] = {p["id"]: dict(p) for p in SEED_PRODUCTS}
_IN_MEMORY_CARTS: Dict[str, List[Dict[str, Any]]] = {}  # user_id -> items
_IN_MEMORY_WISHLISTS: Dict[str, List[str]] = {}         # user_id -> [product_ids]
_IN_MEMORY_ORDERS: Dict[str, Dict[str, Any]] = {}       # order_id -> order dict
_IN_MEMORY_USERS: Dict[str, Dict[str, Any]] = {}        # email -> user dict
_UNAVAILABLE_TABLES: set = set()


class SupabaseClient:
    def __init__(self):
        self.base_url = f"{settings.normalized_supabase_url}/rest/v1"
        self.anon_key = settings.SUPABASE_ANON_KEY
        self.service_role_key = settings.SUPABASE_SERVICE_ROLE_KEY or settings.SUPABASE_ANON_KEY
        self.timeout = 3.0

    def _headers(self, write: bool = False) -> Dict[str, str]:
        headers = {
            "apikey": self.service_role_key,
            "Authorization": f"Bearer {self.service_role_key}",
            "Content-Type": "application/json",
        }
        if write:
            headers["Prefer"] = "return=representation"
        return headers

    def _is_table_available(self, table: str) -> bool:
        return table not in _UNAVAILABLE_TABLES

    async def get_all_products(self) -> List[Product]:
        """Fetch all active products with graceful fallback to catalog."""
        if self._is_table_available("products"):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    res = await client.get(
                        f"{self.base_url}/products?is_active=eq.true&order=created_at.desc",
                        headers=self._headers()
                    )
                    if res.status_code == 200:
                        data = res.json()
                        if data:
                            return [Product(**item) for item in data]
                    elif res.status_code == 404:
                        _UNAVAILABLE_TABLES.add("products")
            except Exception:
                pass
        return [Product(**p) for p in _IN_MEMORY_PRODUCTS.values() if p.get("is_active", True)]

    async def get_product_by_id(self, product_id: str) -> Optional[Product]:
        """Fetch single product by its unique ID."""
        if self._is_table_available("products"):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    res = await client.get(
                        f"{self.base_url}/products?id=eq.{product_id}",
                        headers=self._headers()
                    )
                    if res.status_code == 200:
                        data = res.json()
                        if data and len(data) > 0:
                            return Product(**data[0])
                    elif res.status_code == 404:
                        _UNAVAILABLE_TABLES.add("products")
            except Exception:
                pass
        if product_id in _IN_MEMORY_PRODUCTS:
            return Product(**_IN_MEMORY_PRODUCTS[product_id])
        return None

    async def seed_products_if_empty(self) -> bool:
        """Attempt to populate Supabase products table if empty."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.get(
                    f"{self.base_url}/products?select=id&limit=1",
                    headers=self._headers()
                )
                if res.status_code == 200 and len(res.json()) == 0:
                    post_res = await client.post(
                        f"{self.base_url}/products",
                        headers=self._headers(write=True),
                        json=SEED_PRODUCTS
                    )
                    return post_res.status_code in (200, 201)
        except Exception:
            pass
        return False

    # --- CART ---
    async def get_cart(self, user_id: str) -> List[CartItem]:
        """Fetch cart items for a given user."""
        if self._is_table_available("cart_items"):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    res = await client.get(
                        f"{self.base_url}/cart_items?user_id=eq.{user_id}&order=created_at.asc",
                        headers=self._headers()
                    )
                    if res.status_code == 200:
                        items_raw = res.json()
                        items = []
                        for raw in items_raw:
                            item = CartItem(**raw)
                            item.product = await self.get_product_by_id(item.product_id)
                            items.append(item)
                        return items
                    elif res.status_code == 404:
                        _UNAVAILABLE_TABLES.add("cart_items")
            except Exception:
                pass

        # Fallback to in-memory cart
        mem_items = _IN_MEMORY_CARTS.get(user_id, [])
        items = []
        for raw in mem_items:
            item = CartItem(**raw)
            item.product = await self.get_product_by_id(item.product_id)
            items.append(item)
        return items

    async def add_to_cart(self, user_id: str, product_id: str, size: str, quantity: int = 1) -> CartItem:
        """Add product to user's cart or increment quantity."""
        now = datetime.now(timezone.utc).isoformat()
        if self._is_table_available("cart_items"):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    # Check existing item
                    check_res = await client.get(
                        f"{self.base_url}/cart_items?user_id=eq.{user_id}&product_id=eq.{product_id}&selected_size=eq.{size}",
                        headers=self._headers()
                    )
                    if check_res.status_code == 200 and len(check_res.json()) > 0:
                        existing = check_res.json()[0]
                        new_qty = existing["quantity"] + quantity
                        patch_res = await client.patch(
                            f"{self.base_url}/cart_items?id=eq.{existing['id']}",
                            headers=self._headers(write=True),
                            json={"quantity": new_qty, "updated_at": now}
                        )
                        if patch_res.status_code in (200, 204):
                            updated = patch_res.json()[0] if patch_res.text else {**existing, "quantity": new_qty}
                            item = CartItem(**updated)
                            item.product = await self.get_product_by_id(product_id)
                            return item
                    elif check_res.status_code == 404:
                        _UNAVAILABLE_TABLES.add("cart_items")
                    else:
                        new_item_data = {
                            "user_id": user_id,
                            "product_id": product_id,
                            "selected_size": size,
                            "quantity": quantity,
                            "created_at": now,
                            "updated_at": now
                        }
                        post_res = await client.post(
                            f"{self.base_url}/cart_items",
                            headers=self._headers(write=True),
                            json=new_item_data
                        )
                        if post_res.status_code in (200, 201):
                            created = post_res.json()[0]
                            item = CartItem(**created)
                            item.product = await self.get_product_by_id(product_id)
                            return item
                        elif post_res.status_code == 404:
                            _UNAVAILABLE_TABLES.add("cart_items")
            except Exception:
                pass

        # In-memory fallback
        if user_id not in _IN_MEMORY_CARTS:
            _IN_MEMORY_CARTS[user_id] = []
        user_cart = _IN_MEMORY_CARTS[user_id]
        for existing in user_cart:
            if existing["product_id"] == product_id and existing["selected_size"] == size:
                existing["quantity"] += quantity
                item = CartItem(**existing)
                item.product = await self.get_product_by_id(product_id)
                return item

        new_entry = {
            "id": f"cart_{uuid.uuid4().hex[:12]}",
            "user_id": user_id,
            "product_id": product_id,
            "selected_size": size,
            "quantity": quantity,
            "created_at": now
        }
        user_cart.append(new_entry)
        item = CartItem(**new_entry)
        item.product = await self.get_product_by_id(product_id)
        return item

    async def update_cart_quantity(self, user_id: str, product_id: str, size: str, new_quantity: int) -> bool:
        """Update cart item quantity or remove if quantity <= 0."""
        if new_quantity <= 0:
            return await self.remove_from_cart(user_id, product_id, size)

        now = datetime.now(timezone.utc).isoformat()
        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                patch_res = await client.patch(
                    f"{self.base_url}/cart_items?user_id=eq.{user_id}&product_id=eq.{product_id}&selected_size=eq.{size}",
                    headers=self._headers(),
                    json={"quantity": new_quantity, "updated_at": now}
                )
                if patch_res.status_code in (200, 204):
                    return True
        except Exception:
            pass

        # In-memory fallback
        user_cart = _IN_MEMORY_CARTS.get(user_id, [])
        for item in user_cart:
            if item["product_id"] == product_id and item["selected_size"] == size:
                item["quantity"] = new_quantity
                return True
        return False

    async def remove_from_cart(self, user_id: str, product_id: str, size: str) -> bool:
        """Remove item from cart."""
        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                res = await client.delete(
                    f"{self.base_url}/cart_items?user_id=eq.{user_id}&product_id=eq.{product_id}&selected_size=eq.{size}",
                    headers=self._headers()
                )
                if res.status_code in (200, 204):
                    return True
        except Exception:
            pass

        user_cart = _IN_MEMORY_CARTS.get(user_id, [])
        _IN_MEMORY_CARTS[user_id] = [
            it for it in user_cart
            if not (it["product_id"] == product_id and it["selected_size"] == size)
        ]
        return True

    async def clear_cart(self, user_id: str) -> bool:
        """Clear all items from user cart."""
        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                await client.delete(
                    f"{self.base_url}/cart_items?user_id=eq.{user_id}",
                    headers=self._headers()
                )
        except Exception:
            pass
        _IN_MEMORY_CARTS[user_id] = []
        return True

    # --- WISHLIST ---
    async def get_wishlist(self, user_id: str) -> List[str]:
        """Fetch list of product IDs in wishlist."""
        if self._is_table_available("wishlist_items"):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    res = await client.get(
                        f"{self.base_url}/wishlist_items?user_id=eq.{user_id}&select=product_id",
                        headers=self._headers()
                    )
                    if res.status_code == 200:
                        return [r["product_id"] for r in res.json()]
                    elif res.status_code == 404:
                        _UNAVAILABLE_TABLES.add("wishlist_items")
            except Exception:
                pass
        return _IN_MEMORY_WISHLISTS.get(user_id, [])

    async def toggle_wishlist(self, user_id: str, product_id: str) -> bool:
        """Toggle product in wishlist. Returns True if now present, False if removed."""
        current_list = await self.get_wishlist(user_id)
        is_present = product_id in current_list

        if is_present:
            # Remove
            if self._is_table_available("wishlist_items"):
                try:
                    async with httpx.AsyncClient(timeout=self.timeout) as client:
                        del_res = await client.delete(
                            f"{self.base_url}/wishlist_items?user_id=eq.{user_id}&product_id=eq.{product_id}",
                            headers=self._headers()
                        )
                        if del_res.status_code == 404:
                            _UNAVAILABLE_TABLES.add("wishlist_items")
                except Exception:
                    pass
            if user_id in _IN_MEMORY_WISHLISTS:
                _IN_MEMORY_WISHLISTS[user_id] = [p for p in _IN_MEMORY_WISHLISTS[user_id] if p != product_id]
            return False
        else:
            # Add
            now = datetime.now(timezone.utc).isoformat()
            if self._is_table_available("wishlist_items"):
                try:
                    async with httpx.AsyncClient(timeout=self.timeout) as client:
                        post_res = await client.post(
                            f"{self.base_url}/wishlist_items",
                            headers=self._headers(write=True),
                            json={"user_id": user_id, "product_id": product_id, "created_at": now}
                        )
                        if post_res.status_code == 404:
                            _UNAVAILABLE_TABLES.add("wishlist_items")
                except Exception:
                    pass
            if user_id not in _IN_MEMORY_WISHLISTS:
                _IN_MEMORY_WISHLISTS[user_id] = []
            if product_id not in _IN_MEMORY_WISHLISTS[user_id]:
                _IN_MEMORY_WISHLISTS[user_id].append(product_id)
            return True

    # --- ORDERS ---
    async def create_order(
        self,
        user_id: str,
        subtotal: int,
        shipping_amount: int,
        grand_total: int,
        shipping_address: Dict[str, Any],
        items: List[OrderItem],
        payment_method: str = "razorpay",
        razorpay_order_id: Optional[str] = None
    ) -> Order:
        """Create new order record and associated line items."""
        order_id = f"ord_{uuid.uuid4().hex[:12]}"
        order_number = f"LH-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
        now = datetime.now(timezone.utc).isoformat()

        order_record = {
            "id": order_id,
            "user_id": user_id,
            "order_number": order_number,
            "subtotal": subtotal,
            "shipping_amount": shipping_amount,
            "grand_total": grand_total,
            "status": "pending",
            "payment_status": "pending",
            "payment_method": payment_method,
            "razorpay_order_id": razorpay_order_id,
            "shipping_address": shipping_address,
            "created_at": now,
        }

        # Attempt Supabase insert
        if self._is_table_available("orders"):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    res = await client.post(
                        f"{self.base_url}/orders",
                        headers=self._headers(write=True),
                        json=order_record
                    )
                    if res.status_code in (200, 201):
                        # Insert items
                        line_items_data = [
                            {
                                "order_id": order_id,
                                "product_id": it.product_id,
                                "product_name": it.product_name,
                                "price": it.price,
                                "quantity": it.quantity,
                                "selected_size": it.selected_size,
                                "image_url": it.image_url,
                            }
                            for it in items
                        ]
                        await client.post(
                            f"{self.base_url}/order_items",
                            headers=self._headers(write=True),
                            json=line_items_data
                        )
                    elif res.status_code == 404:
                        _UNAVAILABLE_TABLES.add("orders")
            except Exception:
                pass

        # In-memory store
        order_record["items"] = items
        _IN_MEMORY_ORDERS[order_id] = order_record
        return Order(**order_record)

    async def update_order_payment(
        self,
        order_id: str,
        razorpay_payment_id: str,
        payment_status: str = "paid",
        status: str = "confirmed"
    ) -> bool:
        """Update payment and order status upon verification."""
        if self._is_table_available("orders"):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    patch_res = await client.patch(
                        f"{self.base_url}/orders?id=eq.{order_id}",
                        headers=self._headers(),
                        json={
                            "razorpay_payment_id": razorpay_payment_id,
                            "payment_status": payment_status,
                            "status": status,
                        }
                    )
                    if patch_res.status_code == 404:
                        _UNAVAILABLE_TABLES.add("orders")
            except Exception:
                pass

        if order_id in _IN_MEMORY_ORDERS:
            _IN_MEMORY_ORDERS[order_id]["razorpay_payment_id"] = razorpay_payment_id
            _IN_MEMORY_ORDERS[order_id]["payment_status"] = payment_status
            _IN_MEMORY_ORDERS[order_id]["status"] = status
            return True
        return False

    async def get_order_by_id(self, order_id: str) -> Optional[Order]:
        """Fetch order by ID."""
        if self._is_table_available("orders"):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    res = await client.get(
                        f"{self.base_url}/orders?id=eq.{order_id}",
                        headers=self._headers()
                    )
                    if res.status_code == 200 and len(res.json()) > 0:
                        order_data = res.json()[0]
                        # fetch line items
                        items_res = await client.get(
                            f"{self.base_url}/order_items?order_id=eq.{order_id}",
                            headers=self._headers()
                        )
                        items = [OrderItem(**it) for it in items_res.json()] if items_res.status_code == 200 else []
                        order_data["items"] = items
                        return Order(**order_data)
                    elif res.status_code == 404:
                        _UNAVAILABLE_TABLES.add("orders")
            except Exception:
                pass

        if order_id in _IN_MEMORY_ORDERS:
            return Order(**_IN_MEMORY_ORDERS[order_id])
        return None

    async def get_orders_for_user(self, user_id: str) -> List[Order]:
        """Fetch all orders placed by user."""
        if self._is_table_available("orders"):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    res = await client.get(
                        f"{self.base_url}/orders?user_id=eq.{user_id}&order=created_at.desc",
                        headers=self._headers()
                    )
                    if res.status_code == 200:
                        return [Order(**o) for o in res.json()]
                    elif res.status_code == 404:
                        _UNAVAILABLE_TABLES.add("orders")
            except Exception:
                pass

        user_orders = [
            Order(**ord_data)
            for ord_data in _IN_MEMORY_ORDERS.values()
            if ord_data.get("user_id") == user_id
        ]
        return sorted(user_orders, key=lambda x: x.created_at or "", reverse=True)

    # --- USERS / AUTH ---
    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Look up user by email."""
        clean_email = email.lower().strip()
        if self._is_table_available("users"):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    res = await client.get(
                        f"{self.base_url}/users?email=eq.{clean_email}",
                        headers=self._headers()
                    )
                    if res.status_code == 200 and len(res.json()) > 0:
                        return res.json()[0]
                    elif res.status_code == 404:
                        _UNAVAILABLE_TABLES.add("users")
            except Exception:
                pass
        return _IN_MEMORY_USERS.get(clean_email)

    async def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new user account."""
        clean_email = user_data["email"].lower().strip()
        user_data["email"] = clean_email
        if "id" not in user_data:
            user_data["id"] = f"usr_{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc).isoformat()
        user_data["created_at"] = now

        if self._is_table_available("users"):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    res = await client.post(
                        f"{self.base_url}/users",
                        headers=self._headers(write=True),
                        json=user_data
                    )
                    if res.status_code in (200, 201):
                        return res.json()[0]
                    elif res.status_code == 404:
                        _UNAVAILABLE_TABLES.add("users")
            except Exception:
                pass

        _IN_MEMORY_USERS[clean_email] = user_data
        return user_data


db = SupabaseClient()
