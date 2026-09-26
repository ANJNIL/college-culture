import os
import sys
from pathlib import Path
from fastapi.testclient import TestClient

# Ensure backend root is on path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.main import app
from app.config import settings

client = TestClient(app)


def test_01_environment_loaded():
    """1. Confirm environment variables are loaded."""
    assert bool(settings.GEMINI_API_KEY), "GEMINI_API_KEY must be loaded"
    assert bool(settings.SUPABASE_URL), "SUPABASE_URL must be loaded"
    assert bool(settings.RAZORPAY_KEY_ID), "RAZORPAY_KEY_ID must be loaded"
    assert bool(settings.RAZORPAY_KEY_SECRET), "RAZORPAY_KEY_SECRET must be loaded"
    print("Test 1 PASS: Environment variables loaded properly.")


def test_02_health_endpoint():
    """2. Test health endpoint."""
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}
    # Verify no secret values leaked in response
    text = res.text
    assert settings.GEMINI_API_KEY not in text
    assert settings.RAZORPAY_KEY_SECRET not in text
    print("Test 2 PASS: GET /health returns status ok without secrets.")


def test_03_product_api():
    """3. Test product API."""
    res = client.get("/api/products")
    assert res.status_code == 200
    data = res.json()
    assert "products" in data
    assert len(data["products"]) >= 6
    p1 = data["products"][0]
    assert "id" in p1
    assert "name" in p1
    assert "price" in p1
    assert "category" in p1

    # Test single product
    prod_id = p1["id"]
    single_res = client.get(f"/api/products/{prod_id}")
    assert single_res.status_code == 200
    assert single_res.json()["product"]["id"] == prod_id
    print(f"Test 3 PASS: Product catalog returns {len(data['products'])} luxury accessories.")


def test_04_auth_flow():
    """4. Test authentication registration, login, and profile."""
    import uuid
    rand_email = f"customer_{uuid.uuid4().hex[:6]}@example.com"
    pwd = "college  culturePassword123!"

    # Register
    reg_res = client.post("/api/auth/register", json={
        "email": rand_email,
        "password": pwd,
        "full_name": "Test Customer",
        "phone": "+91 99999 88888"
    })
    assert reg_res.status_code == 200
    reg_data = reg_res.json()
    assert "access_token" in reg_data
    token = reg_data["access_token"]

    # Login
    login_res = client.post("/api/auth/login", json={
        "email": rand_email,
        "password": pwd
    })
    assert login_res.status_code == 200
    login_data = login_res.json()
    assert "access_token" in login_data

    # Profile Me
    me_res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    assert me_res.json()["email"] == rand_email
    print("Test 4 PASS: Authentication flow (register, login, me) passed.")


def test_05_cart_endpoints():
    """5. Test cart operations."""
    headers = {"x-guest-id": "test_cart_user_001"}

    # Add to cart
    add_res = client.post(
        "/api/cart/add",
        headers=headers,
        json={"product_id": "college  culture-rng-01", "selected_size": "US 9", "quantity": 1}
    )
    assert add_res.status_code == 200

    # Get cart
    get_res = client.get("/api/cart", headers=headers)
    assert get_res.status_code == 200
    cart_data = get_res.json()
    assert cart_data["total_count"] >= 1
    assert cart_data["subtotal"] >= 399

    # Update quantity
    upd_res = client.patch(
        "/api/cart/update?product_id=college  culture-rng-01&selected_size=US 9&quantity=2",
        headers=headers
    )
    assert upd_res.status_code == 200

    # Remove item
    rem_res = client.delete(
        "/api/cart/remove?product_id=college  culture-rng-01&selected_size=US 9",
        headers=headers
    )
    assert rem_res.status_code == 200
    print("Test 5 PASS: Cart add, get, update, and remove passed.")


def test_06_wishlist_endpoints():
    """6. Test wishlist operations."""
    headers = {"x-guest-id": "test_wishlist_user_001"}

    # Toggle save
    tog_res = client.post(
        "/api/wishlist/toggle",
        headers=headers,
        json={"product_id": "college  culture-nck-01"}
    )
    assert tog_res.status_code == 200
    assert tog_res.json()["is_saved"] is True

    # Get wishlist
    get_res = client.get("/api/wishlist", headers=headers)
    assert get_res.status_code == 200
    data = get_res.json()
    assert "college  culture-nck-01" in data["product_ids"]

    # Toggle remove
    tog_res2 = client.post(
        "/api/wishlist/toggle",
        headers=headers,
        json={"product_id": "college  culture-nck-01"}
    )
    assert tog_res2.status_code == 200
    assert tog_res2.json()["is_saved"] is False
    print("Test 6 PASS: Wishlist save, get, and toggle passed.")


def test_07_gemini_ai_endpoints():
    """7. Test Gemini style recommendation, description, and chat."""
    # Style Recommendation
    rec_res = client.post("/api/ai/style-recommendation", json={
        "occasion": "Luxury rooftop dinner",
        "style_preference": "Sophisticated monochrome",
        "budget": 1500
    })
    assert rec_res.status_code == 200
    rec_data = rec_res.json()
    assert "styling_advice" in rec_data
    assert "recommended_products" in rec_data
    assert len(rec_data["recommended_products"]) > 0

    # Real products constraint verification:
    valid_ids = {"college  culture-rng-01", "college  culture-nck-01", "college  culture-ear-01", "college  culture-rng-02", "college  culture-nck-02", "college  culture-clp-01"}
    for p in rec_data["recommended_products"]:
        assert p["id"] in valid_ids, f"Gemini recommended hallucinated product: {p['id']}"

    # Product Description
    desc_res = client.post("/api/ai/product-description", json={
        "product_id": "college  culture-rng-01"
    })
    assert desc_res.status_code == 200
    desc_data = desc_res.json()
    assert "luxury_description" in desc_data

    # Style Chat
    chat_res = client.post("/api/ai/style-chat", json={
        "message": "Which chain pairs best with an oversized dark charcoal tee?"
    })
    assert chat_res.status_code == 200
    chat_data = chat_res.json()
    assert "reply" in chat_data
    print("Test 7 PASS: Gemini AI style recommendations, descriptions, and stylist chat verified.")


