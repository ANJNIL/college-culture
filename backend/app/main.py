import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.database.supabase import db
from app.security.rate_limiter import limiter
from app.routes import (
    auth_router,
    products_router,
    cart_router,
    wishlist_router,
    orders_router,
    payment_router,
    ai_router,
    config_router,
    unstop_router,
)

# Configure secure logging without leaking credentials
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("lihas_backend")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Display integration status safely without exposing secrets
    settings.log_configuration_status(logger)
    logger.info("Initializing LIHAS Luxury Accessories Backend...")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Allowed CORS Origins: {settings.allowed_cors_origins}")
    try:
        seeded = await db.seed_products_if_empty()
        if seeded:
            logger.info("Supabase products table populated successfully.")
        else:
            logger.info("Products initialized (Supabase/in-memory catalog ready).")
    except Exception:
        logger.info("Catalog fallback active for local resilience.")
    yield
    logger.info("Shutting down LIHAS backend.")


app = FastAPI(
    title="LIHAS Luxury Accessories API",
    description="Backend API for LIHAS — Premium Men's Accessories, Powered by Gemini AI & Razorpay",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Rate Limiter setup
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS Configuration
# Strictly restricts origins to allowed origins defined in settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"]
)


# Global Safe Error Handler to prevent leakage of paths, secrets, or internal traces
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error processing {request.method} {request.url.path}: {type(exc).__name__}: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred. Please try again later."}
    )


# 1. Health check endpoint (Required by specification)
@app.get("/health", tags=["System"])
async def health_check():
    """Health check endpoint confirming backend operational status."""
    return {"status": "ok"}


# 2. Root API status endpoint
@app.get("/", tags=["System"])
async def root():
    return {
        "brand": "LIHAS",
        "tagline": "Beyond Ordinary | Men's Jewellery",
        "status": "online",
        "version": "1.0.0"
    }


# Register all business API routers
app.include_router(auth_router)
app.include_router(products_router)
app.include_router(cart_router)
app.include_router(wishlist_router)
app.include_router(orders_router)
app.include_router(payment_router)
app.include_router(ai_router)
app.include_router(config_router)
app.include_router(unstop_router)

