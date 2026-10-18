"""DarkSword Admin configuration."""

import os
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

BASE_DIR = Path(__file__).resolve().parent

# Load .env if python-dotenv is installed
if load_dotenv is not None:
    dotenv_path = BASE_DIR / ".env"
    if dotenv_path.exists():
        load_dotenv(dotenv_path)


# JWT
SECRET_KEY = os.getenv("SECRET_KEY", "darksword_secret_key_change_me")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# CORS
CORS_ORIGINS_STR = os.getenv("CORS_ORIGINS", "")
if CORS_ORIGINS_STR:
    CORS_ORIGINS = [origin.strip() for origin in CORS_ORIGINS_STR.split(",") if origin.strip()]
else:
    # Dev defaults
    CORS_ORIGINS = ["http://localhost:8080", "http://localhost:5173", "http://localhost:3000"]

# Rate limiting
RATE_LIMIT = os.getenv("RATE_LIMIT", "100/minute")
AUTH_RATE_LIMIT = os.getenv("AUTH_RATE_LIMIT", "5/minute")