def test_08_payment_order_and_verification():
    """8. Test Razorpay payment order creation and signature verification."""
    pay_order_res = client.post("/api/payment/create-order", json={
        "items": [
            {"product_id": "college  culture-rng-01", "selected_size": "US 9", "quantity": 1}
        ],
        "shipping_address": {
            "first_name": "Dev",
            "last_name": "Kumar",
            "address": "402 Oberoi Towers, Worli",
            "city": "Mumbai",
            "pincode": "400018"
        }
    })
    assert pay_order_res.status_code == 200
    pay_data = pay_order_res.json()
    assert "razorpay_order_id" in pay_data
    assert pay_data["amount_in_inr"] == 399 + 70  # subtotal + shipping
    assert pay_data["amount_in_paise"] == (399 + 70) * 100
    assert "razorpay_key_id" in pay_data
    # Ensure KEY SECRET is NOT in response
    assert settings.RAZORPAY_KEY_SECRET not in pay_order_res.text

    # Test invalid signature rejection
    fake_verify_res = client.post("/api/payment/verify", json={
        "order_id": pay_data["order_id"],
        "razorpay_order_id": pay_data["razorpay_order_id"],
        "razorpay_payment_id": "pay_fake12345",
        "razorpay_signature": "invalid_fake_signature"
    })
    assert fake_verify_res.status_code == 400
    print("Test 8 PASS: Razorpay order creation and signature security check passed.")


def test_09_configuration_manager_and_detection():
    """9. Test configuration manager automatic detection and safe status output."""
    status = settings.get_integrations_status()
    assert isinstance(status, dict)

    # Required integrations status check
    assert status["gemini"] is True
    assert status["database"] is True
    assert status["razorpay"] is True
    assert status["google_maps"] is True
    assert status["unstop_scraper"] is True
    assert status["email"] is True
    assert status["firebase"] is True
    assert status["google_places"] is False

    # Strictly boolean values
    for k, v in status.items():
        assert isinstance(v, bool), f"Integration status {k} should be bool, got {type(v)}"

    # Confirm secrets never leak in status representation
    status_str = str(status)
    assert settings.GEMINI_API_KEY not in status_str
    assert settings.RAZORPAY_KEY_SECRET not in status_str
    assert settings.UNSTOP_SCRAPER_API_KEY not in status_str
    assert settings.RESEND_API_KEY not in status_str
    assert "postgresql://" not in status_str
    print("Test 9 PASS: Configuration manager detection and zero-secret guarantee verified.")


def test_10_config_status_endpoint_security():
    """10. Test protected GET /api/config/status endpoint security."""
    from app.security.auth import create_access_token

    # 1. Anonymous access must be rejected
    anon_res = client.get("/api/config/status")
    assert anon_res.status_code == 401, f"Expected 401 Unauthorized, got {anon_res.status_code}"

    # 2. Customer role access must be forbidden
    customer_token = create_access_token({"sub": "cust_123", "email": "cust@college  culture.com", "role": "customer"})
    cust_res = client.get("/api/config/status", headers={"Authorization": f"Bearer {customer_token}"})
    assert cust_res.status_code == 403, f"Expected 403 Forbidden, got {cust_res.status_code}"

    # 3. Admin role access must succeed
    admin_token = create_access_token({"sub": "admin_001", "email": "admin@college  culture.com", "role": "admin"})
    admin_res = client.get("/api/config/status", headers={"Authorization": f"Bearer {admin_token}"})
    assert admin_res.status_code == 200, f"Expected 200 OK, got {admin_res.status_code}"
    
    data = admin_res.json()
    assert isinstance(data, dict)
    assert data["gemini"] is True
    assert data["database"] is True
    assert data["razorpay"] is True
    assert data["unstop_scraper"] is True
    assert data["google_places"] is False

    # Confirm response body has ZERO secrets
    body_text = admin_res.text
    assert settings.GEMINI_API_KEY not in body_text
    assert settings.RAZORPAY_KEY_SECRET not in body_text
    assert settings.UNSTOP_SCRAPER_API_KEY not in body_text
    assert "AIzaSy" not in body_text
    print("Test 10 PASS: Admin status endpoint access control and boolean-only response verified.")


def test_11_unstop_scraper_route():
    """11. Test Unstop scraper route exists and keeps keys hidden."""
    # Test that route is registered and does not expose API key in schema or headers
    res = client.get("/openapi.json")
    assert res.status_code == 200
    schema_text = res.text
    assert "/api/unstop/items" in schema_text
    assert "/api/config/status" in schema_text
    assert settings.UNSTOP_SCRAPER_API_KEY not in schema_text
    assert settings.GEMINI_API_KEY not in schema_text
    print("Test 11 PASS: Unstop scraper proxy route registered with credentials secured.")


if __name__ == "__main__":
    test_01_environment_loaded()
    test_02_health_endpoint()
    test_03_product_api()
    test_04_auth_flow()
    test_05_cart_endpoints()
    test_06_wishlist_endpoints()
    test_07_gemini_ai_endpoints()
    test_08_payment_order_and_verification()
    test_09_configuration_manager_and_detection()
    test_10_config_status_endpoint_security()
    test_11_unstop_scraper_route()
    print("\n==========================================")
    print("ALL 11 BACKEND INTEGRATION TESTS PASSED!")
    print("==========================================")

