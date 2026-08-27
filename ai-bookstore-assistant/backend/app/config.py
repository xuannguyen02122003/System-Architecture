"""
Central configuration for the backend.

Everything that might change (paths, company name, LLM settings) lives here so
the rest of the code never hard-codes a path or a magic string. This is a small
but important habit: one place to look when something needs to change.
"""
from pathlib import Path
import os

from dotenv import load_dotenv

# Load variables from backend/.env (API key, model name) if the file exists.
load_dotenv()

# --- Paths -------------------------------------------------------------------
# __file__ is .../backend/app/config.py, so:
APP_DIR = Path(__file__).resolve().parent      # .../backend/app
BACKEND_DIR = APP_DIR.parent                    # .../backend
DATA_DIR = BACKEND_DIR / "data"                 # raw JSON/CSV/doc source files
DOCS_DIR = DATA_DIR / "documents"               # TXT/PDF/MD policy documents
DB_PATH = APP_DIR / "bookstore.db"              # generated SQLite database

# --- Business identity (used in answers and the "about" document) ------------
COMPANY_NAME = "Chapter One Books"
COMPANY_TAGLINE = "An online bookstore based in Ho Chi Minh City."

# --- LLM settings (read from environment; safe defaults) ---------------------
# We target an OpenAI-COMPATIBLE API, so this also works with Azure OpenAI,
# local servers (Ollama, LM Studio), or any drop-in provider by changing BASE_URL.
LLM_API_KEY = os.getenv("OPENAI_API_KEY", "")
LLM_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
