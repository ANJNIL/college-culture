import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

# Search for .env candidates
current_file_dir = Path(__file__).resolve().parent
candidates = [
    current_file_dir.parent.parent / ".env",          # backend/.env
    current_file_dir.parent.parent.parent / ".env",   # root/.env
    Path.cwd() / ".env",
    Path.cwd() / "backend" / ".env"
]
for candidate in candidates:
    if candidate.exists():
        load_dotenv(dotenv_path=candidate, override=False)


class Settings(BaseSettings):
    """
    Centralized, secure backend configuration manager using Pydantic Settings.
    
    SECURITY PRINCIPLES:
    - Automatically loads secrets from backend environment variables (.env).
    - Secrets are strictly preserved server-side and never exposed to the frontend or API responses.
    - Application evaluates integration status without exposing credentials.
    - Optional integrations do not prevent application startup.
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # 🤖 GEMINI AI
    GEMINI_API_KEY: str = ""

    # 🗄️ DATABASE / SUPABASE
    DATABASE_URL: str = ""
    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""

    # 🗺️ GOOGLE MAPS & PLACES
    GOOGLE_MAPS_API_KEY: str = ""
    GOOGLE_PLACES_API_KEY: str = ""

    # 🏆 UNSTOP SCRAPER API
    UNSTOP_SCRAPER_API_URL: str = ""
    UNSTOP_SCRAPER_API_KEY: str = ""

    # 💳 RAZORPAY
    RAZORPAY_KEY_ID: str = ""
    RAZORPAY_KEY_SECRET: str = ""

    # 📧 EMAIL (RESEND)
    RESEND_API_KEY: str = ""

    # 🔔 FIREBASE / PUSH NOTIFICATIONS
    FIREBASE_PROJECT_ID: str = ""
    FIREBASE_CLIENT_EMAIL: str = ""
    FIREBASE_PRIVATE_KEY: str = ""

    # 🌐 APPLICATION & AUTHENTICATION
    JWT_SECRET: str = "LIHAS_SUPER_SECURE_JWT_SECRET_KEY"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    FRONTEND_URL: str = "http://localhost:3000"
    ENVIRONMENT: str = "development"
    PORT: int = 8000

    # ==================================================
    # 🔍 AUTOMATIC API CONFIGURATION DETECTION
    # ==================================================
    @property
    def is_gemini_configured(self) -> bool:
        """Determines if Gemini AI integration is configured."""
        return bool(self.GEMINI_API_KEY and self.GEMINI_API_KEY.strip())

    @property
    def is_database_configured(self) -> bool:
        """Determines if Database / Supabase integration is configured."""
        has_db_url = bool(self.DATABASE_URL and self.DATABASE_URL.strip())
        has_supabase = bool(self.SUPABASE_URL and self.SUPABASE_URL.strip())
        return has_db_url or has_supabase

    @property
    def is_google_maps_configured(self) -> bool:
        """Determines if Google Maps integration is configured."""
        return bool(self.GOOGLE_MAPS_API_KEY and self.GOOGLE_MAPS_API_KEY.strip())

    @property
    def is_google_places_configured(self) -> bool:
        """Determines if Google Places integration is configured."""
        return bool(self.GOOGLE_PLACES_API_KEY and self.GOOGLE_PLACES_API_KEY.strip())

    @property
    def is_unstop_scraper_configured(self) -> bool:
        """Determines if Unstop Scraper integration is configured."""
        return bool(self.UNSTOP_SCRAPER_API_URL and self.UNSTOP_SCRAPER_API_URL.strip())

    @property
    def is_razorpay_configured(self) -> bool:
        """Determines if Razorpay payment integration is configured."""
        return bool(
            self.RAZORPAY_KEY_ID and self.RAZORPAY_KEY_ID.strip() and
            self.RAZORPAY_KEY_SECRET and self.RAZORPAY_KEY_SECRET.strip()
        )

    @property
    def is_email_configured(self) -> bool:
        """Determines if Resend Email integration is configured."""
        return bool(self.RESEND_API_KEY and self.RESEND_API_KEY.strip())

    @property
    def is_firebase_configured(self) -> bool:
        """Determines if Firebase push notification integration is configured."""
        return bool(
            self.FIREBASE_PROJECT_ID and self.FIREBASE_PROJECT_ID.strip() and
            self.FIREBASE_CLIENT_EMAIL and self.FIREBASE_CLIENT_EMAIL.strip() and
            self.FIREBASE_PRIVATE_KEY and self.FIREBASE_PRIVATE_KEY.strip()
        )

    def get_integrations_status(self) -> Dict[str, bool]:
        """
        Returns a dictionary containing ONLY boolean configuration status.
        Never returns secrets, tokens, keys, URLs with credentials, or passwords.
        """
        return {
            "gemini": self.is_gemini_configured,
            "database": self.is_database_configured,
            "google_maps": self.is_google_maps_configured,
            "google_places": self.is_google_places_configured,
            "unstop_scraper": self.is_unstop_scraper_configured,
            "razorpay": self.is_razorpay_configured,
            "email": self.is_email_configured,
            "firebase": self.is_firebase_configured,
        }

    def log_configuration_status(self, custom_logger: Optional[logging.Logger] = None) -> None:
        """
        At application startup, displays ONLY configuration status.
        
        CRITICAL SECURITY INVARIANT:
        NEVER display: GEMINI_API_KEY=..., tokens, passwords, database URLs,
        or any partial secrets. Display ONLY service names and status flags.
        """
        status_items = [
            ("Database", self.is_database_configured),
            ("Gemini AI", self.is_gemini_configured),
            ("Google Maps", self.is_google_maps_configured),
            ("Google Places", self.is_google_places_configured),
            ("Unstop Scraper", self.is_unstop_scraper_configured),
            ("Razorpay", self.is_razorpay_configured),
            ("Email", self.is_email_configured),
            ("Firebase", self.is_firebase_configured),
        ]

        # Ensure Windows console handles UTF-8 checkmarks safely
        can_utf8 = True
        try:
            import sys
            if hasattr(sys.stdout, "reconfigure"):
                sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            can_utf8 = False

        lines = [
            "==================================================",
            "API INTEGRATIONS CONFIGURATION STATUS",
            "==================================================",
        ]
        for name, configured in status_items:
            icon = "✓" if configured else "✗"
            state = "Configured" if configured else "Not configured"
            lines.append(f"{icon} {name}: {state}")
        lines.append("==================================================")
        lines.append("Environment: " + self.ENVIRONMENT)
        lines.append("==================================================")

        banner = "\n" + "\n".join(lines)
        if custom_logger:
            try:
                custom_logger.info(banner)
            except Exception:
                # Safe ASCII fallback
                ascii_lines = [
                    line.replace("✓", "[+]").replace("✗", "[-]") for line in lines
                ]
                custom_logger.info("\n" + "\n".join(ascii_lines))
        else:
            try:
                print(banner)
            except Exception:
                # Safe ASCII fallback
                ascii_lines = [
                    line.replace("✓", "[+]").replace("✗", "[-]") for line in lines
                ]
                print("\n" + "\n".join(ascii_lines))

    # ==================================================
    # 🛠️ HELPER PROPERTIES & UTILITIES
    # ==================================================
    @property
    def normalized_supabase_url(self) -> str:
        """Strip trailing /rest/v1 or /rest/v1/ to yield base Supabase URL."""
        url = self.SUPABASE_URL.strip()
        if url.endswith("/rest/v1/"):
            url = url[:-9]
        elif url.endswith("/rest/v1"):
            url = url[:-8]
        return url.rstrip("/")

    @property
    def allowed_cors_origins(self) -> List[str]:
        """Parse allowed origins from FRONTEND_URL and include standard local/preview origins."""
        origins = set()
        if self.FRONTEND_URL:
            for item in self.FRONTEND_URL.split(","):
                cleaned = item.strip().rstrip("/")
                if cleaned:
                    origins.add(cleaned)
        # Always allow standard local Next.js dev server origins
        origins.add("http://localhost:3000")
        origins.add("http://127.0.0.1:3000")
        origins.add("https://remix-remix-liahs-beyond-ordinary-7180.ai.studio")
        origins.add("https://remix-remix-remix-collegeculture-4602.ai.studio")
        return list(origins)


# Export singleton instance
settings = Settings()
