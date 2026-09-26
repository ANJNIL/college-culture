from fastapi import APIRouter, Depends, HTTPException, status, Request
from app.schemas.auth import UserRegisterRequest, UserLoginRequest, TokenResponse, UserProfileResponse
from app.security.auth import hash_password, verify_password, create_access_token, get_current_user
from app.security.rate_limiter import limiter
from app.database.supabase import db

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse)
@limiter.limit("10/minute")
async def register(request: Request, body: UserRegisterRequest):
    """Register a new customer account securely with bcrypt password hashing."""
    existing = await db.get_user_by_email(body.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email address already exists."
        )

    pwd_hash = hash_password(body.password)
    user_data = {
        "email": body.email,
        "password_hash": pwd_hash,
        "full_name": body.full_name,
        "phone": body.phone,
        "role": "customer",
    }
    created_user = await db.create_user(user_data)

    token = create_access_token({
        "sub": created_user["id"],
        "email": created_user["email"],
        "full_name": created_user["full_name"],
        "role": created_user["role"]
    })

    return TokenResponse(
        access_token=token,
        user=UserProfileResponse(
            id=created_user["id"],
            email=created_user["email"],
            full_name=created_user["full_name"],
            phone=created_user.get("phone"),
            role=created_user["role"],
            created_at=created_user.get("created_at")
        )
    )


@router.post("/login", response_model=TokenResponse)
@limiter.limit("15/minute")
async def login(request: Request, body: UserLoginRequest):
    """Authenticate customer credentials and return a signed JWT token."""
    user = await db.get_user_by_email(body.email)
    if not user or not verify_password(body.password, user.get("password_hash", "")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password combination."
        )

    token = create_access_token({
        "sub": user["id"],
        "email": user["email"],
        "full_name": user["full_name"],
        "role": user.get("role", "customer")
    })

    return TokenResponse(
        access_token=token,
        user=UserProfileResponse(
            id=user["id"],
            email=user["email"],
            full_name=user["full_name"],
            phone=user.get("phone"),
            role=user.get("role", "customer"),
            created_at=user.get("created_at")
        )
    )


@router.get("/me", response_model=UserProfileResponse)
async def get_profile(current_user: dict = Depends(get_current_user)):
    """Fetch current authenticated customer profile."""
    return UserProfileResponse(
        id=current_user["id"],
        email=current_user["email"],
        full_name=current_user["full_name"],
        phone=current_user.get("phone"),
        role=current_user.get("role", "customer")
    )
