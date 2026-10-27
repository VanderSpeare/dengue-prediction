"""
config.py – Centralised configuration loader for Dengue Prediction System.

Loads environment variables from .env file (if present) using python-dotenv,
then exposes typed settings throughout the application.

Usage:
    from config import settings
    api_key = settings.GEMINI_API_KEY
"""
import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Locate .env in the project root (two levels up from src/config.py)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_ENV_FILE = _PROJECT_ROOT / ".env"


def _load_dotenv() -> None:
    """Load .env file using python-dotenv (if installed), else skip silently."""
    try:
        from dotenv import load_dotenv
        if _ENV_FILE.exists():
            load_dotenv(dotenv_path=_ENV_FILE, override=False)
            logger.debug(f"Loaded .env from {_ENV_FILE}")
        else:
            logger.debug(".env file not found – relying on system environment variables.")
    except ImportError:
        logger.debug("python-dotenv not installed – relying on system environment variables.")


_load_dotenv()


class _Settings:
    """Typed access to all environment variables used by the application."""

    # ---- Gemini / Google AI ------------------------------------------
    @property
    def GEMINI_API_KEY(self) -> str | None:
        """Primary Google Gemini API key."""
        return os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

    @property
    def GEMINI_MODEL(self) -> str:
        """Gemini model name (default: gemini-3.5-flash-lite).
        Available models (Google AI Studio, Sep 2026):
          gemini-3.5-flash-lite  <- fastest, cheapest (recommended)
          gemini-3.7-flash       <- high-speed, agentic
          gemini-3.1-pro-preview <- most capable
        """
        return os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")

    # ---- Google Maps (optional) --------------------------------------
    @property
    def GOOGLE_MAPS_API_KEY(self) -> str | None:
        return os.getenv("GOOGLE_MAPS_API_KEY")

    # ---- Open-Meteo Weather (optional) --------------------------------
    @property
    def OPEN_METEO_API_URL(self) -> str:
        return os.getenv(
            "OPEN_METEO_API_URL",
            "https://archive-api.open-meteo.com/v1/archive"
        )

    # ---- Logging -------------------------------------------------------
    @property
    def LOG_LEVEL(self) -> str:
        return os.getenv("LOG_LEVEL", "INFO").upper()

    def __repr__(self) -> str:
        key = self.GEMINI_API_KEY
        masked = (key[:8] + "***") if key and key != "your_gemini_api_key_here" else "NOT SET"
        return (
            f"<Settings GEMINI_API_KEY={masked} "
            f"GEMINI_MODEL={self.GEMINI_MODEL} "
            f"LOG_LEVEL={self.LOG_LEVEL}>"
        )


settings = _Settings()
