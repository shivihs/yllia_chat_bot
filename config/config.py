import os
from dotenv import load_dotenv

load_dotenv()  # wczytuje klucze z .env

# OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Langfuse
LANGFUSE_API_KEY = os.getenv("LANGFUSE_SECRET_KEY")
LANGFUSE_HOST = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
LANGFUSE_ENABLED = os.getenv("LANGFUSE_ENABLED", "False").lower() == "true"

# Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SECRET_KEY")

# Nazwy tabel Supabase (prod/test)
ENVIRONMENT = os.getenv("ENVIRONMENT", "prod").lower()  # prod lub test
TABLE_SUFFIX = "_test" if ENVIRONMENT == "test" else ""

SUPABASE_TABLE_SESSIONS = f"yllia_sessions{TABLE_SUFFIX}"
SUPABASE_TABLE_MESSAGES = f"yllia_messages{TABLE_SUFFIX}"
SUPABASE_TABLE_PROMPTS = f"yllia_prompts{TABLE_SUFFIX}"

# Qdrant
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", None)  # jeśli nie ma autoryzacji, zostaw None

# Prompts
PROMPT_GENERAL = os.path.join(os.path.dirname(__file__), "..", "prompts", "prompt_general.md") # Prompt z jakiego korzystamy w aplikacji
PROMPT_SUMMARY = os.path.join(os.path.dirname(__file__), "..", "prompts", "prompt_summary.md") # Prompt do streszczenia historii rozmowy
PROMPT_PATIENTS_SUMMARY = os.path.join(os.path.dirname(__file__), "..", "prompts", "prompt_patients_summary.md") # Prompt do streszczenia historii rozmowy dla pacjentów
PROMPT_TRANSLATE_TO_POLISH = os.path.join(os.path.dirname(__file__), "..", "prompts", "prompt_translate_to_polish.md") # Prompt do tłumaczenia na polski
PROMPT_TRANSLATE_FROM_POLISH = os.path.join(os.path.dirname(__file__), "..", "prompts", "prompt_translate_from_polish.md") # Prompt do tłumaczenia z polska na inny język