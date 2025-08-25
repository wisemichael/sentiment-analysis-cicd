# api/app/config.py
import os
from dotenv import load_dotenv

# Load .env at project root (Final Project/.env)
load_dotenv()

# Core settings
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://postgres:postgres@localhost:5432/preds",
)

ALLOW_FALLBACK_MODEL = os.getenv("ALLOW_FALLBACK_MODEL", "true").lower() == "true"
MODEL_VERSION = os.getenv("MODEL_VERSION", "baseline-tfidf-logreg")

# Test mode: set via $env:TESTING="1" (PowerShell) or in .env
TESTING = os.getenv("TESTING", "0").lower() in ("1", "true", "yes")
