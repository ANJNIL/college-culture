"""
Re-export configuration from app.core.config for backwards compatibility.
All canonical settings definitions reside in app.core.config.
"""
from app.core.config import Settings, settings

__all__ = ["Settings", "settings"]
