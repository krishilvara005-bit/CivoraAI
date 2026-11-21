import os
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent

try:  # backend/.env is read for local development; real environment variables always win
    from dotenv import load_dotenv

    load_dotenv(BASE / ".env", override=False)
except ImportError:  # python-dotenv is optional
    pass

DATA_DIR = Path(os.environ.get("DATA_DIR", BASE / "data"))


def _clean(value):
    """Strip whitespace and stray quotes that sneak in from .env files edited on Windows."""
    return (value or "").strip().strip("\"'").strip()


class Config:
    DATABASE = str(DATA_DIR / "civora.db")
    UPLOAD_DIR = str(DATA_DIR / "uploads")
    MAX_UPLOAD_MB = int(os.environ.get("MAX_UPLOAD_MB", "25"))
    GEMINI_API_KEY = _clean(os.environ.get("GEMINI_API_KEY"))
    GEMINI_MODEL = _clean(os.environ.get("GEMINI_MODEL")) or "gemini-2.5-flash"
    GEMINI_FALLBACK_MODELS = [m.strip() for m in os.environ.get("GEMINI_FALLBACK_MODELS", "gemini-1.5-flash,gemini-1.5-pro,gemini-2.0-flash").split(",") if m.strip()]
    ANTHROPIC_API_KEY = _clean(os.environ.get("ANTHROPIC_API_KEY"))
    ANTHROPIC_MODEL = _clean(os.environ.get("ANTHROPIC_MODEL")) or "claude-sonnet-5-5"
    ANTHROPIC_FALLBACK_MODELS = [m.strip() for m in os.environ.get("ANTHROPIC_FALLBACK_MODELS", "claude-haiku-5-5").split(",") if m.strip()]
    # "ocr" reads the drawing locally. "vision" asks Claude to read it (falls back to OCR on any failure).
    PLAN_READER = _clean(os.environ.get("PLAN_READER")) or "ocr"
    # Read the drawing in a background thread so the upload request returns at once.
    READ_ASYNC = True
